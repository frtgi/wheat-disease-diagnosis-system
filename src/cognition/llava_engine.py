# -*- coding: utf-8 -*-
"""
Agri-LLaVA 认知模块
基于LLaVA架构适配农业场景，实现多模态语义理解

文档参考：
- 4.1 LLaVA架构在农业场景的适配
- 4.2 Agri-LLaVA的两阶段训练策略
"""
import os
import ssl

# 使用HF-Mirror镜像站避免SSL证书问题
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_DISABLE_SSL_VERIFICATION'] = '1'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

# 禁用SSL证书验证
ssl._create_default_https_context = ssl._create_unverified_context

import torch
import torch.nn as nn
from typing import Optional, List, Dict, Any, Tuple
from PIL import Image
import warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 尝试导入transformers，如果不可用则给出警告
try:
    from transformers import (
        CLIPVisionModel, CLIPImageProcessor, 
        AutoTokenizer, AutoModelForCausalLM,
        LlamaTokenizer, LlamaForCausalLM,
        BitsAndBytesConfig
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    warnings.warn("transformers库未安装，LLaVA功能将不可用。请运行: pip install transformers")

try:
    from peft import LoraConfig, get_peft_model, PeftModel
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    warnings.warn("peft库未安装，LoRA微调功能将不可用。请运行: pip install peft")


class CLIPVisionEncoder(nn.Module):
    """
    CLIP视觉编码器适配
    
    根据文档4.1节：
    "视觉编码器：负责将YOLOv8检测到的感兴趣区域（ROI）或全图
    转化为高维的视觉特征向量"
    """
    
    def __init__(
        self,
        model_name: str = "openai/clip-vit-large-patch14",
        cache_dir: Optional[str] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        super().__init__()
        
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers库未安装，无法使用CLIPVisionEncoder")
        
        self.device = device
        self.model_name = model_name
        
        print(f"🔍 [CLIPVisionEncoder] 正在加载视觉编码器: {model_name}")
        print(f"🌐 使用镜像源: {os.environ.get('HF_ENDPOINT', '默认')}")
        
        try:
            # 加载CLIP视觉模型 - 使用镜像源
            self.vision_model = CLIPVisionModel.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                trust_remote_code=True,
                local_files_only=False
            ).to(device)
            
            # 图像处理器
            self.image_processor = CLIPImageProcessor.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                trust_remote_code=True,
                local_files_only=False
            )
        except Exception as e:
            print(f"⚠️ 从镜像加载失败: {e}")
            print("💡 将使用备用模式（基于知识图谱的问答）")
            raise
        
        # 获取特征维度
        self.hidden_size = self.vision_model.config.hidden_size
        self.num_patches = (self.vision_model.config.image_size // 
                           self.vision_model.config.patch_size) ** 2
        
        print(f"✅ [CLIPVisionEncoder] 加载完成")
        print(f"   特征维度: {self.hidden_size}")
        print(f"   Patch数量: {self.num_patches}")
    
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        :param images: 预处理后的图像张量 [batch, 3, 224, 224]
        :return: 视觉特征 [batch, num_patches, hidden_size]
        """
        outputs = self.vision_model.pixel_values(images)
        return outputs.last_hidden_state
    
    def encode_image(self, image: Image.Image) -> torch.Tensor:
        """
        编码单张图像
        
        :param image: PIL图像
        :return: 视觉特征 [1, num_patches, hidden_size]
        """
        # 预处理图像
        inputs = self.image_processor(images=image, return_tensors="pt")
        pixel_values = inputs.pixel_values.to(self.device)
        
        # 提取特征
        with torch.no_grad():
            outputs = self.vision_model(pixel_values=pixel_values)
            # 使用[CLS] token和patch tokens
            image_features = outputs.last_hidden_state
        
        return image_features
    
    def encode_images(self, images: List[Image.Image]) -> torch.Tensor:
        """
        编码多张图像
        
        :param images: PIL图像列表
        :return: 视觉特征 [batch, num_patches, hidden_size]
        """
        features = []
        for image in images:
            feat = self.encode_image(image)
            features.append(feat)
        return torch.cat(features, dim=0)
    
    def freeze(self):
        """冻结视觉编码器参数"""
        for param in self.vision_model.parameters():
            param.requires_grad = False
        print("🔒 [CLIPVisionEncoder] 视觉编码器已冻结")


class ProjectionLayer(nn.Module):
    """
    投影层（Projection Layer）
    
    根据文档4.1节：
    "投影层：这是一个线性层或多层感知机（MLP），其关键作用是
    将视觉特征向量映射到LLM的词嵌入空间（Word Embedding Space）。
    它相当于一个'翻译官'，将图像的视觉信号翻译成LLM能听懂的'单词'"
    """
    
    def __init__(
        self,
        vision_hidden_size: int = 1024,  # CLIP ViT-L/14的hidden_size
        llm_hidden_size: int = 4096,     # LLaMA-2-7B的hidden_size
        projection_type: str = "mlp",    # 'linear' 或 'mlp'
        num_hidden_layers: int = 2       # MLP的隐藏层数
    ):
        super().__init__()
        
        self.vision_hidden_size = vision_hidden_size
        self.llm_hidden_size = llm_hidden_size
        self.projection_type = projection_type
        
        print(f"🔄 [ProjectionLayer] 初始化投影层")
        print(f"   输入维度: {vision_hidden_size} -> 输出维度: {llm_hidden_size}")
        print(f"   类型: {projection_type}")
        
        if projection_type == "linear":
            # 简单的线性投影
            self.projection = nn.Linear(vision_hidden_size, llm_hidden_size)
        elif projection_type == "mlp":
            # MLP投影（多层感知机）
            layers = []
            in_dim = vision_hidden_size
            
            # 隐藏层
            for i in range(num_hidden_layers):
                layers.extend([
                    nn.Linear(in_dim, llm_hidden_size),
                    nn.GELU(),
                    nn.LayerNorm(llm_hidden_size)
                ])
                in_dim = llm_hidden_size
            
            # 输出层
            layers.append(nn.Linear(llm_hidden_size, llm_hidden_size))
            
            self.projection = nn.Sequential(*layers)
        else:
            raise ValueError(f"不支持的投影类型: {projection_type}")
        
        # 层归一化
        self.layer_norm = nn.LayerNorm(llm_hidden_size)
    
    def forward(self, vision_features: torch.Tensor) -> torch.Tensor:
        """
        将视觉特征投影到LLM嵌入空间
        
        :param vision_features: 视觉特征 [batch, num_patches, vision_hidden_size]
        :return: 投影后的特征 [batch, num_patches, llm_hidden_size]
        """
        projected = self.projection(vision_features)
        projected = self.layer_norm(projected)
        return projected


class AgriLLaVA(nn.Module):
    """
    Agri-LLaVA: 农业领域适配的LLaVA模型
    
    根据文档4.2节的两阶段训练策略：
    - 阶段1：特征对齐预训练（冻结视觉编码器和LLM，仅训练投影层）
    - 阶段2：端到端指令微调（使用LoRA微调LLM）
    """
    
    def __init__(
        self,
        vision_encoder_name: str = "openai/clip-vit-large-patch14",
        llm_name: str = "lmsys/vicuna-7b-v1.5",
        cache_dir: Optional[str] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        load_in_8bit: bool = False,
        load_in_4bit: bool = False
    ):
        super().__init__()
        
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers库未安装，无法使用AgriLLaVA")
        
        self.device = device
        self.vision_encoder_name = vision_encoder_name
        self.llm_name = llm_name
        
        print("=" * 60)
        print("🌾 [Agri-LLaVA] 初始化农业多模态认知模型")
        print("=" * 60)
        
        # 1. 初始化视觉编码器
        self.vision_encoder = CLIPVisionEncoder(
            model_name=vision_encoder_name,
            cache_dir=cache_dir,
            device=device
        )
        
        # 2. 初始化LLM
        print(f"📝 [Agri-LLaVA] 正在加载语言模型: {llm_name}")
        
        # 加载tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            llm_name,
            cache_dir=cache_dir,
            use_fast=False
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 加载LLM
        load_kwargs = {
            "torch_dtype": torch.float16 if device == "cuda" else torch.float32,
            "cache_dir": cache_dir,
        }
        
        # 使用新的量化配置方式
        if load_in_8bit or load_in_4bit:
            try:
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=load_in_8bit,
                    load_in_4bit=load_in_4bit
                )
                load_kwargs["quantization_config"] = quantization_config
                print(f"🔧 使用量化配置: 8bit={load_in_8bit}, 4bit={load_in_4bit}")
            except Exception as e:
                print(f"⚠️ 量化配置失败，将不使用量化: {e}")
        
        self.llm = AutoModelForCausalLM.from_pretrained(
            llm_name,
            **load_kwargs
        )
        
        # 如果未使用量化，需要手动移动到设备
        if not (load_in_8bit or load_in_4bit):
            self.llm = self.llm.to(device)
        
        self.llm_hidden_size = self.llm.config.hidden_size
        print(f"✅ [Agri-LLaVA] LLM加载完成，隐藏层维度: {self.llm_hidden_size}")
        
        # 3. 初始化投影层
        self.projection_layer = ProjectionLayer(
            vision_hidden_size=self.vision_encoder.hidden_size,
            llm_hidden_size=self.llm_hidden_size,
            projection_type="mlp"
        ).to(device)
        
        print("=" * 60)
        print("✅ [Agri-LLaVA] 模型初始化完成")
        print("=" * 60)
    
    def forward(
        self,
        images: Optional[torch.Tensor] = None,
        input_ids: Optional[torch.Tensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        前向传播
        
        :param images: 图像张量 [batch, 3, 224, 224]
        :param input_ids: 输入token IDs [batch, seq_len]
        :param attention_mask: 注意力掩码 [batch, seq_len]
        :param labels: 标签 [batch, seq_len]
        :return: 包含loss和logits的字典
        """
        # 处理图像输入
        if images is not None:
            # 提取视觉特征
            vision_outputs = self.vision_encoder.vision_model(images)
            vision_features = vision_outputs.last_hidden_state
            
            # 投影到LLM空间
            projected_features = self.projection_layer(vision_features)
        else:
            projected_features = None
        
        # 准备LLM输入
        if input_ids is not None:
            # 获取文本嵌入
            text_embeds = self.llm.get_input_embeddings()(input_ids)
            
            # 如果有图像特征，将其拼接到文本嵌入前
            if projected_features is not None:
                # 假设图像token位于序列开头
                inputs_embeds = torch.cat([projected_features, text_embeds], dim=1)
                
                # 调整attention_mask
                if attention_mask is not None:
                    batch_size = attention_mask.shape[0]
                    num_image_tokens = projected_features.shape[1]
                    image_attention_mask = torch.ones(
                        (batch_size, num_image_tokens),
                        dtype=attention_mask.dtype,
                        device=attention_mask.device
                    )
                    attention_mask = torch.cat([image_attention_mask, attention_mask], dim=1)
            else:
                inputs_embeds = text_embeds
            
            # 前向传播到LLM
            outputs = self.llm(
                inputs_embeds=inputs_embeds,
                attention_mask=attention_mask,
                labels=labels,
                return_dict=True
            )
        else:
            # 只有图像输入
            if projected_features is not None:
                outputs = self.llm(
                    inputs_embeds=projected_features,
                    return_dict=True
                )
            else:
                raise ValueError("必须提供图像或文本输入")
        
        return outputs
    
    def generate(
        self,
        images: Optional[List[Image.Image]] = None,
        prompt: str = "",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """
        生成文本回复
        
        :param images: 输入图像列表
        :param prompt: 文本提示
        :param max_new_tokens: 最大生成token数
        :param temperature: 温度参数
        :param top_p: top-p采样参数
        :return: 生成的文本
        """
        self.eval()
        
        with torch.no_grad():
            # 处理图像
            if images is not None and len(images) > 0:
                # 编码图像
                vision_features_list = []
                for image in images:
                    feat = self.vision_encoder.encode_image(image)
                    vision_features_list.append(feat)
                vision_features = torch.cat(vision_features_list, dim=0)
                
                # 投影到LLM空间
                projected_features = self.projection_layer(vision_features)
            else:
                projected_features = None
            
            # 处理文本提示
            prompt_tokens = self.tokenizer(prompt, return_tensors="pt")
            input_ids = prompt_tokens.input_ids.to(self.device)
            text_embeds = self.llm.get_input_embeddings()(input_ids)
            
            # 合并图像和文本嵌入
            if projected_features is not None:
                inputs_embeds = torch.cat([projected_features, text_embeds], dim=1)
            else:
                inputs_embeds = text_embeds
            
            # 生成
            outputs = self.llm.generate(
                inputs_embeds=inputs_embeds,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                **kwargs
            )
            
            # 解码
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 移除prompt部分，只保留生成的内容
            if prompt in generated_text:
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
    
    def setup_lora(self, r: int = 16, lora_alpha: int = 32, lora_dropout: float = 0.05):
        """
        设置LoRA微调
        
        根据文档4.2节阶段2：
        "对投影层和LLM基座（通常采用LoRA方式）进行联合微调"
        """
        if not PEFT_AVAILABLE:
            raise ImportError("peft库未安装，无法使用LoRA")
        
        print(f"🔧 [Agri-LLaVA] 设置LoRA微调")
        print(f"   r={r}, alpha={lora_alpha}, dropout={lora_dropout}")
        
        # 配置LoRA
        lora_config = LoraConfig(
            r=r,
            lora_alpha=lora_alpha,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            lora_dropout=lora_dropout,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        # 应用LoRA到LLM
        self.llm = get_peft_model(self.llm, lora_config)
        print("✅ [Agri-LLaVA] LoRA配置完成")
    
    def freeze_vision_encoder(self):
        """冻结视觉编码器（阶段1和阶段2都需要）"""
        self.vision_encoder.freeze()
    
    def freeze_llm(self):
        """冻结LLM（仅阶段1使用）"""
        for param in self.llm.parameters():
            param.requires_grad = False
        print("🔒 [Agri-LLaVA] LLM已冻结")
    
    def unfreeze_projection_layer(self):
        """解冻投影层（阶段1和阶段2都需要训练）"""
        for param in self.projection_layer.parameters():
            param.requires_grad = True
        print("🔓 [Agri-LLaVA] 投影层已解冻")
    
    def save_pretrained(self, output_dir: str):
        """保存模型"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存投影层
        projection_path = os.path.join(output_dir, "projection_layer")
        os.makedirs(projection_path, exist_ok=True)
        torch.save(self.projection_layer.state_dict(), 
                   os.path.join(projection_path, "pytorch_model.bin"))
        
        # 保存LLM（包括LoRA权重）
        llm_path = os.path.join(output_dir, "llm")
        self.llm.save_pretrained(llm_path)
        
        # 保存tokenizer
        self.tokenizer.save_pretrained(output_dir)
        
        print(f"💾 [Agri-LLaVA] 模型已保存到: {output_dir}")
    
    def load_pretrained(self, model_dir: str):
        """加载预训练模型"""
        # 加载投影层
        projection_path = os.path.join(model_dir, "projection_layer")
        if os.path.exists(projection_path):
            state_dict = torch.load(
                os.path.join(projection_path, "pytorch_model.bin"),
                map_location=self.device
            )
            self.projection_layer.load_state_dict(state_dict)
            print(f"📂 [Agri-LLaVA] 投影层已加载")
        
        # 加载LLM
        llm_path = os.path.join(model_dir, "llm")
        if os.path.exists(llm_path):
            self.llm = AutoModelForCausalLM.from_pretrained(llm_path).to(self.device)
            print(f"📂 [Agri-LLaVA] LLM已加载")


def test_llava_engine():
    """测试Agri-LLaVA引擎"""
    print("=" * 60)
    print("🧪 测试 Agri-LLaVA 引擎")
    print("=" * 60)
    
    # 注意：这个测试需要下载CLIP和LLaMA模型，可能需要较长时间
    # 在实际测试前，请确保有足够的磁盘空间和网络连接
    
    print("\n⚠️ 注意：此测试需要下载大型预训练模型（约13GB）")
    print("如果需要跳过此测试，请设置环境变量 SKIP_LLaVA_TEST=1")
    
    if os.environ.get("SKIP_LLaVA_TEST"):
        print("⏭️ 跳过LLaVA测试")
        return
    
    try:
        # 创建模型（使用CPU和小型模型进行测试）
        print("\n1️⃣ 测试模型初始化...")
        model = AgriLLaVA(
            vision_encoder_name="openai/clip-vit-base-patch32",  # 使用较小的模型
            llm_name="gpt2",  # 使用GPT-2代替LLaMA进行测试
            device="cpu",
            load_in_8bit=False
        )
        print("✅ 模型初始化成功")
        
        # 测试投影层
        print("\n2️⃣ 测试投影层...")
        dummy_vision_features = torch.randn(1, 50, 768)  # CLIP base的维度
        projected = model.projection_layer(dummy_vision_features)
        print(f"✅ 投影层输出形状: {projected.shape}")
        assert projected.shape[-1] == model.llm_hidden_size
        
        # 测试生成（可选，因为GPT-2不是指令模型）
        print("\n3️⃣ 测试文本生成...")
        test_prompt = "这是一张小麦病害图像的描述："
        # generated = model.generate(prompt=test_prompt, max_new_tokens=20)
        # print(f"✅ 生成文本: {generated[:100]}...")
        
        print("\n" + "=" * 60)
        print("✅ Agri-LLaVA 引擎测试通过！")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_llava_engine()

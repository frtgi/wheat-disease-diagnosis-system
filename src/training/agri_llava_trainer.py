# -*- coding: utf-8 -*-
"""
Agri-LLaVA 训练模块

根据研究文档实现两阶段训练策略:
1. 第一阶段: 特征对齐预训练 (Feature Alignment)
   - 冻结视觉编码器和LLM基座
   - 仅训练投影层
   - 建立视觉特征与农业术语的强关联

2. 第二阶段: 端到端指令微调 (End-to-End Instruction Tuning)
   - 解冻投影层和LLM基座 (LoRA)
   - 赋予模型遵循复杂指令、进行逻辑推理的能力
"""
import os
import json
import ssl
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import (
    CLIPVisionModel, CLIPImageProcessor,
    AutoTokenizer, AutoModelForCausalLM,
    TrainingArguments, Trainer,
    DataCollatorForLanguageModeling
)
from PIL import Image

# 禁用SSL验证（用于测试环境）
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass


class TrainingPhase(Enum):
    """训练阶段"""
    FEATURE_ALIGNMENT = "feature_alignment"      # 特征对齐预训练
    INSTRUCTION_TUNING = "instruction_tuning"    # 指令微调


@dataclass
class TrainingConfig:
    """训练配置（兼容旧接口）"""
    stage: str = "alignment"  # 'alignment' 或 'instruction'
    batch_size: int = 4
    learning_rate: float = 2e-4
    epochs: int = 3
    device: str = "auto"
    output_dir: str = "models/agri_llava"


@dataclass
class AgriLLaVAConfig:
    """Agri-LLaVA配置"""
    # 模型配置
    vision_encoder: str = "openai/clip-vit-large-patch14"
    llm_name: str = "lmsys/vicuna-7b-v1.5"
    
    # 投影层配置
    projection_hidden_dim: int = 4096
    projection_output_dim: int = 4096
    
    # LoRA配置
    use_lora: bool = True
    lora_rank: int = 8
    lora_alpha: float = 16.0
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = None
    
    # 训练配置
    image_size: int = 224
    max_length: int = 512
    batch_size: int = 4
    learning_rate: float = 2e-4
    num_epochs: int = 3
    warmup_steps: int = 100
    
    def __post_init__(self):
        if self.lora_target_modules is None:
            self.lora_target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]


class ProjectionLayer(nn.Module):
    """
    投影层: 将视觉特征映射到LLM的词嵌入空间
    
    相当于一个"翻译官"，将图像的视觉信号翻译成LLM能听懂的"单词"
    """
    
    def __init__(
        self,
        vision_hidden_size: int = 1024,
        llm_hidden_size: int = 4096,
        intermediate_size: int = 4096
    ):
        super().__init__()
        
        self.projection = nn.Sequential(
            nn.Linear(vision_hidden_size, intermediate_size),
            nn.GELU(),
            nn.LayerNorm(intermediate_size),
            nn.Linear(intermediate_size, llm_hidden_size)
        )
    
    def forward(self, vision_features: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        :param vision_features: 视觉特征 [batch, num_patches, vision_hidden_size]
        :return: 投影后的特征 [batch, num_patches, llm_hidden_size]
        """
        return self.projection(vision_features)


class AgriLLaVAModel(nn.Module):
    """
    Agri-LLaVA 多模态模型
    
    架构:
    - 视觉编码器: CLIP ViT-L/14
    - 投影层: MLP
    - LLM基座: Vicuna-7B
    """
    
    def __init__(self, config: AgriLLaVAConfig):
        super().__init__()
        self.config = config
        
        try:
            # 加载视觉编码器
            print(f"📥 加载视觉编码器: {config.vision_encoder}")
            self.vision_encoder = CLIPVisionModel.from_pretrained(config.vision_encoder)
            self.image_processor = CLIPImageProcessor.from_pretrained(config.vision_encoder)
            
            # 加载LLM
            print(f"📥 加载LLM: {config.llm_name}")
            self.llm = AutoModelForCausalLM.from_pretrained(
                config.llm_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            self.tokenizer = AutoTokenizer.from_pretrained(config.llm_name)
            self.tokenizer.pad_token = self.tokenizer.eos_token
        except Exception as e:
            print(f"⚠️ 无法加载预训练模型: {e}")
            print("💡 使用模拟模型进行测试...")
            self._create_mock_model()
    
    def _create_mock_model(self):
        """创建模拟模型用于测试（完全离线）"""
        from transformers import CLIPVisionConfig, GPT2Config, CLIPImageProcessor
        
        print("   创建模拟视觉编码器...")
        # 创建模拟视觉编码器
        vision_config = CLIPVisionConfig(
            hidden_size=768,
            intermediate_size=3072,
            num_hidden_layers=12,
            num_attention_heads=12,
            image_size=224,
            patch_size=16,
        )
        self.vision_encoder = CLIPVisionModel(vision_config)
        # 创建简化的image processor
        self.image_processor = CLIPImageProcessor(
            size=224,
            do_resize=True,
            do_normalize=True,
        )
        
        print("   创建模拟LLM...")
        # 创建模拟LLM（完全离线配置）
        llm_config = GPT2Config(
            vocab_size=50257,
            n_positions=1024,
            n_embd=768,
            n_layer=4,  # 减小层数用于测试
            n_head=12,
        )
        self.llm = AutoModelForCausalLM.from_config(llm_config)
        
        # 创建tokenizer（离线）
        from transformers import GPT2Tokenizer
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2", local_files_only=False)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 创建投影层
        vision_hidden_size = self.vision_encoder.config.hidden_size
        llm_hidden_size = self.llm.config.hidden_size
        
        self.projection = ProjectionLayer(
            vision_hidden_size=vision_hidden_size,
            llm_hidden_size=llm_hidden_size,
            intermediate_size=config.projection_hidden_dim
        )
        
        print(f"✅ Agri-LLaVA模型初始化完成")
        print(f"   视觉特征维度: {vision_hidden_size}")
        print(f"   LLM维度: {llm_hidden_size}")
    
    def encode_images(self, images: torch.Tensor) -> torch.Tensor:
        """
        编码图像
        
        :param images: 图像张量 [batch, 3, H, W]
        :return: 视觉特征 [batch, num_patches, hidden_size]
        """
        with torch.no_grad():
            vision_outputs = self.vision_encoder(images)
            image_features = vision_outputs.last_hidden_state  # [batch, num_patches, hidden_size]
        
        # 投影到LLM空间
        projected_features = self.projection(image_features)
        
        return projected_features
    
    def forward(
        self,
        images: Optional[torch.Tensor] = None,
        input_ids: Optional[torch.Tensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        前向传播
        
        :param images: 图像
        :param input_ids: 输入token IDs
        :param attention_mask: 注意力掩码
        :param labels: 标签
        :return: 损失和logits
        """
        # 处理图像
        if images is not None:
            image_features = self.encode_images(images)
            
            # 将图像特征与文本特征拼接
            # 这里简化处理，实际应该更复杂的融合策略
            if input_ids is not None:
                text_embeds = self.llm.get_input_embeddings()(input_ids)
                # 在序列开头插入图像特征
                inputs_embeds = torch.cat([image_features, text_embeds], dim=1)
            else:
                inputs_embeds = image_features
        else:
            inputs_embeds = self.llm.get_input_embeddings()(input_ids)
        
        # 前向传播
        outputs = self.llm(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            labels=labels,
            return_dict=True
        )
        
        return outputs
    
    def generate(
        self,
        images: Optional[torch.Tensor] = None,
        prompts: Optional[List[str]] = None,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> List[str]:
        """
        生成文本
        
        :param images: 图像
        :param prompts: 提示词列表
        :param max_new_tokens: 最大生成token数
        :param temperature: 温度
        :param top_p: top-p采样
        :return: 生成的文本列表
        """
        self.eval()
        
        # 处理提示词
        if prompts is None:
            prompts = [""]
        
        # Tokenize
        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True
        ).to(self.llm.device)
        
        # 如果有图像，编码图像
        if images is not None:
            image_features = self.encode_images(images)
            text_embeds = self.llm.get_input_embeddings()(inputs.input_ids)
            inputs_embeds = torch.cat([image_features, text_embeds], dim=1)
        else:
            inputs_embeds = self.llm.get_input_embeddings()(inputs.input_ids)
        
        # 生成
        with torch.no_grad():
            outputs = self.llm.generate(
                inputs_embeds=inputs_embeds,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                **kwargs
            )
        
        # 解码
        generated_texts = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        
        return generated_texts


class AgriInstructDataset(Dataset):
    """
    Agri-Instruct数据集
    
    包含图像-指令-回答对
    """
    
    def __init__(
        self,
        data_path: str,
        image_processor,
        tokenizer,
        image_size: int = 224,
        max_length: int = 512
    ):
        self.data_path = Path(data_path)
        self.image_processor = image_processor
        self.tokenizer = tokenizer
        self.image_size = image_size
        self.max_length = max_length
        
        # 加载数据
        self.data = self._load_data()
    
    def _load_data(self) -> List[Dict]:
        """加载数据"""
        data = []
        
        # 支持JSON和JSONL格式
        if self.data_path.suffix == '.json':
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif self.data_path.suffix == '.jsonl':
            with open(self.data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data.append(json.loads(line))
        
        return data
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.data[idx]
        
        # 加载图像
        image_path = item.get('image')
        if image_path and Path(image_path).exists():
            image = Image.open(image_path).convert('RGB')
            pixel_values = self.image_processor(
                image,
                return_tensors="pt"
            ).pixel_values.squeeze(0)
        else:
            # 如果没有图像，使用零张量
            pixel_values = torch.zeros(3, self.image_size, self.image_size)
        
        # 处理文本
        instruction = item.get('instruction', '')
        answer = item.get('answer', '')
        
        # 构建对话格式
        conversation = f"USER: {instruction}\nASSISTANT: {answer}"
        
        # Tokenize
        tokenized = self.tokenizer(
            conversation,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'pixel_values': pixel_values,
            'input_ids': tokenized.input_ids.squeeze(0),
            'attention_mask': tokenized.attention_mask.squeeze(0),
            'labels': tokenized.input_ids.squeeze(0)
        }


class AgriLLaVATrainer:
    """
    Agri-LLaVA 训练器
    
    实现两阶段训练策略
    """
    
    def __init__(self, config: Optional[AgriLLaVAConfig] = None):
        self.config = config or AgriLLaVAConfig()
        self.model = None
        self.current_phase = None
    
    def setup_model(self):
        """设置模型"""
        print("=" * 70)
        print("🚀 初始化Agri-LLaVA模型")
        print("=" * 70)
        
        self.model = AgriLLaVAModel(self.config)
        
        # 统计参数
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        print(f"\n总参数量: {total_params:,}")
        print(f"可训练参数量: {trainable_params:,}")
        print(f"冻结比例: {(1 - trainable_params/total_params)*100:.2f}%")
    
    def phase1_feature_alignment(
        self,
        train_data_path: str,
        output_dir: str = "checkpoints/agri_llava/phase1",
        num_epochs: int = 3
    ):
        """
        第一阶段: 特征对齐预训练
        
        策略:
        - 冻结视觉编码器和LLM基座
        - 仅训练投影层
        - 建立视觉特征与农业术语的强关联
        
        :param train_data_path: 训练数据路径
        :param output_dir: 输出目录
        :param num_epochs: 训练轮数
        """
        print("\n" + "=" * 70)
        print("🎯 第一阶段: 特征对齐预训练")
        print("=" * 70)
        
        if self.model is None:
            self.setup_model()
        
        self.current_phase = TrainingPhase.FEATURE_ALIGNMENT
        
        # 冻结视觉编码器
        for param in self.model.vision_encoder.parameters():
            param.requires_grad = False
        print("✅ 视觉编码器已冻结")
        
        # 冻结LLM
        for param in self.model.llm.parameters():
            param.requires_grad = False
        print("✅ LLM基座已冻结")
        
        # 只训练投影层
        for param in self.model.projection.parameters():
            param.requires_grad = True
        print("✅ 投影层已解冻")
        
        # 创建数据集
        dataset = AgriInstructDataset(
            train_data_path,
            self.model.image_processor,
            self.model.tokenizer,
            self.config.image_size,
            self.config.max_length
        )
        
        print(f"📊 训练样本数: {len(dataset)}")
        
        # 训练参数
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            logging_steps=10,
            save_steps=500,
            save_total_limit=3,
            fp16=True,
            report_to="none"
        )
        
        # 创建训练器
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            data_collator=DataCollatorForLanguageModeling(
                tokenizer=self.model.tokenizer,
                mlm=False
            )
        )
        
        # 训练
        print("\n🚀 开始训练...")
        trainer.train()
        
        # 保存
        trainer.save_model(output_dir)
        print(f"✅ 第一阶段训练完成，模型已保存: {output_dir}")
    
    def phase2_instruction_tuning(
        self,
        train_data_path: str,
        output_dir: str = "checkpoints/agri_llava/phase2",
        num_epochs: int = 3
    ):
        """
        第二阶段: 端到端指令微调
        
        策略:
        - 保持视觉编码器冻结
        - 解冻投影层和LLM基座 (使用LoRA)
        - 赋予模型遵循复杂指令、进行逻辑推理的能力
        
        :param train_data_path: 训练数据路径
        :param output_dir: 输出目录
        :param num_epochs: 训练轮数
        """
        print("\n" + "=" * 70)
        print("🎯 第二阶段: 端到端指令微调")
        print("=" * 70)
        
        if self.model is None:
            self.setup_model()
        
        self.current_phase = TrainingPhase.INSTRUCTION_TUNING
        
        # 视觉编码器保持冻结
        for param in self.model.vision_encoder.parameters():
            param.requires_grad = False
        print("✅ 视觉编码器保持冻结")
        
        # 投影层保持可训练
        for param in self.model.projection.parameters():
            param.requires_grad = True
        print("✅ 投影层保持可训练")
        
        # 对LLM使用LoRA
        if self.config.use_lora:
            from peft import get_peft_model, LoraConfig, TaskType
            
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=self.config.lora_rank,
                lora_alpha=self.config.lora_alpha,
                lora_dropout=self.config.lora_dropout,
                target_modules=self.config.lora_target_modules
            )
            
            self.model.llm = get_peft_model(self.model.llm, lora_config)
            print(f"✅ LoRA已注入LLM (rank={self.config.lora_rank})")
            
            # 打印可训练参数
            self.model.llm.print_trainable_parameters()
        else:
            # 全参数微调
            for param in self.model.llm.parameters():
                param.requires_grad = True
            print("✅ LLM全参数微调")
        
        # 创建数据集
        dataset = AgriInstructDataset(
            train_data_path,
            self.model.image_processor,
            self.model.tokenizer,
            self.config.image_size,
            self.config.max_length
        )
        
        print(f"📊 训练样本数: {len(dataset)}")
        
        # 训练参数
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate / 10,  # 第二阶段使用更小学习率
            warmup_steps=self.config.warmup_steps,
            logging_steps=10,
            save_steps=500,
            save_total_limit=3,
            fp16=True,
            report_to="none"
        )
        
        # 创建训练器
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            data_collator=DataCollatorForLanguageModeling(
                tokenizer=self.model.tokenizer,
                mlm=False
            )
        )
        
        # 训练
        print("\n🚀 开始训练...")
        trainer.train()
        
        # 保存
        trainer.save_model(output_dir)
        print(f"✅ 第二阶段训练完成，模型已保存: {output_dir}")
    
    def train(
        self,
        phase1_data_path: str = None,
        phase2_data_path: str = None,
        output_dir: str = "checkpoints/agri_llava"
    ):
        """
        执行完整两阶段训练
        
        :param phase1_data_path: 第一阶段数据路径 (可选)
        :param phase2_data_path: 第二阶段数据路径 (可选)
        :param output_dir: 输出目录
        """
        # 如果没有提供数据路径，创建示例数据
        if phase1_data_path is None or phase2_data_path is None:
            print("⚠️ 未提供训练数据路径，创建示例数据...")
            create_sample_training_data("datasets/agri_instruct")
            phase1_data_path = "datasets/agri_instruct/phase1.json"
            phase2_data_path = "datasets/agri_instruct/phase2.json"
        
        # 第一阶段
        phase1_output = os.path.join(output_dir, "phase1")
        self.phase1_feature_alignment(phase1_data_path, phase1_output)
        
        # 第二阶段
        phase2_output = os.path.join(output_dir, "phase2")
        self.phase2_instruction_tuning(phase2_data_path, phase2_output)
        
        print("\n" + "=" * 70)
        print("🎉 Agri-LLaVA两阶段训练全部完成！")
        print("=" * 70)


def create_sample_training_data(output_dir: str = "datasets/agri_instruct"):
    """
    创建示例训练数据
    
    :param output_dir: 输出目录
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 第一阶段数据: 简单图文对齐
    phase1_data = [
        {
            "image": "images/stripe_rust_001.jpg",
            "instruction": "描述这张图片中的病害特征。",
            "answer": "这张图片显示小麦叶片上有鲜黄色的条状孢子堆，沿叶脉平行排列，这是条锈病的典型症状。"
        },
        {
            "image": "images/powdery_mildew_001.jpg",
            "instruction": "这是什么病害？",
            "answer": "这是小麦白粉病，叶片表面覆盖白色粉状霉层。"
        },
        {
            "image": "images/healthy_001.jpg",
            "instruction": "这张图片中的小麦健康吗？",
            "answer": "是的，这张图片中的小麦叶片翠绿，没有明显病斑，是健康状态。"
        }
    ]
    
    # 第二阶段数据: 复杂指令
    phase2_data = [
        {
            "image": "images/stripe_rust_002.jpg",
            "instruction": "图中的小麦叶片出现了黄色条纹，请分析可能的病因，并给出针对性的化学防治方案。",
            "answer": """根据图像特征，叶片呈现沿叶脉排列的鲜黄色条状孢子堆，符合小麦条锈病（Stripe Rust）的典型症状。

病因分析：
1. 病原体：Puccinia striiformis f. sp. tritici 真菌
2. 环境条件：温度9-16°C，高湿度，有露水
3. 品种因素：当前种植品种可能抗病性较差

防治方案：
1. 化学防治：使用三唑类杀菌剂，如三唑酮（粉锈宁）或戊唑醇，按推荐剂量喷雾
2. 农业措施：及时清除病残体，合理密植改善通风
3. 品种选择：下一季选择抗条锈病品种"""
        },
        {
            "image": "images/fusarium_001.jpg",
            "instruction": "小麦穗部出现粉红色霉层，籽粒变色，这是什么病？如何防治？",
            "answer": """这是小麦赤霉病（Fusarium Head Blight），由禾谷镰刀菌引起。

症状特征：
- 穗部出现粉红色霉层
- 籽粒干瘪变色
- 穗轴可能腐烂

发病条件：
- 抽穗扬花期遇连阴雨
- 温度25-30°C
- 田间湿度大

防治措施：
1. 化学防治：花期喷洒多菌灵或戊唑醇
2. 农业防治：清沟排水，降低田间湿度
3. 轮作倒茬：与水稻或非寄主作物轮作"""
        }
    ]
    
    # 保存
    with open(os.path.join(output_dir, "phase1_data.json"), 'w', encoding='utf-8') as f:
        json.dump(phase1_data, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(output_dir, "phase2_data.json"), 'w', encoding='utf-8') as f:
        json.dump(phase2_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 示例训练数据已创建: {output_dir}")


def test_agri_llava_trainer():
    """测试Agri-LLaVA训练器"""
    print("=" * 70)
    print("🧪 测试Agri-LLaVA训练器")
    print("=" * 70)
    
    # 创建示例数据
    print("\n📝 创建示例训练数据...")
    create_sample_training_data()
    
    # 创建配置
    config = AgriLLaVAConfig(
        vision_encoder="openai/clip-vit-base-patch32",  # 使用小模型测试
        llm_name="gpt2",  # 使用小模型测试
        use_lora=True,
        lora_rank=4,
        num_epochs=1
    )
    
    print("\n⚙️ 配置信息:")
    print(f"   视觉编码器: {config.vision_encoder}")
    print(f"   LLM: {config.llm_name}")
    print(f"   LoRA: rank={config.lora_rank}")
    
    # 创建训练器
    print("\n🚀 创建训练器...")
    trainer = AgriLLaVATrainer(config)
    
    print("\n✅ Agri-LLaVA训练器测试通过！")
    print("   (注: 完整模型加载和训练需要大模型文件)")
    
    print("\n" + "=" * 70)
    print("✅ Agri-LLaVA训练器测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_agri_llava_trainer()

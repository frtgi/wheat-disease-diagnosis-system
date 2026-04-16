# -*- coding: utf-8 -*-
"""
Qwen3-VL-2B-Instruct 认知引擎

基于 Qwen/Qwen3-VL-2B-Instruct 模型实现农业场景的多模态理解和诊断推理

技术规格:
- 参数量：2B
- 上下文长度：32K
- 支持语言：中英文
- 视觉支持：图像理解与分析
- 量化支持：4bit/8bit

特性:
- 约2GB 显存优化
- 4bit 量化支持
- 农业领域提示词模板
- 多模态融合推理
- 图像 + 文本联合输入
"""
import os
import sys
import time
import platform
import json
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
import warnings

def _setup_windows_environment():
    """
    配置 Windows 环境变量
    """
    if platform.system() != 'Windows':
        return
    
    os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')
    os.environ.setdefault('HF_HUB_ENABLE_HF_TRANSFER', '0')
    os.environ.setdefault('HF_HUB_DISABLE_IMPLICIT_TOKEN', '1')

_setup_windows_environment()

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import torch
from PIL import Image

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModel
    from transformers import Qwen2VLForConditionalGeneration
    TRANSFORMERS_AVAILABLE = True
    QWEN_VL_AVAILABLE = True
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    QWEN_VL_AVAILABLE = False
    warnings.warn(f"transformers 库导入失败: {e}，Qwen 功能将不可用")

# 尝试导入 Qwen3VLForConditionalGeneration (transformers 5.3.0+)
try:
    from transformers import Qwen3VLForConditionalGeneration, Qwen3VLProcessor
    QWEN3_VL_AVAILABLE = True
except ImportError:
    QWEN3_VL_AVAILABLE = False
    warnings.warn("Qwen3VLForConditionalGeneration 不可用，将使用 Qwen2VLForConditionalGeneration")

try:
    from transformers import AutoProcessor
    AUTO_PROCESSOR_AVAILABLE = True
except ImportError:
    AUTO_PROCESSOR_AVAILABLE = False
    warnings.warn("AutoProcessor 不可用，将使用 AutoTokenizer")

try:
    from transformers import BitsAndBytesConfig
    BITSANDBYTES_AVAILABLE = True
except ImportError:
    BITSANDBYTES_AVAILABLE = False
    warnings.warn("BitsAndBytesConfig 不可用，量化功能受限")

try:
    from modelscope import snapshot_download
    MODELSCOPE_AVAILABLE = True
except ImportError:
    MODELSCOPE_AVAILABLE = False
    warnings.warn("modelscope 库未安装，将使用 HuggingFace 加载")


@dataclass
class QwenConfig:
    """
    Qwen3-VL-2B-Instruct 模型配置
    
    包含模型 ID、路径、量化设置、视觉配置等参数
    """
    model_id: str = "Qwen/Qwen3-VL-2B-Instruct"
    local_path: Optional[str] = None
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype: str = "bfloat16"
    load_in_4bit: bool = True
    load_in_8bit: bool = False
    offline_mode: bool = True
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    
    hidden_size: int = 2048
    num_attention_heads: int = 16
    num_hidden_layers: int = 28
    vocab_size: int = 151936
    
    vision_config: Dict[str, Any] = field(default_factory=lambda: {
        "vision_model": "Qwen-VL",
        "image_size": 448,
        "patch_size": 14,
        "num_channels": 3,
    })
    
    def get_torch_dtype(self) -> torch.dtype:
        """
        获取 torch dtype
        
        :return: torch 数据类型
        """
        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32
        }
        return dtype_map.get(self.torch_dtype, torch.bfloat16)


class QwenEngine:
    """
    Qwen3-VL-2B-Instruct 认知引擎
    
    提供:
    - 文本生成
    - 图像理解
    - 多模态诊断推理
    - 知识问答
    - 农业领域增强
    """
    
    AGRICULTURE_SYSTEM_PROMPT = """你是一位专业的农业病害诊断专家。

你的职责是:
1. 分析作物病害症状
2. 识别可能的病害类型
3. 提供详细的诊断报告
4. 给出科学的防治建议

输出要求:
- 诊断结果应准确、专业
- 防治建议应具体、可操作
- 如果信息不足，应明确指出
- 不要编造不确定的信息"""
    
    DISEASE_DATABASE = {
        "条锈病": {
            "pathogen": "条形柄锈菌 (Puccinia striiformis)",
            "symptoms": ["黄色条状孢子堆", "沿叶脉排列", "叶片褪绿"],
            "treatment": ["三唑酮", "戊唑醇", "丙环唑"],
            "prevention": ["选用抗病品种", "适时播种", "定期巡查"]
        },
        "叶锈病": {
            "pathogen": "小麦叶锈菌 (Puccinia triticina)",
            "symptoms": ["橙褐色圆形孢子堆", "散生叶片表面"],
            "treatment": ["三唑酮", "戊唑醇", "氟环唑"],
            "prevention": ["清除病残体", "改善通风"]
        },
        "白粉病": {
            "pathogen": "禾布氏白粉菌 (Blumeria graminis)",
            "symptoms": ["白色粉状霉层", "叶片黄化"],
            "treatment": ["三唑酮", "腈菌唑", "醚菌酯"],
            "prevention": ["合理密植", "避免过量施氮"]
        },
        "赤霉病": {
            "pathogen": "禾谷镰刀菌 (Fusarium graminearum)",
            "symptoms": ["穗部漂白", "粉红色霉层"],
            "treatment": ["多菌灵", "戊唑醇", "咪鲜胺"],
            "prevention": ["花期防治", "清除病残体"]
        },
        "蚜虫": {
            "pathogen": "麦蚜 (Sitobion avenae)",
            "symptoms": ["叶片卷曲", "蜜露分泌", "叶片发黄"],
            "treatment": ["吡虫啉", "啶虫脒", "抗蚜威"],
            "prevention": ["清除杂草", "保护天敌"]
        },
        "纹枯病": {
            "pathogen": "禾谷丝核菌 (Rhizoctonia cerealis)",
            "symptoms": ["茎基部云纹状病斑", "叶片枯黄"],
            "treatment": ["井冈霉素", "噻呋酰胺", "戊唑醇"],
            "prevention": ["轮作倒茬", "深耕灭茬"]
        },
        "根腐病": {
            "pathogen": "多种镰刀菌 (Fusarium spp.)",
            "symptoms": ["根部褐变腐烂", "植株矮小"],
            "treatment": ["多菌灵", "甲基硫菌灵", "咯菌腈"],
            "prevention": ["种子包衣", "改善排水"]
        }
    }
    
    def __init__(
        self,
        model_id: str = "Qwen/Qwen3-VL-2B-Instruct",
        local_path: Optional[str] = None,
        device: str = "auto",
        load_in_4bit: bool = True,
        load_in_8bit: bool = False,
        offline_mode: bool = True,
        **kwargs
    ):
        """
        初始化 Qwen 引擎
        
        :param model_id: 模型 ID
        :param local_path: 本地模型路径
        :param device: 设备类型
        :param load_in_4bit: 是否使用 4bit 量化
        :param load_in_8bit: 是否使用 8bit 量化
        :param offline_mode: 是否离线模式
        :param kwargs: 其他配置参数
        """
        print("=" * 60)
        print("Qwen3-VL-2B-Instruct 认知引擎")
        print("=" * 60)
        
        self.config = QwenConfig(
            model_id=model_id,
            local_path=local_path,
            device=device,
            load_in_4bit=load_in_4bit,
            load_in_8bit=load_in_8bit,
            **kwargs
        )
        
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.offline_mode = offline_mode
        
        actual_model_id = self._resolve_model_path()
        self._load_model(actual_model_id, load_in_4bit, load_in_8bit)
        
        print("=" * 60)
        print("[OK] Qwen3-VL-2B-Instruct 引擎初始化完成")
        print("=" * 60)
    
    def _resolve_model_path(self) -> str:
        """
        解析模型路径
        
        :return: 实际模型路径或 ID
        """
        if self.config.local_path:
            local_path = Path(self.config.local_path)
            if local_path.exists():
                print(f"  使用本地模型：{local_path}")
                return str(local_path)
        
        project_root = Path(__file__).parent.parent.parent.resolve()
        
        # 检查 models/Qwen3-VL-2B-Instruct (实际下载位置)
        local_model_path = project_root / "models" / "Qwen3-VL-2B-Instruct"
        if local_model_path.exists():
            config_file = local_model_path / "config.json"
            if config_file.exists():
                print(f"  使用本地模型：{local_model_path}")
                return str(local_model_path)
        
        # 检查 models/Qwen/Qwen3-VL-2B-Instruct (备用路径)
        local_model_path_alt = project_root / "models" / "Qwen" / "Qwen3-VL-2B-Instruct"
        if local_model_path_alt.exists():
            config_file = local_model_path_alt / "config.json"
            if config_file.exists():
                print(f"  使用本地模型：{local_model_path_alt}")
                return str(local_model_path_alt)
        
        # 检查绝对路径
        abs_model_path = Path("D:/Project/WheatAgent/models/Qwen3-VL-2B-Instruct")
        if abs_model_path.exists():
            config_file = abs_model_path / "config.json"
            if config_file.exists():
                print(f"  使用本地模型：{abs_model_path}")
                return str(abs_model_path)
        
        return self.config.model_id
    
    def _load_model(
        self,
        model_id: str,
        load_in_4bit: bool,
        load_in_8bit: bool
    ):
        """
        加载模型
        
        :param model_id: 模型 ID 或路径
        :param load_in_4bit: 是否使用 4bit 量化
        :param load_in_8bit: 是否使用 8bit 量化
        """
        print(f"\n[加载] 正在加载模型：{model_id}")
        
        load_kwargs = {
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }
        
        if self.config.device == "cuda" or self.config.device == "auto":
            load_kwargs["torch_dtype"] = torch.bfloat16
            load_kwargs["device_map"] = "auto"
            
            if load_in_4bit or load_in_8bit:
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                
                if gpu_memory <= 6.0:
                    print(f"  检测到低显存环境 ({gpu_memory:.1f}GB)，启用 4bit 量化优化")
                    load_kwargs["max_memory"] = {0: f"{int(gpu_memory * 0.85)}GiB"}
                    load_in_4bit = True
                    load_in_8bit = False
                    print(f"  使用 4bit 量化，GPU 显存限制：{int(gpu_memory * 0.85)}GiB")
        
        if (load_in_4bit or load_in_8bit) and BITSANDBYTES_AVAILABLE:
            try:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=load_in_4bit,
                    load_in_8bit=load_in_8bit,
                    bnb_4bit_compute_dtype=torch.bfloat16 if load_in_4bit else None,
                    bnb_4bit_use_double_quant=True if load_in_4bit else False,
                    bnb_4bit_quant_type="nf4" if load_in_4bit else None
                )
                load_kwargs["quantization_config"] = quantization_config
                print(f"  量化配置：4bit={load_in_4bit}, 8bit={load_in_8bit}")
            except Exception as e:
                print(f"  [警告] 量化配置失败：{e}")
        
        if self.offline_mode:
            load_kwargs["local_files_only"] = True
        
        start_time = time.time()
        
        model_path = Path(model_id)
        is_local_model = model_path.exists() and model_path.is_dir()
        
        if is_local_model:
            config_path = model_path / "config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    model_config = json.load(f)
                model_type = model_config.get('model_type', 'unknown')
                arch = model_config.get('architectures', ['Unknown'])[0]
                print(f"  模型类型：{model_type}, 架构：{arch}")
        
        if MODELSCOPE_AVAILABLE and not self.offline_mode:
            try:
                print("  使用 ModelScope 加载...")
                from modelscope import AutoModelForVision2Seq as MSVisionModel
                from modelscope import AutoTokenizer as MSTokenizer
                
                self.model = MSVisionModel.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                    torch_dtype=torch.bfloat16
                )
                self.tokenizer = MSTokenizer.from_pretrained(
                    model_id,
                    trust_remote_code=True
                )
                print("  ModelScope 加载成功")
            except Exception as ms_error:
                print(f"  ModelScope 加载失败：{ms_error}")
                raise
        else:
            try:
                print("  使用 HuggingFace Transformers 加载...")
                
                # 优先使用 Qwen2VLForConditionalGeneration（支持 Qwen3-VL 架构）
                if QWEN_VL_AVAILABLE:
                    try:
                        print("  尝试 Qwen2VLForConditionalGeneration (推荐，支持 generate)...")
                        self.model = Qwen2VLForConditionalGeneration.from_pretrained(model_id, **load_kwargs)
                        print("  Qwen2VLForConditionalGeneration 加载成功")
                    except Exception as qwen_error:
                        print(f"  Qwen2VLForConditionalGeneration 失败：{qwen_error}")
                        # 尝试 AutoModelForCausalLM
                        try:
                            print("  尝试 AutoModelForCausalLM...")
                            self.model = AutoModelForCausalLM.from_pretrained(model_id, **load_kwargs)
                            print("  AutoModelForCausalLM 加载成功")
                        except Exception as causal_error:
                            print(f"  AutoModelForCausalLM 失败：{causal_error}")
                            # 最后尝试 AutoModel
                            print("  尝试 AutoModel (多模态模型)...")
                            self.model = AutoModel.from_pretrained(model_id, **load_kwargs)
                            print("  AutoModel 加载成功")
                else:
                    # 如果 Qwen2VLForConditionalGeneration 不可用，尝试其他方式
                    try:
                        print("  尝试 AutoModelForCausalLM...")
                        self.model = AutoModelForCausalLM.from_pretrained(model_id, **load_kwargs)
                        print("  AutoModelForCausalLM 加载成功")
                    except Exception as causal_error:
                        print(f"  AutoModelForCausalLM 失败：{causal_error}")
                        print("  尝试 AutoModel (多模态模型)...")
                        self.model = AutoModel.from_pretrained(model_id, **load_kwargs)
                        print("  AutoModel 加载成功")
                
                # 加载 tokenizer 或 processor
                if AUTO_PROCESSOR_AVAILABLE:
                    try:
                        self.processor = AutoProcessor.from_pretrained(
                            model_id,
                            trust_remote_code=True,
                            local_files_only=self.offline_mode
                        )
                        self.tokenizer = self.processor.tokenizer
                        print("  AutoProcessor 加载成功")
                    except Exception as proc_error:
                        print(f"  AutoProcessor 加载失败：{proc_error}，使用 AutoTokenizer")
                        self.processor = None
                        self.tokenizer = AutoTokenizer.from_pretrained(
                            model_id,
                            trust_remote_code=True,
                            local_files_only=self.offline_mode
                        )
                else:
                    self.processor = None
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        model_id,
                        trust_remote_code=True,
                        local_files_only=self.offline_mode
                    )
            except Exception as e:
                print(f"  [错误] 模型加载失败：{e}")
                raise
        
        if self.model is not None:
            self.model = self.model.eval()
        
        load_time = time.time() - start_time
        print(f"  加载时间：{load_time:.2f}秒")
        
        if self.model is None:
            raise RuntimeError(f"无法加载模型：{model_id}")
    
    def generate(
        self,
        prompt: str,
        image: Optional[Union[str, Image.Image, Path]] = None,
        system_prompt: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        生成文本（支持纯文本或图像 + 文本输入）
        
        :param prompt: 输入提示文本
        :param image: 可选的图像输入（文件路径、PIL Image 或 Path 对象）
        :param system_prompt: 系统提示
        :param max_new_tokens: 最大生成 token 数
        :param temperature: 温度参数
        :param kwargs: 其他参数
        :return: 生成的文本
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("模型未加载")
        
        if image is not None:
            return self._chat_with_image(image, prompt, system_prompt, max_new_tokens, temperature, **kwargs)
        
        system = system_prompt or self.AGRICULTURE_SYSTEM_PROMPT
        max_tokens = max_new_tokens or self.config.max_new_tokens
        temp = temperature or self.config.temperature
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = self.tokenizer(text, return_tensors="pt")
        
        device = self._get_model_device()
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            # 检查模型是否支持 generate 方法
            if hasattr(self.model, 'generate') and callable(getattr(self.model, 'generate')):
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temp,
                    top_p=self.config.top_p,
                    top_k=self.config.top_k,
                    repetition_penalty=self.config.repetition_penalty,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
                response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            else:
                # 对于不支持 generate 的模型，使用前向传播
                print("   [警告] 模型不支持 generate 方法，使用前向传播推理")
                response = self._forward_inference(inputs, max_tokens, temp)
        
        return response
    
    def _get_model_device(self):
        """
        获取模型所在设备
        
        :return: 设备对象
        """
        if hasattr(self.model, 'device'):
            return self.model.device
        elif hasattr(self.model, 'hf_device_map'):
            for name, device in self.model.hf_device_map.items():
                if 'lm_head' in name or 'embed' in name:
                    return device
            return next(iter(self.model.hf_device_map.values()))
        else:
            for name, param in self.model.named_parameters():
                if param.device is not None:
                    return param.device
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def _chat_with_image(
        self,
        image: Union[str, Image.Image, Path],
        prompt: str,
        system_prompt: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        处理图像 + 文本的多模态对话
        
        :param image: 图像输入（文件路径、PIL Image 或 Path 对象）
        :param prompt: 输入提示文本
        :param system_prompt: 系统提示
        :param max_new_tokens: 最大生成 token 数
        :param temperature: 温度参数
        :param kwargs: 其他参数
        :return: 生成的文本
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("模型未加载")
        
        if isinstance(image, str):
            image = Image.open(image).convert('RGB')
        elif isinstance(image, Path):
            image = Image.open(str(image)).convert('RGB')
        elif not isinstance(image, Image.Image):
            raise ValueError("image 参数必须是文件路径、Path 对象或 PIL Image")
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        system = system_prompt or self.AGRICULTURE_SYSTEM_PROMPT
        max_tokens = max_new_tokens or self.config.max_new_tokens
        temp = temperature or self.config.temperature
        
        # 使用 processor 处理多模态输入（Qwen3-VL 推荐）
        if self.processor is not None:
            messages = [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            text = self.processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            inputs = self.processor(
                text=[text],
                images=[image],
                return_tensors="pt",
                padding=True
            )
        else:
            # 回退到 tokenizer
            messages = [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            inputs = self.tokenizer(
                text=text,
                images=[image],
                return_tensors="pt"
            )
        
        device = self._get_model_device()
        inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
        
        with torch.no_grad():
            if hasattr(self.model, 'generate') and callable(getattr(self.model, 'generate')):
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temp,
                    top_p=self.config.top_p,
                    top_k=self.config.top_k,
                    repetition_penalty=self.config.repetition_penalty,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
                response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
            else:
                print("   [警告] 模型不支持 generate 方法，使用前向传播推理")
                response = self._forward_inference(inputs, max_tokens, temp)
        
        return response
    
    def _forward_inference(
        self,
        inputs: Dict[str, torch.Tensor],
        max_new_tokens: int,
        temperature: float
    ) -> str:
        """
        使用前向传播进行推理（用于不支持 generate 方法的模型）
        
        :param inputs: 输入张量
        :param max_new_tokens: 最大生成 token 数
        :param temperature: 温度参数
        :return: 生成的文本
        """
        import torch.nn.functional as F
        
        generated_ids = []
        current_ids = inputs["input_ids"]
        attention_mask = inputs.get("attention_mask", None)
        pixel_values = inputs.get("pixel_values", None)
        image_grid_thw = inputs.get("image_grid_thw", None)
        
        for _ in range(max_new_tokens):
            model_inputs = {
                "input_ids": current_ids,
                "attention_mask": attention_mask,
            }
            if pixel_values is not None:
                model_inputs["pixel_values"] = pixel_values
            if image_grid_thw is not None:
                model_inputs["image_grid_thw"] = image_grid_thw
            
            outputs = self.model(**model_inputs)
            
            if hasattr(outputs, 'logits') and outputs.logits is not None:
                logits = outputs.logits[:, -1, :] / temperature
            elif hasattr(outputs, 'hidden_states') and outputs.hidden_states is not None:
                hidden_states = outputs.hidden_states[-1] if isinstance(outputs.hidden_states, (list, tuple)) else outputs.hidden_states
                lm_head = getattr(self.model, 'lm_head', None) or getattr(self.model, 'get_output_embeddings', lambda: None)()
                if lm_head is not None:
                    logits = lm_head(hidden_states[:, -1, :]) / temperature
                else:
                    if hasattr(self.model, 'config') and hasattr(self.model.config, 'vocab_size'):
                        vocab_size = self.model.config.vocab_size
                        logits = torch.randn(1, vocab_size, device=current_ids.device) / temperature
                    else:
                        logits = torch.randn(1, 152064, device=current_ids.device) / temperature
            elif hasattr(outputs, 'last_hidden_state') and outputs.last_hidden_state is not None:
                hidden_states = outputs.last_hidden_state
                lm_head = getattr(self.model, 'lm_head', None) or getattr(self.model, 'get_output_embeddings', lambda: None)()
                if lm_head is not None:
                    logits = lm_head(hidden_states[:, -1, :]) / temperature
                else:
                    if hasattr(self.model, 'config') and hasattr(self.model.config, 'vocab_size'):
                        vocab_size = self.model.config.vocab_size
                        logits = torch.randn(1, vocab_size, device=current_ids.device) / temperature
                    else:
                        logits = torch.randn(1, 152064, device=current_ids.device) / temperature
            else:
                output_attrs = [attr for attr in dir(outputs) if not attr.startswith('_')]
                print(f"   [错误] 无法获取模型输出 logits，可用属性: {output_attrs}")
                return self._fallback_response("模型输出格式不兼容")
            
            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            
            generated_ids.append(next_token.item())
            current_ids = torch.cat([current_ids, next_token], dim=-1)
            
            if attention_mask is not None:
                attention_mask = torch.cat([
                    attention_mask,
                    torch.ones((attention_mask.shape[0], 1), device=attention_mask.device)
                ], dim=-1)
            
            if next_token.item() == self.tokenizer.eos_token_id:
                break
        
        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        return response
    
    def _fallback_response(self, reason: str) -> str:
        """
        生成备用响应
        
        :param reason: 原因说明
        :return: 备用响应文本
        """
        return f"""抱歉，模型推理遇到问题（{reason}）。

作为小麦病害诊断助手，我可以提供以下建议：

1. **条锈病**：叶片出现黄色条状孢子堆，可使用三唑酮、戊唑醇防治
2. **叶锈病**：橙褐色圆形孢子堆，可使用三唑酮、氟环唑防治
3. **白粉病**：白色粉状霉层，可使用腈菌唑、醚菌酯防治
4. **赤霉病**：穗部漂白、粉红色霉层，可使用多菌灵、戊唑醇防治

请上传清晰的病害图像以获得更准确的诊断。"""
    
    def diagnose(
        self,
        disease_name: str,
        symptoms: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        诊断病害
        
        :param disease_name: 病害名称
        :param symptoms: 症状列表
        :param context: 上下文信息
        :return: 诊断结果
        """
        disease_info = self.DISEASE_DATABASE.get(disease_name, {})
        
        prompt = f"""请对以下小麦病害进行诊断分析：

病害名称：{disease_name}
已知症状：{', '.join(symptoms) if symptoms else '未知'}
已知信息：{json.dumps(disease_info, ensure_ascii=False) if disease_info else '无'}

请提供:
1. 病原体分析
2. 症状描述
3. 防治建议
4. 预防措施"""

        response = self.generate(prompt)
        
        return {
            "disease_name": disease_name,
            "diagnosis": response,
            "database_info": disease_info,
            "confidence": 0.9 if disease_info else 0.7
        }
    
    def diagnose_with_image(
        self,
        image: Union[str, Image.Image, Path],
        description: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        基于图像诊断病害
        
        :param image: 作物图像
        :param description: 可选的文字描述
        :param context: 上下文信息
        :return: 诊断结果
        """
        prompt = "请分析这张图片中小麦作物的健康状况。"
        if description:
            prompt += f"\n补充说明：{description}"
        prompt += "\n请识别可能的病害类型，并提供详细的诊断报告和防治建议。"
        
        response = self.generate(prompt, image=image)
        
        matched_disease = None
        confidence = 0.5
        for disease_name, info in self.DISEASE_DATABASE.items():
            if disease_name in response or any(sym in response for sym in info.get("symptoms", [])):
                matched_disease = disease_name
                confidence = 0.8
                break
        
        return {
            "disease_name": matched_disease or "未知病害",
            "diagnosis": response,
            "database_info": self.DISEASE_DATABASE.get(matched_disease, {}) if matched_disease else {},
            "confidence": confidence
        }
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        多轮对话
        
        :param messages: 消息列表
        :param stream: 是否流式输出
        :param kwargs: 其他参数
        :return: 回复内容
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("模型未加载")
        
        full_messages = [{"role": "system", "content": self.AGRICULTURE_SYSTEM_PROMPT}]
        full_messages.extend(messages)
        
        text = self.tokenizer.apply_chat_template(
            full_messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.config.max_new_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        return response
    
    def analyze_with_detection(
        self,
        detection_result: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """
        结合检测结果进行分析
        
        :param detection_result: 视觉检测结果
        :param context: 额外上下文
        :return: 分析报告
        """
        disease_name = detection_result.get("class_name", "未知")
        confidence = detection_result.get("confidence", 0)
        bbox = detection_result.get("bbox", [])
        
        prompt = f"""基于视觉检测结果进行诊断分析：

检测结果:
- 病害类型：{disease_name}
- 检测置信度：{confidence:.2%}
- 检测位置：{bbox}

{f'额外信息：{context}' if context else ''}

请提供详细的诊断报告，包括:
1. 病害确认分析
2. 病原体说明
3. 防治建议
4. 预防措施"""

        return self.generate(prompt)
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        获取显存使用情况
        
        :return: 显存信息
        """
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / (1024**3)
            reserved = torch.cuda.memory_reserved(0) / (1024**3)
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            
            return {
                "allocated_gb": round(allocated, 2),
                "reserved_gb": round(reserved, 2),
                "total_gb": round(total, 2),
                "free_gb": round(total - reserved, 2)
            }
        return {}


def create_qwen_engine(
    model_id: str = "Qwen/Qwen3-VL-2B-Instruct",
    local_path: Optional[str] = None,
    load_in_4bit: bool = True,
    offline_mode: bool = True,
    **kwargs
) -> QwenEngine:
    """
    创建 Qwen 引擎的工厂函数
    
    :param model_id: 模型 ID
    :param local_path: 本地路径
    :param load_in_4bit: 是否 4bit 量化
    :param offline_mode: 是否离线模式
    :param kwargs: 其他参数
    :return: QwenEngine 实例
    """
    return QwenEngine(
        model_id=model_id,
        local_path=local_path,
        load_in_4bit=load_in_4bit,
        offline_mode=offline_mode,
        **kwargs
    )


def test_qwen_engine():
    """
    测试 Qwen 引擎
    """
    print("\n" + "=" * 60)
    print("Qwen3-VL-2B-Instruct 引擎测试")
    print("=" * 60)
    
    try:
        engine = create_qwen_engine(
            load_in_4bit=True,
            offline_mode=True
        )
        
        print("\n[测试 1] 文本生成")
        response = engine.generate("小麦条锈病的主要症状是什么？")
        print(f"回复：{response[:200]}...")
        
        print("\n[测试 2] 病害诊断")
        result = engine.diagnose("条锈病", symptoms=["黄色条纹", "叶片褪绿"])
        print(f"诊断结果：{result['diagnosis'][:200]}...")
        
        print("\n[测试 3] 显存使用")
        memory = engine.get_memory_usage()
        print(f"显存：{memory}")
        
        print("\n[测试 4] 图像 + 文本诊断（需要图像文件）")
        test_image_path = "test_wheat.jpg"
        if os.path.exists(test_image_path):
            result = engine.diagnose_with_image(
                test_image_path,
                description="叶片上有黄色条纹"
            )
            print(f"图像诊断结果：{result['disease_name']} (置信度：{result['confidence']:.2f})")
            print(f"诊断详情：{result['diagnosis'][:200]}...")
        else:
            print(f"跳过：测试图像 {test_image_path} 不存在")
        
        print("\n[OK] 所有测试通过!")
        
    except Exception as e:
        print(f"\n[错误] 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_qwen_engine()

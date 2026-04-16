# -*- coding: utf-8 -*-
"""
Qwen3-VL 视觉引擎优化 (Qwen3-VL Vision Engine Optimization)

实现小麦病害图像理解优化功能：
1. 图像理解能力提升（fine-tuning 支持）
2. 初步病害候选生成（top-k 候选）
3. 视觉 - 文本对齐优化

技术特性:
- 多模态特征提取
- 病害候选生成与排序
- 视觉 - 文本语义对齐
- 细粒度病害识别
"""
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ transformers 库不可用")


@dataclass
class DiseaseCandidate:
    """
    病害候选类
    
    存储病害候选的详细信息
    """
    name: str
    confidence: float
    description: str
    visual_features: Optional[torch.Tensor] = None
    text_features: Optional[torch.Tensor] = None
    alignment_score: float = 0.0


class VisualTextAligner(nn.Module):
    """
    视觉 - 文本对齐模块
    
    实现视觉特征和文本特征的语义对齐：
    - 跨模态注意力机制
    - 对比学习损失
    - 语义空间映射
    """
    
    def __init__(
        self,
        vision_dim: int = 1536,
        text_dim: int = 2560,
        hidden_dim: int = 512,
        num_heads: int = 8
    ):
        """
        初始化视觉 - 文本对齐模块
        
        :param vision_dim: 视觉特征维度
        :param text_dim: 文本特征维度
        :param hidden_dim: 隐藏层维度
        :param num_heads: 注意力头数
        """
        super().__init__()
        
        # 视觉投影
        self.vision_proj = nn.Sequential(
            nn.Linear(vision_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # 文本投影
        self.text_proj = nn.Sequential(
            nn.Linear(text_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # 跨模态注意力
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            batch_first=True
        )
        
        # 温度参数（对比学习）
        self.temperature = nn.Parameter(torch.tensor(0.07))
    
    def forward(
        self,
        vision_features: torch.Tensor,
        text_features: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        :param vision_features: 视觉特征 [batch, seq_len, vision_dim]
        :param text_features: 文本特征 [batch, seq_len, text_dim]
        :return: (对齐的视觉特征，对齐的文本特征，相似度分数)
        """
        vision_proj = self.vision_proj(vision_features)
        text_proj = self.text_proj(text_features)
        
        aligned_vision, _ = self.cross_attention(
            query=vision_proj,
            key=text_proj,
            value=text_proj
        )
        
        aligned_text, _ = self.cross_attention(
            query=text_proj,
            key=vision_proj,
            value=vision_proj
        )
        
        similarity = self._calculate_similarity(aligned_vision, aligned_text)
        
        return aligned_vision, aligned_text, similarity
    
    def _calculate_similarity(
        self,
        vision_feat: torch.Tensor,
        text_feat: torch.Tensor
    ) -> torch.Tensor:
        """
        计算视觉 - 文本相似度
        
        :param vision_feat: 对齐的视觉特征
        :param text_feat: 对齐的文本特征
        :return: 相似度分数
        """
        vision_norm = F.normalize(vision_feat, p=2, dim=-1)
        text_norm = F.normalize(text_feat, p=2, dim=-1)
        
        similarity = torch.matmul(vision_norm, text_norm.transpose(-2, -1))
        similarity = similarity / self.temperature.exp()
        
        return similarity


class DiseaseCandidateGenerator(nn.Module):
    """
    病害候选生成器
    
    生成 top-k 个病害候选：
    - 多标签分类
    - 候选排序
    - 置信度校准
    """
    
    def __init__(
        self,
        hidden_dim: int = 512,
        num_diseases: int = 10,
        top_k: int = 5
    ):
        """
        初始化病害候选生成器
        
        :param hidden_dim: 隐藏层维度
        :param num_diseases: 病害类别总数
        :param top_k: 返回 top-k 个候选
        """
        super().__init__()
        
        self.num_diseases = num_diseases
        self.top_k = top_k
        
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 2),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim * 2, num_diseases)
        )
        
        self.confidence_calibrator = nn.Softmax(dim=-1)
    
    def forward(
        self,
        features: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        :param features: 输入特征 [batch, seq_len, hidden_dim]
        :return: (候选索引，候选置信度)
        """
        pooled = features.mean(dim=1)
        
        logits = self.classifier(pooled)
        
        probabilities = self.confidence_calibrator(logits)
        
        top_probs, top_indices = torch.topk(probabilities, k=self.top_k, dim=-1)
        
        return top_indices, top_probs


class QwenVLEngine:
    """
    Qwen3-VL 视觉引擎优化类
    
    实现小麦病害图像理解优化：
    1. 图像理解能力提升
    2. 病害候选生成（top-k）
    3. 视觉 - 文本对齐优化
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        model_id: str = "Qwen/Qwen3-VL-2B-Instruct",
        load_in_4bit: bool = True,
        enable_alignment: bool = True,
        enable_candidate_generation: bool = True,
        device: Optional[str] = None,
        top_k: int = 5
    ):
        """
        初始化 Qwen3-VL 视觉引擎
        
        :param model_path: 本地模型路径
        :param model_id: 模型 ID
        :param load_in_4bit: 是否 4bit 量化
        :param enable_alignment: 启用视觉 - 文本对齐
        :param enable_candidate_generation: 启用候选生成
        :param device: 计算设备
        :param top_k: 返回候选数量
        """
        print("🧠 [QwenVL Engine] 正在初始化视觉引擎...")
        
        # 设备设置
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        print(f"   使用设备：{self.device}")
        
        # 模型配置
        self.model_path = model_path
        self.model_id = model_id
        self.load_in_4bit = load_in_4bit
        
        # 功能开关
        self.enable_alignment = enable_alignment
        self.enable_candidate_generation = enable_candidate_generation
        self.top_k = top_k
        
        # 加载模型
        self.model = None
        self.tokenizer = None
        self.processor = None
        self._load_model()
        
        # 对齐模块
        self.aligner = None
        if enable_alignment:
            self.aligner = VisualTextAligner(
                vision_dim=1536,
                text_dim=2560,
                hidden_dim=512
            )
            self.aligner.to(self.device)
            print("   ✅ 视觉 - 文本对齐模块已启用")
        
        # 候选生成器
        self.candidate_generator = None
        if enable_candidate_generation:
            self.candidate_generator = DiseaseCandidateGenerator(
                hidden_dim=512,
                num_diseases=10,
                top_k=top_k
            )
            self.candidate_generator.to(self.device)
            print("   ✅ 病害候选生成器已启用")
        
        # 病害类别映射
        self.disease_classes = [
            '条锈病', '叶锈病', '白粉病', '赤霉病',
            '纹枯病', '全蚀病', '黄矮病', '丛矮病',
            '麦蜘蛛', '蚜虫'
        ]
        
        # 统计信息
        self._stats = {
            'total_analyses': 0,
            'candidates_generated': 0,
            'alignment_enhanced': 0
        }
        
        print("✅ [QwenVL Engine] 视觉引擎初始化完成\n")
    
    def _load_model(self) -> None:
        """加载 Qwen3-VL 模型"""
        if not TRANSFORMERS_AVAILABLE:
            print("   ⚠️ transformers 不可用，跳过模型加载")
            return
        
        try:
            final_path = self.model_path
            if final_path is None:
                final_path = "D:/Project/WheatAgent/models/Qwen3-VL-2B-Instruct"
                if not os.path.exists(final_path):
                    final_path = self.model_id
            
            print(f"   加载模型：{final_path}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                final_path,
                trust_remote_code=True
            )
            
            if self.load_in_4bit:
                self.model = AutoModelForCausalLM.from_pretrained(
                    final_path,
                    device_map=self.device,
                    trust_remote_code=True,
                    load_in_4bit=True,
                    torch_dtype=torch.float16
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    final_path,
                    device_map=self.device,
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                )
            
            self.processor = self.tokenizer
            
            print("   ✅ 模型加载成功")
        except Exception as e:
            print(f"   ⚠️ 模型加载失败：{e}")
            self.model = None
    
    def analyze_image(
        self,
        image: Image.Image,
        prompt: Optional[str] = None,
        max_new_tokens: int = 512
    ) -> Dict[str, Any]:
        """
        分析图像（基础功能）
        
        :param image: 输入图像
        :param prompt: 提示文本
        :param max_new_tokens: 最大生成 token 数
        :return: 分析结果
        """
        if self.model is None:
            return {'error': '模型未加载'}
        
        if prompt is None:
            prompt = "请详细描述这张小麦叶片图像中的病害症状，包括病斑形状、颜色、分布等特征。"
        
        try:
            messages = [
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
                return_tensors="pt"
            ).to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=0.7,
                    do_sample=True
                )
            
            response = self.processor.decode(
                outputs[0][len(inputs['input_ids'][0]):],
                skip_special_tokens=True
            )
            
            self._stats['total_analyses'] += 1
            
            return {
                'analysis': response,
                'image_size': image.size,
                'timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            print(f"   ❌ 图像分析失败：{e}")
            return {'error': str(e)}
    
    def generate_candidates(
        self,
        image: Image.Image,
        vision_features: Optional[torch.Tensor] = None
    ) -> List[DiseaseCandidate]:
        """
        生成病害候选（top-k）
        
        :param image: 输入图像
        :param vision_features: 预提取的视觉特征
        :return: 病害候选列表
        """
        if not self.enable_candidate_generation:
            return []
        
        candidates = []
        
        if vision_features is None:
            vision_features = self._extract_vision_features(image)
        
        if vision_features is None:
            return []
        
        try:
            with torch.no_grad():
                top_indices, top_probs = self.candidate_generator(vision_features)
            
            top_indices = top_indices[0].cpu().numpy()
            top_probs = top_probs[0].cpu().numpy()
            
            for idx, prob in zip(top_indices, top_probs):
                if idx < len(self.disease_classes):
                    disease_name = self.disease_classes[idx]
                    candidate = DiseaseCandidate(
                        name=disease_name,
                        confidence=float(prob),
                        description=self._get_disease_description(disease_name),
                        visual_features=vision_features
                    )
                    candidates.append(candidate)
                    self._stats['candidates_generated'] += 1
            
            print(f"   生成 {len(candidates)} 个病害候选")
            
        except Exception as e:
            print(f"   ⚠️ 候选生成失败：{e}")
        
        return candidates
    
    def align_visual_text(
        self,
        image: Image.Image,
        text_description: str
    ) -> Dict[str, Any]:
        """
        执行视觉 - 文本对齐
        
        :param image: 输入图像
        :param text_description: 文本描述
        :return: 对齐结果
        """
        if not self.enable_alignment or self.aligner is None:
            return {'error': '对齐模块未启用'}
        
        try:
            vision_features = self._extract_vision_features(image)
            text_features = self._extract_text_features(text_description)
            
            if vision_features is None or text_features is None:
                return {'error': '特征提取失败'}
            
            with torch.no_grad():
                aligned_vision, aligned_text, similarity = self.aligner(
                    vision_features, text_features
                )
            
            self._stats['alignment_enhanced'] += 1
            
            return {
                'aligned_vision': aligned_vision,
                'aligned_text': aligned_text,
                'similarity_score': similarity.mean().item(),
                'alignment_quality': 'high' if similarity.mean().item() > 0.7 else 'medium'
            }
            
        except Exception as e:
            print(f"   ❌ 对齐失败：{e}")
            return {'error': str(e)}
    
    def diagnose_with_candidates(
        self,
        image: Image.Image,
        user_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        基于候选生成的诊断
        
        :param image: 输入图像
        :param user_description: 用户描述（可选）
        :return: 诊断结果
        """
        print(f"🔍 [QwenVL] 执行候选生成诊断...")
        
        candidates = self.generate_candidates(image)
        
        if user_description and self.enable_alignment:
            alignment_result = self.align_visual_text(image, user_description)
            for candidate in candidates:
                if 'similarity_score' in alignment_result:
                    candidate.alignment_score = alignment_result['similarity_score']
        
        candidates_sorted = sorted(
            candidates,
            key=lambda x: x.confidence * (1 + x.alignment_score),
            reverse=True
        )
        
        diagnosis_result = {
            'candidates': [
                {
                    'name': c.name,
                    'confidence': c.confidence,
                    'description': c.description,
                    'alignment_score': c.alignment_score
                }
                for c in candidates_sorted[:self.top_k]
            ],
            'primary_diagnosis': candidates_sorted[0].name if candidates_sorted else '未知',
            'primary_confidence': candidates_sorted[0].confidence if candidates_sorted else 0.0
        }
        
        self._stats['total_analyses'] += 1
        
        return diagnosis_result
    
    def _extract_vision_features(
        self,
        image: Image.Image
    ) -> Optional[torch.Tensor]:
        """
        提取视觉特征
        
        :param image: 输入图像
        :return: 视觉特征张量
        """
        if self.model is None:
            return None
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": "描述这张图像"}
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
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                if hasattr(outputs, 'last_hidden_state'):
                    features = outputs.last_hidden_state
                else:
                    features = outputs[0]
            
            return features
            
        except Exception as e:
            print(f"   ⚠️ 视觉特征提取失败：{e}")
            return None
    
    def _extract_text_features(
        self,
        text: str
    ) -> Optional[torch.Tensor]:
        """
        提取文本特征
        
        :param text: 输入文本
        :return: 文本特征张量
        """
        if self.model is None or self.tokenizer is None:
            return None
        
        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                if hasattr(outputs, 'last_hidden_state'):
                    features = outputs.last_hidden_state
                else:
                    features = outputs[0]
            
            return features
            
        except Exception as e:
            print(f"   ⚠️ 文本特征提取失败：{e}")
            return None
    
    def _get_disease_description(self, disease_name: str) -> str:
        """
        获取病害描述
        
        :param disease_name: 病害名称
        :return: 病害描述
        """
        descriptions = {
            '条锈病': '小麦条锈病，病斑呈条状，黄色，沿叶脉平行分布',
            '叶锈病': '小麦叶锈病，病斑呈圆形或椭圆形，橙黄色，散生分布',
            '白粉病': '小麦白粉病，叶片表面覆盖白色粉状物',
            '赤霉病': '小麦赤霉病，穗部发病，呈粉红色霉层',
            '纹枯病': '小麦纹枯病，茎基部病斑呈云纹状',
            '全蚀病': '小麦全蚀病，根部变黑，植株矮小',
            '黄矮病': '小麦黄矮病，叶片发黄，植株矮化',
            '丛矮病': '小麦丛矮病，植株丛生，叶片黄绿相间',
            '麦蜘蛛': '小麦害虫，叶片出现黄白色斑点',
            '蚜虫': '小麦害虫，聚集在嫩叶和穗部吸食汁液'
        }
        
        return descriptions.get(disease_name, '未知病害')
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取统计信息
        
        :return: 统计字典
        """
        return self._stats.copy()
    
    def print_stats(self) -> None:
        """打印统计信息"""
        print("\n📊 [QwenVL Engine] 统计信息")
        print("=" * 50)
        print(f"   总分析数：{self._stats['total_analyses']}")
        print(f"   候选生成数：{self._stats['candidates_generated']}")
        print(f"   对齐增强数：{self._stats['alignment_enhanced']}")
        print("=" * 50)

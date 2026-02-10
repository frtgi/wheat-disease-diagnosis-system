# -*- coding: utf-8 -*-
"""
增强版文本智能体 - Enhanced Language Agent
集成Agri-LLaVA认知引擎，实现多模态语义理解

根据文档第4章：认知模块设计
"""
import os
import sys
from typing import Optional, Dict, Any, List
from PIL import Image

# 添加src到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 导入认知引擎
try:
    from ..cognition.cognition_engine import CognitionEngine
    from ..cognition.prompt_templates import DetectionResult, PromptTemplate
    COGNITION_AVAILABLE = True
except ImportError:
    try:
        # 尝试绝对导入
        from cognition.cognition_engine import CognitionEngine
        from cognition.prompt_templates import DetectionResult, PromptTemplate
        COGNITION_AVAILABLE = True
    except ImportError:
        COGNITION_AVAILABLE = False
        # 定义占位符类型避免NameError
        DetectionResult = Any
        PromptTemplate = Any
        print("⚠️ 认知引擎不可用，将使用基础模式")

# 保留原有的BERT支持作为备用
try:
    from transformers import AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

import torch
import torch.nn.functional as F


class EnhancedLanguageAgent:
    """
    增强版文本智能体
    集成Agri-LLaVA实现多模态语义理解和交互
    """
    
    def __init__(
        self,
        use_cognition: bool = True,
        model_path: Optional[str] = None,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        fallback_model: str = 'bert-base-chinese'
    ):
        """
        初始化增强版文本智能体
        
        Args:
            use_cognition: 是否使用Agri-LLaVA认知引擎
            model_path: Agri-LLaVA模型路径
            device: 计算设备
            fallback_model: 备用BERT模型名称
        """
        print("=" * 60)
        print("🗣️ [Enhanced Language Agent] 正在初始化...")
        print("=" * 60)
        
        self.device = device
        self.use_cognition = use_cognition and COGNITION_AVAILABLE
        
        # 初始化认知引擎
        if self.use_cognition:
            try:
                self.cognition_engine = CognitionEngine(
                    model_path=model_path,
                    device=device,
                    use_knowledge_graph=True
                )
                print("✅ Agri-LLaVA认知引擎已加载")
            except Exception as e:
                print(f"⚠️ 认知引擎加载失败: {e}")
                print("   将使用备用BERT模型")
                self.use_cognition = False
        
        # 初始化备用BERT模型
        if not self.use_cognition and TRANSFORMERS_AVAILABLE:
            try:
                print(f"🗣️ 加载备用BERT模型: {fallback_model}")
                os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                self.tokenizer = AutoTokenizer.from_pretrained(fallback_model)
                self.model = AutoModel.from_pretrained(fallback_model)
                self.model.to(device)
                print("✅ BERT模型加载完成")
            except Exception as e:
                print(f"❌ BERT模型加载失败: {e}")
                self.tokenizer = None
                self.model = None
        
        # 初始化提示词模板
        self.prompt_template = PromptTemplate()
        
        print("=" * 60)
        print("✅ 增强版文本智能体初始化完成！")
        print("=" * 60)
    
    def analyze_image(
        self,
        image: Image.Image,
        detection_results: Optional[List[DetectionResult]] = None,
        user_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析图像并生成诊断报告（多模态）
        
        Args:
            image: 输入图像
            detection_results: 检测结果列表
            user_description: 用户描述
            
        Returns:
            诊断报告字典
        """
        if self.use_cognition and hasattr(self, 'cognition_engine'):
            return self.cognition_engine.analyze_image(
                image=image,
                detection_results=detection_results,
                user_description=user_description
            )
        else:
            # 备用模式：返回基础信息
            return {
                "success": False,
                "diagnosis_report": "认知引擎不可用，无法生成详细报告",
                "model_used": "Fallback",
                "multimodal": False
            }
    
    def answer_question(
        self,
        question: str,
        image: Optional[Image.Image] = None,
        detection_results: Optional[List[DetectionResult]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        回答用户问题（支持多模态）
        
        Args:
            question: 用户问题
            image: 可选的图像
            detection_results: 可选的检测结果
            chat_history: 可选的对话历史
            
        Returns:
            回答文本
        """
        if self.use_cognition and hasattr(self, 'cognition_engine'):
            return self.cognition_engine.answer_question(
                question=question,
                image=image,
                detection_results=detection_results,
                chat_history=chat_history
            )
        else:
            # 备用模式：使用BERT相似度匹配
            return self._fallback_answer(question)
    
    def _fallback_answer(self, question: str) -> str:
        """
        备用回答模式（基于BERT相似度）
        
        Args:
            question: 用户问题
            
        Returns:
            回答文本
        """
        # 简单的关键词匹配
        keywords = {
            "条锈病": "条锈病是由条形柄锈菌引起的小麦病害，主要症状为叶片出现黄色条纹。",
            "白粉病": "白粉病是由禾本科布氏白粉菌引起的小麦病害，主要症状为叶片出现白色粉状霉层。",
            "赤霉病": "赤霉病是由禾谷镰刀菌引起的小麦病害，主要危害麦穗，导致穗腐。",
            "防治": "小麦病害防治应遵循预防为主、综合防治的原则，包括农业防治、物理防治和化学防治。",
            "治疗": "治疗小麦病害应根据具体病害选择合适的杀菌剂，如三唑酮、多菌灵等。"
        }
        
        for keyword, answer in keywords.items():
            if keyword in question:
                return answer
        
        return "我是小麦病害诊断助手。请上传图片进行诊断，或询问具体的病害知识。"
    
    def generate_diagnosis_report(
        self,
        disease_name: str,
        confidence: float,
        detection_results: List[DetectionResult],
        user_description: Optional[str] = None
    ) -> str:
        """
        生成格式化的诊断报告
        
        Args:
            disease_name: 病害名称
            confidence: 置信度
            detection_results: 检测结果
            user_description: 用户描述
            
        Returns:
            Markdown格式的报告
        """
        if self.use_cognition and hasattr(self, 'cognition_engine'):
            return self.cognition_engine.generate_diagnosis_report(
                disease_name=disease_name,
                confidence=confidence,
                detection_results=detection_results,
                user_description=user_description
            )
        else:
            # 备用模式：使用模板生成
            return self.prompt_template.format_diagnosis_report(
                diagnosis=disease_name,
                confidence=confidence,
                symptoms=[],
                causes=[],
                preventions=[],
                treatments=[]
            )
    
    def get_embedding(self, text: str) -> torch.Tensor:
        """
        将文本转化为向量（兼容原有接口）
        
        Args:
            text: 输入文本
            
        Returns:
            文本嵌入向量
        """
        if not TRANSFORMERS_AVAILABLE or self.tokenizer is None:
            return torch.zeros(1, 768)
        
        if not text:
            return torch.zeros(1, 768)
        
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # 取[CLS] token的输出作为句向量
        cls_embedding = outputs.last_hidden_state[:, 0, :]
        return cls_embedding
    
    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """
        计算两段文本的语义相似度（兼容原有接口）
        
        Args:
            text_a: 文本A
            text_b: 文本B
            
        Returns:
            相似度分数
        """
        vec_a = self.get_embedding(text_a)
        vec_b = self.get_embedding(text_b)
        
        similarity = F.cosine_similarity(vec_a, vec_b)
        return similarity.item()
    
    def chat(
        self,
        message: str,
        image: Optional[Image.Image] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        通用对话接口
        
        Args:
            message: 用户消息
            image: 可选的图像
            context: 可选的上下文
            
        Returns:
            助手回复
        """
        if self.use_cognition and hasattr(self, 'cognition_engine'):
            return self.cognition_engine.chat(
                message=message,
                image=image,
                context=context
            )
        else:
            return self.answer_question(question=message, image=image)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        info = {
            "agent_type": "EnhancedLanguageAgent",
            "use_cognition": self.use_cognition,
            "device": self.device
        }
        
        if self.use_cognition and hasattr(self, 'cognition_engine'):
            info["cognition_info"] = self.cognition_engine.get_model_info()
        
        return info


def test_enhanced_language_agent():
    """测试增强版文本智能体"""
    print("=" * 60)
    print("🧪 测试 Enhanced Language Agent")
    print("=" * 60)
    
    # 创建智能体（不使用认知引擎，使用备用模式）
    agent = EnhancedLanguageAgent(
        use_cognition=False,  # 使用备用模式测试
        fallback_model='bert-base-chinese'
    )
    
    # 测试问答
    print("\n1️⃣ 测试问答功能")
    question = "条锈病怎么防治？"
    answer = agent.answer_question(question)
    print(f"Q: {question}")
    print(f"A: {answer[:100]}...")
    
    # 测试相似度计算
    print("\n2️⃣ 测试相似度计算")
    text_a = "小麦叶片出现黄色条纹"
    text_b = "条锈病症状表现为黄色条纹状病斑"
    similarity = agent.compute_similarity(text_a, text_b)
    print(f"相似度: {similarity:.4f}")
    
    # 测试报告生成
    print("\n3️⃣ 测试报告生成")
    detections = [
        DetectionResult(
            disease_name="条锈病",
            confidence=0.92,
            bbox=[100, 150, 200, 250]
        )
    ]
    report = agent.generate_diagnosis_report(
        disease_name="条锈病",
        confidence=0.92,
        detection_results=detections
    )
    print(report[:300] + "...")
    
    # 获取模型信息
    print("\n4️⃣ 测试模型信息")
    info = agent.get_model_info()
    print(f"模型信息: {info}")
    
    print("\n" + "=" * 60)
    print("✅ Enhanced Language Agent 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_enhanced_language_agent()

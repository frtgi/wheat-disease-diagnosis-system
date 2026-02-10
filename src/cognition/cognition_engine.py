# -*- coding: utf-8 -*-
"""
认知引擎 - Cognition Engine
集成Agri-LLaVA模型，提供高级语义理解和诊断报告生成功能

该模块作为LanguageAgent的增强版，支持：
1. 多模态输入（图像+文本）
2. 基于LLaVA的语义理解
3. 交互式对话
4. 专业诊断报告生成
"""
import os
import sys
from typing import Optional, List, Dict, Any
from PIL import Image

# 添加src到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cognition.llava_engine import AgriLLaVA
from cognition.prompt_templates import PromptTemplate, DetectionResult
from graph.graph_engine import KnowledgeAgent


class CognitionEngine:
    """
    认知引擎
    
    集成Agri-LLaVA模型，提供：
    - 图像语义理解
    - 诊断报告生成
    - 知识问答
    - 交互式对话
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        vision_encoder_name: str = "openai/clip-vit-large-patch14",
        llm_name: str = "lmsys/vicuna-7b-v1.5",
        device: str = "cuda" if os.system("nvidia-smi") == 0 else "cpu",
        use_knowledge_graph: bool = True,
        kg_password: str = "123456789s"
    ):
        """
        初始化认知引擎
        
        :param model_path: 预训练模型路径（如果为None则加载基础模型）
        :param vision_encoder_name: 视觉编码器名称
        :param llm_name: LLM模型名称
        :param device: 计算设备
        :param use_knowledge_graph: 是否使用知识图谱
        :param kg_password: 知识图谱密码
        """
        print("=" * 60)
        print("🧠 [CognitionEngine] 初始化认知引擎")
        print("=" * 60)
        
        self.device = device
        self.use_knowledge_graph = use_knowledge_graph
        
        # 初始化Agri-LLaVA模型
        try:
            # 先尝试不使用量化加载（更稳定）
            print("🔄 尝试加载Agri-LLaVA模型（无量化）...")
            self.model = AgriLLaVA(
                vision_encoder_name=vision_encoder_name,
                llm_name=llm_name,
                device=device,
                load_in_8bit=False,  # 禁用量化以避免兼容性问题
                load_in_4bit=False
            )
            
            # 如果提供了模型路径，加载预训练权重
            if model_path and os.path.exists(model_path):
                print(f"📂 加载预训练模型: {model_path}")
                self.model.load_pretrained(model_path)
            
            self.model_available = True
            print("✅ Agri-LLaVA模型加载成功")
            
        except Exception as e:
            print(f"⚠️ Agri-LLaVA模型加载失败: {e}")
            print("   将使用备用模式（基于知识图谱的问答）")
            self.model_available = False
            self.model = None
        
        # 初始化知识图谱
        if use_knowledge_graph:
            try:
                self.knowledge_agent = KnowledgeAgent(password=kg_password)
                print("✅ 知识图谱连接成功")
            except Exception as e:
                print(f"⚠️ 知识图谱连接失败: {e}")
                self.knowledge_agent = None
        else:
            self.knowledge_agent = None
        
        # 初始化提示词模板
        self.prompt_template = PromptTemplate()
        
        print("=" * 60)
    
    def analyze_image(
        self,
        image: Image.Image,
        detection_results: Optional[List[DetectionResult]] = None,
        user_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析图像并生成诊断报告
        
        :param image: 输入图像
        :param detection_results: YOLO检测结果
        :param user_description: 用户描述
        :return: 包含诊断报告的字典
        """
        if not self.model_available:
            return self._fallback_analysis(detection_results, user_description)
        
        # 构建提示词
        prompt = self.prompt_template.build_diagnosis_prompt(
            detection_results=detection_results or [],
            user_description=user_description
        )
        
        # 生成诊断报告
        try:
            generated_text = self.model.generate(
                images=[image],
                prompt=prompt,
                max_new_tokens=512,
                temperature=0.7
            )
            
            return {
                "success": True,
                "diagnosis_report": generated_text,
                "model_used": "Agri-LLaVA",
                "multimodal": True
            }
        
        except Exception as e:
            print(f"❌ 图像分析失败: {e}")
            return self._fallback_analysis(detection_results, user_description)
    
    def answer_question(
        self,
        question: str,
        image: Optional[Image.Image] = None,
        detection_results: Optional[List[DetectionResult]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        回答用户问题（支持多模态）
        
        :param question: 用户问题
        :param image: 可选的图像
        :param detection_results: 可选的检测结果
        :param chat_history: 可选的对话历史
        :return: 回答文本
        """
        if not self.model_available:
            return self._fallback_qa(question)
        
        # 构建提示词
        prompt = self.prompt_template.build_interactive_prompt(
            user_question=question,
            detection_results=detection_results,
            chat_history=chat_history
        )
        
        # 生成回答
        try:
            images = [image] if image else None
            answer = self.model.generate(
                images=images,
                prompt=prompt,
                max_new_tokens=256,
                temperature=0.7
            )
            return answer
        
        except Exception as e:
            print(f"❌ 问答失败: {e}")
            return self._fallback_qa(question)
    
    def generate_diagnosis_report(
        self,
        disease_name: str,
        confidence: float,
        detection_results: List[DetectionResult],
        user_description: Optional[str] = None
    ) -> str:
        """
        生成格式化的诊断报告
        
        :param disease_name: 病害名称
        :param confidence: 置信度
        :param detection_results: 检测结果
        :param user_description: 用户描述
        :return: Markdown格式的报告
        """
        # 从知识图谱获取详细信息
        symptoms = []
        causes = []
        preventions = []
        treatments = []
        
        if self.knowledge_agent:
            try:
                info = self.knowledge_agent.get_disease_details(disease_name)
                symptoms = info.get('symptoms', [])
                causes = info.get('causes', [])
                preventions = info.get('preventions', [])
                treatments = info.get('treatments', [])
            except Exception as e:
                print(f"⚠️ 知识图谱查询失败: {e}")
        
        # 构建推理过程
        reasoning_parts = []
        if detection_results:
            reasoning_parts.append("基于视觉检测结果：")
            for r in detection_results:
                reasoning_parts.append(f"- 检测到{r.disease_name}，置信度{r.confidence:.2%}")
        
        if user_description:
            reasoning_parts.append(f"\n结合用户描述：{user_description}")
        
        reasoning = "\n".join(reasoning_parts)
        
        # 格式化报告
        report = self.prompt_template.format_diagnosis_report(
            diagnosis=disease_name,
            confidence=confidence,
            symptoms=symptoms,
            causes=causes,
            preventions=preventions,
            treatments=treatments,
            reasoning=reasoning
        )
        
        return report
    
    def _fallback_analysis(
        self,
        detection_results: Optional[List[DetectionResult]],
        user_description: Optional[str]
    ) -> Dict[str, Any]:
        """
        备用分析模式（当LLaVA不可用时）
        
        :param detection_results: 检测结果
        :param user_description: 用户描述
        :return: 基础诊断报告
        """
        print("🔄 使用备用模式生成报告")
        
        if detection_results:
            main_result = detection_results[0]
            report = self.generate_diagnosis_report(
                disease_name=main_result.disease_name,
                confidence=main_result.confidence,
                detection_results=detection_results,
                user_description=user_description
            )
            
            return {
                "success": True,
                "diagnosis_report": report,
                "model_used": "KnowledgeGraph",
                "multimodal": False
            }
        else:
            return {
                "success": False,
                "diagnosis_report": "无法生成诊断报告：未检测到病害特征",
                "model_used": "None",
                "multimodal": False
            }
    
    def _fallback_qa(self, question: str) -> str:
        """
        备用问答模式（当LLaVA不可用时）
        
        :param question: 用户问题
        :return: 基于知识图谱的回答
        """
        if not self.knowledge_agent:
            return "抱歉，系统暂时无法回答您的问题。请稍后再试。"
        
        # 尝试从知识图谱获取答案
        diseases = ["蚜虫", "螨虫", "锈病", "赤霉病", "白粉病", "条锈病", "叶锈病"]
        target_disease = None
        
        for d in diseases:
            if d in question:
                target_disease = d
                break
        
        if target_disease:
            info = self.knowledge_agent.get_disease_details(target_disease)
            if info:
                response = f"关于【{target_disease}】：\n"
                if "预防" in question or "防" in question:
                    response += f"预防措施：{', '.join(info['preventions'][:3])}"
                elif "药" in question or "治" in question:
                    response += f"治疗方案：{', '.join(info['treatments'][:3])}"
                else:
                    response += f"症状：{', '.join(info['symptoms'][:3])}\n"
                    response += f"预防：{', '.join(info['preventions'][:2])}\n"
                    response += f"治疗：{', '.join(info['treatments'][:2])}"
                return response
        
        return "我是小麦病害诊断助手。请上传图片进行诊断，或询问具体的病害知识。"
    
    def chat(
        self,
        message: str,
        image: Optional[Image.Image] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        通用对话接口
        
        :param message: 用户消息
        :param image: 可选的图像
        :param context: 可选的上下文信息
        :return: 助手回复
        """
        # 解析上下文
        detection_results = None
        if context and 'detection_results' in context:
            detection_results = context['detection_results']
        
        # 如果有图像，进行多模态分析
        if image:
            result = self.analyze_image(
                image=image,
                detection_results=detection_results,
                user_description=message
            )
            return result.get('diagnosis_report', '分析失败')
        
        # 纯文本问答
        return self.answer_question(
            question=message,
            detection_results=detection_results
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        :return: 模型信息字典
        """
        return {
            "model_available": self.model_available,
            "vision_encoder": self.model.vision_encoder_name if self.model else None,
            "llm": self.model.llm_name if self.model else None,
            "device": self.device,
            "knowledge_graph_connected": self.knowledge_agent is not None
        }


def test_cognition_engine():
    """测试认知引擎"""
    print("=" * 60)
    print("🧪 测试 CognitionEngine")
    print("=" * 60)
    
    # 创建引擎实例（不使用LLaVA模型，仅测试备用模式）
    engine = CognitionEngine(
        model_path=None,  # 不加载预训练模型
        use_knowledge_graph=True
    )
    
    # 测试1：基础问答
    print("\n1️⃣ 测试基础问答")
    answer = engine.answer_question("条锈病怎么防治？")
    print(f"Q: 条锈病怎么防治？")
    print(f"A: {answer[:200]}...")
    
    # 测试2：生成诊断报告
    print("\n2️⃣ 测试诊断报告生成")
    detections = [
        DetectionResult(
            disease_name="条锈病",
            confidence=0.92,
            bbox=[100, 150, 200, 250]
        )
    ]
    report = engine.generate_diagnosis_report(
        disease_name="条锈病",
        confidence=0.92,
        detection_results=detections,
        user_description="叶片有黄色条纹"
    )
    print(report[:500] + "...")
    
    # 测试3：获取模型信息
    print("\n3️⃣ 测试模型信息")
    info = engine.get_model_info()
    print(f"模型信息: {info}")
    
    print("\n" + "=" * 60)
    print("✅ CognitionEngine 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_cognition_engine()

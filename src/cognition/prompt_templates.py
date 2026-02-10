# -*- coding: utf-8 -*-
"""
提示工程模块 - Prompt Engineering for Agri-LLaVA

根据文档4.3节：
"为了激发Agri-LLaVA的最佳性能，我们设计了针对性的提示模板（Prompt Templates）。
系统会自动将YOLOv8的检测结果（如病害类别、置信度、位置）作为上下文（Context）嵌入到提示词中。"
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """YOLO检测结果数据结构"""
    disease_name: str
    confidence: float
    bbox: Optional[List[float]] = None  # [x1, y1, x2, y2]
    severity: Optional[str] = None  # 严重程度


class SystemPrompts:
    """
    系统提示词集合
    """
    
    # 基础系统提示词
    BASE_SYSTEM_PROMPT = """你是一个经验丰富的小麦病理学专家。请基于提供的图像视觉特征和上下文信息，进行严谨的病害诊断，并给出科学的防治建议。如果视觉特征不明确，请指出不确定性，不要臆造。"""
    
    # 诊断模式提示词
    DIAGNOSIS_PROMPT = """你是一个专业的小麦病害诊断专家。请根据提供的图像和上下文信息，给出详细的诊断报告。

诊断报告应包含以下内容：
1. 病害名称和置信度
2. 症状描述和识别依据
3. 可能的成因分析
4. 防治建议（包括预防措施和治疗方案）
5. 如有不确定性，请明确指出

请用专业但易懂的语言回答。"""
    
    # 交互式诊断提示词
    INTERACTIVE_PROMPT = """你是小麦病害智能诊断助手。用户可能会询问关于小麦病害的各种问题。

你可以回答：
- 病害识别和诊断
- 症状解释和成因分析
- 防治措施和用药建议
- 病害预防和监测方法

请基于你的专业知识给出准确、实用的建议。如果不确定，请诚实告知。"""
    
    # 知识问答提示词
    KNOWLEDGE_QA_PROMPT = """你是小麦病害知识库专家。请基于农业知识图谱中的信息，回答用户关于小麦病害的问题。

你可以提供的信息包括：
- 病害的基本特征和症状
- 发病条件和传播途径
- 防治药剂和使用方法
- 预防措施和栽培建议

请确保信息的准确性和实用性。"""


class PromptTemplate:
    """
    提示词模板类
    用于构建包含YOLO检测结果的上下文提示
    """
    
    def __init__(self, system_prompt: Optional[str] = None):
        """
        初始化提示词模板
        
        :param system_prompt: 系统提示词，如果为None则使用默认
        """
        self.system_prompt = system_prompt or SystemPrompts.BASE_SYSTEM_PROMPT
    
    def build_diagnosis_prompt(
        self,
        detection_results: List[DetectionResult],
        user_description: Optional[str] = None,
        include_context: bool = True
    ) -> str:
        """
        构建诊断提示词
        
        :param detection_results: YOLO检测结果列表
        :param user_description: 用户提供的症状描述
        :param include_context: 是否包含上下文信息
        :return: 完整的提示词
        """
        prompt_parts = [self.system_prompt]
        
        # 添加上下文信息（YOLO检测结果）
        if include_context and detection_results:
            context = self._build_detection_context(detection_results)
            prompt_parts.append(f"\n【视觉检测上下文】\n{context}")
        
        # 添加用户描述
        if user_description:
            prompt_parts.append(f"\n【用户描述】\n{user_description}")
        
        # 添加任务指令
        prompt_parts.append("\n【任务】\n请基于以上信息，给出专业的小麦病害诊断报告。")
        
        return "\n".join(prompt_parts)
    
    def _build_detection_context(self, detection_results: List[DetectionResult]) -> str:
        """
        构建检测结果的上下文描述
        
        :param detection_results: 检测结果列表
        :return: 上下文描述文本
        """
        if not detection_results:
            return "未检测到明显病害特征。"
        
        context_parts = []
        
        for i, result in enumerate(detection_results, 1):
            # 构建单个检测结果的描述
            desc = f"{i}. 检测到'{result.disease_name}'"
            
            if result.confidence > 0:
                desc += f"，置信度{result.confidence:.2%}"
            
            if result.bbox:
                x1, y1, x2, y2 = result.bbox
                desc += f"，位置[{x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}]"
            
            if result.severity:
                desc += f"，严重程度：{result.severity}"
            
            context_parts.append(desc)
        
        return "\n".join(context_parts)
    
    def build_interactive_prompt(
        self,
        user_question: str,
        detection_results: Optional[List[DetectionResult]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        构建交互式对话提示词
        
        :param user_question: 用户问题
        :param detection_results: 可选的检测结果
        :param chat_history: 可选的对话历史
        :return: 完整的提示词
        """
        prompt_parts = [SystemPrompts.INTERACTIVE_PROMPT]
        
        # 添加对话历史
        if chat_history:
            prompt_parts.append("\n【对话历史】")
            for turn in chat_history[-5:]:  # 只保留最近5轮
                role = turn.get("role", "user")
                content = turn.get("content", "")
                prompt_parts.append(f"{role}: {content}")
        
        # 添加检测结果上下文
        if detection_results:
            context = self._build_detection_context(detection_results)
            prompt_parts.append(f"\n【当前图像检测结果】\n{context}")
        
        # 添加当前问题
        prompt_parts.append(f"\n用户问题：{user_question}")
        prompt_parts.append("\n请回答用户的问题：")
        
        return "\n".join(prompt_parts)
    
    def build_knowledge_qa_prompt(
        self,
        disease_name: str,
        knowledge_context: Dict[str, Any],
        user_question: Optional[str] = None
    ) -> str:
        """
        构建知识问答提示词
        
        :param disease_name: 病害名称
        :param knowledge_context: 知识图谱检索结果
        :param user_question: 用户问题
        :return: 完整的提示词
        """
        prompt_parts = [SystemPrompts.KNOWLEDGE_QA_PROMPT]
        
        # 添加知识上下文
        prompt_parts.append(f"\n【{disease_name}知识档案】")
        
        if 'symptoms' in knowledge_context:
            symptoms = knowledge_context['symptoms']
            if symptoms:
                prompt_parts.append(f"\n典型症状：{', '.join(symptoms[:3])}")
        
        if 'causes' in knowledge_context:
            causes = knowledge_context['causes']
            if causes:
                prompt_parts.append(f"主要成因：{', '.join(causes[:2])}")
        
        if 'preventions' in knowledge_context:
            preventions = knowledge_context['preventions']
            if preventions:
                prompt_parts.append(f"预防措施：{', '.join(preventions[:3])}")
        
        if 'treatments' in knowledge_context:
            treatments = knowledge_context['treatments']
            if treatments:
                prompt_parts.append(f"治疗方案：{', '.join(treatments[:3])}")
        
        # 添加用户问题
        if user_question:
            prompt_parts.append(f"\n用户问题：{user_question}")
        else:
            prompt_parts.append(f"\n请详细介绍{disease_name}的相关知识。")
        
        return "\n".join(prompt_parts)
    
    def build_context_injection_prompt(
        self,
        detection_result: DetectionResult,
        user_query: str
    ) -> str:
        """
        构建上下文注入提示词（文档4.3节示例格式）
        
        示例格式：
        "检测模型已在坐标[x, y]处识别出'赤霉病'症状，置信度为0.92。
        请结合图像细节确认此诊断，并解释判断依据。"
        
        :param detection_result: 单个检测结果
        :param user_query: 用户查询
        :return: 上下文注入提示词
        """
        # 构建上下文描述
        context = f"检测模型已识别出'{detection_result.disease_name}'症状"
        
        if detection_result.confidence > 0:
            context += f"，置信度为{detection_result.confidence:.2f}"
        
        if detection_result.bbox:
            x1, y1, x2, y2 = detection_result.bbox
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            context += f"，位置在坐标[{center_x:.1f}, {center_y:.1f}]"
        
        # 结合用户查询
        prompt = f"{context}。{user_query}"
        
        return prompt
    
    @staticmethod
    def format_diagnosis_report(
        diagnosis: str,
        confidence: float,
        symptoms: List[str],
        causes: List[str],
        preventions: List[str],
        treatments: List[str],
        reasoning: Optional[str] = None
    ) -> str:
        """
        格式化诊断报告
        
        :param diagnosis: 诊断结果
        :param confidence: 置信度
        :param symptoms: 症状列表
        :param causes: 成因列表
        :param preventions: 预防措施列表
        :param treatments: 治疗措施列表
        :param reasoning: 推理过程
        :return: 格式化的报告文本
        """
        report_parts = [
            f"### 🏥 诊断结论：【{diagnosis}】",
            f"**置信度**: {confidence:.2%}",
            "",
            "### 📋 症状描述",
        ]
        
        if symptoms:
            for symptom in symptoms[:5]:
                report_parts.append(f"- {symptom}")
        else:
            report_parts.append("- 暂无详细症状记录")
        
        report_parts.extend([
            "",
            "### 🌡️ 成因分析",
        ])
        
        if causes:
            for cause in causes[:3]:
                report_parts.append(f"- {cause}")
        else:
            report_parts.append("- 暂无详细成因分析")
        
        report_parts.extend([
            "",
            "### 🛡️ 预防措施",
        ])
        
        if preventions:
            for prevention in preventions[:3]:
                report_parts.append(f"- {prevention}")
        else:
            report_parts.append("- 暂无详细预防措施")
        
        report_parts.extend([
            "",
            "### 💊 治疗方案",
        ])
        
        if treatments:
            for treatment in treatments[:3]:
                report_parts.append(f"- {treatment}")
        else:
            report_parts.append("- 建议咨询专业农技人员")
        
        if reasoning:
            report_parts.extend([
                "",
                "### 🔍 诊断推理",
                reasoning
            ])
        
        return "\n".join(report_parts)


def test_prompt_templates():
    """测试提示词模板"""
    print("=" * 60)
    print("🧪 测试提示词模板")
    print("=" * 60)
    
    # 创建模板实例
    template = PromptTemplate()
    
    # 测试数据
    detections = [
        DetectionResult(
            disease_name="条锈病",
            confidence=0.92,
            bbox=[100, 150, 200, 250],
            severity="中度"
        ),
        DetectionResult(
            disease_name="白粉病",
            confidence=0.78,
            bbox=[300, 350, 400, 450],
            severity="轻度"
        )
    ]
    
    # 测试1：诊断提示词
    print("\n1️⃣ 测试诊断提示词")
    diagnosis_prompt = template.build_diagnosis_prompt(
        detection_results=detections,
        user_description="叶片上有黄色条纹，背面有白色粉末"
    )
    print(diagnosis_prompt[:500] + "...")
    print("✅ 诊断提示词生成成功")
    
    # 测试2：交互式提示词
    print("\n2️⃣ 测试交互式提示词")
    interactive_prompt = template.build_interactive_prompt(
        user_question="条锈病怎么防治？",
        detection_results=detections[:1]
    )
    print(interactive_prompt[:500] + "...")
    print("✅ 交互式提示词生成成功")
    
    # 测试3：上下文注入提示词
    print("\n3️⃣ 测试上下文注入提示词")
    context_prompt = template.build_context_injection_prompt(
        detection_result=detections[0],
        user_query="请结合图像细节确认此诊断，并解释判断依据。"
    )
    print(context_prompt)
    print("✅ 上下文注入提示词生成成功")
    
    # 测试4：报告格式化
    print("\n4️⃣ 测试报告格式化")
    report = PromptTemplate.format_diagnosis_report(
        diagnosis="条锈病",
        confidence=0.92,
        symptoms=["叶片出现黄色条纹", "条纹沿叶脉排列", "背面有孢子堆"],
        causes=["高温高湿环境", "病原菌传播"],
        preventions=["选用抗病品种", "合理密植", "及时清除病残体"],
        treatments=["喷施粉锈宁", "使用三唑酮防治"],
        reasoning="基于视觉检测的黄色条纹特征和知识图谱匹配"
    )
    print(report[:800] + "...")
    print("✅ 报告格式化成功")
    
    print("\n" + "=" * 60)
    print("✅ 提示词模板测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_prompt_templates()

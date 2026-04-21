"""
Qwen3-VL 输出后处理模块
提供响应解析、病害信息提取、置信度格式化等功能
"""
import logging
from typing import Dict, Any, List

from .qwen_config import (
    COMMON_DISEASES,
    CONFIDENCE_KEYWORDS,
    SEVERITY_KEYWORDS
)

logger = logging.getLogger(__name__)


class QwenPostprocessor:
    """
    Qwen3-VL 输出后处理器

    职责：
    - 模型响应文本解析和结构化
    - 病害名称提取和匹配
    - 置信度估计和格式化
    - 症状/防治方法/治疗方法提取
    - 严重程度评估
    - 推理链提取和分析
    """

    def parse_response(self, response: str, enable_thinking: bool = False) -> Dict[str, Any]:
        """
        解析诊断结果

        将模型原始响应文本解析为结构化的诊断结果字典。

        Args:
            response: 模型响应文本
            enable_thinking: 是否启用了 Thinking 模式

        Returns:
            Dict[str, Any]: 结构化的诊断结果，包含以下字段：
                - disease_name: 病害名称
                - confidence: 置信度 (0-1)
                - symptoms: 症状描述
                - prevention_methods: 防治方法
                - treatment_methods: 治疗方法
                - severity: 严重程度
                - reasoning: 推理过程（如果启用 Thinking）
        """
        if enable_thinking and "推理过程" in response:
            parts = response.split("诊断结论")
            if len(parts) > 1:
                reasoning = parts[0]
                conclusion = "诊断结论" + parts[1]
            else:
                reasoning = response
                conclusion = response
        else:
            reasoning = ""
            conclusion = response

        return {
            "disease_name": self.extract_disease_name(conclusion),
            "confidence": self.estimate_confidence(conclusion),
            "symptoms": self.extract_symptoms(conclusion),
            "prevention_methods": self.extract_prevention(conclusion),
            "treatment_methods": self.extract_treatment(conclusion),
            "severity": self.estimate_severity(conclusion),
            "reasoning": reasoning if enable_thinking else None
        }

    def extract_disease_info(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取并增强病害信息

        从诊断结果中提取关键信息，并进行标准化处理。

        Args:
            diagnosis: 解析后的诊断结果字典

        Returns:
            Dict[str, Any]: 增强后的病害信息
        """
        disease_name = diagnosis.get("disease_name", "未知病害")
        confidence = diagnosis.get("confidence", 0.85)
        severity = diagnosis.get("severity", "中等")

        return {
            "disease_name": disease_name,
            "confidence": self.format_confidence(confidence),
            "confidence_raw": confidence,
            "severity": severity,
            "is_common_disease": disease_name in COMMON_DISEASES,
            "has_symptoms": bool(diagnosis.get("symptoms")),
            "has_treatment": bool(diagnosis.get("treatment_methods"))
        }

    def format_confidence(self, confidence: float) -> str:
        """
        格式化置信度为可读字符串

        将数值置信度转换为百分比字符串，并添加等级描述。

        Args:
            confidence: 置信度值 (0-1)

        Returns:
            str: 格式化的置信度字符串，例如 "85% (高置信度)"
        """
        percentage = confidence * 100

        if confidence >= 0.9:
            level = "极高"
        elif confidence >= 0.8:
            level = "高"
        elif confidence >= 0.7:
            level = "中等偏高"
        elif confidence >= 0.6:
            level = "中等"
        elif confidence >= 0.5:
            level = "偏低"
        else:
            level = "低"

        return f"{percentage:.1f}% ({level}置信度)"

    def extract_reasoning_chain(self, response: str) -> List[str]:
        """
        提取推理链

        从模型响应中提取推理步骤，返回结构化的推理链列表。

        Args:
            response: 模型响应文本

        Returns:
            List[str]: 推理步骤列表，每项包含步骤编号和内容
        """
        reasoning_steps = []

        if "推理过程" in response:
            start = response.find("推理过程")
            end = response.find("诊断结论")
            if end == -1:
                end = len(response)
            reasoning_text = response[start:end].strip()

            lines = reasoning_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    step_content = line[2:].strip()
                    if step_content:
                        reasoning_steps.append(f"步骤{line[0]}: {step_content}")
                elif line.startswith(('步骤', 'Step', '第')):
                    reasoning_steps.append(line)
                elif '首先' in line or '然后' in line or '接着' in line or '最后' in line:
                    reasoning_steps.append(line)
                elif reasoning_steps and not line.startswith('推理过程'):
                    reasoning_steps[-1] += f" {line}"

        if not reasoning_steps and ("分析" in response or "诊断" in response):
            sentences = response.replace('。', '。\n').split('\n')
            step_num = 1
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                if any(keyword in sentence for keyword in ['分析', '观察', '识别', '判断', '诊断', '建议', '考虑']):
                    reasoning_steps.append(f"步骤{step_num}: {sentence}")
                    step_num += 1

        return reasoning_steps

    def estimate_confidence(self, text: str) -> float:
        """
        从诊断文本中估计置信度

        基于关键词匹配算法，识别模型输出中的确定性表达，
        并映射到对应的置信度值。

        Args:
            text: 诊断文本

        Returns:
            float: 置信度值 (0-1)，默认 0.85
        """
        for keyword, conf in CONFIDENCE_KEYWORDS.items():
            if keyword in text:
                return conf

        return 0.85

    def extract_symptoms(self, text: str) -> str:
        """
        提取症状描述

        从诊断文本中定位和提取症状相关内容。

        Args:
            text: 诊断文本

        Returns:
            str: 症状描述（最多 200 字符）
        """
        keywords = ["症状", "病斑", "叶片", "麦穗", "茎秆"]
        for keyword in keywords:
            if keyword in text:
                start = text.find(keyword)
                start = max(0, start - 50)
                end = min(len(text), start + 150)
                return text[start:end]
        return text[:200]

    def extract_prevention(self, text: str) -> str:
        """
        提取防治方法

        从诊断文本中定位和提取防治相关内容。

        Args:
            text: 诊断文本

        Returns:
            str: 防治方法（最多 300 字符）
        """
        keywords = ["防治", "预防", "农业防治", "化学防治"]
        for keyword in keywords:
            if keyword in text:
                start = text.find(keyword)
                return text[start:start+300]
        return "请参考当地农业专家建议"

    def extract_treatment(self, text: str) -> str:
        """
        提取治疗方法

        从诊断文本中定位和治疗相关内容。

        Args:
            text: 诊断文本

        Returns:
            str: 治疗方法（最多 300 字符）
        """
        keywords = ["治疗", "药剂", "喷洒", "用药"]
        for keyword in keywords:
            if keyword in text:
                start = text.find(keyword)
                return text[start:start+300]
        return "请咨询专业农技人员"

    def estimate_severity(self, text: str) -> str:
        """
        评估严重程度

        基于关键词匹配，从诊断文本中判断病害严重程度。

        Args:
            text: 诊断文本

        Returns:
            str: 严重程度等级 ("严重"/"中等"/"轻度")，默认 "中等"
        """
        for keyword, severity in SEVERITY_KEYWORDS.items():
            if keyword in text:
                return severity

        return "中等"

    def extract_disease_name(self, text: str) -> str:
        """
        从诊断文本中提取病害名称

        在预定义的常见小麦病害列表中进行匹配。

        Args:
            text: 诊断文本

        Returns:
            str: 匹配到的病害名称，如果未匹配到则返回 "未知病害"
        """
        for disease in COMMON_DISEASES:
            if disease in text:
                return disease

        return "未知病害"


def get_postprocessor() -> QwenPostprocessor:
    """
    获取后处理器实例

    Returns:
        QwenPostprocessor: 后处理器实例
    """
    return QwenPostprocessor()

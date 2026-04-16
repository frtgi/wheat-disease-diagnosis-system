"""
Qwen3-VL 配置常量模块
集中管理模型名称、路径、量化配置、推理参数和提示模板
"""
from pathlib import Path
from typing import Dict, Any
import torch


def get_default_model_path() -> Path:
    """
    获取默认模型路径

    Returns:
        Path: Qwen3-VL-2B-Instruct 模型路径
    """
    return Path(__file__).parent.parent.parent.parent.parent.parent / "models" / "Qwen3-VL-2B-Instruct"


MODEL_NAME = "Qwen3-VL-2B-Instruct"
MODEL_PATH = get_default_model_path()


QUANTIZATION_CONFIG: Dict[str, Any] = {
    "load_in_4bit": True,
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_compute_dtype": torch.float16,
    "bnb_4bit_use_double_quant": True
}


INFERENCE_PARAMS: Dict[str, Any] = {
    "max_new_tokens": 384,
    "temperature_diagnosis": 0.1,
    "temperature_thinking": 0.5,
    "top_p": 0.85,
    "do_sample": False,
    "repetition_penalty": 1.1,
    "max_tokens_thinking": 768,
    "max_tokens_normal": 384
}


PROMPT_TEMPLATES: Dict[str, str] = {
    "system_base": """你是一位专业的小麦病害诊断专家，具备以下能力：
1. 准确识别小麦病害类型（真菌病害、虫害、病毒病害等）
2. 分析病害症状（病斑形状、颜色、分布等）
3. 提供科学的防治建议（农业防治、化学防治、生物防治）
4. 解释病害发生规律和环境因素

请以专业、准确、易懂的方式回答用户问题。""",

    "system_thinking": """

【推理模式】请在回答时展现完整的推理过程：
1. 首先描述观察到的症状特征
2. 然后分析可能的病害类型及其依据
3. 接着排除其他相似病害
4. 最后给出诊断结论和防治建议

请确保推理逻辑清晰、符合农学常识。""",

    "multimodal_query": "请分析这张小麦病害图像，并结合以下症状描述进行诊断：{symptoms}",

    "image_query": "请分析这张小麦病害图像，识别病害类型并提供防治建议。",

    "text_query": "作为小麦病害诊断专家，请根据以下症状进行诊断并提供防治建议：{symptoms}",

    "graphrag_context": "\n\n相关知识参考：\n{context}",

    "thinking_suffix": "\n\n请逐步推理并解释诊断依据。"
}


COMMON_DISEASES: list = [
    "条锈病", "叶锈病", "秆锈病",
    "白粉病",
    "赤霉病",
    "纹枯病",
    "根腐病",
    "叶斑病",
    "病毒病",
    "全蚀病",
    "黄矮病",
    "丛矮病"
]


CONFIDENCE_KEYWORDS: Dict[str, float] = {
    "高度怀疑": 0.95,
    "很可能是": 0.85,
    "可能是": 0.75,
    "疑似": 0.65,
    "不确定": 0.5
}


SEVERITY_KEYWORDS: Dict[str, str] = {
    "严重": "严重",
    "重度": "严重",
    "中等": "中等",
    "轻度": "轻度",
    "轻微": "轻度"
}

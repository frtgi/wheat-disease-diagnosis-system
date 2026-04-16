"""
Qwen3-VL 模块化服务包
提供配置、加载、预处理、推理和后处理的模块化接口
"""

from .qwen_config import (
    MODEL_NAME,
    MODEL_PATH,
    QUANTIZATION_CONFIG,
    INFERENCE_PARAMS,
    PROMPT_TEMPLATES,
    COMMON_DISEASES,
    CONFIDENCE_KEYWORDS,
    SEVERITY_KEYWORDS
)
from .qwen_loader import QwenModelLoader, get_model_loader
from .qwen_preprocessor import QwenPreprocessor, get_preprocessor
from .qwen_inferencer import QwenInferencer, get_inferencer
from .qwen_postprocessor import QwenPostprocessor, get_postprocessor

__all__ = [
    'MODEL_NAME',
    'MODEL_PATH',
    'QUANTIZATION_CONFIG',
    'INFERENCE_PARAMS',
    'PROMPT_TEMPLATES',
    'COMMON_DISEASES',
    'CONFIDENCE_KEYWORDS',
    'SEVERITY_KEYWORDS',
    'QwenModelLoader',
    'get_model_loader',
    'QwenPreprocessor',
    'get_preprocessor',
    'QwenInferencer',
    'get_inferencer',
    'QwenPostprocessor',
    'get_postprocessor'
]

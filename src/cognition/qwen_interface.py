# -*- coding: utf-8 -*-
"""
Qwen 模型统一接口规范

定义了所有 Qwen 模型实现必须遵循的接口，确保不同实现之间的兼容性。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass
from PIL import Image


@dataclass
class QwenDiagnosisResult:
    """
    统一的诊断结果数据结构
    
    所有 Qwen 实现的诊断方法都应返回此结构
    """
    success: bool
    disease_name: str
    confidence: float
    diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    prevention_methods: Optional[str] = None
    treatment_methods: Optional[str] = None
    severity: Optional[str] = None
    reasoning_chain: Optional[List[str]] = None
    raw_response: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class QwenModelInterface(ABC):
    """
    Qwen 模型统一接口
    
    所有 Qwen 模型实现（QwenEngine、QwenService、QwenVLEngine）都应继承此类
    """
    
    @abstractmethod
    def diagnose(
        self,
        image: Optional[Image.Image] = None,
        symptoms: str = "",
        **kwargs
    ) -> QwenDiagnosisResult:
        """
        诊断病害（统一接口）
        
        :param image: 病害图像（可选）
        :param symptoms: 症状描述文本
        :param kwargs: 其他参数（如 enable_thinking, use_graph_rag 等）
        :return: QwenDiagnosisResult 对象
        """
        pass
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        image: Optional[Union[str, Image.Image, Path]] = None,
        **kwargs
    ) -> str:
        """
        生成文本（统一接口）
        
        :param prompt: 输入提示文本
        :param image: 可选的图像输入
        :param kwargs: 其他参数
        :return: 生成的文本
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息（统一接口）
        
        :return: 包含模型详细信息的字典
        """
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """
        检查模型是否已加载
        
        :return: 模型是否已加载
        """
        pass
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        多轮对话（可选实现）
        
        :param messages: 消息列表
        :param kwargs: 其他参数
        :return: 回复内容
        """
        raise NotImplementedError("此实现不支持多轮对话")
    
    def analyze_with_detection(
        self,
        detection_result: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        结合检测结果进行分析（可选实现）
        
        :param detection_result: 视觉检测结果
        :param kwargs: 其他参数
        :return: 分析报告
        """
        raise NotImplementedError("此实现不支持检测结果分析")
    
    def unload_from_gpu(self):
        """
        从 GPU 卸载模型（可选实现）
        
        用于释放 GPU 显存
        """
        pass
    
    def load_to_gpu(self):
        """
        将模型加载到 GPU（可选实现）
        
        用于动态加载模型到 GPU
        """
        pass


def create_diagnosis_result(
    success: bool,
    disease_name: str = "未知",
    confidence: float = 0.0,
    **kwargs
) -> QwenDiagnosisResult:
    """
    创建诊断结果的工厂函数
    
    :param success: 是否成功
    :param disease_name: 病害名称
    :param confidence: 置信度
    :param kwargs: 其他参数
    :return: QwenDiagnosisResult 对象
    """
    return QwenDiagnosisResult(
        success=success,
        disease_name=disease_name,
        confidence=confidence,
        **kwargs
    )

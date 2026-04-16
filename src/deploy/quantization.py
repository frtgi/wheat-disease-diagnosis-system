# -*- coding: utf-8 -*-
"""
模型量化模块

提供模型量化功能：
- INT8量化
- FP16量化
- 动态量化
- 静态量化
- 量化感知训练
"""
import os
import time
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader


class QuantizationType(Enum):
    """量化类型"""
    FP32 = "fp32"
    FP16 = "fp16"
    INT8_DYNAMIC = "int8_dynamic"
    INT8_STATIC = "int8_static"


@dataclass
class QuantizationConfig:
    """量化配置"""
    quantization_type: QuantizationType = QuantizationType.INT8_STATIC
    calibration_batches: int = 10
    calibration_batch_size: int = 4
    per_channel: bool = True
    symmetric: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "quantization_type": self.quantization_type.value,
            "calibration_batches": self.calibration_batches,
            "calibration_batch_size": self.calibration_batch_size,
            "per_channel": self.per_channel,
            "symmetric": self.symmetric
        }


class ModelQuantizer:
    """
    模型量化器
    
    提供多种量化方法，优化模型在边缘端的部署
    """
    
    def __init__(self, config: Optional[QuantizationConfig] = None):
        """
        初始化量化器
        
        :param config: 量化配置
        """
        self.config = config or QuantizationConfig()
        self.calibration_cache = []
        print(f"🔧 [ModelQuantizer] 初始化完成")
        print(f"   量化类型: {self.config.quantization_type.value}")
    
    def quantize(
        self,
        model: nn.Module,
        calibration_loader: Optional[DataLoader] = None
    ) -> nn.Module:
        """
        执行模型量化
        
        :param model: 原始模型
        :param calibration_loader: 校准数据加载器
        :return: 量化后模型
        """
        quant_type = self.config.quantization_type
        
        if quant_type == QuantizationType.FP32:
            print("📦 使用FP32精度 (无量化)")
            return model
        
        elif quant_type == QuantizationType.FP16:
            print("📦 执行FP16量化")
            return self._quantize_fp16(model)
        
        elif quant_type == QuantizationType.INT8_DYNAMIC:
            print("📦 执行INT8动态量化")
            return self._quantize_int8_dynamic(model)
        
        elif quant_type == QuantizationType.INT8_STATIC:
            print("📦 执行INT8静态量化")
            if calibration_loader is None:
                print("⚠️ 静态量化需要校准数据，使用动态量化替代")
                return self._quantize_int8_dynamic(model)
            return self._quantize_int8_static(model, calibration_loader)
        
        return model
    
    def _quantize_fp16(self, model: nn.Module) -> nn.Module:
        """FP16量化"""
        model = model.half()
        return model
    
    def _quantize_int8_dynamic(self, model: nn.Module) -> nn.Module:
        """INT8动态量化"""
        quantized_model = torch.quantization.quantize_dynamic(
            model,
            {nn.Linear, nn.Conv2d},
            dtype=torch.qint8
        )
        return quantized_model
    
    def _quantize_int8_static(
        self,
        model: nn.Module,
        calibration_loader: DataLoader
    ) -> nn.Module:
        """INT8静态量化"""
        model.eval()
        
        model.qconfig = torch.quantization.get_default_qconfig('fbgemm')
        
        torch.quantization.prepare(model, inplace=True)
        
        print(f"📊 执行校准 ({self.config.calibration_batches} 批次)...")
        with torch.no_grad():
            for i, (images, _) in enumerate(calibration_loader):
                if i >= self.config.calibration_batches:
                    break
                model(images)
        
        torch.quantization.convert(model, inplace=True)
        
        return model
    
    def compare_models(
        self,
        original_model: nn.Module,
        quantized_model: nn.Module,
        sample_input: torch.Tensor
    ) -> Dict[str, Any]:
        """
        比较原始模型和量化模型
        
        :param original_model: 原始模型
        :param quantized_model: 量化模型
        :param sample_input: 样本输入
        :return: 比较结果
        """
        results = {}
        
        original_model.eval()
        quantized_model.eval()
        
        with torch.no_grad():
            start = time.time()
            for _ in range(10):
                _ = original_model(sample_input)
            original_time = (time.time() - start) / 10 * 1000
            
            start = time.time()
            for _ in range(10):
                _ = quantized_model(sample_input)
            quantized_time = (time.time() - start) / 10 * 1000
        
        results["inference_time"] = {
            "original_ms": original_time,
            "quantized_ms": quantized_time,
            "speedup": original_time / quantized_time if quantized_time > 0 else 1.0
        }
        
        def get_model_size(model):
            torch.save(model.state_dict(), "temp_model.pt")
            size = os.path.getsize("temp_model.pt") / (1024 * 1024)
            os.remove("temp_model.pt")
            return size
        
        results["model_size"] = {
            "original_mb": get_model_size(original_model),
            "quantized_mb": get_model_size(quantized_model),
            "compression_ratio": get_model_size(original_model) / get_model_size(quantized_model)
        }
        
        return results
    
    def export_quantized_model(
        self,
        model: nn.Module,
        output_path: str,
        format: str = "torchscript"
    ):
        """
        导出量化模型
        
        :param model: 量化模型
        :param output_path: 输出路径
        :param format: 导出格式 (torchscript/onnx)
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if format == "torchscript":
            scripted = torch.jit.script(model)
            scripted.save(output_path)
            print(f"✅ TorchScript模型已保存: {output_path}")
        
        elif format == "onnx":
            dummy_input = torch.randn(1, 3, 640, 640)
            torch.onnx.export(
                model,
                dummy_input,
                output_path,
                opset_version=13,
                input_names=['images'],
                output_names=['output']
            )
            print(f"✅ ONNX模型已保存: {output_path}")


class CalibrationDataset:
    """
    校准数据集
    
    用于静态量化的校准数据
    """
    
    def __init__(
        self,
        image_dir: str,
        image_size: Tuple[int, int] = (640, 640),
        max_samples: int = 100
    ):
        """
        初始化校准数据集
        
        :param image_dir: 图像目录
        :param image_size: 图像尺寸
        :param max_samples: 最大样本数
        """
        self.image_dir = Path(image_dir)
        self.image_size = image_size
        self.max_samples = max_samples
        
        self.image_paths = list(self.image_dir.glob("*.jpg"))[:max_samples]
        if not self.image_paths:
            self.image_paths = list(self.image_dir.glob("*.png"))[:max_samples]
        
        print(f"📊 加载 {len(self.image_paths)} 个校准样本")
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        import cv2
        
        image_path = self.image_paths[idx]
        image = cv2.imread(str(image_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, self.image_size)
        image = image.transpose(2, 0, 1) / 255.0
        
        return torch.FloatTensor(image), torch.zeros(1)


def create_quantizer(
    quantization_type: str = "int8_static",
    calibration_batches: int = 10
) -> ModelQuantizer:
    """
    工厂函数: 创建量化器
    
    :param quantization_type: 量化类型
    :param calibration_batches: 校准批次数
    :return: ModelQuantizer实例
    """
    type_map = {
        "fp32": QuantizationType.FP32,
        "fp16": QuantizationType.FP16,
        "int8_dynamic": QuantizationType.INT8_DYNAMIC,
        "int8_static": QuantizationType.INT8_STATIC
    }
    
    config = QuantizationConfig(
        quantization_type=type_map.get(quantization_type, QuantizationType.INT8_STATIC),
        calibration_batches=calibration_batches
    )
    
    return ModelQuantizer(config)

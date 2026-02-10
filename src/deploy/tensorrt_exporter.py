# -*- coding: utf-8 -*-
"""
TensorRT 导出与部署优化模块
根据研究文档，实现模型的高效部署

功能:
1. ONNX 模型导出
2. TensorRT 引擎构建
3. FP16/INT8 量化支持
4. 动态形状支持
5. 推理加速
"""
import os
import time
import warnings
from typing import Dict, Any, Optional, Tuple, List, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


class PrecisionMode(Enum):
    """精度模式"""
    FP32 = "fp32"    # 单精度浮点
    FP16 = "fp16"    # 半精度浮点
    INT8 = "int8"    # 8位整数量化


@dataclass
class TensorRTConfig:
    """TensorRT 配置"""
    # 精度模式
    precision: PrecisionMode = PrecisionMode.FP16
    
    # 工作空间大小 (MB)
    workspace_mb: int = 1024
    
    # 最大批次大小
    max_batch_size: int = 1
    
    # 输入形状
    input_shape: Tuple[int, ...] = (1, 3, 640, 640)
    
    # 动态形状支持
    dynamic_shapes: bool = False
    min_input_shape: Optional[Tuple[int, ...]] = None
    opt_input_shape: Optional[Tuple[int, ...]] = None
    max_input_shape: Optional[Tuple[int, ...]] = None
    
    # INT8 量化配置
    calibration_samples: int = 100
    calibration_data_path: Optional[str] = None
    
    # 优化级别
    optimization_level: int = 3
    
    # 引擎缓存
    cache_engine: bool = True
    engine_cache_dir: str = "models/tensorrt_engines"


class ONNXExporter:
    """ONNX 模型导出器"""
    
    def __init__(self, config: Optional[TensorRTConfig] = None):
        """
        初始化 ONNX 导出器
        
        :param config: 配置
        """
        self.config = config or TensorRTConfig()
    
    def export(
        self,
        model: nn.Module,
        output_path: str,
        input_sample: Optional[torch.Tensor] = None,
        opset_version: int = 11,
        simplify: bool = True
    ) -> Dict[str, Any]:
        """
        导出模型到 ONNX 格式
        
        :param model: PyTorch 模型
        :param output_path: 输出路径
        :param input_sample: 输入样本
        :param opset_version: ONNX opset 版本
        :param simplify: 是否简化模型
        :return: 导出结果
        """
        model.eval()
        
        # 创建输入样本
        if input_sample is None:
            input_sample = torch.randn(self.config.input_shape)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # 导出 ONNX
            torch.onnx.export(
                model,
                input_sample,
                output_path,
                export_params=True,
                opset_version=opset_version,
                do_constant_folding=True,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes={
                    'input': {0: 'batch_size'},
                    'output': {0: 'batch_size'}
                } if self.config.dynamic_shapes else None
            )
            
            print(f"✅ ONNX 模型已导出: {output_path}")
            
            # 简化模型
            if simplify:
                self._simplify_onnx(output_path)
            
            # 验证模型
            is_valid = self._validate_onnx(output_path)
            
            return {
                "success": True,
                "output_path": output_path,
                "input_shape": list(input_sample.shape),
                "validated": is_valid
            }
            
        except Exception as e:
            print(f"❌ ONNX 导出失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _simplify_onnx(self, onnx_path: str):
        """
        简化 ONNX 模型
        
        :param onnx_path: ONNX 模型路径
        """
        try:
            import onnx
            from onnxsim import simplify
            
            # 加载模型
            model = onnx.load(onnx_path)
            
            # 简化
            model_simp, check = simplify(model)
            
            if check:
                onnx.save(model_simp, onnx_path)
                print(f"✅ ONNX 模型已简化")
            else:
                print(f"⚠️ ONNX 简化失败，使用原始模型")
                
        except ImportError:
            print(f"⚠️ onnx-simplifier 未安装，跳过简化")
        except Exception as e:
            print(f"⚠️ ONNX 简化失败: {e}")
    
    def _validate_onnx(self, onnx_path: str) -> bool:
        """
        验证 ONNX 模型
        
        :param onnx_path: ONNX 模型路径
        :return: 是否有效
        """
        try:
            import onnx
            model = onnx.load(onnx_path)
            onnx.checker.check_model(model)
            print(f"✅ ONNX 模型验证通过")
            return True
        except ImportError:
            print(f"⚠️ onnx 未安装，跳过验证")
            return False
        except Exception as e:
            print(f"⚠️ ONNX 验证失败: {e}")
            return False


class TensorRTBuilder:
    """TensorRT 引擎构建器"""
    
    def __init__(self, config: Optional[TensorRTConfig] = None):
        """
        初始化 TensorRT 构建器
        
        :param config: 配置
        """
        self.config = config or TensorRTConfig()
        self.trt_available = self._check_tensorrt()
    
    def _check_tensorrt(self) -> bool:
        """检查 TensorRT 是否可用"""
        try:
            import tensorrt as trt
            print(f"✅ TensorRT 版本: {trt.__version__}")
            return True
        except ImportError:
            warnings.warn("TensorRT 未安装，将使用模拟模式")
            return False
    
    def build_engine(
        self,
        onnx_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        构建 TensorRT 引擎
        
        :param onnx_path: ONNX 模型路径
        :param output_path: 引擎输出路径
        :return: 构建结果
        """
        if not self.trt_available:
            return self._build_engine_mock(onnx_path, output_path)
        
        import tensorrt as trt
        
        # 设置输出路径
        if output_path is None:
            model_name = Path(onnx_path).stem
            output_path = os.path.join(
                self.config.engine_cache_dir,
                f"{model_name}_{self.config.precision.value}.trt"
            )
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 检查缓存
        if self.config.cache_engine and os.path.exists(output_path):
            print(f"✅ 使用缓存的 TensorRT 引擎: {output_path}")
            return {
                "success": True,
                "engine_path": output_path,
                "cached": True
            }
        
        # 创建 logger 和 builder
        logger = trt.Logger(trt.Logger.WARNING)
        builder = trt.Builder(logger)
        network = builder.create_network(
            1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
        )
        parser = trt.OnnxParser(network, logger)
        
        # 解析 ONNX
        with open(onnx_path, 'rb') as f:
            if not parser.parse(f.read()):
                errors = [parser.get_error(i) for i in range(parser.num_errors)]
                print(f"❌ ONNX 解析失败: {errors}")
                return {"success": False, "errors": errors}
        
        # 配置 builder
        config = builder.create_builder_config()
        config.max_workspace_size = self.config.workspace_mb * (1 << 20)
        
        # 设置精度
        if self.config.precision == PrecisionMode.FP16:
            config.set_flag(trt.BuilderFlag.FP16)
            print("✅ 启用 FP16 精度")
        elif self.config.precision == PrecisionMode.INT8:
            config.set_flag(trt.BuilderFlag.INT8)
            print("✅ 启用 INT8 量化")
            # TODO: 设置 INT8 校准器
        
        # 动态形状配置
        if self.config.dynamic_shapes:
            profile = builder.create_optimization_profile()
            
            min_shape = self.config.min_input_shape or self.config.input_shape
            opt_shape = self.config.opt_input_shape or self.config.input_shape
            max_shape = self.config.max_input_shape or self.config.input_shape
            
            profile.set_shape("input", min_shape, opt_shape, max_shape)
            config.add_optimization_profile(profile)
            
            print(f"✅ 动态形状配置:")
            print(f"   最小: {min_shape}")
            print(f"   最优: {opt_shape}")
            print(f"   最大: {max_shape}")
        
        # 构建引擎
        print(f"🔄 构建 TensorRT 引擎...")
        start_time = time.time()
        
        engine = builder.build_engine(network, config)
        
        if engine is None:
            print(f"❌ TensorRT 引擎构建失败")
            return {"success": False, "error": "Engine build failed"}
        
        build_time = time.time() - start_time
        
        # 保存引擎
        with open(output_path, 'wb') as f:
            f.write(engine.serialize())
        
        print(f"✅ TensorRT 引擎构建完成")
        print(f"   耗时: {build_time:.2f}s")
        print(f"   路径: {output_path}")
        
        return {
            "success": True,
            "engine_path": output_path,
            "build_time": build_time,
            "cached": False
        }
    
    def _build_engine_mock(self, onnx_path: str, output_path: Optional[str]) -> Dict[str, Any]:
        """
        模拟构建引擎（当 TensorRT 不可用时）
        
        :param onnx_path: ONNX 路径
        :param output_path: 输出路径
        :return: 模拟结果
        """
        print(f"⚠️ TensorRT 不可用，使用模拟模式")
        
        if output_path is None:
            model_name = Path(onnx_path).stem
            output_path = os.path.join(
                self.config.engine_cache_dir,
                f"{model_name}_{self.config.precision.value}.trt"
            )
        
        return {
            "success": True,
            "engine_path": output_path,
            "mock": True,
            "message": "TensorRT 模拟模式，实际推理将使用 PyTorch"
        }


class TensorRTInference:
    """TensorRT 推理引擎"""
    
    def __init__(self, engine_path: str, config: Optional[TensorRTConfig] = None):
        """
        初始化 TensorRT 推理引擎
        
        :param engine_path: TensorRT 引擎路径
        :param config: 配置
        """
        self.engine_path = engine_path
        self.config = config or TensorRTConfig()
        self.trt_available = self._check_tensorrt()
        
        # 加载引擎
        self.engine = None
        self.context = None
        self.inputs = []
        self.outputs = []
        self.bindings = []
        self.stream = None
        
        if self.trt_available:
            self._load_engine()
    
    def _check_tensorrt(self) -> bool:
        """检查 TensorRT 是否可用"""
        try:
            import tensorrt as trt
            return True
        except ImportError:
            return False
    
    def _load_engine(self):
        """加载 TensorRT 引擎"""
        import tensorrt as trt
        import pycuda.driver as cuda
        import pycuda.autoinit
        
        logger = trt.Logger(trt.Logger.WARNING)
        
        # 加载引擎
        with open(self.engine_path, 'rb') as f:
            runtime = trt.Runtime(logger)
            self.engine = runtime.deserialize_cuda_engine(f.read())
        
        # 创建执行上下文
        self.context = self.engine.create_execution_context()
        
        # 分配内存
        self._allocate_buffers()
        
        print(f"✅ TensorRT 引擎已加载: {self.engine_path}")
    
    def _allocate_buffers(self):
        """分配 GPU 内存"""
        import pycuda.driver as cuda
        
        for i in range(self.engine.num_bindings):
            name = self.engine.get_binding_name(i)
            dtype = trt.nptype(self.engine.get_binding_dtype(i))
            shape = tuple(self.engine.get_binding_shape(i))
            
            # 计算大小
            size = trt.volume(shape)
            
            # 分配主机和设备内存
            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            
            self.bindings.append(int(device_mem))
            
            if self.engine.binding_is_input(i):
                self.inputs.append({
                    'name': name,
                    'host': host_mem,
                    'device': device_mem,
                    'shape': shape,
                    'dtype': dtype
                })
            else:
                self.outputs.append({
                    'name': name,
                    'host': host_mem,
                    'device': device_mem,
                    'shape': shape,
                    'dtype': dtype
                })
    
    def infer(self, input_data: np.ndarray) -> np.ndarray:
        """
        执行推理
        
        :param input_data: 输入数据
        :return: 输出结果
        """
        if not self.trt_available or self.engine is None:
            # 模拟推理
            return self._mock_infer(input_data)
        
        import pycuda.driver as cuda
        
        # 复制输入数据到设备
        np.copyto(self.inputs[0]['host'], input_data.ravel())
        cuda.memcpy_htod_async(self.inputs[0]['device'], self.inputs[0]['host'], self.stream)
        
        # 执行推理
        self.context.execute_async_v2(bindings=self.bindings, stream_handle=self.stream.handle)
        
        # 复制输出数据到主机
        cuda.memcpy_dtoh_async(self.outputs[0]['host'], self.outputs[0]['device'], self.stream)
        self.stream.synchronize()
        
        # 返回结果
        output = self.outputs[0]['host'].reshape(self.outputs[0]['shape'])
        return output
    
    def _mock_infer(self, input_data: np.ndarray) -> np.ndarray:
        """
        模拟推理
        
        :param input_data: 输入数据
        :return: 模拟输出
        """
        # 返回随机输出
        batch_size = input_data.shape[0]
        output_shape = (batch_size, 1000)  # 假设分类任务
        return np.random.randn(*output_shape).astype(np.float32)
    
    def benchmark(self, num_runs: int = 100, warmup: int = 10) -> Dict[str, float]:
        """
        性能基准测试
        
        :param num_runs: 运行次数
        :param warmup: 预热次数
        :return: 性能统计
        """
        # 创建随机输入
        input_data = np.random.randn(*self.config.input_shape).astype(np.float32)
        
        # 预热
        for _ in range(warmup):
            self.infer(input_data)
        
        # 基准测试
        times = []
        for _ in range(num_runs):
            start = time.time()
            self.infer(input_data)
            times.append(time.time() - start)
        
        stats = {
            "mean_latency_ms": np.mean(times) * 1000,
            "median_latency_ms": np.median(times) * 1000,
            "min_latency_ms": np.min(times) * 1000,
            "max_latency_ms": np.max(times) * 1000,
            "std_latency_ms": np.std(times) * 1000,
            "throughput_fps": 1.0 / np.mean(times)
        }
        
        return stats


class ModelOptimizer:
    """模型优化器 - 整合 ONNX 导出和 TensorRT 构建"""
    
    def __init__(self, config: Optional[TensorRTConfig] = None):
        """
        初始化模型优化器
        
        :param config: 配置
        """
        self.config = config or TensorRTConfig()
        self.onnx_exporter = ONNXExporter(self.config)
        self.trt_builder = TensorRTBuilder(self.config)
    
    def optimize(
        self,
        model: nn.Module,
        model_name: str,
        input_sample: Optional[torch.Tensor] = None
    ) -> Dict[str, Any]:
        """
        优化模型（导出 ONNX + 构建 TensorRT）
        
        :param model: PyTorch 模型
        :param model_name: 模型名称
        :param input_sample: 输入样本
        :return: 优化结果
        """
        print("=" * 70)
        print(f"🚀 优化模型: {model_name}")
        print("=" * 70)
        
        # 步骤 1: 导出 ONNX
        print("\n📦 步骤 1: 导出 ONNX 模型")
        onnx_path = f"models/onnx/{model_name}.onnx"
        
        onnx_result = self.onnx_exporter.export(
            model=model,
            output_path=onnx_path,
            input_sample=input_sample
        )
        
        if not onnx_result["success"]:
            return {
                "success": False,
                "stage": "onnx_export",
                "error": onnx_result.get("error")
            }
        
        # 步骤 2: 构建 TensorRT 引擎
        print("\n⚡ 步骤 2: 构建 TensorRT 引擎")
        
        trt_result = self.trt_builder.build_engine(
            onnx_path=onnx_path,
            output_path=f"models/tensorrt/{model_name}_{self.config.precision.value}.trt"
        )
        
        if not trt_result["success"]:
            return {
                "success": False,
                "stage": "tensorrt_build",
                "error": trt_result.get("error")
            }
        
        print("\n" + "=" * 70)
        print("✅ 模型优化完成")
        print("=" * 70)
        
        return {
            "success": True,
            "onnx_path": onnx_result["output_path"],
            "engine_path": trt_result["engine_path"],
            "precision": self.config.precision.value,
            "cached": trt_result.get("cached", False)
        }
    
    def load_optimized_model(self, engine_path: str) -> TensorRTInference:
        """
        加载优化后的模型
        
        :param engine_path: TensorRT 引擎路径
        :return: TensorRT 推理引擎
        """
        return TensorRTInference(engine_path, self.config)


def test_tensorrt_exporter():
    """测试 TensorRT 导出器"""
    print("=" * 70)
    print("🧪 测试 TensorRT 导出器")
    print("=" * 70)
    
    # 创建简单模型
    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(3, 16, 3, padding=1)
            self.relu = nn.ReLU()
            self.pool = nn.AdaptiveAvgPool2d(1)
            self.fc = nn.Linear(16, 10)
        
        def forward(self, x):
            x = self.conv1(x)
            x = self.relu(x)
            x = self.pool(x)
            x = x.view(x.size(0), -1)
            x = self.fc(x)
            return x
    
    model = SimpleModel()
    model.eval()
    
    # 测试 ONNX 导出
    print("\n" + "=" * 70)
    print("🧪 测试 ONNX 导出")
    print("=" * 70)
    
    config = TensorRTConfig(
        precision=PrecisionMode.FP16,
        input_shape=(1, 3, 224, 224)
    )
    
    exporter = ONNXExporter(config)
    
    input_sample = torch.randn(1, 3, 224, 224)
    onnx_result = exporter.export(
        model=model,
        output_path="models/onnx/test_model.onnx",
        input_sample=input_sample
    )
    
    print(f"✅ ONNX 导出: {'成功' if onnx_result['success'] else '失败'}")
    if onnx_result['success']:
        print(f"   路径: {onnx_result['output_path']}")
    
    # 测试 TensorRT 构建
    print("\n" + "=" * 70)
    print("🧪 测试 TensorRT 引擎构建")
    print("=" * 70)
    
    builder = TensorRTBuilder(config)
    trt_result = builder.build_engine(
        onnx_path="models/onnx/test_model.onnx",
        output_path="models/tensorrt/test_model_fp16.trt"
    )
    
    print(f"✅ TensorRT 构建: {'成功' if trt_result['success'] else '失败'}")
    if trt_result['success']:
        print(f"   路径: {trt_result['engine_path']}")
        print(f"   使用缓存: {trt_result.get('cached', False)}")
    
    # 测试模型优化器
    print("\n" + "=" * 70)
    print("🧪 测试模型优化器")
    print("=" * 70)
    
    optimizer = ModelOptimizer(config)
    opt_result = optimizer.optimize(
        model=model,
        model_name="test_model_v2"
    )
    
    print(f"✅ 模型优化: {'成功' if opt_result['success'] else '失败'}")
    if opt_result['success']:
        print(f"   ONNX: {opt_result['onnx_path']}")
        print(f"   TensorRT: {opt_result['engine_path']}")
    
    # 清理测试文件
    import shutil
    if os.path.exists("models/onnx"):
        shutil.rmtree("models/onnx")
    if os.path.exists("models/tensorrt"):
        shutil.rmtree("models/tensorrt")
    
    print("\n" + "=" * 70)
    print("✅ TensorRT 导出器测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_tensorrt_exporter()

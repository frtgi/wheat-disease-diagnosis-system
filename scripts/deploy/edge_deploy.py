# -*- coding: utf-8 -*-
"""
边缘端部署脚本
根据研究文档第8章，实现模型的边缘端部署优化

功能：
1. 模型导出 (ONNX/TensorRT)
2. INT8 量化
3. 推理性能测试
4. 部署包生成

目标硬件：NVIDIA Jetson Orin NX
目标性能：> 30 FPS
"""
import os
import sys
import json
import time
import argparse
import torch
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')


@dataclass
class EdgeDeployConfig:
    """边缘端部署配置"""
    model_path: str = "models/wheat_disease_v5_optimized_phase2/weights/best.pt"
    output_dir: str = "deploy/edge"
    input_size: int = 640
    batch_size: int = 1
    precision: str = "fp16"  # fp32, fp16, int8
    target_fps: int = 30
    workspace_mb: int = 1024
    calibration_samples: int = 100


class EdgeDeployer:
    """
    边缘端部署器
    
    实现 YOLOv8 模型的边缘端部署优化：
    1. ONNX 导出
    2. TensorRT 转换
    3. INT8 量化
    4. 性能测试
    """
    
    def __init__(self, config: Optional[EdgeDeployConfig] = None):
        """
        初始化部署器
        
        :param config: 部署配置
        """
        self.config = config or EdgeDeployConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.onnx_path = None
        self.engine_path = None
        
        print("=" * 60)
        print("🚀 [Edge Deploy] 边缘端部署器初始化")
        print("=" * 60)
        print(f"   模型路径: {self.config.model_path}")
        print(f"   输出目录: {self.config.output_dir}")
        print(f"   输入尺寸: {self.config.input_size}")
        print(f"   精度模式: {self.config.precision}")
        print(f"   目标 FPS: {self.config.target_fps}")
    
    def load_model(self) -> bool:
        """
        加载模型
        
        :return: 是否成功
        """
        print("\n🔄 加载模型...")
        
        try:
            from ultralytics import YOLO
            
            self.model = YOLO(self.config.model_path)
            print(f"✅ 模型加载成功: {self.config.model_path}")
            return True
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            return False
    
    def export_onnx(self) -> Optional[str]:
        """
        导出 ONNX 模型
        
        :return: ONNX 文件路径
        """
        print("\n📦 导出 ONNX 模型...")
        
        if self.model is None:
            if not self.load_model():
                return None
        
        try:
            onnx_path = self.output_dir / "model.onnx"
            
            self.model.export(
                format="onnx",
                imgsz=self.config.input_size,
                batch=self.config.batch_size,
                opset=12,
                simplify=True,
                output=str(onnx_path).replace(".onnx", "")
            )
            
            self.onnx_path = onnx_path
            print(f"✅ ONNX 导出成功: {onnx_path}")
            
            return str(onnx_path)
            
        except Exception as e:
            print(f"❌ ONNX 导出失败: {e}")
            return None
    
    def export_tensorrt(self) -> Optional[str]:
        """
        导出 TensorRT 引擎
        
        :return: TensorRT 引擎路径
        """
        print("\n⚡ 导出 TensorRT 引擎...")
        
        if self.model is None:
            if not self.load_model():
                return None
        
        try:
            engine_path = self.output_dir / f"model_{self.config.precision}.engine"
            
            # 检查 TensorRT 支持
            try:
                import tensorrt as trt
                print(f"   TensorRT 版本: {trt.__version__}")
            except ImportError:
                print("⚠️ TensorRT 未安装，跳过引擎构建")
                print("   提示: 在 Jetson 设备上运行此脚本以生成 TensorRT 引擎")
                return None
            
            # 导出 TensorRT
            self.model.export(
                format="engine",
                imgsz=self.config.input_size,
                batch=self.config.batch_size,
                half=(self.config.precision == "fp16"),
                int8=(self.config.precision == "int8"),
                device=0,
                workspace=self.config.workspace_mb,
                output=str(engine_path).replace(".engine", "")
            )
            
            self.engine_path = engine_path
            print(f"✅ TensorRT 导出成功: {engine_path}")
            
            return str(engine_path)
            
        except Exception as e:
            print(f"❌ TensorRT 导出失败: {e}")
            return None
    
    def benchmark_inference(self, num_runs: int = 100) -> Dict[str, Any]:
        """
        推理性能测试
        
        :param num_runs: 测试次数
        :return: 性能结果
        """
        print(f"\n📊 推理性能测试 ({num_runs} 次)...")
        
        if self.model is None:
            if not self.load_model():
                return {}
        
        try:
            # 预热
            dummy_input = np.random.randint(0, 255, 
                (self.config.input_size, self.config.input_size, 3), dtype=np.uint8)
            
            for _ in range(10):
                _ = self.model(dummy_input, verbose=False)
            
            # 测试
            latencies = []
            
            for i in range(num_runs):
                start = time.perf_counter()
                _ = self.model(dummy_input, verbose=False)
                end = time.perf_counter()
                
                latencies.append((end - start) * 1000)  # ms
            
            # 统计
            avg_latency = np.mean(latencies)
            min_latency = np.min(latencies)
            max_latency = np.max(latencies)
            fps = 1000 / avg_latency
            
            results = {
                "avg_latency_ms": round(avg_latency, 2),
                "min_latency_ms": round(min_latency, 2),
                "max_latency_ms": round(max_latency, 2),
                "fps": round(fps, 1),
                "target_fps": self.config.target_fps,
                "meets_target": fps >= self.config.target_fps
            }
            
            print(f"   平均延迟: {avg_latency:.2f} ms")
            print(f"   最小延迟: {min_latency:.2f} ms")
            print(f"   最大延迟: {max_latency:.2f} ms")
            print(f"   FPS: {fps:.1f}")
            
            if results["meets_target"]:
                print(f"✅ 达到目标 FPS ({self.config.target_fps})")
            else:
                print(f"⚠️ 未达到目标 FPS ({self.config.target_fps})")
            
            return results
            
        except Exception as e:
            print(f"❌ 性能测试失败: {e}")
            return {}
    
    def create_deployment_package(self) -> str:
        """
        创建部署包
        
        :return: 部署包路径
        """
        print("\n📦 创建部署包...")
        
        package_dir = self.output_dir / "package"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制模型文件
        if self.onnx_path and self.onnx_path.exists():
            import shutil
            shutil.copy(self.onnx_path, package_dir / "model.onnx")
        
        if self.engine_path and self.engine_path.exists():
            import shutil
            shutil.copy(self.engine_path, package_dir / f"model_{self.config.precision}.engine")
        
        # 创建配置文件
        deploy_config = {
            "model": {
                "type": "yolov8",
                "input_size": self.config.input_size,
                "precision": self.config.precision
            },
            "deployment": {
                "target_device": "Jetson Orin NX",
                "target_fps": self.config.target_fps,
                "created_at": datetime.now().isoformat()
            },
            "classes": [
                "条锈病", "叶锈病", "秆锈病", "白粉病", "赤霉病",
                "纹枯病", "根腐病", "全蚀病", "叶枯病", "颖枯病",
                "黑穗病", "病毒病", "蚜虫", "红蜘蛛", "吸浆虫"
            ]
        }
        
        config_path = package_dir / "deploy_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(deploy_config, f, ensure_ascii=False, indent=2)
        
        # 创建推理脚本
        inference_script = '''# -*- coding: utf-8 -*-
"""
边缘端推理脚本
用于 Jetson Orin NX 设备
"""
import cv2
import numpy as np
import json
import time
from pathlib import Path

class EdgeInference:
    def __init__(self, model_path, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.input_size = self.config['model']['input_size']
        self.classes = self.config['classes']
        
        # 加载模型
        from ultralytics import YOLO
        self.model = YOLO(model_path)
    
    def preprocess(self, image):
        """预处理图像"""
        h, w = image.shape[:2]
        scale = min(self.input_size / h, self.input_size / w)
        new_h, new_w = int(h * scale), int(w * scale)
        
        resized = cv2.resize(image, (new_w, new_h))
        
        pad_h = self.input_size - new_h
        pad_w = self.input_size - new_w
        top = pad_h // 2
        bottom = pad_h - top
        left = pad_w // 2
        right = pad_w - left
        
        padded = cv2.copyMakeBorder(resized, top, bottom, left, right,
                                    cv2.BORDER_CONSTANT, value=(114, 114, 114))
        
        return padded, scale, (left, top)
    
    def infer(self, image, conf_threshold=0.5):
        """执行推理"""
        start = time.perf_counter()
        
        results = self.model(image, conf=conf_threshold, verbose=False)
        
        latency = (time.perf_counter() - start) * 1000
        
        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({
                    'class': self.classes[int(box.cls)],
                    'confidence': float(box.conf),
                    'bbox': box.xyxy[0].tolist()
                })
        
        return {
            'detections': detections,
            'latency_ms': latency,
            'fps': 1000 / latency
        }

if __name__ == "__main__":
    inference = EdgeInference("model.onnx", "deploy_config.json")
    
    # 测试
    import numpy as np
    test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    result = inference.infer(test_image)
    print(f"FPS: {result['fps']:.1f}")
'''
        
        script_path = package_dir / "inference.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(inference_script)
        
        print(f"✅ 部署包创建成功: {package_dir}")
        
        return str(package_dir)
    
    def run_full_deployment(self) -> Dict[str, Any]:
        """
        执行完整部署流程
        
        :return: 部署结果
        """
        print("\n" + "=" * 60)
        print("🚀 开始完整部署流程")
        print("=" * 60)
        
        results = {
            "started_at": datetime.now().isoformat(),
            "config": asdict(self.config)
        }
        
        # 1. 加载模型
        if not self.load_model():
            results["status"] = "failed"
            results["error"] = "模型加载失败"
            return results
        
        # 2. 导出 ONNX
        onnx_path = self.export_onnx()
        results["onnx_exported"] = onnx_path is not None
        
        # 3. 导出 TensorRT (可选)
        engine_path = self.export_tensorrt()
        results["tensorrt_exported"] = engine_path is not None
        
        # 4. 性能测试
        benchmark_results = self.benchmark_inference()
        results["benchmark"] = benchmark_results
        
        # 5. 创建部署包
        package_path = self.create_deployment_package()
        results["package_path"] = package_path
        
        results["status"] = "completed"
        results["completed_at"] = datetime.now().isoformat()
        
        # 保存结果
        results_path = self.output_dir / "deployment_results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ 部署完成")
        print("=" * 60)
        print(f"   ONNX: {'✅' if results['onnx_exported'] else '❌'}")
        print(f"   TensorRT: {'✅' if results['tensorrt_exported'] else '⚠️'}")
        print(f"   FPS: {benchmark_results.get('fps', 'N/A')}")
        print(f"   部署包: {package_path}")
        
        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="边缘端部署")
    parser.add_argument("--model", default="models/wheat_disease_v5_optimized_phase2/weights/best.pt")
    parser.add_argument("--output", default="deploy/edge")
    parser.add_argument("--size", type=int, default=640)
    parser.add_argument("--precision", default="fp16", choices=["fp32", "fp16", "int8"])
    parser.add_argument("--target-fps", type=int, default=30)
    
    args = parser.parse_args()
    
    config = EdgeDeployConfig(
        model_path=args.model,
        output_dir=args.output,
        input_size=args.size,
        precision=args.precision,
        target_fps=args.target_fps
    )
    
    deployer = EdgeDeployer(config)
    results = deployer.run_full_deployment()
    
    print(f"\n📄 部署结果: {json.dumps(results, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    main()

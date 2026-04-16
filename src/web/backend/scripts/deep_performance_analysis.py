"""
深度性能分析脚本
分析 Qwen3-VL-2B-Instruct 模型在 RTX 3050 (4GB) 上的性能瓶颈
"""
import os
import sys
import time
import json
import torch
import psutil
import GPUtil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

class DeepPerformanceAnalyzer:
    """深度性能分析器"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "hardware": {},
            "model_loading": {},
            "inference": {},
            "bottlenecks": [],
            "recommendations": []
        }
    
    def analyze_hardware(self) -> Dict[str, Any]:
        """分析硬件配置"""
        print("\n" + "=" * 60)
        print("[1] 硬件配置分析")
        print("=" * 60)
        
        hardware = {
            "cpu": {
                "cores": psutil.cpu_count(logical=False),
                "threads": psutil.cpu_count(logical=True),
                "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2)
            },
            "gpu": {}
        }
        
        # GPU 信息
        if torch.cuda.is_available():
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                hardware["gpu"] = {
                    "name": gpu.name,
                    "memory_total_mb": gpu.memoryTotal,
                    "memory_free_mb": gpu.memoryFree,
                    "memory_used_mb": gpu.memoryUsed,
                    "utilization_percent": gpu.load * 100,
                    "temperature_c": gpu.temperature
                }
                print(f"  GPU: {gpu.name}")
                print(f"  显存: {gpu.memoryTotal}MB (已用: {gpu.memoryUsed}MB)")
                print(f"  GPU利用率: {gpu.load * 100:.1f}%")
        
        print(f"  CPU: {hardware['cpu']['cores']}核 {hardware['cpu']['threads']}线程")
        print(f"  内存: {hardware['memory']['total_gb']}GB")
        
        self.results["hardware"] = hardware
        return hardware
    
    def analyze_model_loading(self) -> Dict[str, Any]:
        """分析模型加载性能"""
        print("\n" + "=" * 60)
        print("[2] 模型加载性能分析")
        print("=" * 60)
        
        model_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "Qwen3-VL-2B-Instruct"
        
        loading_result = {
            "model_path": str(model_path),
            "model_exists": model_path.exists(),
            "load_time_seconds": 0,
            "memory_before_mb": 0,
            "memory_after_mb": 0,
            "memory_delta_mb": 0
        }
        
        # 记录加载前显存
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            memory_before = torch.cuda.memory_allocated() / (1024**2)
            loading_result["memory_before_mb"] = round(memory_before, 2)
        
        # 加载模型
        start_time = time.time()
        try:
            from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
            
            print(f"  正在加载模型: {model_path}")
            
            # 使用 BF16 + CPU Offload
            model = Qwen3VLForConditionalGeneration.from_pretrained(
                str(model_path),
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            processor = AutoProcessor.from_pretrained(
                str(model_path),
                trust_remote_code=True
            )
            
            load_time = time.time() - start_time
            loading_result["load_time_seconds"] = round(load_time, 2)
            
            # 记录加载后显存
            if torch.cuda.is_available():
                memory_after = torch.cuda.memory_allocated() / (1024**2)
                memory_peak = torch.cuda.max_memory_allocated() / (1024**2)
                loading_result["memory_after_mb"] = round(memory_after, 2)
                loading_result["memory_peak_mb"] = round(memory_peak, 2)
                loading_result["memory_delta_mb"] = round(memory_after - memory_before, 2)
            
            print(f"  加载时间: {load_time:.2f}秒")
            print(f"  显存占用: {loading_result['memory_after_mb']}MB")
            print(f"  显存峰值: {loading_result.get('memory_peak_mb', 0)}MB")
            
            # 保存模型引用用于后续测试
            self.model = model
            self.processor = processor
            
        except Exception as e:
            loading_result["error"] = str(e)
            print(f"  加载失败: {e}")
        
        self.results["model_loading"] = loading_result
        return loading_result
    
    def analyze_inference(self) -> Dict[str, Any]:
        """分析推理性能"""
        print("\n" + "=" * 60)
        print("[3] 推理性能分析")
        print("=" * 60)
        
        if not hasattr(self, 'model'):
            print("  模型未加载，跳过推理分析")
            return {}
        
        inference_result = {
            "warmup": {},
            "inference_runs": [],
            "average_time_seconds": 0,
            "tokens_per_second": 0
        }
        
        # 创建测试输入
        from PIL import Image
        import numpy as np
        
        # 创建随机测试图像
        test_image = Image.fromarray(np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        
        # 预热
        print("  预热模型...")
        warmup_start = time.time()
        try:
            messages = [
                {"role": "system", "content": "你是一位专业的小麦病害诊断专家。"},
                {"role": "user", "content": [
                    {"type": "image", "image": test_image},
                    {"type": "text", "text": "请分析这张图像。"}
                ]}
            ]
            
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=text, images=test_image, return_tensors="pt")
            inputs = inputs.to(self.model.device)
            
            # 短生成预热
            with torch.no_grad():
                _ = self.model.generate(**inputs, max_new_tokens=10)
            
            warmup_time = time.time() - warmup_start
            inference_result["warmup"]["time_seconds"] = round(warmup_time, 2)
            print(f"  预热完成: {warmup_time:.2f}秒")
            
        except Exception as e:
            inference_result["warmup"]["error"] = str(e)
            print(f"  预热失败: {e}")
            return inference_result
        
        # 多次推理测试
        print("  执行推理测试...")
        inference_times = []
        total_tokens = 0
        
        for i in range(3):
            torch.cuda.reset_peak_memory_stats()
            memory_before = torch.cuda.memory_allocated() / (1024**2)
            
            start_time = time.time()
            try:
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=64,
                        do_sample=False
                    )
                
                inference_time = time.time() - start_time
                memory_after = torch.cuda.memory_allocated() / (1024**2)
                memory_peak = torch.cuda.max_memory_allocated() / (1024**2)
                
                generated_tokens = outputs.shape[1] - inputs["input_ids"].shape[1]
                total_tokens += generated_tokens
                
                run_result = {
                    "run": i + 1,
                    "time_seconds": round(inference_time, 2),
                    "tokens_generated": generated_tokens,
                    "memory_before_mb": round(memory_before, 2),
                    "memory_after_mb": round(memory_after, 2),
                    "memory_peak_mb": round(memory_peak, 2),
                    "tokens_per_second": round(generated_tokens / inference_time, 2) if inference_time > 0 else 0
                }
                
                inference_times.append(inference_time)
                inference_result["inference_runs"].append(run_result)
                
                print(f"  第{i+1}次推理: {inference_time:.2f}秒, {generated_tokens}tokens, 峰值显存: {memory_peak:.0f}MB")
                
            except Exception as e:
                print(f"  第{i+1}次推理失败: {e}")
        
        # 计算平均值
        if inference_times:
            avg_time = sum(inference_times) / len(inference_times)
            inference_result["average_time_seconds"] = round(avg_time, 2)
            inference_result["tokens_per_second"] = round(total_tokens / sum(inference_times), 2)
            print(f"  平均推理时间: {avg_time:.2f}秒")
            print(f"  平均生成速度: {inference_result['tokens_per_second']} tokens/秒")
        
        self.results["inference"] = inference_result
        return inference_result
    
    def identify_bottlenecks(self) -> List[str]:
        """识别性能瓶颈"""
        print("\n" + "=" * 60)
        print("[4] 性能瓶颈识别")
        print("=" * 60)
        
        bottlenecks = []
        
        # 检查显存使用
        hardware = self.results.get("hardware", {})
        gpu = hardware.get("gpu", {})
        
        if gpu:
            memory_used = gpu.get("memory_used_mb", 0)
            memory_total = gpu.get("memory_total_mb", 4096)
            memory_ratio = memory_used / memory_total
            
            if memory_ratio > 0.9:
                bottleneck = f"显存使用率过高 ({memory_ratio*100:.1f}%)，可能导致频繁的内存交换"
                bottlenecks.append(bottleneck)
                print(f"  ⚠️ {bottleneck}")
        
        # 检查推理时间
        inference = self.results.get("inference", {})
        avg_time = inference.get("average_time_seconds", 0)
        
        if avg_time > 30:
            bottleneck = f"推理时间过长 ({avg_time:.1f}秒)，需要优化"
            bottlenecks.append(bottleneck)
            print(f"  ⚠️ {bottleneck}")
        
        # 检查生成速度
        tokens_per_second = inference.get("tokens_per_second", 0)
        if tokens_per_second < 5:
            bottleneck = f"生成速度过慢 ({tokens_per_second:.1f} tokens/秒)"
            bottlenecks.append(bottleneck)
            print(f"  ⚠️ {bottleneck}")
        
        # 检查 GPU 利用率
        gpu_util = gpu.get("utilization_percent", 0)
        if gpu_util < 50:
            bottleneck = f"GPU 利用率较低 ({gpu_util:.1f}%)，可能存在 CPU 瓶颈"
            bottlenecks.append(bottleneck)
            print(f"  ⚠️ {bottleneck}")
        
        if not bottlenecks:
            print("  ✅ 未发现明显性能瓶颈")
        
        self.results["bottlenecks"] = bottlenecks
        return bottlenecks
    
    def generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        print("\n" + "=" * 60)
        print("[5] 优化建议")
        print("=" * 60)
        
        recommendations = []
        
        # 基于瓶颈生成建议
        bottlenecks = self.results.get("bottlenecks", [])
        
        for bottleneck in bottlenecks:
            if "显存" in bottleneck:
                rec = "建议：使用更小的模型或启用 INT4/INT8 量化"
                recommendations.append(rec)
                print(f"  💡 {rec}")
            
            if "推理时间" in bottleneck or "生成速度" in bottleneck:
                rec = "建议：减少 max_new_tokens，禁用 Thinking 模式"
                recommendations.append(rec)
                print(f"  💡 {rec}")
                
                rec = "建议：使用 torch.compile() 优化模型"
                recommendations.append(rec)
                print(f"  💡 {rec}")
            
            if "GPU 利用率" in bottleneck:
                rec = "建议：检查数据预处理是否在 CPU 上成为瓶颈"
                recommendations.append(rec)
                print(f"  💡 {rec}")
        
        # 通用建议
        general_recs = [
            "使用 flash_attention_2 加速注意力计算",
            "启用 bfloat16 混合精度推理",
            "使用 torch.inference_mode() 替代 torch.no_grad()",
            "考虑使用 vLLM 或 TensorRT-LLM 进行部署优化"
        ]
        
        for rec in general_recs:
            if rec not in recommendations:
                recommendations.append(rec)
                print(f"  💡 {rec}")
        
        self.results["recommendations"] = recommendations
        return recommendations
    
    def save_report(self, output_path: str = None):
        """保存分析报告"""
        if output_path is None:
            output_path = Path(__file__).parent.parent / "performance_analysis_report.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {output_path}")
    
    def run_full_analysis(self):
        """执行完整分析"""
        print("=" * 60)
        print("Qwen3-VL-2B-Instruct 深度性能分析")
        print("=" * 60)
        
        self.analyze_hardware()
        self.analyze_model_loading()
        self.analyze_inference()
        self.identify_bottlenecks()
        self.generate_recommendations()
        self.save_report()
        
        print("\n" + "=" * 60)
        print("分析完成")
        print("=" * 60)


if __name__ == "__main__":
    analyzer = DeepPerformanceAnalyzer()
    analyzer.run_full_analysis()

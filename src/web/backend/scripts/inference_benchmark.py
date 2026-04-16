# -*- coding: utf-8 -*-
"""
推理性能基准测试脚本
测试不同配置下的模型推理性能
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
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """基准测试结果数据类"""
    config_name: str
    avg_latency_ms: float
    first_latency_ms: float
    throughput_tokens_per_sec: float
    peak_memory_mb: float
    gpu_utilization_percent: float
    total_tokens: int
    num_runs: int
    details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BenchmarkConfig:
    """基准测试配置数据类"""
    name: str
    use_int4: bool = False
    max_new_tokens: int = 64
    batch_size: int = 1
    use_bf16: bool = True
    warmup_runs: int = 1
    test_runs: int = 3


class InferenceBenchmark:
    """推理性能基准测试类"""
    
    def __init__(self, model_path: str):
        """
        初始化基准测试器
        
        :param model_path: 模型路径
        """
        self.model_path = Path(model_path)
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.results: List[BenchmarkResult] = []
        self.hardware_info: Dict[str, Any] = {}
        
    def collect_hardware_info(self) -> Dict[str, Any]:
        """
        收集硬件信息
        
        :return: 硬件信息字典
        """
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
        
        if torch.cuda.is_available():
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                hardware["gpu"] = {
                    "name": gpu.name,
                    "memory_total_mb": gpu.memoryTotal,
                    "memory_free_mb": gpu.memoryFree,
                    "driver_version": gpu.driver
                }
        
        self.hardware_info = hardware
        return hardware
    
    def load_model(self, config: BenchmarkConfig) -> bool:
        """
        根据配置加载模型
        
        :param config: 基准测试配置
        :return: 是否加载成功
        """
        print(f"\n{'='*60}")
        print(f"加载模型配置: {config.name}")
        print(f"{'='*60}")
        
        try:
            from transformers import Qwen3VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
            
            load_kwargs = {
                "trust_remote_code": True,
                "low_cpu_mem_usage": True,
            }
            
            if config.use_int4:
                print("  使用 INT4 量化...")
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                load_kwargs["quantization_config"] = quantization_config
                load_kwargs["device_map"] = "auto"
            else:
                if config.use_bf16:
                    print("  使用 BF16 精度...")
                    load_kwargs["torch_dtype"] = torch.bfloat16
                else:
                    print("  使用 FP32 精度...")
                    load_kwargs["torch_dtype"] = torch.float32
                load_kwargs["device_map"] = "auto"
            
            start_time = time.time()
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                str(self.model_path),
                **load_kwargs
            )
            
            self.processor = AutoProcessor.from_pretrained(
                str(self.model_path),
                trust_remote_code=True
            )
            self.tokenizer = self.processor
            
            load_time = time.time() - start_time
            print(f"  模型加载完成，耗时: {load_time:.2f}秒")
            
            if torch.cuda.is_available():
                memory_allocated = torch.cuda.memory_allocated() / (1024**2)
                print(f"  显存占用: {memory_allocated:.2f}MB")
            
            return True
            
        except Exception as e:
            print(f"  模型加载失败: {e}")
            return False
    
    def unload_model(self):
        """卸载模型释放显存"""
        if self.model is not None:
            del self.model
            self.model = None
        if self.processor is not None:
            del self.processor
            self.processor = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
        
        print("  模型已卸载，显存已释放")
    
    def prepare_test_inputs(self, batch_size: int = 1) -> Dict[str, Any]:
        """
        准备测试输入数据
        
        :param batch_size: 批处理大小
        :return: 输入数据字典
        """
        from PIL import Image
        import numpy as np
        
        test_image = Image.fromarray(
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        )
        
        messages = [
            {"role": "system", "content": "你是一位专业的小麦病害诊断专家。"},
            {"role": "user", "content": [
                {"type": "image", "image": test_image},
                {"type": "text", "text": "请分析这张小麦叶片图像，描述可能的病害特征。"}
            ]}
        ]
        
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.processor(text=text, images=test_image, return_tensors="pt")
        
        if batch_size > 1:
            inputs = self._expand_batch(inputs, batch_size)
        
        inputs = inputs.to(self.model.device)
        return inputs
    
    def _expand_batch(self, inputs: Dict[str, Any], batch_size: int) -> Dict[str, Any]:
        """
        扩展输入为批处理
        
        :param inputs: 原始输入
        :param batch_size: 批处理大小
        :return: 扩展后的输入
        """
        expanded = {}
        for key, value in inputs.items():
            if isinstance(value, torch.Tensor):
                expanded[key] = value.repeat(batch_size, 1)
            else:
                expanded[key] = value
        return expanded
    
    def measure_gpu_utilization(self) -> float:
        """
        测量当前 GPU 利用率
        
        :return: GPU 利用率百分比
        """
        if not torch.cuda.is_available():
            return 0.0
        
        gpus = GPUtil.getGPUs()
        if gpus:
            return gpus[0].load * 100
        return 0.0
    
    def run_single_inference(
        self,
        inputs: Dict[str, Any],
        max_new_tokens: int
    ) -> Dict[str, Any]:
        """
        执行单次推理并测量性能
        
        :param inputs: 输入数据
        :param max_new_tokens: 最大生成 token 数
        :return: 性能测量结果
        """
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            memory_before = torch.cuda.memory_allocated() / (1024**2)
        
        gpu_util_before = self.measure_gpu_utilization()
        
        start_time = time.time()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )
        inference_time = time.time() - start_time
        
        gpu_util_after = self.measure_gpu_utilization()
        
        result = {
            "latency_ms": round(inference_time * 1000, 2),
            "tokens_generated": outputs.shape[1] - inputs["input_ids"].shape[1]
        }
        
        if torch.cuda.is_available():
            memory_after = torch.cuda.memory_allocated() / (1024**2)
            memory_peak = torch.cuda.max_memory_allocated() / (1024**2)
            result["memory_before_mb"] = round(memory_before, 2)
            result["memory_after_mb"] = round(memory_after, 2)
            result["memory_peak_mb"] = round(memory_peak, 2)
        
        result["gpu_utilization_percent"] = round((gpu_util_before + gpu_util_after) / 2, 2)
        
        return result
    
    def run_benchmark(self, config: BenchmarkConfig) -> Optional[BenchmarkResult]:
        """
        运行基准测试
        
        :param config: 基准测试配置
        :return: 基准测试结果
        """
        print(f"\n{'='*60}")
        print(f"运行基准测试: {config.name}")
        print(f"{'='*60}")
        print(f"  配置: INT4={config.use_int4}, BF16={config.use_bf16}")
        print(f"  max_new_tokens={config.max_new_tokens}, batch_size={config.batch_size}")
        print(f"  预热次数={config.warmup_runs}, 测试次数={config.test_runs}")
        
        if not self.load_model(config):
            return None
        
        try:
            inputs = self.prepare_test_inputs(config.batch_size)
            
            print(f"\n  预热阶段 ({config.warmup_runs} 次)...")
            for i in range(config.warmup_runs):
                _ = self.run_single_inference(inputs, min(10, config.max_new_tokens))
                print(f"    预热 {i+1}/{config.warmup_runs} 完成")
            
            print(f"\n  测试阶段 ({config.test_runs} 次)...")
            results = []
            total_tokens = 0
            total_latency = 0
            peak_memory = 0
            total_gpu_util = 0
            
            for i in range(config.test_runs):
                result = self.run_single_inference(inputs, config.max_new_tokens)
                results.append(result)
                
                total_tokens += result["tokens_generated"]
                total_latency += result["latency_ms"]
                peak_memory = max(peak_memory, result.get("memory_peak_mb", 0))
                total_gpu_util += result.get("gpu_utilization_percent", 0)
                
                print(f"    测试 {i+1}/{config.test_runs}: "
                      f"{result['latency_ms']:.0f}ms, "
                      f"{result['tokens_generated']} tokens, "
                      f"峰值显存 {result.get('memory_peak_mb', 0):.0f}MB")
            
            avg_latency = total_latency / config.test_runs
            first_latency = results[0]["latency_ms"]
            throughput = (total_tokens / total_latency) * 1000 if total_latency > 0 else 0
            avg_gpu_util = total_gpu_util / config.test_runs
            
            benchmark_result = BenchmarkResult(
                config_name=config.name,
                avg_latency_ms=round(avg_latency, 2),
                first_latency_ms=round(first_latency, 2),
                throughput_tokens_per_sec=round(throughput, 2),
                peak_memory_mb=round(peak_memory, 2),
                gpu_utilization_percent=round(avg_gpu_util, 2),
                total_tokens=total_tokens,
                num_runs=config.test_runs,
                details=results
            )
            
            print(f"\n  结果汇总:")
            print(f"    平均延迟: {benchmark_result.avg_latency_ms:.2f}ms")
            print(f"    首次延迟: {benchmark_result.first_latency_ms:.2f}ms")
            print(f"    吞吐量: {benchmark_result.throughput_tokens_per_sec:.2f} tokens/s")
            print(f"    峰值显存: {benchmark_result.peak_memory_mb:.2f}MB")
            print(f"    GPU利用率: {benchmark_result.gpu_utilization_percent:.2f}%")
            
            self.results.append(benchmark_result)
            return benchmark_result
            
        except Exception as e:
            print(f"  基准测试失败: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.unload_model()
    
    def compare_int4_vs_bf16(
        self,
        max_new_tokens: int = 64,
        test_runs: int = 3
    ) -> List[BenchmarkResult]:
        """
        比较 INT4 量化与 BF16 精度的性能
        
        :param max_new_tokens: 最大生成 token 数
        :param test_runs: 测试次数
        :return: 测试结果列表
        """
        print(f"\n{'#'*60}")
        print("# 测试场景: INT4 量化 vs BF16 精度")
        print(f"{'#'*60}")
        
        configs = [
            BenchmarkConfig(
                name="BF16_基准",
                use_int4=False,
                use_bf16=True,
                max_new_tokens=max_new_tokens,
                test_runs=test_runs
            ),
            BenchmarkConfig(
                name="INT4_量化",
                use_int4=True,
                use_bf16=True,
                max_new_tokens=max_new_tokens,
                test_runs=test_runs
            )
        ]
        
        results = []
        for config in configs:
            result = self.run_benchmark(config)
            if result:
                results.append(result)
        
        return results
    
    def compare_max_new_tokens(
        self,
        token_values: List[int] = [32, 64, 128, 256],
        use_int4: bool = True,
        test_runs: int = 3
    ) -> List[BenchmarkResult]:
        """
        比较不同 max_new_tokens 值的性能
        
        :param token_values: max_new_tokens 值列表
        :param use_int4: 是否使用 INT4 量化
        :param test_runs: 测试次数
        :return: 测试结果列表
        """
        print(f"\n{'#'*60}")
        print("# 测试场景: 不同 max_new_tokens 值")
        print(f"{'#'*60}")
        
        results = []
        for tokens in token_values:
            config = BenchmarkConfig(
                name=f"max_tokens_{tokens}",
                use_int4=use_int4,
                max_new_tokens=tokens,
                test_runs=test_runs
            )
            result = self.run_benchmark(config)
            if result:
                results.append(result)
        
        return results
    
    def compare_batch_vs_single(
        self,
        batch_sizes: List[int] = [1, 2, 4],
        max_new_tokens: int = 64,
        use_int4: bool = True,
        test_runs: int = 3
    ) -> List[BenchmarkResult]:
        """
        比较批处理与单次推理的性能
        
        :param batch_sizes: 批处理大小列表
        :param max_new_tokens: 最大生成 token 数
        :param use_int4: 是否使用 INT4 量化
        :param test_runs: 测试次数
        :return: 测试结果列表
        """
        print(f"\n{'#'*60}")
        print("# 测试场景: 批处理 vs 单次推理")
        print(f"{'#'*60}")
        
        results = []
        for batch_size in batch_sizes:
            config = BenchmarkConfig(
                name=f"batch_{batch_size}",
                use_int4=use_int4,
                max_new_tokens=max_new_tokens,
                batch_size=batch_size,
                test_runs=test_runs
            )
            result = self.run_benchmark(config)
            if result:
                results.append(result)
        
        return results
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        生成 JSON 格式的测试报告
        
        :param output_path: 输出文件路径
        :return: 报告文件路径
        """
        if output_path is None:
            output_path = Path(__file__).parent / "inference_benchmark_report.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "hardware": self.hardware_info,
            "model_path": str(self.model_path),
            "results": [asdict(r) for r in self.results],
            "summary": self._generate_summary()
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试报告已保存: {output_path}")
        return str(output_path)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """
        生成测试结果摘要
        
        :return: 摘要字典
        """
        if not self.results:
            return {}
        
        summary = {
            "total_tests": len(self.results),
            "best_throughput": {
                "config": "",
                "value": 0
            },
            "lowest_latency": {
                "config": "",
                "value": float("inf")
            },
            "lowest_memory": {
                "config": "",
                "value": float("inf")
            }
        }
        
        for result in self.results:
            if result.throughput_tokens_per_sec > summary["best_throughput"]["value"]:
                summary["best_throughput"] = {
                    "config": result.config_name,
                    "value": result.throughput_tokens_per_sec
                }
            
            if result.avg_latency_ms < summary["lowest_latency"]["value"]:
                summary["lowest_latency"] = {
                    "config": result.config_name,
                    "value": result.avg_latency_ms
                }
            
            if result.peak_memory_mb < summary["lowest_memory"]["value"]:
                summary["lowest_memory"] = {
                    "config": result.config_name,
                    "value": result.peak_memory_mb
                }
        
        summary["best_throughput"]["value"] = round(summary["best_throughput"]["value"], 2)
        summary["lowest_latency"]["value"] = round(summary["lowest_latency"]["value"], 2)
        summary["lowest_memory"]["value"] = round(summary["lowest_memory"]["value"], 2)
        
        return summary
    
    def print_comparison_table(self):
        """打印结果对比表格"""
        if not self.results:
            print("没有测试结果")
            return
        
        print(f"\n{'='*80}")
        print("基准测试结果对比")
        print(f"{'='*80}")
        
        header = f"{'配置名称':<20} {'延迟(ms)':<12} {'吞吐量':<15} {'显存(MB)':<12} {'GPU利用率':<10}"
        print(header)
        print("-" * 80)
        
        for result in self.results:
            row = (
                f"{result.config_name:<20} "
                f"{result.avg_latency_ms:<12.2f} "
                f"{result.throughput_tokens_per_sec:<15.2f} "
                f"{result.peak_memory_mb:<12.2f} "
                f"{result.gpu_utilization_percent:<10.2f}"
            )
            print(row)
        
        print(f"{'='*80}")


def main():
    """主函数"""
    print("=" * 60)
    print("推理性能基准测试")
    print("=" * 60)
    
    model_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "Qwen3-VL-2B-Instruct"
    
    if not model_path.exists():
        print(f"错误: 模型路径不存在: {model_path}")
        print("请修改 model_path 为正确的模型路径")
        return
    
    benchmark = InferenceBenchmark(str(model_path))
    
    print("\n[1] 收集硬件信息...")
    hardware = benchmark.collect_hardware_info()
    print(f"  CPU: {hardware['cpu']['cores']}核 {hardware['cpu']['threads']}线程")
    print(f"  内存: {hardware['memory']['total_gb']}GB")
    if hardware['gpu']:
        print(f"  GPU: {hardware['gpu']['name']}")
        print(f"  显存: {hardware['gpu']['memory_total_mb']}MB")
    
    print("\n[2] 测试 INT4 量化 vs BF16 精度...")
    benchmark.compare_int4_vs_bf16(max_new_tokens=64, test_runs=3)
    
    print("\n[3] 测试不同 max_new_tokens 值...")
    benchmark.compare_max_new_tokens(
        token_values=[32, 64, 128],
        use_int4=True,
        test_runs=3
    )
    
    print("\n[4] 测试批处理 vs 单次推理...")
    benchmark.compare_batch_vs_single(
        batch_sizes=[1, 2],
        max_new_tokens=64,
        use_int4=True,
        test_runs=3
    )
    
    print("\n[5] 生成测试报告...")
    benchmark.print_comparison_table()
    benchmark.generate_report()
    
    print("\n" + "=" * 60)
    print("基准测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

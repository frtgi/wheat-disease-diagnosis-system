# -*- coding: utf-8 -*-
"""
性能基准测试套件
测量推理延迟、吞吐量、资源利用率等关键指标
"""
import os
import sys
import time
import json
import torch
import psutil
import threading
import platform
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict, field

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False
    warnings.warn("GPUtil 库未安装，GPU 监控功能受限")

try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except Exception:
    NVML_AVAILABLE = False
    warnings.warn("pynvml 库未安装或初始化失败，GPU 监控功能受限")


@dataclass
class BenchmarkMetrics:
    """
    基准测试指标数据类
    
    包含延迟、吞吐量、资源利用率等关键性能指标
    """
    first_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    throughput_tokens_per_sec: float = 0.0
    throughput_requests_per_sec: float = 0.0
    gpu_utilization_percent: float = 0.0
    gpu_memory_used_mb: float = 0.0
    gpu_memory_peak_mb: float = 0.0
    cpu_utilization_percent: float = 0.0
    ram_used_mb: float = 0.0
    total_tokens: int = 0
    total_requests: int = 0
    test_duration_sec: float = 0.0


@dataclass
class BenchmarkConfig:
    """
    基准测试配置数据类
    
    定义测试运行的各项参数配置
    """
    name: str = "default"
    max_new_tokens: int = 64
    num_runs: int = 10
    warmup_runs: int = 2
    use_int4: bool = True
    use_bf16: bool = True
    batch_size: int = 1
    concurrent_requests: int = 1
    test_image_path: Optional[str] = None
    test_text: str = "请分析小麦条锈病的主要症状和防治方法。"


@dataclass
class ResourceSnapshot:
    """
    资源快照数据类
    
    记录某一时刻的系统资源使用状态
    """
    timestamp: float = 0.0
    cpu_percent: float = 0.0
    ram_used_mb: float = 0.0
    gpu_utilization: float = 0.0
    gpu_memory_used_mb: float = 0.0
    gpu_memory_total_mb: float = 0.0


class ResourceMonitor:
    """
    资源监控器
    
    实时监控 CPU、内存、GPU 利用率等资源指标
    """
    
    def __init__(self, interval_ms: int = 100):
        """
        初始化资源监控器
        
        :param interval_ms: 采样间隔（毫秒）
        """
        self.interval_ms = interval_ms
        self.snapshots: List[ResourceSnapshot] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start(self):
        """
        启动资源监控
        """
        self._running = True
        self.snapshots = []
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """
        停止资源监控
        """
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
    
    def _monitor_loop(self):
        """
        监控循环，定期采集资源数据
        """
        while self._running:
            snapshot = self._collect_snapshot()
            with self._lock:
                self.snapshots.append(snapshot)
            time.sleep(self.interval_ms / 1000.0)
    
    def _collect_snapshot(self) -> ResourceSnapshot:
        """
        采集当前资源快照
        
        :return: 资源快照对象
        """
        snapshot = ResourceSnapshot(timestamp=time.time())
        
        snapshot.cpu_percent = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        snapshot.ram_used_mb = ram.used / (1024 ** 2)
        
        if NVML_AVAILABLE:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                snapshot.gpu_utilization = util.gpu
                snapshot.gpu_memory_used_mb = mem_info.used / (1024 ** 2)
                snapshot.gpu_memory_total_mb = mem_info.total / (1024 ** 2)
            except Exception:
                pass
        elif GPUTIL_AVAILABLE and torch.cuda.is_available():
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    snapshot.gpu_utilization = gpu.load * 100
                    snapshot.gpu_memory_used_mb = gpu.memoryUsed
                    snapshot.gpu_memory_total_mb = gpu.memoryTotal
            except Exception:
                pass
        
        return snapshot
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        计算资源使用统计信息
        
        :return: 统计信息字典
        """
        with self._lock:
            if not self.snapshots:
                return {}
            
            cpu_values = [s.cpu_percent for s in self.snapshots]
            ram_values = [s.ram_used_mb for s in self.snapshots]
            gpu_values = [s.gpu_utilization for s in self.snapshots if s.gpu_utilization > 0]
            gpu_mem_values = [s.gpu_memory_used_mb for s in self.snapshots if s.gpu_memory_used_mb > 0]
            
            stats = {
                "cpu_avg_percent": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "cpu_max_percent": max(cpu_values) if cpu_values else 0,
                "ram_avg_mb": sum(ram_values) / len(ram_values) if ram_values else 0,
                "ram_max_mb": max(ram_values) if ram_values else 0,
                "sample_count": len(self.snapshots)
            }
            
            if gpu_values:
                stats["gpu_avg_percent"] = sum(gpu_values) / len(gpu_values)
                stats["gpu_max_percent"] = max(gpu_values)
            
            if gpu_mem_values:
                stats["gpu_memory_avg_mb"] = sum(gpu_mem_values) / len(gpu_mem_values)
                stats["gpu_memory_max_mb"] = max(gpu_mem_values)
            
            return stats


class PerformanceBenchmarkSuite:
    """
    性能基准测试套件
    
    提供全面的模型性能测试功能，包括延迟、吞吐量、资源利用率等指标测量
    """
    
    DEFAULT_SYSTEM_PROMPT = "你是一位专业的小麦病害诊断专家，请根据用户的问题提供专业、准确的回答。"
    
    def __init__(self, model_path: str, num_runs: int = 10):
        """
        初始化性能基准测试套件
        
        :param model_path: 模型路径
        :param num_runs: 默认测试运行次数
        """
        self.model_path = Path(model_path)
        self.default_num_runs = num_runs
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.results: Dict[str, BenchmarkMetrics] = {}
        self.hardware_info: Dict[str, Any] = {}
        self.resource_monitor = ResourceMonitor(interval_ms=50)
        
        self._setup_environment()
    
    def _setup_environment(self):
        """
        配置运行环境
        """
        if platform.system() == 'Windows':
            os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')
            os.environ.setdefault('HF_HUB_ENABLE_HF_TRANSFER', '0')
        
        os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
    
    def collect_hardware_info(self) -> Dict[str, Any]:
        """
        收集硬件配置信息
        
        :return: 硬件信息字典
        """
        hardware = {
            "cpu": {
                "cores": psutil.cpu_count(logical=False),
                "threads": psutil.cpu_count(logical=True),
                "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "architecture": platform.processor()
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024 ** 3), 2)
            },
            "os": {
                "system": platform.system(),
                "version": platform.version(),
                "python_version": platform.python_version()
            },
            "gpu": {}
        }
        
        if torch.cuda.is_available():
            gpu_props = torch.cuda.get_device_properties(0)
            hardware["gpu"] = {
                "name": gpu_props.name,
                "memory_total_mb": gpu_props.total_memory / (1024 ** 2),
                "compute_capability": f"{gpu_props.major}.{gpu_props.minor}",
                "multi_processor_count": gpu_props.multi_processor_count,
                "cuda_version": torch.version.cuda
            }
        
        self.hardware_info = hardware
        return hardware
    
    def load_model(self, config: BenchmarkConfig) -> bool:
        """
        根据配置加载模型
        
        :param config: 基准测试配置
        :return: 是否加载成功
        """
        print(f"\n{'=' * 60}")
        print(f"加载模型: {self.model_path}")
        print(f"{'=' * 60}")
        
        try:
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
            
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
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
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
                memory_allocated = torch.cuda.memory_allocated() / (1024 ** 2)
                print(f"  显存占用: {memory_allocated:.2f}MB")
            
            return True
            
        except Exception as e:
            print(f"  模型加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def unload_model(self):
        """
        卸载模型释放显存
        """
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
    
    def _prepare_text_inputs(self, text: str) -> Dict[str, Any]:
        """
        准备纯文本输入数据
        
        :param text: 输入文本
        :return: 模型输入字典
        """
        messages = [
            {"role": "system", "content": self.DEFAULT_SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
        
        prompt_text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.processor(text=prompt_text, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        return inputs
    
    def _prepare_image_inputs(self, image_path: str, text: str = "请描述这张图片的内容。") -> Dict[str, Any]:
        """
        准备图像输入数据
        
        :param image_path: 图像路径
        :param text: 附加文本提示
        :return: 模型输入字典
        """
        from PIL import Image
        import numpy as np
        
        if not os.path.exists(image_path):
            test_image = Image.fromarray(
                np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            )
        else:
            test_image = Image.open(image_path).convert('RGB')
        
        messages = [
            {"role": "system", "content": self.DEFAULT_SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "image", "image": test_image},
                {"type": "text", "text": text}
            ]}
        ]
        
        prompt_text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.processor(text=prompt_text, images=test_image, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        return inputs
    
    def _prepare_multimodal_inputs(self, image_path: str, text: str) -> Dict[str, Any]:
        """
        准备多模态输入数据
        
        :param image_path: 图像路径
        :param text: 文本提示
        :return: 模型输入字典
        """
        return self._prepare_image_inputs(image_path, text)
    
    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """
        计算百分位数值
        
        :param values: 数值列表
        :param percentile: 百分位数（0-100）
        :return: 百分位对应的值
        """
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def _run_inference(self, inputs: Dict[str, Any], max_new_tokens: int) -> Dict[str, Any]:
        """
        执行单次推理
        
        :param inputs: 模型输入
        :param max_new_tokens: 最大生成 token 数
        :return: 推理结果
        """
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
        
        start_time = time.time()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )
        inference_time = time.time() - start_time
        
        tokens_generated = outputs.shape[1] - inputs["input_ids"].shape[1]
        
        result = {
            "latency_ms": inference_time * 1000,
            "tokens_generated": tokens_generated,
            "tokens_per_sec": tokens_generated / inference_time if inference_time > 0 else 0
        }
        
        if torch.cuda.is_available():
            result["gpu_memory_peak_mb"] = torch.cuda.max_memory_allocated() / (1024 ** 2)
        
        return result
    
    def run_text_benchmark(self, text: Optional[str] = None, config: Optional[BenchmarkConfig] = None) -> BenchmarkMetrics:
        """
        运行纯文本推理基准测试
        
        :param text: 测试文本，如果为 None 则使用默认文本
        :param config: 测试配置，如果为 None 则使用默认配置
        :return: 基准测试指标
        """
        if config is None:
            config = BenchmarkConfig(name="text_benchmark", num_runs=self.default_num_runs)
        
        test_text = text or config.test_text
        print(f"\n{'#' * 60}")
        print(f"# 测试场景: 纯文本推理")
        print(f"{'#' * 60}")
        print(f"  测试文本: {test_text[:50]}...")
        print(f"  运行次数: {config.num_runs} (预热: {config.warmup_runs})")
        
        inputs = self._prepare_text_inputs(test_text)
        
        return self._execute_benchmark(inputs, config, "text_benchmark")
    
    def run_image_benchmark(self, image_path: Optional[str] = None, config: Optional[BenchmarkConfig] = None) -> BenchmarkMetrics:
        """
        运行纯图像推理基准测试
        
        :param image_path: 图像路径，如果为 None 则使用随机生成的图像
        :param config: 测试配置，如果为 None 则使用默认配置
        :return: 基准测试指标
        """
        if config is None:
            config = BenchmarkConfig(name="image_benchmark", num_runs=self.default_num_runs)
        
        actual_image_path = image_path or config.test_image_path
        print(f"\n{'#' * 60}")
        print(f"# 测试场景: 纯图像推理")
        print(f"{'#' * 60}")
        print(f"  图像路径: {actual_image_path or '随机生成'}")
        print(f"  运行次数: {config.num_runs} (预热: {config.warmup_runs})")
        
        inputs = self._prepare_image_inputs(actual_image_path or "", "请详细描述这张图片的内容。")
        
        return self._execute_benchmark(inputs, config, "image_benchmark")
    
    def run_multimodal_benchmark(self, image_path: Optional[str] = None, text: Optional[str] = None, config: Optional[BenchmarkConfig] = None) -> BenchmarkMetrics:
        """
        运行多模态推理基准测试
        
        :param image_path: 图像路径
        :param text: 文本提示
        :param config: 测试配置
        :return: 基准测试指标
        """
        if config is None:
            config = BenchmarkConfig(name="multimodal_benchmark", num_runs=self.default_num_runs)
        
        actual_image_path = image_path or config.test_image_path
        test_text = text or "请分析这张小麦图像，识别可能的病害类型并提供诊断建议。"
        
        print(f"\n{'#' * 60}")
        print(f"# 测试场景: 多模态推理")
        print(f"{'#' * 60}")
        print(f"  图像路径: {actual_image_path or '随机生成'}")
        print(f"  文本提示: {test_text[:50]}...")
        print(f"  运行次数: {config.num_runs} (预热: {config.warmup_runs})")
        
        inputs = self._prepare_multimodal_inputs(actual_image_path or "", test_text)
        
        return self._execute_benchmark(inputs, config, "multimodal_benchmark")
    
    def _execute_benchmark(self, inputs: Dict[str, Any], config: BenchmarkConfig, scenario_name: str) -> BenchmarkMetrics:
        """
        执行基准测试核心逻辑
        
        :param inputs: 模型输入
        :param config: 测试配置
        :param scenario_name: 场景名称
        :return: 基准测试指标
        """
        latencies = []
        total_tokens = 0
        total_gpu_memory_peak = 0
        
        print(f"\n  预热阶段 ({config.warmup_runs} 次)...")
        for i in range(config.warmup_runs):
            _ = self._run_inference(inputs, min(10, config.max_new_tokens))
            print(f"    预热 {i + 1}/{config.warmup_runs} 完成")
        
        print(f"\n  测试阶段 ({config.num_runs} 次)...")
        
        self.resource_monitor.start()
        test_start_time = time.time()
        
        for i in range(config.num_runs):
            result = self._run_inference(inputs, config.max_new_tokens)
            
            latencies.append(result["latency_ms"])
            total_tokens += result["tokens_generated"]
            total_gpu_memory_peak = max(total_gpu_memory_peak, result.get("gpu_memory_peak_mb", 0))
            
            print(f"    测试 {i + 1}/{config.num_runs}: "
                  f"{result['latency_ms']:.0f}ms, "
                  f"{result['tokens_generated']} tokens, "
                  f"{result['tokens_per_sec']:.1f} tokens/s")
        
        test_duration = time.time() - test_start_time
        self.resource_monitor.stop()
        
        resource_stats = self.resource_monitor.get_statistics()
        
        metrics = BenchmarkMetrics(
            first_latency_ms=round(latencies[0], 2) if latencies else 0,
            avg_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else 0,
            p95_latency_ms=round(self._calculate_percentile(latencies, 95), 2),
            p99_latency_ms=round(self._calculate_percentile(latencies, 99), 2),
            min_latency_ms=round(min(latencies), 2) if latencies else 0,
            max_latency_ms=round(max(latencies), 2) if latencies else 0,
            throughput_tokens_per_sec=round(total_tokens / (sum(latencies) / 1000), 2) if latencies else 0,
            throughput_requests_per_sec=round(config.num_runs / (sum(latencies) / 1000), 2) if latencies else 0,
            gpu_utilization_percent=round(resource_stats.get("gpu_avg_percent", 0), 2),
            gpu_memory_used_mb=round(resource_stats.get("gpu_memory_avg_mb", 0), 2),
            gpu_memory_peak_mb=round(total_gpu_memory_peak, 2),
            cpu_utilization_percent=round(resource_stats.get("cpu_avg_percent", 0), 2),
            ram_used_mb=round(resource_stats.get("ram_avg_mb", 0), 2),
            total_tokens=total_tokens,
            total_requests=config.num_runs,
            test_duration_sec=round(test_duration, 2)
        )
        
        self.results[scenario_name] = metrics
        
        self._print_metrics(metrics, scenario_name)
        
        return metrics
    
    def _print_metrics(self, metrics: BenchmarkMetrics, scenario_name: str):
        """
        打印测试指标
        
        :param metrics: 基准测试指标
        :param scenario_name: 场景名称
        """
        print(f"\n  结果汇总 ({scenario_name}):")
        print(f"    首次延迟: {metrics.first_latency_ms:.2f}ms")
        print(f"    平均延迟: {metrics.avg_latency_ms:.2f}ms")
        print(f"    P95 延迟: {metrics.p95_latency_ms:.2f}ms")
        print(f"    P99 延迟: {metrics.p99_latency_ms:.2f}ms")
        print(f"    最小延迟: {metrics.min_latency_ms:.2f}ms")
        print(f"    最大延迟: {metrics.max_latency_ms:.2f}ms")
        print(f"    吞吐量 (tokens/s): {metrics.throughput_tokens_per_sec:.2f}")
        print(f"    吞吐量 (requests/s): {metrics.throughput_requests_per_sec:.2f}")
        print(f"    GPU 利用率: {metrics.gpu_utilization_percent:.2f}%")
        print(f"    GPU 显存峰值: {metrics.gpu_memory_peak_mb:.2f}MB")
        print(f"    CPU 利用率: {metrics.cpu_utilization_percent:.2f}%")
        print(f"    内存使用: {metrics.ram_used_mb:.2f}MB")
    
    def run_all_benchmarks(self, config: Optional[BenchmarkConfig] = None) -> Dict[str, BenchmarkMetrics]:
        """
        运行所有基准测试场景
        
        :param config: 测试配置
        :return: 所有场景的测试指标
        """
        print("\n" + "=" * 60)
        print("性能基准测试套件 - 全面测试")
        print("=" * 60)
        
        if config is None:
            config = BenchmarkConfig(name="full_suite", num_runs=self.default_num_runs)
        
        if not self.load_model(config):
            print("模型加载失败，无法继续测试")
            return {}
        
        try:
            self.run_text_benchmark(config=config)
            self.run_image_benchmark(config=config)
            self.run_multimodal_benchmark(config=config)
        finally:
            self.unload_model()
        
        return self.results
    
    def run_concurrent_benchmark(self, num_concurrent: int = 4, config: Optional[BenchmarkConfig] = None) -> BenchmarkMetrics:
        """
        运行并发推理基准测试
        
        :param num_concurrent: 并发请求数
        :param config: 测试配置
        :return: 基准测试指标
        """
        if config is None:
            config = BenchmarkConfig(name="concurrent_benchmark", num_runs=self.default_num_runs)
        
        print(f"\n{'#' * 60}")
        print(f"# 测试场景: 并发推理 ({num_concurrent} 并发)")
        print(f"{'#' * 60}")
        
        import concurrent.futures
        import queue
        
        latencies = []
        total_tokens = 0
        results_queue = queue.Queue()
        
        def inference_task(task_id: int):
            """
            单个推理任务
            
            :param task_id: 任务 ID
            """
            inputs = self._prepare_text_inputs(f"任务 {task_id}: {config.test_text}")
            result = self._run_inference(inputs, config.max_new_tokens)
            results_queue.put(result)
        
        print(f"\n  预热阶段...")
        for _ in range(config.warmup_runs):
            inputs = self._prepare_text_inputs(config.test_text)
            _ = self._run_inference(inputs, min(10, config.max_new_tokens))
        
        print(f"\n  并发测试阶段 ({config.num_runs} 轮, {num_concurrent} 并发)...")
        
        self.resource_monitor.start()
        test_start_time = time.time()
        
        for round_num in range(config.num_runs):
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                futures = [executor.submit(inference_task, i) for i in range(num_concurrent)]
                concurrent.futures.wait(futures)
            
            print(f"    第 {round_num + 1}/{config.num_runs} 轮完成")
        
        test_duration = time.time() - test_start_time
        self.resource_monitor.stop()
        
        while not results_queue.empty():
            result = results_queue.get()
            latencies.append(result["latency_ms"])
            total_tokens += result["tokens_generated"]
        
        resource_stats = self.resource_monitor.get_statistics()
        
        metrics = BenchmarkMetrics(
            first_latency_ms=round(latencies[0], 2) if latencies else 0,
            avg_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else 0,
            p95_latency_ms=round(self._calculate_percentile(latencies, 95), 2),
            p99_latency_ms=round(self._calculate_percentile(latencies, 99), 2),
            min_latency_ms=round(min(latencies), 2) if latencies else 0,
            max_latency_ms=round(max(latencies), 2) if latencies else 0,
            throughput_tokens_per_sec=round(total_tokens / (sum(latencies) / 1000), 2) if latencies else 0,
            throughput_requests_per_sec=round(len(latencies) / (sum(latencies) / 1000), 2) if latencies else 0,
            gpu_utilization_percent=round(resource_stats.get("gpu_avg_percent", 0), 2),
            gpu_memory_used_mb=round(resource_stats.get("gpu_memory_avg_mb", 0), 2),
            gpu_memory_peak_mb=round(resource_stats.get("gpu_memory_max_mb", 0), 2),
            cpu_utilization_percent=round(resource_stats.get("cpu_avg_percent", 0), 2),
            ram_used_mb=round(resource_stats.get("ram_avg_mb", 0), 2),
            total_tokens=total_tokens,
            total_requests=len(latencies),
            test_duration_sec=round(test_duration, 2)
        )
        
        self.results["concurrent_benchmark"] = metrics
        self._print_metrics(metrics, "concurrent_benchmark")
        
        return metrics
    
    def generate_report(self, output_path: str) -> str:
        """
        生成 JSON 格式的测试报告
        
        :param output_path: 输出文件路径
        :return: 报告文件路径
        """
        report = {
            "report_info": {
                "timestamp": datetime.now().isoformat(),
                "generator": "PerformanceBenchmarkSuite",
                "version": "1.0.0"
            },
            "hardware": self.hardware_info,
            "model_path": str(self.model_path),
            "benchmark_results": {},
            "summary": self._generate_summary()
        }
        
        for scenario, metrics in self.results.items():
            report["benchmark_results"][scenario] = asdict(metrics)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试报告已保存: {output_file}")
        return str(output_file)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """
        生成测试结果摘要
        
        :return: 摘要字典
        """
        if not self.results:
            return {}
        
        summary = {
            "total_scenarios": len(self.results),
            "scenarios_tested": list(self.results.keys()),
            "best_throughput": {
                "scenario": "",
                "tokens_per_sec": 0
            },
            "lowest_latency": {
                "scenario": "",
                "avg_latency_ms": float("inf")
            },
            "lowest_gpu_memory": {
                "scenario": "",
                "peak_mb": float("inf")
            },
            "overall": {
                "total_tokens": 0,
                "total_requests": 0,
                "total_duration_sec": 0
            }
        }
        
        for scenario, metrics in self.results.items():
            if metrics.throughput_tokens_per_sec > summary["best_throughput"]["tokens_per_sec"]:
                summary["best_throughput"] = {
                    "scenario": scenario,
                    "tokens_per_sec": metrics.throughput_tokens_per_sec
                }
            
            if metrics.avg_latency_ms < summary["lowest_latency"]["avg_latency_ms"]:
                summary["lowest_latency"] = {
                    "scenario": scenario,
                    "avg_latency_ms": metrics.avg_latency_ms
                }
            
            if metrics.gpu_memory_peak_mb < summary["lowest_gpu_memory"]["peak_mb"]:
                summary["lowest_gpu_memory"] = {
                    "scenario": scenario,
                    "peak_mb": metrics.gpu_memory_peak_mb
                }
            
            summary["overall"]["total_tokens"] += metrics.total_tokens
            summary["overall"]["total_requests"] += metrics.total_requests
            summary["overall"]["total_duration_sec"] += metrics.test_duration_sec
        
        summary["best_throughput"]["tokens_per_sec"] = round(
            summary["best_throughput"]["tokens_per_sec"], 2
        )
        summary["lowest_latency"]["avg_latency_ms"] = round(
            summary["lowest_latency"]["avg_latency_ms"], 2
        )
        summary["lowest_gpu_memory"]["peak_mb"] = round(
            summary["lowest_gpu_memory"]["peak_mb"], 2
        )
        
        return summary
    
    def print_comparison_table(self):
        """
        打印所有场景的结果对比表格
        """
        if not self.results:
            print("没有测试结果")
            return
        
        print(f"\n{'=' * 100}")
        print("基准测试结果对比")
        print(f"{'=' * 100}")
        
        header = (f"{'场景':<25} "
                  f"{'延迟(ms)':<20} "
                  f"{'P95(ms)':<10} "
                  f"{'P99(ms)':<10} "
                  f"{'吞吐量':<12} "
                  f"{'GPU显存(MB)':<12}")
        print(header)
        print("-" * 100)
        
        for scenario, metrics in self.results.items():
            row = (f"{scenario:<25} "
                   f"{metrics.avg_latency_ms:<20.2f} "
                   f"{metrics.p95_latency_ms:<10.2f} "
                   f"{metrics.p99_latency_ms:<10.2f} "
                   f"{metrics.throughput_tokens_per_sec:<12.2f} "
                   f"{metrics.gpu_memory_peak_mb:<12.2f}")
            print(row)
        
        print(f"{'=' * 100}")


def main():
    """
    主函数 - 运行完整的性能基准测试
    """
    print("=" * 60)
    print("性能基准测试套件")
    print("=" * 60)
    
    model_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "Qwen3-VL-2B-Instruct"
    
    if not model_path.exists():
        alt_path = Path("D:/Project/WheatAgent/models/Qwen3-VL-2B-Instruct")
        if alt_path.exists():
            model_path = alt_path
        else:
            print(f"错误: 模型路径不存在: {model_path}")
            print("请修改 model_path 为正确的模型路径")
            return
    
    config = BenchmarkConfig(
        name="full_benchmark",
        num_runs=10,
        warmup_runs=2,
        max_new_tokens=64,
        use_int4=True,
        use_bf16=True
    )
    
    suite = PerformanceBenchmarkSuite(str(model_path), num_runs=config.num_runs)
    
    print("\n[1] 收集硬件信息...")
    hardware = suite.collect_hardware_info()
    print(f"  CPU: {hardware['cpu']['cores']}核 {hardware['cpu']['threads']}线程")
    print(f"  内存: {hardware['memory']['total_gb']}GB")
    if hardware['gpu']:
        print(f"  GPU: {hardware['gpu']['name']}")
        print(f"  显存: {hardware['gpu']['memory_total_mb']:.0f}MB")
    
    print("\n[2] 运行基准测试...")
    results = suite.run_all_benchmarks(config)
    
    if results:
        print("\n[3] 打印对比结果...")
        suite.print_comparison_table()
        
        print("\n[4] 生成测试报告...")
        report_path = Path(__file__).parent / "performance_benchmark_report.json"
        suite.generate_report(str(report_path))
    
    print("\n" + "=" * 60)
    print("基准测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

"""
性能分析工具模块

提供推理性能分析、GPU 指标收集和报告生成功能
"""
import time
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)


@dataclass
class StageMetrics:
    """阶段性能指标"""
    name: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    gpu_memory_before_mb: float = 0.0
    gpu_memory_after_mb: float = 0.0
    gpu_memory_delta_mb: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "duration_ms": round(self.duration_ms, 2),
            "gpu_memory_before_mb": round(self.gpu_memory_before_mb, 2),
            "gpu_memory_after_mb": round(self.gpu_memory_after_mb, 2),
            "gpu_memory_delta_mb": round(self.gpu_memory_delta_mb, 2),
            "metadata": self.metadata
        }


@dataclass
class InferenceMetrics:
    """推理性能指标"""
    total_time_ms: float = 0.0
    preprocess_time_ms: float = 0.0
    inference_time_ms: float = 0.0
    postprocess_time_ms: float = 0.0
    tokens_generated: int = 0
    tokens_per_second: float = 0.0
    first_token_latency_ms: float = 0.0
    gpu_utilization_avg: float = 0.0
    gpu_memory_peak_mb: float = 0.0
    stages: List[StageMetrics] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_time_ms": round(self.total_time_ms, 2),
            "preprocess_time_ms": round(self.preprocess_time_ms, 2),
            "inference_time_ms": round(self.inference_time_ms, 2),
            "postprocess_time_ms": round(self.postprocess_time_ms, 2),
            "tokens_generated": self.tokens_generated,
            "tokens_per_second": round(self.tokens_per_second, 2),
            "first_token_latency_ms": round(self.first_token_latency_ms, 2),
            "gpu_utilization_avg": round(self.gpu_utilization_avg, 2),
            "gpu_memory_peak_mb": round(self.gpu_memory_peak_mb, 2),
            "stages": [s.to_dict() for s in self.stages]
        }


class InferenceProfiler:
    """
    推理性能分析器
    
    用于分阶段计时和性能数据收集
    """
    
    def __init__(self):
        """初始化分析器"""
        self.stages: List[StageMetrics] = []
        self.current_stage: Optional[StageMetrics] = None
        self._lock = threading.Lock()
        self._start_time: float = 0.0
    
    def start(self) -> "InferenceProfiler":
        """
        开始整体计时
        
        返回:
            self，支持链式调用
        """
        self._start_time = time.perf_counter()
        self.stages = []
        return self
    
    def start_stage(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> "InferenceProfiler":
        """
        开始一个阶段的计时
        
        参数:
            name: 阶段名称
            metadata: 阶段元数据
        
        返回:
            self，支持链式调用
        """
        with self._lock:
            if self.current_stage is not None:
                self.end_stage()
            
            self.current_stage = StageMetrics(
                name=name,
                start_time=time.perf_counter(),
                metadata=metadata or {}
            )
            
            try:
                from .gpu_monitor import get_gpu_memory_info
                gpu_info = get_gpu_memory_info()
                self.current_stage.gpu_memory_before_mb = gpu_info.used_memory_mb
            except Exception:
                pass
        
        return self
    
    def end_stage(self, metadata: Optional[Dict[str, Any]] = None) -> StageMetrics:
        """
        结束当前阶段的计时
        
        参数:
            metadata: 额外的阶段元数据
        
        返回:
            完成的阶段指标
        """
        with self._lock:
            if self.current_stage is None:
                return StageMetrics(name="unknown")
            
            self.current_stage.end_time = time.perf_counter()
            self.current_stage.duration_ms = (self.current_stage.end_time - self.current_stage.start_time) * 1000
            
            if metadata:
                self.current_stage.metadata.update(metadata)
            
            try:
                from .gpu_monitor import get_gpu_memory_info
                gpu_info = get_gpu_memory_info()
                self.current_stage.gpu_memory_after_mb = gpu_info.used_memory_mb
                self.current_stage.gpu_memory_delta_mb = (
                    self.current_stage.gpu_memory_after_mb - self.current_stage.gpu_memory_before_mb
                )
            except Exception:
                pass
            
            completed_stage = self.current_stage
            self.stages.append(completed_stage)
            self.current_stage = None
            
            return completed_stage
    
    @contextmanager
    def stage(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        阶段计时上下文管理器
        
        参数:
            name: 阶段名称
            metadata: 阶段元数据
        
        用法:
            with profiler.stage("preprocess"):
                # 预处理代码
        """
        self.start_stage(name, metadata)
        try:
            yield self
        finally:
            self.end_stage()
    
    def stop(self) -> InferenceMetrics:
        """
        停止整体计时并返回指标
        
        返回:
            推理性能指标
        """
        total_time_ms = (time.perf_counter() - self._start_time) * 1000
        
        preprocess_time = 0.0
        inference_time = 0.0
        postprocess_time = 0.0
        
        for stage in self.stages:
            stage_lower = stage.name.lower()
            if "preprocess" in stage_lower or "input" in stage_lower or "load" in stage_lower:
                preprocess_time += stage.duration_ms
            elif "inference" in stage_lower or "generate" in stage_lower or "forward" in stage_lower:
                inference_time += stage.duration_ms
            elif "postprocess" in stage_lower or "decode" in stage_lower or "output" in stage_lower:
                postprocess_time += stage.duration_ms
        
        metrics = InferenceMetrics(
            total_time_ms=total_time_ms,
            preprocess_time_ms=preprocess_time,
            inference_time_ms=inference_time,
            postprocess_time_ms=postprocess_time,
            stages=self.stages.copy()
        )
        
        return metrics
    
    def get_summary(self) -> str:
        """
        获取性能摘要
        
        返回:
            性能摘要字符串
        """
        lines = ["=" * 50, "推理性能分析", "=" * 50]
        
        for stage in self.stages:
            lines.append(f"  {stage.name}: {stage.duration_ms:.2f}ms")
            if stage.gpu_memory_delta_mb != 0:
                lines.append(f"    显存变化: {stage.gpu_memory_delta_mb:+.0f}MB")
        
        total = sum(s.duration_ms for s in self.stages)
        lines.append("-" * 50)
        lines.append(f"  总耗时: {total:.2f}ms")
        lines.append("=" * 50)
        
        return "\n".join(lines)


class GPUMetricsCollector:
    """
    GPU 指标收集器
    
    用于收集 GPU 利用率、显存带宽等指标
    """
    
    def __init__(self, device_id: int = 0):
        """
        初始化 GPU 指标收集器
        
        参数:
            device_id: GPU 设备 ID
        """
        self.device_id = device_id
        self.metrics_history: List[Dict[str, Any]] = []
        self._collecting = False
        self._collect_thread: Optional[threading.Thread] = None
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        获取当前 GPU 指标
        
        返回:
            GPU 指标字典
        """
        metrics = {
            "timestamp": time.time(),
            "device_id": self.device_id,
            "cuda_available": False,
            "gpu_utilization": 0.0,
            "memory_used_mb": 0.0,
            "memory_free_mb": 0.0,
            "memory_total_mb": 0.0,
            "memory_utilization": 0.0,
            "temperature": 0,
            "power_draw": 0.0,
            "power_limit": 0.0
        }
        
        try:
            import torch
            
            if not torch.cuda.is_available():
                return metrics
            
            metrics["cuda_available"] = True
            
            torch.cuda.set_device(self.device_id)
            
            from .gpu_monitor import get_gpu_memory_info, get_device_info
            
            mem_info = get_gpu_memory_info(self.device_id)
            metrics["memory_used_mb"] = mem_info.used_memory_mb
            metrics["memory_free_mb"] = mem_info.free_memory_mb
            metrics["memory_total_mb"] = mem_info.total_memory_mb
            metrics["memory_utilization"] = mem_info.utilization_percent
            
            device_info = get_device_info()
            if device_info.get("devices"):
                for device in device_info["devices"]:
                    if device["id"] == self.device_id:
                        metrics["device_name"] = device["name"]
                        break
            
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_id)
                
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                metrics["gpu_utilization"] = util.gpu
                
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                metrics["temperature"] = temp
                
                power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                metrics["power_draw"] = power
                
                power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0
                metrics["power_limit"] = power_limit
                
                pynvml.nvmlShutdown()
            except ImportError:
                pass
            except Exception as e:
                logger.debug(f"获取 NVML 指标失败: {e}")
            
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"获取 GPU 指标失败: {e}")
        
        return metrics
    
    def start_collecting(self, interval_ms: int = 100) -> None:
        """
        开始持续收集 GPU 指标
        
        参数:
            interval_ms: 收集间隔（毫秒）
        """
        if self._collecting:
            return
        
        self._collecting = True
        self.metrics_history = []
        
        def collect_loop():
            while self._collecting:
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)
                time.sleep(interval_ms / 1000.0)
        
        self._collect_thread = threading.Thread(target=collect_loop, daemon=True)
        self._collect_thread.start()
    
    def stop_collecting(self) -> List[Dict[str, Any]]:
        """
        停止收集 GPU 指标
        
        返回:
            收集到的指标历史
        """
        self._collecting = False
        if self._collect_thread:
            self._collect_thread.join(timeout=1.0)
            self._collect_thread = None
        
        return self.metrics_history
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取 GPU 指标统计
        
        返回:
            统计数据字典
        """
        if not self.metrics_history:
            return {}
        
        def avg(lst):
            return sum(lst) / len(lst) if lst else 0
        
        def max_val(lst):
            return max(lst) if lst else 0
        
        def min_val(lst):
            return min(lst) if lst else 0
        
        gpu_utils = [m.get("gpu_utilization", 0) for m in self.metrics_history]
        mem_utils = [m.get("memory_utilization", 0) for m in self.metrics_history]
        temps = [m.get("temperature", 0) for m in self.metrics_history]
        powers = [m.get("power_draw", 0) for m in self.metrics_history]
        
        return {
            "samples_count": len(self.metrics_history),
            "duration_seconds": self.metrics_history[-1]["timestamp"] - self.metrics_history[0]["timestamp"] if len(self.metrics_history) > 1 else 0,
            "gpu_utilization": {
                "avg": round(avg(gpu_utils), 2),
                "max": round(max_val(gpu_utils), 2),
                "min": round(min_val(gpu_utils), 2)
            },
            "memory_utilization": {
                "avg": round(avg(mem_utils), 2),
                "max": round(max_val(mem_utils), 2),
                "min": round(min_val(mem_utils), 2)
            },
            "temperature": {
                "avg": round(avg(temps), 2),
                "max": round(max_val(temps), 2)
            },
            "power_draw": {
                "avg": round(avg(powers), 2),
                "max": round(max_val(powers), 2)
            }
        }


class PerformanceReport:
    """
    性能分析报告生成器
    
    用于生成结构化的性能分析报告
    """
    
    def __init__(self):
        """初始化报告生成器"""
        self.hardware_info: Dict[str, Any] = {}
        self.model_info: Dict[str, Any] = {}
        self.inference_metrics: Optional[InferenceMetrics] = None
        self.gpu_statistics: Dict[str, Any] = {}
        self.bottlenecks: List[Dict[str, Any]] = []
        self.recommendations: List[Dict[str, Any]] = []
    
    def set_hardware_info(self, info: Dict[str, Any]) -> None:
        """
        设置硬件信息
        
        参数:
            info: 硬件信息字典
        """
        self.hardware_info = info
    
    def set_model_info(self, info: Dict[str, Any]) -> None:
        """
        设置模型信息
        
        参数:
            info: 模型信息字典
        """
        self.model_info = info
    
    def set_inference_metrics(self, metrics: InferenceMetrics) -> None:
        """
        设置推理指标
        
        参数:
            metrics: 推理性能指标
        """
        self.inference_metrics = metrics
    
    def set_gpu_statistics(self, stats: Dict[str, Any]) -> None:
        """
        设置 GPU 统计
        
        参数:
            stats: GPU 统计数据
        """
        self.gpu_statistics = stats
    
    def add_bottleneck(self, name: str, severity: str, impact: float, description: str) -> None:
        """
        添加瓶颈信息
        
        参数:
            name: 瓶颈名称
            severity: 严重程度 (critical/high/medium/low)
            impact: 影响程度 (0-1)
            description: 描述
        """
        self.bottlenecks.append({
            "name": name,
            "severity": severity,
            "impact": round(impact, 2),
            "description": description
        })
    
    def add_recommendation(self, title: str, priority: str, description: str, expected_improvement: str) -> None:
        """
        添加优化建议
        
        参数:
            title: 建议标题
            priority: 优先级 (high/medium/low)
            description: 详细描述
            expected_improvement: 预期改进
        """
        self.recommendations.append({
            "title": title,
            "priority": priority,
            "description": description,
            "expected_improvement": expected_improvement
        })
    
    def analyze_bottlenecks(self) -> None:
        """
        自动分析瓶颈
        """
        if not self.hardware_info:
            return
        
        vram_mb = self.hardware_info.get("gpu", {}).get("total_memory_mb", 0)
        if vram_mb > 0 and vram_mb < 8000:
            self.add_bottleneck(
                name="显存容量不足",
                severity="critical",
                impact=0.9,
                description=f"GPU 显存仅 {vram_mb:.0f}MB，模型加载后几乎无剩余显存，导致大量使用共享内存"
            )
        
        if self.inference_metrics:
            total_time = self.inference_metrics.total_time_ms
            if total_time > 30000:
                self.add_bottleneck(
                    name="推理时间过长",
                    severity="high",
                    impact=0.8,
                    description=f"单次推理耗时 {total_time/1000:.1f}秒，严重影响用户体验"
                )
            
            if self.inference_metrics.tokens_per_second > 0 and self.inference_metrics.tokens_per_second < 10:
                self.add_bottleneck(
                    name="生成速度慢",
                    severity="high",
                    impact=0.7,
                    description=f"Token 生成速度仅 {self.inference_metrics.tokens_per_second:.1f}/秒"
                )
        
        if self.gpu_statistics:
            avg_gpu_util = self.gpu_statistics.get("gpu_utilization", {}).get("avg", 0)
            if avg_gpu_util < 50:
                self.add_bottleneck(
                    name="GPU 利用率低",
                    severity="medium",
                    impact=0.5,
                    description=f"GPU 平均利用率仅 {avg_gpu_util:.1f}%，可能存在内存带宽瓶颈"
                )
    
    def generate_recommendations(self) -> None:
        """
        生成优化建议
        """
        for bottleneck in self.bottlenecks:
            if bottleneck["name"] == "显存容量不足":
                self.add_recommendation(
                    title="使用更大量化或更小模型",
                    priority="high",
                    description="考虑使用 INT8 量化、更小的模型（如 Qwen3-VL-2B），或升级 GPU",
                    expected_improvement="可减少显存占用 30-50%"
                )
                self.add_recommendation(
                    title="启用 CPU offload",
                    priority="medium",
                    description="将部分模型层卸载到 CPU，减少 GPU 显存压力",
                    expected_improvement="可运行更大模型，但推理速度会下降"
                )
            
            elif bottleneck["name"] == "推理时间过长":
                self.add_recommendation(
                    title="禁用 Thinking 模式",
                    priority="high",
                    description="Thinking 模式会生成更长的推理链，显著增加推理时间",
                    expected_improvement="可减少推理时间 50-70%"
                )
                self.add_recommendation(
                    title="减少 max_new_tokens",
                    priority="medium",
                    description="将 max_new_tokens 从 1024 减少到 256-512",
                    expected_improvement="可减少推理时间 30-50%"
                )
                self.add_recommendation(
                    title="使用 vLLM 或 TensorRT-LLM",
                    priority="high",
                    description="使用优化的推理引擎替代 transformers",
                    expected_improvement="可提升推理速度 2-5 倍"
                )
            
            elif bottleneck["name"] == "GPU 利用率低":
                self.add_recommendation(
                    title="启用 Flash Attention",
                    priority="high",
                    description="Flash Attention 可显著提升注意力计算效率",
                    expected_improvement="可提升 GPU 利用率 20-40%"
                )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        返回:
            报告字典
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "hardware": self.hardware_info,
            "model": self.model_info,
            "inference": self.inference_metrics.to_dict() if self.inference_metrics else {},
            "gpu_statistics": self.gpu_statistics,
            "bottlenecks": self.bottlenecks,
            "recommendations": self.recommendations
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        转换为 JSON 字符串
        
        参数:
            indent: 缩进空格数
        
        返回:
            JSON 字符串
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_text(self) -> str:
        """
        转换为可读文本
        
        返回:
            文本报告
        """
        lines = [
            "=" * 70,
            "AI 模型推理性能分析报告",
            "=" * 70,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        if self.hardware_info:
            lines.extend([
                "硬件配置",
                "-" * 50
            ])
            gpu = self.hardware_info.get("gpu", {})
            if gpu:
                lines.append(f"  GPU: {gpu.get('name', 'Unknown')}")
                lines.append(f"  显存: {gpu.get('total_memory_mb', 0):.0f}MB")
                lines.append(f"  CUDA 核心: {gpu.get('cuda_cores', 'Unknown')}")
            lines.append("")
        
        if self.model_info:
            lines.extend([
                "模型配置",
                "-" * 50
            ])
            lines.append(f"  模型: {self.model_info.get('name', 'Unknown')}")
            lines.append(f"  参数量: {self.model_info.get('parameters', 'Unknown')}")
            lines.append(f"  量化: {self.model_info.get('quantization', 'Unknown')}")
            lines.append("")
        
        if self.inference_metrics:
            lines.extend([
                "推理性能",
                "-" * 50
            ])
            lines.append(f"  总耗时: {self.inference_metrics.total_time_ms/1000:.2f}秒")
            lines.append(f"  预处理: {self.inference_metrics.preprocess_time_ms:.2f}ms")
            lines.append(f"  推理: {self.inference_metrics.inference_time_ms:.2f}ms")
            lines.append(f"  后处理: {self.inference_metrics.postprocess_time_ms:.2f}ms")
            if self.inference_metrics.tokens_per_second > 0:
                lines.append(f"  生成速度: {self.inference_metrics.tokens_per_second:.1f} tokens/s")
            lines.append("")
        
        if self.bottlenecks:
            lines.extend([
                "性能瓶颈",
                "-" * 50
            ])
            for i, b in enumerate(self.bottlenecks, 1):
                lines.append(f"  {i}. [{b['severity'].upper()}] {b['name']}")
                lines.append(f"     影响: {b['impact']*100:.0f}%")
                lines.append(f"     {b['description']}")
            lines.append("")
        
        if self.recommendations:
            lines.extend([
                "优化建议",
                "-" * 50
            ])
            for i, r in enumerate(self.recommendations, 1):
                lines.append(f"  {i}. [{r['priority'].upper()}] {r['title']}")
                lines.append(f"     {r['description']}")
                lines.append(f"     预期改进: {r['expected_improvement']}")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)


def create_profiler() -> InferenceProfiler:
    """
    创建推理性能分析器
    
    返回:
        InferenceProfiler 实例
    """
    return InferenceProfiler()


def create_gpu_collector(device_id: int = 0) -> GPUMetricsCollector:
    """
    创建 GPU 指标收集器
    
    参数:
        device_id: GPU 设备 ID
    
    返回:
        GPUMetricsCollector 实例
    """
    return GPUMetricsCollector(device_id)


def create_report() -> PerformanceReport:
    """
    创建性能报告生成器
    
    返回:
        PerformanceReport 实例
    """
    return PerformanceReport()

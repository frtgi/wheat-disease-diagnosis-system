"""
硬件资源瓶颈分析脚本

分析 GPU、显存、计算能力等硬件资源瓶颈，包括：
- GPU 型号、显存大小、计算能力
- 当前显存使用情况
- GPU 利用率
- 内存带宽瓶颈
"""
import sys
import os
import time
import json
import platform
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import torch
import psutil


def get_gpu_basic_info() -> Dict[str, Any]:
    """
    获取 GPU 基础信息，包括型号、显存大小、计算能力
    
    返回:
        Dict[str, Any]: GPU 基础信息字典
    """
    gpu_info = {
        "cuda_available": False,
        "device_count": 0,
        "devices": [],
        "error": None
    }
    
    try:
        if not torch.cuda.is_available():
            gpu_info["error"] = "CUDA 不可用"
            return gpu_info
        
        gpu_info["cuda_available"] = True
        gpu_info["device_count"] = torch.cuda.device_count()
        gpu_info["cuda_version"] = torch.version.cuda
        gpu_info["pytorch_version"] = torch.__version__
        
        for i in range(gpu_info["device_count"]):
            props = torch.cuda.get_device_properties(i)
            device_data = {
                "device_id": i,
                "name": props.name,
                "total_memory_mb": round(props.total_memory / (1024 ** 2), 2),
                "total_memory_gb": round(props.total_memory / (1024 ** 3), 2),
                "multi_processor_count": props.multi_processor_count,
                "compute_capability": f"{props.major}.{props.minor}",
                "major": props.major,
                "minor": props.minor
            }
            gpu_info["devices"].append(device_data)
        
        gpu_info["current_device"] = torch.cuda.current_device()
        
    except Exception as e:
        gpu_info["error"] = str(e)
    
    return gpu_info


def get_gpu_memory_usage() -> Dict[str, Any]:
    """
    获取当前 GPU 显存使用情况
    
    返回:
        Dict[str, Any]: 显存使用情况字典
    """
    memory_info = {
        "cuda_available": False,
        "devices": [],
        "error": None
    }
    
    try:
        if not torch.cuda.is_available():
            memory_info["error"] = "CUDA 不可用"
            return memory_info
        
        memory_info["cuda_available"] = True
        
        for i in range(torch.cuda.device_count()):
            torch.cuda.set_device(i)
            
            total_memory = torch.cuda.get_device_properties(i).total_memory
            reserved_memory = torch.cuda.memory_reserved(i)
            allocated_memory = torch.cuda.memory_allocated(i)
            free_memory = total_memory - reserved_memory
            
            device_memory = {
                "device_id": i,
                "total_mb": round(total_memory / (1024 ** 2), 2),
                "reserved_mb": round(reserved_memory / (1024 ** 2), 2),
                "allocated_mb": round(allocated_memory / (1024 ** 2), 2),
                "free_mb": round(free_memory / (1024 ** 2), 2),
                "utilization_percent": round((reserved_memory / total_memory) * 100, 2) if total_memory > 0 else 0,
                "allocated_percent": round((allocated_memory / total_memory) * 100, 2) if total_memory > 0 else 0
            }
            memory_info["devices"].append(device_memory)
        
        memory_info["peak_memory_mb"] = round(torch.cuda.max_memory_allocated() / (1024 ** 2), 2)
        
    except Exception as e:
        memory_info["error"] = str(e)
    
    return memory_info


def get_gpu_utilization() -> Dict[str, Any]:
    """
    获取 GPU 利用率信息
    
    返回:
        Dict[str, Any]: GPU 利用率信息字典
    """
    utilization_info = {
        "cuda_available": False,
        "devices": [],
        "error": None
    }
    
    try:
        if not torch.cuda.is_available():
            utilization_info["error"] = "CUDA 不可用"
            return utilization_info
        
        utilization_info["cuda_available"] = True
        
        try:
            import pynvml
            pynvml.nvmlInit()
            
            for i in range(torch.cuda.device_count()):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                util_rates = pynvml.nvmlDeviceGetUtilizationRates(handle)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0
                
                try:
                    memory_info_nvml = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    memory_util = (memory_info_nvml.used / memory_info_nvml.total) * 100
                except Exception:
                    memory_util = util_rates.memory
                
                try:
                    clock_info = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                    sm_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
                    mem_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                except Exception:
                    clock_info = 0
                    sm_clock = 0
                    mem_clock = 0
                
                device_util = {
                    "device_id": i,
                    "gpu_utilization_percent": util_rates.gpu,
                    "memory_utilization_percent": memory_util,
                    "encoder_utilization_percent": getattr(util_rates, 'encoder', 0),
                    "decoder_utilization_percent": getattr(util_rates, 'decoder', 0),
                    "temperature_c": temp,
                    "power_usage_w": round(power_usage, 2),
                    "power_limit_w": round(power_limit, 2),
                    "power_utilization_percent": round((power_usage / power_limit) * 100, 2) if power_limit > 0 else 0,
                    "graphics_clock_mhz": clock_info,
                    "sm_clock_mhz": sm_clock,
                    "memory_clock_mhz": mem_clock
                }
                utilization_info["devices"].append(device_util)
            
            pynvml.nvmlShutdown()
            
        except ImportError:
            utilization_info["nvml_available"] = False
            utilization_info["error"] = "pynvml 未安装，无法获取详细利用率"
            
            for i in range(torch.cuda.device_count()):
                device_util = {
                    "device_id": i,
                    "note": "需要安装 pynvml 获取详细利用率"
                }
                utilization_info["devices"].append(device_util)
        
    except Exception as e:
        utilization_info["error"] = str(e)
    
    return utilization_info


def analyze_memory_bandwidth() -> Dict[str, Any]:
    """
    分析内存带宽瓶颈
    
    通过执行内存传输测试来评估内存带宽
    
    返回:
        Dict[str, Any]: 内存带宽分析结果
    """
    bandwidth_info = {
        "cuda_available": False,
        "tests": [],
        "theoretical_bandwidth": {},
        "bottleneck_analysis": {},
        "error": None
    }
    
    try:
        if not torch.cuda.is_available():
            bandwidth_info["error"] = "CUDA 不可用"
            return bandwidth_info
        
        bandwidth_info["cuda_available"] = True
        
        test_sizes = [
            (64, "64MB"),
            (128, "128MB"),
            (256, "256MB"),
            (512, "512MB"),
            (1024, "1GB")
        ]
        
        device = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(device)
        
        bandwidth_info["device_name"] = props.name
        bandwidth_info["compute_capability"] = f"{props.major}.{props.minor}"
        
        bandwidth_info["theoretical_bandwidth"] = estimate_theoretical_bandwidth(props)
        
        for size_mb, label in test_sizes:
            try:
                size_bytes = size_mb * 1024 * 1024
                num_elements = size_bytes // 4
                
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                
                start_time = time.perf_counter()
                tensor = torch.randn(num_elements, dtype=torch.float32, device="cuda")
                torch.cuda.synchronize()
                alloc_time = time.perf_counter() - start_time
                
                start_time = time.perf_counter()
                tensor_cpu = tensor.cpu()
                torch.cuda.synchronize()
                h2d_time = time.perf_counter() - start_time
                
                start_time = time.perf_counter()
                tensor_gpu = tensor_cpu.cuda()
                torch.cuda.synchronize()
                d2h_time = time.perf_counter() - start_time
                
                start_time = time.perf_counter()
                result = tensor * 2.0
                torch.cuda.synchronize()
                compute_time = time.perf_counter() - start_time
                
                h2d_bandwidth = (size_bytes / h2d_time) / (1024 ** 3) if h2d_time > 0 else 0
                d2h_bandwidth = (size_bytes / d2h_time) / (1024 ** 3) if d2h_time > 0 else 0
                compute_bandwidth = (size_bytes * 2 / compute_time) / (1024 ** 3) if compute_time > 0 else 0
                
                test_result = {
                    "size": label,
                    "size_mb": size_mb,
                    "allocation_time_ms": round(alloc_time * 1000, 2),
                    "h2d_time_ms": round(h2d_time * 1000, 2),
                    "d2h_time_ms": round(d2h_time * 1000, 2),
                    "compute_time_ms": round(compute_time * 1000, 2),
                    "h2d_bandwidth_gbps": round(h2d_bandwidth, 2),
                    "d2h_bandwidth_gbps": round(d2h_bandwidth, 2),
                    "compute_bandwidth_gbps": round(compute_bandwidth, 2)
                }
                bandwidth_info["tests"].append(test_result)
                
                del tensor, tensor_cpu, tensor_gpu, result
                torch.cuda.empty_cache()
                
            except Exception as e:
                test_result = {
                    "size": label,
                    "error": str(e)
                }
                bandwidth_info["tests"].append(test_result)
        
        bandwidth_info["bottleneck_analysis"] = analyze_bandwidth_bottleneck(bandwidth_info)
        
    except Exception as e:
        bandwidth_info["error"] = str(e)
    
    return bandwidth_info


def estimate_theoretical_bandwidth(props) -> Dict[str, Any]:
    """
    估算 GPU 理论内存带宽
    
    参数:
        props: torch.cuda 设备属性对象
    
    返回:
        Dict[str, Any]: 理论带宽估算结果
    """
    theoretical = {
        "estimated_gbps": 0,
        "memory_bus_width": "Unknown",
        "memory_type": "Unknown",
        "method": "estimation"
    }
    
    gpu_name = props.name.lower()
    
    if "rtx 4090" in gpu_name:
        theoretical.update({
            "estimated_gbps": 1008,
            "memory_bus_width": "384-bit",
            "memory_type": "GDDR6X"
        })
    elif "rtx 4080" in gpu_name:
        theoretical.update({
            "estimated_gbps": 717,
            "memory_bus_width": "256-bit",
            "memory_type": "GDDR6X"
        })
    elif "rtx 4070" in gpu_name:
        theoretical.update({
            "estimated_gbps": 504,
            "memory_bus_width": "192-bit",
            "memory_type": "GDDR6X"
        })
    elif "rtx 3090" in gpu_name:
        theoretical.update({
            "estimated_gbps": 936,
            "memory_bus_width": "384-bit",
            "memory_type": "GDDR6X"
        })
    elif "rtx 3080" in gpu_name:
        theoretical.update({
            "estimated_gbps": 760,
            "memory_bus_width": "320-bit",
            "memory_type": "GDDR6X"
        })
    elif "rtx 3070" in gpu_name:
        theoretical.update({
            "estimated_gbps": 448,
            "memory_bus_width": "256-bit",
            "memory_type": "GDDR6"
        })
    elif "rtx 3060" in gpu_name:
        theoretical.update({
            "estimated_gbps": 360,
            "memory_bus_width": "192-bit",
            "memory_type": "GDDR6"
        })
    elif "rtx 3050" in gpu_name:
        theoretical.update({
            "estimated_gbps": 224,
            "memory_bus_width": "128-bit",
            "memory_type": "GDDR6"
        })
    elif "a100" in gpu_name:
        theoretical.update({
            "estimated_gbps": 2039,
            "memory_bus_width": "5120-bit",
            "memory_type": "HBM2e"
        })
    elif "v100" in gpu_name:
        theoretical.update({
            "estimated_gbps": 900,
            "memory_bus_width": "4096-bit",
            "memory_type": "HBM2"
        })
    elif "t4" in gpu_name:
        theoretical.update({
            "estimated_gbps": 320,
            "memory_bus_width": "256-bit",
            "memory_type": "GDDR6"
        })
    else:
        memory_gb = props.total_memory / (1024 ** 3)
        if memory_gb >= 20:
            theoretical["estimated_gbps"] = 800
        elif memory_gb >= 10:
            theoretical["estimated_gbps"] = 500
        elif memory_gb >= 6:
            theoretical["estimated_gbps"] = 300
        else:
            theoretical["estimated_gbps"] = 200
    
    return theoretical


def analyze_bandwidth_bottleneck(bandwidth_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析带宽瓶颈
    
    参数:
        bandwidth_info: 带宽测试结果
    
    返回:
        Dict[str, Any]: 瓶颈分析结果
    """
    analysis = {
        "h2d_efficiency": 0,
        "d2h_efficiency": 0,
        "bottlenecks": [],
        "severity": "none"
    }
    
    if not bandwidth_info.get("tests"):
        return analysis
    
    theoretical = bandwidth_info.get("theoretical_bandwidth", {}).get("estimated_gbps", 0)
    
    if theoretical <= 0:
        return analysis
    
    valid_tests = [t for t in bandwidth_info["tests"] if "h2d_bandwidth_gbps" in t]
    
    if not valid_tests:
        return analysis
    
    large_tests = [t for t in valid_tests if t.get("size_mb", 0) >= 256]
    
    if large_tests:
        avg_h2d = sum(t["h2d_bandwidth_gbps"] for t in large_tests) / len(large_tests)
        avg_d2h = sum(t["d2h_bandwidth_gbps"] for t in large_tests) / len(large_tests)
    else:
        avg_h2d = sum(t["h2d_bandwidth_gbps"] for t in valid_tests) / len(valid_tests)
        avg_d2h = sum(t["d2h_bandwidth_gbps"] for t in valid_tests) / len(valid_tests)
    
    analysis["h2d_efficiency"] = round((avg_h2d / theoretical) * 100, 1)
    analysis["d2h_efficiency"] = round((avg_d2h / theoretical) * 100, 1)
    analysis["avg_h2d_bandwidth_gbps"] = round(avg_h2d, 2)
    analysis["avg_d2h_bandwidth_gbps"] = round(avg_d2h, 2)
    
    if analysis["h2d_efficiency"] < 50:
        analysis["bottlenecks"].append({
            "type": "h2d_bandwidth",
            "severity": "high",
            "description": f"Host-to-Device 带宽效率仅 {analysis['h2d_efficiency']:.1f}%，数据传输可能是瓶颈"
        })
        analysis["severity"] = "high"
    elif analysis["h2d_efficiency"] < 70:
        analysis["bottlenecks"].append({
            "type": "h2d_bandwidth",
            "severity": "medium",
            "description": f"Host-to-Device 带宽效率 {analysis['h2d_efficiency']:.1f}%，存在优化空间"
        })
        if analysis["severity"] != "high":
            analysis["severity"] = "medium"
    
    if analysis["d2h_efficiency"] < 50:
        analysis["bottlenecks"].append({
            "type": "d2h_bandwidth",
            "severity": "high",
            "description": f"Device-to-Host 带宽效率仅 {analysis['d2h_efficiency']:.1f}%，结果回传可能是瓶颈"
        })
        if analysis["severity"] not in ["high", "critical"]:
            analysis["severity"] = "high"
    elif analysis["d2h_efficiency"] < 70:
        analysis["bottlenecks"].append({
            "type": "d2h_bandwidth",
            "severity": "medium",
            "description": f"Device-to-Host 带宽效率 {analysis['d2h_efficiency']:.1f}%，存在优化空间"
        })
        if analysis["severity"] not in ["high", "critical", "medium"]:
            analysis["severity"] = "medium"
    
    return analysis


def identify_bottlenecks(gpu_info: Dict, memory_info: Dict, utilization_info: Dict, bandwidth_info: Dict) -> List[Dict[str, Any]]:
    """
    综合识别硬件瓶颈
    
    参数:
        gpu_info: GPU 基础信息
        memory_info: 显存使用信息
        utilization_info: GPU 利用率信息
        bandwidth_info: 内存带宽信息
    
    返回:
        List[Dict[str, Any]]: 瓶颈列表
    """
    bottlenecks = []
    
    if not gpu_info.get("cuda_available"):
        bottlenecks.append({
            "type": "cuda_unavailable",
            "severity": "critical",
            "category": "gpu",
            "description": "CUDA 不可用，无法使用 GPU 加速",
            "impact": "无法运行 GPU 模型",
            "recommendation": "检查 CUDA 驱动和 PyTorch 安装"
        })
        return bottlenecks
    
    for device in gpu_info.get("devices", []):
        device_id = device.get("device_id", 0)
        device_name = device.get("name", "Unknown")
        total_memory_mb = device.get("total_memory_mb", 0)
        compute_capability = device.get("compute_capability", "0.0")
        
        if total_memory_mb < 4096:
            bottlenecks.append({
                "type": "vram_severely_limited",
                "severity": "critical",
                "category": "memory",
                "device_id": device_id,
                "device_name": device_name,
                "description": f"显存仅 {total_memory_mb:.0f}MB，严重限制模型选择",
                "impact": "只能运行小型模型或需要激进量化",
                "recommendation": "使用 INT4 量化、CPU offload 或更小的模型"
            })
        elif total_memory_mb < 8192:
            bottlenecks.append({
                "type": "vram_limited",
                "severity": "high",
                "category": "memory",
                "device_id": device_id,
                "device_name": device_name,
                "description": f"显存 {total_memory_mb:.0f}MB，对大模型推理有限制",
                "impact": "4B-7B 模型需要量化或 offload",
                "recommendation": "使用 INT8/INT4 量化或模型分割"
            })
        elif total_memory_mb < 16384:
            bottlenecks.append({
                "type": "vram_moderate",
                "severity": "medium",
                "category": "memory",
                "device_id": device_id,
                "device_name": device_name,
                "description": f"显存 {total_memory_mb:.0f}MB，可运行中等规模模型",
                "impact": "13B+ 模型需要量化",
                "recommendation": "可运行 7B-13B 模型，更大模型需要量化"
            })
        
        major, minor = map(int, compute_capability.split("."))
        if major < 7:
            bottlenecks.append({
                "type": "compute_capability_low",
                "severity": "high",
                "category": "compute",
                "device_id": device_id,
                "device_name": device_name,
                "description": f"计算能力 {compute_capability}，不支持某些现代特性",
                "impact": "无法使用 Tensor Core、Flash Attention 等优化",
                "recommendation": "考虑升级 GPU 或使用兼容的模型配置"
            })
        elif major == 7 and minor < 5:
            bottlenecks.append({
                "type": "compute_capability_limited",
                "severity": "medium",
                "category": "compute",
                "device_id": device_id,
                "device_name": device_name,
                "description": f"计算能力 {compute_capability}，部分优化不可用",
                "impact": "Flash Attention 2 等特性可能不可用",
                "recommendation": "使用 Flash Attention 1 或其他兼容配置"
            })
    
    for device in memory_info.get("devices", []):
        device_id = device.get("device_id", 0)
        utilization = device.get("utilization_percent", 0)
        free_mb = device.get("free_mb", 0)
        
        if utilization > 90:
            bottlenecks.append({
                "type": "vram_exhausted",
                "severity": "critical",
                "category": "memory",
                "device_id": device_id,
                "description": f"显存使用率 {utilization:.1f}%，几乎耗尽",
                "impact": "可能导致 OOM 错误",
                "recommendation": "释放显存、减小 batch size 或使用量化"
            })
        elif utilization > 75:
            bottlenecks.append({
                "type": "vram_high",
                "severity": "high",
                "category": "memory",
                "device_id": device_id,
                "description": f"显存使用率 {utilization:.1f}%，接近上限",
                "impact": "可能影响模型加载和推理稳定性",
                "recommendation": "监控显存使用，考虑优化"
            })
    
    for device in utilization_info.get("devices", []):
        device_id = device.get("device_id", 0)
        gpu_util = device.get("gpu_utilization_percent", 0)
        power_util = device.get("power_utilization_percent", 0)
        
        if gpu_util < 30 and power_util > 50:
            bottlenecks.append({
                "type": "gpu_underutilized",
                "severity": "medium",
                "category": "compute",
                "device_id": device_id,
                "description": f"GPU 利用率仅 {gpu_util:.1f}%，但功耗 {power_util:.1f}%",
                "impact": "可能存在 CPU 瓶颈或数据传输瓶颈",
                "recommendation": "检查数据加载、预处理是否在 CPU 上成为瓶颈"
            })
        
        if power_util > 95:
            bottlenecks.append({
                "type": "power_limited",
                "severity": "medium",
                "category": "power",
                "device_id": device_id,
                "description": f"功耗已达 {power_util:.1f}% 上限",
                "impact": "GPU 可能因功耗限制而降频",
                "recommendation": "检查散热情况，必要时提高功耗限制"
            })
    
    bandwidth_bottlenecks = bandwidth_info.get("bottleneck_analysis", {}).get("bottlenecks", [])
    for bn in bandwidth_bottlenecks:
        bottlenecks.append({
            "type": bn.get("type", "bandwidth"),
            "severity": bn.get("severity", "medium"),
            "category": "bandwidth",
            "description": bn.get("description", "内存带宽瓶颈"),
            "impact": "数据传输速度限制整体性能",
            "recommendation": "使用 pinned memory、异步传输优化"
        })
    
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    bottlenecks.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))
    
    return bottlenecks


def generate_recommendations(bottlenecks: List[Dict], gpu_info: Dict) -> List[Dict[str, Any]]:
    """
    基于瓶颈分析生成优化建议
    
    参数:
        bottlenecks: 瓶颈列表
        gpu_info: GPU 基础信息
    
    返回:
        List[Dict[str, Any]]: 优化建议列表
    """
    recommendations = []
    seen_types = set()
    
    for bottleneck in bottlenecks:
        btype = bottleneck.get("type", "")
        
        if btype in seen_types:
            continue
        seen_types.add(btype)
        
        if btype == "vram_severely_limited":
            recommendations.append({
                "priority": "critical",
                "category": "memory",
                "title": "显存严重不足优化",
                "actions": [
                    "使用 INT4 量化加载模型（bitsandbytes）",
                    "启用 CPU offload，将部分层放在 CPU",
                    "使用更小的模型（如 Qwen3-VL-2B）",
                    "减小 max_new_tokens 限制",
                    "使用 gradient checkpointing 减少显存占用"
                ],
                "expected_improvement": "可减少显存占用 50-70%"
            })
        
        elif btype == "vram_limited":
            recommendations.append({
                "priority": "high",
                "category": "memory",
                "title": "显存优化",
                "actions": [
                    "使用 INT8 量化加载模型",
                    "启用 bfloat16 混合精度",
                    "使用 device_map='auto' 自动分配",
                    "考虑模型分割或多 GPU 并行"
                ],
                "expected_improvement": "可减少显存占用 30-50%"
            })
        
        elif btype == "compute_capability_low":
            recommendations.append({
                "priority": "high",
                "category": "compute",
                "title": "计算能力兼容性优化",
                "actions": [
                    "禁用 Flash Attention，使用标准注意力",
                    "避免使用 bf16，改用 fp16 或 fp32",
                    "检查模型是否支持当前计算能力",
                    "考虑升级 GPU 硬件"
                ],
                "expected_improvement": "确保模型兼容性"
            })
        
        elif btype == "gpu_underutilized":
            recommendations.append({
                "priority": "medium",
                "category": "performance",
                "title": "GPU 利用率优化",
                "actions": [
                    "增加 batch size 以充分利用 GPU",
                    "使用 DataLoader 的 num_workers 并行加载数据",
                    "使用 pinned memory 加速数据传输",
                    "检查 CPU 是否成为瓶颈",
                    "使用异步数据传输"
                ],
                "expected_improvement": "可提升 GPU 利用率 20-40%"
            })
        
        elif btype == "h2d_bandwidth":
            recommendations.append({
                "priority": "medium",
                "category": "bandwidth",
                "title": "Host-to-Device 带宽优化",
                "actions": [
                    "使用 pinned memory (non_blocking=True)",
                    "批量传输数据而非逐个传输",
                    "使用 CUDA Streams 实现异步传输",
                    "减少 CPU-GPU 数据交换频率"
                ],
                "expected_improvement": "可提升传输效率 30-50%"
            })
        
        elif btype == "d2h_bandwidth":
            recommendations.append({
                "priority": "medium",
                "category": "bandwidth",
                "title": "Device-to-Host 带宽优化",
                "actions": [
                    "减少不必要的 GPU 结果回传",
                    "在 GPU 上完成更多计算",
                    "使用异步传输避免阻塞",
                    "批量获取结果"
                ],
                "expected_improvement": "可减少数据回传开销"
            })
        
        elif btype == "power_limited":
            recommendations.append({
                "priority": "low",
                "category": "power",
                "title": "功耗限制优化",
                "actions": [
                    "检查 GPU 散热情况",
                    "清理 GPU 风扇灰尘",
                    "考虑提高功耗限制（需谨慎）",
                    "降低环境温度"
                ],
                "expected_improvement": "避免降频，保持稳定性能"
            })
    
    general_recs = [
        {
            "priority": "info",
            "category": "general",
            "title": "通用性能优化建议",
            "actions": [
                "使用 torch.compile() 编译模型加速推理",
                "使用 torch.inference_mode() 替代 torch.no_grad()",
                "考虑使用 vLLM 或 TensorRT-LLM 部署",
                "定期清理 GPU 缓存 (torch.cuda.empty_cache())"
            ]
        }
    ]
    
    recommendations.extend(general_recs)
    
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "info"), 4))
    
    return recommendations


def generate_report() -> str:
    """
    生成完整的硬件资源瓶颈分析报告
    
    返回:
        str: 格式化的分析报告
    """
    report_lines = []
    
    report_lines.append("=" * 70)
    report_lines.append("硬件资源瓶颈分析报告")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 70)
    
    report_lines.append("\n[1] GPU 基础信息")
    report_lines.append("-" * 50)
    gpu_info = get_gpu_basic_info()
    
    if gpu_info.get("cuda_available"):
        report_lines.append(f"  CUDA 版本: {gpu_info.get('cuda_version', 'Unknown')}")
        report_lines.append(f"  PyTorch 版本: {gpu_info.get('pytorch_version', 'Unknown')}")
        report_lines.append(f"  GPU 数量: {gpu_info.get('device_count', 0)}")
        
        for device in gpu_info.get("devices", []):
            report_lines.append(f"\n  GPU {device['device_id']}: {device['name']}")
            report_lines.append(f"    显存大小: {device['total_memory_mb']:.0f} MB ({device['total_memory_gb']:.1f} GB)")
            report_lines.append(f"    计算能力: {device['compute_capability']}")
            report_lines.append(f"    SM 数量: {device['multi_processor_count']}")
    else:
        report_lines.append(f"  CUDA 不可用: {gpu_info.get('error', 'Unknown')}")
    
    report_lines.append("\n[2] 显存使用情况")
    report_lines.append("-" * 50)
    memory_info = get_gpu_memory_usage()
    
    if memory_info.get("cuda_available"):
        for device in memory_info.get("devices", []):
            report_lines.append(f"\n  GPU {device['device_id']}:")
            report_lines.append(f"    总显存: {device['total_mb']:.0f} MB")
            report_lines.append(f"    已预留: {device['reserved_mb']:.0f} MB ({device['utilization_percent']:.1f}%)")
            report_lines.append(f"    已分配: {device['allocated_mb']:.0f} MB ({device['allocated_percent']:.1f}%)")
            report_lines.append(f"    可用: {device['free_mb']:.0f} MB")
        
        report_lines.append(f"\n  峰值显存使用: {memory_info.get('peak_memory_mb', 0):.0f} MB")
    else:
        report_lines.append(f"  无法获取显存信息: {memory_info.get('error', 'Unknown')}")
    
    report_lines.append("\n[3] GPU 利用率")
    report_lines.append("-" * 50)
    utilization_info = get_gpu_utilization()
    
    if utilization_info.get("devices"):
        for device in utilization_info.get("devices", []):
            report_lines.append(f"\n  GPU {device.get('device_id', 0)}:")
            report_lines.append(f"    GPU 利用率: {device.get('gpu_utilization_percent', 0):.1f}%")
            report_lines.append(f"    显存利用率: {device.get('memory_utilization_percent', 0):.1f}%")
            report_lines.append(f"    温度: {device.get('temperature_c', 0)}°C")
            report_lines.append(f"    功耗: {device.get('power_usage_w', 0):.1f}W / {device.get('power_limit_w', 0):.1f}W ({device.get('power_utilization_percent', 0):.1f}%)")
            report_lines.append(f"    图形时钟: {device.get('graphics_clock_mhz', 0)} MHz")
            report_lines.append(f"    显存时钟: {device.get('memory_clock_mhz', 0)} MHz")
    else:
        report_lines.append(f"  无法获取利用率: {utilization_info.get('error', '需要安装 pynvml')}")
    
    report_lines.append("\n[4] 内存带宽分析")
    report_lines.append("-" * 50)
    bandwidth_info = analyze_memory_bandwidth()
    
    if bandwidth_info.get("cuda_available"):
        theoretical = bandwidth_info.get("theoretical_bandwidth", {})
        report_lines.append(f"  设备: {bandwidth_info.get('device_name', 'Unknown')}")
        report_lines.append(f"  理论带宽: {theoretical.get('estimated_gbps', 0):.0f} GB/s ({theoretical.get('memory_type', 'Unknown')}, {theoretical.get('memory_bus_width', 'Unknown')})")
        
        report_lines.append("\n  带宽测试结果:")
        for test in bandwidth_info.get("tests", []):
            if "error" not in test:
                report_lines.append(f"    {test['size']}:")
                report_lines.append(f"      H2D: {test['h2d_bandwidth_gbps']:.2f} GB/s ({test['h2d_time_ms']:.2f}ms)")
                report_lines.append(f"      D2H: {test['d2h_bandwidth_gbps']:.2f} GB/s ({test['d2h_time_ms']:.2f}ms)")
        
        bottleneck_analysis = bandwidth_info.get("bottleneck_analysis", {})
        if bottleneck_analysis.get("h2d_efficiency"):
            report_lines.append(f"\n  H2D 带宽效率: {bottleneck_analysis.get('h2d_efficiency', 0):.1f}%")
            report_lines.append(f"  D2H 带宽效率: {bottleneck_analysis.get('d2h_efficiency', 0):.1f}%")
    else:
        report_lines.append(f"  无法进行带宽测试: {bandwidth_info.get('error', 'Unknown')}")
    
    report_lines.append("\n[5] 瓶颈识别")
    report_lines.append("-" * 50)
    bottlenecks = identify_bottlenecks(gpu_info, memory_info, utilization_info, bandwidth_info)
    
    if bottlenecks:
        for i, bn in enumerate(bottlenecks, 1):
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(bn.get("severity", "low"), "⚪")
            report_lines.append(f"\n  {i}. {severity_icon} [{bn.get('severity', 'unknown').upper()}] {bn.get('type', 'unknown')}")
            report_lines.append(f"     描述: {bn.get('description', 'N/A')}")
            report_lines.append(f"     影响: {bn.get('impact', 'N/A')}")
            report_lines.append(f"     建议: {bn.get('recommendation', 'N/A')}")
    else:
        report_lines.append("  ✅ 未发现明显硬件瓶颈")
    
    report_lines.append("\n[6] 优化建议")
    report_lines.append("-" * 50)
    recommendations = generate_recommendations(bottlenecks, gpu_info)
    
    for i, rec in enumerate(recommendations, 1):
        priority_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(rec.get("priority", "info"), "ℹ️")
        report_lines.append(f"\n  {i}. {priority_icon} [{rec.get('priority', 'info').upper()}] {rec.get('title', 'N/A')}")
        
        for action in rec.get("actions", []):
            report_lines.append(f"     - {action}")
        
        if rec.get("expected_improvement"):
            report_lines.append(f"     预期效果: {rec.get('expected_improvement')}")
    
    report_lines.append("\n" + "=" * 70)
    report_lines.append("分析完成")
    report_lines.append("=" * 70)
    
    return "\n".join(report_lines)


def save_analysis_result(output_path: str = None) -> Dict[str, Any]:
    """
    保存分析结果到 JSON 文件
    
    参数:
        output_path: 输出文件路径，默认为脚本目录下的 hardware_bottleneck_result.json
    
    返回:
        Dict[str, Any]: 完整的分析结果
    """
    gpu_info = get_gpu_basic_info()
    memory_info = get_gpu_memory_usage()
    utilization_info = get_gpu_utilization()
    bandwidth_info = analyze_memory_bandwidth()
    bottlenecks = identify_bottlenecks(gpu_info, memory_info, utilization_info, bandwidth_info)
    recommendations = generate_recommendations(bottlenecks, gpu_info)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "system_info": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        },
        "gpu_info": gpu_info,
        "memory_usage": memory_info,
        "utilization": utilization_info,
        "bandwidth": bandwidth_info,
        "bottlenecks": bottlenecks,
        "recommendations": recommendations
    }
    
    if output_path is None:
        output_path = str(Path(__file__).parent / "hardware_bottleneck_result.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 分析结果已保存到: {output_path}")
    
    return result


if __name__ == "__main__":
    print(generate_report())
    save_analysis_result()

"""
硬件资源瓶颈分析脚本

分析 GPU、CPU、内存等硬件资源，识别性能瓶颈
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import json
from datetime import datetime


def analyze_hardware() -> dict:
    """
    分析硬件资源
    
    返回:
        硬件分析结果
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "gpu": {},
        "cpu": {},
        "memory": {},
        "bottlenecks": [],
        "recommendations": []
    }
    
    print("=" * 60)
    print("硬件资源分析")
    print("=" * 60)
    
    # GPU 分析
    print("\n[1] GPU 分析")
    print("-" * 40)
    try:
        import torch
        
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()
            device_name = torch.cuda.get_device_name(current_device)
            total_memory = torch.cuda.get_device_properties(current_device).total_memory
            total_memory_mb = total_memory / (1024 ** 2)
            multi_processor = torch.cuda.get_device_properties(current_device).multi_processor_count
            compute_capability = f"{torch.cuda.get_device_properties(current_device).major}.{torch.cuda.get_device_properties(current_device).minor}"
            
            result["gpu"] = {
                "cuda_available": True,
                "device_count": device_count,
                "current_device": current_device,
                "name": device_name,
                "total_memory_mb": round(total_memory_mb, 2),
                "multi_processor_count": multi_processor,
                "compute_capability": compute_capability,
                "cuda_version": torch.version.cuda
            }
            
            print(f"  GPU 型号: {device_name}")
            print(f"  显存大小: {total_memory_mb:.0f} MB")
            print(f"  CUDA 核心: {multi_processor}")
            print(f"  计算能力: {compute_capability}")
            print(f"  CUDA 版本: {torch.version.cuda}")
            
            # 显存瓶颈分析
            if total_memory_mb < 6000:
                bottleneck = {
                    "type": "vram_limited",
                    "severity": "critical",
                    "description": f"显存仅 {total_memory_mb:.0f}MB，对于 4B 模型严重不足",
                    "impact": 0.9
                }
                result["bottlenecks"].append(bottleneck)
                print(f"  ⚠️ 瓶颈: 显存容量不足")
            
            # 尝试获取 NVML 信息
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(current_device)
                
                power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0
                result["gpu"]["power_limit_w"] = power_limit
                
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                result["gpu"]["temperature_c"] = temp
                
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                result["gpu"]["gpu_utilization"] = util.gpu
                result["gpu"]["memory_utilization"] = util.memory
                
                print(f"  功耗限制: {power_limit:.0f}W")
                print(f"  当前温度: {temp}°C")
                print(f"  GPU 利用率: {util.gpu}%")
                print(f"  显存利用率: {util.memory}%")
                
                pynvml.nvmlShutdown()
            except ImportError:
                print("  (pynvml 未安装，跳过详细 GPU 信息)")
            except Exception as e:
                print(f"  (获取 NVML 信息失败: {e})")
            
        else:
            result["gpu"]["cuda_available"] = False
            print("  CUDA 不可用")
            
    except ImportError:
        result["gpu"]["cuda_available"] = False
        print("  PyTorch 未安装")
    
    # CPU 分析
    print("\n[2] CPU 分析")
    print("-" * 40)
    try:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        result["cpu"]["cores"] = cpu_count
        print(f"  CPU 核心: {cpu_count}")
        
        try:
            import psutil
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                result["cpu"]["frequency_mhz"] = cpu_freq.current
                print(f"  CPU 频率: {cpu_freq.current:.0f} MHz")
            
            cpu_percent = psutil.cpu_percent(interval=1)
            result["cpu"]["utilization_percent"] = cpu_percent
            print(f"  CPU 利用率: {cpu_percent:.1f}%")
        except ImportError:
            print("  (psutil 未安装，跳过 CPU 详细信息)")
            
    except Exception as e:
        print(f"  CPU 分析失败: {e}")
    
    # 内存分析
    print("\n[3] 内存分析")
    print("-" * 40)
    try:
        import psutil
        mem = psutil.virtual_memory()
        result["memory"] = {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "utilization_percent": mem.percent
        }
        print(f"  总内存: {mem.total / (1024 ** 3):.1f} GB")
        print(f"  可用内存: {mem.available / (1024 ** 3):.1f} GB")
        print(f"  内存利用率: {mem.percent:.1f}%")
        
        if mem.percent > 80:
            bottleneck = {
                "type": "memory_pressure",
                "severity": "medium",
                "description": f"系统内存利用率 {mem.percent:.1f}%，可能影响性能",
                "impact": 0.5
            }
            result["bottlenecks"].append(bottleneck)
            print(f"  ⚠️ 瓶颈: 系统内存压力大")
            
    except ImportError:
        print("  (psutil 未安装，跳过内存分析)")
    
    # 生成建议
    print("\n[4] 瓶颈总结")
    print("-" * 40)
    
    for i, b in enumerate(result["bottlenecks"], 1):
        print(f"  {i}. [{b['severity'].upper()}] {b['description']}")
    
    if not result["bottlenecks"]:
        print("  未发现明显硬件瓶颈")
    
    # 优化建议
    print("\n[5] 优化建议")
    print("-" * 40)
    
    gpu_memory = result.get("gpu", {}).get("total_memory_mb", 0)
    if gpu_memory > 0 and gpu_memory < 8000:
        rec = {
            "priority": "high",
            "title": "显存优化",
            "description": "显存不足是主要瓶颈，建议：\n  1. 使用更小的模型（如 Qwen3-VL-2B）\n  2. 启用更激进的量化（INT8 或更低）\n  3. 使用 CPU offload 分担显存压力\n  4. 减少 max_new_tokens 限制",
            "expected_improvement": "可减少显存占用 30-50%"
        }
        result["recommendations"].append(rec)
        print(f"  [HIGH] {rec['title']}")
        print(f"         {rec['expected_improvement']}")
    
    print("\n" + "=" * 60)
    
    return result


if __name__ == "__main__":
    result = analyze_hardware()
    
    # 保存结果
    output_path = os.path.join(os.path.dirname(__file__), "hardware_analysis_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n分析结果已保存到: {output_path}")

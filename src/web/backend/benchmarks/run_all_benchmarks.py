# -*- coding: utf-8 -*-
"""
基准测试运行器 - 收集所有基准数据并输出结果
"""
import sys
import os
import json
import platform

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND_DIR)
os.environ.setdefault("DEBUG", "True")


def collect_env_info():
    """收集环境信息"""
    info = {
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
    }

    try:
        import torch
        info["pytorch"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1)
    except Exception:
        info["pytorch"] = "N/A"

    for mod_name, attr in [("ultralytics", "__version__"), ("transformers", "__version__"), ("fastapi", "__version__")]:
        try:
            m = __import__(mod_name)
            info[mod_name] = getattr(m, attr, "unknown")
        except ImportError:
            pass

    return info


def run_sse_benchmarks():
    """运行 SSE 基准测试（不依赖 AI 模型）"""
    from benchmarks.benchmark_sse_latency import (
        benchmark_sse_manager_creation,
        benchmark_sse_progress_event,
        benchmark_sse_heartbeat,
        benchmark_sse_first_event,
    )

    results = {}
    print("\n" + "=" * 60)
    print("[SSE] Manager 创建延迟")
    results["manager_creation"] = benchmark_sse_manager_creation(100)

    print("\n" + "=" * 60)
    print("[SSE] ProgressEvent 格式化延迟")
    results["progress_event"] = benchmark_sse_progress_event(1000)

    print("\n" + "=" * 60)
    print("[SSE] HeartbeatEvent 生成延迟")
    results["heartbeat"] = benchmark_sse_heartbeat(1000)

    print("\n" + "=" * 60)
    print("[SSE] 首个事件到达延迟")
    results["first_event"] = benchmark_sse_first_event(50)

    return results


def run_yolo_benchmark():
    """运行 YOLO 基准测试"""
    try:
        from benchmarks.benchmark_yolo_inference import benchmark_yolo_inference
        return benchmark_yolo_inference(iterations=3)
    except Exception as e:
        return {"status": "error", "error": str(e), "note": f"N/A ({e})"}


def run_qwen_benchmarks():
    """运行 Qwen 基准测试"""
    results = {}
    try:
        from benchmarks.benchmark_qwen_inference import (
            benchmark_qwen_first_inference,
            benchmark_qwen_subsequent_inference,
        )
        print("\n[Qwen] 首次推理 (含懒加载)")
        results["first_inference"] = benchmark_qwen_first_inference(iterations=1)

        print("\n[Qwen] 后续推理 (模型已加载)")
        results["subsequent_inference"] = benchmark_qwen_subsequent_inference(iterations=2)
    except Exception as e:
        results["error"] = str(e)
        results["note"] = f"N/A ({e})"
    return results


def run_full_diagnosis_benchmark():
    """运行完整诊断流程基准测试"""
    try:
        from benchmarks.benchmark_full_diagnosis import benchmark_full_diagnosis
        return benchmark_full_diagnosis(iterations=1)
    except Exception as e:
        return {"status": "error", "error": str(e), "note": f"N/A ({e})"}


def main():
    """主函数：运行全部基准测试并汇总报告"""
    print("#" * 70)
    print("# WheatAgent 性能基准测试套件 - 完整运行")
    print("#" * 70)

    env = collect_env_info()
    print("\n## 环境信息")
    for k, v in env.items():
        print(f"   {k}: {v}")

    all_results = {
        "env": env,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }

    print("\n\n### 1/4: SSE 延迟基准测试")
    all_results["sse"] = run_sse_benchmarks()

    print("\n\n### 2/4: YOLO 推理基准测试")
    all_results["yolo"] = run_yolo_benchmark()

    print("\n\n### 3/4: Qwen 推理基准测试")
    all_results["qwen"] = run_qwen_benchmarks()

    print("\n\n### 4/4: 完整诊断流程基准测试")
    all_results["full_diagnosis"] = run_full_diagnosis_benchmark()

    output_file = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'#'*70}")
    print(f"# 结果已保存至: {output_file}")
    print(f"{'#'*70}")

    return all_results


if __name__ == "__main__":
    results = main()

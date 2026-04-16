# -*- coding: utf-8 -*-
"""
性能基准测试：YOLOv8 推理延迟

测量 YOLOv8 单图推理的响应时间，用于：
- 建立性能基线数据
- 对比优化前后效果
- 检测性能退化

使用 time.perf_counter() 高精度计时。
目标值: < 150ms (FP16 半精度)
"""
import time
import statistics
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

YOLO_TARGET_MS = 150.0


def create_test_image(width: int = 640, height: int = 640) -> Image.Image:
    """
    创建测试用纯色图像

    Args:
        width: 图像宽度（像素）
        height: 图像高度（像素）

    Returns:
        Image.Image: RGB 模式的 PIL 图像对象
    """
    arr = np.random.randint(100, 200, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def benchmark_yolo_inference(iterations: int = 3) -> Dict[str, Any]:
    """
    执行 YOLOv8 推理基准测试并返回统计结果

    通过创建测试图像并调用 YOLOv8Service.detect() 测量单次推理耗时。
    如果模型未加载，记录为 N/A 并跳过。

    Args:
        iterations: 推理迭代次数（默认 3 次，AI 推理耗时较长）

    Returns:
        Dict[str, Any]: 包含以下字段的统计结果字典：
            - mean: 平均耗时（秒）
            - median: 中位数耗时（秒）
            - min: 最小耗时（秒）
            - max: 最大耗时（秒）
            - stdev: 标准差（秒）
            - iterations: 迭代次数
            - target_ms: 目标值（毫秒）
            - status: 测试状态 ("passed" / "warning" / "skipped")
            - model_loaded: 模型是否已加载
            - fp16_used: 是否使用了 FP16
            - details: 各次迭代的详细结果列表
    """
    print("=" * 60)
    print("📊 YOLOv8 推理延迟基准测试")
    print(f"   目标值: < {YOLO_TARGET_MS}ms (FP16 半精度)")
    print(f"   迭代次数: {iterations}")
    print("=" * 60)

    results = []
    details = []
    model_loaded = False
    fp16_used = False

    try:
        from app.services.yolo_service import get_yolo_service, YOLOv8Service

        yolo_service = get_yolo_service()
        model_loaded = yolo_service.is_loaded

        if not model_loaded:
            print("\n⚠️ YOLO 模型未加载，跳过推理测试")
            return {
                "mean": float("nan"),
                "median": float("nan"),
                "min": float("nan"),
                "max": float("nan"),
                "stdev": 0.0,
                "iterations": 0,
                "target_ms": YOLO_TARGET_MS,
                "status": "skipped",
                "model_loaded": False,
                "fp16_used": False,
                "details": [],
                "note": "N/A (模型未加载)",
            }

        fp16_used = getattr(yolo_service, "_fp16_available", False)
        print(f"\n✅ YOLO 模型已加载 | FP16: {'启用' if fp16_used else '禁用'}")

        test_image = create_test_image(640, 640)
        print(f"   测试图像尺寸: {test_image.size}")

        for i in range(iterations):
            start = time.perf_counter()
            result = yolo_service.detect(test_image, use_cache=False)
            elapsed = time.perf_counter() - start
            elapsed_ms = elapsed * 1000

            inference_time = result.get("inference_time_ms", elapsed_ms)
            detection_count = result.get("count", 0)

            results.append(elapsed)
            details.append({
                "iteration": i + 1,
                "elapsed_s": round(elapsed, 4),
                "elapsed_ms": round(elapsed_ms, 2),
                "reported_inference_ms": inference_time,
                "detections": detection_count,
                "success": result.get("success", False),
            })
            print(f"  迭代 {i+1}/{iterations}: {elapsed_ms:.2f}ms (检测到 {detection_count} 个目标)")

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return {
            "mean": float("nan"),
            "median": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
            "stdev": 0.0,
            "iterations": 0,
            "target_ms": YOLO_TARGET_MS,
            "status": "skipped",
            "model_loaded": False,
            "fp16_used": False,
            "details": [],
            "note": f"N/A ({e})",
        }
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        return {
            "mean": float("nan"),
            "median": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
            "stdev": 0.0,
            "iterations": len(results),
            "target_ms": YOLO_TARGET_MS,
            "status": "error",
            "model_loaded": model_loaded,
            "fp16_used": fp16_used,
            "details": details,
            "error": str(e),
        }

    if not results:
        return {
            "mean": float("nan"),
            "median": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
            "stdev": 0.0,
            "iterations": 0,
            "target_ms": YOLO_TARGET_MS,
            "status": "skipped",
            "model_loaded": model_loaded,
            "fp16_used": fp16_used,
            "details": [],
        }

    mean_s = statistics.mean(results)
    median_s = statistics.median(results)
    mean_ms = mean_s * 1000
    status = "passed" if mean_ms < YOLO_TARGET_MS else "warning"

    print(f"\n{'='*60}")
    print(f"📈 结果汇总:")
    print(f"   平均值: {mean_ms:.2f}ms")
    print(f"   中位数: {median_s*1000:.2f}ms")
    print(f"   最小值: {min(results)*1000:.2f}ms")
    print(f"   最大值: {max(results)*1000:.2f}ms")
    print(f"   标准差: {(statistics.stdev(results) if len(results)>1 else 0)*1000:.2f}ms")
    print(f"   状态: {'✅ 达标' if status=='passed' else '⚠️ 未达标'} (目标 <{YOLO_TARGET_MS}ms)")
    print(f"{'='*60}\n")

    return {
        "mean": round(mean_s, 6),
        "median": round(median_s, 6),
        "min": round(min(results), 6),
        "max": round(max(results), 6),
        "stdev": round(statistics.stdev(results) if len(results) > 1 else 0, 6),
        "iterations": iterations,
        "target_ms": YOLO_TARGET_MS,
        "status": status,
        "model_loaded": model_loaded,
        "fp16_used": fp16_used,
        "details": details,
    }


if __name__ == "__main__":
    result = benchmark_yolo_inference()
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

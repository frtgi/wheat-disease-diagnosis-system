# -*- coding: utf-8 -*-
"""
性能基准测试：Qwen3-VL 推理延迟

测量 Qwen3-VL 多模态推理的响应时间，用于：
- 建立性能基线数据
- 对比优化前后效果
- 检测性能退化

区分两种场景:
- 首次推理: 包含模型加载时间（懒加载模式），目标 < 35s
- 后续推理: 模型已加载状态，目标 < 30s

使用 time.perf_counter() 高精度计时。
"""
import time
import statistics
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

QWEN_FIRST_TARGET_S = 35.0
QWEN_SUBSEQUENT_TARGET_S = 30.0


def create_test_image(width: int = 448, height: int = 448) -> Image.Image:
    """
    创建 Qwen 推理用的测试图像

    Args:
        width: 图像宽度（像素），默认 448 适配 Qwen 输入
        height: 图像高度（像素）

    Returns:
        Image.Image: RGB 模式的 PIL 图像对象
    """
    arr = np.random.randint(80, 180, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def get_test_prompt() -> str:
    """
    获取固定的测试 prompt 文本

    Returns:
        str: 小麦病害诊断相关的固定 prompt
    """
    return (
        "这是一张小麦叶片的图像，请分析图像中的病害症状，"
        "判断可能的病害类型，并给出简要的诊断结论。"
    )


def _run_single_qwen_inference(
    qwen_service: Any,
    test_image: Optional[Image.Image],
    prompt: str,
    enable_thinking: bool = False,
) -> tuple:
    """
    执行单次 Qwen 推理调用

    Args:
        qwen_service: QwenService 实例
        test_image: 测试图像（可选）
        prompt: 推理 prompt
        enable_thinking: 是否启用 Thinking 模式

    Returns:
        tuple: (elapsed_time, result_dict)
    """
    start = time.perf_counter()

    if qwen_service.is_lazy_load and not qwen_service.is_loaded:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, qwen_service.ensure_loaded())
                    future.result(timeout=120)
            else:
                loop.run_until_complete(qwen_service.ensure_loaded())
        except Exception:
            pass

    result = qwen_service.diagnose(
        image=test_image,
        symptoms=prompt,
        enable_thinking=enable_thinking,
        use_graph_rag=False,
    )

    elapsed = time.perf_counter() - start
    return elapsed, result


def benchmark_qwen_first_inference(iterations: int = 1) -> Dict[str, Any]:
    """
    执行 Qwen3-VL 首次推理基准测试（含模型加载时间）

    首次推理包含懒加载模式的模型加载开销，
    用于评估冷启动性能。

    Args:
        iterations: 迭代次数（首次推理通常只跑 1 次）

    Returns:
        Dict[str, Any]: 统计结果字典
    """
    print("=" * 60)
    print("📊 Qwen3-VL 首次推理延迟基准测试 (含懒加载)")
    print(f"   目标值: < {QWEN_FIRST_TARGET_S}s")
    print(f"   迭代次数: {iterations}")
    print("=" * 60)

    results = []
    details = []

    try:
        from app.services.qwen_service import QwenService, get_qwen_service

        test_image = create_test_image(448, 448)
        prompt = get_test_prompt()

        for i in range(iterations):
            print(f"\n  🔄 迭代 {i+1}/{iterations}: 初始化新服务实例...")

            try:
                qwen_service = get_qwen_service(lazy_load=True)
            except TypeError as e:
                if "lazy_load" in str(e):
                    print(f"   ℹ️ lazy_load 参数不受支持，使用默认初始化")
                    qwen_service = get_qwen_service()
                else:
                    raise

            was_loaded_before = qwen_service.is_loaded

            if was_loaded_before:
                print(f"   ℹ️ 模型已预加载，本次结果将标注为'非纯首次'")
            else:
                print(f"   ℹ️ 模型未加载，将触发懒加载")

            elapsed, result = _run_single_qwen_inference(
                qwen_service, test_image, prompt, enable_thinking=False
            )

            loaded_after = qwen_service.is_loaded
            success = result.get("success", False)

            results.append(elapsed)
            details.append({
                "iteration": i + 1,
                "elapsed_s": round(elapsed, 4),
                "was_loaded_before": was_loaded_before,
                "loaded_after": loaded_after,
                "success": success,
                "has_lazy_load_overhead": not was_loaded_before,
            })

            status_tag = "含懒加载" if not was_loaded_before else "已预热"
            print(f"  ✅ 耗时: {elapsed:.2f}s [{status_tag}] | 成功: {success}")

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return {
            "mean": float("nan"),
            "median": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
            "stdev": 0.0,
            "iterations": 0,
            "target_s": QWEN_FIRST_TARGET_S,
            "status": "skipped",
            "details": [],
            "note": f"N/A ({e})",
        }
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        return {
            "mean": statistics.mean(results) if results else float("nan"),
            "median": statistics.median(results) if results else float("nan"),
            "min": min(results) if results else float("nan"),
            "max": max(results) if results else float("nan"),
            "stdev": statistics.stdev(results) if len(results) > 1 else 0.0,
            "iterations": len(results),
            "target_s": QWEN_FIRST_TARGET_S,
            "status": "error",
            "details": details,
            "error": str(e),
        }

    if not results:
        return {
            "mean": float("nan"), "median": float("nan"), "min": float("nan"),
            "max": float("nan"), "stdev": 0.0, "iterations": 0,
            "target_s": QWEN_FIRST_TARGET_S, "status": "skipped", "details": [],
        }

    mean_s = statistics.mean(results)
    status = "passed" if mean_s < QWEN_FIRST_TARGET_S else "warning"

    print(f"\n{'='*60}")
    print(f"📈 首次推理结果汇总:")
    print(f"   平均值: {mean_s:.2f}s")
    print(f"   状态: {'✅ 达标' if status=='passed' else '⚠️ 未达标'} (目标 <{QWEN_FIRST_TARGET_S}s)")
    print(f"{'='*60}\n")

    return {
        "mean": round(mean_s, 4),
        "median": round(statistics.median(results), 4),
        "min": round(min(results), 4),
        "max": round(max(results), 4),
        "stdev": round(statistics.stdev(results) if len(results) > 1 else 0, 4),
        "iterations": iterations,
        "target_s": QWEN_FIRST_TARGET_S,
        "status": status,
        "details": details,
    }


def benchmark_qwen_subsequent_inference(iterations: int = 3) -> Dict[str, Any]:
    """
    执行 Qwen3-VL 后续推理基准测试（模型已加载状态）

    在模型已经加载到内存的情况下测量纯推理延迟，
    排除懒加载开销。

    Args:
        iterations: 推理迭代次数（默认 3 次）

    Returns:
        Dict[str, Any]: 统计结果字典
    """
    print("=" * 60)
    print("📊 Qwen3-VL 后续推理延迟基准测试 (模型已加载)")
    print(f"   目标值: < {QWEN_SUBSEQUENT_TARGET_S}s")
    print(f"   迭代次数: {iterations}")
    print("=" * 60)

    results = []
    details = []

    try:
        from app.services.qwen_service import get_qwen_service

        try:
            qwen_service = get_qwen_service(lazy_load=True)
        except TypeError as e:
            if "lazy_load" in str(e):
                print(f"   ℹ️ lazy_load 参数不受支持，使用默认初始化")
                qwen_service = get_qwen_service()
            else:
                raise

        if not qwen_service.is_loaded:
            print("\n⏳ 模型未加载，先执行一次预热加载...")
            preload_start = time.perf_counter()
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(qwen_service.ensure_loaded())
                loop.close()
            except Exception as e:
                print(f"   ⚠️ 预热加载失败: {e}")
                return {
                    "mean": float("nan"), "median": float("nan"), "min": float("nan"),
                    "max": float("nan"), "stdev": 0.0, "iterations": 0,
                    "target_s": QWEN_SUBSEQUENT_TARGET_S, "status": "skipped",
                    "details": [], "note": "N/A (模型加载失败)",
                }
            preload_elapsed = time.perf_counter() - preload_start
            print(f"   ✅ 预热加载完成，耗时 {preload_elapsed:.2f}s")

        test_image = create_test_image(448, 448)
        prompt = get_test_prompt()
        print(f"\n✅ 开始后续推理测试 (模型已加载)\n")

        for i in range(iterations):
            elapsed, result = _run_single_qwen_inference(
                qwen_service, test_image, prompt, enable_thinking=False
            )

            success = result.get("success", False)
            disease_name = ""
            if result.get("diagnosis"):
                disease_name = result["diagnosis"].get("disease_name", "")

            results.append(elapsed)
            details.append({
                "iteration": i + 1,
                "elapsed_s": round(elapsed, 4),
                "success": success,
                "disease_name": disease_name,
            })
            print(f"  迭代 {i+1}/{iterations}: {elapsed:.2f}s | 诊断: {disease_name or 'N/A'}")

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return {
            "mean": float("nan"), "median": float("nan"), "min": float("nan"),
            "max": float("nan"), "stdev": 0.0, "iterations": 0,
            "target_s": QWEN_SUBSEQUENT_TARGET_S, "status": "skipped",
            "details": [], "note": f"N/A ({e})",
        }
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        return {
            "mean": statistics.mean(results) if results else float("nan"),
            "median": statistics.median(results) if results else float("nan"),
            "min": min(results) if results else float("nan"),
            "max": max(results) if results else float("nan"),
            "stdev": statistics.stdev(results) if len(results) > 1 else 0.0,
            "iterations": len(results),
            "target_s": QWEN_SUBSEQUENT_TARGET_S,
            "status": "error",
            "details": details,
            "error": str(e),
        }

    if not results:
        return {
            "mean": float("nan"), "median": float("nan"), "min": float("nan"),
            "max": float("nan"), "stdev": 0.0, "iterations": 0,
            "target_s": QWEN_SUBSEQUENT_TARGET_S, "status": "skipped", "details": [],
        }

    mean_s = statistics.mean(results)
    status = "passed" if mean_s < QWEN_SUBSEQUENT_TARGET_S else "warning"

    print(f"\n{'='*60}")
    print(f"📈 后续推理结果汇总:")
    print(f"   平均值: {mean_s:.2f}s")
    print(f"   中位数: {statistics.median(results):.2f}s")
    print(f"   最小值: {min(results):.2f}s")
    print(f"   最大值: {max(results):.2f}s")
    print(f"   标准差: {(statistics.stdev(results) if len(results)>1 else 0):.2f}s")
    print(f"   状态: {'✅ 达标' if status=='passed' else '⚠️ 未达标'} (目标 <{QWEN_SUBSEQUENT_TARGET_S}s)")
    print(f"{'='*60}\n")

    return {
        "mean": round(mean_s, 4),
        "median": round(statistics.median(results), 4),
        "min": round(min(results), 4),
        "max": round(max(results), 4),
        "stdev": round(statistics.stdev(results) if len(results) > 1 else 0, 4),
        "iterations": iterations,
        "target_s": QWEN_SUBSEQUENT_TARGET_S,
        "status": status,
        "details": details,
    }


if __name__ == "__main__":
    import json

    print("\n" + "#" * 70)
    print("# Qwen3-VL 推理基准测试套件")
    print("#" * 70 + "\n")

    first_result = benchmark_qwen_first_inference(iterations=1)
    print(json.dumps(first_result, indent=2, ensure_ascii=False, default=str))

    subsequent_result = benchmark_qwen_subsequent_inference(iterations=3)
    print(json.dumps(subsequent_result, indent=2, ensure_ascii=False, default=str))

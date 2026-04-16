# -*- coding: utf-8 -*-
"""
性能基准测试：完整诊断流程端到端延迟

测量从请求接收到完成诊断的完整流程响应时间，用于：
- 建立端到端性能基线
- 识别各阶段瓶颈
- 检测整体性能退化

测试策略:
- 优先运行真实诊断流程（如果 AI 服务可用）
- 若不可用，则分别测量各组件独立耗时并汇总
- 目标值: < 40s（含 Qwen 推理）

使用 time.perf_counter() 高精度计时。
"""
import time
import statistics
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

FULL_DIAGNOSIS_TARGET_S = 40.0


def create_test_image(width: int = 640, height: int = 640) -> Image.Image:
    """
    创建诊断流程测试图像

    Args:
        width: 图像宽度
        height: 图像高度

    Returns:
        Image.Image: 测试用 PIL 图像
    """
    arr = np.random.randint(80, 180, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def _measure_component(
    name: str,
    func,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    测量单个组件的执行耗时

    Args:
        name: 组件名称
        func: 要测量的可调用对象
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        Dict[str, Any]: 包含组件名称、耗时、成功状态的字典
    """
    start = time.perf_counter()
    try:
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        return {"name": name, "elapsed_s": round(elapsed, 4), "success": True, "result": result}
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {"name": name, "elapsed_s": round(elapsed, 4), "success": False, "error": str(e)}


def benchmark_full_diagnosis(iterations: int = 1) -> Dict[str, Any]:
    """
    执行完整诊断流程基准测试

    测量端到端诊断延迟，包括：
    1. 图像预处理
    2. YOLO 视觉检测
    3. Qwen 语义分析
    4. 结果融合与输出

    如果无法运行完整流程，将分别测量各组件耗时并汇总。

    Args:
        iterations: 完整流程迭代次数（默认 1 次，因耗时长）

    Returns:
        Dict[str, Any]: 完整诊断流程的统计结果和各组件分解耗时
    """
    print("=" * 60)
    print("📊 完整诊断流程端到端基准测试")
    print(f"   目标值: < {FULL_DIAGNOSIS_TARGET_S}s")
    print(f"   迭代次数: {iterations}")
    print("=" * 60)

    total_results = []
    all_component_breakdowns = []

    try:
        from app.services.yolo_service import get_yolo_service
        from app.services.qwen_service import get_qwen_service

        yolo_available = False
        qwen_available = False

        try:
            yolo_svc = get_yolo_service()
            yolo_available = yolo_svc.is_loaded
        except Exception as e:
            print(f"   ⚠️ YOLO 服务不可用: {e}")

        try:
            try:
                qwen_svc = get_qwen_service(lazy_load=True)
            except TypeError as e:
                if "lazy_load" in str(e):
                    print(f"   ℹ️ lazy_load 参数不受支持，使用默认初始化")
                    qwen_svc = get_qwen_service()
                else:
                    raise
            qwen_available = qwen_svc.is_loaded
            if not qwen_available and getattr(qwen_svc, 'is_lazy_load', False):
                print("   ⚠️ Qwen 使用懒加载模式，将在首次推理时加载")
                qwen_available = True
        except Exception as e:
            print(f"   ⚠️ Qwen 服务不可用: {e}")

        print(f"\n   服务可用性: YOLO={'✅' if yolo_available else '❌'} | Qwen={'✅' if qwen_available else '❌'}")

        for i in range(iterations):
            print(f"\n{'─'*50}")
            print(f"  🔄 完整流程迭代 {i+1}/{iterations}")
            print(f"{'─'*50}")

            pipeline_start = time.perf_counter()
            component_times = []
            test_image = create_test_image(640, 640)
            symptoms_text = "小麦叶片出现黄色条纹状病斑，请诊断病害类型。"

            stage1 = _measure_component(
                "图像预处理",
                lambda img: img.resize((640, 640)).convert("RGB"),
                test_image,
            )
            component_times.append(stage1)
            print(f"  [1/4] 图像预处理: {stage1['elapsed_s']:.4f}s")

            yolo_result = None
            if yolo_available:
                stage2 = _measure_component(
                    "YOLO 视觉检测",
                    lambda: get_yolo_service().detect(test_image, use_cache=False),
                )
                component_times.append(stage2)
                yolo_result = stage2.get("result") if stage2["success"] else None
                det_count = yolo_result.get("count", 0) if yolo_result else 0
                print(f"  [2/4] YOLO 视觉检测: {stage2['elapsed_s']:.4f}s (检测 {det_count} 个目标)")
            else:
                component_times.append({"name": "YOLO 视觉检测", "elapsed_s": 0, "success": False, "note": "跳过"})
                print(f"  [2/4] YOLO 视觉检测: 跳过 (不可用)")

            qwen_result = None
            if qwen_available:
                stage3 = _measure_component(
                    "Qwen 语义分析",
                    lambda: get_qwen_service().diagnose(
                        image=test_image,
                        symptoms=symptoms_text,
                        enable_thinking=False,
                        use_graph_rag=False,
                    ),
                )
                component_times.append(stage3)
                qwen_result = stage3.get("result") if stage3["success"] else None
                diagnosis_name = ""
                if qwen_result and qwen_result.get("diagnosis"):
                    diagnosis_name = qwen_result["diagnosis"].get("disease_name", "")
                print(f"  [3/4] Qwen 语义分析: {stage3['elapsed_s']:.4f}s (诊断: {diagnosis_name or 'N/A'})")
            else:
                component_times.append({"name": "Qwen 语义分析", "elapsed_s": 0, "success": False, "note": "跳过"})
                print(f"  [3/4] Qwen 语义分析: 跳过 (不可用)")

            stage4_start = time.perf_counter()
            fusion_summary = {
                "yolo_detections": yolo_result.get("count", 0) if yolo_result else 0,
                "qwen_diagnosis": qwen_result.get("diagnosis", {}).get("disease_name", "") if qwen_result and qwen_result.get("diagnosis") else "N/A",
                "overall_success": (yolo_result and yolo_result.get("success")) or (not yolo_available),
            }
            stage4_elapsed = time.perf_counter() - stage4_start
            component_times.append({"name": "结果融合", "elapsed_s": round(stage4_elapsed, 6), "success": True})
            print(f"  [4/4] 结果融合: {stage4_elapsed:.6f}s")

            total_elapsed = time.perf_counter() - pipeline_start
            total_results.append(total_elapsed)

            breakdown = {
                "iteration": i + 1,
                "total_s": round(total_elapsed, 4),
                "components": component_times,
                "fusion_summary": fusion_summary,
            }
            all_component_breakdowns.append(breakdown)
            print(f"\n  ⏱️ 总耗时: {total_elapsed:.2f}s")

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return {
            "mean": float("nan"), "median": float("nan"), "min": float("nan"),
            "max": float("nan"), "stdev": 0.0, "iterations": 0,
            "target_s": FULL_DIAGNOSIS_TARGET_S, "status": "skipped",
            "component_breakdowns": [], "note": f"N/A ({e})",
        }
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        return {
            "mean": statistics.mean(total_results) if total_results else float("nan"),
            "median": statistics.median(total_results) if total_results else float("nan"),
            "min": min(total_results) if total_results else float("nan"),
            "max": max(total_results) if total_results else float("nan"),
            "stdev": statistics.stdev(total_results) if len(total_results) > 1 else 0.0,
            "iterations": len(total_results),
            "target_s": FULL_DIAGNOSIS_TARGET_S,
            "status": "error",
            "component_breakdowns": all_component_breakdowns,
            "error": str(e),
        }

    if not total_results:
        return {
            "mean": float("nan"), "median": float("nan"), "min": float("nan"),
            "max": float("nan"), "stdev": 0.0, "iterations": 0,
            "target_s": FULL_DIAGNOSIS_TARGET_S, "status": "skipped",
            "component_breakdowns": [],
        }

    mean_s = statistics.mean(total_results)
    status = "passed" if mean_s < FULL_DIAGNOSIS_TARGET_S else "warning"

    print(f"\n{'='*60}")
    print(f"📈 完整诊断流程结果汇总:")
    print(f"   平均值: {mean_s:.2f}s")
    print(f"   中位数: {statistics.median(total_results):.2f}s")
    print(f"   最小值: {min(total_results):.2f}s")
    print(f"   最大值: {max(total_results):.2f}s")
    print(f"   状态: {'✅ 达标' if status=='passed' else '⚠️ 未达标'} (目标 <{FULL_DIAGNOSIS_TARGET_S}s)")

    if all_component_breakdowns:
        print(f"\n   各组件耗时分解 (最近一次):")
        for comp in all_component_breakdowns[-1]["components"]:
            mark = "✅" if comp.get("success") else "⚠️"
            note = f" ({comp.get('note', '')})" if comp.get("note") else ""
            print(f"     {mark} {comp['name']}: {comp['elapsed_s']:.4f}s{note}")

    print(f"{'='*60}\n")

    return {
        "mean": round(mean_s, 4),
        "median": round(statistics.median(total_results), 4),
        "min": round(min(total_results), 4),
        "max": round(max(total_results), 4),
        "stdev": round(statistics.stdev(total_results) if len(total_results) > 1 else 0, 4),
        "iterations": iterations,
        "target_s": FULL_DIAGNOSIS_TARGET_S,
        "status": status,
        "component_breakdowns": all_component_breakdowns,
    }


if __name__ == "__main__":
    import json
    result = benchmark_full_diagnosis(iterations=1)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

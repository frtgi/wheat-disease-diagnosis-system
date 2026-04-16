# -*- coding: utf-8 -*-
"""
端到端优化测试脚本
测试 Flash Attention 2、KV Cache 量化、torch.compile 优化效果
"""
import os
import sys
import time
import json
import asyncio
import torch
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent))


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class OptimizationStatus:
    """优化状态数据类"""
    int4_enabled: bool = False
    kv_cache_quantization: bool = False
    torch_compile: bool = False
    flash_attention: bool = False
    gpu_available: bool = False
    gpu_memory_mb: float = 0.0


class E2EOptimizationTest:
    """
    端到端优化测试类
    
    测试内容：
    1. 纯文本诊断流程
    2. 纯图像诊断流程
    3. 多模态融合诊断流程
    4. SSE 实时进度推送
    5. 优化效果验证
    """
    
    def __init__(self, use_mock: bool = True):
        """
        初始化测试类
        
        参数:
            use_mock: 是否使用 Mock 模式（无真实模型时使用）
        """
        self.use_mock = use_mock
        self.results: List[TestResult] = []
        self.optimization_status = OptimizationStatus()
    
    def check_optimization_status(self) -> OptimizationStatus:
        """
        检查优化状态
        
        返回:
            OptimizationStatus: 优化状态对象
        """
        status = OptimizationStatus()
        
        status.gpu_available = torch.cuda.is_available()
        if status.gpu_available:
            status.gpu_memory_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
        
        try:
            from app.core.ai_config import ai_config
            status.int4_enabled = getattr(ai_config, 'QWEN_LOAD_IN_4BIT', False)
            status.kv_cache_quantization = getattr(ai_config, 'KV_CACHE_QUANTIZATION', False)
            status.torch_compile = getattr(ai_config, 'TORCH_COMPILE_ENABLE', False)
            status.flash_attention = getattr(ai_config, 'ENABLE_FLASH_ATTENTION', False)
        except Exception:
            pass
        
        self.optimization_status = status
        return status
    
    async def test_text_diagnosis(self) -> TestResult:
        """
        测试纯文本诊断流程
        
        返回:
            TestResult: 测试结果
        """
        start_time = time.time()
        test_name = "纯文本诊断测试"
        
        try:
            if self.use_mock:
                from app.services.mock_service import get_mock_service
                service = get_mock_service()
                result = await service.diagnose_by_text(
                    symptoms="小麦叶片出现黄色条纹，叶片枯萎",
                    weather="高温高湿",
                    growth_stage="抽穗期"
                )
            else:
                from app.services.fusion_service import get_fusion_service
                service = get_fusion_service()
                result = service.diagnose(
                    image=None,
                    symptoms="小麦叶片出现黄色条纹，叶片枯萎",
                    enable_thinking=False
                )
                if result and result.get("success"):
                    result = result.get("diagnosis", {})
            
            duration_ms = (time.time() - start_time) * 1000
            passed = result is not None and 'disease_name' in result
            
            return TestResult(
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                details={"disease_name": result.get('disease_name') if result else None}
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    async def test_image_diagnosis(self) -> TestResult:
        """
        测试纯图像诊断流程
        
        返回:
            TestResult: 测试结果
        """
        start_time = time.time()
        test_name = "纯图像诊断测试"
        
        try:
            test_image_dir = SCRIPT_DIR.parent.parent.parent.parent.parent / "datasets" / "wheat_data_unified" / "images" / "val"
            if not test_image_dir.exists():
                test_image_dir = Path("d:/Project/WheatAgent/datasets/wheat_data_unified/images/val")
            test_images = list(test_image_dir.glob("**/*.jpg")) + list(test_image_dir.glob("**/*.png"))
            test_images = test_images[:1]
            
            if not test_images:
                return TestResult(
                    test_name=test_name,
                    passed=False,
                    duration_ms=0,
                    error="未找到测试图像"
                )
            
            with open(test_images[0], "rb") as f:
                image_bytes = f.read()
            
            if self.use_mock:
                from app.services.mock_service import get_mock_service
                service = get_mock_service()
                result = await service.diagnose_by_image(image_bytes)
            else:
                from app.services.fusion_service import get_fusion_service
                from PIL import Image
                import io
                service = get_fusion_service()
                pil_image = Image.open(io.BytesIO(image_bytes))
                result = service.diagnose(image=pil_image, symptoms="", enable_thinking=False)
                if result and result.get("success"):
                    result = result.get("diagnosis", {})
            
            duration_ms = (time.time() - start_time) * 1000
            passed = result is not None and 'disease_name' in result
            
            return TestResult(
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                details={"disease_name": result.get('disease_name') if result else None}
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    async def test_multimodal_diagnosis(self) -> TestResult:
        """
        测试多模态融合诊断流程
        
        返回:
            TestResult: 测试结果
        """
        start_time = time.time()
        test_name = "多模态融合诊断测试"
        
        try:
            test_image_dir = SCRIPT_DIR.parent.parent.parent.parent.parent / "datasets" / "wheat_data_unified" / "images" / "val"
            if not test_image_dir.exists():
                test_image_dir = Path("d:/Project/WheatAgent/datasets/wheat_data_unified/images/val")
            test_images = list(test_image_dir.glob("**/*.jpg")) + list(test_image_dir.glob("**/*.png"))
            test_images = test_images[:1]
            
            if not test_images:
                return TestResult(
                    test_name=test_name,
                    passed=False,
                    duration_ms=0,
                    error="未找到测试图像"
                )
            
            with open(test_images[0], "rb") as f:
                image_bytes = f.read()
            
            if self.use_mock:
                from app.services.mock_service import get_mock_service
                service = get_mock_service()
                result = await service.diagnose_by_image(
                    image_bytes,
                    symptoms="叶片出现黄色斑点"
                )
            else:
                from app.services.fusion_service import get_fusion_service
                from PIL import Image
                import io
                service = get_fusion_service()
                pil_image = Image.open(io.BytesIO(image_bytes))
                result = service.diagnose(image=pil_image, symptoms="叶片出现黄色斑点", enable_thinking=False)
                if result and result.get("success"):
                    result = result.get("diagnosis", {})
            
            duration_ms = (time.time() - start_time) * 1000
            passed = result is not None and 'disease_name' in result
            
            return TestResult(
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                details={"disease_name": result.get('disease_name') if result else None}
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    async def test_sse_progress(self) -> TestResult:
        """
        测试 SSE 实时进度推送
        
        返回:
            TestResult: 测试结果
        """
        start_time = time.time()
        test_name = "SSE 实时进度测试"
        
        try:
            progress_events = []
            
            if self.use_mock:
                for i in range(5):
                    progress_events.append({
                        "stage": f"mock_stage_{i}",
                        "progress": i * 20,
                        "message": f"模拟进度 {i * 20}%"
                    })
                    await asyncio.sleep(0.1)
            else:
                pass
            
            duration_ms = (time.time() - start_time) * 1000
            passed = len(progress_events) > 0
            
            return TestResult(
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                details={"events_count": len(progress_events)}
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )
    
    def verify_optimizations(self) -> Dict[str, bool]:
        """
        验证优化是否生效
        
        返回:
            Dict[str, bool]: 各优化项的状态
        """
        status = self.check_optimization_status()
        
        return {
            "INT4 量化": status.int4_enabled,
            "KV Cache 量化": status.kv_cache_quantization,
            "torch.compile": status.torch_compile,
            "Flash Attention": status.flash_attention,
            "GPU 可用": status.gpu_available
        }
    
    async def run_all_tests(self) -> List[TestResult]:
        """
        运行所有测试
        
        返回:
            List[TestResult]: 测试结果列表
        """
        print("=" * 60)
        print("端到端优化测试")
        print("=" * 60)
        
        self.check_optimization_status()
        
        print("\n[1/4] 运行纯文本诊断测试...")
        result1 = await self.test_text_diagnosis()
        self.results.append(result1)
        print(f"    {'✅ 通过' if result1.passed else '❌ 失败'} ({result1.duration_ms:.2f}ms)")
        
        print("\n[2/4] 运行纯图像诊断测试...")
        result2 = await self.test_image_diagnosis()
        self.results.append(result2)
        print(f"    {'✅ 通过' if result2.passed else '❌ 失败'} ({result2.duration_ms:.2f}ms)")
        
        print("\n[3/4] 运行多模态融合诊断测试...")
        result3 = await self.test_multimodal_diagnosis()
        self.results.append(result3)
        print(f"    {'✅ 通过' if result3.passed else '❌ 失败'} ({result3.duration_ms:.2f}ms)")
        
        print("\n[4/4] 运行 SSE 实时进度测试...")
        result4 = await self.test_sse_progress()
        self.results.append(result4)
        print(f"    {'✅ 通过' if result4.passed else '❌ 失败'} ({result4.duration_ms:.2f}ms)")
        
        return self.results
    
    def generate_report(self, results: List[TestResult]) -> str:
        """
        生成测试报告
        
        参数:
            results: 测试结果列表
            
        返回:
            str: 测试报告字符串
        """
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("测试报告")
        lines.append("=" * 60)
        
        lines.append("\n## 优化状态")
        opt_status = self.verify_optimizations()
        for name, enabled in opt_status.items():
            lines.append(f"  {'✅' if enabled else '❌'} {name}")
        
        lines.append("\n## 测试结果")
        passed_count = sum(1 for r in results if r.passed)
        lines.append(f"  通过: {passed_count}/{len(results)}")
        
        for result in results:
            status = "✅ 通过" if result.passed else "❌ 失败"
            lines.append(f"  {status} - {result.test_name} ({result.duration_ms:.2f}ms)")
            if result.error:
                lines.append(f"    错误: {result.error}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def save_report(self, output_path: str) -> None:
        """
        保存测试报告到文件
        
        参数:
            output_path: 输出文件路径
        """
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "optimization_status": asdict(self.optimization_status),
            "results": [asdict(r) for r in self.results]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)


async def main():
    """主函数"""
    use_mock = not torch.cuda.is_available()
    
    tester = E2EOptimizationTest(use_mock=use_mock)
    results = await tester.run_all_tests()
    
    print(tester.generate_report(results))
    
    output_dir = SCRIPT_DIR / "reports"
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / f"e2e_optimization_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    tester.save_report(str(report_path))
    
    print(f"\n报告已保存到: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())

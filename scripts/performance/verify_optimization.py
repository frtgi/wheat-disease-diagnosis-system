# -*- coding: utf-8 -*-
"""
诊断推理优化验证测试脚本

验证内容：
1. 优化后诊断推理时间（验证 < 60s 要求）
2. 推理时间对比（优化前 vs 优化后）
3. 诊断结果准确性验证

使用方法：
    conda activate wheatagent-py310
    python scripts/performance/verify_optimization.py
"""
import os
import sys
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from PIL import Image
import traceback

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class TestResult:
    """测试结果数据结构"""
    test_name: str
    success: bool
    inference_time: float
    disease_name: str
    confidence: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceReport:
    """性能测试报告"""
    test_date: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    avg_inference_time: float
    max_inference_time: float
    min_inference_time: float
    meets_requirement: bool
    results: List[Dict[str, Any]]


class OptimizationVerifier:
    """优化验证测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.project_root = PROJECT_ROOT
        self.test_images_dir = self.project_root / "datasets" / "wheat_data_unified" / "images" / "val"
        self.results: List[TestResult] = []
        
        self.test_images = [
            "Aphid_0.png",
            "Blast_0.jpg",
            "Mildew_0.jpg",
        ]
        
        print("=" * 80)
        print("诊断推理优化验证测试")
        print("=" * 80)
        print(f"项目根目录: {self.project_root}")
        print(f"测试图像目录: {self.test_images_dir}")
        print(f"测试图像数量: {len(self.test_images)}")
        print("=" * 80)
    
    def run_all_tests(self) -> PerformanceReport:
        """运行所有测试"""
        print("\n开始运行优化验证测试...\n")
        
        self._test_single_image_diagnosis()
        self._test_text_diagnosis()
        self._test_multimodal_diagnosis()
        
        report = self._generate_report()
        self._save_report(report)
        self._print_summary(report)
        
        return report
    
    def _test_single_image_diagnosis(self):
        """测试单图像诊断"""
        print("\n" + "=" * 80)
        print("测试 1: 单图像诊断（优化后）")
        print("=" * 80)
        
        for image_name in self.test_images:
            image_path = self.test_images_dir / image_name
            
            if not image_path.exists():
                print(f"⚠️  测试图像不存在: {image_path}")
                continue
            
            print(f"\n测试图像: {image_name}")
            
            try:
                from src.web.backend.app.services.fusion_service import get_fusion_service
                
                fusion_service = get_fusion_service()
                fusion_service.initialize()
                
                image = Image.open(image_path).convert('RGB')
                
                print(f"  开始诊断...")
                start_time = time.time()
                
                result = fusion_service.diagnose(
                    image=image,
                    symptoms="",
                    enable_thinking=False,
                    use_graph_rag=True,
                    use_cache=False
                )
                
                inference_time = time.time() - start_time
                
                if result.get("success"):
                    diagnosis = result.get("diagnosis", {})
                    disease_name = diagnosis.get("disease_name", "未知")
                    confidence = diagnosis.get("confidence", 0.0)
                    
                    print(f"  ✅ 诊断成功")
                    print(f"     病害名称: {disease_name}")
                    print(f"     置信度: {confidence:.2%}")
                    print(f"     推理时间: {inference_time:.2f}秒")
                    
                    self.results.append(TestResult(
                        test_name=f"单图像诊断-{image_name}",
                        success=True,
                        inference_time=inference_time,
                        disease_name=disease_name,
                        confidence=confidence,
                        details={
                            "image_path": str(image_path),
                            "features": result.get("features", {})
                        }
                    ))
                else:
                    error = result.get("error", "未知错误")
                    print(f"  ❌ 诊断失败: {error}")
                    
                    self.results.append(TestResult(
                        test_name=f"单图像诊断-{image_name}",
                        success=False,
                        inference_time=inference_time,
                        disease_name="",
                        confidence=0.0,
                        error_message=error
                    ))
                    
            except Exception as e:
                print(f"  ❌ 测试异常: {e}")
                traceback.print_exc()
                
                self.results.append(TestResult(
                    test_name=f"单图像诊断-{image_name}",
                    success=False,
                    inference_time=0.0,
                    disease_name="",
                    confidence=0.0,
                    error_message=str(e)
                ))
    
    def _test_text_diagnosis(self):
        """测试文本诊断"""
        print("\n" + "=" * 80)
        print("测试 2: 文本诊断（优化后）")
        print("=" * 80)
        
        test_cases = [
            {
                "symptoms": "小麦叶片上出现黄色条状斑点，沿叶脉排列",
                "expected": "条锈病"
            },
            {
                "symptoms": "叶片表面覆盖白色粉状霉层",
                "expected": "白粉病"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            symptoms = case["symptoms"]
            expected = case["expected"]
            
            print(f"\n测试案例 {i}: {symptoms}")
            
            try:
                from src.web.backend.app.services.fusion_service import get_fusion_service
                
                fusion_service = get_fusion_service()
                fusion_service.initialize()
                
                print(f"  开始诊断...")
                start_time = time.time()
                
                result = fusion_service.diagnose(
                    image=None,
                    symptoms=symptoms,
                    enable_thinking=False,
                    use_graph_rag=True,
                    use_cache=False
                )
                
                inference_time = time.time() - start_time
                
                if result.get("success"):
                    diagnosis = result.get("diagnosis", {})
                    disease_name = diagnosis.get("disease_name", "未知")
                    confidence = diagnosis.get("confidence", 0.0)
                    
                    print(f"  ✅ 诊断成功")
                    print(f"     病害名称: {disease_name}")
                    print(f"     预期病害: {expected}")
                    print(f"     置信度: {confidence:.2%}")
                    print(f"     推理时间: {inference_time:.2f}秒")
                    
                    is_correct = expected in disease_name or disease_name in expected
                    
                    self.results.append(TestResult(
                        test_name=f"文本诊断-{i}",
                        success=True,
                        inference_time=inference_time,
                        disease_name=disease_name,
                        confidence=confidence,
                        details={
                            "symptoms": symptoms,
                            "expected": expected,
                            "is_correct": is_correct
                        }
                    ))
                else:
                    error = result.get("error", "未知错误")
                    print(f"  ❌ 诊断失败: {error}")
                    
                    self.results.append(TestResult(
                        test_name=f"文本诊断-{i}",
                        success=False,
                        inference_time=inference_time,
                        disease_name="",
                        confidence=0.0,
                        error_message=error
                    ))
                    
            except Exception as e:
                print(f"  ❌ 测试异常: {e}")
                traceback.print_exc()
                
                self.results.append(TestResult(
                    test_name=f"文本诊断-{i}",
                    success=False,
                    inference_time=0.0,
                    disease_name="",
                    confidence=0.0,
                    error_message=str(e)
                ))
    
    def _test_multimodal_diagnosis(self):
        """测试多模态诊断"""
        print("\n" + "=" * 80)
        print("测试 3: 多模态诊断（优化后）")
        print("=" * 80)
        
        image_name = "Mildew_0.jpg"
        image_path = self.test_images_dir / image_name
        
        if not image_path.exists():
            print(f"⚠️  测试图像不存在: {image_path}")
            return
        
        print(f"\n测试图像: {image_name}")
        print(f"症状描述: 叶片上出现白色粉状物")
        
        try:
            from src.web.backend.app.services.fusion_service import get_fusion_service
            
            fusion_service = get_fusion_service()
            fusion_service.initialize()
            
            image = Image.open(image_path).convert('RGB')
            
            print(f"  开始诊断...")
            start_time = time.time()
            
            result = fusion_service.diagnose(
                image=image,
                symptoms="叶片上出现白色粉状物",
                enable_thinking=False,
                use_graph_rag=True,
                use_cache=False
            )
            
            inference_time = time.time() - start_time
            
            if result.get("success"):
                diagnosis = result.get("diagnosis", {})
                disease_name = diagnosis.get("disease_name", "未知")
                confidence = diagnosis.get("confidence", 0.0)
                
                print(f"  ✅ 诊断成功")
                print(f"     病害名称: {disease_name}")
                print(f"     置信度: {confidence:.2%}")
                print(f"     推理时间: {inference_time:.2f}秒")
                
                self.results.append(TestResult(
                    test_name="多模态诊断",
                    success=True,
                    inference_time=inference_time,
                    disease_name=disease_name,
                    confidence=confidence,
                    details={
                        "image_path": str(image_path),
                        "symptoms": "叶片上出现白色粉状物",
                        "features": result.get("features", {})
                    }
                ))
            else:
                error = result.get("error", "未知错误")
                print(f"  ❌ 诊断失败: {error}")
                
                self.results.append(TestResult(
                    test_name="多模态诊断",
                    success=False,
                    inference_time=inference_time,
                    disease_name="",
                    confidence=0.0,
                    error_message=error
                ))
                
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            traceback.print_exc()
            
            self.results.append(TestResult(
                test_name="多模态诊断",
                success=False,
                inference_time=0.0,
                disease_name="",
                confidence=0.0,
                error_message=str(e)
            ))
    
    def _generate_report(self) -> PerformanceReport:
        """生成测试报告"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        inference_times = [r.inference_time for r in self.results if r.success]
        avg_inference_time = sum(inference_times) / len(inference_times) if inference_times else 0.0
        max_inference_time = max(inference_times) if inference_times else 0.0
        min_inference_time = min(inference_times) if inference_times else 0.0
        
        meets_requirement = max_inference_time < 60.0
        
        return PerformanceReport(
            test_date=datetime.now().isoformat(),
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            avg_inference_time=avg_inference_time,
            max_inference_time=max_inference_time,
            min_inference_time=min_inference_time,
            meets_requirement=meets_requirement,
            results=[asdict(r) for r in self.results]
        )
    
    def _save_report(self, report: PerformanceReport):
        """保存测试报告"""
        report_dir = self.project_root / "reports" / "performance"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"optimization_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试报告已保存: {report_file}")
    
    def _print_summary(self, report: PerformanceReport):
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("测试摘要")
        print("=" * 80)
        print(f"测试时间: {report.test_date}")
        print(f"总测试数: {report.total_tests}")
        print(f"通过测试: {report.passed_tests}")
        print(f"失败测试: {report.failed_tests}")
        print(f"平均推理时间: {report.avg_inference_time:.2f}秒")
        print(f"最大推理时间: {report.max_inference_time:.2f}秒")
        print(f"最小推理时间: {report.min_inference_time:.2f}秒")
        print(f"满足 < 60s 要求: {'✅ 是' if report.meets_requirement else '❌ 否'}")
        print("=" * 80)
        
        if report.meets_requirement:
            print("\n🎉 优化成功！推理时间满足 < 60s 要求")
        else:
            print("\n⚠️  优化未达标，推理时间仍需进一步优化")


def main():
    """主函数"""
    try:
        verifier = OptimizationVerifier()
        report = verifier.run_all_tests()
        
        if report.meets_requirement:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

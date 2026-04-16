# -*- coding: utf-8 -*-
"""
诊断推理性能测试脚本

测试内容：
1. 单次诊断推理时间（验证 < 60s 要求）
2. 高分辨率图像推理时间
3. 多轮对话推理时间

使用方法：
    conda activate wheatagent-py310
    python scripts/performance/diagnosis_inference_test.py
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

# 设置控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 sys.path
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
    meets_requirement: bool  # 是否满足 < 60s 要求
    results: List[Dict[str, Any]]


class DiagnosisPerformanceTester:
    """诊断推理性能测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.project_root = PROJECT_ROOT
        self.test_images_dir = self.project_root / "datasets" / "wheat_data_unified" / "images" / "val"
        self.results: List[TestResult] = []
        
        # 测试图像列表（不同病害类型）
        self.test_images = [
            "Aphid_0.png",
            "Blast_0.jpg",
            "Mite_0.png",
            "Mildew_0.jpg",
            "Smut_0.jpg"
        ]
        
        # 多轮对话测试场景
        self.multi_turn_scenarios = [
            {
                "round": 1,
                "symptoms": "小麦叶片上出现黄色条状斑点，沿叶脉排列",
                "expected_disease": "条锈病"
            },
            {
                "round": 2,
                "symptoms": "斑点逐渐扩大，形成孢子堆",
                "expected_disease": "条锈病"
            },
            {
                "round": 3,
                "symptoms": "请问如何防治？",
                "expected_disease": "条锈病"
            }
        ]
        
        print("=" * 60)
        print("[WheatAgent] 诊断推理性能测试")
        print("=" * 60)
        print(f"[INFO] 项目根目录: {self.project_root}")
        print(f"[INFO] 测试图像目录: {self.test_images_dir}")
        print(f"[INFO] 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def _get_test_image_path(self, image_name: str) -> Optional[Path]:
        """
        获取测试图像路径
        
        :param image_name: 图像文件名
        :return: 图像路径，不存在返回 None
        """
        image_path = self.test_images_dir / image_name
        if image_path.exists():
            return image_path
        
        # 尝试查找其他可用图像
        for ext in ['.jpg', '.png', '.jpeg']:
            alt_path = self.test_images_dir / image_name.replace('.png', ext).replace('.jpg', ext)
            if alt_path.exists():
                return alt_path
        
        return None
    
    def _create_high_resolution_image(self, base_image_path: Path, scale_factor: int = 2) -> Path:
        """
        创建高分辨率测试图像
        
        :param base_image_path: 基础图像路径
        :param scale_factor: 缩放因子
        :return: 高分辨率图像路径
        """
        output_dir = self.project_root / "test_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"high_res_{scale_factor}x_{base_image_path.name}"
        
        if output_path.exists():
            return output_path
        
        with Image.open(base_image_path) as img:
            new_size = (img.width * scale_factor, img.height * scale_factor)
            high_res_img = img.resize(new_size, Image.Resampling.LANCZOS)
            high_res_img.save(output_path)
        
        return output_path
    
    def _init_services(self):
        """
        初始化诊断服务
        
        :return: 诊断服务实例
        """
        print("\n[INIT] 初始化诊断服务...")
        
        try:
            # 添加 backend 目录到 sys.path
            backend_path = self.project_root / "src" / "web" / "backend"
            if str(backend_path) not in sys.path:
                sys.path.insert(0, str(backend_path))
            
            # 直接导入服务模块（避免 __init__.py 的循环导入）
            import importlib.util
            
            # 导入 YOLO 服务
            print("  - 初始化 YOLO 视觉引擎...")
            yolo_module_path = backend_path / "app" / "services" / "yolo_service.py"
            spec = importlib.util.spec_from_file_location("yolo_service", yolo_module_path)
            yolo_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(yolo_module)
            yolo_service = yolo_module.get_yolo_service()
            print("  [OK] YOLO 视觉引擎初始化完成")
            
            # 导入 Qwen 服务
            print("  - 初始化 Qwen 认知引擎...")
            qwen_module_path = backend_path / "app" / "services" / "qwen_service.py"
            spec = importlib.util.spec_from_file_location("qwen_service", qwen_module_path)
            qwen_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(qwen_module)
            qwen_service = qwen_module.get_qwen_service()
            print("  [OK] Qwen 认知引擎初始化完成")
            
            return yolo_service, qwen_service
            
        except Exception as e:
            print(f"  [ERROR] 服务初始化失败: {e}")
            traceback.print_exc()
            raise
    
    def test_single_diagnosis(self, yolo_service, qwen_service) -> TestResult:
        """
        测试单次诊断推理时间
        
        :param yolo_service: YOLO 服务实例
        :param qwen_service: Qwen 服务实例
        :return: 测试结果
        """
        print("\n" + "=" * 60)
        print("[TEST 1] 单次诊断推理时间")
        print("=" * 60)
        
        # 选择一个测试图像
        test_image_name = self.test_images[0]
        image_path = self._get_test_image_path(test_image_name)
        
        if not image_path:
            return TestResult(
                test_name="单次诊断推理",
                success=False,
                inference_time=0,
                disease_name="",
                confidence=0,
                error_message=f"测试图像不存在: {test_image_name}"
            )
        
        print(f"[IMAGE] 测试图像: {image_path.name}")
        
        try:
            # 加载图像
            image = Image.open(image_path).convert('RGB')
            print(f"   图像尺寸: {image.size}")
            
            # 开始计时
            start_time = time.time()
            
            # 步骤 1: YOLO 视觉检测
            print("\n[STEP 1] YOLO 视觉检测...")
            yolo_start = time.time()
            vision_result = yolo_service.detect(image)
            yolo_time = time.time() - yolo_start
            print(f"   [OK] YOLO 检测完成，耗时: {yolo_time:.2f}s")
            
            # 解析视觉检测结果
            disease_name = "未知病害"
            confidence = 0.0
            
            if vision_result.get('success') and vision_result.get('count', 0) > 0:
                detections = vision_result.get('detections', [])
                primary_detection = max(detections, key=lambda x: x.get('confidence', 0))
                disease_name = primary_detection.get('class_name', '未知病害')
                confidence = primary_detection.get('confidence', 0.0)
                print(f"   检测结果: {disease_name} (置信度: {confidence:.2%})")
            else:
                print("   [WARN] 未检测到病害目标")
            
            # 步骤 2: Qwen AI 增强分析
            print("\n[STEP 2] Qwen AI 增强分析...")
            qwen_start = time.time()
            ai_result = qwen_service.diagnose(
                image=image,
                symptoms=f"检测到{disease_name}" if disease_name != "未知病害" else "小麦病害",
                enable_thinking=False,
                use_graph_rag=True,
                disease_context=disease_name if disease_name != "未知病害" else None
            )
            qwen_time = time.time() - qwen_start
            print(f"   [OK] Qwen 分析完成，耗时: {qwen_time:.2f}s")
            
            # 解析 AI 结果
            if ai_result.get('success'):
                ai_diagnosis = ai_result.get('diagnosis', {})
                if ai_diagnosis.get('disease_name'):
                    disease_name = ai_diagnosis['disease_name']
                if ai_diagnosis.get('confidence'):
                    confidence = max(confidence, ai_diagnosis['confidence'])
                print(f"   AI 诊断: {disease_name} (置信度: {confidence:.2%})")
            
            # 结束计时
            total_time = time.time() - start_time
            
            # 判断是否满足要求
            meets_requirement = total_time < 60
            status = "[PASS]" if meets_requirement else "[FAIL]"
            
            print(f"\n[TIME] 总推理时间: {total_time:.2f}s")
            print(f"[REQ] 性能要求: < 60s")
            print(f"[RESULT] 测试结果: {status}")
            
            return TestResult(
                test_name="单次诊断推理",
                success=True,
                inference_time=total_time,
                disease_name=disease_name,
                confidence=confidence,
                details={
                    "yolo_time": yolo_time,
                    "qwen_time": qwen_time,
                    "meets_requirement": meets_requirement,
                    "image_size": image.size,
                    "image_name": image_path.name
                }
            )
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n[ERROR] 测试失败: {error_msg}")
            traceback.print_exc()
            
            return TestResult(
                test_name="单次诊断推理",
                success=False,
                inference_time=0,
                disease_name="",
                confidence=0,
                error_message=error_msg
            )
    
    def test_high_resolution_images(self, yolo_service, qwen_service) -> List[TestResult]:
        """
        测试高分辨率图像推理时间
        
        :param yolo_service: YOLO 服务实例
        :param qwen_service: Qwen 服务实例
        :return: 测试结果列表
        """
        print("\n" + "=" * 60)
        print("[TEST 2] 高分辨率图像推理时间")
        print("=" * 60)
        
        results = []
        
        # 测试不同分辨率
        resolution_configs = [
            {"name": "原始分辨率", "scale": 1},
            {"name": "2倍分辨率", "scale": 2},
            {"name": "4倍分辨率", "scale": 4}
        ]
        
        # 选择基础图像
        base_image_name = self.test_images[0]
        base_image_path = self._get_test_image_path(base_image_name)
        
        if not base_image_path:
            print(f"[ERROR] 基础图像不存在: {base_image_name}")
            return [TestResult(
                test_name="高分辨率图像推理",
                success=False,
                inference_time=0,
                disease_name="",
                confidence=0,
                error_message=f"基础图像不存在: {base_image_name}"
            )]
        
        for config in resolution_configs:
            print(f"\n[IMAGE] 测试分辨率: {config['name']}")
            
            try:
                # 准备测试图像
                if config['scale'] == 1:
                    image_path = base_image_path
                else:
                    image_path = self._create_high_resolution_image(base_image_path, config['scale'])
                
                # 加载图像
                image = Image.open(image_path).convert('RGB')
                print(f"   图像尺寸: {image.size}")
                
                # 开始计时
                start_time = time.time()
                
                # YOLO 检测
                vision_result = yolo_service.detect(image)
                
                # Qwen 分析
                disease_name = "未知病害"
                confidence = 0.0
                
                if vision_result.get('success') and vision_result.get('count', 0) > 0:
                    detections = vision_result.get('detections', [])
                    primary_detection = max(detections, key=lambda x: x.get('confidence', 0))
                    disease_name = primary_detection.get('class_name', '未知病害')
                    confidence = primary_detection.get('confidence', 0.0)
                
                ai_result = qwen_service.diagnose(
                    image=image,
                    symptoms=f"检测到{disease_name}",
                    enable_thinking=False,
                    use_graph_rag=True,
                    disease_context=disease_name
                )
                
                if ai_result.get('success'):
                    ai_diagnosis = ai_result.get('diagnosis', {})
                    if ai_diagnosis.get('disease_name'):
                        disease_name = ai_diagnosis['disease_name']
                    if ai_diagnosis.get('confidence'):
                        confidence = max(confidence, ai_diagnosis['confidence'])
                
                # 结束计时
                total_time = time.time() - start_time
                
                print(f"   [TIME] 推理时间: {total_time:.2f}s")
                print(f"   [RESULT] 诊断结果: {disease_name} (置信度: {confidence:.2%})")
                
                results.append(TestResult(
                    test_name=f"高分辨率图像推理 ({config['name']})",
                    success=True,
                    inference_time=total_time,
                    disease_name=disease_name,
                    confidence=confidence,
                    details={
                        "resolution": config['name'],
                        "scale_factor": config['scale'],
                        "image_size": image.size
                    }
                ))
                
            except Exception as e:
                error_msg = str(e)
                print(f"   [ERROR] 测试失败: {error_msg}")
                
                results.append(TestResult(
                    test_name=f"高分辨率图像推理 ({config['name']})",
                    success=False,
                    inference_time=0,
                    disease_name="",
                    confidence=0,
                    error_message=error_msg
                ))
        
        return results
    
    def test_multi_turn_dialog(self, qwen_service) -> TestResult:
        """
        测试多轮对话推理时间
        
        :param qwen_service: Qwen 服务实例
        :return: 测试结果
        """
        print("\n" + "=" * 60)
        print("[TEST 3] 多轮对话推理时间")
        print("=" * 60)
        
        total_time = 0
        round_times = []
        round_results = []
        
        try:
            for scenario in self.multi_turn_scenarios:
                print(f"\n[ROUND {scenario['round']}] 对话")
                print(f"   症状描述: {scenario['symptoms']}")
                
                # 开始计时
                start_time = time.time()
                
                # 执行诊断
                result = qwen_service.diagnose(
                    image=None,
                    symptoms=scenario['symptoms'],
                    enable_thinking=False,
                    use_graph_rag=True,
                    disease_context=scenario['expected_disease']
                )
                
                # 结束计时
                round_time = time.time() - start_time
                total_time += round_time
                round_times.append(round_time)
                
                if result.get('success'):
                    ai_diagnosis = result.get('diagnosis', {})
                    disease_name = ai_diagnosis.get('disease_name', '未知')
                    confidence = ai_diagnosis.get('confidence', 0)
                    
                    print(f"   [OK] 诊断完成，耗时: {round_time:.2f}s")
                    print(f"   [RESULT] 诊断结果: {disease_name} (置信度: {confidence:.2%})")
                    
                    round_results.append({
                        "round": scenario['round'],
                        "inference_time": round_time,
                        "disease_name": disease_name,
                        "confidence": confidence
                    })
                else:
                    print(f"   [ERROR] 诊断失败")
                    round_results.append({
                        "round": scenario['round'],
                        "inference_time": round_time,
                        "disease_name": "未知",
                        "confidence": 0
                    })
            
            # 计算平均时间
            avg_time = total_time / len(self.multi_turn_scenarios)
            
            print(f"\n[SUMMARY] 多轮对话测试汇总:")
            print(f"   总轮数: {len(self.multi_turn_scenarios)}")
            print(f"   总时间: {total_time:.2f}s")
            print(f"   平均每轮: {avg_time:.2f}s")
            print(f"   最快轮次: {min(round_times):.2f}s")
            print(f"   最慢轮次: {max(round_times):.2f}s")
            
            return TestResult(
                test_name="多轮对话推理",
                success=True,
                inference_time=avg_time,
                disease_name=round_results[-1]['disease_name'] if round_results else "未知",
                confidence=round_results[-1]['confidence'] if round_results else 0,
                details={
                    "total_rounds": len(self.multi_turn_scenarios),
                    "total_time": total_time,
                    "round_times": round_times,
                    "round_results": round_results
                }
            )
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n[ERROR] 测试失败: {error_msg}")
            traceback.print_exc()
            
            return TestResult(
                test_name="多轮对话推理",
                success=False,
                inference_time=0,
                disease_name="",
                confidence=0,
                error_message=error_msg
            )
    
    def run_all_tests(self) -> PerformanceReport:
        """
        运行所有性能测试
        
        :return: 性能测试报告
        """
        print("\n" + "=" * 60)
        print("[START] 开始运行所有性能测试")
        print("=" * 60)
        
        # 初始化服务
        yolo_service, qwen_service = self._init_services()
        
        # 测试 1: 单次诊断推理
        result1 = self.test_single_diagnosis(yolo_service, qwen_service)
        self.results.append(result1)
        
        # 测试 2: 高分辨率图像推理
        results2 = self.test_high_resolution_images(yolo_service, qwen_service)
        self.results.extend(results2)
        
        # 测试 3: 多轮对话推理
        result3 = self.test_multi_turn_dialog(qwen_service)
        self.results.append(result3)
        
        # 生成报告
        return self._generate_report()
    
    def _generate_report(self) -> PerformanceReport:
        """
        生成性能测试报告
        
        :return: 性能测试报告
        """
        print("\n" + "=" * 60)
        print("[REPORT] 生成性能测试报告")
        print("=" * 60)
        
        # 统计结果
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        # 计算时间统计
        successful_results = [r for r in self.results if r.success]
        
        if successful_results:
            inference_times = [r.inference_time for r in successful_results]
            avg_time = sum(inference_times) / len(inference_times)
            max_time = max(inference_times)
            min_time = min(inference_times)
        else:
            avg_time = 0
            max_time = 0
            min_time = 0
        
        # 判断是否满足 < 60s 要求
        meets_requirement = all(r.inference_time < 60 for r in successful_results)
        
        # 创建报告
        report = PerformanceReport(
            test_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            avg_inference_time=avg_time,
            max_inference_time=max_time,
            min_inference_time=min_time,
            meets_requirement=meets_requirement,
            results=[asdict(r) for r in self.results]
        )
        
        # 打印报告摘要
        print(f"\n[SUMMARY] 测试报告摘要:")
        print(f"   测试时间: {report.test_date}")
        print(f"   总测试数: {report.total_tests}")
        print(f"   通过数: {report.passed_tests}")
        print(f"   失败数: {report.failed_tests}")
        print(f"   平均推理时间: {report.avg_inference_time:.2f}s")
        print(f"   最大推理时间: {report.max_inference_time:.2f}s")
        print(f"   最小推理时间: {report.min_inference_time:.2f}s")
        print(f"   满足 < 60s 要求: {'[YES]' if report.meets_requirement else '[NO]'}")
        
        # 保存报告
        self._save_report(report)
        
        return report
    
    def _save_report(self, report: PerformanceReport):
        """
        保存测试报告到文件
        
        :param report: 性能测试报告
        """
        output_dir = self.project_root / "test_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = output_dir / f"diagnosis_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)
        
        print(f"\n[SAVED] 报告已保存: {report_path}")


def main():
    """主函数"""
    try:
        tester = DiagnosisPerformanceTester()
        report = tester.run_all_tests()
        
        print("\n" + "=" * 60)
        print("[DONE] 性能测试完成")
        print("=" * 60)
        
        # 返回退出码
        return 0 if report.meets_requirement else 1
        
    except Exception as e:
        print(f"\n[ERROR] 测试执行失败: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

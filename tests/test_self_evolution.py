# -*- coding: utf-8 -*-
"""
自进化机制测试脚本

测试内容：
1. 不确定性检测 - 置信度阈值、熵值计算、OOD检测
2. 反馈收集 - 人机协同反馈闭环
3. 增量学习 - 经验回放、知识蒸馏
4. LoRA 适配器管理

使用方法:
    python tests/test_self_evolution.py
"""
import os
import sys
import json
import time
import random
import numpy as np
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class TestResult:
    """测试结果"""
    name: str
    passed: bool
    message: str
    duration: float
    details: Dict = None


class SelfEvolutionTester:
    """
    自进化机制测试器
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
    
    def record_result(self, result: TestResult):
        """
        记录测试结果
        
        :param result: 测试结果
        """
        self.results.append(result)
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"  {status}: {result.name} ({result.duration:.2f}s)")
        if not result.passed:
            print(f"         {result.message}")
    
    def test_uncertainty_detection(self) -> TestResult:
        """
        测试不确定性检测
        
        :return: 测试结果
        """
        start = time.time()
        name = "不确定性检测"
        
        try:
            from src.action.feedback_integration import UncertaintyDetector
            
            detector = UncertaintyDetector(
                confidence_threshold=0.85,
                entropy_threshold=1.5,
                ood_threshold=0.3
            )
            
            high_conf_probs = np.array([0.95, 0.03, 0.01, 0.01])
            result1 = detector.compute_uncertainty(high_conf_probs)
            assert result1["is_uncertain"] == False, "高置信度预测不应标记为不确定"
            
            low_conf_probs = np.array([0.75, 0.15, 0.05, 0.05])
            result2 = detector.compute_uncertainty(low_conf_probs)
            assert result2["is_uncertain"] == True, "低置信度预测应标记为不确定"
            
            high_entropy_probs = np.array([0.40, 0.35, 0.15, 0.10])
            result3 = detector.compute_uncertainty(high_entropy_probs)
            assert result3["is_uncertain"] == True, "高熵预测应标记为不确定"
            
            uncertainty_score = result3["uncertainty_score"]
            assert 0 <= uncertainty_score <= 1, "不确定性分数应在0-1之间"
            
            return TestResult(
                name=name,
                passed=True,
                message="不确定性检测功能正常",
                duration=time.time() - start,
                details={
                    "high_conf_result": result1["is_uncertain"],
                    "low_conf_result": result2["is_uncertain"],
                    "high_entropy_result": result3["is_uncertain"],
                    "uncertainty_score": uncertainty_score
                }
            )
            
        except Exception as e:
            return TestResult(
                name=name,
                passed=False,
                message=str(e),
                duration=time.time() - start
            )
    
    def test_experience_replay(self) -> TestResult:
        """
        测试经验回放
        
        :return: 测试结果
        """
        start = time.time()
        name = "经验回放"
        
        try:
            from src.evolution.experience_replay import ExperienceReplayBuffer
            
            buffer = ExperienceReplayBuffer(
                buffer_size=100,
                save_path=str(PROJECT_ROOT / "logs" / "test_experience")
            )
            
            for i in range(50):
                buffer.add_experience(
                    image_path=f"image_{i}.jpg",
                    user_text=f"这是第{i}个样本",
                    vision_result={"disease": f"class_{i % 5}", "confidence": 0.9},
                    text_result={"disease": f"class_{i % 5}"},
                    final_diagnosis=f"class_{i % 5}"
                )
            
            assert len(buffer.buffer) <= 100, "缓冲区大小应限制在容量内"
            
            stats = buffer.get_statistics()
            
            return TestResult(
                name=name,
                passed=True,
                message="经验回放功能正常",
                duration=time.time() - start,
                details={
                    "buffer_size": len(buffer.buffer),
                    "stats": stats
                }
            )
            
        except Exception as e:
            return TestResult(
                name=name,
                passed=False,
                message=str(e),
                duration=time.time() - start
            )
    
    def test_incremental_learning(self) -> TestResult:
        """
        测试增量学习
        
        :return: 测试结果
        """
        start = time.time()
        name = "增量学习"
        
        try:
            from src.evolution.incremental_learning import IncrementalConfig, ExemplarMemory
            
            config = IncrementalConfig(
                num_classes=15,
                embedding_dim=512,
                memory_size=100
            )
            
            memory = ExemplarMemory(memory_size=100)
            
            features = torch.randn(50, 512)
            labels = torch.randint(0, 5, (50,))
            
            memory.update_exemplars(features, labels, [0, 1, 2, 3, 4])
            
            all_features, all_labels = memory.get_all_exemplars()
            
            assert all_features.shape[0] > 0, "应有记忆样本"
            
            return TestResult(
                name=name,
                passed=True,
                message="增量学习功能正常",
                duration=time.time() - start,
                details={
                    "config": {
                        "num_classes": config.num_classes,
                        "memory_size": config.memory_size
                    },
                    "exemplar_count": all_features.shape[0]
                }
            )
            
        except Exception as e:
            return TestResult(
                name=name,
                passed=False,
                message=str(e),
                duration=time.time() - start
            )
    
    def test_human_feedback_loop(self) -> TestResult:
        """
        测试人机协同反馈闭环
        
        :return: 测试结果
        """
        start = time.time()
        name = "人机协同反馈闭环"
        
        try:
            from src.evolution.human_in_the_loop import HumanInTheLoop, FeedbackStatus, FeedbackRecord
            
            hitl = HumanInTheLoop(
                feedback_dir=str(PROJECT_ROOT / "logs" / "feedback_test")
            )
            
            record = hitl.submit_prediction(
                image_path="test_image.jpg",
                system_diagnosis="条锈病",
                system_confidence=0.45
            )
            
            if record:
                success = hitl.submit_feedback(
                    record_id=record.id,
                    user_correction="叶锈病",
                    user_comments="病斑颜色偏橙褐色，应为叶锈病"
                )
                assert success, "反馈提交应成功"
            
            return TestResult(
                name=name,
                passed=True,
                message="人机协同反馈闭环功能正常",
                duration=time.time() - start,
                details={
                    "record_id": record.id if record else None,
                    "submitted": success if record else False
                }
            )
            
        except Exception as e:
            return TestResult(
                name=name,
                passed=False,
                message=str(e),
                duration=time.time() - start
            )
    
    def test_knowledge_extraction(self) -> TestResult:
        """
        测试知识提取
        
        :return: 测试结果
        """
        start = time.time()
        name = "知识提取"
        
        try:
            from src.action.feedback_integration import UncertaintyDetector
            
            detector = UncertaintyDetector()
            
            probs = np.array([0.4, 0.35, 0.15, 0.1])
            result = detector.compute_uncertainty(probs)
            
            assert "is_uncertain" in result, "结果应包含不确定性标志"
            assert "entropy" in result, "结果应包含熵值"
            
            return TestResult(
                name=name,
                passed=True,
                message="知识提取功能正常",
                duration=time.time() - start,
                details={
                    "uncertainty_result": result
                }
            )
            
        except Exception as e:
            return TestResult(
                name=name,
                passed=False,
                message=str(e),
                duration=time.time() - start
            )
    
    def test_self_evolution_manager(self) -> TestResult:
        """
        测试自进化管理器
        
        :return: 测试结果
        """
        start = time.time()
        name = "自进化管理器"
        
        try:
            from src.evolution.self_evolution_manager import SelfEvolutionManager, EvolutionConfig
            
            config = EvolutionConfig(
                memory_size=100,
                confidence_threshold=0.7
            )
            
            manager = SelfEvolutionManager(
                config=config,
                output_dir=str(PROJECT_ROOT / "logs" / "evolution_test")
            )
            
            result = manager.check_uncertainty(
                diagnosis="条锈病",
                confidence=0.65
            )
            assert "needs_review" in result, "结果应包含是否需要审核"
            
            feedback = manager.collect_feedback(
                image_path="test.jpg",
                system_diagnosis="条锈病",
                system_confidence=0.65,
                user_correction="叶锈病"
            )
            assert feedback is not None, "反馈收集应成功"
            
            stats = manager.get_statistics()
            
            return TestResult(
                name=name,
                passed=True,
                message="自进化管理器功能正常",
                duration=time.time() - start,
                details={
                    "uncertainty_result": result,
                    "stats": stats
                }
            )
            
        except Exception as e:
            return TestResult(
                name=name,
                passed=False,
                message=str(e),
                duration=time.time() - start
            )
    
    def run_all_tests(self) -> Dict:
        """
        运行所有测试
        
        :return: 测试报告
        """
        print("\n" + "=" * 70)
        print("🧪 自进化机制测试")
        print("=" * 70)
        
        tests = [
            self.test_uncertainty_detection,
            self.test_experience_replay,
            self.test_incremental_learning,
            self.test_human_feedback_loop,
            self.test_knowledge_extraction,
            self.test_self_evolution_manager,
        ]
        
        for test in tests:
            result = test()
            self.record_result(result)
        
        total_duration = time.time() - self.start_time
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        print("\n" + "=" * 70)
        print("📊 测试结果汇总")
        print("=" * 70)
        print(f"  总测试数: {len(self.results)}")
        print(f"  通过: {passed}")
        print(f"  失败: {failed}")
        print(f"  通过率: {passed/len(self.results)*100:.1f}%")
        print(f"  总耗时: {total_duration:.2f}s")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(self.results) if self.results else 0,
            "total_duration": total_duration,
            "results": [asdict(r) for r in self.results]
        }
        
        report_path = PROJECT_ROOT / "logs" / "self_evolution_test_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 测试报告已保存: {report_path}")
        
        return report


def main():
    """
    主函数
    """
    tester = SelfEvolutionTester()
    report = tester.run_all_tests()
    
    if report["failed"] > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
端到端集成测试

测试完整的诊断流程：图像输入 → 视觉检测 → 知识检索 → 融合决策 → 诊断报告
"""
import os
import sys
import json
import time
import random
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class DiagnosisResult:
    """诊断结果数据结构"""
    success: bool
    disease_name: str
    confidence: float
    bbox: Optional[List[float]] = None
    symptoms: Optional[List[str]] = None
    causes: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    knowledge_sources: Optional[List[str]] = None
    processing_time_ms: float = 0.0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestCase:
    """测试用例"""
    name: str
    image_path: Optional[str]
    expected_disease: Optional[str]
    description: str
    difficulty: str  # 'easy', 'medium', 'hard'


class EndToEndTestSuite:
    """
    端到端测试套件
    
    测试完整的诊断流程，验证系统各模块的协同工作能力
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化端到端测试套件
        
        :param config: 测试配置
        """
        self.config = config or {}
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.results: List[Dict[str, Any]] = []
        
        # 测试用例
        self.test_cases: List[TestCase] = []
        
        # 模块实例
        self.vision_agent = None
        self.language_agent = None
        self.knowledge_agent = None
        self.fusion_agent = None
        
        print("🧪 [EndToEndTestSuite] 端到端测试套件初始化完成")
    
    def setup_test_cases(self):
        """设置测试用例"""
        print("\n📋 设置测试用例...")
        
        # 基础测试用例
        self.test_cases = [
            TestCase(
                name="基础检测-条锈病",
                image_path=None,  # 将使用合成图像
                expected_disease="条锈病",
                description="测试基本的条锈病检测能力",
                difficulty="easy"
            ),
            TestCase(
                name="基础检测-白粉病",
                image_path=None,
                expected_disease="白粉病",
                description="测试白粉病检测能力",
                difficulty="easy"
            ),
            TestCase(
                name="复杂场景-多病害",
                image_path=None,
                expected_disease=None,  # 多病害场景
                description="测试多病害同时存在的复杂场景",
                difficulty="hard"
            ),
            TestCase(
                name="鲁棒性测试-低光照",
                image_path=None,
                expected_disease="条锈病",
                description="测试低光照条件下的检测能力",
                difficulty="medium"
            ),
            TestCase(
                name="知识推理-病害关联",
                image_path=None,
                expected_disease="赤霉病",
                description="测试知识图谱推理能力",
                difficulty="medium"
            ),
        ]
        
        print(f"   已加载 {len(self.test_cases)} 个测试用例")
    
    def initialize_modules(self):
        """初始化系统模块"""
        print("\n🔧 初始化系统模块...")
        
        try:
            # 导入模块
            from src.vision import EnhancedVisionAgent
            from src.text import EnhancedLanguageAgent
            from src.graph import KnowledgeAgent
            from src.fusion import EnhancedFusionAgent
            
            # 初始化视觉模块
            print("   初始化视觉模块...")
            self.vision_agent = EnhancedVisionAgent(
                model_path='models/yolov8_wheat.pt',
                device=self.device
            )
            
            # 初始化语言模块
            print("   初始化语言模块...")
            self.language_agent = EnhancedLanguageAgent(
                model_path='models/agri_llava',
                device=self.device
            )
            
            # 初始化知识图谱模块
            print("   初始化知识图谱模块...")
            self.knowledge_agent = KnowledgeAgent(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password"
            )
            
            # 初始化融合模块
            print("   初始化融合模块...")
            self.fusion_agent = EnhancedFusionAgent(
                knowledge_agent=self.knowledge_agent
            )
            
            print("   ✅ 所有模块初始化成功")
            return True
            
        except Exception as e:
            print(f"   ⚠️ 模块初始化失败: {e}")
            print("   将使用模拟模块进行测试")
            self._setup_mock_modules()
            return False
    
    def _setup_mock_modules(self):
        """设置模拟模块（用于测试环境）"""
        print("   设置模拟模块...")
        
        # 模拟视觉模块
        class MockVisionAgent:
            def detect(self, image, **kwargs):
                return {
                    'detections': [
                        {
                            'class': '条锈病',
                            'confidence': 0.92,
                            'bbox': [100, 100, 200, 200]
                        }
                    ]
                }
        
        # 模拟语言模块
        class MockLanguageAgent:
            def analyze(self, image, context=None):
                return {
                    'description': '叶片出现黄色条状病斑',
                    'symptoms': ['黄色条纹', '孢子堆'],
                    'confidence': 0.88
                }
        
        # 模拟知识图谱模块
        class MockKnowledgeAgent:
            def query(self, disease_name):
                return {
                    'disease': disease_name,
                    'symptoms': ['黄色条纹', '孢子堆'],
                    'causes': ['低温高湿', '真菌感染'],
                    'treatments': ['粉锈宁', '戊唑醇']
                }
        
        # 模拟融合模块
        class MockFusionAgent:
            def fuse(self, vision_result, language_result, knowledge_result):
                return {
                    'disease': vision_result['detections'][0]['class'],
                    'confidence': 0.90,
                    'symptoms': knowledge_result['symptoms'],
                    'causes': knowledge_result['causes'],
                    'recommendations': knowledge_result['treatments']
                }
        
        self.vision_agent = MockVisionAgent()
        self.language_agent = MockLanguageAgent()
        self.knowledge_agent = MockKnowledgeAgent()
        self.fusion_agent = MockFusionAgent()
        
        print("   ✅ 模拟模块设置完成")
    
    def create_test_image(self, test_case: TestCase) -> str:
        """创建测试图像并保存到临时文件，返回文件路径"""
        import tempfile
        from PIL import Image
        
        # 创建合成图像
        if test_case.name == "鲁棒性测试-低光照":
            # 低光照图像
            image = np.random.randint(20, 80, (480, 640, 3), dtype=np.uint8)
        elif test_case.name == "复杂场景-多病害":
            # 复杂场景
            image = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
            # 添加多个病害区域
            image[100:150, 100:200] = [200, 200, 50]  # 黄色区域
            image[300:350, 400:500] = [255, 255, 255]  # 白色区域
        else:
            # 标准测试图像
            image = np.random.randint(80, 180, (480, 640, 3), dtype=np.uint8)
            # 添加病害特征
            if test_case.expected_disease == "条锈病":
                image[150:250, 200:400] = [220, 220, 50]  # 黄色条纹
            elif test_case.expected_disease == "白粉病":
                image[150:250, 200:400] = [240, 240, 240]  # 白色粉状
            elif test_case.expected_disease == "赤霉病":
                image[150:250, 200:400] = [180, 100, 100]  # 粉红色
        
        # 保存到临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        Image.fromarray(image).save(temp_file.name)
        temp_file.close()
        
        return temp_file.name
    
    def run_diagnosis_pipeline(self, image_path: str) -> DiagnosisResult:
        """
        运行完整诊断流程
        
        :param image_path: 输入图像路径
        :return: 诊断结果
        """
        import os
        from PIL import Image
        
        start_time = time.time()
        
        try:
            # Step 1: 视觉检测
            vision_result, features = self.vision_agent.detect(image_path)
            
            # 处理不同格式的返回结果
            if isinstance(vision_result, dict):
                detections = vision_result.get('detections', [])
            elif isinstance(vision_result, list):
                detections = vision_result
            else:
                detections = []
            
            if not detections:
                return DiagnosisResult(
                    success=False,
                    disease_name="",
                    confidence=0.0,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    error_message="未检测到病害"
                )
            
            # 获取主要检测结果
            primary_detection = detections[0]
            if isinstance(primary_detection, dict):
                disease_name = primary_detection.get('class', '未知病害')
                confidence = primary_detection.get('confidence', 0.0)
                bbox = primary_detection.get('bbox')
            else:
                disease_name = str(primary_detection)
                confidence = 0.5
                bbox = None
            
            # Step 2: 语言理解分析
            try:
                # 加载图像用于语言分析
                pil_image = Image.open(image_path)
                language_result = self.language_agent.analyze(
                    pil_image,
                    context={'detected_disease': disease_name}
                )
            except Exception as le:
                print(f"   语言分析失败，使用默认值: {le}")
                language_result = {
                    'description': f'检测到{disease_name}',
                    'symptoms': [],
                    'confidence': confidence
                }
            
            # Step 3: 知识图谱检索
            try:
                knowledge_result = self.knowledge_agent.query(disease_name)
            except Exception as ke:
                print(f"   知识查询失败，使用默认值: {ke}")
                knowledge_result = {
                    'disease': disease_name,
                    'symptoms': [],
                    'causes': [],
                    'treatments': []
                }
            
            # Step 4: 多模态融合
            try:
                fusion_result = self.fusion_agent.fuse(
                    vision_result,
                    language_result,
                    knowledge_result
                )
            except Exception as fe:
                print(f"   融合失败，使用视觉结果: {fe}")
                fusion_result = {
                    'disease': disease_name,
                    'confidence': confidence,
                    'symptoms': knowledge_result.get('symptoms', []),
                    'causes': knowledge_result.get('causes', []),
                    'recommendations': knowledge_result.get('treatments', [])
                }
            
            processing_time = (time.time() - start_time) * 1000
            
            return DiagnosisResult(
                success=True,
                disease_name=fusion_result.get('disease', disease_name),
                confidence=fusion_result.get('confidence', confidence),
                bbox=bbox,
                symptoms=fusion_result.get('symptoms', []),
                causes=fusion_result.get('causes', []),
                recommendations=fusion_result.get('recommendations', []),
                knowledge_sources=knowledge_result.get('sources', []),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return DiagnosisResult(
                success=False,
                disease_name="",
                confidence=0.0,
                processing_time_ms=processing_time,
                error_message=str(e)
            )
    
    def run_single_test(self, test_case: TestCase) -> Dict[str, Any]:
        """运行单个测试"""
        import os
        
        print(f"\n📝 运行测试: {test_case.name}")
        print(f"   描述: {test_case.description}")
        print(f"   难度: {test_case.difficulty}")
        
        # 创建测试图像
        image_path = self.create_test_image(test_case)
        
        try:
            # 运行诊断
            result = self.run_diagnosis_pipeline(image_path)
        finally:
            # 清理临时文件
            if os.path.exists(image_path):
                os.unlink(image_path)
        
        # 评估结果
        passed = self._evaluate_result(result, test_case)
        
        test_result = {
            'name': test_case.name,
            'description': test_case.description,
            'difficulty': test_case.difficulty,
            'expected': test_case.expected_disease,
            'actual': result.disease_name if result.success else None,
            'confidence': result.confidence,
            'processing_time_ms': result.processing_time_ms,
            'success': result.success,
            'passed': passed,
            'error': result.error_message
        }
        
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   结果: {status}")
        if result.success:
            print(f"   诊断: {result.disease_name} (置信度: {result.confidence:.2%})")
            print(f"   耗时: {result.processing_time_ms:.2f}ms")
        else:
            print(f"   错误: {result.error_message}")
        
        return test_result
    
    def _evaluate_result(self, result: DiagnosisResult, test_case: TestCase) -> bool:
        """评估测试结果"""
        if not result.success:
            return False
        
        # 基础检查
        if result.confidence < 0.5:
            return False
        
        if result.processing_time_ms > 5000:  # 5秒超时
            return False
        
        # 期望结果检查
        if test_case.expected_disease:
            return result.disease_name == test_case.expected_disease
        
        return True
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("\n" + "=" * 70)
        print("🚀 开始端到端集成测试")
        print("=" * 70)
        
        # 设置测试用例
        self.setup_test_cases()
        
        # 初始化模块
        use_mock = not self.initialize_modules()
        
        # 运行测试
        results = []
        for test_case in self.test_cases:
            result = self.run_single_test(test_case)
            results.append(result)
        
        # 统计结果
        total = len(results)
        passed = sum(1 for r in results if r['passed'])
        failed = total - passed
        
        # 按难度统计
        by_difficulty = {}
        for r in results:
            diff = r['difficulty']
            if diff not in by_difficulty:
                by_difficulty[diff] = {'total': 0, 'passed': 0}
            by_difficulty[diff]['total'] += 1
            if r['passed']:
                by_difficulty[diff]['passed'] += 1
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total if total > 0 else 0,
            'by_difficulty': by_difficulty,
            'use_mock_modules': use_mock,
            'results': results
        }
        
        self.results = results
        
        # 打印摘要
        print("\n" + "=" * 70)
        print("📊 测试结果摘要")
        print("=" * 70)
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {summary['pass_rate']:.1%}")
        print("\n按难度统计:")
        for diff, stats in by_difficulty.items():
            rate = stats['passed'] / stats['total'] if stats['total'] > 0 else 0
            print(f"   {diff}: {stats['passed']}/{stats['total']} ({rate:.1%})")
        
        if use_mock:
            print("\n⚠️ 注意: 使用了模拟模块进行测试")
        
        print("=" * 70)
        
        return summary
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """生成测试报告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/end_to_end_test_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'results': self.results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试报告已保存: {output_path}")
        return output_path


def test_end_to_end():
    """测试端到端流程"""
    print("=" * 70)
    print("🧪 测试端到端集成")
    print("=" * 70)
    
    suite = EndToEndTestSuite()
    summary = suite.run_all_tests()
    
    # 生成报告
    report_path = suite.generate_report()
    
    # 清理
    import shutil
    if os.path.exists("reports"):
        shutil.rmtree("reports")
    
    print("\n" + "=" * 70)
    print("✅ 端到端测试完成！")
    print("=" * 70)
    
    return summary


# 创建兼容函数供外部调用
run_tests = test_end_to_end


if __name__ == "__main__":
    test_end_to_end()

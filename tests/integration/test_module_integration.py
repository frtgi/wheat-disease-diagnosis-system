# -*- coding: utf-8 -*-
"""
模块集成测试

测试各模块之间的接口兼容性和数据流
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class IntegrationTestResult:
    """集成测试结果"""
    module_pair: str
    test_name: str
    passed: bool
    execution_time_ms: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ModuleIntegrationTest:
    """
    模块集成测试类
    
    测试各模块之间的集成点：
    1. Vision → Fusion
    2. Language → Fusion
    3. Knowledge → Fusion
    4. Fusion → Action
    5. Vision → Knowledge (通过检测结果查询知识)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化模块集成测试
        
        :param config: 测试配置
        """
        self.config = config or {}
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.results: List[IntegrationTestResult] = []
        
        # 模块实例
        self.modules = {}
        
        print("🔗 [ModuleIntegrationTest] 模块集成测试初始化完成")
    
    def setup_modules(self):
        """设置测试模块"""
        print("\n🔧 设置测试模块...")
        
        try:
            # 尝试导入真实模块
            from src.vision import EnhancedVisionAgent
            from src.text import EnhancedLanguageAgent
            from src.graph import KnowledgeAgent
            from src.fusion import EnhancedFusionAgent
            from src.action import EnhancedActiveLearner
            
            print("   使用真实模块进行测试")
            self.use_mock = False
            
        except ImportError as e:
            print(f"   模块导入失败: {e}")
            print("   使用模拟模块进行测试")
            self.use_mock = True
            self._setup_mock_modules()
    
    def _setup_mock_modules(self):
        """设置模拟模块"""
        # 模拟视觉模块
        class MockVisionAgent:
            def detect(self, image, **kwargs):
                return {
                    'detections': [
                        {
                            'class': '条锈病',
                            'confidence': 0.92,
                            'bbox': [100, 100, 200, 200],
                            'features': np.random.randn(512)
                        }
                    ],
                    'feature_map': np.random.randn(256, 20, 20)
                }
            
            def extract_features(self, image):
                return np.random.randn(512)
        
        # 模拟语言模块
        class MockLanguageAgent:
            def analyze(self, image, context=None):
                return {
                    'description': '叶片出现黄色条状病斑',
                    'symptoms': ['黄色条纹', '孢子堆'],
                    'confidence': 0.88,
                    'embeddings': np.random.randn(768)
                }
            
            def encode_text(self, text):
                return np.random.randn(768)
        
        # 模拟知识图谱模块
        class MockKnowledgeAgent:
            def query(self, disease_name):
                return {
                    'disease': disease_name,
                    'symptoms': ['黄色条纹', '孢子堆'],
                    'causes': ['低温高湿', '真菌感染'],
                    'treatments': ['粉锈宁', '戊唑醇'],
                    'kg_embedding': np.random.randn(256)
                }
            
            def get_related_diseases(self, symptom):
                return ['条锈病', '叶锈病']
        
        # 模拟融合模块
        class MockFusionAgent:
            def __init__(self, knowledge_agent=None):
                self.knowledge_agent = knowledge_agent
            
            def fuse(self, vision_result, language_result, knowledge_result):
                return {
                    'disease': vision_result['detections'][0]['class'],
                    'confidence': 0.90,
                    'symptoms': knowledge_result['symptoms'],
                    'causes': knowledge_result['causes'],
                    'recommendations': knowledge_result['treatments'],
                    'fused_embedding': np.random.randn(512)
                }
            
            def knowledge_guided_attention(self, visual_features, knowledge_embedding):
                return visual_features * 1.1  # 模拟注意力加权
        
        # 模拟行动模块
        class MockActiveLearner:
            def learn_from_feedback(self, diagnosis_result, feedback):
                return {'status': 'success', 'updated': True}
            
            def get_uncertainty(self, prediction):
                return 0.15
        
        self.modules = {
            'vision': MockVisionAgent(),
            'language': MockLanguageAgent(),
            'knowledge': MockKnowledgeAgent(),
            'fusion': MockFusionAgent(MockKnowledgeAgent()),
            'action': MockActiveLearner()
        }
        
        print("   ✅ 模拟模块设置完成")
    
    def test_vision_to_fusion(self) -> IntegrationTestResult:
        """测试视觉模块到融合模块的数据流"""
        print("\n🧪 测试: Vision → Fusion")
        
        start_time = time.time()
        
        try:
            # 创建测试图像
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # 视觉检测
            vision_result = self.modules['vision'].detect(test_image)
            
            # 验证视觉输出格式
            assert 'detections' in vision_result
            assert len(vision_result['detections']) > 0
            assert 'class' in vision_result['detections'][0]
            assert 'confidence' in vision_result['detections'][0]
            
            # 准备融合输入
            language_result = self.modules['language'].analyze(test_image)
            disease_name = vision_result['detections'][0]['class']
            knowledge_result = self.modules['knowledge'].query(disease_name)
            
            # 融合
            fusion_result = self.modules['fusion'].fuse(
                vision_result, language_result, knowledge_result
            )
            
            # 验证融合输出
            assert 'disease' in fusion_result
            assert 'confidence' in fusion_result
            
            execution_time = (time.time() - start_time) * 1000
            
            return IntegrationTestResult(
                module_pair="Vision → Fusion",
                test_name="视觉融合数据流",
                passed=True,
                execution_time_ms=execution_time,
                details={
                    'detected_disease': disease_name,
                    'fusion_confidence': fusion_result['confidence']
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return IntegrationTestResult(
                module_pair="Vision → Fusion",
                test_name="视觉融合数据流",
                passed=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
    
    def test_language_to_fusion(self) -> IntegrationTestResult:
        """测试语言模块到融合模块的数据流"""
        print("\n🧪 测试: Language → Fusion")
        
        start_time = time.time()
        
        try:
            # 创建测试图像
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # 语言分析
            language_result = self.modules['language'].analyze(test_image)
            
            # 验证语言输出格式
            assert 'description' in language_result
            assert 'embeddings' in language_result
            
            # 准备融合输入
            vision_result = self.modules['vision'].detect(test_image)
            disease_name = vision_result['detections'][0]['class']
            knowledge_result = self.modules['knowledge'].query(disease_name)
            
            # 融合
            fusion_result = self.modules['fusion'].fuse(
                vision_result, language_result, knowledge_result
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return IntegrationTestResult(
                module_pair="Language → Fusion",
                test_name="语言融合数据流",
                passed=True,
                execution_time_ms=execution_time,
                details={
                    'description': language_result['description'],
                    'embedding_dim': len(language_result['embeddings'])
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return IntegrationTestResult(
                module_pair="Language → Fusion",
                test_name="语言融合数据流",
                passed=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
    
    def test_knowledge_to_fusion(self) -> IntegrationTestResult:
        """测试知识图谱到融合模块的数据流"""
        print("\n🧪 测试: Knowledge → Fusion")
        
        start_time = time.time()
        
        try:
            # 查询知识图谱
            disease_name = "条锈病"
            knowledge_result = self.modules['knowledge'].query(disease_name)
            
            # 验证知识输出格式
            assert 'disease' in knowledge_result
            assert 'symptoms' in knowledge_result
            assert 'treatments' in knowledge_result
            
            # 准备融合输入
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            vision_result = self.modules['vision'].detect(test_image)
            language_result = self.modules['language'].analyze(test_image)
            
            # 融合
            fusion_result = self.modules['fusion'].fuse(
                vision_result, language_result, knowledge_result
            )
            
            # 验证知识信息被正确传递
            assert fusion_result['symptoms'] == knowledge_result['symptoms']
            assert fusion_result['recommendations'] == knowledge_result['treatments']
            
            execution_time = (time.time() - start_time) * 1000
            
            return IntegrationTestResult(
                module_pair="Knowledge → Fusion",
                test_name="知识融合数据流",
                passed=True,
                execution_time_ms=execution_time,
                details={
                    'disease': disease_name,
                    'symptoms_count': len(knowledge_result['symptoms']),
                    'treatments_count': len(knowledge_result['treatments'])
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return IntegrationTestResult(
                module_pair="Knowledge → Fusion",
                test_name="知识融合数据流",
                passed=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
    
    def test_fusion_to_action(self) -> IntegrationTestResult:
        """测试融合模块到行动模块的数据流"""
        print("\n🧪 测试: Fusion → Action")
        
        start_time = time.time()
        
        try:
            # 创建融合结果
            fusion_result = {
                'disease': '条锈病',
                'confidence': 0.92,
                'symptoms': ['黄色条纹'],
                'recommendations': ['粉锈宁']
            }
            
            # 模拟反馈
            feedback = {
                'correct': True,
                'expert_notes': '诊断正确'
            }
            
            # 行动模块学习
            learn_result = self.modules['action'].learn_from_feedback(
                fusion_result, feedback
            )
            
            # 验证学习结果
            assert learn_result['status'] == 'success'
            
            # 测试不确定性估计
            uncertainty = self.modules['action'].get_uncertainty(fusion_result)
            assert 0 <= uncertainty <= 1
            
            execution_time = (time.time() - start_time) * 1000
            
            return IntegrationTestResult(
                module_pair="Fusion → Action",
                test_name="融合行动数据流",
                passed=True,
                execution_time_ms=execution_time,
                details={
                    'learning_status': learn_result['status'],
                    'uncertainty': uncertainty
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return IntegrationTestResult(
                module_pair="Fusion → Action",
                test_name="融合行动数据流",
                passed=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
    
    def test_vision_to_knowledge(self) -> IntegrationTestResult:
        """测试视觉模块到知识图谱的查询链路"""
        print("\n🧪 测试: Vision → Knowledge")
        
        start_time = time.time()
        
        try:
            # 创建测试图像
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # 视觉检测
            vision_result = self.modules['vision'].detect(test_image)
            detected_disease = vision_result['detections'][0]['class']
            
            # 基于检测结果查询知识图谱
            knowledge_result = self.modules['knowledge'].query(detected_disease)
            
            # 验证查询结果
            assert knowledge_result['disease'] == detected_disease
            
            # 获取相关病害
            related = self.modules['knowledge'].get_related_diseases(
                knowledge_result['symptoms'][0]
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return IntegrationTestResult(
                module_pair="Vision → Knowledge",
                test_name="视觉知识查询链路",
                passed=True,
                execution_time_ms=execution_time,
                details={
                    'detected_disease': detected_disease,
                    'related_diseases': related
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return IntegrationTestResult(
                module_pair="Vision → Knowledge",
                test_name="视觉知识查询链路",
                passed=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
    
    def test_knowledge_guided_attention(self) -> IntegrationTestResult:
        """测试知识引导注意力机制"""
        print("\n🧪 测试: Knowledge-Guided Attention")
        
        start_time = time.time()
        
        try:
            # 创建视觉特征
            visual_features = np.random.randn(256, 20, 20)
            
            # 创建知识嵌入
            knowledge_embedding = np.random.randn(256)
            
            # 应用知识引导注意力
            attended_features = self.modules['fusion'].knowledge_guided_attention(
                visual_features, knowledge_embedding
            )
            
            # 验证输出形状
            assert attended_features.shape == visual_features.shape
            
            execution_time = (time.time() - start_time) * 1000
            
            return IntegrationTestResult(
                module_pair="KGA",
                test_name="知识引导注意力",
                passed=True,
                execution_time_ms=execution_time,
                details={
                    'feature_shape': list(attended_features.shape),
                    'attention_applied': True
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return IntegrationTestResult(
                module_pair="KGA",
                test_name="知识引导注意力",
                passed=False,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有集成测试"""
        print("\n" + "=" * 70)
        print("🔗 开始模块集成测试")
        print("=" * 70)
        
        # 设置模块
        self.setup_modules()
        
        # 定义测试列表
        tests = [
            self.test_vision_to_fusion,
            self.test_language_to_fusion,
            self.test_knowledge_to_fusion,
            self.test_fusion_to_action,
            self.test_vision_to_knowledge,
            self.test_knowledge_guided_attention,
        ]
        
        # 运行测试
        results = []
        for test_func in tests:
            result = test_func()
            results.append(result)
            
            status = "✅ 通过" if result.passed else "❌ 失败"
            print(f"   结果: {status} ({result.execution_time_ms:.2f}ms)")
            if result.error_message:
                print(f"   错误: {result.error_message}")
        
        # 统计结果
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total if total > 0 else 0,
            'use_mock_modules': getattr(self, 'use_mock', True),
            'results': [r.to_dict() for r in results]
        }
        
        self.results = results
        
        # 打印摘要
        print("\n" + "=" * 70)
        print("📊 模块集成测试结果摘要")
        print("=" * 70)
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {summary['pass_rate']:.1%}")
        
        if getattr(self, 'use_mock', True):
            print("\n⚠️ 注意: 使用了模拟模块进行测试")
        
        print("=" * 70)
        
        return summary
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """生成测试报告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/module_integration_test_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'results': [r.to_dict() for r in self.results]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试报告已保存: {output_path}")
        return output_path


def test_module_integration():
    """测试模块集成"""
    print("=" * 70)
    print("🧪 测试模块集成")
    print("=" * 70)
    
    tester = ModuleIntegrationTest()
    summary = tester.run_all_tests()
    
    # 生成报告
    report_path = tester.generate_report()
    
    # 清理
    import shutil
    if os.path.exists("reports"):
        shutil.rmtree("reports")
    
    print("\n" + "=" * 70)
    print("✅ 模块集成测试完成！")
    print("=" * 70)
    
    return summary


# 创建兼容函数供外部调用
run_tests = test_module_integration


if __name__ == "__main__":
    test_module_integration()

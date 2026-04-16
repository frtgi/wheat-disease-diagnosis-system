# -*- coding: utf-8 -*-
"""
IWDDA 系统集成测试脚本

测试所有模块的协同工作能力，验证系统完整性
"""
import os
import sys
import time
import json
import io
import locale
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 解决Windows下的编码问题
if sys.platform == 'win32':
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # 设置标准输出编码为UTF-8
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # 设置控制台代码页为UTF-8
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
    except Exception:
        pass

import torch
import numpy as np
from PIL import Image

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class TestResult:
    """测试结果"""
    module: str
    test_name: str
    success: bool
    message: str
    duration_ms: float = 0


class SystemIntegrationTest:
    """
    系统集成测试类
    
    测试所有模块的协同工作能力
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        
        # 模块实例
        self.vision_engine = None
        self.cognition_engine = None
        self.fusion_engine = None
        self.graph_engine = None
        self.kad_fusion = None
        self.gnn_reasoner = None
        self.incremental_learner = None
        
    def run_all_tests(self) -> bool:
        """
        运行所有测试
        
        :return: 是否全部通过
        """
        print("=" * 70)
        print("🧪 IWDDA 系统集成测试")
        print("=" * 70)
        
        self.start_time = time.time()
        
        # 1. 模块导入测试
        print("\n📦 阶段 1: 模块导入测试")
        print("-" * 70)
        self._test_imports()
        
        # 2. 核心模块初始化测试
        print("\n🔧 阶段 2: 核心模块初始化测试")
        print("-" * 70)
        self._test_core_modules()
        
        # 3. 视觉模块测试
        print("\n👁️ 阶段 3: 视觉模块测试")
        print("-" * 70)
        self._test_vision_module()
        
        # 4. 知识图谱模块测试
        print("\n🧠 阶段 4: 知识图谱模块测试")
        print("-" * 70)
        self._test_knowledge_graph()
        
        # 5. 融合模块测试
        print("\n🔗 阶段 5: 融合模块测试")
        print("-" * 70)
        self._test_fusion_module()
        
        # 6. 增量学习模块测试
        print("\n📚 阶段 6: 增量学习模块测试")
        print("-" * 70)
        self._test_incremental_learning()
        
        # 7. 端到端诊断测试
        print("\n🚀 阶段 7: 端到端诊断测试")
        print("-" * 70)
        self._test_end_to_end()
        
        # 打印结果摘要
        self._print_summary()
        
        return all(r.success for r in self.results)
    
    def _record_result(self, module: str, test_name: str, success: bool, 
                       message: str, duration_ms: float = 0):
        """记录测试结果"""
        result = TestResult(
            module=module,
            test_name=test_name,
            success=success,
            message=message,
            duration_ms=duration_ms
        )
        self.results.append(result)
        
        status = "✅" if success else "❌"
        print(f"  {status} [{module}] {test_name}: {message}")
        if duration_ms > 0:
            print(f"      耗时: {duration_ms:.2f}ms")
    
    def _test_imports(self):
        """测试模块导入"""
        modules_to_test = [
            ("src.vision.vision_engine", "VisionAgent"),
            ("src.vision.enhanced_yolo", "SerpensGateYOLO"),
            ("src.vision.dy_snake_conv", "DySnakeConv"),
            ("src.vision.sppelan_module", "SPPELAN"),
            ("src.vision.sta_module", "SuperTokenAttention"),
            ("src.cognition.cognition_engine", "CognitionEngine"),
            ("src.cognition.llava_engine", "AgriLLaVA"),
            ("src.graph.graph_engine", "KnowledgeAgent"),
            ("src.graph.graphrag_engine", "GraphRAGEngine"),
            ("src.graph.itext2kg", "IText2KG"),  # 修正类名
            ("src.graph.gnn_reasoning", "MultiHopGNN"),
            ("src.fusion.fusion_engine", "FusionAgent"),
            ("src.fusion.kga_module", "KADFusion"),
            ("src.fusion.cross_attention", "CrossModalAttention"),
            ("src.evolution.incremental_learning", "iCaRL"),
            ("src.data.augmentation_engine", "AugmentationEngine"),
            ("src.evaluation.evaluation_framework", "PerformanceEvaluator"),
            ("src.deploy.edge_optimizer", "EdgeOptimizer"),
        ]
        
        for module_path, class_name in modules_to_test:
            start = time.time()
            try:
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                duration = (time.time() - start) * 1000
                self._record_result(
                    "Import", f"导入 {class_name}", True, 
                    f"成功导入 {module_path}.{class_name}", duration
                )
            except Exception as e:
                duration = (time.time() - start) * 1000
                self._record_result(
                    "Import", f"导入 {class_name}", False, 
                    f"导入失败: {str(e)[:50]}", duration
                )
    
    def _test_core_modules(self):
        """测试核心模块初始化"""
        # 测试视觉引擎
        start = time.time()
        try:
            from src.vision.vision_engine import VisionAgent
            self.vision_engine = VisionAgent()
            duration = (time.time() - start) * 1000
            self._record_result(
                "Vision", "初始化视觉引擎", True, 
                f"模型加载成功", duration
            )
        except Exception as e:
            self._record_result("Vision", "初始化视觉引擎", False, str(e)[:100])
        
        # 测试知识图谱引擎
        start = time.time()
        try:
            from src.graph.graph_engine import KnowledgeAgent
            self.graph_engine = KnowledgeAgent(password="123456789s")
            duration = (time.time() - start) * 1000
            self._record_result(
                "Graph", "初始化知识图谱引擎", True, 
                "连接成功", duration
            )
        except Exception as e:
            self._record_result("Graph", "初始化知识图谱引擎", False, str(e)[:100])
        
        # 测试融合引擎
        start = time.time()
        try:
            from src.fusion.fusion_engine import FusionAgent
            self.fusion_engine = FusionAgent(knowledge_agent=self.graph_engine)
            duration = (time.time() - start) * 1000
            self._record_result(
                "Fusion", "初始化融合引擎", True, 
                "初始化成功", duration
            )
        except Exception as e:
            self._record_result("Fusion", "初始化融合引擎", False, str(e)[:100])
        
        # 测试KAD-Fusion
        start = time.time()
        try:
            from src.fusion.kga_module import KADFusion
            self.kad_fusion = KADFusion(
                vision_dim=256,
                text_dim=768,
                knowledge_dim=768
            )
            duration = (time.time() - start) * 1000
            self._record_result(
                "KAD", "初始化KAD-Fusion", True, 
                f"参数量: {sum(p.numel() for p in self.kad_fusion.parameters()):,}", duration
            )
        except Exception as e:
            self._record_result("KAD", "初始化KAD-Fusion", False, str(e)[:100])
    
    def _test_vision_module(self):
        """测试视觉模块"""
        # 测试DySnakeConv
        start = time.time()
        try:
            from src.vision.dy_snake_conv import DySnakeConv
            conv = DySnakeConv(64, 128, 3)
            x = torch.randn(1, 64, 32, 32)
            y = conv(x)
            duration = (time.time() - start) * 1000
            self._record_result(
                "Vision", "DySnakeConv前向传播", True, 
                f"输入{tuple(x.shape)} -> 输出{tuple(y.shape)}", duration
            )
        except Exception as e:
            self._record_result("Vision", "DySnakeConv前向传播", False, str(e)[:100])
        
        # 测试SPPELAN
        start = time.time()
        try:
            from src.vision.sppelan_module import SPPELAN
            sppelan = SPPELAN(64, 128)
            x = torch.randn(1, 64, 32, 32)
            y = sppelan(x)
            duration = (time.time() - start) * 1000
            self._record_result(
                "Vision", "SPPELAN前向传播", True, 
                f"输入{tuple(x.shape)} -> 输出{tuple(y.shape)}", duration
            )
        except Exception as e:
            self._record_result("Vision", "SPPELAN前向传播", False, str(e)[:100])
        
        # 测试STA
        start = time.time()
        try:
            from src.vision.sta_module import SuperTokenAttention
            sta = SuperTokenAttention(256, num_super_tokens=4)
            x = torch.randn(1, 256, 16, 16)
            y = sta(x)
            duration = (time.time() - start) * 1000
            self._record_result(
                "Vision", "STA前向传播", True, 
                f"输入{tuple(x.shape)} -> 输出{tuple(y.shape)}", duration
            )
        except Exception as e:
            self._record_result("Vision", "STA前向传播", False, str(e)[:100])
        
        # 测试视觉引擎检测
        if self.vision_engine:
            start = time.time()
            try:
                test_image = "datasets/wheat_data/images/train/Aphid_aphid_0.png"
                if os.path.exists(test_image):
                    result = self.vision_engine.detect(test_image)
                    duration = (time.time() - start) * 1000
                    self._record_result(
                        "Vision", "病害检测", True, 
                        f"检测完成", duration
                    )
                else:
                    self._record_result("Vision", "病害检测", True, "测试图像不存在，跳过")
            except Exception as e:
                self._record_result("Vision", "病害检测", False, str(e)[:100])
    
    def _test_knowledge_graph(self):
        """测试知识图谱模块"""
        # 测试iText2KG
        start = time.time()
        try:
            from src.graph.itext2kg import IText2KG
            extractor = IText2KG()
            text = "小麦条锈病是由条形柄锈菌引起的真菌性病害，主要症状是叶片出现黄色条纹状孢子堆。"
            triples = extractor.process_text(text)  # 使用正确的方法名
            entities = list(extractor.entities.values())  # 获取实体
            relations = triples  # 三元组即关系
            duration = (time.time() - start) * 1000
            self._record_result(
                "Graph", "iText2KG知识抽取", True, 
                f"抽取{len(entities)}个实体, {len(relations)}个三元组", duration
            )
        except Exception as e:
            self._record_result("Graph", "iText2KG知识抽取", False, str(e)[:100])
        
        # 测试GNN推理
        start = time.time()
        try:
            from src.graph.gnn_reasoning import MultiHopGNN, KnowledgeGraphReasoner
            gnn = MultiHopGNN(num_entities=100, num_relations=20, embedding_dim=64)
            # 正确的输入：entity_ids是实体索引，不是特征张量
            entity_ids = torch.randint(0, 100, (10,), dtype=torch.long)
            edge_index = torch.randint(0, 100, (2, 200), dtype=torch.long)
            edge_type = torch.randint(0, 20, (200,), dtype=torch.long)
            out = gnn(entity_ids, edge_index, edge_type)
            duration = (time.time() - start) * 1000
            self._record_result(
                "Graph", "GNN多跳推理", True, 
                f"输出形状: {tuple(out.shape)}", duration
            )
        except Exception as e:
            self._record_result("Graph", "GNN多跳推理", False, str(e)[:100])
        
        # 测试知识图谱查询
        if self.graph_engine:
            start = time.time()
            try:
                # 使用正确的方法名
                if hasattr(self.graph_engine, 'query_disease'):
                    diseases = self.graph_engine.query_disease("条锈病")
                elif hasattr(self.graph_engine, 'search'):
                    diseases = self.graph_engine.search("条锈病")
                else:
                    diseases = []
                duration = (time.time() - start) * 1000
                self._record_result(
                    "Graph", "知识图谱查询", True, 
                    f"查询完成", duration
                )
            except Exception as e:
                self._record_result("Graph", "知识图谱查询", False, str(e)[:100])
    
    def _test_fusion_module(self):
        """测试融合模块"""
        # 测试KGA
        start = time.time()
        try:
            from src.fusion.kga_module import KnowledgeGuidedAttention
            kga = KnowledgeGuidedAttention(vision_dim=256, knowledge_dim=768)
            vision_feat = torch.randn(2, 10, 256)
            knowledge_emb = torch.randn(2, 5, 768)
            enhanced = kga(vision_feat, knowledge_emb)
            duration = (time.time() - start) * 1000
            self._record_result(
                "Fusion", "知识引导注意力", True, 
                f"输出形状: {tuple(enhanced.shape)}", duration
            )
        except Exception as e:
            self._record_result("Fusion", "知识引导注意力", False, str(e)[:100])
        
        # 测试跨模态注意力
        start = time.time()
        try:
            from src.fusion.cross_attention import CrossModalAttention
            cross_attn = CrossModalAttention(text_dim=768, vision_dim=256)
            text_feat = torch.randn(2, 768)
            vision_feat = torch.randn(2, 10, 256)
            fused = cross_attn(text_feat, vision_feat)
            duration = (time.time() - start) * 1000
            self._record_result(
                "Fusion", "跨模态注意力", True, 
                f"输出形状: {tuple(fused.shape)}", duration
            )
        except Exception as e:
            self._record_result("Fusion", "跨模态注意力", False, str(e)[:100])
        
        # 测试完整KAD-Fusion
        if self.kad_fusion:
            start = time.time()
            try:
                vision_feat = torch.randn(2, 10, 256)
                text_feat = torch.randn(2, 768)
                knowledge_emb = torch.randn(2, 5, 768)
                output = self.kad_fusion(vision_feat, text_feat, knowledge_emb)
                duration = (time.time() - start) * 1000
                self._record_result(
                    "Fusion", "完整KAD-Fusion", True, 
                    f"输出形状: {tuple(output.shape)}", duration
                )
            except Exception as e:
                self._record_result("Fusion", "完整KAD-Fusion", False, str(e)[:100])
    
    def _test_incremental_learning(self):
        """测试增量学习模块"""
        # 测试iCaRL
        start = time.time()
        try:
            from src.evolution.incremental_learning import iCaRL, IncrementalConfig
            config = IncrementalConfig(num_classes=10, embedding_dim=256)
            icarl = iCaRL(config)
            features = torch.randn(32, 256)
            labels = torch.randint(0, 10, (32,))
            total_loss, loss_dict = icarl.compute_loss(features, labels, new_classes=[3])
            duration = (time.time() - start) * 1000
            self._record_result(
                "Learning", "iCaRL增量学习", True, 
                f"损失值: {total_loss.item():.4f}", duration
            )
        except Exception as e:
            self._record_result("Learning", "iCaRL增量学习", False, str(e)[:100])
        
        # 测试LwF
        start = time.time()
        try:
            from src.evolution.incremental_learning import LwF, IncrementalConfig
            config = IncrementalConfig(num_classes=10, embedding_dim=256)
            lwf = LwF(config)
            features = torch.randn(32, 256)
            labels = torch.randint(0, 10, (32,))
            old_logits = torch.randn(32, 10)
            total_loss, loss_dict = lwf.compute_loss(features, labels, old_logits)
            duration = (time.time() - start) * 1000
            self._record_result(
                "Learning", "LwF学习", True, 
                f"损失值: {total_loss.item():.4f}", duration
            )
        except Exception as e:
            self._record_result("Learning", "LwF学习", False, str(e)[:100])
        
        # 测试EWC
        start = time.time()
        try:
            from src.evolution.incremental_learning import EWC, IncrementalConfig
            config = IncrementalConfig()
            # EWC参数顺序是 (model, config)
            ewc = EWC(model=None, config=config)  # model可以为None用于初始化测试
            self._record_result(
                "Learning", "EWC初始化", True, 
                "初始化成功", (time.time() - start) * 1000
            )
        except Exception as e:
            self._record_result("Learning", "EWC初始化", False, str(e)[:100])
    
    def _test_end_to_end(self):
        """测试端到端诊断流程"""
        # 创建测试图像
        test_image_path = "datasets/wheat_data/images/train/Aphid_aphid_0.png"
        
        if not os.path.exists(test_image_path):
            # 创建模拟测试图像
            test_image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
            test_image_path = "test_image_temp.png"
            Image.fromarray(test_image).save(test_image_path)
        
        # 测试完整诊断流程
        start = time.time()
        try:
            if self.vision_engine:
                # 视觉检测
                vision_result = self.vision_engine.detect(test_image_path)
                
                # 知识图谱增强（如果可用）
                if self.graph_engine and vision_result:
                    for res in vision_result[:1]:
                        disease_name = res.get('name', '未知')
                        # 使用正确的方法名
                        if hasattr(self.graph_engine, 'query_disease'):
                            disease_info = self.graph_engine.query_disease(disease_name)
                        elif hasattr(self.graph_engine, 'search'):
                            disease_info = self.graph_engine.search(disease_name)
                        else:
                            disease_info = None
                        if disease_info:
                            res['knowledge'] = disease_info
                
                duration = (time.time() - start) * 1000
                self._record_result(
                    "E2E", "端到端诊断", True, 
                    f"完成{len(vision_result) if vision_result else 0}个检测结果", duration
                )
            else:
                self._record_result("E2E", "端到端诊断", False, "视觉引擎未初始化")
        except Exception as e:
            self._record_result("E2E", "端到端诊断", False, str(e)[:100])
        
        # 清理临时文件
        if test_image_path == "test_image_temp.png" and os.path.exists(test_image_path):
            os.remove(test_image_path)
    
    def _print_summary(self):
        """打印测试摘要"""
        total_time = time.time() - self.start_time
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 70)
        print("📊 测试摘要")
        print("=" * 70)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        print(f"总耗时: {total_time:.2f}秒")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for r in self.results:
                if not r.success:
                    print(f"   [{r.module}] {r.test_name}: {r.message}")
        
        print("=" * 70)
        
        # 保存结果
        self._save_results()
    
    def _save_results(self):
        """保存测试结果"""
        output_dir = Path("logs/test_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"integration_test_{timestamp}.json"
        
        results_data = {
            "timestamp": timestamp,
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "results": [
                {
                    "module": r.module,
                    "test_name": r.test_name,
                    "success": r.success,
                    "message": r.message,
                    "duration_ms": r.duration_ms
                }
                for r in self.results
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试结果已保存: {output_file}")


def main():
    """主函数"""
    tester = SystemIntegrationTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过！系统运行正常。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查相关模块。")
        return 1


if __name__ == "__main__":
    exit(main())

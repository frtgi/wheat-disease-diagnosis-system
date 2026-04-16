# -*- coding: utf-8 -*-
"""
多模态特征融合集成测试模块 (Multimodal Feature Fusion Integration Test)

验证所有新模块的功能和集成效果：
1. DeepStack 多层特征注入
2. 交叉注意力与 SE 机制
3. 环境数据嵌入分支
4. 数据结构扩展
5. LoRA 微调配置
6. 不确定性量化损失

技术特性:
- 模块单元测试
- 集成流程测试
- 性能基准测试
- 端到端验证
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MultimodalFusionIntegrationTest:
    """
    多模态融合集成测试类
    """
    
    def __init__(self):
        """初始化测试类"""
        self.test_results = {}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"测试设备: {self.device}")
        
    def run_all_tests(self) -> Dict[str, bool]:
        """
        运行所有测试
        
        :return: 测试结果字典
        """
        print("\n" + "=" * 70)
        print("多模态特征融合集成测试")
        print("=" * 70)
        
        # 1. DeepStack 模块测试
        self.test_results['deepstack'] = self._test_deepstack_injection()
        
        # 2. 交叉注意力与 SE 机制测试
        self.test_results['cross_attention_se'] = self._test_cross_attention_se()
        
        # 3. 环境数据嵌入测试
        self.test_results['environment_embedding'] = self._test_environment_embedding()
        
        # 4. 数据结构测试
        self.test_results['data_structure'] = self._test_data_structure()
        
        # 5. LoRA 配置测试
        self.test_results['lora_config'] = self._test_lora_config()
        
        # 6. 不确定性损失测试
        self.test_results['uncertainty_loss'] = self._test_uncertainty_loss()
        
        # 7. 端到端集成测试
        self.test_results['end_to_end'] = self._test_end_to_end_integration()
        
        # 打印汇总
        self._print_summary()
        
        return self.test_results
    
    def _test_deepstack_injection(self) -> bool:
        """测试 DeepStack 多层特征注入模块"""
        print("\n[测试 1] DeepStack 多层特征注入模块")
        print("-" * 50)
        
        try:
            from fusion.deepstack_injection import (
                DeepStackFeatureInjection, 
                create_deepstack_injection
            )
            
            # 创建模块
            deepstack = create_deepstack_injection(
                vision_dims={'low': 1024, 'mid': 1024, 'high': 1024},
                llm_dim=4096
            ).to(self.device)
            
            # 测试输入
            batch_size = 2
            seq_len = 64
            
            low_features = torch.randn(batch_size, seq_len, 1024).to(self.device)
            mid_features = torch.randn(batch_size, seq_len, 1024).to(self.device)
            high_features = torch.randn(batch_size, seq_len, 1024).to(self.device)
            llm_hidden = torch.randn(batch_size, seq_len, 4096).to(self.device)
            
            # 前向传播
            with torch.no_grad():
                result = deepstack(low_features, mid_features, high_features, llm_hidden)
            
            # 验证输出
            assert result['fused_features'].shape == (batch_size, seq_len, 4096), \
                f"融合特征维度错误: {result['fused_features'].shape}"
            
            print(f"  [OK] 融合特征维度: {result['fused_features'].shape}")
            print(f"  [OK] 层级权重: {result['layer_weights']}")
            print(f"  [OK] 参数数量: {sum(p.numel() for p in deepstack.parameters()):,}")
            
            return True
            
        except Exception as e:
            print(f"  [失败] {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _test_cross_attention_se(self) -> bool:
        """测试交叉注意力与 SE 机制模块"""
        print("\n[测试 2] 交叉注意力与 SE 机制模块")
        print("-" * 50)
        
        try:
            from fusion.cross_attention import (
                SEEnhancedCrossModalAttention,
                MultiScaleCrossModalAttention,
                create_cross_attention_model
            )
            
            # 创建 SE 增强模块
            se_model = create_cross_attention_model(
                text_dim=768,
                vision_dim=512,
                num_heads=8,
                use_se=True
            ).to(self.device)
            
            # 测试输入
            batch_size = 2
            text_seq_len = 32
            vision_seq_len = 64
            
            text_features = torch.randn(batch_size, text_seq_len, 768).to(self.device)
            vision_features = torch.randn(batch_size, vision_seq_len, 512).to(self.device)
            
            # 前向传播
            with torch.no_grad():
                result = se_model(text_features, vision_features)
            
            # 验证输出
            assert result['fused_features'].shape == (batch_size, text_seq_len, 768), \
                f"融合特征维度错误: {result['fused_features'].shape}"
            
            print(f"  [OK] 融合特征维度: {result['fused_features'].shape}")
            print(f"  [OK] 文本加权特征维度: {result['text_weighted'].shape}")
            print(f"  [OK] 注意力权重维度: {result['cross_attention_weights'].shape}")
            
            # 测试多尺度模块
            multi_scale_model = MultiScaleCrossModalAttention(
                text_dim=768,
                vision_dim=512,
                num_heads=8,
                num_scales=3
            ).to(self.device)
            
            with torch.no_grad():
                ms_result = multi_scale_model(text_features, vision_features)
            
            print(f"  [OK] 多尺度融合特征维度: {ms_result['fused_features'].shape}")
            print(f"  [OK] 尺度权重: {ms_result['scale_weights']}")
            
            return True
            
        except Exception as e:
            print(f"  [失败] {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _test_environment_embedding(self) -> bool:
        """测试环境数据嵌入分支"""
        print("\n[测试 3] 环境数据嵌入分支")
        print("-" * 50)
        
        try:
            from fusion.environment_embedding import (
                EnvironmentEmbeddingBranch,
                create_environment_embedding_branch
            )
            
            # 创建模块
            env_branch = create_environment_embedding_branch(
                output_dim=768,
                hidden_dim=256
            ).to(self.device)
            
            # 测试输入
            batch_size = 4
            
            # 前向传播
            with torch.no_grad():
                result = env_branch.forward(
                    temperature=torch.randn(batch_size).to(self.device) * 10 + 20,
                    humidity=torch.rand(batch_size).to(self.device) * 40 + 40,
                    region_id=torch.randint(0, 50, (batch_size,)).to(self.device),
                    province_id=torch.randint(0, 34, (batch_size,)).to(self.device),
                    growth_stage_id=torch.randint(0, 11, (batch_size,)).to(self.device),
                    light_intensity=torch.rand(batch_size).to(self.device) * 100,
                    soil_moisture=torch.rand(batch_size).to(self.device) * 100,
                    wind_speed=torch.rand(batch_size).to(self.device) * 10
                )
            
            # 验证输出
            assert result['environment_embedding'].shape == (batch_size, 768), \
                f"环境嵌入维度错误: {result['environment_embedding'].shape}"
            
            print(f"  [OK] 环境嵌入维度: {result['environment_embedding'].shape}")
            print(f"  [OK] 3D 嵌入维度: {result['environment_embedding_3d'].shape}")
            print(f"  [OK] 特征名称: {result['feature_names']}")
            
            # 测试从原始值获取嵌入
            with torch.no_grad():
                raw_result = env_branch.get_environment_feature_vector(
                    temperature=25.0,
                    humidity=80.0,
                    growth_stage="抽穗期"
                )
            
            print(f"  [OK] 原始值嵌入维度: {raw_result['environment_embedding'].shape}")
            
            return True
            
        except Exception as e:
            print(f"  [失败] {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _test_data_structure(self) -> bool:
        """测试数据结构扩展"""
        print("\n[测试 4] 数据结构扩展")
        print("-" * 50)
        
        try:
            from data.multimodal_data_structure import (
                MultimodalDataSample,
                EnvironmentMetadata,
                KnowledgeGraphTriple,
                MultimodalDatasetBuilder,
                create_sample_json_example
            )
            
            # 测试示例 JSON
            example_json = create_sample_json_example()
            print(f"  [OK] 示例 JSON 创建成功")
            
            # 解析 JSON
            import json
            data = json.loads(example_json)
            sample = MultimodalDataSample.from_dict(data)
            
            print(f"  [OK] 样本 ID: {sample.id}")
            print(f"  [OK] 图像路径: {sample.image}")
            print(f"  [OK] 对话数量: {len(sample.conversations)}")
            print(f"  [OK] 元数据温度: {sample.metadata.temperature}")
            print(f"  [OK] 知识三元组数量: {len(sample.knowledge_triples)}")
            
            # 测试数据集构建器
            builder = MultimodalDatasetBuilder(output_dir="data/test")
            
            sample = builder.create_sample_with_environment(
                image_path="images/test_001.jpg",
                disease_name="白粉病",
                temperature=22.0,
                humidity=75.0,
                growth_stage="拔节期",
                location="山东济南"
            )
            
            print(f"  [OK] 创建样本 ID: {sample.id}")
            print(f"  [OK] 元数据: {sample.metadata.to_dict()}")
            
            return True
            
        except Exception as e:
            print(f"  [失败] {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _test_lora_config(self) -> bool:
        """测试 LoRA 微调配置"""
        print("\n[测试 5] LoRA 微调配置")
        print("-" * 50)
        
        try:
            from training.lora_config import (
                LoRAModule,
                LoRALinear,
                FullComponentLoRAConfig,
                create_qwen3vl_lora_config,
                count_lora_parameters
            )
            
            # 创建配置
            config = create_qwen3vl_lora_config(
                vision_r=8,
                adapter_r=8,
                language_r=16,
                learning_rate=1e-4
            )
            
            print(f"  [OK] 视觉编码器 LoRA 秩: {config.vision_config.r}")
            print(f"  [OK] 适配器 LoRA 秩: {config.adapter_config.r}")
            print(f"  [OK] 语言模型 LoRA 秩: {config.language_config.r}")
            print(f"  [OK] 学习率: {config.learning_rate}")
            
            # 测试 LoRA 模块
            lora_module = LoRAModule(
                in_features=768,
                out_features=768,
                r=8,
                lora_alpha=16
            ).to(self.device)
            
            x = torch.randn(2, 10, 768).to(self.device)
            with torch.no_grad():
                output = lora_module(x)
            
            print(f"  [OK] LoRA 输出维度: {output.shape}")
            
            # 测试 LoRA 线性层
            original_linear = nn.Linear(768, 768).to(self.device)
            lora_linear = LoRALinear(original_linear, r=8, lora_alpha=16).to(self.device)
            
            with torch.no_grad():
                output = lora_linear(x)
            
            print(f"  [OK] LoRA 线性层输出维度: {output.shape}")
            
            # 统计参数
            param_stats = count_lora_parameters(lora_linear)
            print(f"  [OK] 总参数: {param_stats['total_params']:,}")
            print(f"  [OK] LoRA 参数: {param_stats['lora_params']:,}")
            
            return True
            
        except Exception as e:
            print(f"  [失败] {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _test_uncertainty_loss(self) -> bool:
        """测试不确定性量化损失"""
        print("\n[测试 6] 不确定性量化损失")
        print("-" * 50)
        
        try:
            from training.uncertainty_loss import (
                HeteroscedasticUncertaintyLoss,
                ConfidenceCalibrationLoss,
                EnvironmentConflictLoss,
                UncertaintyQuantificationLoss,
                UncertaintyAwareDiagnosisHead,
                create_uncertainty_loss
            )
            
            batch_size = 4
            num_classes = 15
            
            # 测试异方差损失
            het_loss = HeteroscedasticUncertaintyLoss(num_classes=num_classes).to(self.device)
            
            logits = torch.randn(batch_size, num_classes).to(self.device)
            log_variance = torch.randn(batch_size, num_classes).to(self.device)
            targets = torch.randint(0, num_classes, (batch_size,)).to(self.device)
            
            loss, stats = het_loss(logits, log_variance, targets)
            print(f"  [OK] 异方差损失: {loss.item():.4f}")
            print(f"  [OK] 不确定性: {stats['uncertainty']:.4f}")
            
            # 测试置信度校准损失
            cal_loss = ConfidenceCalibrationLoss(learn_temperature=True).to(self.device)
            
            loss, stats = cal_loss(logits, targets)
            print(f"  [OK] 校准损失: {loss.item():.4f}")
            print(f"  [OK] ECE: {stats['ece']:.4f}")
            
            # 测试环境冲突损失
            conflict_loss = EnvironmentConflictLoss().to(self.device)
            
            vision_conf = torch.tensor([0.9, 0.8, 0.7, 0.6]).to(self.device)
            env_conf = torch.tensor([0.5, 0.8, 0.3, 0.9]).to(self.device)
            vision_pred = torch.tensor([1, 2, 3, 4]).to(self.device)
            env_pred = torch.tensor([1, 2, 1, 5]).to(self.device)
            
            loss, stats = conflict_loss(vision_conf, env_conf, vision_pred, env_pred)
            print(f"  [OK] 冲突损失: {loss.item():.4f}")
            print(f"  [OK] 冲突率: {stats['conflict_rate']:.4f}")
            
            # 测试综合损失
            total_loss = create_uncertainty_loss(num_classes=num_classes).to(self.device)
            
            loss, stats = total_loss(
                logits=logits,
                targets=targets,
                log_variance=log_variance,
                vision_confidence=vision_conf,
                environment_confidence=env_conf,
                vision_prediction=vision_pred,
                environment_prediction=env_pred
            )
            print(f"  [OK] 总损失: {loss.item():.4f}")
            
            # 测试不确定性感知诊断头
            diagnosis_head = UncertaintyAwareDiagnosisHead(
                input_dim=768, 
                num_classes=num_classes
            ).to(self.device)
            
            features = torch.randn(batch_size, 768).to(self.device)
            result = diagnosis_head(features)
            
            print(f"  [OK] Logits 维度: {result['logits'].shape}")
            print(f"  [OK] 置信度: {result['confidence']}")
            print(f"  [OK] 不确定性: {result['uncertainty']}")
            
            return True
            
        except Exception as e:
            print(f"  [失败] {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _test_end_to_end_integration(self) -> bool:
        """端到端集成测试"""
        print("\n[测试 7] 端到端集成测试")
        print("-" * 50)
        
        try:
            from fusion.deepstack_injection import create_deepstack_injection
            from fusion.cross_attention import create_cross_attention_model
            from fusion.environment_embedding import create_environment_embedding_branch
            from training.uncertainty_loss import UncertaintyAwareDiagnosisHead
            
            # 创建所有模块
            deepstack = create_deepstack_injection(
                vision_dims={'low': 1024, 'mid': 1024, 'high': 1024},
                llm_dim=4096
            ).to(self.device)
            
            cross_attn = create_cross_attention_model(
                text_dim=768,
                vision_dim=4096,  # 来自 DeepStack 输出
                num_heads=8,
                use_se=True
            ).to(self.device)
            
            env_branch = create_environment_embedding_branch(
                output_dim=768,
                hidden_dim=256
            ).to(self.device)
            
            diagnosis_head = UncertaintyAwareDiagnosisHead(
                input_dim=768,
                num_classes=15
            ).to(self.device)
            
            # 模拟输入数据
            batch_size = 2
            seq_len = 64
            
            # 1. DeepStack 特征注入
            low_features = torch.randn(batch_size, seq_len, 1024).to(self.device)
            mid_features = torch.randn(batch_size, seq_len, 1024).to(self.device)
            high_features = torch.randn(batch_size, seq_len, 1024).to(self.device)
            llm_hidden = torch.randn(batch_size, seq_len, 4096).to(self.device)
            
            with torch.no_grad():
                deepstack_result = deepstack(low_features, mid_features, high_features, llm_hidden)
            
            print(f"  [OK] Step 1 - DeepStack 输出: {deepstack_result['fused_features'].shape}")
            
            # 2. 环境数据嵌入
            with torch.no_grad():
                env_result = env_branch.forward(
                    temperature=torch.tensor([25.0, 20.0]).to(self.device),
                    humidity=torch.tensor([80.0, 60.0]).to(self.device),
                    growth_stage_id=torch.tensor([7, 5]).to(self.device)  # 抽穗期, 拔节期
                )
            
            print(f"  [OK] Step 2 - 环境嵌入: {env_result['environment_embedding'].shape}")
            
            # 3. 交叉注意力融合
            text_features = env_result['environment_embedding_3d'].expand(-1, seq_len, -1)
            vision_features = deepstack_result['fused_features']
            
            with torch.no_grad():
                cross_result = cross_attn(text_features, vision_features)
            
            print(f"  [OK] Step 3 - 交叉注意力输出: {cross_result['fused_features'].shape}")
            
            # 4. 诊断输出
            pooled_features = cross_result['fused_features'].mean(dim=1)
            
            with torch.no_grad():
                diagnosis_result = diagnosis_head(pooled_features)
            
            print(f"  [OK] Step 4 - 诊断 Logits: {diagnosis_result['logits'].shape}")
            print(f"  [OK] 置信度: {diagnosis_result['confidence']}")
            print(f"  [OK] 不确定性: {diagnosis_result['uncertainty']}")
            
            # 5. 预测结果
            predictions = diagnosis_result['probs'].argmax(dim=-1)
            print(f"  [OK] 预测类别: {predictions}")
            
            print("\n  [OK] 端到端集成测试通过!")
            
            return True
            
        except Exception as e:
            print(f"  [失败] {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _print_summary(self):
        """打印测试汇总"""
        print("\n" + "=" * 70)
        print("测试结果汇总")
        print("=" * 70)
        
        passed = sum(1 for v in self.test_results.values() if v)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        print("-" * 70)
        print(f"  总计: {passed}/{total} 测试通过")
        
        if passed == total:
            print("\n  🎉 所有测试通过! 多模态特征融合架构升级完成。")
        else:
            print(f"\n  ⚠️ 有 {total - passed} 个测试失败，请检查相关模块。")


def run_integration_tests():
    """运行集成测试"""
    tester = MultimodalFusionIntegrationTest()
    return tester.run_all_tests()


if __name__ == "__main__":
    run_integration_tests()

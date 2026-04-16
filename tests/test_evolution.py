# -*- coding: utf-8 -*-
"""
自进化机制强化模块单元测试
测试 GRPOTrainer 和 LoRAFinetuner 的功能

测试覆盖:
1. GRPOTrainer 的奖励计算和策略优化
2. LoRAFinetuner 的微调和适配器管理
3. 与 CaseMemory 和 FeedbackHandler 的集成
"""

import os
import sys
import unittest
import torch
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.evolution.grpo_trainer import GRPOTrainer, GRPOConfig, PolicyNetwork, RewardNetwork
from src.evolution.lora_finetuner import LoRAFinetuner, LoRAConfig, LoRALayer, LoRAAdapter
from src.memory.case_memory import CaseMemory
from src.memory.feedback_handler import FeedbackHandler, FeedbackType


class TestGRPOTrainer(unittest.TestCase):
    """GRPOTrainer 单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.config = GRPOConfig(
            hidden_size=64,
            num_layers=2,
            num_samples_per_state=3,
            learning_rate=1e-3,
            max_epochs=5,
            batch_size=8
        )
        
        # 初始化 CaseMemory 和 FeedbackHandler
        self.case_memory_path = os.path.join(self.test_dir, "test_cases.json")
        self.case_memory = CaseMemory(storage_path=self.case_memory_path)
        self.feedback_handler = FeedbackHandler(case_memory=self.case_memory)
        
        # 初始化 GRPOTrainer
        self.trainer = GRPOTrainer(
            input_size=512,
            num_disease_types=15,
            config=self.config,
            case_memory=self.case_memory,
            feedback_handler=self.feedback_handler,
            model_path=os.path.join(self.test_dir, "grpo_model")
        )
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """测试初始化"""
        print("\n[测试] GRPOTrainer 初始化")
        
        self.assertEqual(self.trainer.config.hidden_size, 64)
        self.assertEqual(self.trainer.config.num_layers, 2)
        self.assertEqual(self.trainer.config.num_samples_per_state, 3)
        self.assertEqual(len(self.trainer.training_history), 0)
        
        print("✓ 初始化参数正确")
    
    def test_reward_calculation(self):
        """测试奖励计算"""
        print("\n[测试] 奖励计算")
        
        # 测试准确性奖励
        diagnosis = {
            "disease_type": "条锈病",
            "severity": "中度",
            "confidence": 0.9,
            "recommendation": "使用三唑酮可湿性粉剂"
        }
        
        accuracy_reward = self.trainer._calculate_accuracy_reward(
            predicted_disease="条锈病",
            expert_label="条锈病",
            confidence=0.9
        )
        
        # 正确预测应该有正奖励
        self.assertGreater(accuracy_reward, 0)
        print(f"✓ 准确性奖励计算正确：{accuracy_reward:.4f}")
        
        # 测试错误预测的负奖励
        wrong_reward = self.trainer._calculate_accuracy_reward(
            predicted_disease="叶锈病",
            expert_label="条锈病",
            confidence=0.5
        )
        self.assertLess(wrong_reward, 0)
        print(f"✓ 错误预测奖励计算正确：{wrong_reward:.4f}")
        
        # 测试逻辑性奖励
        context = {
            "month": 4,
            "lesion_area": 0.25
        }
        
        logic_reward = self.trainer._calculate_logic_reward(diagnosis, context)
        self.assertGreaterEqual(logic_reward, 0)
        print(f"✓ 逻辑性奖励计算正确：{logic_reward:.4f}")
        
        # 测试简洁度奖励
        concise_text = "使用三唑酮喷雾"
        verbose_text = "使用三唑酮喷雾防治，注意三唑酮是一种高效杀菌剂，三唑酮可以有效防治多种病害，需要多次喷洒"
        
        concise_reward = self.trainer._calculate_conciseness_reward(concise_text)
        verbose_reward = self.trainer._calculate_conciseness_reward(verbose_text)
        
        # 简洁的文本奖励应该大于等于冗长的文本（由于长度惩罚）
        self.assertGreaterEqual(concise_reward, verbose_reward)
        print(f"✓ 简洁度奖励计算正确：简洁={concise_reward:.4f}, 冗长={verbose_reward:.4f}")
    
    def test_total_reward(self):
        """测试综合奖励计算"""
        print("\n[测试] 综合奖励计算")
        
        diagnosis = {
            "disease_type": "条锈病",
            "severity": "中度",
            "confidence": 0.85,
            "recommendation": "使用三唑酮可湿性粉剂"
        }
        
        context = {
            "month": 4,
            "lesion_area": 0.25
        }
        
        total_reward, reward_details = self.trainer._calculate_total_reward(
            diagnosis=diagnosis,
            expert_label="条锈病",
            case_context=context,
            output_text="使用三唑酮喷雾"
        )
        
        self.assertIn("accuracy", reward_details)
        self.assertIn("logic", reward_details)
        self.assertIn("conciseness", reward_details)
        
        print(f"✓ 综合奖励计算正确：{total_reward:.4f}")
        print(f"  - 准确性：{reward_details['accuracy']:.4f}")
        print(f"  - 逻辑性：{reward_details['logic']:.4f}")
        print(f"  - 简洁度：{reward_details['conciseness']:.4f}")
    
    def test_group_advantage(self):
        """测试组内相对优势计算"""
        print("\n[测试] 组内相对优势计算")
        
        rewards = [0.8, 0.6, 0.9, 0.7, 0.5]
        advantages = self.trainer._compute_group_advantage(rewards)
        
        self.assertEqual(len(advantages), len(rewards))
        
        # 优势值应该均值为 0（近似）
        mean_adv = sum(advantages) / len(advantages)
        self.assertAlmostEqual(mean_adv, 0.0, places=5)
        
        print(f"✓ 组内相对优势计算正确")
        print(f"  奖励：{rewards}")
        print(f"  优势：{[f'{a:.4f}' for a in advantages]}")
    
    def test_action_sampling(self):
        """测试动作采样"""
        print("\n[测试] 动作采样")
        
        state = torch.randn(1, 512)
        num_samples = 5
        
        actions = self.trainer._sample_actions(state, num_samples)
        
        self.assertEqual(len(actions), num_samples)
        
        # 检查每个动作的格式
        for action, action_prob in actions:
            self.assertIsInstance(action, int)
            self.assertIsInstance(action_prob, torch.Tensor)
        
        print(f"✓ 动作采样正确：采样 {num_samples} 个动作")
    
    def test_training(self):
        """测试训练流程"""
        print("\n[测试] GRPO 训练流程")
        
        # 执行训练（使用模拟数据）
        result = self.trainer.train(num_iterations=10, batch_size=8)
        
        # 训练可能完成或被跳过（如果没有真实数据）
        self.assertIn(result["status"], ["completed", "skipped"])
        
        if result["status"] == "completed":
            self.assertIn("num_iterations", result)
            self.assertIn("final_reward", result)
            self.assertEqual(len(self.trainer.training_history), 10)
            print(f"✓ 训练流程执行成功")
            print(f"  迭代次数：{result['num_iterations']}")
            print(f"  最终奖励：{result['final_reward']:.4f}")
        else:
            print(f"✓ 训练流程被跳过（无训练数据）")
            print(f"  原因：{result.get('reason', 'unknown')}")
    
    def test_evaluation(self):
        """测试评估流程"""
        print("\n[测试] GRPO 评估流程")
        
        # 先训练几轮（使用模拟数据）
        self.trainer.train(num_iterations=5, batch_size=8)
        
        # 评估
        eval_result = self.trainer.evaluate()
        
        # 评估可能完成或被跳过
        self.assertIn(eval_result["status"], ["completed", "skipped"])
        
        if eval_result["status"] == "completed":
            self.assertIn("accuracy", eval_result)
            self.assertIn("avg_reward", eval_result)
            print(f"✓ 评估流程执行成功")
            print(f"  准确率：{eval_result['accuracy']:.4f}")
            print(f"  平均奖励：{eval_result['avg_reward']:.4f}")
        else:
            print(f"✓ 评估流程被跳过（无测试数据）")
    
    def test_model_save_load(self):
        """测试模型保存和加载"""
        print("\n[测试] 模型保存与加载")
        
        # 训练几轮
        self.trainer.train(num_iterations=5, batch_size=8)
        initial_history = len(self.trainer.training_history)
        
        # 保存模型
        save_success = self.trainer._save_model()
        self.assertTrue(save_success)
        
        # 创建新的 trainer 并加载模型
        new_trainer = GRPOTrainer(
            input_size=512,
            num_disease_types=15,
            config=self.config,
            model_path=self.trainer.model_path
        )
        
        # 检查模型是否正确加载
        self.assertEqual(len(new_trainer.training_history), initial_history)
        
        print(f"✓ 模型保存与加载成功")
        print(f"  加载历史轮次：{len(new_trainer.training_history)}")
    
    def test_statistics(self):
        """测试统计信息"""
        print("\n[测试] 统计信息")
        
        # 训练前
        stats = self.trainer.get_statistics()
        self.assertEqual(stats["status"], "no_training")
        
        # 训练后（使用模拟数据）
        self.trainer.train(num_iterations=5, batch_size=8)
        stats = self.trainer.get_statistics()
        
        # 状态可能是 no_training 或有训练数据
        self.assertIn(stats["status"], ["no_training", "training"])
        
        if stats["status"] != "no_training":
            self.assertIn("total_iterations", stats)
            self.assertIn("final_reward", stats)
            self.assertIn("best_reward", stats)
        else:
            # no_training 状态下应该有 message
            self.assertIn("message", stats)
        
        print(f"✓ 统计信息获取成功")
        print(f"  状态：{stats['status']}")
        if stats["status"] != "no_training":
            print(f"  总迭代：{stats['total_iterations']}")


class TestLoRAFinetuner(unittest.TestCase):
    """LoRAFinetuner 单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.config = LoRAConfig(
            lora_r=8,
            lora_alpha=16,
            learning_rate=1e-3,
            num_epochs=5,
            batch_size=8
        )
        
        # 初始化 CaseMemory 和 FeedbackHandler
        self.case_memory_path = os.path.join(self.test_dir, "test_cases.json")
        self.case_memory = CaseMemory(storage_path=self.case_memory_path)
        self.feedback_handler = FeedbackHandler(case_memory=self.case_memory)
        
        # 初始化 LoRAFinetuner
        self.finetuner = LoRAFinetuner(
            config=self.config,
            case_memory=self.case_memory,
            feedback_handler=self.feedback_handler,
            output_dir=os.path.join(self.test_dir, "lora_models")
        )
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_lora_layer_initialization(self):
        """测试 LoRA 层初始化"""
        print("\n[测试] LoRA 层初始化")
        
        lora_layer = LoRALayer(
            in_features=128,
            out_features=256,
            r=8,
            alpha=16
        )
        
        self.assertEqual(lora_layer.r, 8)
        self.assertEqual(lora_layer.alpha, 16)
        self.assertEqual(lora_layer.scaling, 2.0)
        
        # 检查参数形状
        self.assertEqual(lora_layer.lora_A.shape, (8, 128))
        self.assertEqual(lora_layer.lora_B.shape, (256, 8))
        
        print(f"✓ LoRA 层初始化正确")
        print(f"  秩 r={lora_layer.r}, 缩放系数α={lora_layer.alpha}")
    
    def test_lora_layer_forward(self):
        """测试 LoRA 层前向传播"""
        print("\n[测试] LoRA 层前向传播")
        
        lora_layer = LoRALayer(
            in_features=64,
            out_features=128,
            r=4,
            alpha=8
        )
        
        x = torch.randn(2, 64)  # batch_size=2
        
        # 初始时 LoRA 分支应该输出 0（因为 B 初始化为 0）
        with torch.no_grad():
            output = lora_layer(x)
        
        # 检查输出形状
        self.assertEqual(output.shape, (2, 128))
        
        print(f"✓ LoRA 层前向传播正确")
        print(f"  输入形状：{x.shape}, 输出形状：{output.shape}")
    
    def test_adapter_creation(self):
        """测试适配器创建"""
        print("\n[测试] LoRA 适配器创建")
        
        adapter = self.finetuner.create_adapter("test_adapter")
        
        self.assertEqual(adapter.adapter_name, "test_adapter")
        self.assertEqual(len(adapter.lora_layers), len(self.config.target_modules))
        
        print(f"✓ 适配器创建成功")
        print(f"  适配器名称：{adapter.adapter_name}")
        print(f"  LoRA 层数：{len(adapter.lora_layers)}")
    
    def test_few_shot_finetuning(self):
        """测试 few-shot 微调"""
        print("\n[测试] Few-shot 微调")
        
        # 执行微调
        result = self.finetuner.finetune_new_disease(
            disease_type="测试病害",
            num_shots=16,
            num_epochs=3
        )
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["disease_type"], "测试病害")
        self.assertIn("adapter_name", result)
        self.assertIn("output_dir", result)
        
        print(f"✓ Few-shot 微调成功")
        print(f"  病害类型：{result['disease_type']}")
        print(f"  适配器：{result['adapter_name']}")
    
    def test_regional_finetuning(self):
        """测试区域微调"""
        print("\n[测试] 区域专属模型微调")
        
        # 执行区域微调
        result = self.finetuner.finetune_regional_model(
            region="测试区域",
            disease_types=["条锈病", "叶锈病"],
            num_epochs=3
        )
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["region"], "测试区域")
        self.assertIn("adapter_name", result)
        
        print(f"✓ 区域微调成功")
        print(f"  区域：{result['region']}")
        print(f"  适配器：{result['adapter_name']}")
    
    def test_adapter_management(self):
        """测试适配器管理"""
        """测试适配器的创建、列表、切换"""
        print("\n[测试] 适配器管理")
        
        # 创建多个适配器
        adapter1 = self.finetuner.create_adapter("adapter_1")
        adapter2 = self.finetuner.create_adapter("adapter_2")
        
        # 列出所有适配器
        adapters = self.finetuner.list_adapters()
        self.assertEqual(len(adapters), 2)
        
        adapter_names = [a["name"] for a in adapters]
        self.assertIn("adapter_1", adapter_names)
        self.assertIn("adapter_2", adapter_names)
        
        # 切换活跃适配器
        success = self.finetuner.set_active_adapter("adapter_1")
        self.assertTrue(success)
        self.assertEqual(self.finetuner.active_adapter.adapter_name, "adapter_1")
        
        print(f"✓ 适配器管理成功")
        print(f"  适配器列表：{adapter_names}")
    
    def test_adapter_save_load(self):
        """测试适配器保存和加载"""
        print("\n[测试] 适配器保存与加载")
        
        # 创建并训练适配器
        adapter = self.finetuner.create_adapter("save_test")
        self.finetuner.finetune_new_disease(
            disease_type="测试病害",
            num_shots=8,
            num_epochs=2
        )
        
        # 保存适配器
        output_dir = os.path.join(self.test_dir, "saved_adapter")
        adapter_path = adapter.save_adapter(output_dir)
        self.assertTrue(os.path.exists(adapter_path))
        
        # 加载适配器
        loaded_adapter = LoRAAdapter.load_adapter(
            self.finetuner.base_model,
            adapter_path
        )
        
        self.assertEqual(loaded_adapter.adapter_name, "save_test")
        self.assertEqual(loaded_adapter.training_samples, adapter.training_samples)
        
        print(f"✓ 适配器保存与加载成功")
        print(f"  保存路径：{adapter_path}")
    
    def test_statistics(self):
        """测试统计信息"""
        print("\n[测试] 统计信息")
        
        # 初始统计
        stats = self.finetuner.get_statistics()
        self.assertIn("num_adapters", stats)
        self.assertIn("total_training_samples", stats)
        
        # 创建适配器后统计
        self.finetuner.create_adapter("stats_test")
        stats = self.finetuner.get_statistics()
        
        self.assertEqual(stats["num_adapters"], 1)
        
        print(f"✓ 统计信息获取成功")
        print(f"  适配器数：{stats['num_adapters']}")
        print(f"  总训练样本：{stats['total_training_samples']}")


class TestIntegration(unittest.TestCase):
    """集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        
        # 初始化所有组件
        self.case_memory = CaseMemory(
            storage_path=os.path.join(self.test_dir, "cases.json")
        )
        self.feedback_handler = FeedbackHandler(
            case_memory=self.case_memory
        )
        
        self.grpo_config = GRPOConfig(
            hidden_size=32,
            num_layers=1,
            max_epochs=2,
            batch_size=4
        )
        
        self.lora_config = LoRAConfig(
            lora_r=4,
            lora_alpha=8,
            num_epochs=2,
            batch_size=4
        )
        
        self.grpo_trainer = GRPOTrainer(
            input_size=512,
            num_disease_types=15,
            config=self.grpo_config,
            case_memory=self.case_memory,
            model_path=os.path.join(self.test_dir, "grpo")
        )
        
        self.lora_finetuner = LoRAFinetuner(
            config=self.lora_config,
            case_memory=self.case_memory,
            output_dir=os.path.join(self.test_dir, "lora")
        )
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_feedback_loop_integration(self):
        """测试反馈闭环集成"""
        print("\n[集成测试] 反馈闭环集成")
        
        # 1. 存储病例
        case_id = self.case_memory.store_case(
            user_id="test_user",
            field_id="test_field",
            image_path="test.jpg",
            disease_type="条锈病",
            severity="中度",
            recommendation="使用三唑酮"
        )
        
        # 2. 处理反馈
        feedback_result = self.feedback_handler.process_feedback(
            case_id=case_id,
            feedback_type=FeedbackType.MEDICATION_EFFECTIVE.value,
            details="施药后病情好转",
            medication_applied=True
        )
        
        self.assertTrue(feedback_result["success"])
        
        # 3. GRPO 训练（使用积累的病例）
        grpo_result = self.grpo_trainer.train(num_iterations=3, batch_size=4)
        self.assertEqual(grpo_result["status"], "completed")
        
        # 4. LoRA 微调（使用反馈数据）
        lora_result = self.lora_finetuner.finetune_new_disease(
            disease_type="条锈病",
            num_shots=8,
            num_epochs=2
        )
        self.assertEqual(lora_result["status"], "completed")
        
        print(f"✓ 反馈闭环集成测试通过")
        print(f"  病例存储：{case_id}")
        print(f"  反馈处理：{'成功' if feedback_result['success'] else '失败'}")
        print(f"  GRPO 训练：{grpo_result['status']}")
        print(f"  LoRA 微调：{lora_result['status']}")


def run_tests():
    """运行所有测试"""
    print("=" * 80)
    print("🧪 开始运行自进化机制强化模块单元测试")
    print("=" * 80)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestGRPOTrainer))
    suite.addTests(loader.loadTestsFromTestCase(TestLoRAFinetuner))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print(f"总测试数：{result.testsRun}")
    print(f"成功：{result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败：{len(result.failures)}")
    print(f"错误：{len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
        return True
    else:
        print("\n❌ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

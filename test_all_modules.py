# -*- coding: utf-8 -*-
"""
综合测试脚本 - 验证所有新开发模块的功能
"""
import sys
import os

# 添加src到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_all_modules():
    """测试所有模块"""
    print("=" * 70)
    print("🧪 IWDDA 系统模块综合测试")
    print("=" * 70)
    
    test_results = {}
    
    # 1. 测试动态蛇形卷积
    print("\n" + "=" * 70)
    print("1️⃣ 测试动态蛇形卷积 (DySnakeConv)")
    print("=" * 70)
    try:
        from vision.dy_snake_conv import DySnakeConv, C2f_DySnake
        import torch
        
        x = torch.randn(2, 64, 32, 32)
        dysnake = DySnakeConv(64, 128)
        out = dysnake(x)
        assert out.shape == torch.Size([2, 128, 32, 32])
        
        c2f = C2f_DySnake(64, 128, n=2)
        out2 = c2f(x)
        assert out2.shape == torch.Size([2, 128, 32, 32])
        
        test_results["DySnakeConv"] = "✅ 通过"
        print("✅ 动态蛇形卷积模块测试通过")
    except Exception as e:
        test_results["DySnakeConv"] = f"❌ 失败: {e}"
        print(f"❌ 动态蛇形卷积模块测试失败: {e}")
    
    # 2. 测试SPPELAN
    print("\n" + "=" * 70)
    print("2️⃣ 测试 SPPELAN 模块")
    print("=" * 70)
    try:
        from vision.sppelan_module import SPPELAN, ELANBlock, MultiScaleFusion
        import torch
        
        x = torch.randn(2, 256, 64, 64)
        sppelan = SPPELAN(256, 512)
        out = sppelan(x)
        assert out.shape == torch.Size([2, 512, 64, 64])
        
        elan = ELANBlock(256, 512)
        out2 = elan(x)
        assert out2.shape == torch.Size([2, 512, 64, 64])
        
        features = [
            torch.randn(2, 128, 64, 64),
            torch.randn(2, 256, 32, 32),
            torch.randn(2, 512, 16, 16)
        ]
        fusion = MultiScaleFusion([128, 256, 512], 256)
        out3 = fusion(features, target_size=(64, 64))
        assert out3.shape == torch.Size([2, 256, 64, 64])
        
        test_results["SPPELAN"] = "✅ 通过"
        print("✅ SPPELAN模块测试通过")
    except Exception as e:
        test_results["SPPELAN"] = f"❌ 失败: {e}"
        print(f"❌ SPPELAN模块测试失败: {e}")
    
    # 3. 测试STA
    print("\n" + "=" * 70)
    print("3️⃣ 测试超级令牌注意力 (STA)")
    print("=" * 70)
    try:
        from vision.sta_module import SuperTokenAttention, STABlock
        import torch
        
        x = torch.randn(2, 256, 32, 32)
        sta = SuperTokenAttention(dim=256, num_heads=8, num_super_tokens=4)
        out = sta(x)
        assert out.shape == torch.Size([2, 256, 32, 32])
        
        sta_block = STABlock(256, num_heads=8, num_super_tokens=4)
        out2 = sta_block(x)
        assert out2.shape == torch.Size([2, 256, 32, 32])
        
        test_results["STA"] = "✅ 通过"
        print("✅ STA模块测试通过")
    except Exception as e:
        test_results["STA"] = f"❌ 失败: {e}"
        print(f"❌ STA模块测试失败: {e}")
    
    # 4. 测试KGA
    print("\n" + "=" * 70)
    print("4️⃣ 测试知识引导注意力 (KGA)")
    print("=" * 70)
    try:
        from fusion.kga_module import KnowledgeGuidedAttention, KADFusion
        from fusion.cross_attention import CrossModalAttention
        import torch
        
        # 使用兼容的维度: vision_dim=256, knowledge_dim=256, hidden_dim=256
        vision_features = torch.randn(2, 16, 256)
        knowledge_embeddings = torch.randn(2, 8, 256)
        
        kga = KnowledgeGuidedAttention(vision_dim=256, knowledge_dim=256, num_heads=8, hidden_dim=256)
        out = kga(vision_features, knowledge_embeddings)
        assert out.shape == vision_features.shape
        
        text_features = torch.randn(2, 768)
        cross_attn = CrossModalAttention(text_dim=768, vision_dim=256, num_heads=8, hidden_dim=256)
        out2 = cross_attn(text_features, vision_features)
        assert out2.shape[0] == text_features.shape[0]  # batch size匹配
        
        kad_fusion = KADFusion(vision_dim=256, text_dim=768, knowledge_dim=256)
        out3 = kad_fusion(vision_features, text_features, knowledge_embeddings)
        assert out3.shape == vision_features.shape
        
        test_results["KGA"] = "✅ 通过"
        print("✅ KGA模块测试通过")
    except Exception as e:
        test_results["KGA"] = f"❌ 失败: {e}"
        print(f"❌ KGA模块测试失败: {e}")
    
    # 5. 测试经验回放
    print("\n" + "=" * 70)
    print("5️⃣ 测试经验回放 (Experience Replay)")
    print("=" * 70)
    try:
        from action.experience_replay import ExperienceReplayBuffer
        import shutil
        
        buffer = ExperienceReplayBuffer(
            capacity=100,
            storage_dir="data/test_replay"
        )
        
        # 添加测试经验
        for i in range(10):
            buffer.add_experience(
                image_path=f"test_{i}.jpg",
                label="条锈病" if i % 2 == 0 else "白粉病",
                confidence=0.8 + i * 0.01
            )
        
        assert len(buffer) == 10
        
        # 测试采样
        samples, indices = buffer.sample(5, strategy="random")
        assert len(samples) == 5
        
        # 测试原型样本
        prototypes = buffer.get_prototype_samples("条锈病", num_samples=3)
        assert len(prototypes) <= 3
        
        # 清理
        buffer.clear()
        if os.path.exists("data/test_replay"):
            shutil.rmtree("data/test_replay")
        
        test_results["ExperienceReplay"] = "✅ 通过"
        print("✅ 经验回放模块测试通过")
    except Exception as e:
        test_results["ExperienceReplay"] = f"❌ 失败: {e}"
        print(f"❌ 经验回放模块测试失败: {e}")
    
    # 6. 测试人机协同
    print("\n" + "=" * 70)
    print("6️⃣ 测试人机协同反馈闭环 (Human-in-the-Loop)")
    print("=" * 70)
    try:
        from action.human_in_the_loop import HumanInTheLoop
        import shutil
        
        hitl = HumanInTheLoop(
            feedback_dir="data/test_hitl",
            auto_flag_threshold=0.6
        )
        
        # 测试高置信度预测（不需要审核）
        record1 = hitl.submit_prediction(
            image_path="test1.jpg",
            system_diagnosis="条锈病",
            system_confidence=0.92
        )
        assert record1 is None  # 高置信度不需要审核
        
        # 测试低置信度预测（需要审核）
        record2 = hitl.submit_prediction(
            image_path="test2.jpg",
            system_diagnosis="白粉病",
            system_confidence=0.45
        )
        assert record2 is not None  # 低置信度需要审核
        
        # 提交反馈
        hitl.submit_feedback(
            record_id=record2.id,
            user_correction="白粉病",
            user_comments="诊断正确"
        )
        
        # 获取统计
        stats = hitl.get_feedback_statistics()
        assert stats["total_records"] == 1
        
        # 清理
        if os.path.exists("data/test_hitl"):
            shutil.rmtree("data/test_hitl")
        
        test_results["HumanInTheLoop"] = "✅ 通过"
        print("✅ 人机协同模块测试通过")
    except Exception as e:
        test_results["HumanInTheLoop"] = f"❌ 失败: {e}"
        print(f"❌ 人机协同模块测试失败: {e}")
    
    # 打印测试总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    passed = sum(1 for v in test_results.values() if v.startswith("✅"))
    total = len(test_results)
    
    for module, result in test_results.items():
        print(f"{module:20s}: {result}")
    
    print("\n" + "=" * 70)
    print(f"总计: {passed}/{total} 个模块通过测试")
    print("=" * 70)
    
    if passed == total:
        print("🎉 所有模块测试通过！系统功能完整。")
        return True
    else:
        print("⚠️ 部分模块测试失败，请检查错误信息。")
        return False


if __name__ == "__main__":
    success = test_all_modules()
    sys.exit(0 if success else 1)

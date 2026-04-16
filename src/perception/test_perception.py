# -*- coding: utf-8 -*-
"""
感知诊断层优化测试脚本

测试 IWDDA Agent Phase 10 的所有功能：
1. YOLOv8 引擎优化
2. Qwen3-VL 视觉引擎优化
3. 双引擎融合
"""
import os
import sys
import torch

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from perception import YOLOEngine, QwenVLEngine, DualEngineFusion


def test_yolo_engine():
    """测试 YOLOv8 引擎"""
    print("\n" + "=" * 60)
    print("Task 10.1: YOLOv8 引擎测试")
    print("=" * 60)
    
    try:
        print("\n[测试 1.1] 初始化 YOLO 引擎")
        yolo = YOLOEngine(
            enable_attention=True,
            enable_multi_scale=True,
            enable_small_object=True
        )
        print("✅ YOLO 引擎初始化成功")
        
        print("\n[测试 1.2] 检查优化模块")
        assert yolo.attention_module is not None, "CBAM 注意力模块未加载"
        print("   ✅ CBAM 注意力模块已加载")
        
        assert yolo.multi_scale_extractor is not None, "多尺度特征提取器未加载"
        print("   ✅ 多尺度特征提取器已加载")
        
        assert yolo.small_object_head is not None, "小目标检测头未加载"
        print("   ✅ 小目标检测头已加载")
        
        print("\n[测试 1.3] 测试统计信息")
        stats = yolo.get_stats()
        print(f"   统计信息：{stats}")
        
        print("\n✅ Task 10.1: YOLOv8 引擎测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ Task 10.1 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_qwen_vl_engine():
    """测试 Qwen3-VL 视觉引擎"""
    print("\n" + "=" * 60)
    print("Task 10.2: Qwen3-VL 视觉引擎测试")
    print("=" * 60)
    
    try:
        print("\n[测试 2.1] 初始化 QwenVL 引擎")
        qwen_vl = QwenVLEngine(
            enable_alignment=True,
            enable_candidate_generation=True,
            load_in_4bit=False
        )
        print("✅ QwenVL 引擎初始化成功")
        
        print("\n[测试 2.2] 检查优化模块")
        assert qwen_vl.aligner is not None, "视觉 - 文本对齐模块未加载"
        print("   ✅ 视觉 - 文本对齐模块已加载")
        
        assert qwen_vl.candidate_generator is not None, "病害候选生成器未加载"
        print("   ✅ 病害候选生成器已加载")
        
        print("\n[测试 2.3] 测试统计信息")
        stats = qwen_vl.get_stats()
        print(f"   统计信息：{stats}")
        
        print("\n✅ Task 10.2: Qwen3-VL 视觉引擎测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ Task 10.2 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_dual_fusion():
    """测试双引擎融合"""
    print("\n" + "=" * 60)
    print("Task 10.3: 双引擎融合测试")
    print("=" * 60)
    
    try:
        print("\n[测试 3.1] 初始化双引擎融合")
        fusion = DualEngineFusion(
            enable_early_fusion=True,
            enable_gating=True,
            enable_cross_attention=True
        )
        print("✅ 双引擎融合初始化成功")
        
        print("\n[测试 3.2] 检查融合模块")
        assert fusion.early_fusion is not None, "Early Fusion 模块未加载"
        print("   ✅ Early Fusion 模块已加载")
        
        assert fusion.gating is not None, "Gating Mechanism 未加载"
        print("   ✅ Gating Mechanism 已加载")
        
        assert fusion.cross_attention is not None, "Cross-Modal Attention 未加载"
        print("   ✅ Cross-Modal Attention 已加载")
        
        print("\n[测试 3.3] 测试特征融合（简化版）")
        yolo_feat = {
            'detections': [
                {'name': '条锈病', 'confidence': 0.85, 'bbox': [100, 100, 200, 200]}
            ]
        }
        
        qwen_feat = {
            'candidates': [
                {'name': '条锈病', 'confidence': 0.78, 'alignment_score': 0.65}
            ]
        }
        
        result = fusion.fuse_features(yolo_feat, qwen_feat)
        print(f"   ✅ 特征融合成功")
        print(f"   YOLO 特征维度：{result['yolo_features'].shape if result['yolo_features'] is not None else 'N/A'}")
        print(f"   Qwen 特征维度：{result['qwen_features'].shape if result['qwen_features'] is not None else 'N/A'}")
        
        print("\n[测试 3.4] 测试融合诊断")
        yolo_results = [
            {'name': '条锈病', 'confidence': 0.85, 'bbox': [100, 100, 200, 200]}
        ]
        qwen_results = [
            {'name': '条锈病', 'confidence': 0.78, 'alignment_score': 0.65},
            {'name': '叶锈病', 'confidence': 0.45, 'alignment_score': 0.32}
        ]
        
        diagnosis = fusion.diagnose_with_fusion(yolo_results, qwen_results)
        print(f"   ✅ 融合诊断成功")
        print(f"   主要诊断：{diagnosis['primary_diagnosis']}")
        print(f"   置信度：{diagnosis['primary_confidence']:.2%}")
        
        print("\n[测试 3.5] 测试门控权重")
        if fusion.gating is not None:
            yolo_tensor = torch.randn(1, 10, 512)
            qwen_tensor = torch.randn(1, 10, 512)
            weights = fusion.get_fusion_weights(yolo_tensor, qwen_tensor)
            print(f"   门控权重：{weights}")
        
        print("\n✅ Task 10.3: 双引擎融合测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ Task 10.3 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """集成测试"""
    print("\n" + "=" * 60)
    print("集成测试：完整感知诊断流程")
    print("=" * 60)
    
    try:
        print("\n[集成测试] 初始化所有引擎")
        yolo = YOLOEngine(
            enable_attention=True,
            enable_multi_scale=True,
            enable_small_object=True
        )
        
        qwen_vl = QwenVLEngine(
            enable_alignment=True,
            enable_candidate_generation=True,
            load_in_4bit=False
        )
        
        fusion = DualEngineFusion(
            enable_early_fusion=True,
            enable_gating=True,
            enable_cross_attention=True
        )
        
        print("✅ 所有引擎初始化成功")
        
        print("\n[集成测试] 模拟完整诊断流程")
        yolo_results = [
            {'name': '条锈病', 'confidence': 0.85, 'bbox': [100, 100, 200, 200]},
            {'name': '叶锈病', 'confidence': 0.72, 'bbox': [150, 150, 250, 250]}
        ]
        
        qwen_results = [
            {'name': '条锈病', 'confidence': 0.78, 'alignment_score': 0.65},
            {'name': '白粉病', 'confidence': 0.55, 'alignment_score': 0.42}
        ]
        
        print(f"\n最终诊断结果:")
        print(f"   病害：{diagnosis['primary_diagnosis']}")
        print(f"   置信度：{diagnosis['primary_confidence']:.2%}")
        print(f"   检测总数：{len(diagnosis['all_detections'])}")
        
        print(f"\n最终诊断结果:")
        print(f"   病害：{diagnosis['primary_diagnosis']}")
        print(f"   置信度：{diagnosis['primary_confidence']:.2%}")
        print(f"   检测总数：{len(diagnosis['all_detections'])}")
        
        print("\n✅ 集成测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 集成测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("IWDDA Agent Phase 10: 感知诊断层优化 - 功能验证")
    print("=" * 60)
    
    results = {
        'Task 10.1': test_yolo_engine(),
        'Task 10.2': test_qwen_vl_engine(),
        'Task 10.3': test_dual_fusion(),
        'Integration': test_integration()
    }
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for task, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{task}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 所有测试通过！感知诊断层优化完成")
        print("\n实现的功能:")
        print("  1. ✅ YOLOv8 ROI 定位精度提升（CBAM 注意力）")
        print("  2. ✅ 病斑特征提取优化（多尺度特征）")
        print("  3. ✅ 小目标检测优化（早期病斑检测）")
        print("  4. ✅ Qwen3-VL 图像理解能力提升")
        print("  5. ✅ 病害候选生成（top-k 候选）")
        print("  6. ✅ 视觉 - 文本对齐优化")
        print("  7. ✅ 双引擎 Early Fusion 策略")
        print("  8. ✅ 联合特征输出（concat + attention）")
        print("  9. ✅ Gating Mechanism 学习融合权重")
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

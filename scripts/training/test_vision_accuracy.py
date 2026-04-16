# -*- coding: utf-8 -*-
"""
视觉检测精度测试脚本
测试小麦病害检测模型的性能
"""
import os
import sys
import glob
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_vision_accuracy():
    """测试视觉检测精度"""
    print("=" * 60)
    print("🌾 小麦病害视觉检测精度测试")
    print("=" * 60)
    
    # 1. 初始化视觉引擎
    print("\n[1/4] 初始化视觉引擎...")
    from src.vision.vision_engine import VisionAgent
    
    # 尝试加载专用模型
    model_path = os.path.join(os.getcwd(), "models", "yolov8_wheat.pt")
    if os.path.exists(model_path):
        print(f"   使用模型: {model_path}")
        vision = VisionAgent(model_path=model_path)
    else:
        print("   未找到专用模型，使用自动搜索...")
        vision = VisionAgent()
    
    # 2. 查找测试图像
    print("\n[2/4] 查找测试图像...")
    test_dirs = [
        os.path.join(os.getcwd(), "datasets", "wheat_data", "images", "train"),
        os.path.join(os.getcwd(), "datasets", "wheat_data", "images", "test"),
        os.path.join(os.getcwd(), "datasets", "wheat_data", "images", "val"),
    ]
    
    test_images = []
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            images = glob.glob(os.path.join(test_dir, "*.png")) + \
                   glob.glob(os.path.join(test_dir, "*.jpg"))
            test_images.extend(images)
    
    if not test_images:
        print("   ❌ 未找到测试图像")
        return
    
    # 选择前5张图像进行测试
    test_images = test_images[:5]
    print(f"   找到 {len(test_images)} 张测试图像")
    for i, img in enumerate(test_images):
        print(f"   {i+1}. {os.path.basename(img)}")
    
    # 3. 执行检测测试
    print("\n[3/4] 执行检测测试...")
    
    all_results = []
    for i, image_path in enumerate(test_images):
        print(f"\n   测试图像 {i+1}/{len(test_images)}: {os.path.basename(image_path)}")
        
        # 使用不同置信度阈值进行测试
        for conf_thresh in [0.25, 0.5, 0.75]:
            results = vision.detect(image_path, conf_threshold=conf_thresh)
            count = len(results)
            avg_conf = sum(r['confidence'] for r in results) / count if count > 0 else 0
            
            print(f"      阈值 {conf_thresh:.2f}: 检测到 {count} 个目标, 平均置信度: {avg_conf:.2%}")
            
            if results:
                for j, r in enumerate(results[:3]):  # 只显示前3个
                    print(f"         - {r['name']}: {r['confidence']:.2%}")
        
        # 使用默认阈值保存详细结果
        results = vision.detect(image_path, conf_threshold=0.25)
        all_results.append({
            'image': os.path.basename(image_path),
            'detections': results
        })
    
    # 4. 生成测试报告
    print("\n[4/4] 生成测试报告...")
    
    total_detections = sum(len(r['detections']) for r in all_results)
    avg_confidence = sum(
        d['confidence'] 
        for r in all_results 
        for d in r['detections']
    ) / total_detections if total_detections > 0 else 0
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"测试图像数: {len(test_images)}")
    print(f"总检测数: {total_detections}")
    print(f"平均每图检测: {total_detections / len(test_images):.1f}")
    print(f"平均置信度: {avg_confidence:.2%}")
    
    # 检测到的病害类型统计
    disease_counts = {}
    for r in all_results:
        for d in r['detections']:
            name = d['name']
            disease_counts[name] = disease_counts.get(name, 0) + 1
    
    if disease_counts:
        print("\n检测到的病害类型:")
        for disease, count in sorted(disease_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {disease}: {count} 次")
    
    # 保存详细报告
    report_path = os.path.join(os.getcwd(), "vision_test_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("🌾 小麦病害视觉检测测试报告\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"测试图像数: {len(test_images)}\n")
        f.write(f"总检测数: {total_detections}\n")
        f.write(f"平均置信度: {avg_confidence:.2%}\n\n")
        
        f.write("详细检测结果:\n")
        for r in all_results:
            f.write(f"\n图像: {r['image']}\n")
            if r['detections']:
                for d in r['detections']:
                    f.write(f"  - {d['name']}: {d['confidence']:.2%} @ {d['bbox']}\n")
            else:
                f.write("  未检测到病害\n")
    
    print(f"\n✅ 详细报告已保存: {report_path}")
    print("=" * 60)
    
    return all_results

if __name__ == "__main__":
    try:
        test_vision_accuracy()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

# -*- coding: utf-8 -*-
"""
验证和修复模型文件
"""
import os
import sys
import torch
from ultralytics import YOLO

def verify_and_fix_model():
    """验证模型文件并修复"""
    print("=" * 60)
    print("🔍 模型验证和修复工具")
    print("=" * 60)
    
    # 检查所有可用的模型文件
    model_paths = [
        os.path.join(os.getcwd(), "models", "yolov8_wheat.pt"),
        os.path.join(os.getcwd(), "runs", "detect", "runs", "detect", "runs", "train", "wheat_evolution_v2", "weights", "best.pt"),
        os.path.join(os.getcwd(), "runs", "detect", "runs", "detect", "runs", "train", "wheat_evolution", "weights", "best.pt"),
        os.path.join(os.getcwd(), "runs", "detect", "runs", "train", "wheat_experiment2", "weights", "best.pt"),
    ]
    
    print("\n[1/3] 检查可用模型...")
    available_models = []
    for path in model_paths:
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"   ✅ {path}")
            print(f"      大小: {size_mb:.1f} MB")
            available_models.append(path)
        else:
            print(f"   ❌ {path}")
    
    if not available_models:
        print("\n   没有找到可用的模型文件！")
        return False
    
    # 尝试加载每个模型
    print("\n[2/3] 验证模型加载...")
    working_models = []
    
    for path in available_models:
        print(f"\n   测试: {os.path.basename(path)}")
        try:
            model = YOLO(path)
            print(f"   ✅ 加载成功")
            
            # 检查模型类别
            if hasattr(model, 'names'):
                num_classes = len(model.names)
                print(f"   📊 类别数: {num_classes}")
                print(f"   📋 类别: {list(model.names.values())[:5]}...")  # 显示前5个
                
                # 检查是否是小麦病害类别
                class_names = list(model.names.values())
                wheat_classes = ['aphid', 'mite', 'rust', 'smut', 'blast', 'healthy']
                has_wheat = any(any(wc in str(c).lower() for wc in wheat_classes) for c in class_names)
                
                if has_wheat or num_classes == 17:
                    print(f"   🌾 这是小麦病害检测模型！")
                    working_models.append((path, model, True))
                else:
                    print(f"   ⚠️ 这可能是通用模型（COCO）")
                    working_models.append((path, model, False))
            else:
                print(f"   ⚠️ 无法获取类别信息")
                working_models.append((path, model, False))
                
        except Exception as e:
            print(f"   ❌ 加载失败: {e}")
    
    # 选择最佳模型
    print("\n[3/3] 选择最佳模型...")
    
    # 优先选择小麦病害模型
    wheat_models = [(p, m) for p, m, is_wheat in working_models if is_wheat]
    other_models = [(p, m) for p, m, is_wheat in working_models if not is_wheat]
    
    if wheat_models:
        best_path, best_model = wheat_models[0]
        print(f"   ✅ 选择小麦病害模型: {best_path}")
    elif other_models:
        best_path, best_model = other_models[0]
        print(f"   ⚠️ 使用可用模型: {best_path}")
        print(f"   💡 建议重新训练专用模型")
    else:
        print("   ❌ 没有可用的工作模型")
        return False
    
    # 测试推理
    print("\n[4/4] 测试推理...")
    test_image = os.path.join(os.getcwd(), "datasets", "wheat_data", "images", "train", "Aphid_aphid_0.png")
    
    if os.path.exists(test_image):
        try:
            results = best_model.predict(test_image, conf=0.25, verbose=False)
            if len(results) > 0 and results[0].boxes is not None:
                num_detections = len(results[0].boxes)
                print(f"   ✅ 推理成功，检测到 {num_detections} 个目标")
                
                # 显示检测结果
                for i, box in enumerate(results[0].boxes[:3]):
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    name = best_model.names.get(cls_id, f'class_{cls_id}')
                    print(f"      {i+1}. {name}: {conf:.2%}")
            else:
                print(f"   ⚠️ 未检测到目标")
        except Exception as e:
            print(f"   ❌ 推理失败: {e}")
    else:
        print(f"   ⚠️ 测试图像不存在: {test_image}")
    
    # 复制最佳模型到models目录
    print("\n[5/5] 更新models目录...")
    target_path = os.path.join(os.getcwd(), "models", "yolov8_wheat.pt")
    
    if best_path != target_path:
        import shutil
        try:
            shutil.copy2(best_path, target_path)
            print(f"   ✅ 模型已复制到: {target_path}")
        except Exception as e:
            print(f"   ❌ 复制失败: {e}")
    else:
        print(f"   ✅ 模型已在正确位置")
    
    print("\n" + "=" * 60)
    print("✅ 模型验证完成")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    verify_and_fix_model()

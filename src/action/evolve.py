# -*- coding: utf-8 -*-
# 文件路径: WheatAgent/src/action/evolve.py
import os
import shutil
import glob
from pathlib import Path

class EvolutionEngine:
    def __init__(self, feedback_root="datasets/feedback_data", dataset_root="datasets/wheat_data"):
        self.feedback_root = feedback_root
        self.dataset_root = dataset_root
        # 全量 16 类映射表 (支持中文名和英文名)
        self.class_map = {
            "蚜虫": 0, "Aphids": 0,
            "螨虫": 1, "Mites": 1,
            "茎蝇": 2, "Stem Fly": 2,
            "锈病": 3, "Rust": 3,
            "茎锈病": 4, "Stem Rust": 4,
            "叶锈病": 5, "Leaf Rust": 5,
            "条锈病": 6, "Stripe Rust": 6,
            "黑粉病": 7, "Smuts": 7,
            "根腐病": 8, "Common Root Rot": 8,
            "叶斑病": 9, "Spot Blotch": 9,
            "小麦爆发病": 10, "Wheat Blast": 10,
            "赤霉病": 11, "Fusarium Head Blight": 11,
            "壳针孢叶斑病": 12, "Septoria Leaf Blotch": 12,
            "斑点叶斑病": 13, "Speckled Leaf Blotch": 13,
            "褐斑病": 14, "Brown Spot": 14,
            "白粉病": 15, "Powdery Mildew": 15
        }
        
    def digest_feedback(self):
        """消化反馈数据：将 feedback_data 中的样本清洗并移动到训练集"""
        print(f"🔄 [Evolution] 开始扫描反馈池: {self.feedback_root}")
        
        processed_count = 0
        
        # 遍历每个病害类别的文件夹
        for class_name, class_id in self.class_map.items():
            class_dir = os.path.join(self.feedback_root, class_name)
            if not os.path.exists(class_dir):
                continue
                
            # 查找所有图片
            images = glob.glob(os.path.join(class_dir, "*.*"))
            images = [f for f in images if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            
            for img_path in images:
                # 1. 移动图片到训练集
                target_img_dir = os.path.join(self.dataset_root, "images", "train")
                os.makedirs(target_img_dir, exist_ok=True)
                
                # 生成唯一文件名
                filename = os.path.basename(img_path)
                new_filename = f"evolve_v3_{filename}"
                target_img_path = os.path.join(target_img_dir, new_filename)
                
                shutil.copy2(img_path, target_img_path)
                
                # 2. 生成标签文件 (Weak Supervision)
                target_lbl_dir = os.path.join(self.dataset_root, "labels", "train")
                os.makedirs(target_lbl_dir, exist_ok=True)
                
                label_filename = os.path.splitext(new_filename)[0] + ".txt"
                target_lbl_path = os.path.join(target_lbl_dir, label_filename)
                
                with open(target_lbl_path, "w") as f:
                    # 默认中心框
                    f.write(f"{class_id} 0.5 0.5 0.7 0.7\n")
                
                # 3. 归档
                archive_dir = os.path.join(self.feedback_root, "archived", class_name)
                os.makedirs(archive_dir, exist_ok=True)
                shutil.move(img_path, os.path.join(archive_dir, filename))
                
                processed_count += 1
                
        print(f"✅ [Evolution] 消化完成！新增训练样本: {processed_count} 个")
        return processed_count

if __name__ == "__main__":
    engine = EvolutionEngine()
    engine.digest_feedback()
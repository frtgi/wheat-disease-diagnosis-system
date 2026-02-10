# 文件路径: WheatAgent/src/tools/data_converter.py
import os
import shutil
import random
from pathlib import Path
from tqdm import tqdm

def convert_classification_to_detection(source_root, target_root, split_ratio=0.8):
    """
    将图像分类格式数据集转换为 YOLO 检测格式
    :param source_root: 原始数据根目录 (包含 train/Aphid/*.png)
    :param target_root: 输出 YOLO 格式目录
    """
    print(f"🚀 [DataConverter] 正在处理数据: {source_root} -> {target_root}")
    
    # 1. 定义 16 类映射表 (兼容单复数、中文名)
    # 键是文件夹可能的名称，值是 YOLO 的类别 ID
    class_map = {
        # 0: 蚜虫
        "Aphid": 0, "Aphids": 0, "aphid": 0, "aphids": 0, "蚜虫": 0,
        # 1: 螨虫
        "Mite": 1, "Mites": 1, "mite": 1, "mites": 1, "螨虫": 1,
        # 2: 茎蝇
        "Stem_fly": 2, "Stem_Fly": 2, "stem_fly": 2, "茎蝇": 2,
        # 3: 锈病
        "Rust": 3, "rust": 3, "锈病": 3,
        # 4: 茎锈病
        "Stem_rust": 4, "Stem_Rust": 4, "stem_rust": 4, "茎锈病": 4,
        # 5: 叶锈病
        "Leaf_rust": 5, "Leaf_Rust": 5, "leaf_rust": 5, "Brown_rust": 5, "叶锈病": 5,
        # 6: 条锈病
        "Stripe_rust": 6, "Stripe_Rust": 6, "Yellow_rust": 6, "stripe_rust": 6, "条锈病": 6,
        # 7: 黑粉病
        "Smut": 7, "Smuts": 7, "Loose_smut": 7, "smut": 7, "黑粉病": 7,
        # 8: 根腐病
        "Root_rot": 8, "Common_root_rot": 8, "Crown_rot": 8, "root_rot": 8, "根腐病": 8,
        # 9: 叶斑病
        "Leaf_blotch": 9, "Spot_blotch": 9, "leaf_blotch": 9, "叶斑病": 9,
        # 10: 小麦爆发病
        "Wheat_blast": 10, "Blast": 10, "wheat_blast": 10, "小麦爆发病": 10,
        # 11: 镰刀菌穗腐病/赤霉病
        "Fusarium": 11, "Head_blight": 11, "Scab": 11, "FHB": 11, "赤霉病": 11,
        # 12: 壳针孢叶斑病
        "Septoria": 12, "Septoria_leaf_blotch": 12, "septoria": 12, "壳针孢叶斑病": 12,
        # 13: 斑点叶斑病
        "Speckled_leaf_blotch": 13, "Septoria_tritici": 13, "斑点叶斑病": 13,
        # 14: 褐斑病
        "Brown_spot": 14, "brown_spot": 14, "褐斑病": 14,
        # 15: 白粉病
        "Powdery_mildew": 15, "Mildew": 15, "powdery_mildew": 15, "白粉病": 15,
        # 健康 (可选)
        "Healthy": 16, "healthy": 16, "健康": 16
    }

    # 准备目标目录
    dirs = {
        "train_img": os.path.join(target_root, "images", "train"),
        "val_img": os.path.join(target_root, "images", "val"),
        "train_lbl": os.path.join(target_root, "labels", "train"),
        "val_lbl": os.path.join(target_root, "labels", "val")
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    total_files = 0
    matched_files = 0

    # 扫描原始目录 (假设结构为 source_root/train/ClassName/xxx.png)
    # 或者 source_root/ClassName/xxx.png
    # 我们递归查找所有子文件夹
    source_path = Path(source_root)
    
    # 获取所有图片文件
    all_images = []
    for ext in ['*.jpg', '*.png', '*.jpeg', '*.bmp']:
        all_images.extend(list(source_path.rglob(ext)))

    print(f"📊 扫描到 {len(all_images)} 张图片，开始转换...")

    for img_path in tqdm(all_images):
        # 获取父文件夹名称作为类别名
        parent_folder = img_path.parent.name
        
        # 尝试匹配类别
        class_id = class_map.get(parent_folder)
        
        if class_id is None:
            # 尝试模糊匹配 (比如 parent="Aphid_Data" 包含 "Aphid")
            for key, val in class_map.items():
                if key.lower() == parent_folder.lower():
                    class_id = val
                    break
        
        if class_id is None:
            # print(f"⚠️ 跳过未知类别文件夹: {parent_folder}")
            continue
            
        if class_id == 16: # 忽略健康或单独处理，这里暂不作为检测目标，或作为空标签
            continue 

        matched_files += 1

        # 随机划分训练/验证集
        is_train = random.random() < split_ratio
        target_img_dir = dirs["train_img"] if is_train else dirs["val_img"]
        target_lbl_dir = dirs["train_lbl"] if is_train else dirs["val_lbl"]

        # 1. 复制图片
        # 重命名以防冲突: ClassName_OriginalName
        new_filename = f"{parent_folder}_{img_path.name}"
        shutil.copy2(str(img_path), os.path.join(target_img_dir, new_filename))

        # 2. 生成 YOLO 标签
        # 由于是分类数据集，没有真实边框。我们生成一个"伪边框"覆盖图像中心。
        # 格式: class_id x_center y_center width height (归一化 0-1)
        # 这里框选中间 90% 的区域
        lbl_filename = os.path.splitext(new_filename)[0] + ".txt"
        with open(os.path.join(target_lbl_dir, lbl_filename), "w") as f:
            f.write(f"{class_id} 0.5 0.5 0.9 0.9\n")

    print("="*40)
    print(f"✅ 转换完成！")
    print(f"   - 原始图片: {len(all_images)}")
    print(f"   - 成功转换: {matched_files}")
    print(f"   - 输出目录: {target_root}")
    print("="*40)

if __name__ == "__main__":
    # 配置区
    # 请修改为您实际的 raw 数据路径
    # 假设您的原始数据在 d:/Project/wheat_image/dataset/images
    RAW_DATA_PATH = r"D:\Project\wheat_image\dataset" 
    
    # 目标路径 (WheatAgent 使用的路径)
    TARGET_DATA_PATH = r"D:\Project\WheatAgent\datasets\wheat_data"
    
    convert_classification_to_detection(RAW_DATA_PATH, TARGET_DATA_PATH)
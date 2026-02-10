import os
from pathlib import Path
from tqdm import tqdm

def generate_yolo_labels(dataset_root):
    """
    为wheat数据集生成YOLO格式标签文件
    :param dataset_root: 数据集根目录
    """
    print("="*60)
    print("🚀 [LabelGenerator] 开始生成YOLO格式标签文件")
    print("="*60)
    
    # 类别映射表：文件夹名 -> 类别ID (0-16)
    class_mapping = {
        # 训练集文件夹
        "Aphid": 0,
        "Black Rust": 4,
        "Blast": 10,
        "Brown Rust": 5,
        "Common Root Rot": 8,
        "Fusarium Head Blight": 11,
        "Healthy": 16,
        "Leaf Blight": 9,
        "Mildew": 15,
        "Mite": 1,
        "Septoria": 12,
        "Smut": 7,
        "Stem fly": 2,
        "Tan spot": 14,
        "Yellow Rust": 6,
        
        # 验证集文件夹
        "aphid_valid": 0,
        "black_rust_valid": 4,
        "blast_test_valid": 10,
        "brown_rust_valid": 5,
        "common_root_rot_valid": 8,
        "fusarium_head_blight_valid": 11,
        "healthy_valid": 16,
        "leaf_blight_valid": 9,
        "mildew_valid": 15,
        "mite_valid": 1,
        "septoria_valid": 12,
        "smut_valid": 7,
        "stem_fly_valid": 2,
        "tan_spot_valid": 14,
        "yellow_rust_valid": 6
    }
    
    # 类别名称映射（用于统计报告）
    class_names = {
        0: "蚜虫",
        1: "螨虫",
        2: "茎蝇",
        3: "锈病",
        4: "茎锈病",
        5: "叶锈病",
        6: "条锈病",
        7: "黑粉病",
        8: "根腐病",
        9: "叶斑病",
        10: "小麦爆发病",
        11: "赤霉病",
        12: "壳针孢叶斑病",
        13: "斑点叶斑病",
        14: "褐斑病",
        15: "白粉病",
        16: "健康"
    }
    
    # 数据集路径
    train_img_dir = os.path.join(dataset_root, "images", "train")
    val_img_dir = os.path.join(dataset_root, "images", "val")
    train_lbl_dir = os.path.join(dataset_root, "labels", "train")
    val_lbl_dir = os.path.join(dataset_root, "labels", "val")
    
    # 确保标签目录存在
    os.makedirs(train_lbl_dir, exist_ok=True)
    os.makedirs(val_lbl_dir, exist_ok=True)
    
    # 统计信息
    stats = {
        "train": {"total": 0, "by_class": {}},
        "val": {"total": 0, "by_class": {}}
    }
    
    # 处理训练集
    print("\n📂 处理训练集...")
    process_directory(train_img_dir, train_lbl_dir, class_mapping, class_names, stats["train"])
    
    # 处理验证集
    print("\n📂 处理验证集...")
    process_directory(val_img_dir, val_lbl_dir, class_mapping, class_names, stats["val"])
    
    # 打印统计报告
    print("\n" + "="*60)
    print("📊 数据集统计报告")
    print("="*60)
    print(f"\n训练集:")
    print(f"  总图片数: {stats['train']['total']}")
    for class_id, count in sorted(stats['train']['by_class'].items()):
        print(f"  - {class_names[class_id]} (ID:{class_id}): {count} 张")
    
    print(f"\n验证集:")
    print(f"  总图片数: {stats['val']['total']}")
    for class_id, count in sorted(stats['val']['by_class'].items()):
        print(f"  - {class_names[class_id]} (ID:{class_id}): {count} 张")
    
    print(f"\n总计: {stats['train']['total'] + stats['val']['total']} 张图片")
    print("="*60)
    print("✅ 标签生成完成！")
    print("="*60)

def process_directory(img_dir, lbl_dir, class_mapping, class_names, stats):
    """
    处理指定目录下的所有图片，生成标签文件
    :param img_dir: 图片目录
    :param lbl_dir: 标签输出目录
    :param class_mapping: 类别映射表
    :param class_names: 类别名称映射
    :param stats: 统计信息字典
    """
    img_dir_path = Path(img_dir)
    
    # 遍历所有子文件夹
    for class_folder in img_dir_path.iterdir():
        if not class_folder.is_dir():
            continue
        
        # 获取类别ID
        class_id = class_mapping.get(class_folder.name)
        
        if class_id is None:
            print(f"⚠️ 跳过未知类别文件夹: {class_folder.name}")
            continue
        
        # 获取该类别下的所有图片
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp']:
            image_files.extend(class_folder.glob(ext))
        
        if not image_files:
            continue
        
        # 初始化统计
        if class_id not in stats["by_class"]:
            stats["by_class"][class_id] = 0
        
        # 为每张图片生成标签
        for img_path in tqdm(image_files, desc=f"  处理 {class_folder.name}", leave=False):
            # 生成标签文件名
            lbl_filename = img_path.stem + ".txt"
            lbl_path = os.path.join(lbl_dir, lbl_filename)
            
            # 生成YOLO格式标签（覆盖整个图片的90%区域）
            # 格式: class_id x_center y_center width height (归一化 0-1)
            yolo_label = f"{class_id} 0.5 0.5 0.9 0.9\n"
            
            # 写入标签文件
            with open(lbl_path, "w") as f:
                f.write(yolo_label)
            
            # 更新统计
            stats["total"] += 1
            stats["by_class"][class_id] += 1

def validate_dataset(dataset_root):
    """
    验证数据集完整性，检查每张图片是否有对应的标签文件
    :param dataset_root: 数据集根目录
    """
    print("\n" + "="*60)
    print("🔍 验证数据集完整性")
    print("="*60)
    
    missing_labels = []
    total_images = 0
    
    # 检查训练集
    train_img_dir = os.path.join(dataset_root, "images", "train")
    train_lbl_dir = os.path.join(dataset_root, "labels", "train")
    missing_labels.extend(check_labels(train_img_dir, train_lbl_dir))
    
    # 检查验证集
    val_img_dir = os.path.join(dataset_root, "images", "val")
    val_lbl_dir = os.path.join(dataset_root, "labels", "val")
    missing_labels.extend(check_labels(val_img_dir, val_lbl_dir))
    
    if missing_labels:
        print(f"\n⚠️ 发现 {len(missing_labels)} 张图片缺少标签文件:")
        for img_path in missing_labels[:10]:  # 只显示前10个
            print(f"  - {img_path}")
        if len(missing_labels) > 10:
            print(f"  ... 还有 {len(missing_labels) - 10} 个")
    else:
        print("\n✅ 所有图片都有对应的标签文件！")
    
    print("="*60)

def check_labels(img_dir, lbl_dir):
    """
    检查指定目录下的图片是否有对应的标签文件
    :param img_dir: 图片目录
    :param lbl_dir: 标签目录
    :return: 缺少标签的图片路径列表
    """
    missing = []
    img_dir_path = Path(img_dir)
    
    for class_folder in img_dir_path.rglob("*"):
        if not class_folder.is_dir():
            continue
        
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp']:
            for img_path in class_folder.glob(ext):
                lbl_path = os.path.join(lbl_dir, img_path.stem + ".txt")
                if not os.path.exists(lbl_path):
                    missing.append(str(img_path.relative_to(img_dir_path.parent.parent)))
    
    return missing

if __name__ == "__main__":
    # 数据集路径
    DATASET_ROOT = r"D:\Project\WheatAgent\datasets\wheat_data"
    
    # 生成标签
    generate_yolo_labels(DATASET_ROOT)
    
    # 验证数据集
    validate_dataset(DATASET_ROOT)

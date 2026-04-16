"""
数据集重新组织脚本
将按类别组织的图片重新组织为 YOLOv8 标准格式
"""
import os
import shutil
from pathlib import Path
from tqdm import tqdm

def reorganize_dataset():
    """
    重新组织数据集为 YOLOv8 标准格式
    """
    data_root = Path('datasets/wheat_data')
    
    print("=" * 60)
    print("数据集重新组织")
    print("=" * 60)
    
    # 类别名称映射
    class_mapping = {
        'Aphid': '蚜虫',
        'Mite': '螨虫',
        'Stem fly': '茎蝇',
        'Rust': '锈病',
        'Stem Rust': '茎锈病',
        'Leaf Rust': '叶锈病',
        'Yellow Rust': '条锈病',
        'Smuts': '黑粉病',
        'Common root rot': '根腐病',
        'Tan spot': '叶斑病',
        'Blast': '小麦爆发病',
        'Scab': '赤霉病',
        'Septoria': '壳针孢叶斑病',
        'Speckled leaf blotch': '斑点叶斑病',
        'Brown spot': '褐斑病',
        'Mildew': '白粉病'
    }
    
    # 处理训练集
    print("\n处理训练集...")
    train_images_dir = data_root / 'images' / 'train'
    train_labels_dir = data_root / 'labels' / 'train'
    
    # 创建临时目录
    temp_train_images = data_root / 'images' / 'train_temp'
    temp_train_labels = data_root / 'labels' / 'train_temp'
    
    temp_train_images.mkdir(exist_ok=True)
    temp_train_labels.mkdir(exist_ok=True)
    
    # 遍历所有类别目录
    moved_count = 0
    for class_dir in train_images_dir.iterdir():
        if class_dir.is_dir():
            class_name = class_dir.name
            
            # 获取该类别对应的中文名称
            cn_name = class_mapping.get(class_name, class_name)
            
            # 查找对应的标签文件
            label_pattern = f"{class_name.lower().replace(' ', '_')}_*.txt"
            label_files = list((data_root / 'labels' / 'train').glob(label_pattern))
            
            # 遍历该类别的所有图片
            image_files = list(class_dir.glob('*.png')) + list(class_dir.glob('*.jpg'))
            
            for img_file in tqdm(image_files, desc=f"  处理 {class_name}"):
                # 生成新的文件名（使用序号）
                new_name = f"{class_name}_{img_file.stem}{img_file.suffix}"
                
                # 复制图片
                new_img_path = temp_train_images / new_name
                shutil.copy2(img_file, new_img_path)
                
                # 查找对应的标签文件
                img_num = img_file.stem.split('_')[-1] if '_' in img_file.stem else img_file.stem
                label_file = data_root / 'labels' / 'train' / f"{class_name.lower().replace(' ', '_')}_{img_num}.txt"
                
                if label_file.exists():
                    # 复制标签文件
                    new_label_path = temp_train_labels / f"{new_name}.txt"
                    shutil.copy2(label_file, new_label_path)
                    moved_count += 1
                else:
                    # 创建默认标签（中心框）
                    new_label_path = temp_train_labels / f"{new_name}.txt"
                    with open(new_label_path, 'w') as f:
                        f.write("0 0.5 0.5 0.7 0.7\n")
    
    # 处理验证集
    print("\n处理验证集...")
    val_images_dir = data_root / 'images' / 'val'
    
    temp_val_images = data_root / 'images' / 'val_temp'
    temp_val_labels = data_root / 'labels' / 'val_temp'
    
    temp_val_images.mkdir(exist_ok=True)
    temp_val_labels.mkdir(exist_ok=True)
    
    for class_dir in val_images_dir.iterdir():
        if class_dir.is_dir():
            class_name = class_dir.name
            
            # 遍历该类别的所有图片
            image_files = list(class_dir.glob('*.png')) + list(class_dir.glob('*.jpg'))
            
            for img_file in tqdm(image_files, desc=f"  处理 {class_name}"):
                # 生成新的文件名
                new_name = f"{class_name}_{img_file.stem}{img_file.suffix}"
                
                # 复制图片
                new_img_path = temp_val_images / new_name
                shutil.copy2(img_file, new_img_path)
                
                # 创建默认标签（中心框）
                new_label_path = temp_val_labels / f"{new_name}.txt"
                with open(new_label_path, 'w') as f:
                    f.write("0 0.5 0.5 0.7 0.7\n")
    
    # 备份原始目录
    print("\n备份原始目录...")
    if (data_root / 'images' / 'train').exists():
        shutil.move(data_root / 'images' / 'train', data_root / 'images' / 'train_backup')
    if (data_root / 'images' / 'val').exists():
        shutil.move(data_root / 'images' / 'val', data_root / 'images' / 'val_backup')
    if (data_root / 'labels' / 'train').exists():
        shutil.move(data_root / 'labels' / 'train', data_root / 'labels' / 'train_backup')
    if (data_root / 'labels' / 'val').exists():
        shutil.move(data_root / 'labels' / 'val', data_root / 'labels' / 'val_backup')
    
    # 重命名临时目录
    print("\n应用新结构...")
    temp_train_images.rename(data_root / 'images' / 'train')
    temp_train_labels.rename(data_root / 'labels' / 'train')
    temp_val_images.rename(data_root / 'images' / 'val')
    temp_val_labels.rename(data_root / 'labels' / 'val')
    
    print(f"\n✅ 数据集重新组织完成！")
    print(f"   移动了 {moved_count} 个标签文件")
    print(f"   训练集图片: {len(list((data_root / 'images' / 'train').glob('*.png')) + list((data_root / 'images' / 'train').glob('*.jpg')))}")
    print(f"   验证集图片: {len(list((data_root / 'images' / 'val').glob('*.png')) + list((data_root / 'images' / 'val').glob('*.jpg')))}")
    print("=" * 60)

if __name__ == "__main__":
    reorganize_dataset()

"""
数据集完整性检查脚本
"""
from pathlib import Path

def check_dataset():
    """
    检查数据集完整性
    """
    data_root = Path('datasets/wheat_data')
    
    print("=" * 60)
    print("数据集完整性检查")
    print("=" * 60)
    
    # 检查目录是否存在
    dirs_to_check = [
        'images/train',
        'images/val',
        'labels/train',
        'labels/val'
    ]
    
    for dir_path in dirs_to_check:
        full_path = data_root / dir_path
        if full_path.exists():
            count = len(list(full_path.glob('*')))
            print(f"✅ {dir_path}: {count} 个文件")
        else:
            print(f"❌ {dir_path}: 目录不存在")
    
    # 检查一一对应
    img_train = list((data_root / 'images/train').glob('*.jpg')) + \
                  list((data_root / 'images/train').glob('*.png'))
    lbl_train = list((data_root / 'labels/train').glob('*.txt'))
    
    img_val = list((data_root / 'images/val').glob('*.jpg')) + \
                list((data_root / 'images/val').glob('*.png'))
    lbl_val = list((data_root / 'labels/val').glob('*.txt'))
    
    print()
    print(f"训练集图片数量: {len(img_train)}")
    print(f"训练集标签数量: {len(lbl_train)}")
    print(f"验证集图片数量: {len(img_val)}")
    print(f"验证集标签数量: {len(lbl_val)}")
    print()
    
    # 检查完整性
    train_match = len(img_train) == len(lbl_train)
    val_match = len(img_val) == len(lbl_val)
    
    if train_match and val_match:
        print("✅ 数据集完整性检查通过")
    else:
        print("❌ 数据集完整性检查失败")
        if not train_match:
            print(f"   - 训练集不匹配: 图片 {len(img_train)} vs 标签 {len(lbl_train)}")
        if not val_match:
            print(f"   - 验证集不匹配: 图片 {len(img_val)} vs 标签 {len(lbl_val)}")
    
    # 检查类别文件
    classes_file = data_root / 'labels/train' / 'classes.txt'
    if classes_file.exists():
        with open(classes_file, 'r', encoding='utf-8') as f:
            classes = f.read().strip().split('\n')
        print(f"\n类别数量: {len(classes)}")
        print(f"类别列表: {classes[:5]}..." if len(classes) > 5 else classes)
    else:
        print("\n⚠️ 未找到 classes.txt 文件")
    
    print("=" * 60)

if __name__ == "__main__":
    check_dataset()

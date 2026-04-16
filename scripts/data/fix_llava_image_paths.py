# -*- coding: utf-8 -*-
"""
LLaVA LoRA 微调图片路径修复脚本

解决 JSON 数据集中的图片路径与实际图片位置不匹配的问题：
- JSON 路径格式: images/蚜虫/002090.jpg
- 实际图片位置: datasets/wheat_data_unified/images/train/Aphid_0.png

使用方法:
    python scripts/data/fix_llava_image_paths.py --dry-run
    python scripts/data/fix_llava_image_paths.py --fix-json
    python scripts/data/fix_llava_image_paths.py --create-symlinks

作者: IWDDA 项目
"""
import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict


PROJECT_ROOT = Path(__file__).parent.parent.parent

DISEASE_NAME_MAPPING = {
    "蚜虫": {
        "english": "Aphid",
        "folder_names": ["Aphid"],
        "keywords": ["aphid", "蚜虫"]
    },
    "叶锈病": {
        "english": "Leaf Rust",
        "folder_names": ["Blast", "Brown Rust"],
        "keywords": ["blast", "rust", "叶锈"]
    },
    "白粉病": {
        "english": "Powdery Mildew",
        "folder_names": ["Mildew"],
        "keywords": ["mildew", "白粉"]
    },
    "赤霉病": {
        "english": "Fusarium Head Blight",
        "folder_names": ["Smut", "Fusarium Head Blight"],
        "keywords": ["smut", "fusarium", "赤霉", "黑穗"]
    },
    "条锈病": {
        "english": "Stripe Rust",
        "folder_names": ["Blast", "Yellow Rust"],
        "keywords": ["stripe", "rust", "条锈"]
    },
    "螨虫": {
        "english": "Mite",
        "folder_names": ["Mite"],
        "keywords": ["mite", "螨"]
    },
    "全蚀病": {
        "english": "Take-all Disease",
        "folder_names": ["Common Root Rot"],
        "keywords": ["take-all", "root rot", "全蚀"]
    },
    "叶斑病": {
        "english": "Leaf Spot",
        "folder_names": ["Leaf Blight", "Tan spot"],
        "keywords": ["leaf spot", "blight", "叶斑"]
    },
    "壳针孢叶斑病": {
        "english": "Septoria Leaf Spot",
        "folder_names": ["Septoria"],
        "keywords": ["septoria", "壳针孢"]
    },
    "大麦黄矮病": {
        "english": "Barley Yellow Dwarf",
        "folder_names": ["Yellow Rust"],
        "keywords": ["yellow dwarf", "barley", "黄矮"]
    },
    "小麦梭条斑花叶病": {
        "english": "Wheat Spindle Streak Mosaic",
        "folder_names": ["Leaf Blight"],
        "keywords": ["spindle", "mosaic", "梭条斑"]
    },
    "根腐病": {
        "english": "Root Rot",
        "folder_names": ["Common Root Rot"],
        "keywords": ["root rot", "根腐"]
    },
    "眼斑病": {
        "english": "Eye Spot",
        "folder_names": ["Leaf Blight", "Septoria"],
        "keywords": ["eye spot", "眼斑"]
    },
    "秆锈病": {
        "english": "Stem Rust",
        "folder_names": ["Black Rust", "Brown Rust"],
        "keywords": ["stem rust", "black rust", "秆锈"]
    },
    "稻瘟病": {
        "english": "Rice Blast",
        "folder_names": ["Blast"],
        "keywords": ["rice blast", "稻瘟"]
    },
    "褐斑病": {
        "english": "Brown Spot",
        "folder_names": ["Tan spot", "Leaf Blight"],
        "keywords": ["brown spot", "tan spot", "褐斑"]
    },
    "雪霉病": {
        "english": "Snow Mold",
        "folder_names": ["Mildew", "Leaf Blight"],
        "keywords": ["snow mold", "雪霉"]
    },
    "黑粉病": {
        "english": "Smut",
        "folder_names": ["Smut"],
        "keywords": ["smut", "黑粉"]
    }
}

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}


def scan_actual_images(base_dir: Path) -> Dict[str, List[Path]]:
    """
    扫描实际图片目录，构建图片索引
    
    Args:
        base_dir: 图片基础目录
    
    Returns:
        按类别分组的图片路径字典
    """
    image_index = defaultdict(list)
    
    for split in ['train', 'val']:
        split_dir = base_dir / split
        if not split_dir.exists():
            continue
        
        for img_file in split_dir.iterdir():
            if img_file.suffix.lower() in IMAGE_EXTENSIONS:
                stem = img_file.stem
                if '_' in stem:
                    category = stem.rsplit('_', 1)[0]
                    image_index[category].append(img_file)
    
    return dict(image_index)


def parse_json_image_path(image_path: str) -> Tuple[str, int]:
    """
    解析 JSON 中的图片路径
    
    Args:
        image_path: JSON 中的图片路径，如 "images/蚜虫/002090.jpg"
    
    Returns:
        (疾病类别, 图片编号) 元组
    """
    parts = image_path.replace('\\', '/').split('/')
    
    if len(parts) >= 2:
        disease_name = parts[-2]
        filename = parts[-1]
        
        file_stem = Path(filename).stem
        
        try:
            image_num = int(file_stem)
        except ValueError:
            image_num = 0
        
        return disease_name, image_num
    
    return "unknown", 0


def find_matching_image(
    disease_name: str,
    image_num: int,
    image_index: Dict[str, List[Path]],
    prefer_split: str = 'train',
    used_images: set = None
) -> Optional[Path]:
    """
    查找匹配的实际图片
    
    使用智能映射策略：
    1. 首先尝试精确编号匹配
    2. 如果失败，使用顺序分配策略（基于图片编号取模）
    
    Args:
        disease_name: 疾病名称（中文）
        image_num: 图片编号
        image_index: 图片索引
        prefer_split: 优先使用的分割集
        used_images: 已使用的图片集合（避免重复）
    
    Returns:
        匹配的图片路径，未找到返回 None
    """
    if used_images is None:
        used_images = set()
    
    disease_info = DISEASE_NAME_MAPPING.get(disease_name)
    if not disease_info:
        return None
    
    folder_names = disease_info['folder_names']
    
    for folder_name in folder_names:
        if folder_name not in image_index:
            continue
        
        images = image_index[folder_name]
        available_images = [img for img in images if str(img) not in used_images]
        
        if not available_images:
            available_images = images
        
        for img_path in available_images:
            if prefer_split in str(img_path):
                stem = img_path.stem
                if '_' in stem:
                    try:
                        num = int(stem.rsplit('_', 1)[1])
                        if num == image_num:
                            return img_path
                    except ValueError:
                        continue
        
        for img_path in available_images:
            stem = img_path.stem
            if '_' in stem:
                try:
                    num = int(stem.rsplit('_', 1)[1])
                    if num == image_num:
                        return img_path
                except ValueError:
                    continue
        
        prefer_images = [img for img in available_images if prefer_split in str(img)]
        if prefer_images:
            idx = image_num % len(prefer_images)
            return prefer_images[idx]
        
        if available_images:
            idx = image_num % len(available_images)
            return available_images[idx]
    
    return None


def analyze_dataset(
    json_path: Path,
    image_base_dir: Path
) -> Dict:
    """
    分析数据集，统计路径匹配情况
    
    Args:
        json_path: JSON 数据集路径
        image_base_dir: 图片基础目录
    
    Returns:
        分析结果字典
    """
    print("=" * 60)
    print("📊 分析数据集路径映射")
    print("=" * 60)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📁 JSON 文件: {json_path}")
    print(f"📁 图片目录: {image_base_dir}")
    print(f"📝 数据条目: {len(data)}")
    
    image_index = scan_actual_images(image_base_dir)
    print(f"\n📷 实际图片统计:")
    for category, images in sorted(image_index.items()):
        print(f"   {category}: {len(images)} 张图片")
    
    results = {
        'total': len(data),
        'matched': 0,
        'unmatched': 0,
        'by_disease': defaultdict(lambda: {'matched': 0, 'unmatched': 0, 'examples': []}),
        'unmatched_entries': [],
        'image_index': image_index
    }
    
    print(f"\n🔍 匹配分析:")
    
    used_images_by_disease = defaultdict(set)
    
    for entry in data:
        image_path = entry.get('image_path', '')
        metadata = entry.get('metadata', {})
        disease_name = metadata.get('disease', 'unknown')
        
        json_disease, image_num = parse_json_image_path(image_path)
        matched_path = find_matching_image(
            disease_name, 
            image_num, 
            image_index,
            used_images=used_images_by_disease[disease_name]
        )
        
        if matched_path:
            used_images_by_disease[disease_name].add(str(matched_path))
            results['matched'] += 1
            results['by_disease'][disease_name]['matched'] += 1
        else:
            results['unmatched'] += 1
            results['by_disease'][disease_name]['unmatched'] += 1
            
            if len(results['by_disease'][disease_name]['examples']) < 3:
                results['by_disease'][disease_name]['examples'].append({
                    'json_path': image_path,
                    'json_disease': json_disease,
                    'image_num': image_num
                })
            
            results['unmatched_entries'].append(entry)
    
    print(f"\n📈 匹配结果:")
    print(f"   ✅ 匹配成功: {results['matched']} / {results['total']} ({results['matched']/results['total']*100:.1f}%)")
    print(f"   ❌ 匹配失败: {results['unmatched']} / {results['total']} ({results['unmatched']/results['total']*100:.1f}%)")
    
    print(f"\n📊 按疾病分类:")
    for disease, stats in sorted(results['by_disease'].items()):
        total = stats['matched'] + stats['unmatched']
        match_rate = stats['matched'] / total * 100 if total > 0 else 0
        print(f"   {disease}: {stats['matched']}/{total} ({match_rate:.1f}%)")
        
        if stats['examples']:
            print(f"      未匹配示例:")
            for ex in stats['examples']:
                print(f"         - {ex['json_path']} (编号: {ex['image_num']})")
    
    return results


def fix_json_paths(
    json_path: Path,
    image_base_dir: Path,
    output_path: Optional[Path] = None,
    use_relative: bool = True
) -> Dict:
    """
    修复 JSON 文件中的图片路径
    
    Args:
        json_path: JSON 数据集路径
        image_base_dir: 图片基础目录
        output_path: 输出路径，默认覆盖原文件
        use_relative: 是否使用相对路径
    
    Returns:
        修复统计信息
    """
    print("\n" + "=" * 60)
    print("🔧 修复 JSON 图片路径")
    print("=" * 60)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    image_index = scan_actual_images(image_base_dir)
    
    stats = {
        'total': len(data),
        'fixed': 0,
        'skipped': 0,
        'errors': 0
    }
    
    fixed_data = []
    used_images_by_disease = defaultdict(set)
    
    for entry in data:
        image_path = entry.get('image_path', '')
        metadata = entry.get('metadata', {})
        disease_name = metadata.get('disease', 'unknown')
        
        _, image_num = parse_json_image_path(image_path)
        matched_path = find_matching_image(
            disease_name, 
            image_num, 
            image_index,
            used_images=used_images_by_disease[disease_name]
        )
        
        new_entry = entry.copy()
        
        if matched_path:
            used_images_by_disease[disease_name].add(str(matched_path))
            if use_relative:
                rel_path = matched_path.relative_to(PROJECT_ROOT)
                new_entry['image_path'] = str(rel_path).replace('\\', '/')
            else:
                new_entry['image_path'] = str(matched_path).replace('\\', '/')
            
            new_entry['original_image_path'] = image_path
            stats['fixed'] += 1
        else:
            stats['skipped'] += 1
        
        fixed_data.append(new_entry)
    
    if output_path is None:
        backup_path = json_path.with_suffix('.json.bak')
        shutil.copy2(json_path, backup_path)
        print(f"💾 已备份原文件到: {backup_path}")
        output_path = json_path
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存修复后的文件: {output_path}")
    print(f"   总条目: {stats['total']}")
    print(f"   已修复: {stats['fixed']}")
    print(f"   跳过(未匹配): {stats['skipped']}")
    
    return stats


def create_symlink_structure(
    json_path: Path,
    image_base_dir: Path,
    output_dir: Path
) -> Dict:
    """
    创建符合 JSON 路径结构的符号链接目录
    
    Args:
        json_path: JSON 数据集路径
        image_base_dir: 图片基础目录
        output_dir: 输出目录
    
    Returns:
        创建统计信息
    """
    print("\n" + "=" * 60)
    print("🔗 创建符号链接目录结构")
    print("=" * 60)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    image_index = scan_actual_images(image_base_dir)
    
    stats = {
        'total': len(data),
        'links_created': 0,
        'copies_created': 0,
        'skipped': 0
    }
    
    output_dir.mkdir(parents=True, exist_ok=True)
    used_images_by_disease = defaultdict(set)
    
    for entry in data:
        image_path = entry.get('image_path', '')
        metadata = entry.get('metadata', {})
        disease_name = metadata.get('disease', 'unknown')
        
        _, image_num = parse_json_image_path(image_path)
        matched_path = find_matching_image(
            disease_name, 
            image_num, 
            image_index,
            used_images=used_images_by_disease[disease_name]
        )
        
        if matched_path:
            used_images_by_disease[disease_name].add(str(matched_path))
            target_dir = output_dir / Path(image_path).parent
            target_dir.mkdir(parents=True, exist_ok=True)
            
            target_file = output_dir / image_path
            
            if not target_file.exists():
                try:
                    os.symlink(matched_path, target_file)
                    stats['links_created'] += 1
                except OSError:
                    shutil.copy2(matched_path, target_file)
                    stats['copies_created'] += 1
        else:
            stats['skipped'] += 1
    
    print(f"\n✅ 符号链接目录创建完成: {output_dir}")
    print(f"   符号链接: {stats['links_created']}")
    print(f"   文件复制: {stats['copies_created']}")
    print(f"   跳过: {stats['skipped']}")
    
    return stats


def generate_mapping_report(
    json_path: Path,
    image_base_dir: Path,
    output_path: Optional[Path] = None
) -> Dict:
    """
    生成详细的路径映射报告
    
    Args:
        json_path: JSON 数据集路径
        image_base_dir: 图片基础目录
        output_path: 报告输出路径
    
    Returns:
        映射字典
    """
    print("\n" + "=" * 60)
    print("📋 生成路径映射报告")
    print("=" * 60)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    image_index = scan_actual_images(image_base_dir)
    
    mapping = {
        'generated_at': datetime.now().isoformat(),
        'json_file': str(json_path),
        'image_base_dir': str(image_base_dir),
        'disease_mapping': DISEASE_NAME_MAPPING,
        'path_mappings': [],
        'unmapped': []
    }
    
    used_images_by_disease = defaultdict(set)
    
    for entry in data:
        image_path = entry.get('image_path', '')
        metadata = entry.get('metadata', {})
        disease_name = metadata.get('disease', 'unknown')
        entry_id = entry.get('id', '')
        
        _, image_num = parse_json_image_path(image_path)
        matched_path = find_matching_image(
            disease_name, 
            image_num, 
            image_index,
            used_images=used_images_by_disease[disease_name]
        )
        
        mapping_entry = {
            'id': entry_id,
            'original_path': image_path,
            'disease': disease_name,
            'image_num': image_num
        }
        
        if matched_path:
            used_images_by_disease[disease_name].add(str(matched_path))
            mapping_entry['matched_path'] = str(matched_path)
            mapping_entry['relative_path'] = str(matched_path.relative_to(PROJECT_ROOT))
            mapping['path_mappings'].append(mapping_entry)
        else:
            mapping['unmapped'].append(mapping_entry)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 映射报告已保存: {output_path}")
    
    print(f"\n📊 映射统计:")
    print(f"   成功映射: {len(mapping['path_mappings'])}")
    print(f"   未映射: {len(mapping['unmapped'])}")
    
    return mapping


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description='LLaVA LoRA 微调图片路径修复工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析路径映射情况
  python scripts/data/fix_llava_image_paths.py --dry-run
  
  # 修复 JSON 文件中的路径
  python scripts/data/fix_llava_image_paths.py --fix-json
  
  # 创建符号链接目录
  python scripts/data/fix_llava_image_paths.py --create-symlinks
  
  # 生成映射报告
  python scripts/data/fix_llava_image_paths.py --generate-report
        """
    )
    
    parser.add_argument(
        '--json',
        default='datasets/agroinstruct/agroinstruct_train.json',
        help='JSON 数据集路径 (默认: datasets/agroinstruct/agroinstruct_train.json)'
    )
    
    parser.add_argument(
        '--images',
        default='datasets/wheat_data_unified/images',
        help='图片基础目录 (默认: datasets/wheat_data_unified/images)'
    )
    
    parser.add_argument(
        '--output',
        help='输出路径 (默认: 覆盖原文件或使用默认输出目录)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅分析，不修改文件'
    )
    
    parser.add_argument(
        '--fix-json',
        action='store_true',
        help='修复 JSON 文件中的图片路径'
    )
    
    parser.add_argument(
        '--create-symlinks',
        action='store_true',
        help='创建符号链接目录结构'
    )
    
    parser.add_argument(
        '--generate-report',
        action='store_true',
        help='生成路径映射报告'
    )
    
    parser.add_argument(
        '--absolute-paths',
        action='store_true',
        help='使用绝对路径而非相对路径'
    )
    
    args = parser.parse_args()
    
    json_path = PROJECT_ROOT / args.json
    image_base_dir = PROJECT_ROOT / args.images
    
    if not json_path.exists():
        print(f"❌ JSON 文件不存在: {json_path}")
        sys.exit(1)
    
    if not image_base_dir.exists():
        print(f"❌ 图片目录不存在: {image_base_dir}")
        sys.exit(1)
    
    if args.dry_run or not any([args.fix_json, args.create_symlinks, args.generate_report]):
        analyze_dataset(json_path, image_base_dir)
    
    if args.fix_json:
        output_path = Path(args.output) if args.output else None
        fix_json_paths(json_path, image_base_dir, output_path, use_relative=not args.absolute_paths)
    
    if args.create_symlinks:
        output_dir = Path(args.output) if args.output else PROJECT_ROOT / 'data' / 'llava_images'
        create_symlink_structure(json_path, image_base_dir, output_dir)
    
    if args.generate_report:
        output_path = Path(args.output) if args.output else PROJECT_ROOT / 'logs' / 'image_path_mapping.json'
        generate_mapping_report(json_path, image_base_dir, output_path)
    
    print("\n" + "=" * 60)
    print("✅ 完成")
    print("=" * 60)


if __name__ == '__main__':
    main()

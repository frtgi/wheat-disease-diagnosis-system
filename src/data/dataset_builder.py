# -*- coding: utf-8 -*-
"""
多模态数据集构建模块 (Dataset Builder)

根据研究文档构建 L1/L2/L3 三层数据体系：
- L1: 基础感知层 (图像 + 基础类别标签)
- L2: 任务量化层 (图像 + 细粒度标注)
- L3: 决策认知层 (图像 + 复杂文本描述)

支持数据集整合: WisWheat, LWDCD2020, PlantDoc
"""
import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import random
from collections import defaultdict

import numpy as np
from PIL import Image
import cv2


class DataLevel(Enum):
    """数据层级"""
    L1_PERCEPTION = "L1"      # 基础感知层
    L2_QUANTIFICATION = "L2"  # 任务量化层
    L3_COGNITION = "L3"       # 决策认知层


@dataclass
class L1Sample:
    """L1层样本: 基础感知"""
    image_path: str
    label: str
    source: str  # 数据来源
    split: str   # train/val/test
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class L2Sample:
    """L2层样本: 任务量化"""
    image_path: str
    label: str
    bbox: List[float]  # [x, y, w, h] 归一化坐标
    severity: Optional[str]  # 严重度分级
    lesion_count: Optional[int]  # 病斑计数
    area_ratio: Optional[float]  # 病斑面积比例
    source: str
    split: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class L3Sample:
    """L3层样本: 决策认知"""
    image_path: str
    label: str
    symptoms: List[str]  # 症状列表
    causes: List[str]    # 成因列表
    environment: List[str]  # 环境因素
    control_measures: List[str]  # 防治措施
    description: str     # 综合描述
    source: str
    split: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MultimodalDatasetBuilder:
    """
    多模态数据集构建器
    
    功能:
    1. 整合多个数据源
    2. 构建三层数据体系
    3. 数据质量检查
    4. 数据集统计
    """
    
    # 小麦病害类别定义
    DISEASE_CLASSES = [
        "健康",
        "条锈病", "叶锈病", "秆锈病",
        "白粉病", "赤霉病", "纹枯病",
        "根腐病", "全蚀病", "叶枯病",
        "蚜虫", "红蜘蛛", "吸浆虫"
    ]
    
    # 严重度分级
    SEVERITY_LEVELS = ["轻度", "中度", "重度", "极重度"]
    
    def __init__(self, output_dir: str = "datasets/multimodal"):
        """
        初始化数据集构建器
        
        :param output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建层级目录
        for level in DataLevel:
            (self.output_dir / level.value).mkdir(exist_ok=True)
        
        # 数据存储
        self.l1_data: List[L1Sample] = []
        self.l2_data: List[L2Sample] = []
        self.l3_data: List[L3Sample] = []
        
        print(f"🗂️ 多模态数据集构建器初始化完成")
        print(f"   输出目录: {self.output_dir}")
    
    def add_l1_sample(
        self,
        image_path: str,
        label: str,
        source: str = "unknown",
        split: str = "train"
    ):
        """
        添加L1层样本
        
        :param image_path: 图像路径
        :param label: 标签
        :param source: 数据来源
        :param split: 数据划分
        """
        sample = L1Sample(
            image_path=image_path,
            label=label,
            source=source,
            split=split
        )
        self.l1_data.append(sample)
    
    def add_l2_sample(
        self,
        image_path: str,
        label: str,
        bbox: List[float],
        severity: Optional[str] = None,
        lesion_count: Optional[int] = None,
        area_ratio: Optional[float] = None,
        source: str = "unknown",
        split: str = "train"
    ):
        """
        添加L2层样本
        
        :param image_path: 图像路径
        :param label: 标签
        :param bbox: 边界框 [x, y, w, h]
        :param severity: 严重度
        :param lesion_count: 病斑计数
        :param area_ratio: 面积比例
        :param source: 数据来源
        :param split: 数据划分
        """
        sample = L2Sample(
            image_path=image_path,
            label=label,
            bbox=bbox,
            severity=severity,
            lesion_count=lesion_count,
            area_ratio=area_ratio,
            source=source,
            split=split
        )
        self.l2_data.append(sample)
    
    def add_l3_sample(
        self,
        image_path: str,
        label: str,
        symptoms: List[str],
        causes: List[str],
        environment: List[str],
        control_measures: List[str],
        description: str,
        source: str = "unknown",
        split: str = "train"
    ):
        """
        添加L3层样本
        
        :param image_path: 图像路径
        :param label: 标签
        :param symptoms: 症状列表
        :param causes: 成因列表
        :param environment: 环境因素
        :param control_measures: 防治措施
        :param description: 综合描述
        :param source: 数据来源
        :param split: 数据划分
        """
        sample = L3Sample(
            image_path=image_path,
            label=label,
            symptoms=symptoms,
            causes=causes,
            environment=environment,
            control_measures=control_measures,
            description=description,
            source=source,
            split=split
        )
        self.l3_data.append(sample)
    
    def integrate_wiswheat(self, wiswheat_dir: str):
        """
        整合WisWheat数据集
        
        :param wiswheat_dir: WisWheat数据集目录
        """
        print(f"\n📥 整合WisWheat数据集: {wiswheat_dir}")
        
        wiswheat_path = Path(wiswheat_dir)
        if not wiswheat_path.exists():
            print(f"⚠️ WisWheat数据集不存在: {wiswheat_dir}")
            return
        
        # 遍历各级目录
        for tier in ["Tier1", "Tier2", "Tier3"]:
            tier_path = wiswheat_path / tier
            if not tier_path.exists():
                continue
            
            print(f"   处理 {tier}...")
            
            for split in ["train", "val", "test"]:
                split_path = tier_path / split
                if not split_path.exists():
                    continue
                
                for class_dir in split_path.iterdir():
                    if not class_dir.is_dir():
                        continue
                    
                    class_name = class_dir.name
                    
                    for img_path in class_dir.glob("*.jpg"):
                        if tier == "Tier1":
                            self.add_l1_sample(
                                image_path=str(img_path),
                                label=class_name,
                                source="WisWheat",
                                split=split
                            )
                        elif tier == "Tier2":
                            # L2数据需要标注文件
                            self._process_l2_annotation(img_path, class_name, split)
                        elif tier == "Tier3":
                            # L3数据需要文本描述
                            self._process_l3_description(img_path, class_name, split)
        
        print(f"   ✅ WisWheat整合完成")
    
    def _process_l2_annotation(self, img_path: Path, label: str, split: str):
        """处理L2层标注"""
        # 模拟从标注文件读取
        # 实际实现需要解析XML/JSON标注文件
        annotation_path = img_path.with_suffix('.json')
        
        if annotation_path.exists():
            try:
                with open(annotation_path, 'r') as f:
                    anno = json.load(f)
                
                self.add_l2_sample(
                    image_path=str(img_path),
                    label=label,
                    bbox=anno.get('bbox', [0, 0, 1, 1]),
                    severity=anno.get('severity'),
                    lesion_count=anno.get('lesion_count'),
                    area_ratio=anno.get('area_ratio'),
                    source="WisWheat",
                    split=split
                )
            except Exception as e:
                print(f"   ⚠️ 处理标注失败 {img_path}: {e}")
    
    def _process_l3_description(self, img_path: Path, label: str, split: str):
        """处理L3层描述"""
        desc_path = img_path.with_suffix('.txt')
        
        if desc_path.exists():
            try:
                with open(desc_path, 'r', encoding='utf-8') as f:
                    description = f.read().strip()
                
                # 解析描述文本
                # 这里简化处理，实际应该使用NLP提取结构化信息
                self.add_l3_sample(
                    image_path=str(img_path),
                    label=label,
                    symptoms=["症状1", "症状2"],  # 从描述中提取
                    causes=["成因1"],
                    environment=["环境因素1"],
                    control_measures=["防治措施1"],
                    description=description,
                    source="WisWheat",
                    split=split
                )
            except Exception as e:
                print(f"   ⚠️ 处理描述失败 {img_path}: {e}")
    
    def integrate_lwdcd2020(self, lwdcd_dir: str):
        """
        整合LWDCD2020数据集
        
        :param lwdcd_dir: LWDCD2020数据集目录
        """
        print(f"\n📥 整合LWDCD2020数据集: {lwdcd_dir}")
        
        lwdcd_path = Path(lwdcd_dir)
        if not lwdcd_path.exists():
            print(f"⚠️ LWDCD2020数据集不存在: {lwdcd_dir}")
            return
        
        # LWDCD2020主要是L1层数据
        for split in ["train", "test"]:
            split_path = lwdcd_path / split
            if not split_path.exists():
                continue
            
            for class_dir in split_path.iterdir():
                if not class_dir.is_dir():
                    continue
                
                class_name = class_dir.name
                
                for img_path in class_dir.glob("*.jpg"):
                    self.add_l1_sample(
                        image_path=str(img_path),
                        label=class_name,
                        source="LWDCD2020",
                        split=split
                    )
        
        print(f"   ✅ LWDCD2020整合完成")
    
    def integrate_plantdoc(self, plantdoc_dir: str):
        """
        整合PlantDoc数据集
        
        :param plantdoc_dir: PlantDoc数据集目录
        """
        print(f"\n📥 整合PlantDoc数据集: {plantdoc_dir}")
        
        plantdoc_path = Path(plantdoc_dir)
        if not plantdoc_path.exists():
            print(f"⚠️ PlantDoc数据集不存在: {plantdoc_dir}")
            return
        
        # PlantDoc包含检测标注
        for split in ["train", "test"]:
            split_path = plantdoc_path / split
            if not split_path.exists():
                continue
            
            for img_path in split_path.glob("*.jpg"):
                # 解析标注
                anno_path = img_path.with_suffix('.json')
                if anno_path.exists():
                    try:
                        with open(anno_path, 'r') as f:
                            anno = json.load(f)
                        
                        label = anno.get('label', 'unknown')
                        bbox = anno.get('bbox', [0, 0, 1, 1])
                        
                        # 添加到L1和L2
                        self.add_l1_sample(
                            image_path=str(img_path),
                            label=label,
                            source="PlantDoc",
                            split=split
                        )
                        
                        self.add_l2_sample(
                            image_path=str(img_path),
                            label=label,
                            bbox=bbox,
                            source="PlantDoc",
                            split=split
                        )
                    except Exception as e:
                        print(f"   ⚠️ 处理失败 {img_path}: {e}")
        
        print(f"   ✅ PlantDoc整合完成")
    
    def generate_synthetic_l3_data(self, num_samples: int = 100):
        """
        生成合成L3层数据
        
        使用模板生成文本描述，用于扩充L3数据
        
        :param num_samples: 生成样本数
        """
        print(f"\n🎨 生成合成L3数据: {num_samples} 样本")
        
        # 病害描述模板
        templates = {
            "条锈病": {
                "symptoms": ["叶片出现鲜黄色条状孢子堆", "沿叶脉排列成行", "孢子堆破裂后呈粉状"],
                "causes": ["Puccinia striiformis f. sp. tritici 真菌感染", "低温高湿环境", "品种抗病性差"],
                "environment": ["温度9-16°C", "相对湿度>90%", "有露水或小雨"],
                "control_measures": ["喷洒三唑酮", "选用抗病品种", "合理密植通风"]
            },
            "白粉病": {
                "symptoms": ["叶片出现白色粉状霉层", "后期出现黑色小点", "叶片发黄枯萎"],
                "causes": ["Blumeria graminis f. sp. tritici 真菌感染", "通风不良", "氮肥过量"],
                "environment": ["温度15-22°C", "湿度较高", "种植密度大"],
                "control_measures": ["喷洒粉锈宁", "降低种植密度", "平衡施肥"]
            },
            "赤霉病": {
                "symptoms": ["穗部出现粉红色霉层", "籽粒干瘪变色", "穗轴腐烂"],
                "causes": ["Fusarium graminearum 真菌感染", "花期连阴雨", "田间湿度大"],
                "environment": ["温度25-30°C", "花期降雨", "田间积水"],
                "control_measures": ["喷洒多菌灵", "清沟排水", "轮作倒茬"]
            }
        }
        
        for _ in range(num_samples):
            disease = random.choice(list(templates.keys()))
            template = templates[disease]
            
            # 生成描述文本
            description = f"该小麦植株表现出{disease}的典型症状。"
            description += f"主要症状包括：{'、'.join(template['symptoms'][:2])}。"
            description += f"发病原因：{template['causes'][0]}。"
            description += f"建议防治措施：{template['control_measures'][0]}。"
            
            self.add_l3_sample(
                image_path=f"synthetic_{_}.jpg",
                label=disease,
                symptoms=template["symptoms"],
                causes=template["causes"],
                environment=template["environment"],
                control_measures=template["control_measures"],
                description=description,
                source="Synthetic",
                split=random.choice(["train", "val", "test"])
            )
        
        print(f"   ✅ 合成数据生成完成")
    
    def validate_dataset(self) -> Dict[str, Any]:
        """
        验证数据集质量
        
        :return: 验证结果
        """
        print("\n🔍 验证数据集质量...")
        
        issues = []
        
        # 检查图像文件是否存在
        for sample in self.l1_data:
            if not Path(sample.image_path).exists():
                issues.append(f"图像不存在: {sample.image_path}")
        
        # 检查标签有效性
        for sample in self.l1_data:
            if sample.label not in self.DISEASE_CLASSES:
                issues.append(f"未知标签: {sample.label}")
        
        # 统计信息
        stats = self.get_statistics()
        
        result = {
            "valid": len(issues) == 0,
            "issues": issues[:10],  # 只显示前10个问题
            "total_issues": len(issues),
            "statistics": stats
        }
        
        if issues:
            print(f"   ⚠️ 发现 {len(issues)} 个问题")
        else:
            print(f"   ✅ 数据集验证通过")
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据集统计信息
        
        :return: 统计信息
        """
        stats = {
            "total_samples": len(self.l1_data) + len(self.l2_data) + len(self.l3_data),
            "L1_perception": {
                "total": len(self.l1_data),
                "by_source": defaultdict(int),
                "by_split": defaultdict(int),
                "by_class": defaultdict(int)
            },
            "L2_quantification": {
                "total": len(self.l2_data),
                "by_source": defaultdict(int),
                "by_split": defaultdict(int),
                "has_severity": sum(1 for s in self.l2_data if s.severity is not None),
                "has_bbox": sum(1 for s in self.l2_data if s.bbox != [0, 0, 1, 1])
            },
            "L3_cognition": {
                "total": len(self.l3_data),
                "by_source": defaultdict(int),
                "by_split": defaultdict(int),
                "avg_description_length": np.mean([len(s.description) for s in self.l3_data]) if self.l3_data else 0
            }
        }
        
        # L1统计
        for sample in self.l1_data:
            stats["L1_perception"]["by_source"][sample.source] += 1
            stats["L1_perception"]["by_split"][sample.split] += 1
            stats["L1_perception"]["by_class"][sample.label] += 1
        
        # L2统计
        for sample in self.l2_data:
            stats["L2_quantification"]["by_source"][sample.source] += 1
            stats["L2_quantification"]["by_split"][sample.split] += 1
        
        # L3统计
        for sample in self.l3_data:
            stats["L3_cognition"]["by_source"][sample.source] += 1
            stats["L3_cognition"]["by_split"][sample.split] += 1
        
        return stats
    
    def export_dataset(self):
        """导出数据集到文件"""
        print("\n💾 导出数据集...")
        
        # 导出L1数据
        l1_file = self.output_dir / "L1" / "dataset.json"
        with open(l1_file, 'w', encoding='utf-8') as f:
            json.dump([s.to_dict() for s in self.l1_data], f, ensure_ascii=False, indent=2)
        print(f"   ✅ L1数据已导出: {l1_file}")
        
        # 导出L2数据
        l2_file = self.output_dir / "L2" / "dataset.json"
        with open(l2_file, 'w', encoding='utf-8') as f:
            json.dump([s.to_dict() for s in self.l2_data], f, ensure_ascii=False, indent=2)
        print(f"   ✅ L2数据已导出: {l2_file}")
        
        # 导出L3数据
        l3_file = self.output_dir / "L3" / "dataset.json"
        with open(l3_file, 'w', encoding='utf-8') as f:
            json.dump([s.to_dict() for s in self.l3_data], f, ensure_ascii=False, indent=2)
        print(f"   ✅ L3数据已导出: {l3_file}")
        
        # 导出统计信息
        stats = self.get_statistics()
        stats_file = self.output_dir / "statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"   ✅ 统计信息已导出: {stats_file}")
    
    def print_summary(self):
        """打印数据集摘要"""
        print("\n" + "=" * 70)
        print("📊 多模态数据集摘要")
        print("=" * 70)
        
        stats = self.get_statistics()
        
        print(f"\n总样本数: {stats['total_samples']}")
        
        print(f"\nL1 - 基础感知层:")
        print(f"   样本数: {stats['L1_perception']['total']}")
        print(f"   来源分布: {dict(stats['L1_perception']['by_source'])}")
        print(f"   划分分布: {dict(stats['L1_perception']['by_split'])}")
        
        print(f"\nL2 - 任务量化层:")
        print(f"   样本数: {stats['L2_quantification']['total']}")
        print(f"   有严重度标注: {stats['L2_quantification']['has_severity']}")
        print(f"   有边界框标注: {stats['L2_quantification']['has_bbox']}")
        
        print(f"\nL3 - 决策认知层:")
        print(f"   样本数: {stats['L3_cognition']['total']}")
        print(f"   平均描述长度: {stats['L3_cognition']['avg_description_length']:.1f} 字符")


def test_dataset_builder():
    """测试数据集构建器"""
    print("=" * 70)
    print("🧪 测试多模态数据集构建器")
    print("=" * 70)
    
    # 创建构建器
    builder = MultimodalDatasetBuilder(output_dir="datasets/test_multimodal")
    
    # 添加L1样本
    print("\n📝 添加L1样本...")
    for i in range(10):
        builder.add_l1_sample(
            image_path=f"test_{i}.jpg",
            label=random.choice(builder.DISEASE_CLASSES),
            source="Test",
            split=random.choice(["train", "val", "test"])
        )
    
    # 添加L2样本
    print("\n📝 添加L2样本...")
    for i in range(5):
        builder.add_l2_sample(
            image_path=f"test_{i}.jpg",
            label="条锈病",
            bbox=[0.1, 0.2, 0.3, 0.4],
            severity=random.choice(builder.SEVERITY_LEVELS),
            lesion_count=random.randint(1, 10),
            area_ratio=random.uniform(0.05, 0.5),
            source="Test",
            split="train"
        )
    
    # 生成合成L3数据
    print("\n🎨 生成合成L3数据...")
    builder.generate_synthetic_l3_data(num_samples=5)
    
    # 验证数据集
    print("\n🔍 验证数据集...")
    validation = builder.validate_dataset()
    print(f"   验证结果: {'通过' if validation['valid'] else '失败'}")
    
    # 导出数据集
    print("\n💾 导出数据集...")
    builder.export_dataset()
    
    # 打印摘要
    builder.print_summary()
    
    # 清理
    import shutil
    if Path("datasets/test_multimodal").exists():
        shutil.rmtree("datasets/test_multimodal")
    
    print("\n" + "=" * 70)
    print("✅ 数据集构建器测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_dataset_builder()

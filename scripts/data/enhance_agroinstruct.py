# -*- coding: utf-8 -*-
"""
AgroInstruct 数据集增强脚本

基于知识图谱生成更丰富的指令数据集：
1. 多轮对话数据
2. 复杂推理链数据
3. 多病害对比数据
4. 环境因素关联数据

使用方法:
    python enhance_agroinstruct.py --input_dir ./datasets/agroinstruct --output_dir ./datasets/agroinstruct_enhanced
"""
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import copy


def load_knowledge_graph(kg_path: str) -> tuple:
    """
    加载知识图谱
    
    Args:
        kg_path: 知识图谱路径
    
    Returns:
        (实体字典, 关系列表) 元组
    """
    with open(Path(kg_path) / "entities.json", 'r', encoding='utf-8') as f:
        entities = json.load(f)
    
    with open(Path(kg_path) / "triples.json", 'r', encoding='utf-8') as f:
        triples = json.load(f)
    
    return entities, triples


def build_relation_index(triples: List[Dict]) -> Dict:
    """
    构建关系索引以便快速查询
    
    Args:
        triples: 三元组列表
    
    Returns:
        关系索引字典
    """
    index = {
        "by_head": {},
        "by_tail": {},
        "by_relation": {}
    }
    
    for triple in triples:
        head = triple["head"]
        tail = triple["tail"]
        relation = triple["relation"]
        
        if head not in index["by_head"]:
            index["by_head"][head] = []
        index["by_head"][head].append(triple)
        
        if tail not in index["by_tail"]:
            index["by_tail"][tail] = []
        index["by_tail"][tail].append(triple)
        
        if relation not in index["by_relation"]:
            index["by_relation"][relation] = []
        index["by_relation"][relation].append(triple)
    
    return index


class AgroInstructEnhancer:
    """
    AgroInstruct 数据集增强器
    """
    
    def __init__(self, entities: Dict, triples: List[Dict]):
        """
        初始化增强器
        
        Args:
            entities: 实体字典
            triples: 三元组列表
        """
        self.entities = entities
        self.triples = triples
        self.relation_index = build_relation_index(triples)
        
        self.diseases = {k: v for k, v in entities.items() if v.get("type") == "Disease"}
        self.pests = {k: v for k, v in entities.items() if v.get("type") == "Pest"}
        self.symptoms = {k: v for k, v in entities.items() if v.get("type") == "Symptom"}
        self.controls = {k: v for k, v in entities.items() if v.get("type") == "ControlMeasure"}
        self.environments = {k: v for k, v in entities.items() if v.get("type") == "Environment"}
        self.varieties = {k: v for k, v in entities.items() if v.get("type") == "Variety"}
        self.regions = {k: v for k, v in entities.items() if v.get("type") == "Region"}
    
    def get_disease_symptoms(self, disease_id: str) -> List[Dict]:
        """
        获取病害的症状列表
        
        Args:
            disease_id: 病害ID
        
        Returns:
            症状列表
        """
        triples = self.relation_index["by_head"].get(disease_id, [])
        return [self.entities[t["tail"]] for t in triples 
                if t["relation"] == "HAS_SYMPTOM" and t["tail"] in self.entities]
    
    def get_disease_controls(self, disease_id: str) -> List[Dict]:
        """
        获取病害的防治措施
        
        Args:
            disease_id: 病害ID
        
        Returns:
            防治措施列表
        """
        triples = self.relation_index["by_head"].get(disease_id, [])
        controls = []
        for t in triples:
            if t["relation"] == "TREATED_BY" and t["tail"] in self.entities:
                controls.append(self.entities[t["tail"]])
        return controls
    
    def get_disease_pathogen(self, disease_id: str) -> Optional[Dict]:
        """
        获取病害的病原体
        
        Args:
            disease_id: 病害ID
        
        Returns:
            病原体信息
        """
        triples = self.relation_index["by_head"].get(disease_id, [])
        for t in triples:
            if t["relation"] == "CAUSED_BY" and t["tail"] in self.entities:
                return self.entities[t["tail"]]
        return None
    
    def get_disease_environment(self, disease_id: str) -> List[Dict]:
        """
        获取病害的有利环境条件
        
        Args:
            disease_id: 病害ID
        
        Returns:
            环境条件列表
        """
        pathogen = self.get_disease_pathogen(disease_id)
        if not pathogen:
            return []
        
        triples = self.relation_index["by_head"].get(pathogen["id"], [])
        return [self.entities[t["tail"]] for t in triples 
                if t["relation"] == "FAVORS" and t["tail"] in self.entities]
    
    def generate_diagnosis_conversation(self, disease: Dict, image_path: str) -> Dict:
        """
        生成诊断对话数据
        
        Args:
            disease: 病害实体
            image_path: 图像路径
        
        Returns:
            对话数据
        """
        symptoms = self.get_disease_symptoms(disease["id"])
        pathogen = self.get_disease_pathogen(disease["id"])
        
        symptom_desc = "、".join([s["name"] for s in symptoms[:3]]) if symptoms else "未知症状"
        
        conversation = {
            "id": f"diag_{disease['id']}_{random.randint(1000, 9999)}",
            "image_path": image_path,
            "conversations": [
                {
                    "role": "user",
                    "content": f"<image>\n检测模型在图像中识别出疑似【{disease['name']}】症状，主要特征包括：{symptom_desc}。\n\n请分析这是什么病害？严重程度如何？"
                },
                {
                    "role": "assistant",
                    "content": self._generate_diagnosis_response(disease, symptoms, pathogen)
                }
            ],
            "metadata": {
                "disease": disease["name"],
                "question_type": "diagnosis_detailed",
                "english_name": disease["properties"].get("english_name", "")
            }
        }
        
        return conversation
    
    def _generate_diagnosis_response(self, disease: Dict, symptoms: List[Dict], 
                                      pathogen: Optional[Dict]) -> str:
        """
        生成诊断回复
        
        Args:
            disease: 病害实体
            symptoms: 症状列表
            pathogen: 病原体
        
        Returns:
            诊断回复文本
        """
        lines = [
            "## 诊断结果",
            "",
            f"根据图像特征分析，这是**{disease['name']}**的症状。",
        ]
        
        if pathogen:
            lines.append(f"**病原体**：{pathogen['name']} ({pathogen['properties'].get('scientific_name', '')})")
        
        lines.extend([
            "",
            "**典型症状**："
        ])
        
        for i, symptom in enumerate(symptoms[:5], 1):
            desc = symptom["properties"].get("description", "")
            lines.append(f"{i}. {symptom['name']}" + (f"：{desc}" if desc else ""))
        
        lines.extend([
            "",
            "**发病条件**："
        ])
        
        envs = self.get_disease_environment(disease["id"])
        for env in envs[:3]:
            condition = env["properties"].get("condition", "")
            lines.append(f"- {env['name']}" + (f"（{condition}）" if condition else ""))
        
        lines.extend([
            "",
            "---",
            "*诊断结果由 IWDDA 智能诊断系统生成*"
        ])
        
        return "\n".join(lines)
    
    def generate_treatment_conversation(self, disease: Dict, image_path: str) -> Dict:
        """
        生成防治对话数据
        
        Args:
            disease: 病害实体
            image_path: 图像路径
        
        Returns:
            对话数据
        """
        controls = self.get_disease_controls(disease["id"])
        
        conversation = {
            "id": f"treat_{disease['id']}_{random.randint(1000, 9999)}",
            "image_path": image_path,
            "conversations": [
                {
                    "role": "user",
                    "content": f"<image>\n经诊断确认为【{disease['name']}】，请给出详细的防治方案。"
                },
                {
                    "role": "assistant",
                    "content": self._generate_treatment_response(disease, controls)
                }
            ],
            "metadata": {
                "disease": disease["name"],
                "question_type": "treatment_detailed",
                "english_name": disease["properties"].get("english_name", "")
            }
        }
        
        return conversation
    
    def _generate_treatment_response(self, disease: Dict, controls: List[Dict]) -> str:
        """
        生成防治回复
        
        Args:
            disease: 病害实体
            controls: 防治措施列表
        
        Returns:
            防治回复文本
        """
        lines = [
            f"## {disease['name']}防治方案",
            ""
        ]
        
        chemical_controls = [c for c in controls if c["properties"].get("type") == "化学防治"]
        bio_controls = [c for c in controls if c["properties"].get("type") == "生物防治"]
        agri_controls = [c for c in controls if c["properties"].get("type") == "农业防治"]
        
        if chemical_controls:
            lines.append("### 化学防治")
            for control in chemical_controls[:4]:
                trade_name = control["properties"].get("trade_name", control["name"])
                rate = control["properties"].get("application_rate", "")
                lines.append(f"- **{control['name']}**（{trade_name}）")
                if rate:
                    lines.append(f"  用量：{rate}")
            lines.append("")
        
        if bio_controls:
            lines.append("### 生物防治")
            for control in bio_controls:
                lines.append(f"- {control['name']}")
            lines.append("")
        
        if agri_controls:
            lines.append("### 农业措施")
            for control in agri_controls:
                desc = control["properties"].get("description", "")
                lines.append(f"- {control['name']}" + (f"：{desc}" if desc else ""))
            lines.append("")
        
        lines.extend([
            "### 注意事项",
            "- 施药时间：选择无风晴天上午",
            "- 安全间隔：收获前14天停止用药",
            "- 轮换用药：避免产生抗药性",
            "",
            "---",
            "*防治方案由 IWDDA 智能诊断系统生成*"
        ])
        
        return "\n".join(lines)
    
    def generate_comparison_conversation(self, disease1: Dict, disease2: Dict, 
                                          image_path: str) -> Dict:
        """
        生成病害对比对话数据
        
        Args:
            disease1: 第一个病害
            disease2: 第二个病害
            image_path: 图像路径
        
        Returns:
            对话数据
        """
        symptoms1 = self.get_disease_symptoms(disease1["id"])
        symptoms2 = self.get_disease_symptoms(disease2["id"])
        
        conversation = {
            "id": f"compare_{disease1['id']}_{disease2['id']}_{random.randint(1000, 9999)}",
            "image_path": image_path,
            "conversations": [
                {
                    "role": "user",
                    "content": f"<image>\n请对比分析【{disease1['name']}】和【{disease2['name']}】的区别，帮助我准确识别。"
                },
                {
                    "role": "assistant",
                    "content": self._generate_comparison_response(disease1, disease2, symptoms1, symptoms2)
                }
            ],
            "metadata": {
                "disease": f"{disease1['name']} vs {disease2['name']}",
                "question_type": "comparison",
                "english_name": f"{disease1['properties'].get('english_name', '')} vs {disease2['properties'].get('english_name', '')}"
            }
        }
        
        return conversation
    
    def _generate_comparison_response(self, disease1: Dict, disease2: Dict,
                                       symptoms1: List[Dict], symptoms2: List[Dict]) -> str:
        """
        生成对比回复
        
        Args:
            disease1: 第一个病害
            disease2: 第二个病害
            symptoms1: 第一个病害的症状
            symptoms2: 第二个病害的症状
        
        Returns:
            对比回复文本
        """
        lines = [
            "## 病害对比分析",
            "",
            f"### {disease1['name']} vs {disease2['name']}",
            "",
            "| 特征 | " + disease1['name'] + " | " + disease2['name'] + " |",
            "|------|------|------|"
        ]
        
        pathogen1 = self.get_disease_pathogen(disease1["id"])
        pathogen2 = self.get_disease_pathogen(disease2["id"])
        
        lines.append(f"| 病原体 | {pathogen1['name'] if pathogen1 else '未知'} | {pathogen2['name'] if pathogen2 else '未知'} |")
        
        symptom1_str = "、".join([s["name"] for s in symptoms1[:3]]) if symptoms1 else "未知"
        symptom2_str = "、".join([s["name"] for s in symptoms2[:3]]) if symptoms2 else "未知"
        lines.append(f"| 主要症状 | {symptom1_str} | {symptom2_str} |")
        
        period1 = disease1["properties"].get("high_risk_period", "未知")
        period2 = disease2["properties"].get("high_risk_period", "未知")
        lines.append(f"| 高发期 | {period1} | {period2} |")
        
        lines.extend([
            "",
            "### 识别要点",
            "",
            f"**{disease1['name']}**：",
        ])
        
        for s in symptoms1[:3]:
            desc = s["properties"].get("description", "")
            lines.append(f"- {s['name']}" + (f"：{desc}" if desc else ""))
        
        lines.extend([
            "",
            f"**{disease2['name']}**：",
        ])
        
        for s in symptoms2[:3]:
            desc = s["properties"].get("description", "")
            lines.append(f"- {s['name']}" + (f"：{desc}" if desc else ""))
        
        lines.extend([
            "",
            "---",
            "*对比分析由 IWDDA 智能诊断系统生成*"
        ])
        
        return "\n".join(lines)
    
    def generate_environment_conversation(self, disease: Dict, image_path: str) -> Dict:
        """
        生成环境因素关联对话数据
        
        Args:
            disease: 病害实体
            image_path: 图像路径
        
        Returns:
            对话数据
        """
        envs = self.get_disease_environment(disease["id"])
        
        conversation = {
            "id": f"env_{disease['id']}_{random.randint(1000, 9999)}",
            "image_path": image_path,
            "conversations": [
                {
                    "role": "user",
                    "content": f"<image>\n当前田间发现【{disease['name']}】症状，请问在什么环境条件下容易发生？如何通过环境管理预防？"
                },
                {
                    "role": "assistant",
                    "content": self._generate_environment_response(disease, envs)
                }
            ],
            "metadata": {
                "disease": disease["name"],
                "question_type": "environment",
                "english_name": disease["properties"].get("english_name", "")
            }
        }
        
        return conversation
    
    def _generate_environment_response(self, disease: Dict, envs: List[Dict]) -> str:
        """
        生成环境因素回复
        
        Args:
            disease: 病害实体
            envs: 环境条件列表
        
        Returns:
            环境因素回复文本
        """
        lines = [
            f"## {disease['name']}环境因素分析",
            "",
            "### 有利发病的环境条件",
            ""
        ]
        
        for env in envs:
            condition = env["properties"].get("condition", "")
            lines.append(f"- **{env['name']}**" + (f"：{condition}" if condition else ""))
        
        lines.extend([
            "",
            "### 环境管理预防措施",
            ""
        ])
        
        if disease["properties"].get("high_risk_period"):
            lines.append(f"- 避开高发期：{disease['properties']['high_risk_period']}")
        
        lines.extend([
            "- 改善通风：合理密植，增加田间通风",
            "- 控制湿度：及时排水，避免田间积水",
            "- 温度管理：根据天气变化及时采取防护措施",
            "",
            "---",
            "*环境分析由 IWDDA 智能诊断系统生成*"
        ])
        
        return "\n".join(lines)
    
    def generate_multiturn_conversation(self, disease: Dict, image_path: str) -> Dict:
        """
        生成多轮对话数据
        
        Args:
            disease: 病害实体
            image_path: 图像路径
        
        Returns:
            多轮对话数据
        """
        symptoms = self.get_disease_symptoms(disease["id"])
        controls = self.get_disease_controls(disease["id"])
        pathogen = self.get_disease_pathogen(disease["id"])
        
        conversation = {
            "id": f"multi_{disease['id']}_{random.randint(1000, 9999)}",
            "image_path": image_path,
            "conversations": [
                {
                    "role": "user",
                    "content": f"<image>\n这是什么病害？"
                },
                {
                    "role": "assistant",
                    "content": f"根据图像特征，这是**{disease['name']}**。" + 
                              (f"\n\n主要症状包括：" + "、".join([s["name"] for s in symptoms[:3]]) if symptoms else "")
                },
                {
                    "role": "user",
                    "content": "严重程度如何？"
                },
                {
                    "role": "assistant",
                    "content": "根据病斑覆盖面积判断，当前处于**中度**发病阶段。\n\n建议及时采取防治措施，避免病情进一步扩展。"
                },
                {
                    "role": "user",
                    "content": "应该用什么药防治？"
                },
                {
                    "role": "assistant",
                    "content": self._generate_treatment_response(disease, controls)
                }
            ],
            "metadata": {
                "disease": disease["name"],
                "question_type": "multiturn",
                "english_name": disease["properties"].get("english_name", ""),
                "turn_count": 3
            }
        }
        
        return conversation


def enhance_dataset(input_dir: str, output_dir: str, kg_path: str, 
                    multiplier: int = 3) -> Dict:
    """
    增强数据集
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        kg_path: 知识图谱路径
        multiplier: 数据增强倍数
    
    Returns:
        增强统计信息
    """
    entities, triples = load_knowledge_graph(kg_path)
    enhancer = AgroInstructEnhancer(entities, triples)
    
    with open(Path(input_dir) / "agroinstruct_train.json", 'r', encoding='utf-8') as f:
        original_train = json.load(f)
    
    with open(Path(input_dir) / "agroinstruct_val.json", 'r', encoding='utf-8') as f:
        original_val = json.load(f)
    
    enhanced_train = list(original_train)
    enhanced_val = list(original_val)
    
    new_samples = []
    
    disease_list = list(enhancer.diseases.values())
    pest_list = list(enhancer.pests.values())
    
    for disease in disease_list:
        for _ in range(multiplier):
            image_path = f"images/{disease['name']}/sample_{random.randint(1, 1000)}.jpg"
            
            new_samples.append(enhancer.generate_diagnosis_conversation(disease, image_path))
            
            new_samples.append(enhancer.generate_treatment_conversation(disease, image_path))
            
            new_samples.append(enhancer.generate_environment_conversation(disease, image_path))
            
            new_samples.append(enhancer.generate_multiturn_conversation(disease, image_path))
    
    for i, disease1 in enumerate(disease_list):
        for disease2 in disease_list[i+1:]:
            if random.random() < 0.3:
                image_path = f"images/comparison/{disease1['name']}_{disease2['name']}.jpg"
                new_samples.append(enhancer.generate_comparison_conversation(
                    disease1, disease2, image_path
                ))
    
    random.shuffle(new_samples)
    
    split_idx = int(len(new_samples) * 0.9)
    enhanced_train.extend(new_samples[:split_idx])
    enhanced_val.extend(new_samples[split_idx:])
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(Path(output_dir) / "agroinstruct_train.json", 'w', encoding='utf-8') as f:
        json.dump(enhanced_train, f, indent=2, ensure_ascii=False)
    
    with open(Path(output_dir) / "agroinstruct_val.json", 'w', encoding='utf-8') as f:
        json.dump(enhanced_val, f, indent=2, ensure_ascii=False)
    
    stats = {
        "original_train": len(original_train),
        "original_val": len(original_val),
        "new_samples": len(new_samples),
        "enhanced_train": len(enhanced_train),
        "enhanced_val": len(enhanced_val),
        "disease_count": len(disease_list),
        "pest_count": len(pest_list),
        "multiplier": multiplier,
        "created_at": datetime.now().isoformat()
    }
    
    with open(Path(output_dir) / "enhancement_stats.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    return stats


def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="增强 AgroInstruct 数据集")
    parser.add_argument("--input_dir", type=str, 
                        default="./datasets/agroinstruct",
                        help="输入数据集目录")
    parser.add_argument("--output_dir", type=str, 
                        default="./datasets/agroinstruct_enhanced",
                        help="输出数据集目录")
    parser.add_argument("--kg_path", type=str, 
                        default="./checkpoints/knowledge_graph",
                        help="知识图谱路径")
    parser.add_argument("--multiplier", type=int, default=3,
                        help="数据增强倍数")
    args = parser.parse_args()
    
    print("=" * 70)
    print("📊 AgroInstruct 数据集增强")
    print("=" * 70)
    
    stats = enhance_dataset(
        args.input_dir, 
        args.output_dir, 
        args.kg_path,
        args.multiplier
    )
    
    print(f"\n📈 增强统计:")
    print(f"   原始训练集: {stats['original_train']} → {stats['enhanced_train']}")
    print(f"   原始验证集: {stats['original_val']} → {stats['enhanced_val']}")
    print(f"   新增样本: {stats['new_samples']}")
    print(f"   病害类型: {stats['disease_count']}")
    print(f"   虫害类型: {stats['pest_count']}")
    
    print(f"\n✅ 数据集增强完成!")


if __name__ == "__main__":
    main()

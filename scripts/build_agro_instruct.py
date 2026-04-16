# -*- coding: utf-8 -*-
"""
AgroInstruct 数据集构建工具
用于生成大规模农业指令微调数据集

根据文档第4章：认知模块 - 基于LLaVA的多模态语义理解
数据集应包含：
1. 多种病害类型的图文对
2. 复杂诊断场景的指令数据
3. 专家构建或GPT-4生成的问答对
"""
import os
import json
import random
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class AgroInstructBuilder:
    """
    AgroInstruct数据集构建器
    
    生成用于Agri-LLaVA两阶段训练的指令数据：
    - Phase 1: 特征对齐预训练（图像-描述对）
    - Phase 2: 端到端指令微调（复杂问答对）
    """
    
    def __init__(self, output_dir: str = "datasets/agri_instruct"):
        """
        初始化数据集构建器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 小麦病害知识库
        self.disease_knowledge = self._build_disease_knowledge()
        
        # 指令模板
        self.instruction_templates = self._build_instruction_templates()
    
    def _build_disease_knowledge(self) -> Dict:
        """
        构建病害知识库
        
        Returns:
            病害知识字典
        """
        return {
            "stripe_rust": {
                "name_cn": "小麦条锈病",
                "name_en": "Stripe Rust",
                "pathogen": "条形柄锈菌 (Puccinia striiformis)",
                "symptoms": [
                    "叶片出现鲜黄色条状孢子堆",
                    "沿叶脉平行排列成行",
                    "孢子堆较小，呈椭圆形",
                    "严重时叶片枯黄"
                ],
                "environment": {
                    "temperature": "9-16°C",
                    "humidity": "高湿环境",
                    "weather": "连阴雨天气"
                },
                "treatment": {
                    "chemical": [
                        "三唑酮（粉锈宁）15%可湿性粉剂，每亩100-150克",
                        "戊唑醇 25%乳油，每亩60-80毫升",
                        "丙环唑 25%乳油，每亩30-40毫升"
                    ],
                    "biological": [
                        "选用抗病品种",
                        "合理密植，改善通风透光"
                    ],
                    "cultural": [
                        "及时清除病残体",
                        "避免过量施氮肥",
                        "适时播种，避开病害高发期"
                    ]
                },
                "prevention": [
                    "选用抗病品种",
                    "种子处理：用粉锈宁拌种",
                    "发病初期及时喷药"
                ]
            },
            "leaf_rust": {
                "name_cn": "小麦叶锈病",
                "name_en": "Leaf Rust",
                "pathogen": "小麦隐匿柄锈菌 (Puccinia triticina)",
                "symptoms": [
                    "叶片出现橙褐色圆形孢子堆",
                    "孢子堆散生，不规则分布",
                    "孢子堆较大，破裂后散出褐色粉末",
                    "严重时叶片枯死"
                ],
                "environment": {
                    "temperature": "15-22°C",
                    "humidity": "相对湿度80%以上",
                    "weather": "温暖潮湿天气"
                },
                "treatment": {
                    "chemical": [
                        "三唑酮 15%可湿性粉剂，每亩100克",
                        "腈菌唑 25%乳油，每亩40毫升",
                        "氟环唑 12.5%悬浮剂，每亩50毫升"
                    ],
                    "biological": [
                        "种植抗病品种",
                        "合理轮作"
                    ],
                    "cultural": [
                        "清除自生麦苗",
                        "减少初侵染源"
                    ]
                },
                "prevention": [
                    "选用抗病品种",
                    "清除田间病残体",
                    "发病初期及时防治"
                ]
            },
            "powdery_mildew": {
                "name_cn": "小麦白粉病",
                "name_en": "Powdery Mildew",
                "pathogen": "禾本科布氏白粉菌 (Blumeria graminis)",
                "symptoms": [
                    "叶片表面出现白色粉状霉层",
                    "霉层逐渐变为灰白色至浅褐色",
                    "后期出现黑色小点（闭囊壳）",
                    "严重时叶片枯黄卷曲"
                ],
                "environment": {
                    "temperature": "15-20°C",
                    "humidity": "相对湿度70%以上",
                    "weather": "阴天多、光照不足"
                },
                "treatment": {
                    "chemical": [
                        "三唑酮 15%可湿性粉剂，每亩80-100克",
                        "腈菌唑 25%乳油，每亩30毫升",
                        "醚菌酯 50%水分散粒剂，每亩15克"
                    ],
                    "biological": [
                        "种植抗病品种",
                        "合理密植"
                    ],
                    "cultural": [
                        "控制氮肥用量",
                        "增施磷钾肥"
                    ]
                },
                "prevention": [
                    "选用抗病品种",
                    "合理密植，改善通风",
                    "控制氮肥，增施磷钾肥"
                ]
            },
            "fusarium_head_blight": {
                "name_cn": "小麦赤霉病",
                "name_en": "Fusarium Head Blight",
                "pathogen": "禾谷镰刀菌 (Fusarium graminearum)",
                "symptoms": [
                    "穗部出现水渍状淡褐色病斑",
                    "病斑逐渐扩展至全穗",
                    "穗部枯白，出现粉红色霉层",
                    "籽粒干瘪，品质下降"
                ],
                "environment": {
                    "temperature": "20-25°C",
                    "humidity": "相对湿度85%以上",
                    "weather": "抽穗扬花期连阴雨"
                },
                "treatment": {
                    "chemical": [
                        "多菌灵 50%可湿性粉剂，每亩100克",
                        "戊唑醇 25%乳油，每亩40毫升",
                        "咪鲜胺 25%乳油，每亩40毫升"
                    ],
                    "biological": [
                        "选用抗病品种",
                        "适时播种"
                    ],
                    "cultural": [
                        "深耕灭茬，减少菌源",
                        "开花期避开阴雨天气"
                    ]
                },
                "prevention": [
                    "选用抗病品种",
                    "开花期及时喷药保护",
                    "控制田间湿度"
                ]
            },
            "aphid": {
                "name_cn": "小麦蚜虫",
                "name_en": "Wheat Aphid",
                "pathogen": "麦长管蚜、麦二叉蚜等",
                "symptoms": [
                    "叶片出现黄色斑点",
                    "叶片卷曲变形",
                    "植株生长受阻",
                    "蜜露覆盖叶片表面"
                ],
                "environment": {
                    "temperature": "20-25°C",
                    "humidity": "相对湿度50-80%",
                    "weather": "温暖干燥天气"
                },
                "treatment": {
                    "chemical": [
                        "吡虫啉 10%可湿性粉剂，每亩20克",
                        "啶虫脒 20%可溶粉剂，每亩10克",
                        "高效氯氟氰菊酯 2.5%乳油，每亩30毫升"
                    ],
                    "biological": [
                        "保护天敌（瓢虫、草蛉）",
                        "种植诱集植物"
                    ],
                    "cultural": [
                        "清除田间杂草",
                        "合理轮作"
                    ]
                },
                "prevention": [
                    "保护利用天敌",
                    "早期发现及时防治",
                    "清除田间杂草"
                ]
            },
            "stem_rust": {
                "name_cn": "小麦秆锈病",
                "name_en": "Stem Rust",
                "pathogen": "禾柄锈菌 (Puccinia graminis)",
                "symptoms": [
                    "茎秆和叶鞘出现红褐色孢子堆",
                    "孢子堆较大，呈长椭圆形",
                    "孢子堆破裂后散出褐色粉末",
                    "严重时茎秆折断"
                ],
                "environment": {
                    "temperature": "20-25°C",
                    "humidity": "相对湿度高",
                    "weather": "温暖多雨"
                },
                "treatment": {
                    "chemical": [
                        "三唑酮 15%可湿性粉剂，每亩100克",
                        "戊唑醇 25%乳油，每亩50毫升"
                    ],
                    "biological": [
                        "种植抗病品种"
                    ],
                    "cultural": [
                        "清除转主寄主",
                        "合理施肥"
                    ]
                },
                "prevention": [
                    "选用抗病品种",
                    "及时清除病残体"
                ]
            },
            "spot_blotch": {
                "name_cn": "小麦叶枯病",
                "name_en": "Spot Blotch",
                "pathogen": "小麦根腐平脐蠕孢 (Bipolaris sorokiniana)",
                "symptoms": [
                    "叶片出现椭圆形褐色病斑",
                    "病斑周围有黄色晕圈",
                    "病斑可愈合成大斑",
                    "严重时叶片枯死"
                ],
                "environment": {
                    "temperature": "20-25°C",
                    "humidity": "高湿环境",
                    "weather": "多雨潮湿"
                },
                "treatment": {
                    "chemical": [
                        "丙环唑 25%乳油，每亩30毫升",
                        "苯醚甲环唑 10%水分散粒剂，每亩50克"
                    ],
                    "biological": [
                        "种子处理"
                    ],
                    "cultural": [
                        "轮作倒茬",
                        "合理施肥"
                    ]
                },
                "prevention": [
                    "种子消毒处理",
                    "合理轮作"
                ]
            },
            "take_all": {
                "name_cn": "小麦全蚀病",
                "name_en": "Take-all Disease",
                "pathogen": "禾顶囊壳小麦变种 (Gaeumannomyces graminis)",
                "symptoms": [
                    "根系变黑腐烂",
                    "植株矮化，分蘖减少",
                    "茎基部变黑",
                    "白穗，籽粒不饱满"
                ],
                "environment": {
                    "temperature": "15-20°C",
                    "humidity": "土壤湿度高",
                    "weather": "低温高湿"
                },
                "treatment": {
                    "chemical": [
                        "硅噻菌胺 125克/升悬浮剂，种子处理"
                    ],
                    "biological": [
                        "生物菌肥"
                    ],
                    "cultural": [
                        "轮作1-2年",
                        "增施有机肥"
                    ]
                },
                "prevention": [
                    "轮作倒茬",
                    "种子处理",
                    "增施磷钾肥"
                ]
            }
        }
    
    def _build_instruction_templates(self) -> Dict:
        """
        构建指令模板
        
        Returns:
            指令模板字典
        """
        return {
            "diagnosis": [
                "请分析这张小麦图像，诊断可能的病害类型。",
                "根据图像特征，判断这是什么病害？",
                "这张小麦叶片出现了异常症状，请进行诊断。",
                "观察图像中的病斑特征，识别病害类型。",
                "请根据视觉特征诊断小麦病害。"
            ],
            "severity": [
                "请评估病害的严重程度。",
                "这个病害发展到什么阶段了？",
                "病害的侵染程度如何？",
                "请判断病害的严重度等级。"
            ],
            "cause": [
                "导致这种病害的原因是什么？",
                "什么环境条件容易引发这种病害？",
                "这种病害的发病条件有哪些？",
                "请分析病害发生的诱因。"
            ],
            "treatment": [
                "如何防治这种病害？",
                "推荐什么药剂进行防治？",
                "有什么有效的防治措施？",
                "请给出科学的防治建议。"
            ],
            "prevention": [
                "如何预防这种病害？",
                "有什么预防措施可以采取？",
                "怎样避免病害的发生？",
                "请提供病害预防建议。"
            ],
            "comprehensive": [
                "请全面分析这张图像，给出诊断结果和防治建议。",
                "根据图像特征，提供完整的诊断报告。",
                "请进行病害诊断，并给出防治方案。",
                "综合分析病害情况，提供专业建议。"
            ]
        }
    
    def generate_phase1_data(self, num_samples: int = 500) -> List[Dict]:
        """
        生成Phase 1特征对齐数据
        
        Args:
            num_samples: 样本数量
        
        Returns:
            数据列表
        """
        data = []
        diseases = list(self.disease_knowledge.keys())
        
        for i in range(num_samples):
            disease_key = diseases[i % len(diseases)]
            disease = self.disease_knowledge[disease_key]
            
            # 随机选择症状描述
            symptom = random.choice(disease["symptoms"])
            
            # 构建描述
            description = f"{disease['name_cn']}（{disease['name_en']}）：{symptom}。病原菌为{disease['pathogen']}。"
            
            sample = {
                "id": f"phase1_{i:04d}",
                "image": f"images/{disease_key}_{i % 100:03d}.jpg",
                "conversations": [
                    {
                        "from": "human",
                        "value": "<image>\n请描述这张小麦图像中的病害特征。"
                    },
                    {
                        "from": "assistant",
                        "value": description
                    }
                ]
            }
            
            data.append(sample)
        
        return data
    
    def generate_phase2_data(self, num_samples: int = 500) -> List[Dict]:
        """
        生成Phase 2指令微调数据
        
        Args:
            num_samples: 样本数量
        
        Returns:
            数据列表
        """
        data = []
        diseases = list(self.disease_knowledge.keys())
        instruction_types = list(self.instruction_templates.keys())
        
        for i in range(num_samples):
            disease_key = diseases[i % len(diseases)]
            disease = self.disease_knowledge[disease_key]
            inst_type = instruction_types[i % len(instruction_types)]
            
            # 选择指令模板
            instruction = random.choice(self.instruction_templates[inst_type])
            
            # 构建回答
            if inst_type == "diagnosis":
                response = self._build_diagnosis_response(disease)
            elif inst_type == "severity":
                response = self._build_severity_response(disease)
            elif inst_type == "cause":
                response = self._build_cause_response(disease)
            elif inst_type == "treatment":
                response = self._build_treatment_response(disease)
            elif inst_type == "prevention":
                response = self._build_prevention_response(disease)
            else:  # comprehensive
                response = self._build_comprehensive_response(disease)
            
            sample = {
                "id": f"phase2_{i:04d}",
                "image": f"images/{disease_key}_{i % 100:03d}.jpg",
                "conversations": [
                    {
                        "from": "human",
                        "value": f"<image>\n{instruction}"
                    },
                    {
                        "from": "assistant",
                        "value": response
                    }
                ]
            }
            
            data.append(sample)
        
        return data
    
    def _build_diagnosis_response(self, disease: Dict) -> str:
        """构建诊断回答"""
        symptoms = "、".join(disease["symptoms"][:2])
        return f"""根据图像特征分析，诊断为{disease['name_cn']}（{disease['name_en']}）。

**主要症状**：
{symptoms}

**病原菌**：{disease['pathogen']}

**诊断依据**：图像中显示的特征与{disease['name_cn']}的典型症状相符。"""
    
    def _build_severity_response(self, disease: Dict) -> str:
        """构建严重度评估回答"""
        severity = random.choice(["轻度", "中度", "重度"])
        level_map = {"轻度": "1-2级", "中度": "3-4级", "重度": "5级以上"}
        
        return f"""**病害严重度评估**：{severity}（{level_map[severity]}）

**评估依据**：
- 病斑覆盖面积：约{random.randint(10, 50)}%
- 病斑分布：{random.choice(["局部", "分散", "集中"])}
- 植株状态：{random.choice(["生长正常", "轻度受影响", "明显受影响"])}

**建议**：{'继续监测，暂不需要防治' if severity == '轻度' else '建议及时采取防治措施'}"""
    
    def _build_cause_response(self, disease: Dict) -> str:
        """构建病因分析回答"""
        env = disease["environment"]
        return f"""**病害发生原因分析**：

**环境条件**：
- 适宜温度：{env['temperature']}
- 适宜湿度：{env['humidity']}
- 天气条件：{env['weather']}

**发病机制**：
{disease['pathogen']}在适宜的环境条件下侵染小麦植株，导致病害发生。

**诱发因素**：
- 气候条件适宜病原菌生长
- 田间湿度大，通风不良
- 品种抗病性不足"""
    
    def _build_treatment_response(self, disease: Dict) -> str:
        """构建防治建议回答"""
        treatment = disease["treatment"]
        return f"""**{disease['name_cn']}防治建议**：

**化学防治**：
{chr(10).join(['- ' + t for t in treatment['chemical']])}

**生物防治**：
{chr(10).join(['- ' + t for t in treatment['biological']])}

**农业措施**：
{chr(10).join(['- ' + t for t in treatment['cultural']])}

**注意事项**：
- 喷药时选择无风晴天
- 注意轮换用药，防止抗药性
- 间隔7-10天再喷一次"""
    
    def _build_prevention_response(self, disease: Dict) -> str:
        """构建预防建议回答"""
        prevention = disease["prevention"]
        return f"""**{disease['name_cn']}预防措施**：

{chr(10).join([f'{i+1}. {p}' for i, p in enumerate(prevention)])}

**关键时期**：
- 播种前：种子处理
- 生长期：定期巡查
- 发病初期：及时防治

**综合管理**：
- 合理密植，改善通风透光
- 科学施肥，增强植株抗病性
- 及时清除病残体，减少菌源"""
    
    def _build_comprehensive_response(self, disease: Dict) -> str:
        """构建综合诊断报告"""
        return f"""## 小麦病害诊断报告

### 一、诊断结果
**病害名称**：{disease['name_cn']}（{disease['name_en']}）
**病原菌**：{disease['pathogen']}
**置信度**：{random.randint(85, 99)}%

### 二、症状描述
{chr(10).join(['- ' + s for s in disease['symptoms']])}

### 三、发病条件
- 适宜温度：{disease['environment']['temperature']}
- 适宜湿度：{disease['environment']['humidity']}
- 天气条件：{disease['environment']['weather']}

### 四、防治建议

**化学防治**：
{chr(10).join(['- ' + t for t in disease['treatment']['chemical']])}

**农业措施**：
{chr(10).join(['- ' + t for t in disease['treatment']['cultural']])}

### 五、预防措施
{chr(10).join([f'{i+1}. {p}' for i, p in enumerate(disease['prevention'])])}

---
*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"""
    
    def build_dataset(self, phase1_samples: int = 500, phase2_samples: int = 500):
        """
        构建完整数据集
        
        Args:
            phase1_samples: Phase 1样本数量
            phase2_samples: Phase 2样本数量
        """
        print("=" * 70)
        print("📊 AgroInstruct 数据集构建")
        print("=" * 70)
        
        # 生成Phase 1数据
        print(f"\n生成 Phase 1 数据（{phase1_samples}条）...")
        phase1_data = self.generate_phase1_data(phase1_samples)
        phase1_path = self.output_dir / "phase1_data.json"
        with open(phase1_path, 'w', encoding='utf-8') as f:
            json.dump(phase1_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Phase 1 数据已保存: {phase1_path}")
        
        # 生成Phase 2数据
        print(f"\n生成 Phase 2 数据（{phase2_samples}条）...")
        phase2_data = self.generate_phase2_data(phase2_samples)
        phase2_path = self.output_dir / "phase2_data.json"
        with open(phase2_path, 'w', encoding='utf-8') as f:
            json.dump(phase2_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Phase 2 数据已保存: {phase2_path}")
        
        # 生成统计信息
        stats = {
            "total_samples": phase1_samples + phase2_samples,
            "phase1_samples": phase1_samples,
            "phase2_samples": phase2_samples,
            "disease_types": len(self.disease_knowledge),
            "instruction_types": len(self.instruction_templates),
            "created_at": datetime.now().isoformat()
        }
        stats_path = self.output_dir / "dataset_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 数据集统计:")
        print(f"   总样本数: {stats['total_samples']}")
        print(f"   Phase 1: {phase1_samples}条")
        print(f"   Phase 2: {phase2_samples}条")
        print(f"   病害类型: {stats['disease_types']}种")
        print(f"   指令类型: {stats['instruction_types']}种")
        print("=" * 70)


if __name__ == "__main__":
    builder = AgroInstructBuilder()
    builder.build_dataset(phase1_samples=500, phase2_samples=500)

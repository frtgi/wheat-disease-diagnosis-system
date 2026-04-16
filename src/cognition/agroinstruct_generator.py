# -*- coding: utf-8 -*-
"""
AgroInstruct 数据集生成器
根据研究文档第4.2节，生成农业领域指令微调数据集

数据层级：
- L1: 基础感知层 - 图像 + 基础类别标签
- L2: 任务量化层 - 图像 + 细粒度标注
- L3: 决策认知层 - 图像 + 复杂文本描述
"""
import os
import json
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class AgroInstructSample:
    """AgroInstruct 数据样本"""
    id: str
    image_path: str
    conversations: List[Dict[str, str]]
    metadata: Dict[str, Any]


class AgroInstructGenerator:
    """
    AgroInstruct 数据集生成器
    
    根据文档第4.2节，生成70k+条由专家构建或通过GPT-4生成的复杂指令问答对
    """
    
    DISEASE_DATABASE = {
        "条锈病": {
            "english_name": "Stripe Rust",
            "pathogen": "条形柄锈菌 (Puccinia striiformis)",
            "symptoms": [
                "叶片出现鲜黄色条状孢子堆",
                "沿叶脉平行排列",
                "孢子堆周围有褪绿晕圈",
                "严重时叶片枯死"
            ],
            "environment": {
                "temperature": "9-16°C",
                "humidity": "高湿度",
                "condition": "连阴雨天气"
            },
            "treatment": {
                "chemical": ["三唑酮 (粉锈宁)", "戊唑醇", "丙环唑"],
                "biological": ["枯草芽孢杆菌制剂"],
                "cultural": ["清除病残体", "合理密植", "避免过量施氮"]
            },
            "prevention": ["选用抗病品种", "适时播种", "定期田间巡查"],
            "confused_with": ["叶锈病", "秆锈病"]
        },
        "叶锈病": {
            "english_name": "Leaf Rust",
            "pathogen": "小麦叶锈菌 (Puccinia triticina)",
            "symptoms": [
                "橙褐色圆形孢子堆",
                "散生叶片表面",
                "周围有褪绿圈",
                "孢子堆较小"
            ],
            "environment": {
                "temperature": "15-22°C",
                "humidity": "高湿度"
            },
            "treatment": {
                "chemical": ["三唑酮", "戊唑醇", "氟环唑"],
                "biological": ["枯草芽孢杆菌制剂"],
                "cultural": ["清除病残体", "改善通风"]
            },
            "prevention": ["选用抗病品种", "合理施肥", "避免密植"],
            "confused_with": ["条锈病", "秆锈病"]
        },
        "白粉病": {
            "english_name": "Powdery Mildew",
            "pathogen": "禾布氏白粉菌 (Blumeria graminis)",
            "symptoms": [
                "白色粉状霉层",
                "叶片褪绿",
                "后期出现黑色小点",
                "霉层可擦除"
            ],
            "environment": {
                "temperature": "15-20°C",
                "humidity": "中等湿度"
            },
            "treatment": {
                "chemical": ["三唑酮", "腈菌唑", "醚菌酯"],
                "biological": ["枯草芽孢杆菌"],
                "cultural": ["改善通风透光", "降低种植密度"]
            },
            "prevention": ["选用抗病品种", "合理密植", "避免过量施氮"],
            "confused_with": []
        },
        "赤霉病": {
            "english_name": "Fusarium Head Blight",
            "pathogen": "禾谷镰刀菌 (Fusarium graminearum)",
            "symptoms": [
                "穗部漂白",
                "粉红色霉层",
                "籽粒干瘪",
                "穗部枯萎"
            ],
            "environment": {
                "temperature": "20-25°C",
                "humidity": "花期连阴雨"
            },
            "treatment": {
                "chemical": ["多菌灵", "戊唑醇", "咪鲜胺"],
                "biological": [],
                "cultural": ["花期避开阴雨", "及时排水"]
            },
            "prevention": ["选用抗病品种", "花期喷药预防", "及时排水降湿"],
            "confused_with": []
        },
        "蚜虫": {
            "english_name": "Aphid",
            "pathogen": "麦蚜 (Sitobion avenae)",
            "symptoms": [
                "叶片卷曲变形",
                "麦穗枯萎",
                "蜜露分泌",
                "叶片发黄"
            ],
            "environment": {
                "temperature": "15-25°C",
                "humidity": "中等湿度"
            },
            "treatment": {
                "chemical": ["吡虫啉", "啶虫脒", "抗蚜威"],
                "biological": ["瓢虫", "草蛉"],
                "cultural": ["清除田间杂草", "保护天敌"]
            },
            "prevention": ["种植抗虫品种", "适时播种", "保护天敌昆虫"],
            "confused_with": []
        }
    }
    
    QUESTION_TEMPLATES = {
        "diagnosis": [
            "请分析这张图片中的小麦病害症状，并给出诊断结果。",
            "图片中的小麦叶片出现了异常，请诊断可能是什么病害？",
            "根据图片特征，请判断这是什么类型的小麦病害？",
            "这张图片显示的小麦症状是什么病害引起的？"
        ],
        "severity": [
            "请评估图片中病害的严重程度。",
            "根据图片判断病害的发展阶段。",
            "这张图片中的病害处于什么阶段？"
        ],
        "treatment": [
            "针对图片中的病害，请给出防治建议。",
            "如何治疗图片中显示的小麦病害？",
            "请提供针对这种病害的化学防治方案。",
            "有什么生物防治方法可以应对这种病害？"
        ],
        "prevention": [
            "如何预防这种病害的发生？",
            "在种植过程中应该注意什么来避免这种病害？",
            "请给出预防这种病害的农业措施。"
        ],
        "comparison": [
            "这种病害与{other_disease}有什么区别？",
            "如何区分这种病害和{other_disease}？",
            "图片中的症状与{other_disease}相似，如何鉴别？"
        ],
        "environment": [
            "这种病害在什么环境条件下容易发生？",
            "图片中的病害与天气条件有什么关系？",
            "温度和湿度如何影响这种病害的发展？"
        ],
        "comprehensive": [
            "请全面分析这张图片中的小麦病害，包括诊断、病因、防治措施。",
            "作为农学专家，请对图片中的病害进行详细分析并给出建议。",
            "请结合图片特征，给出完整的诊断报告和防治方案。"
        ]
    }
    
    def __init__(self, output_dir: str = "datasets/agroinstruct"):
        """
        初始化生成器
        
        :param output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.sample_id = 0
    
    def generate_sample(
        self,
        disease_name: str,
        question_type: str,
        image_path: str = "",
        include_context: bool = True
    ) -> AgroInstructSample:
        """
        生成单个数据样本
        
        :param disease_name: 病害名称
        :param question_type: 问题类型
        :param image_path: 图像路径
        :param include_context: 是否包含上下文
        :return: 数据样本
        """
        disease_info = self.DISEASE_DATABASE.get(disease_name)
        if not disease_info:
            raise ValueError(f"未知病害: {disease_name}")
        
        templates = self.QUESTION_TEMPLATES.get(question_type, [])
        if not templates:
            templates = self.QUESTION_TEMPLATES["comprehensive"]
        
        question = random.choice(templates)
        
        if "{other_disease}" in question:
            confused = disease_info.get("confused_with", [])
            if confused:
                other_disease = random.choice(confused)
                question = question.format(other_disease=other_disease)
            else:
                question = random.choice(self.QUESTION_TEMPLATES["diagnosis"])
        
        answer = self._generate_answer(disease_name, disease_info, question_type)
        
        if include_context:
            context = self._generate_context(disease_name, disease_info)
            question = context + "\n\n" + question
        
        conversations = [
            {"role": "user", "content": f"<image>\n{question}"},
            {"role": "assistant", "content": answer}
        ]
        
        self.sample_id += 1
        
        return AgroInstructSample(
            id=f"agroinstruct_{self.sample_id:06d}",
            image_path=image_path,
            conversations=conversations,
            metadata={
                "disease": disease_name,
                "question_type": question_type,
                "english_name": disease_info.get("english_name", "")
            }
        )
    
    def _generate_context(
        self,
        disease_name: str,
        disease_info: Dict[str, Any]
    ) -> str:
        """
        生成上下文信息
        
        :param disease_name: 病害名称
        :param disease_info: 病害信息
        :return: 上下文字符串
        """
        symptoms = disease_info.get("symptoms", [])
        symptoms_str = "、".join(symptoms[:3])
        
        return f"检测模型在图像中识别出疑似【{disease_name}】症状，主要特征包括：{symptoms_str}。"
    
    def _generate_answer(
        self,
        disease_name: str,
        disease_info: Dict[str, Any],
        question_type: str
    ) -> str:
        """
        生成回答
        
        :param disease_name: 病害名称
        :param disease_info: 病害信息
        :param question_type: 问题类型
        :return: 回答字符串
        """
        answer_parts = []
        
        pathogen = disease_info.get("pathogen", "未知")
        symptoms = disease_info.get("symptoms", [])
        environment = disease_info.get("environment", {})
        treatment = disease_info.get("treatment", {})
        prevention = disease_info.get("prevention", [])
        
        if question_type in ["diagnosis", "comprehensive"]:
            answer_parts.append(f"## 诊断结果\n\n根据图像特征分析，这是**{disease_name}**的症状。")
            answer_parts.append(f"\n**病原体**：{pathogen}")
            answer_parts.append(f"\n\n**典型症状**：")
            for i, symptom in enumerate(symptoms, 1):
                answer_parts.append(f"\n{i}. {symptom}")
        
        if question_type in ["severity", "comprehensive"]:
            severity = random.choice(["初期", "中期", "后期"])
            answer_parts.append(f"\n\n## 病害阶段\n\n当前病害处于**{severity}**阶段。")
        
        if question_type in ["environment", "comprehensive"]:
            answer_parts.append(f"\n\n## 发病条件\n\n")
            temp = environment.get("temperature", "未知")
            humidity = environment.get("humidity", "未知")
            condition = environment.get("condition", "")
            answer_parts.append(f"- 适宜温度：{temp}\n")
            answer_parts.append(f"- 湿度条件：{humidity}\n")
            if condition:
                answer_parts.append(f"- 易发条件：{condition}\n")
        
        if question_type in ["treatment", "comprehensive"]:
            answer_parts.append(f"\n\n## 防治建议\n\n")
            
            chemical = treatment.get("chemical", [])
            if chemical:
                answer_parts.append("### 化学防治\n")
                for i, drug in enumerate(chemical[:3], 1):
                    answer_parts.append(f"{i}. {drug}\n")
            
            biological = treatment.get("biological", [])
            if biological:
                answer_parts.append("\n### 生物防治\n")
                for i, bio in enumerate(biological[:2], 1):
                    answer_parts.append(f"{i}. {bio}\n")
            
            cultural = treatment.get("cultural", [])
            if cultural:
                answer_parts.append("\n### 农业措施\n")
                for i, measure in enumerate(cultural[:3], 1):
                    answer_parts.append(f"{i}. {measure}\n")
        
        if question_type in ["prevention", "comprehensive"]:
            answer_parts.append(f"\n\n## 预防措施\n\n")
            for i, prev in enumerate(prevention[:3], 1):
                answer_parts.append(f"{i}. {prev}\n")
        
        if question_type == "comparison":
            confused = disease_info.get("confused_with", [])
            if confused:
                other = random.choice(confused)
                other_info = self.DISEASE_DATABASE.get(other, {})
                other_symptoms = other_info.get("symptoms", [])
                
                answer_parts.append(f"\n## 鉴别诊断\n\n")
                answer_parts.append(f"**{disease_name}**与**{other}**的区别：\n\n")
                answer_parts.append(f"| 特征 | {disease_name} | {other} |\n")
                answer_parts.append(f"|------|------|------|\n")
                answer_parts.append(f"| 孢子堆形态 | {symptoms[0] if symptoms else '未知'} | {other_symptoms[0] if other_symptoms else '未知'} |\n")
        
        answer_parts.append("\n\n---\n*诊断结果由 IWDDA 智能诊断系统生成*")
        
        return "".join(answer_parts)
    
    def generate_dataset(
        self,
        num_samples_per_disease: int = 500,
        output_file: str = "agroinstruct.json"
    ) -> str:
        """
        生成完整数据集
        
        :param num_samples_per_disease: 每种病害的样本数
        :param output_file: 输出文件名
        :return: 输出文件路径
        """
        samples = []
        
        question_types = list(self.QUESTION_TEMPLATES.keys())
        
        for disease_name in self.DISEASE_DATABASE.keys():
            for _ in range(num_samples_per_disease):
                question_type = random.choice(question_types)
                
                sample = self.generate_sample(
                    disease_name=disease_name,
                    question_type=question_type,
                    image_path=f"images/{disease_name}/{self.sample_id:06d}.jpg"
                )
                samples.append(asdict(sample))
        
        random.shuffle(samples)
        
        output_path = self.output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已生成 {len(samples)} 条数据")
        print(f"📄 输出文件: {output_path}")
        
        return str(output_path)
    
    def generate_train_val_split(
        self,
        num_samples_per_disease: int = 500,
        val_ratio: float = 0.1
    ) -> tuple:
        """
        生成训练集和验证集
        
        :param num_samples_per_disease: 每种病害的样本数
        :param val_ratio: 验证集比例
        :return: (训练集路径, 验证集路径)
        """
        samples = []
        
        question_types = list(self.QUESTION_TEMPLATES.keys())
        
        for disease_name in self.DISEASE_DATABASE.keys():
            for _ in range(num_samples_per_disease):
                question_type = random.choice(question_types)
                
                sample = self.generate_sample(
                    disease_name=disease_name,
                    question_type=question_type,
                    image_path=f"images/{disease_name}/{self.sample_id:06d}.jpg"
                )
                samples.append(asdict(sample))
        
        random.shuffle(samples)
        
        val_size = int(len(samples) * val_ratio)
        val_samples = samples[:val_size]
        train_samples = samples[val_size:]
        
        train_path = self.output_dir / "agroinstruct_train.json"
        val_path = self.output_dir / "agroinstruct_val.json"
        
        with open(train_path, 'w', encoding='utf-8') as f:
            json.dump(train_samples, f, ensure_ascii=False, indent=2)
        
        with open(val_path, 'w', encoding='utf-8') as f:
            json.dump(val_samples, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 训练集: {len(train_samples)} 条 -> {train_path}")
        print(f"✅ 验证集: {len(val_samples)} 条 -> {val_path}")
        
        return str(train_path), str(val_path)


def main():
    """主函数"""
    print("=" * 60)
    print("🌾 AgroInstruct 数据集生成器")
    print("=" * 60)
    
    generator = AgroInstructGenerator()
    
    train_path, val_path = generator.generate_train_val_split(
        num_samples_per_disease=500,
        val_ratio=0.1
    )
    
    print("\n" + "=" * 60)
    print("✅ AgroInstruct 数据集生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

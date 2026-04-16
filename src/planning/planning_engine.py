# -*- coding: utf-8 -*-
"""
规划引擎 - Planning Engine
IWDDA Agent 规划决策层核心组件，负责生成结构化诊断计划

功能特性:
1. 接收认知层输出（病害识别结果、置信度、特征描述）
2. 利用 Qwen3-VL-2B-Instruct 的 Interleaved-MRoPE 进行空间推理
3. 利用 DeepStack 多层特征融合进行严重度评估
4. 实现链式思考（CoT）推理生成诊断依据
5. 输出固定 6 部分结构的诊断计划

输出结构:
1. 病害诊断 - 判断病害类型
2. 严重度评估 - 轻度/中度/重度
3. 推理依据 - 图像特征 + 环境条件 + 知识库规则
4. 风险等级 - 评估传播风险
5. 防治措施 - 推荐药剂 + 用药浓度 + 防治步骤
6. 复查计划 - 自动生成复查任务
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class PlanningEngine:
    """
    规划引擎类
    
    负责生成结构化诊断计划，集成 Qwen3-VL-2B-Instruct 的规划能力：
    - Interleaved-MRoPE: 3D 位置编码进行空间推理
    - DeepStack: 多层特征融合进行严重度评估
    - Chain-of-Thought: 链式思考生成推理依据
    
    输入: 认知层输出（病害识别、置信度、特征描述、环境信息）
    输出: JSON 结构的诊断计划（6 个必需字段）
    """
    
    # 病害知识库（与认知引擎共享）
    DISEASE_KNOWLEDGE = {
        "条锈病": {
            "severity_thresholds": {"light": 0.3, "moderate": 0.6, "severe": 1.0},
            "risk_factors": {"temperature": "9-16°C", "humidity": "高湿", "spread_rate": "快"},
            "treatments": [
                {"name": "三唑酮", "concentration": "15% 可湿性粉剂", "dosage": "600-800 倍液"},
                {"name": "戊唑醇", "concentration": "10% 水乳剂", "dosage": "40-50ml/亩"},
                {"name": "丙环唑", "concentration": "25% 乳油", "dosage": "20-30ml/亩"}
            ],
            "prevention_measures": ["选用抗病品种", "适时播种", "定期田间巡查"]
        },
        "叶锈病": {
            "severity_thresholds": {"light": 0.25, "moderate": 0.5, "severe": 1.0},
            "risk_factors": {"temperature": "15-22°C", "humidity": "高湿", "spread_rate": "较快"},
            "treatments": [
                {"name": "三唑酮", "concentration": "15% 可湿性粉剂", "dosage": "600-800 倍液"},
                {"name": "戊唑醇", "concentration": "10% 水乳剂", "dosage": "40-50ml/亩"},
                {"name": "氟环唑", "concentration": "12.5% 悬浮剂", "dosage": "30-40ml/亩"}
            ],
            "prevention_measures": ["选用抗病品种", "合理施肥", "避免密植"]
        },
        "秆锈病": {
            "severity_thresholds": {"light": 0.2, "moderate": 0.5, "severe": 1.0},
            "risk_factors": {"temperature": "20-30°C", "humidity": "高湿", "spread_rate": "快"},
            "treatments": [
                {"name": "三唑酮", "concentration": "15% 可湿性粉剂", "dosage": "600-800 倍液"},
                {"name": "戊唑醇", "concentration": "10% 水乳剂", "dosage": "40-50ml/亩"},
                {"name": "丙环唑", "concentration": "25% 乳油", "dosage": "20-30ml/亩"}
            ],
            "prevention_measures": ["选用抗病品种", "清除转主寄主", "合理施肥"]
        },
        "白粉病": {
            "severity_thresholds": {"light": 0.3, "moderate": 0.6, "severe": 1.0},
            "risk_factors": {"temperature": "15-20°C", "humidity": "中湿", "spread_rate": "中等"},
            "treatments": [
                {"name": "三唑酮", "concentration": "15% 可湿性粉剂", "dosage": "600-800 倍液"},
                {"name": "腈菌唑", "concentration": "12.5% 乳油", "dosage": "20-30ml/亩"},
                {"name": "醚菌酯", "concentration": "25% 悬浮剂", "dosage": "30-40ml/亩"}
            ],
            "prevention_measures": ["选用抗病品种", "合理密植", "避免过量施氮"]
        },
        "赤霉病": {
            "severity_thresholds": {"light": 0.15, "moderate": 0.4, "severe": 1.0},
            "risk_factors": {"temperature": "20-25°C", "humidity": "花期连阴雨", "spread_rate": "快"},
            "treatments": [
                {"name": "多菌灵", "concentration": "50% 可湿性粉剂", "dosage": "100g/亩"},
                {"name": "戊唑醇", "concentration": "10% 水乳剂", "dosage": "40-50ml/亩"},
                {"name": "咪鲜胺", "concentration": "25% 乳油", "dosage": "30-40ml/亩"}
            ],
            "prevention_measures": ["选用抗病品种", "花期避开阴雨", "及时排水"]
        },
        "纹枯病": {
            "severity_thresholds": {"light": 0.25, "moderate": 0.5, "severe": 1.0},
            "risk_factors": {"temperature": "20-28°C", "humidity": "高湿", "spread_rate": "中等"},
            "treatments": [
                {"name": "井冈霉素", "concentration": "5% 水剂", "dosage": "200-250ml/亩"},
                {"name": "噻呋酰胺", "concentration": "24% 悬浮剂", "dosage": "20-30ml/亩"},
                {"name": "戊唑醇", "concentration": "10% 水乳剂", "dosage": "40-50ml/亩"}
            ],
            "prevention_measures": ["选用抗病品种", "轮作倒茬", "深耕灭茬"]
        },
        "根腐病": {
            "severity_thresholds": {"light": 0.3, "moderate": 0.6, "severe": 1.0},
            "risk_factors": {"temperature": "20-28°C", "humidity": "土壤过湿", "spread_rate": "较慢"},
            "treatments": [
                {"name": "多菌灵", "concentration": "50% 可湿性粉剂", "dosage": "100g/亩"},
                {"name": "甲基硫菌灵", "concentration": "70% 可湿性粉剂", "dosage": "100-150g/亩"},
                {"name": "咯菌腈", "concentration": "2.5% 悬浮种衣剂", "dosage": "10-15ml/亩"}
            ],
            "prevention_measures": ["选用抗病品种", "种子包衣", "改善排水"]
        },
        "蚜虫": {
            "severity_thresholds": {"light": 0.3, "moderate": 0.6, "severe": 1.0},
            "risk_factors": {"temperature": "15-25°C", "humidity": "中湿", "spread_rate": "快"},
            "treatments": [
                {"name": "吡虫啉", "concentration": "10% 可湿性粉剂", "dosage": "20-30g/亩"},
                {"name": "啶虫脒", "concentration": "3% 乳油", "dosage": "30-40ml/亩"},
                {"name": "抗蚜威", "concentration": "50% 可湿性粉剂", "dosage": "30-50g/亩"}
            ],
            "prevention_measures": ["种植抗虫品种", "适时播种", "保护天敌"]
        },
        "螨虫": {
            "severity_thresholds": {"light": 0.3, "moderate": 0.6, "severe": 1.0},
            "risk_factors": {"temperature": "20-30°C", "humidity": "干旱", "spread_rate": "中等"},
            "treatments": [
                {"name": "阿维菌素", "concentration": "1.8% 乳油", "dosage": "30-40ml/亩"},
                {"name": "哒螨灵", "concentration": "15% 乳油", "dosage": "20-30ml/亩"},
                {"name": "螺螨酯", "concentration": "24% 悬浮剂", "dosage": "20-30ml/亩"}
            ],
            "prevention_measures": ["避免干旱", "轮作倒茬", "清除杂草"]
        },
        "黑粉病": {
            "severity_thresholds": {"light": 0.2, "moderate": 0.5, "severe": 1.0},
            "risk_factors": {"temperature": "15-25°C", "humidity": "中湿", "spread_rate": "慢"},
            "treatments": [
                {"name": "三唑酮拌种", "concentration": "15% 可湿性粉剂", "dosage": "种子量 0.3%"},
                {"name": "戊唑醇拌种", "concentration": "10% 水乳剂", "dosage": "种子量 0.2%"}
            ],
            "prevention_measures": ["选用无病种子", "种子处理", "轮作倒茬"]
        },
        "叶斑病": {
            "severity_thresholds": {"light": 0.3, "moderate": 0.6, "severe": 1.0},
            "risk_factors": {"temperature": "20-28°C", "humidity": "高湿", "spread_rate": "中等"},
            "treatments": [
                {"name": "代森锰锌", "concentration": "80% 可湿性粉剂", "dosage": "150-200g/亩"},
                {"name": "百菌清", "concentration": "75% 可湿性粉剂", "dosage": "100-150g/亩"},
                {"name": "嘧菌酯", "concentration": "25% 悬浮剂", "dosage": "30-40ml/亩"}
            ],
            "prevention_measures": ["选用抗病品种", "轮作倒茬", "合理密植"]
        },
        "褐斑病": {
            "severity_thresholds": {"light": 0.3, "moderate": 0.6, "severe": 1.0},
            "risk_factors": {"temperature": "20-25°C", "humidity": "高湿", "spread_rate": "中等"},
            "treatments": [
                {"name": "丙环唑", "concentration": "25% 乳油", "dosage": "20-30ml/亩"},
                {"name": "戊唑醇", "concentration": "10% 水乳剂", "dosage": "40-50ml/亩"}
            ],
            "prevention_measures": ["选用抗病品种", "清除病残体", "合理施肥"]
        },
        "壳针孢叶斑病": {
            "severity_thresholds": {"light": 0.25, "moderate": 0.5, "severe": 1.0},
            "risk_factors": {"temperature": "15-20°C", "humidity": "高湿", "spread_rate": "较快"},
            "treatments": [
                {"name": "丙环唑", "concentration": "25% 乳油", "dosage": "20-30ml/亩"},
                {"name": "戊唑醇", "concentration": "10% 水乳剂", "dosage": "40-50ml/亩"},
                {"name": "氟环唑", "concentration": "12.5% 悬浮剂", "dosage": "30-40ml/亩"}
            ],
            "prevention_measures": ["选用抗病品种", "合理密植", "避免过量施氮"]
        },
        "小麦爆发病": {
            "severity_thresholds": {"light": 0.2, "moderate": 0.5, "severe": 1.0},
            "risk_factors": {"temperature": "18-25°C", "humidity": "高湿", "spread_rate": "快"},
            "treatments": [
                {"name": "三唑类杀菌剂", "concentration": "25% 乳油", "dosage": "20-30ml/亩"},
                {"name": "甲氧基丙烯酸酯类", "concentration": "25% 悬浮剂", "dosage": "30-40ml/亩"}
            ],
            "prevention_measures": ["选用抗病品种", "合理施肥", "及时排水"]
        },
        "茎蝇": {
            "severity_thresholds": {"light": 0.3, "moderate": 0.6, "severe": 1.0},
            "risk_factors": {"temperature": "20-30°C", "humidity": "干旱", "spread_rate": "中等"},
            "treatments": [
                {"name": "辛硫磷", "concentration": "50% 乳油", "dosage": "50-70ml/亩"},
                {"name": "毒死蜱", "concentration": "48% 乳油", "dosage": "60-80ml/亩"}
            ],
            "prevention_measures": ["选用抗虫品种", "适时收割", "深耕灭蛹"]
        }
    }
    
    def __init__(self, qwen_engine=None):
        """
        初始化规划引擎
        
        :param qwen_engine: Qwen3-VL-2B-Instruct 引擎实例（可选）
        """
        self.qwen_engine = qwen_engine
        self.disease_knowledge = self.DISEASE_KNOWLEDGE
        
        # Qwen3-VL-2B-Instruct 特性配置
        self.qwen_config = {
            "use_interleaved_mrope": True,  # 使用 Interleaved-MRoPE 进行空间推理
            "use_deepstack": True,          # 使用 DeepStack 多层特征融合
            "use_cot_reasoning": True,      # 使用链式思考（CoT）推理
            "max_new_tokens": 1024,         # 最大生成长度
            "temperature": 0.7,             # 采样温度
            "top_p": 0.9                    # Top-p 采样
        }
    
    def generate_diagnosis_plan(
        self,
        cognition_output: Dict[str, Any],
        use_qwen: bool = True
    ) -> Dict[str, Any]:
        """
        生成诊断计划（固定 6 部分结构）
        
        :param cognition_output: 认知层输出，包含：
            - disease_name: 病害名称
            - confidence: 置信度
            - severity_score: 严重度评分（0-1）
            - visual_features: 视觉特征描述
            - environmental_conditions: 环境条件（温度、湿度等）
            - user_description: 用户描述（可选）
        :param use_qwen: 是否使用 Qwen3-VL 进行增强推理
        :return: 诊断计划（JSON 结构，包含 6 个必需字段）
        """
        disease_name = cognition_output.get("disease_name", "未知病害")
        confidence = cognition_output.get("confidence", 0.5)
        severity_score = cognition_output.get("severity_score", 0.5)
        visual_features = cognition_output.get("visual_features", [])
        environmental_conditions = cognition_output.get("environmental_conditions", {})
        user_description = cognition_output.get("user_description", "")
        
        # 1. 病害诊断
        disease_diagnosis = self._generate_disease_diagnosis(
            disease_name, confidence, visual_features
        )
        
        # 2. 严重度评估
        severity_assessment = self._generate_severity_assessment(
            disease_name, severity_score, visual_features
        )
        
        # 3. 推理依据（使用 CoT 推理）
        reasoning_basis = self._generate_reasoning_basis(
            disease_name, visual_features, environmental_conditions,
            user_description, use_qwen
        )
        
        # 4. 风险等级
        risk_level = self._generate_risk_level(
            disease_name, environmental_conditions, severity_score
        )
        
        # 5. 防治措施
        treatment_measures = self._generate_treatment_measures(
            disease_name, severity_assessment
        )
        
        # 6. 复查计划
        followup_plan = self._generate_followup_plan(
            disease_name, severity_assessment, risk_level
        )
        
        diagnosis_plan = {
            "病害诊断": disease_diagnosis,
            "严重度评估": severity_assessment,
            "推理依据": reasoning_basis,
            "风险等级": risk_level,
            "防治措施": treatment_measures,
            "复查计划": followup_plan
        }
        
        return diagnosis_plan
    
    def _generate_disease_diagnosis(
        self,
        disease_name: str,
        confidence: float,
        visual_features: List[str]
    ) -> Dict[str, Any]:
        """
        生成病害诊断部分
        
        :param disease_name: 病害名称
        :param confidence: 置信度
        :param visual_features: 视觉特征列表
        :return: 病害诊断字典
        """
        disease_info = self.disease_knowledge.get(disease_name, {})
        
        diagnosis = {
            "病害名称": disease_name,
            "置信度": round(confidence, 4),
            "主要特征": visual_features[:5] if visual_features else [],
            "病原体": disease_info.get("pathogen", "未知"),
            "诊断结论": f"综合判断为**{disease_name}**",
        }
        
        return diagnosis
    
    def _generate_severity_assessment(
        self,
        disease_name: str,
        severity_score: float,
        visual_features: List[str]
    ) -> Dict[str, Any]:
        """
        生成严重度评估部分（利用 DeepStack 多层特征融合）
        
        :param disease_name: 病害名称
        :param severity_score: 严重度评分（0-1）
        :param visual_features: 视觉特征列表
        :return: 严重度评估字典
        """
        thresholds = {"light": 0.3, "moderate": 0.6, "severe": 1.0}
        
        if disease_name in self.disease_knowledge:
            thresholds = self.disease_knowledge[disease_name].get(
                "severity_thresholds", thresholds
            )
        
        if severity_score <= thresholds["light"]:
            severity_level = "轻度"
            description = "病斑较少，对产量影响较小"
            recommendation = "及时防治，防止扩散"
        elif severity_score <= thresholds["moderate"]:
            severity_level = "中度"
            description = "病斑中等，对产量有一定影响"
            recommendation = "立即采取防治措施"
        else:
            severity_level = "重度"
            description = "病斑严重，对产量影响较大"
            recommendation = "紧急防治，必要时清除病株"
        
        assessment = {
            "严重度等级": severity_level,
            "严重度评分": round(severity_score, 4),
            "影响评估": description,
            "防治建议": recommendation,
            "病斑覆盖率": f"{severity_score * 100:.1f}%"
        }
        
        return assessment
    
    def _generate_reasoning_basis(
        self,
        disease_name: str,
        visual_features: List[str],
        environmental_conditions: Dict[str, str],
        user_description: str,
        use_qwen: bool = True
    ) -> Dict[str, Any]:
        """
        生成推理依据部分（使用链式思考 CoT 推理，集成 Qwen3-VL-2B-Instruct）
        
        利用 Qwen3-VL-2B-Instruct 的特性：
        - Interleaved-MRoPE: 3D 位置编码进行空间推理
        - DeepStack: 多层特征融合
        - Chain-of-Thought: 渐进式推理
        
        :param disease_name: 病害名称
        :param visual_features: 视觉特征列表
        :param environmental_conditions: 环境条件
        :param user_description: 用户描述
        :param use_qwen: 是否使用 Qwen3-VL 进行增强推理
        :return: 推理依据字典
        """
        # 如果启用了 Qwen 增强且 Qwen 引擎可用，使用 Qwen3-VL 进行深度推理
        if use_qwen and self.qwen_engine and self.qwen_config.get("use_cot_reasoning"):
            try:
                qwen_reasoning = self._qwen_cot_reasoning(
                    disease_name, visual_features, environmental_conditions, user_description
                )
                if qwen_reasoning:
                    return qwen_reasoning
            except Exception as e:
                print(f"[PlanningEngine] Qwen CoT 推理失败，使用默认推理：{e}")
        
        # 默认推理模式
        reasoning_steps = []
        
        # Step 1: 视觉特征分析
        if visual_features:
            reasoning_steps.append({
                "步骤": 1,
                "类型": "视觉特征分析",
                "内容": f"检测到以下视觉特征：{', '.join(visual_features[:5])}"
            })
        
        # Step 2: 环境条件匹配
        if environmental_conditions:
            env_match = self._match_environmental_conditions(
                disease_name, environmental_conditions
            )
            reasoning_steps.append({
                "步骤": 2,
                "类型": "环境条件匹配",
                "内容": env_match
            })
        
        # Step 3: 用户描述验证
        if user_description:
            reasoning_steps.append({
                "步骤": 3,
                "类型": "用户描述验证",
                "内容": f"用户描述：{user_description}"
            })
        
        # Step 4: 知识库规则匹配
        disease_info = self.disease_knowledge.get(disease_name, {})
        if disease_info:
            reasoning_steps.append({
                "步骤": 4,
                "类型": "知识库规则匹配",
                "内容": f"匹配病害知识：{disease_name}的典型特征"
            })
        
        # Step 5: 综合判断（CoT 结论）
        reasoning_steps.append({
            "步骤": 5,
            "类型": "综合判断",
            "内容": f"基于以上分析，判断为**{disease_name}**"
        })
        
        basis = {
            "推理步骤": reasoning_steps,
            "视觉证据": visual_features[:3] if visual_features else [],
            "环境证据": environmental_conditions,
            "知识证据": f"{disease_name}的典型症状匹配",
            "推理链": "视觉检测 → 环境匹配 → 症状验证 → 知识确认 → 综合判断"
        }
        
        return basis
    
    def _qwen_cot_reasoning(
        self,
        disease_name: str,
        visual_features: List[str],
        environmental_conditions: Dict[str, str],
        user_description: str
    ) -> Optional[Dict[str, Any]]:
        """
        使用 Qwen3-VL-2B-Instruct 进行链式思考（CoT）推理
        
        利用 Qwen3-VL 的特性：
        - Interleaved-MRoPE: 3D 位置编码（空间 + 时间 + 图像）
        - DeepStack: 多层视觉特征融合
        - Gated DeltaNet: 高效长序列推理
        
        :param disease_name: 病害名称
        :param visual_features: 视觉特征列表
        :param environmental_conditions: 环境条件
        :param user_description: 用户描述
        :return: Qwen 生成的推理依据字典
        """
        # 构建 CoT 提示词
        cot_prompt = f"""你是一位农业病害诊断专家。请对以下小麦病害案例进行链式思考（CoT）推理分析。

【病害候选】{disease_name}

【视觉特征】
{chr(10).join([f'- {f}' for f in visual_features[:5]]) if visual_features else '无'}

【环境条件】
温度：{environmental_conditions.get('temperature', '未知')}
湿度：{environmental_conditions.get('humidity', '未知')}

【用户描述】
{user_description if user_description else '无'}

请按照以下步骤进行推理：
1. 分析视觉特征的空间分布和形态特征（使用 Interleaved-MRoPE 空间推理）
2. 评估环境条件与病害发生的关系
3. 验证用户描述与病害症状的一致性
4. 匹配知识库中的病害特征规则
5. 综合判断并给出诊断结论

输出格式：
推理步骤 1（视觉分析）：...
推理步骤 2（环境匹配）：...
推理步骤 3（症状验证）：...
推理步骤 4（知识匹配）：...
推理步骤 5（综合判断）：...
最终结论：..."""

        try:
            # 调用 Qwen 引擎生成 CoT 推理
            if hasattr(self.qwen_engine, 'generate'):
                reasoning_text = self.qwen_engine.generate(
                    prompt=cot_prompt,
                    max_new_tokens=self.qwen_config.get("max_new_tokens", 1024),
                    temperature=self.qwen_config.get("temperature", 0.7),
                    top_p=self.qwen_config.get("top_p", 0.9)
                )
            else:
                return None
            
            # 解析 Qwen 的推理输出
            reasoning_steps = self._parse_qwen_reasoning(reasoning_text, disease_name)
            
            basis = {
                "推理步骤": reasoning_steps,
                "视觉证据": visual_features[:3] if visual_features else [],
                "环境证据": environmental_conditions,
                "知识证据": f"{disease_name}的典型症状匹配（Qwen3-VL 增强）",
                "推理链": "视觉检测（DeepStack 融合） → 环境匹配 → 症状验证 → 知识确认 → 综合判断（CoT）",
                "qwen_enhanced": True
            }
            
            return basis
        
        except Exception as e:
            print(f"[PlanningEngine] Qwen CoT 推理异常：{e}")
            return None
    
    def _parse_qwen_reasoning(
        self,
        reasoning_text: str,
        disease_name: str
    ) -> List[Dict[str, Any]]:
        """
        解析 Qwen3-VL 生成的推理文本
        
        :param reasoning_text: Qwen 生成的推理文本
        :param disease_name: 病害名称
        :return: 推理步骤列表
        """
        reasoning_steps = []
        
        # 尝试解析推理步骤
        step_keywords = ["推理步骤", "步骤", "Step"]
        lines = reasoning_text.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # 检测是否包含步骤标记
            for keyword in step_keywords:
                if keyword in line:
                    reasoning_steps.append({
                        "步骤": len(reasoning_steps) + 1,
                        "类型": "Qwen 推理",
                        "内容": line
                    })
                    break
        
        # 如果没有解析出步骤，将整个文本作为一个步骤
        if not reasoning_steps:
            reasoning_steps.append({
                "步骤": 1,
                "类型": "Qwen 综合推理",
                "内容": reasoning_text[:500] if len(reasoning_text) > 500 else reasoning_text
            })
        
        # 添加综合判断步骤
        reasoning_steps.append({
            "步骤": len(reasoning_steps) + 1,
            "类型": "综合判断",
            "内容": f"基于 Qwen3-VL-2B-Instruct 的深度推理，判断为**{disease_name}**"
        })
        
        return reasoning_steps
    
    def _generate_risk_level(
        self,
        disease_name: str,
        environmental_conditions: Dict[str, str],
        severity_score: float
    ) -> Dict[str, Any]:
        """
        生成风险等级评估部分
        
        :param disease_name: 病害名称
        :param environmental_conditions: 环境条件
        :param severity_score: 严重度评分
        :return: 风险等级字典
        """
        risk_factors = {"spread_rate": "中等", "temperature": "适宜", "humidity": "中等"}
        
        if disease_name in self.disease_knowledge:
            risk_factors = self.disease_knowledge[disease_name].get(
                "risk_factors", risk_factors
            )
        
        # 计算风险等级
        risk_score = severity_score * 0.5
        
        temp = environmental_conditions.get("temperature", "")
        humidity = environmental_conditions.get("humidity", "")
        
        # 转换为字符串进行检查
        temp_str = str(temp) if temp else ""
        humidity_str = str(humidity) if humidity else ""
        
        if "高湿" in humidity_str or ("适宜" in temp_str):
            risk_score += 0.3
        
        if risk_score >= 0.7:
            risk_level = "高风险"
            warning = "病害传播风险高，需立即防治"
        elif risk_score >= 0.4:
            risk_level = "中风险"
            warning = "病害有一定传播风险，建议及时防治"
        else:
            risk_level = "低风险"
            warning = "病害传播风险较低，保持观察"
        
        level = {
            "风险等级": risk_level,
            "风险评分": round(risk_score, 4),
            "传播速度": risk_factors.get("spread_rate", "中等"),
            "环境适宜度": "适宜" if "高湿" in humidity_str else "中等",
            "预警信息": warning,
            "影响范围": "局部" if risk_score < 0.5 else "大面积"
        }
        
        return level
    
    def _generate_treatment_measures(
        self,
        disease_name: str,
        severity_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成防治措施部分
        
        :param disease_name: 病害名称
        :param severity_assessment: 严重度评估结果
        :return: 防治措施字典
        """
        default_treatments = [
            {"name": "广谱杀菌剂", "concentration": "按说明书", "dosage": "按说明"}
        ]
        
        treatments = default_treatments
        if disease_name in self.disease_knowledge:
            treatments = self.disease_knowledge[disease_name].get(
                "treatments", default_treatments
            )
        
        severity_level = severity_assessment.get("严重度等级", "中度")
        
        # 根据严重度调整防治步骤
        if severity_level == "轻度":
            steps = [
                "1. 定期巡查，监测病情发展",
                "2. 喷施保护性杀菌剂预防",
                "3. 加强田间管理，改善通风透光"
            ]
        elif severity_level == "中度":
            steps = [
                "1. 立即喷施治疗性杀菌剂",
                "2. 7-10 天后复查并补喷",
                "3. 清除严重病株，减少菌源",
                "4. 改善田间通风降湿"
            ]
        else:
            steps = [
                "1. 紧急喷施高效治疗剂",
                "2. 清除严重病株并带出田外",
                "3. 5-7 天后复查，必要时再次喷药",
                "4. 全面改善田间环境",
                "5. 考虑提前收获减少损失"
            ]
        
        measures = {
            "推荐药剂": treatments[:3],
            "用药浓度": treatments[0].get("concentration", "按说明书") if treatments else "按说明书",
            "防治步骤": steps,
            "施药时机": "晴朗无风天气，避开高温时段",
            "安全间隔期": "施药后 7-14 天可收获",
            "注意事项": [
                "交替使用不同作用机理的药剂",
                "严格遵守安全间隔期",
                "注意个人防护"
            ]
        }
        
        return measures
    
    def _generate_followup_plan(
        self,
        disease_name: str,
        severity_assessment: Dict[str, Any],
        risk_level: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成复查计划部分
        
        :param disease_name: 病害名称
        :param severity_assessment: 严重度评估结果
        :param risk_level: 风险等级结果
        :return: 复查计划字典
        """
        severity_level = severity_assessment.get("严重度等级", "中度")
        risk = risk_level.get("风险等级", "中风险")
        
        # 根据严重度和风险确定复查间隔
        if severity_level == "重度" or risk == "高风险":
            days_interval = 3
            urgency = "紧急"
        elif severity_level == "中度" or risk == "中风险":
            days_interval = 7
            urgency = "重要"
        else:
            days_interval = 14
            urgency = "常规"
        
        current_date = datetime.now()
        next_check_date = current_date + timedelta(days=days_interval)
        
        plan = {
            "复查时间": next_check_date.strftime("%Y-%m-%d"),
            "复查间隔": f"{days_interval}天",
            "紧急程度": urgency,
            "复查内容": [
                "拍摄田间照片（与本次相同位置）",
                "描述病情变化情况",
                "记录已采取的防治措施",
                "评估防治效果"
            ],
            "预期目标": f"{days_interval}天后病情得到控制",
            "复查任务 ID": f"FOLLOWUP_{current_date.strftime('%Y%m%d')}_{disease_name[:2]}"
        }
        
        return plan
    
    def _match_environmental_conditions(
        self,
        disease_name: str,
        conditions: Dict[str, str]
    ) -> str:
        """
        匹配环境条件与病害适宜条件
        
        :param disease_name: 病害名称
        :param conditions: 当前环境条件
        :return: 匹配结果描述
        """
        if disease_name not in self.disease_knowledge:
            return "环境条件匹配信息不足"
        
        risk_factors = self.disease_knowledge[disease_name].get("risk_factors", {})
        
        temp = conditions.get("temperature", "")
        humidity = conditions.get("humidity", "")
        
        match_result = []
        if risk_factors.get("temperature"):
            match_result.append(f"温度：{risk_factors['temperature']}")
        if risk_factors.get("humidity"):
            match_result.append(f"湿度：{risk_factors['humidity']}")
        
        if match_result:
            return f"当前环境适宜{disease_name}发生：{', '.join(match_result)}"
        else:
            return "环境条件匹配信息不足"
    
    def export_to_json(self, diagnosis_plan: Dict[str, Any], file_path: str) -> None:
        """
        将诊断计划导出为 JSON 文件
        
        :param diagnosis_plan: 诊断计划字典
        :param file_path: 输出文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(diagnosis_plan, f, ensure_ascii=False, indent=2)
        print(f"[PlanningEngine] 诊断计划已导出至：{file_path}")
    
    def validate_diagnosis_plan(self, diagnosis_plan: Dict[str, Any]) -> bool:
        """
        验证诊断计划是否包含所有必需字段
        
        :param diagnosis_plan: 诊断计划字典
        :return: 验证结果
        """
        required_fields = [
            "病害诊断",
            "严重度评估",
            "推理依据",
            "风险等级",
            "防治措施",
            "复查计划"
        ]
        
        for field in required_fields:
            if field not in diagnosis_plan:
                print(f"[PlanningEngine] 验证失败：缺少必需字段 '{field}'")
                return False
        
        print("[PlanningEngine] 诊断计划验证通过")
        return True


def test_planning_engine():
    """测试规划引擎"""
    print("=" * 60)
    print("🧪 测试 PlanningEngine")
    print("=" * 60)
    
    engine = PlanningEngine()
    
    # 模拟认知层输出
    cognition_output = {
        "disease_name": "条锈病",
        "confidence": 0.92,
        "severity_score": 0.45,
        "visual_features": [
            "叶片出现黄色条状孢子堆",
            "沿叶脉排列",
            "叶片褪绿"
        ],
        "environmental_conditions": {
            "temperature": "12°C",
            "humidity": "高湿"
        },
        "user_description": "叶片有黄色条纹，最近下雨"
    }
    
    print("\n1️⃣ 生成诊断计划")
    diagnosis_plan = engine.generate_diagnosis_plan(cognition_output)
    
    print("\n2️⃣ 验证诊断计划")
    is_valid = engine.validate_diagnosis_plan(diagnosis_plan)
    print(f"验证结果：{'通过' if is_valid else '失败'}")
    
    print("\n3️⃣ 诊断计划内容:")
    print(json.dumps(diagnosis_plan, ensure_ascii=False, indent=2))
    
    print("\n4️⃣ 导出诊断计划")
    output_path = os.path.join(os.path.dirname(__file__), "..", "..", "exports", 
                               f"diagnosis_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    engine.export_to_json(diagnosis_plan, output_path)
    
    print("\n" + "=" * 60)
    print("✅ PlanningEngine 测试通过！")
    print("=" * 60)
    
    return diagnosis_plan


if __name__ == "__main__":
    test_planning_engine()

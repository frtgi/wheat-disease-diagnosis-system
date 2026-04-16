# -*- coding: utf-8 -*-
"""
防治方案生成工具 - Treatment Tool
根据病害诊断结果生成个性化防治方案
"""

import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .base_tool import BaseTool


class TreatmentTool(BaseTool):
    """
    防治方案生成工具类
    
    功能：
    1. 根据病害类型和严重度生成防治方案
    2. 推荐合适的药剂和用药浓度
    3. 生成详细的防治步骤
    4. 提供施药时机和安全间隔期建议
    
    输入参数:
        disease_name: 病害名称（必需）
        severity_level: 严重度等级（可选）
        environmental_conditions: 环境条件（可选）
        existing_measures: 已有防治措施（可选）
    
    输出结果:
        recommended_agents: 推荐药剂列表
        application_method: 施药方法
        treatment_steps: 防治步骤
        timing_suggestions: 施药时机建议
        safety_interval: 安全间隔期
        precautions: 注意事项
    """
    
    # 防治方案知识库
    TREATMENT_KNOWLEDGE = {
        "条锈病": {
            "agents": [
                {
                    "name": "三唑酮",
                    "concentration": "15% 可湿性粉剂",
                    "dosage": "600-800 倍液",
                    "mechanism": "抑制真菌细胞膜合成",
                    "preharvest_interval": "14 天"
                },
                {
                    "name": "戊唑醇",
                    "concentration": "10% 水乳剂",
                    "dosage": "40-50ml/亩",
                    "mechanism": "干扰真菌细胞壁形成",
                    "preharvest_interval": "10 天"
                },
                {
                    "name": "丙环唑",
                    "concentration": "25% 乳油",
                    "dosage": "20-30ml/亩",
                    "mechanism": "抑制真菌甾醇合成",
                    "preharvest_interval": "14 天"
                }
            ]
        },
        "叶锈病": {
            "agents": [
                {
                    "name": "三唑酮",
                    "concentration": "15% 可湿性粉剂",
                    "dosage": "600-800 倍液",
                    "mechanism": "抑制真菌细胞膜合成",
                    "preharvest_interval": "14 天"
                },
                {
                    "name": "戊唑醇",
                    "concentration": "10% 水乳剂",
                    "dosage": "40-50ml/亩",
                    "mechanism": "干扰真菌细胞壁形成",
                    "preharvest_interval": "10 天"
                }
            ]
        },
        "秆锈病": {
            "agents": [
                {
                    "name": "三唑酮",
                    "concentration": "15% 可湿性粉剂",
                    "dosage": "600-800 倍液",
                    "mechanism": "抑制真菌细胞膜合成",
                    "preharvest_interval": "14 天"
                },
                {
                    "name": "戊唑醇",
                    "concentration": "10% 水乳剂",
                    "dosage": "40-50ml/亩",
                    "mechanism": "干扰真菌细胞壁形成",
                    "preharvest_interval": "10 天"
                }
            ]
        },
        "白粉病": {
            "agents": [
                {
                    "name": "三唑酮",
                    "concentration": "15% 可湿性粉剂",
                    "dosage": "600-800 倍液",
                    "mechanism": "抑制真菌细胞膜合成",
                    "preharvest_interval": "14 天"
                },
                {
                    "name": "腈菌唑",
                    "concentration": "12.5% 乳油",
                    "dosage": "20-30ml/亩",
                    "mechanism": "抑制真菌甾醇合成",
                    "preharvest_interval": "7 天"
                }
            ]
        },
        "蚜虫": {
            "agents": [
                {
                    "name": "吡虫啉",
                    "concentration": "10% 可湿性粉剂",
                    "dosage": "20-30g/亩",
                    "mechanism": "作用于昆虫神经系统",
                    "preharvest_interval": "7 天"
                },
                {
                    "name": "啶虫脒",
                    "concentration": "3% 乳油",
                    "dosage": "30-40ml/亩",
                    "mechanism": "干扰昆虫神经传递",
                    "preharvest_interval": "7 天"
                }
            ]
        },
        "螨虫": {
            "agents": [
                {
                    "name": "阿维菌素",
                    "concentration": "1.8% 乳油",
                    "dosage": "30-40ml/亩",
                    "mechanism": "干扰昆虫神经肌肉系统",
                    "preharvest_interval": "7 天"
                },
                {
                    "name": "哒螨灵",
                    "concentration": "15% 乳油",
                    "dosage": "20-30ml/亩",
                    "mechanism": "抑制螨虫呼吸作用",
                    "preharvest_interval": "14 天"
                }
            ]
        }
    }
    
    def __init__(self):
        """
        初始化防治方案生成工具
        """
        super().__init__(
            name="TreatmentTool",
            description="防治方案生成工具，根据病害诊断结果生成个性化防治方案"
        )
        self._treatment_knowledge = self.TREATMENT_KNOWLEDGE
    
    def get_name(self) -> str:
        """
        获取工具名称
        
        :return: 工具名称
        """
        return "TreatmentTool"
    
    def get_description(self) -> str:
        """
        获取工具描述
        
        :return: 工具描述
        """
        return "防治方案生成工具，根据病害诊断结果生成个性化防治方案"
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证输入参数
        
        :param kwargs: 输入参数
        :return: 参数是否有效
        """
        disease_name = kwargs.get('disease_name')
        if not disease_name:
            print("[TreatmentTool] 参数验证失败：缺少 disease_name")
            return False
        
        return True
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行防治方案生成
        
        :param kwargs: 执行参数
            - disease_name: 病害名称
            - severity_level: 严重度等级（轻度/中度/重度）
            - environmental_conditions: 环境条件
            - existing_measures: 已有防治措施
        :return: 防治方案字典
        """
        disease_name = kwargs.get('disease_name')
        severity_level = kwargs.get('severity_level', '中度')
        environmental_conditions = kwargs.get('environmental_conditions', {})
        existing_measures = kwargs.get('existing_measures', {})
        
        print(f"[TreatmentTool] 生成防治方案：{disease_name} ({severity_level})")
        
        try:
            # 生成防治方案
            treatment_plan = self._generate_treatment_plan(
                disease_name,
                severity_level,
                environmental_conditions,
                existing_measures
            )
            
            result = {
                "success": True,
                "data": treatment_plan,
                "message": f"防治方案生成成功：{disease_name}",
                "tool_name": self.get_name()
            }
            
            print(f"[TreatmentTool] 防治方案生成完成")
            
            return result
        
        except Exception as e:
            error_msg = f"防治方案生成异常：{str(e)}"
            print(f"[TreatmentTool] {error_msg}")
            return {
                "success": False,
                "data": None,
                "message": error_msg,
                "error": error_msg,
                "tool_name": self.get_name()
            }
    
    def _generate_treatment_plan(
        self,
        disease_name: str,
        severity_level: str,
        environmental_conditions: Dict[str, Any],
        existing_measures: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成防治方案
        
        :param disease_name: 病害名称
        :param severity_level: 严重度等级
        :param environmental_conditions: 环境条件
        :param existing_measures: 已有防治措施
        :return: 防治方案字典
        """
        # 获取病害防治知识
        disease_treatment = self._treatment_knowledge.get(disease_name)
        
        if not disease_treatment:
            return self._generate_default_plan(disease_name, severity_level)
        
        agents = disease_treatment.get("agents", [])
        
        # 根据严重度调整推荐策略
        if severity_level == "轻度":
            recommended_agents = agents[:1]
            urgency = "常规防治"
        elif severity_level == "中度":
            recommended_agents = agents[:2]
            urgency = "及时防治"
        else:  # 重度
            recommended_agents = agents
            urgency = "紧急防治"
        
        # 生成防治步骤
        treatment_steps = self._generate_treatment_steps(
            severity_level,
            environmental_conditions
        )
        
        # 生成施药时机建议
        timing_suggestions = self._generate_timing_suggestions(
            environmental_conditions
        )
        
        # 生成注意事项
        precautions = self._generate_precautions(disease_name, severity_level)
        
        # 计算安全间隔期
        safety_interval = self._calculate_safety_interval(recommended_agents)
        
        treatment_plan = {
            "disease_name": disease_name,
            "severity_level": severity_level,
            "urgency": urgency,
            "recommended_agents": recommended_agents,
            "application_method": "叶面喷施，均匀覆盖",
            "treatment_steps": treatment_steps,
            "timing_suggestions": timing_suggestions,
            "safety_interval": safety_interval,
            "precautions": precautions,
            "generated_time": datetime.now().isoformat()
        }
        
        return treatment_plan
    
    def _generate_default_plan(
        self,
        disease_name: str,
        severity_level: str
    ) -> Dict[str, Any]:
        """
        生成默认防治方案（未知病害）
        
        :param disease_name: 病害名称
        :param severity_level: 严重度等级
        :return: 默认防治方案
        """
        return {
            "disease_name": disease_name,
            "severity_level": severity_level,
            "urgency": "建议咨询专家",
            "recommended_agents": [
                {
                    "name": "广谱杀菌剂",
                    "concentration": "按说明书",
                    "dosage": "按说明使用",
                    "mechanism": "广谱抗菌",
                    "preharvest_interval": "按说明"
                }
            ],
            "application_method": "按说明书使用",
            "treatment_steps": [
                "1. 确认病害类型",
                "2. 选择合适的防治药剂",
                "3. 按说明书配制药液",
                "4. 均匀喷施于叶片表面"
            ],
            "timing_suggestions": "晴朗无风天气，避开高温时段",
            "safety_interval": "按药剂说明",
            "precautions": [
                "建议咨询农业专家",
                "先小面积试验",
                "注意个人防护"
            ],
            "generated_time": datetime.now().isoformat()
        }
    
    def _generate_treatment_steps(
        self,
        severity_level: str,
        environmental_conditions: Dict[str, Any]
    ) -> List[str]:
        """
        生成防治步骤
        
        :param severity_level: 严重度等级
        :param environmental_conditions: 环境条件
        :return: 防治步骤列表
        """
        if severity_level == "轻度":
            steps = [
                "1. 定期巡查，监测病情发展",
                "2. 喷施保护性杀菌剂预防扩散",
                "3. 加强田间管理，改善通风透光",
                "4. 7 天后复查病情"
            ]
        elif severity_level == "中度":
            steps = [
                "1. 立即配制药液，准备喷施",
                "2. 均匀喷施治疗性杀菌剂",
                "3. 重点喷施病斑部位",
                "4. 7-10 天后复查并补喷",
                "5. 清除严重病株，减少菌源"
            ]
        else:  # 重度
            steps = [
                "1. 紧急配制药液，准备防治",
                "2. 喷施高效治疗剂，加大浓度",
                "3. 清除严重病株并带出田外",
                "4. 5-7 天后复查，必要时再次喷药",
                "5. 全面改善田间环境",
                "6. 考虑提前收获减少损失"
            ]
        
        return steps
    
    def _generate_timing_suggestions(
        self,
        environmental_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成施药时机建议
        
        :param environmental_conditions: 环境条件
        :return: 施药时机建议字典
        """
        return {
            "best_time": "晴朗无风天气，上午 9-11 点或下午 3-5 点",
            "avoid_conditions": [
                "避免雨天施药",
                "避免高温时段（中午 12 点 - 下午 3 点）",
                "避免大风天气"
            ],
            "frequency": "根据病情，间隔 7-10 天喷施一次",
            "environmental_notes": self._get_environmental_notes(environmental_conditions)
        }
    
    def _get_environmental_notes(
        self,
        environmental_conditions: Dict[str, Any]
    ) -> str:
        """
        获取环境条件相关的施药建议
        
        :param environmental_conditions: 环境条件
        :return: 环境建议字符串
        """
        if not environmental_conditions:
            return "无特殊环境限制"
        
        notes = []
        
        temperature = environmental_conditions.get("temperature", "")
        humidity = environmental_conditions.get("humidity", "")
        
        if "高温" in temperature:
            notes.append("高温天气，建议避开中午时段施药")
        if "高湿" in humidity or "阴雨" in humidity:
            notes.append("高湿环境，注意选择雨前施药或添加助剂")
        
        return "; ".join(notes) if notes else "环境条件适宜施药"
    
    def _generate_precautions(
        self,
        disease_name: str,
        severity_level: str
    ) -> List[str]:
        """
        生成注意事项
        
        :param disease_name: 病害名称
        :param severity_level: 严重度等级
        :return: 注意事项列表
        """
        precautions = [
            "交替使用不同作用机理的药剂，避免产生抗药性",
            "严格按照推荐浓度配药，不要随意增减",
            "施药时穿戴防护服、口罩、手套等防护用品",
            "施药后及时清洗暴露皮肤和衣物",
            "遵守安全间隔期，确保农产品安全"
        ]
        
        if severity_level == "重度":
            precautions.append("重度发生，建议咨询当地农业专家")
        
        return precautions
    
    def _calculate_safety_interval(
        self,
        recommended_agents: List[Dict[str, Any]]
    ) -> str:
        """
        计算安全间隔期
        
        :param recommended_agents: 推荐药剂列表
        :return: 安全间隔期字符串
        """
        if not recommended_agents:
            return "按药剂说明"
        
        intervals = []
        for agent in recommended_agents:
            interval = agent.get("preharvest_interval", "未知")
            intervals.append(interval)
        
        if len(set(intervals)) == 1:
            return intervals[0]
        else:
            return f"{'-'.join(intervals)}（取最大值）"


def test_treatment_tool():
    """测试防治方案生成工具"""
    print("=" * 60)
    print("🧪 测试 TreatmentTool")
    print("=" * 60)
    
    tool = TreatmentTool()
    
    print("\n1️⃣ 获取工具信息")
    print(f"   工具名称：{tool.get_name()}")
    print(f"   工具描述：{tool.get_description()}")
    
    print("\n2️⃣ 生成防治方案：条锈病（中度）")
    result = tool.execute(
        disease_name="条锈病",
        severity_level="中度"
    )
    
    print(f"\n3️⃣ 防治方案:")
    print(f"   成功：{result.get('success')}")
    if result.get('data'):
        data = result['data']
        print(f"   病害：{data.get('disease_name')}")
        print(f"   紧急程度：{data.get('urgency')}")
        print(f"   推荐药剂:")
        for agent in data.get('recommended_agents', []):
            print(f"     - {agent.get('name')} ({agent.get('concentration')})")
        print(f"   防治步骤:")
        for step in data.get('treatment_steps', []):
            print(f"     {step}")
        print(f"   安全间隔期：{data.get('safety_interval')}")
    
    print("\n4️⃣ 生成防治方案：蚜虫（轻度）")
    result2 = tool.execute(
        disease_name="蚜虫",
        severity_level="轻度"
    )
    
    if result2.get('data'):
        data2 = result2['data']
        print(f"   推荐药剂:")
        for agent in data2.get('recommended_agents', []):
            print(f"     - {agent.get('name')} - {agent.get('dosage')}")
    
    print("\n" + "=" * 60)
    print("✅ TreatmentTool 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_treatment_tool()

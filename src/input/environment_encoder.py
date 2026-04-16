"""
环境因素编码器模块

负责解析和编码天气数据、生长阶段、发病部位等环境因素，
并计算环境风险评分。
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date


class EnvironmentEncoder:
    """环境因素编码器类"""
    
    # 小麦生长阶段定义及编码
    GROWTH_STAGES = {
        "苗期": 0, "分蘖期": 1, "越冬期": 2, "返青期": 3, "起身期": 4,
        "拔节期": 5, "孕穗期": 6, "抽穗期": 7, "开花期": 8, "灌浆期": 9, "成熟期": 10
    }
    
    # 生长阶段对病害的易感性权重
    GROWTH_STAGE_SUSCEPTIBILITY = {
        "苗期": 0.6, "分蘖期": 0.7, "越冬期": 0.3, "返青期": 0.5, "起身期": 0.6,
        "拔节期": 0.8, "孕穗期": 0.9, "抽穗期": 1.0, "开花期": 0.9, "灌浆期": 0.8, "成熟期": 0.5
    }
    
    # 发病部位定义及编码
    DISEASE_PARTS = {
        "叶片": 0, "叶鞘": 1, "茎秆": 2, "穗部": 3, "根部": 4, "整株": 5
    }
    
    # 发病部位对病害诊断的重要性权重
    DISEASE_PART_WEIGHTS = {
        "叶片": 1.0, "叶鞘": 0.8, "茎秆": 0.7, "穗部": 0.9, "根部": 0.6, "整株": 1.0
    }
    
    # 天气状况编码
    WEATHER_CONDITIONS = {
        "晴": 0, "多云": 1, "阴": 2, "小雨": 3, "中雨": 4, "大雨": 5, "雪": 6
    }
    
    # 天气状况对病害发生的风险权重
    WEATHER_RISK_WEIGHTS = {
        "晴": 0.2, "多云": 0.4, "阴": 0.6, "小雨": 0.7, "中雨": 0.8, "大雨": 0.9, "雪": 0.3
    }
    
    def __init__(self):
        """初始化环境编码器"""
        pass
    
    def encode_weather(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析和编码天气数据
        
        参数:
            weather_data: 包含温度、湿度、降水等信息的字典
            
        返回:
            编码后的天气数据
        """
        encoded = {
            "temperature": self._encode_temperature(weather_data.get("temperature")),
            "humidity": self._encode_humidity(weather_data.get("humidity")),
            "precipitation": self._encode_precipitation(weather_data.get("precipitation")),
            "weather_condition": self._encode_weather_condition(weather_data.get("weather_condition")),
            "risk_score": 0.0
        }
        
        # 计算天气风险评分
        encoded["risk_score"] = self._calculate_weather_risk_score(encoded)
        
        return encoded
    
    def _encode_temperature(self, temperature: Optional[float]) -> Dict[str, Any]:
        """
        编码温度数据
        
        参数:
            temperature: 温度值（摄氏度）
            
        返回:
            编码后的温度信息
        """
        if temperature is None:
            return {
                "value": None,
                "category": "未知",
                "risk_level": 0.5,
                "encoded": 0.5
            }
        
        # 温度分类
        if temperature < 5:
            category = "低温"
            risk_level = 0.3
        elif 5 <= temperature < 15:
            category = "较低温"
            risk_level = 0.5
        elif 15 <= temperature < 25:
            category = "适宜"
            risk_level = 0.7
        elif 25 <= temperature < 30:
            category = "较高温"
            risk_level = 0.8
        else:
            category = "高温"
            risk_level = 0.6
        
        # 归一化到 [0, 1]
        encoded = np.clip((temperature + 5) / 40, 0, 1)
        
        return {
            "value": temperature,
            "category": category,
            "risk_level": risk_level,
            "encoded": encoded
        }
    
    def _encode_humidity(self, humidity: Optional[float]) -> Dict[str, Any]:
        """
        编码湿度数据
        
        参数:
            humidity: 湿度值（百分比）
            
        返回:
            编码后的湿度信息
        """
        if humidity is None:
            return {
                "value": None,
                "category": "未知",
                "risk_level": 0.5,
                "encoded": 0.5
            }
        
        # 湿度分类
        if humidity < 40:
            category = "干燥"
            risk_level = 0.3
        elif 40 <= humidity < 60:
            category = "较干燥"
            risk_level = 0.5
        elif 60 <= humidity < 80:
            category = "适宜"
            risk_level = 0.7
        elif 80 <= humidity < 90:
            category = "较湿润"
            risk_level = 0.9
        else:
            category = "高湿"
            risk_level = 1.0
        
        # 归一化到 [0, 1]
        encoded = humidity / 100.0
        
        return {
            "value": humidity,
            "category": category,
            "risk_level": risk_level,
            "encoded": encoded
        }
    
    def _encode_precipitation(self, precipitation: Optional[float]) -> Dict[str, Any]:
        """
        编码降水数据
        
        参数:
            precipitation: 降水量（毫米）
            
        返回:
            编码后的降水信息
        """
        if precipitation is None:
            return {
                "value": None,
                "category": "未知",
                "risk_level": 0.5,
                "encoded": 0.5
            }
        
        # 降水分类
        if precipitation == 0:
            category = "无降水"
            risk_level = 0.3
        elif 0 < precipitation < 10:
            category = "小雨"
            risk_level = 0.6
        elif 10 <= precipitation < 25:
            category = "中雨"
            risk_level = 0.8
        elif 25 <= precipitation < 50:
            category = "大雨"
            risk_level = 0.9
        else:
            category = "暴雨"
            risk_level = 0.8
        
        # 归一化到 [0, 1] (假设最大降水为 100mm)
        encoded = np.clip(precipitation / 100, 0, 1)
        
        return {
            "value": precipitation,
            "category": category,
            "risk_level": risk_level,
            "encoded": encoded
        }
    
    def _encode_weather_condition(self, condition: Optional[str]) -> Dict[str, Any]:
        """
        编码天气状况
        
        参数:
            condition: 天气状况描述
            
        返回:
            编码后的天气状况信息
        """
        if condition is None:
            return {
                "value": None,
                "category": "未知",
                "risk_level": 0.5,
                "encoded": 0.5
            }
        
        # 获取编码和风险权重
        code = self.WEATHER_CONDITIONS.get(condition, 0)
        risk_level = self.WEATHER_RISK_WEIGHTS.get(condition, 0.5)
        
        # 归一化编码
        encoded = code / len(self.WEATHER_CONDITIONS)
        
        return {
            "value": condition,
            "category": condition,
            "risk_level": risk_level,
            "encoded": encoded
        }
    
    def _calculate_weather_risk_score(self, encoded_weather: Dict[str, Any]) -> float:
        """
        计算天气风险评分
        
        参数:
            encoded_weather: 编码后的天气数据
            
        返回:
            风险评分 (0-1)
        """
        # 各因素的权重
        weights = {
            "temperature": 0.2,
            "humidity": 0.35,
            "precipitation": 0.25,
            "weather_condition": 0.2
        }
        
        # 计算加权风险评分
        risk_score = 0.0
        
        temp_risk = encoded_weather["temperature"]["risk_level"]
        humidity_risk = encoded_weather["humidity"]["risk_level"]
        precip_risk = encoded_weather["precipitation"]["risk_level"]
        condition_risk = encoded_weather["weather_condition"]["risk_level"]
        
        risk_score = (
            weights["temperature"] * temp_risk +
            weights["humidity"] * humidity_risk +
            weights["precipitation"] * precip_risk +
            weights["weather_condition"] * condition_risk
        )
        
        return round(risk_score, 3)
    
    def encode_growth_stage(self, stage: str) -> Dict[str, Any]:
        """
        编码生长阶段
        
        参数:
            stage: 生长阶段名称
            
        返回:
            编码后的生长阶段信息
        """
        if stage not in self.GROWTH_STAGES:
            stage = "未知"
        
        # 获取编码
        code = self.GROWTH_STAGES.get(stage, -1)
        
        # 获取易感性权重
        susceptibility = self.GROWTH_STAGE_SUSCEPTIBILITY.get(stage, 0.5)
        
        # One-hot 编码
        one_hot = np.zeros(len(self.GROWTH_STAGES))
        if code >= 0:
            one_hot[code] = 1
        
        return {
            "value": stage,
            "code": code,
            "susceptibility": susceptibility,
            "one_hot": one_hot.tolist(),
            "encoded": code / len(self.GROWTH_STAGES) if code >= 0 else 0.5
        }
    
    def encode_disease_part(self, part: str) -> Dict[str, Any]:
        """
        编码发病部位
        
        参数:
            part: 发病部位名称
            
        返回:
            编码后的发病部位信息
        """
        if part not in self.DISEASE_PARTS:
            part = "未知"
        
        # 获取编码
        code = self.DISEASE_PARTS.get(part, -1)
        
        # 获取权重
        weight = self.DISEASE_PART_WEIGHTS.get(part, 0.5)
        
        # One-hot 编码
        one_hot = np.zeros(len(self.DISEASE_PARTS))
        if code >= 0:
            one_hot[code] = 1
        
        return {
            "value": part,
            "code": code,
            "weight": weight,
            "one_hot": one_hot.tolist(),
            "encoded": code / len(self.DISEASE_PARTS) if code >= 0 else 0.5
        }
    
    def encode_multiple_disease_parts(self, parts: List[str]) -> Dict[str, Any]:
        """
        编码多个发病部位
        
        参数:
            parts: 发病部位列表
            
        返回:
            编码后的多发病部位信息
        """
        if not parts:
            return {
                "values": [],
                "codes": [],
                "multi_hot": np.zeros(len(self.DISEASE_PARTS)).tolist(),
                "encoded": 0.5
            }
        
        # Multi-hot 编码
        multi_hot = np.zeros(len(self.DISEASE_PARTS))
        codes = []
        valid_parts = []
        
        for part in parts:
            if part in self.DISEASE_PARTS:
                code = self.DISEASE_PARTS[part]
                multi_hot[code] = 1
                codes.append(code)
                valid_parts.append(part)
        
        # 计算综合权重
        total_weight = sum(self.DISEASE_PART_WEIGHTS.get(part, 0.5) for part in valid_parts)
        avg_weight = total_weight / len(valid_parts) if valid_parts else 0.5
        
        return {
            "values": valid_parts,
            "codes": codes,
            "multi_hot": multi_hot.tolist(),
            "weight": avg_weight,
            "encoded": sum(codes) / len(self.DISEASE_PARTS) / len(codes) if codes else 0.5
        }
    
    def calculate_environment_risk_score(
        self,
        weather_data: Dict[str, Any],
        growth_stage: str,
        disease_parts: List[str]
    ) -> Dict[str, Any]:
        """
        计算综合环境风险评分
        
        参数:
            weather_data: 天气数据
            growth_stage: 生长阶段
            disease_parts: 发病部位列表
            
        返回:
            包含各项评分和综合评分的字典
        """
        # 编码各项数据
        encoded_weather = self.encode_weather(weather_data)
        encoded_stage = self.encode_growth_stage(growth_stage)
        encoded_parts = self.encode_multiple_disease_parts(disease_parts)
        
        # 各维度风险评分
        weather_risk = encoded_weather["risk_score"]
        stage_risk = encoded_stage["susceptibility"]
        parts_risk = encoded_parts["weight"]
        
        # 计算综合风险评分（加权平均）
        # 权重：天气 50%, 生长阶段 30%, 发病部位 20%
        comprehensive_risk = (
            0.5 * weather_risk +
            0.3 * stage_risk +
            0.2 * parts_risk
        )
        
        # 风险等级划分
        if comprehensive_risk < 0.3:
            risk_level = "低风险"
        elif comprehensive_risk < 0.5:
            risk_level = "中低风险"
        elif comprehensive_risk < 0.7:
            risk_level = "中风险"
        elif comprehensive_risk < 0.85:
            risk_level = "高风险"
        else:
            risk_level = "极高风险"
        
        return {
            "weather_risk": round(weather_risk, 3),
            "growth_stage_risk": round(stage_risk, 3),
            "disease_part_risk": round(parts_risk, 3),
            "comprehensive_risk": round(comprehensive_risk, 3),
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat(),
            "details": {
                "weather": encoded_weather,
                "growth_stage": encoded_stage,
                "disease_parts": encoded_parts
            }
        }
    
    def create_environment_feature_vector(
        self,
        weather_data: Dict[str, Any],
        growth_stage: str,
        disease_parts: List[str]
    ) -> np.ndarray:
        """
        创建环境特征向量
        
        参数:
            weather_data: 天气数据
            growth_stage: 生长阶段
            disease_parts: 发病部位列表
            
        返回:
            环境特征向量 (numpy 数组)
        """
        # 编码各项数据
        encoded_weather = self.encode_weather(weather_data)
        encoded_stage = self.encode_growth_stage(growth_stage)
        encoded_parts = self.encode_multiple_disease_parts(disease_parts)
        
        # 构建特征向量
        features = [
            # 天气特征 (4 维)
            encoded_weather["temperature"]["encoded"],
            encoded_weather["humidity"]["encoded"],
            encoded_weather["precipitation"]["encoded"],
            encoded_weather["weather_condition"]["encoded"],
            
            # 生长阶段特征 (11 维 one-hot)
            *encoded_stage["one_hot"],
            
            # 发病部位特征 (6 维 multi-hot)
            *encoded_parts["multi_hot"],
            
            # 风险评分特征 (3 维)
            encoded_weather["risk_score"],
            encoded_stage["susceptibility"],
            encoded_parts["weight"]
        ]
        
        return np.array(features, dtype=np.float32)
    
    def parse_weather_from_text(self, text: str) -> Dict[str, Any]:
        """
        从文本中解析天气信息
        
        参数:
            text: 包含天气信息的文本
            
        返回:
            解析后的天气数据
        """
        import re
        
        weather_data = {}
        
        # 解析温度
        temp_pattern = r'温度 [:\s为]*(-?\d+(?:\.\d+)?)\s*[°℃度]'
        temp_match = re.search(temp_pattern, text, re.IGNORECASE)
        if temp_match:
            weather_data["temperature"] = float(temp_match.group(1))
        
        # 解析湿度
        humidity_pattern = r'湿度 [:\s为]*(\d+(?:\.\d+)?)\s*%'
        humidity_match = re.search(humidity_pattern, text, re.IGNORECASE)
        if humidity_match:
            weather_data["humidity"] = float(humidity_match.group(1))
        
        # 解析降水
        precip_pattern = r'降水 (?:量)?[:\s为]*(\d+(?:\.\d+)?)\s*(?:mm|毫米)'
        precip_match = re.search(precip_pattern, text, re.IGNORECASE)
        if precip_match:
            weather_data["precipitation"] = float(precip_match.group(1))
        
        # 解析天气状况
        for condition in self.WEATHER_CONDITIONS.keys():
            if condition in text:
                weather_data["weather_condition"] = condition
                break
        
        return weather_data
    
    def get_seasonal_risk_factors(self, month: Optional[int] = None) -> Dict[str, Any]:
        """
        获取季节性风险因子
        
        参数:
            month: 月份 (1-12)，如果不提供则使用当前月份
            
        返回:
            季节性风险因子
        """
        if month is None:
            month = datetime.now().month
        
        # 定义各月份的季节风险因子
        seasonal_factors = {
            1: {"name": "冬季", "base_risk": 0.2, "common_diseases": ["纹枯病", "根腐病"]},
            2: {"name": "冬季", "base_risk": 0.2, "common_diseases": ["纹枯病", "根腐病"]},
            3: {"name": "春季", "base_risk": 0.5, "common_diseases": ["纹枯病", "条锈病"]},
            4: {"name": "春季", "base_risk": 0.6, "common_diseases": ["条锈病", "白粉病"]},
            5: {"name": "春季", "base_risk": 0.7, "common_diseases": ["条锈病", "赤霉病"]},
            6: {"name": "夏季", "base_risk": 0.6, "common_diseases": ["赤霉病", "叶锈病"]},
            7: {"name": "夏季", "base_risk": 0.5, "common_diseases": ["叶锈病", "纹枯病"]},
            8: {"name": "夏季", "base_risk": 0.4, "common_diseases": ["纹枯病", "根腐病"]},
            9: {"name": "秋季", "base_risk": 0.5, "common_diseases": ["纹枯病", "条锈病"]},
            10: {"name": "秋季", "base_risk": 0.4, "common_diseases": ["纹枯病", "蚜虫"]},
            11: {"name": "秋季", "base_risk": 0.3, "common_diseases": ["纹枯病", "根腐病"]},
            12: {"name": "冬季", "base_risk": 0.2, "common_diseases": ["纹枯病", "根腐病"]}
        }
        
        return seasonal_factors.get(month, {"name": "未知", "base_risk": 0.5, "common_diseases": []})
    
    def generate_environment_report(
        self,
        weather_data: Dict[str, Any],
        growth_stage: str,
        disease_parts: List[str]
    ) -> str:
        """
        生成环境因素分析报告
        
        参数:
            weather_data: 天气数据
            growth_stage: 生长阶段
            disease_parts: 发病部位列表
            
        返回:
            环境因素分析报告文本
        """
        risk_info = self.calculate_environment_risk_score(
            weather_data, growth_stage, disease_parts
        )
        
        season_info = self.get_seasonal_risk_factors()
        
        report = f"""
=== 环境因素分析报告 ===

【天气条件】
  温度：{weather_data.get('temperature', '未知')}°C - {risk_info['details']['weather']['temperature']['category']}
  湿度：{weather_data.get('humidity', '未知')}% - {risk_info['details']['weather']['humidity']['category']}
  降水：{weather_data.get('precipitation', '未知')}mm - {risk_info['details']['weather']['precipitation']['category']}
  天气：{weather_data.get('weather_condition', '未知')}
  天气风险评分：{risk_info['weather_risk']:.2f}

【生长阶段】
  当前阶段：{growth_stage}
  阶段易感性：{risk_info['details']['growth_stage']['susceptibility']:.2f}

【发病部位】
  受影响部位：{', '.join(disease_parts) if disease_parts else '未知'}
  部位权重：{risk_info['details']['disease_parts']['weight']:.2f}

【风险评估】
  综合风险评分：{risk_info['comprehensive_risk']:.2f}
  风险等级：{risk_info['risk_level']}

【季节性因素】
  当前季节：{season_info['name']}
  基础风险：{season_info['base_risk']:.2f}
  常见病害：{', '.join(season_info['common_diseases'])}

【建议】
"""
        # 根据风险等级生成建议
        if risk_info['comprehensive_risk'] >= 0.85:
            report += "  ⚠️ 极高风险！建议立即采取防治措施，加强监测频率。\n"
        elif risk_info['comprehensive_risk'] >= 0.7:
            report += "  ⚠️ 高风险！建议尽快进行病害防治，密切监测病情发展。\n"
        elif risk_info['comprehensive_risk'] >= 0.5:
            report += "  ⚠️ 中风险！建议加强田间管理，适时进行预防性喷药。\n"
        elif risk_info['comprehensive_risk'] >= 0.3:
            report += "  ✓ 中低风险！保持常规监测，注意天气变化。\n"
        else:
            report += "  ✓ 低风险！保持常规田间管理即可。\n"
        
        report += "========================\n"
        
        return report

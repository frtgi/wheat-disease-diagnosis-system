"""
多模态输入解析器模块

负责处理图像、文本和结构化数据的输入解析。
"""

import cv2
import numpy as np
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class InputParser:
    """多模态输入解析器类"""
    
    # 小麦生长阶段定义
    GROWTH_STAGES = [
        "苗期", "分蘖期", "越冬期", "返青期", "起身期",
        "拔节期", "孕穗期", "抽穗期", "开花期", "灌浆期", "成熟期"
    ]
    
    # 发病部位定义
    DISEASE_PARTS = [
        "叶片", "叶鞘", "茎秆", "穗部", "根部", "整株"
    ]
    
    # 常见病害症状关键词
    SYMPTOM_KEYWORDS = {
        "病斑": ["病斑", "斑点", "斑块", "褐斑", "黑斑", "白斑"],
        "霉层": ["霉层", "白粉", "黑霉", "灰霉", "霉状物"],
        "变色": ["变黄", "褪绿", "黄化", "发红", "发紫", "变色"],
        "萎蔫": ["萎蔫", "枯萎", "干枯", "死亡"],
        "畸形": ["畸形", "卷曲", "皱缩", "肿大", "肿瘤"],
        "锈粉": ["锈粉", "粉状", "孢子堆", "夏孢子"],
        "腐烂": ["腐烂", "软腐", "湿腐", "恶臭"]
    }
    
    def __init__(self, image_size: Tuple[int, int] = (224, 224)):
        """
        初始化输入解析器
        
        参数:
            image_size: 图像预处理后的目标尺寸 (宽，高)
        """
        self.image_size = image_size
    
    def parse_image(self, image_path: str, augment: bool = False) -> Dict[str, Any]:
        """
        解析和预处理图像输入
        
        参数:
            image_path: 图像文件路径
            augment: 是否进行数据增强
            
        返回:
            包含预处理后图像和元数据的字典
        """
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像：{image_path}")
        
        # 获取原始信息
        original_shape = image.shape
        height, width = original_shape[:2]
        
        # 图像预处理
        processed_image = self._preprocess_image(image, augment)
        
        # 生成元数据
        metadata = {
            "original_size": {"width": width, "height": height},
            "processed_size": {"width": self.image_size[0], "height": self.image_size[1]},
            "channels": 3,
            "file_path": image_path,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "image": processed_image,
            "metadata": metadata,
            "type": "image"
        }
    
    def _preprocess_image(self, image: np.ndarray, augment: bool = False) -> np.ndarray:
        """
        预处理图像：resize, normalize, augment
        
        参数:
            image: 输入图像 (BGR 格式)
            augment: 是否进行数据增强
            
        返回:
            预处理后的图像数组
        """
        # 1. Resize 到目标尺寸
        resized = cv2.resize(image, self.image_size, interpolation=cv2.INTER_LINEAR)
        
        # 2. 数据增强（可选）
        if augment:
            resized = self._augment_image(resized)
        
        # 3. 归一化到 [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # 4. 转换通道顺序 BGR -> RGB
        normalized = cv2.cvtColor(normalized, cv2.COLOR_BGR2RGB)
        
        return normalized
    
    def _augment_image(self, image: np.ndarray) -> np.ndarray:
        """
        对图像进行数据增强
        
        参数:
            image: 输入图像
            
        返回:
            增强后的图像
        """
        # 随机水平翻转
        if np.random.random() > 0.5:
            image = cv2.flip(image, 1)
        
        # 随机亮度调整
        brightness_factor = np.random.uniform(0.8, 1.2)
        image = cv2.convertScaleAbs(image, alpha=brightness_factor, beta=0)
        
        # 随机对比度调整
        contrast_factor = np.random.uniform(0.8, 1.2)
        image = cv2.convertScaleAbs(image, alpha=contrast_factor, beta=0)
        
        return image
    
    def parse_text(self, text: str) -> Dict[str, Any]:
        """
        解析文本症状描述，使用 NER 提取关键症状
        
        参数:
            text: 用户输入的文本描述
            
        返回:
            包含提取的症状信息的字典
        """
        # 提取症状关键词
        symptoms = self._extract_symptoms(text)
        
        # 提取发病部位
        disease_parts = self._extract_disease_parts(text)
        
        # 提取生长阶段
        growth_stage = self._extract_growth_stage(text)
        
        # 提取时间信息
        time_info = self._extract_time_info(text)
        
        # 提取严重程度
        severity = self._extract_severity(text)
        
        return {
            "symptoms": symptoms,
            "disease_parts": disease_parts,
            "growth_stage": growth_stage,
            "time_info": time_info,
            "severity": severity,
            "original_text": text,
            "type": "text"
        }
    
    def _extract_symptoms(self, text: str) -> List[Dict[str, str]]:
        """
        从文本中提取症状关键词
        
        参数:
            text: 输入文本
            
        返回:
            症状列表，每个症状包含类别和具体词汇
        """
        extracted = []
        text_lower = text.lower()
        
        for category, keywords in self.SYMPTOM_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    extracted.append({
                        "category": category,
                        "keyword": keyword,
                        "confidence": 0.9
                    })
        
        return extracted
    
    def _extract_disease_parts(self, text: str) -> List[str]:
        """
        从文本中提取发病部位
        
        参数:
            text: 输入文本
            
        返回:
            发病部位列表
        """
        parts = []
        for part in self.DISEASE_PARTS:
            if part in text:
                parts.append(part)
        return parts
    
    def _extract_growth_stage(self, text: str) -> Optional[str]:
        """
        从文本中提取生长阶段信息
        
        参数:
            text: 输入文本
            
        返回:
            生长阶段名称，如果未找到则返回 None
        """
        for stage in self.GROWTH_STAGES:
            if stage in text:
                return stage
        return None
    
    def _extract_time_info(self, text: str) -> Optional[str]:
        """
        从文本中提取时间信息
        
        参数:
            text: 输入文本
            
        返回:
            时间信息字符串
        """
        # 匹配日期格式
        date_patterns = [
            r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?',
            r'\d{1,2}月\d{1,2}[日号]',
            r'最近\s*\d+\s*天',
            r'\d+\s*天前'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return None
    
    def _extract_severity(self, text: str) -> str:
        """
        从文本中提取病害严重程度
        
        参数:
            text: 输入文本
            
        返回:
            严重程度等级 (轻微/中等/严重)
        """
        severe_keywords = ["严重", "很多", "大面积", "全部", "整片"]
        moderate_keywords = ["中等", "一些", "部分", "有点"]
        mild_keywords = ["轻微", "少量", "个别", "几株"]
        
        text_lower = text.lower()
        
        # 计算各等级得分
        severe_score = sum(1 for kw in severe_keywords if kw in text_lower)
        moderate_score = sum(1 for kw in moderate_keywords if kw in text_lower)
        mild_score = sum(1 for kw in mild_keywords if kw in text_lower)
        
        max_score = max(severe_score, moderate_score, mild_score)
        
        if max_score == 0:
            return "未知"
        elif severe_score == max_score:
            return "严重"
        elif moderate_score == max_score:
            return "中等"
        else:
            return "轻微"
    
    def parse_structured_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析和验证结构化数据
        
        参数:
            data: 输入的 JSON 格式数据
            
        返回:
            验证和标准化后的结构化数据
        """
        # 标准化字段名称
        standardized = self._standardize_fields(data)
        
        # 填充默认值
        standardized = self._fill_defaults(standardized)
        
        # 类型转换
        standardized = self._convert_types(standardized)
        
        return {
            "data": standardized,
            "type": "structured"
        }
    
    def _standardize_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化字段名称
        
        参数:
            data: 原始数据
            
        返回:
            字段名标准化后的数据
        """
        field_mapping = {
            "image": ["image", "img", "photo", "picture"],
            "text": ["text", "description", "desc", "symptom"],
            "location": ["location", "place", "address", "gps"],
            "time": ["time", "date", "timestamp", "datetime"],
            "weather": ["weather", "climate", "meteorology"],
            "growth_stage": ["growth_stage", "stage", "growth"],
            "disease_part": ["disease_part", "part", "affected_part"]
        }
        
        result = {}
        for standard_name, variants in field_mapping.items():
            for variant in variants:
                if variant in data:
                    result[standard_name] = data[variant]
                    break
        
        # 复制未映射的字段
        for key, value in data.items():
            if key not in result:
                result[key] = value
        
        return result
    
    def _fill_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        填充默认值
        
        参数:
            data: 输入数据
            
        返回:
            填充默认值后的数据
        """
        defaults = {
            "growth_stage": "未知",
            "disease_part": "未知",
            "severity": "未知",
            "location": "未知",
            "weather": {}
        }
        
        for key, default_value in defaults.items():
            if key not in data or data[key] is None:
                data[key] = default_value
        
        return data
    
    def _convert_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换数据类型
        
        参数:
            data: 输入数据
            
        返回:
            类型转换后的数据
        """
        # 确保数值类型为 float 或 int
        if "temperature" in data.get("weather", {}):
            try:
                data["weather"]["temperature"] = float(data["weather"]["temperature"])
            except (ValueError, TypeError):
                pass
        
        if "humidity" in data.get("weather", {}):
            try:
                data["weather"]["humidity"] = float(data["weather"]["humidity"])
            except (ValueError, TypeError):
                pass
        
        return data
    
    def parse_multimodal_input(
        self,
        image_path: Optional[str] = None,
        text: Optional[str] = None,
        structured_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        解析多模态输入（图像 + 文本 + 结构化数据）
        
        参数:
            image_path: 图像文件路径（可选）
            text: 文本描述（可选）
            structured_data: 结构化数据（可选）
            
        返回:
            整合后的多模态输入数据
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "components": []
        }
        
        # 解析图像
        if image_path:
            try:
                image_data = self.parse_image(image_path)
                result["image"] = image_data
                result["components"].append("image")
            except Exception as e:
                result["image_error"] = str(e)
        
        # 解析文本
        if text:
            text_data = self.parse_text(text)
            result["text"] = text_data
            result["components"].append("text")
        
        # 解析结构化数据
        if structured_data:
            struct_data = self.parse_structured_data(structured_data)
            result["structured"] = struct_data
            result["components"].append("structured")
        
        # 生成融合特征
        result["fused"] = self._fuse_modalities(result)
        
        return result
    
    def _fuse_modalities(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        融合多模态数据
        
        参数:
            data: 包含各模态数据的字典
            
        返回:
            融合后的特征数据
        """
        fused = {
            "has_image": "image" in data and data.get("image") is not None,
            "has_text": "text" in data and data.get("text") is not None,
            "has_structured": "structured" in data and data.get("structured") is not None,
            "symptoms": [],
            "disease_parts": [],
            "growth_stage": None,
            "severity": "未知",
            "environment": {}
        }
        
        # 从文本模态提取信息
        if "text" in data:
            text_data = data["text"]
            fused["symptoms"] = text_data.get("symptoms", [])
            fused["disease_parts"] = text_data.get("disease_parts", [])
            fused["growth_stage"] = text_data.get("growth_stage")
            fused["severity"] = text_data.get("severity", "未知")
        
        # 从结构化数据补充信息
        if "structured" in data:
            struct_data = data["structured"].get("data", {})
            if not fused["growth_stage"]:
                fused["growth_stage"] = struct_data.get("growth_stage")
            if not fused["disease_parts"]:
                fused["disease_parts"] = [struct_data.get("disease_part")] if struct_data.get("disease_part") else []
            fused["environment"] = struct_data.get("weather", {})
        
        return fused
    
    def generate_json_schema(self) -> Dict[str, Any]:
        """
        生成输入数据的 JSON Schema
        
        返回:
            JSON Schema 字典
        """
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "IWDDA 输入数据 Schema",
            "description": "小麦病害诊断代理的输入数据格式定义",
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "图像文件路径",
                    "format": "file-path"
                },
                "text": {
                    "type": "string",
                    "description": "症状文本描述",
                    "minLength": 1
                },
                "structured": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "地理位置"
                        },
                        "time": {
                            "type": "string",
                            "description": "时间信息"
                        },
                        "weather": {
                            "type": "object",
                            "properties": {
                                "temperature": {
                                    "type": "number",
                                    "description": "温度（摄氏度）"
                                },
                                "humidity": {
                                    "type": "number",
                                    "description": "湿度（百分比）",
                                    "minimum": 0,
                                    "maximum": 100
                                },
                                "precipitation": {
                                    "type": "number",
                                    "description": "降水量（毫米）",
                                    "minimum": 0
                                },
                                "weather_condition": {
                                    "type": "string",
                                    "description": "天气状况",
                                    "enum": ["晴", "多云", "阴", "小雨", "中雨", "大雨", "雪"]
                                }
                            }
                        },
                        "growth_stage": {
                            "type": "string",
                            "description": "小麦生长阶段",
                            "enum": self.GROWTH_STAGES
                        },
                        "disease_part": {
                            "type": "string",
                            "description": "发病部位",
                            "enum": self.DISEASE_PARTS
                        },
                        "severity": {
                            "type": "string",
                            "description": "病害严重程度",
                            "enum": ["轻微", "中等", "严重", "未知"]
                        }
                    }
                }
            },
            "required": []
        }
        
        return schema
    
    def validate_against_schema(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        根据 JSON Schema 验证数据
        
        参数:
            data: 待验证的数据
            
        返回:
            (是否有效，错误信息列表)
        """
        errors = []
        
        # 验证 image 字段
        if "image" in data:
            if not isinstance(data["image"], str):
                errors.append("image 字段必须是字符串类型")
        
        # 验证 text 字段
        if "text" in data:
            if not isinstance(data["text"], str):
                errors.append("text 字段必须是字符串类型")
            elif len(data["text"]) < 1:
                errors.append("text 字段不能为空")
        
        # 验证 structured 字段
        if "structured" in data:
            struct = data["structured"]
            if not isinstance(struct, dict):
                errors.append("structured 字段必须是对象类型")
            else:
                # 验证 weather 子字段
                if "weather" in struct:
                    weather = struct["weather"]
                    if not isinstance(weather, dict):
                        errors.append("weather 字段必须是对象类型")
                    else:
                        if "humidity" in weather:
                            if not isinstance(weather["humidity"], (int, float)):
                                errors.append("humidity 必须是数值类型")
                            elif not (0 <= weather["humidity"] <= 100):
                                errors.append("humidity 必须在 0-100 之间")
                        
                        if "temperature" in weather:
                            if not isinstance(weather["temperature"], (int, float)):
                                errors.append("temperature 必须是数值类型")
                
                # 验证 growth_stage
                if "growth_stage" in struct:
                    if struct["growth_stage"] not in self.GROWTH_STAGES:
                        errors.append(f"growth_stage 必须是以下值之一：{self.GROWTH_STAGES}")
                
                # 验证 disease_part
                if "disease_part" in struct:
                    if struct["disease_part"] not in self.DISEASE_PARTS:
                        errors.append(f"disease_part 必须是以下值之一：{self.DISEASE_PARTS}")
        
        is_valid = len(errors) == 0
        return is_valid, errors

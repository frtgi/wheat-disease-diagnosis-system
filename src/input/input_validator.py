"""
输入验证器模块

负责图像质量检查、数据完整性验证和异常处理。
"""

import cv2
import numpy as np
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class InputValidator:
    """输入验证器类"""
    
    # 图像质量阈值
    MIN_IMAGE_WIDTH = 100
    MIN_IMAGE_HEIGHT = 100
    MAX_IMAGE_SIZE_MB = 50
    MIN_BRIGHTNESS = 20
    MAX_BRIGHTNESS = 250
    MAX_BLURNESS = 500  # Laplacian 方差阈值
    
    # 必填字段定义
    REQUIRED_FIELDS = {
        "image": ["image_path"],
        "text": ["description"],
        "structured": ["location", "time"]
    }
    
    def __init__(self):
        """初始化输入验证器"""
        pass
    
    def validate_image(self, image_path: str) -> Dict[str, Any]:
        """
        验证图像质量
        
        参数:
            image_path: 图像文件路径
            
        返回:
            验证结果字典
        """
        result = {
            "valid": False,
            "path": image_path,
            "checks": {},
            "errors": [],
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 检查文件是否存在
        if not os.path.exists(image_path):
            result["errors"].append(f"文件不存在：{image_path}")
            return result
        
        # 检查文件扩展名
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in valid_extensions:
            result["warnings"].append(f"非标准图像格式：{ext}")
        
        # 尝试读取图像
        try:
            image = cv2.imread(image_path)
            if image is None:
                result["errors"].append("无法读取图像文件")
                return result
        except Exception as e:
            result["errors"].append(f"读取图像时出错：{str(e)}")
            return result
        
        # 执行各项检查
        result["checks"]["resolution"] = self._check_resolution(image)
        result["checks"]["brightness"] = self._check_brightness(image)
        result["checks"]["blur"] = self._check_blur(image)
        result["checks"]["file_size"] = self._check_file_size(image_path)
        result["checks"]["aspect_ratio"] = self._check_aspect_ratio(image)
        
        # 汇总检查结果
        all_passed = all(
            check.get("passed", False) 
            for check in result["checks"].values()
        )
        
        # 如果有错误则标记为无效
        if result["errors"]:
            result["valid"] = False
        elif all_passed:
            result["valid"] = True
        else:
            # 部分检查未通过但有警告
            result["valid"] = all(
                not check.get("critical", False) or check.get("passed", False)
                for check in result["checks"].values()
            )
        
        # 生成质量评分
        result["quality_score"] = self._calculate_quality_score(result["checks"])
        
        return result
    
    def _check_resolution(self, image: np.ndarray) -> Dict[str, Any]:
        """
        检查图像分辨率
        
        参数:
            image: 图像数组
            
        返回:
            检查结果
        """
        height, width = image.shape[:2]
        
        passed = (width >= self.MIN_IMAGE_WIDTH and height >= self.MIN_IMAGE_HEIGHT)
        
        return {
            "passed": passed,
            "critical": True,
            "value": {"width": width, "height": height},
            "threshold": {
                "min_width": self.MIN_IMAGE_WIDTH,
                "min_height": self.MIN_IMAGE_HEIGHT
            },
            "message": f"分辨率：{width}x{height}" if passed else f"分辨率过低：{width}x{height}"
        }
    
    def _check_brightness(self, image: np.ndarray) -> Dict[str, Any]:
        """
        检查图像亮度
        
        参数:
            image: 图像数组
            
        返回:
            检查结果
        """
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 计算平均亮度
        mean_brightness = np.mean(gray)
        
        passed = (self.MIN_BRIGHTNESS <= mean_brightness <= self.MAX_BRIGHTNESS)
        
        if mean_brightness < self.MIN_BRIGHTNESS:
            message = f"图像过暗：{mean_brightness:.1f}"
        elif mean_brightness > self.MAX_BRIGHTNESS:
            message = f"图像过曝：{mean_brightness:.1f}"
        else:
            message = f"亮度正常：{mean_brightness:.1f}"
        
        return {
            "passed": passed,
            "critical": False,
            "value": mean_brightness,
            "threshold": {
                "min": self.MIN_BRIGHTNESS,
                "max": self.MAX_BRIGHTNESS
            },
            "message": message
        }
    
    def _check_blur(self, image: np.ndarray) -> Dict[str, Any]:
        """
        检查图像模糊度（使用 Laplacian 方差）
        
        参数:
            image: 图像数组
            
        返回:
            检查结果
        """
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 计算 Laplacian 方差
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = np.var(laplacian)
        
        passed = variance > self.MAX_BLURNESS
        
        if passed:
            message = f"清晰度良好：{variance:.1f}"
        else:
            message = f"图像模糊：{variance:.1f}"
        
        return {
            "passed": passed,
            "critical": False,
            "value": variance,
            "threshold": {
                "min": self.MAX_BLURNESS
            },
            "message": message
        }
    
    def _check_file_size(self, file_path: str) -> Dict[str, Any]:
        """
        检查文件大小
        
        参数:
            file_path: 文件路径
            
        返回:
            检查结果
        """
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        passed = file_size_mb <= self.MAX_IMAGE_SIZE_MB
        
        return {
            "passed": passed,
            "critical": True,
            "value": file_size_mb,
            "threshold": {
                "max": self.MAX_IMAGE_SIZE_MB
            },
            "message": f"文件大小：{file_size_mb:.2f}MB" if passed else f"文件过大：{file_size_mb:.2f}MB"
        }
    
    def _check_aspect_ratio(self, image: np.ndarray) -> Dict[str, Any]:
        """
        检查图像宽高比
        
        参数:
            image: 图像数组
            
        返回:
            检查结果
        """
        height, width = image.shape[:2]
        aspect_ratio = width / height if height > 0 else 0
        
        # 常见的合理宽高比范围
        min_ratio = 0.5  # 2:1 (竖图)
        max_ratio = 2.0  # 1:2 (横图)
        
        passed = min_ratio <= aspect_ratio <= max_ratio
        
        if passed:
            message = f"宽高比正常：{aspect_ratio:.2f}"
        else:
            message = f"宽高比异常：{aspect_ratio:.2f}"
        
        return {
            "passed": passed,
            "critical": False,
            "value": aspect_ratio,
            "threshold": {
                "min": min_ratio,
                "max": max_ratio
            },
            "message": message
        }
    
    def _calculate_quality_score(self, checks: Dict[str, Any]) -> float:
        """
        计算图像质量综合评分
        
        参数:
            checks: 各项检查结果
            
        返回:
            质量评分 (0-100)
        """
        weights = {
            "resolution": 0.3,
            "brightness": 0.2,
            "blur": 0.3,
            "file_size": 0.1,
            "aspect_ratio": 0.1
        }
        
        total_score = 0.0
        
        for check_name, check_result in checks.items():
            weight = weights.get(check_name, 0.2)
            
            if check_result.get("passed", False):
                # 通过检查得满分
                score = 1.0
            else:
                # 未通过检查，根据偏离程度给分
                value = check_result.get("value", 0)
                threshold = check_result.get("threshold", {})
                
                if "min" in threshold and "max" in threshold:
                    # 有范围限制
                    min_val = threshold["min"]
                    max_val = threshold["max"]
                    mid_val = (min_val + max_val) / 2
                    
                    if value < min_val:
                        score = max(0, value / min_val)
                    elif value > max_val:
                        score = max(0, 1 - (value - max_val) / max_val)
                    else:
                        score = 1.0
                elif "min" in threshold:
                    # 只有下限
                    min_val = threshold["min"]
                    score = min(1.0, value / min_val) if min_val > 0 else 0
                elif "max" in threshold:
                    # 只有上限
                    max_val = threshold["max"]
                    score = max(0, 1 - value / max_val) if max_val > 0 else 0
                else:
                    score = 0
            
            total_score += weight * score
        
        return round(total_score * 100, 2)
    
    def validate_data_completeness(
        self,
        data: Dict[str, Any],
        required_fields: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        验证数据完整性
        
        参数:
            data: 待验证的数据字典
            required_fields: 必填字段定义，如果不提供则使用默认值
            
        返回:
            验证结果
        """
        if required_fields is None:
            required_fields = self.REQUIRED_FIELDS
        
        result = {
            "valid": True,
            "completeness_score": 0.0,
            "missing_fields": [],
            "present_fields": [],
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        total_fields = 0
        present_count = 0
        
        # 检查各类型必填字段
        for data_type, fields in required_fields.items():
            type_result = {
                "type": data_type,
                "required": fields,
                "missing": [],
                "present": []
            }
            
            for field in fields:
                total_fields += 1
                if field in data and data[field] is not None:
                    present_count += 1
                    type_result["present"].append(field)
                    result["present_fields"].append(f"{data_type}.{field}")
                else:
                    type_result["missing"].append(field)
                    result["missing_fields"].append(f"{data_type}.{field}")
            
            result["details"][data_type] = type_result
        
        # 计算完整性评分
        if total_fields > 0:
            result["completeness_score"] = round(present_count / total_fields * 100, 2)
        
        # 判断是否有效（至少有一个必填字段）
        result["valid"] = len(result["missing_fields"]) == 0
        
        return result
    
    def validate_input(
        self,
        image_path: Optional[str] = None,
        text: Optional[str] = None,
        structured_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        综合验证输入数据
        
        参数:
            image_path: 图像路径（可选）
            text: 文本描述（可选）
            structured_data: 结构化数据（可选）
            
        返回:
            综合验证结果
        """
        result = {
            "valid": False,
            "overall_score": 0.0,
            "components": {},
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "timestamp": datetime.now().isoformat()
        }
        
        scores = []
        weights = []
        
        # 验证图像
        if image_path:
            image_result = self.validate_image(image_path)
            result["components"]["image"] = image_result
            
            if not image_result["valid"]:
                result["errors"].extend(image_result["errors"])
            
            result["warnings"].extend(image_result["warnings"])
            
            if "quality_score" in image_result:
                scores.append(image_result["quality_score"])
                weights.append(0.5)
        
        # 验证文本
        if text:
            text_result = self.validate_text(text)
            result["components"]["text"] = text_result
            
            if not text_result["valid"]:
                result["errors"].extend(text_result["errors"])
            
            result["warnings"].extend(text_result["warnings"])
            
            if "quality_score" in text_result:
                scores.append(text_result["quality_score"])
                weights.append(0.3)
        
        # 验证结构化数据
        if structured_data:
            struct_result = self.validate_structured_data(structured_data)
            result["components"]["structured"] = struct_result
            
            if not struct_result["valid"]:
                result["errors"].extend(struct_result["errors"])
            
            result["warnings"].extend(struct_result["warnings"])
            
            if "completeness_score" in struct_result:
                scores.append(struct_result["completeness_score"])
                weights.append(0.2)
        
        # 计算总体评分
        if scores:
            total_weight = sum(weights)
            weighted_sum = sum(s * w for s, w in zip(scores, weights))
            result["overall_score"] = round(weighted_sum / total_weight, 2)
        
        # 判断整体有效性
        result["valid"] = len(result["errors"]) == 0
        
        # 生成建议
        result["suggestions"] = self._generate_suggestions(result)
        
        return result
    
    def validate_text(self, text: str) -> Dict[str, Any]:
        """
        验证文本输入
        
        参数:
            text: 文本内容
            
        返回:
            验证结果
        """
        result = {
            "valid": True,
            "quality_score": 0.0,
            "errors": [],
            "warnings": [],
            "checks": {}
        }
        
        # 检查长度
        if len(text) < 5:
            result["errors"].append("文本描述过短，至少需要 5 个字符")
            result["valid"] = False
        elif len(text) < 20:
            result["warnings"].append("文本描述较短，建议提供更多细节")
        
        # 检查是否包含关键词
        keywords = ["病", "斑", "黄", "枯", "霉", "虫", "害"]
        has_keyword = any(kw in text for kw in keywords)
        
        if not has_keyword:
            result["warnings"].append("文本中未检测到病害相关关键词")
        
        # 计算质量评分
        length_score = min(len(text) / 50, 1.0) * 50  # 长度占 50 分
        keyword_score = 50 if has_keyword else 0  # 关键词占 50 分
        
        result["quality_score"] = round(length_score + keyword_score, 2)
        
        return result
    
    def validate_structured_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证结构化数据
        
        参数:
            data: 结构化数据
            
        返回:
            验证结果
        """
        result = {
            "valid": True,
            "completeness_score": 0.0,
            "errors": [],
            "warnings": [],
            "field_validations": {}
        }
        
        # 验证 location 字段
        if "location" in data:
            location = data["location"]
            if not location or location == "未知":
                result["warnings"].append("位置信息缺失或不明确")
            else:
                result["field_validations"]["location"] = {"valid": True, "value": location}
        
        # 验证 time 字段
        if "time" in data:
            time_val = data["time"]
            if not time_val:
                result["warnings"].append("时间信息缺失")
            else:
                result["field_validations"]["time"] = {"valid": True, "value": time_val}
        
        # 验证 weather 字段
        if "weather" in data:
            weather = data["weather"]
            weather_valid = True
            
            if "temperature" in weather:
                temp = weather["temperature"]
                if not isinstance(temp, (int, float)) or temp < -40 or temp > 60:
                    result["errors"].append(f"温度值无效：{temp}")
                    weather_valid = False
            
            if "humidity" in weather:
                humidity = weather["humidity"]
                if not isinstance(humidity, (int, float)) or humidity < 0 or humidity > 100:
                    result["errors"].append(f"湿度值无效：{humidity}")
                    weather_valid = False
            
            result["field_validations"]["weather"] = {"valid": weather_valid, "value": weather}
        
        # 验证 growth_stage 字段
        if "growth_stage" in data:
            valid_stages = [
                "苗期", "分蘖期", "越冬期", "返青期", "起身期",
                "拔节期", "孕穗期", "抽穗期", "开花期", "灌浆期", "成熟期"
            ]
            stage = data["growth_stage"]
            if stage not in valid_stages:
                result["warnings"].append(f"生长阶段不在有效范围内：{stage}")
            else:
                result["field_validations"]["growth_stage"] = {"valid": True, "value": stage}
        
        # 计算完整性评分
        expected_fields = ["location", "time", "weather", "growth_stage", "disease_part"]
        present_fields = sum(1 for field in expected_fields if field in data)
        result["completeness_score"] = round(present_fields / len(expected_fields) * 100, 2)
        
        result["valid"] = len(result["errors"]) == 0
        
        return result
    
    def _generate_suggestions(self, validation_result: Dict[str, Any]) -> List[str]:
        """
        根据验证结果生成改进建议
        
        参数:
            validation_result: 验证结果
            
        返回:
            建议列表
        """
        suggestions = []
        
        # 检查图像相关建议
        if "image" in validation_result["components"]:
            image_result = validation_result["components"]["image"]
            
            if not image_result["checks"].get("resolution", {}).get("passed", False):
                suggestions.append("建议使用分辨率更高的图像（至少 100x100 像素）")
            
            if not image_result["checks"].get("brightness", {}).get("passed", False):
                brightness = image_result["checks"]["brightness"]["value"]
                if brightness < self.MIN_BRIGHTNESS:
                    suggestions.append("图像过暗，建议在光线充足的环境下重新拍摄")
                elif brightness > self.MAX_BRIGHTNESS:
                    suggestions.append("图像过曝，建议避免强光直射")
            
            if not image_result["checks"].get("blur", {}).get("passed", False):
                suggestions.append("图像模糊，建议对焦清晰后重新拍摄")
        
        # 检查文本相关建议
        if "text" in validation_result["components"]:
            text_result = validation_result["components"]["text"]
            
            if text_result["quality_score"] < 50:
                suggestions.append("建议提供更详细的症状描述，包括病斑形状、颜色等特征")
        
        # 检查结构化数据相关建议
        if "structured" in validation_result["components"]:
            struct_result = validation_result["components"]["structured"]
            
            if struct_result["completeness_score"] < 50:
                suggestions.append("建议补充位置、时间、天气等环境信息")
        
        # 总体建议
        if validation_result["overall_score"] < 60:
            suggestions.append("输入数据质量较低，可能影响诊断准确性，建议完善后再提交")
        elif validation_result["overall_score"] < 80:
            suggestions.append("输入数据质量一般，建议补充更多信息以提高诊断准确性")
        else:
            suggestions.append("输入数据质量良好，可以进行诊断")
        
        return suggestions
    
    def get_recovery_suggestions(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取错误恢复建议
        
        参数:
            validation_result: 验证结果
            
        返回:
            恢复建议字典
        """
        recovery = {
            "can_recover": True,
            "actions": [],
            "alternative_inputs": []
        }
        
        # 检查是否有致命错误
        has_critical_error = False
        
        # 检查是否包含 components 字段
        if "components" not in validation_result:
            return recovery
        
        for component_name, component_result in validation_result["components"].items():
            if component_name == "image":
                # 图像致命错误
                if "文件不存在" in str(component_result.get("errors", [])):
                    has_critical_error = True
                    recovery["actions"].append("请确认图像文件路径正确")
                elif "无法读取图像文件" in str(component_result.get("errors", [])):
                    has_critical_error = True
                    recovery["actions"].append("图像文件可能已损坏，请重新上传")
            
            # 提供替代输入建议
            if component_result.get("valid") is False:
                if component_name == "image":
                    recovery["alternative_inputs"].append("可以改用文本描述症状")
                elif component_name == "text":
                    recovery["alternative_inputs"].append("可以上传图像代替文本描述")
        
        recovery["can_recover"] = not has_critical_error
        
        return recovery

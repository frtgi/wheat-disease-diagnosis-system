# -*- coding: utf-8 -*-
"""
检测后分析模块

提供检测结果分析功能：
- 病斑面积计算
- 严重程度评估
- 病斑分布分析
- 检测结果统计
"""
import numpy as np
import cv2
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SeverityLevel(Enum):
    """严重程度级别"""
    HEALTHY = "健康"
    MILD = "轻度"
    MODERATE = "中度"
    SEVERE = "重度"
    CRITICAL = "严重"


@dataclass
class AnalysisResult:
    """分析结果"""
    total_detections: int = 0
    total_lesion_area: float = 0.0
    coverage_ratio: float = 0.0
    severity: str = "未知"
    disease_distribution: Dict[str, int] = None
    confidence_stats: Dict[str, float] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.disease_distribution is None:
            self.disease_distribution = {}
        if self.confidence_stats is None:
            self.confidence_stats = {}
        if self.recommendations is None:
            self.recommendations = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_detections": self.total_detections,
            "total_lesion_area": self.total_lesion_area,
            "coverage_ratio": self.coverage_ratio,
            "severity": self.severity,
            "disease_distribution": self.disease_distribution,
            "confidence_stats": self.confidence_stats,
            "recommendations": self.recommendations
        }


class LesionAnalyzer:
    """
    病斑分析器
    
    计算病斑面积和严重程度
    """
    
    SEVERITY_THRESHOLDS = {
        SeverityLevel.HEALTHY: 0.0,
        SeverityLevel.MILD: 0.05,
        SeverityLevel.MODERATE: 0.15,
        SeverityLevel.SEVERE: 0.30,
        SeverityLevel.CRITICAL: 0.50
    }
    
    DISEASE_PRIORITY = {
        "Yellow Rust": 3,
        "Brown Rust": 3,
        "Black Rust": 4,
        "Mildew": 2,
        "Fusarium Head Blight": 4,
        "Aphid": 2,
        "Mite": 2,
        "Healthy": 0
    }
    
    def __init__(self):
        """初始化病斑分析器"""
        pass
    
    def analyze(
        self,
        detections: List[Dict[str, Any]],
        image_shape: Tuple[int, int]
    ) -> AnalysisResult:
        """
        分析检测结果
        
        :param detections: 检测结果列表
        :param image_shape: 图像尺寸 (H, W)
        :return: 分析结果
        """
        if not detections:
            return AnalysisResult(
                total_detections=0,
                severity="健康",
                recommendations=["作物状态良好，继续保持监测"]
            )
        
        h, w = image_shape
        image_area = h * w
        
        total_lesion_area = 0.0
        disease_distribution = {}
        confidences = []
        
        for det in detections:
            bbox = det.get("bbox", [0, 0, 0, 0])
            name = det.get("name", "Unknown")
            conf = det.get("confidence", 0)
            
            if len(bbox) >= 4:
                box_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                total_lesion_area += box_area
            
            disease_distribution[name] = disease_distribution.get(name, 0) + 1
            confidences.append(conf)
        
        coverage_ratio = total_lesion_area / image_area if image_area > 0 else 0
        
        severity = self._determine_severity(coverage_ratio, detections)
        
        confidence_stats = {
            "mean": float(np.mean(confidences)) if confidences else 0,
            "min": float(np.min(confidences)) if confidences else 0,
            "max": float(np.max(confidences)) if confidences else 0,
            "std": float(np.std(confidences)) if confidences else 0
        }
        
        recommendations = self._generate_recommendations(
            severity, disease_distribution, coverage_ratio
        )
        
        return AnalysisResult(
            total_detections=len(detections),
            total_lesion_area=total_lesion_area,
            coverage_ratio=coverage_ratio,
            severity=severity,
            disease_distribution=disease_distribution,
            confidence_stats=confidence_stats,
            recommendations=recommendations
        )
    
    def _determine_severity(
        self,
        coverage_ratio: float,
        detections: List[Dict[str, Any]]
    ) -> str:
        """
        确定严重程度
        
        :param coverage_ratio: 覆盖率
        :param detections: 检测结果
        :return: 严重程度字符串
        """
        max_priority = 0
        for det in detections:
            name = det.get("name", "")
            priority = self.DISEASE_PRIORITY.get(name, 1)
            max_priority = max(max_priority, priority)
        
        if coverage_ratio < self.SEVERITY_THRESHOLDS[SeverityLevel.MILD]:
            if max_priority == 0:
                return "健康"
            return "轻度"
        elif coverage_ratio < self.SEVERITY_THRESHOLDS[SeverityLevel.MODERATE]:
            return "中度"
        elif coverage_ratio < self.SEVERITY_THRESHOLDS[SeverityLevel.SEVERE]:
            return "重度"
        else:
            return "严重"
    
    def _generate_recommendations(
        self,
        severity: str,
        disease_distribution: Dict[str, int],
        coverage_ratio: float
    ) -> List[str]:
        """
        生成防治建议
        
        :param severity: 严重程度
        :param disease_distribution: 病害分布
        :param coverage_ratio: 覆盖率
        :return: 建议列表
        """
        recommendations = []
        
        if severity == "健康":
            recommendations.append("作物状态良好，继续保持监测")
            return recommendations
        
        if severity == "轻度":
            recommendations.append("加强田间监测，关注病害发展")
            recommendations.append("清除病残体，改善通风条件")
        elif severity == "中度":
            recommendations.append("及时喷药防治，控制病害扩散")
            recommendations.append("建议使用三唑酮或戊唑醇进行防治")
        elif severity == "重度":
            recommendations.append("紧急防治，间隔7-10天再喷一次")
            recommendations.append("注意轮换用药，防止抗药性")
        else:
            recommendations.append("严重发生，建议咨询当地农技专家")
            recommendations.append("考虑使用高效药剂进行紧急防治")
        
        for disease in disease_distribution:
            if disease == "Yellow Rust":
                recommendations.append("条锈病：选用抗病品种，适时播种")
            elif disease == "Brown Rust":
                recommendations.append("叶锈病：清除病残体，合理施肥")
            elif disease == "Mildew":
                recommendations.append("白粉病：控制种植密度，改善通风")
            elif disease == "Fusarium Head Blight":
                recommendations.append("赤霉病：花期注意天气，及时防治")
            elif disease == "Aphid":
                recommendations.append("蚜虫：保护天敌，早期监测")
        
        return recommendations[:5]


class DetectionStatistics:
    """
    检测统计器
    
    统计检测结果
    """
    
    def __init__(self):
        """初始化统计器"""
        self.history = []
    
    def add_result(self, result: AnalysisResult):
        """
        添加分析结果
        
        :param result: 分析结果
        """
        self.history.append(result)
    
    def get_summary(self, n: int = 10) -> Dict[str, Any]:
        """
        获取统计摘要
        
        :param n: 最近N次结果
        :return: 统计摘要
        """
        recent = self.history[-n:]
        
        if not recent:
            return {"message": "暂无统计数据"}
        
        total_detections = sum(r.total_detections for r in recent)
        avg_coverage = np.mean([r.coverage_ratio for r in recent])
        
        all_diseases = {}
        for r in recent:
            for disease, count in r.disease_distribution.items():
                all_diseases[disease] = all_diseases.get(disease, 0) + count
        
        severity_counts = {}
        for r in recent:
            s = r.severity
            severity_counts[s] = severity_counts.get(s, 0) + 1
        
        return {
            "total_images": len(recent),
            "total_detections": total_detections,
            "average_coverage": float(avg_coverage),
            "disease_distribution": all_diseases,
            "severity_distribution": severity_counts
        }


class VisualizationGenerator:
    """
    可视化生成器
    
    生成分析可视化
    """
    
    def __init__(self):
        """初始化可视化生成器"""
        pass
    
    def generate_analysis_image(
        self,
        image: np.ndarray,
        detections: List[Dict[str, Any]],
        analysis: AnalysisResult
    ) -> np.ndarray:
        """
        生成分析可视化图像
        
        :param image: 原始图像
        :param detections: 检测结果
        :param analysis: 分析结果
        :return: 可视化图像
        """
        result = image.copy()
        
        for det in detections:
            bbox = det.get("bbox", [0, 0, 0, 0])
            name = det.get("name", "Unknown")
            conf = det.get("confidence", 0)
            
            if len(bbox) >= 4:
                x1, y1, x2, y2 = [int(x) for x in bbox]
                
                color = self._get_color(name)
                
                cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)
                
                label = f"{name} {conf:.0%}"
                cv2.putText(result, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        info_text = [
            f"检测数: {analysis.total_detections}",
            f"覆盖率: {analysis.coverage_ratio:.1%}",
            f"严重程度: {analysis.severity}"
        ]
        
        y_offset = 30
        for text in info_text:
            cv2.putText(result, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 25
        
        return result
    
    def _get_color(self, disease_name: str) -> Tuple[int, int, int]:
        """获取病害对应的颜色"""
        colors = {
            "Yellow Rust": (0, 255, 255),
            "Brown Rust": (0, 165, 255),
            "Black Rust": (0, 0, 139),
            "Mildew": (255, 255, 255),
            "Fusarium Head Blight": (203, 192, 255),
            "Aphid": (0, 255, 0),
            "Mite": (255, 0, 255),
            "Healthy": (0, 255, 0)
        }
        return colors.get(disease_name, (0, 255, 0))


def create_lesion_analyzer() -> LesionAnalyzer:
    """创建病斑分析器"""
    return LesionAnalyzer()


def create_detection_statistics() -> DetectionStatistics:
    """创建检测统计器"""
    return DetectionStatistics()

# -*- coding: utf-8 -*-
"""
特征可视化模块

提供特征可视化和诊断可视化功能：
- 特征图可视化
- 注意力权重可视化
- 检测结果可视化
- 置信度热力图
"""
import os
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


class FeatureVisualizer:
    """
    特征可视化器
    
    可视化卷积层特征和注意力权重
    """
    
    def __init__(self, output_dir: str = "outputs/visualizations"):
        """
        初始化可视化器
        
        :param output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def visualize_feature_maps(
        self,
        feature_maps: np.ndarray,
        layer_name: str = "layer",
        num_channels: int = 16,
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        可视化特征图
        
        :param feature_maps: 特征图 (C, H, W) 或 (N, C, H, W)
        :param layer_name: 层名称
        :param num_channels: 显示的通道数
        :param save_path: 保存路径
        :return: 可视化图像
        """
        if len(feature_maps.shape) == 4:
            feature_maps = feature_maps[0]
        
        C, H, W = feature_maps.shape
        num_channels = min(num_channels, C)
        
        # 创建网格
        cols = 4
        rows = (num_channels + cols - 1) // cols
        
        cell_size = 64
        grid_h = rows * cell_size
        grid_w = cols * cell_size
        
        grid = np.zeros((grid_h, grid_w), dtype=np.uint8)
        
        for i in range(num_channels):
            feat = feature_maps[i]
            
            # 归一化到0-255
            feat = (feat - feat.min()) / (feat.max() - feat.min() + 1e-8) * 255
            feat = feat.astype(np.uint8)
            
            # 调整大小
            feat_resized = cv2.resize(feat, (cell_size, cell_size))
            
            # 应用颜色映射
            feat_colored = cv2.applyColorMap(feat_resized, cv2.COLORMAP_JET)
            feat_gray = cv2.cvtColor(feat_colored, cv2.COLOR_BGR2GRAY)
            
            # 放置到网格
            row = i // cols
            col = i % cols
            y1 = row * cell_size
            x1 = col * cell_size
            grid[y1:y1+cell_size, x1:x1+cell_size] = feat_gray
        
        # 转换为彩色
        grid_colored = cv2.applyColorMap(grid, cv2.COLORMAP_JET)
        
        # 添加标题
        title = f"{layer_name} - {num_channels} channels"
        grid_with_title = self._add_title(grid_colored, title)
        
        if save_path:
            cv2.imwrite(save_path, grid_with_title)
        
        return grid_with_title
    
    def visualize_attention(
        self,
        attention_weights: np.ndarray,
        image: np.ndarray,
        layer_name: str = "attention",
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        可视化注意力权重
        
        :param attention_weights: 注意力权重 (H, W) 或 (N, H, W)
        :param image: 原始图像
        :param layer_name: 层名称
        :param save_path: 保存路径
        :return: 可视化图像
        """
        if len(attention_weights.shape) == 3:
            attention_weights = attention_weights[0]
        
        # 归一化
        attn = (attention_weights - attention_weights.min()) / \
               (attention_weights.max() - attention_weights.min() + 1e-8)
        
        # 调整大小
        h, w = image.shape[:2]
        attn_resized = cv2.resize(attn, (w, h))
        
        # 创建热力图
        heatmap = (attn_resized * 255).astype(np.uint8)
        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        # 叠加到原图
        overlay = cv2.addWeighted(image, 0.6, heatmap, 0.4, 0)
        
        # 添加标题
        title = f"{layer_name} Attention"
        result = self._add_title(overlay, title)
        
        if save_path:
            cv2.imwrite(save_path, result)
        
        return result
    
    def _add_title(self, image: np.ndarray, title: str) -> np.ndarray:
        """添加标题"""
        h, w = image.shape[:2]
        title_height = 30
        
        canvas = np.zeros((h + title_height, w, 3), dtype=np.uint8)
        canvas[title_height:] = image
        
        cv2.putText(
            canvas, title, (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1
        )
        
        return canvas


class DetectionVisualizer:
    """
    检测结果可视化器
    
    可视化检测结果、边界框和置信度
    """
    
    # 类别颜色映射
    DISEASE_COLORS = {
        "Yellow Rust": (0, 255, 255),      # 黄色
        "Brown Rust": (0, 165, 255),       # 橙色
        "Black Rust": (0, 0, 139),         # 深红
        "Mildew": (255, 255, 255),         # 白色
        "Fusarium Head Blight": (203, 192, 255),  # 粉色
        "Aphid": (0, 255, 0),              # 绿色
        "Mite": (255, 0, 255),             # 紫色
        "Healthy": (0, 255, 0),            # 绿色
        "default": (0, 255, 0)             # 默认绿色
    }
    
    def __init__(self, output_dir: str = "outputs/detections"):
        """
        初始化检测可视化器
        
        :param output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def visualize_detections(
        self,
        image: np.ndarray,
        detections: List[Dict[str, Any]],
        show_confidence: bool = True,
        show_bbox: bool = True,
        show_label: bool = True,
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        可视化检测结果
        
        :param image: 原始图像
        :param detections: 检测结果列表
        :param show_confidence: 是否显示置信度
        :param show_bbox: 是否显示边界框
        :param show_label: 是否显示标签
        :param save_path: 保存路径
        :return: 可视化图像
        """
        result = image.copy()
        
        for det in detections:
            name = det.get("name", "Unknown")
            confidence = det.get("confidence", 0)
            bbox = det.get("bbox", None)
            
            if bbox is None:
                continue
            
            x1, y1, x2, y2 = [int(x) for x in bbox]
            
            # 获取颜色
            color = self.DISEASE_COLORS.get(name, self.DISEASE_COLORS["default"])
            
            # 绘制边界框
            if show_bbox:
                cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签
            if show_label:
                label = name
                if show_confidence:
                    label += f" {confidence:.0%}"
                
                # 计算文本大小
                (text_w, text_h), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
                )
                
                # 绘制文本背景
                cv2.rectangle(
                    result,
                    (x1, y1 - text_h - 10),
                    (x1 + text_w + 10, y1),
                    color, -1
                )
                
                # 绘制文本
                cv2.putText(
                    result, label,
                    (x1 + 5, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1
                )
        
        if save_path:
            cv2.imwrite(save_path, result)
        
        return result
    
    def create_confidence_heatmap(
        self,
        image: np.ndarray,
        detections: List[Dict[str, Any]],
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        创建置信度热力图
        
        :param image: 原始图像
        :param detections: 检测结果列表
        :param save_path: 保存路径
        :return: 热力图
        """
        h, w = image.shape[:2]
        heatmap = np.zeros((h, w), dtype=np.float32)
        
        for det in detections:
            confidence = det.get("confidence", 0)
            bbox = det.get("bbox", None)
            
            if bbox is None:
                continue
            
            x1, y1, x2, y2 = [int(x) for x in bbox]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            # 在边界框区域填充置信度
            heatmap[y1:y2, x1:x2] = np.maximum(
                heatmap[y1:y2, x1:x2],
                confidence
            )
        
        # 转换为彩色热力图
        heatmap = (heatmap * 255).astype(np.uint8)
        heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        # 叠加到原图
        result = cv2.addWeighted(image, 0.5, heatmap_colored, 0.5, 0)
        
        if save_path:
            cv2.imwrite(save_path, result)
        
        return result
    
    def create_diagnosis_report_image(
        self,
        image: np.ndarray,
        detections: List[Dict[str, Any]],
        title: str = "诊断结果",
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        创建诊断报告图像
        
        :param image: 原始图像
        :param detections: 检测结果列表
        :param title: 标题
        :param save_path: 保存路径
        :return: 报告图像
        """
        # 可视化检测结果
        vis_image = self.visualize_detections(image, detections)
        
        # 创建报告区域
        h, w = vis_image.shape[:2]
        report_width = 300
        report_height = h
        
        # 创建画布
        canvas = np.ones((report_height, w + report_width, 3), dtype=np.uint8) * 255
        
        # 放置检测图像
        canvas[:h, :w] = vis_image
        
        # 添加报告文本
        x_text = w + 20
        y_text = 40
        
        cv2.putText(canvas, title, (x_text, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        y_text += 40
        cv2.putText(canvas, "-" * 20, (x_text, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)
        
        y_text += 30
        cv2.putText(canvas, f"检测数量: {len(detections)}", (x_text, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        for i, det in enumerate(detections[:5]):
            y_text += 30
            name = det.get("name", "Unknown")
            conf = det.get("confidence", 0)
            cv2.putText(canvas, f"{i+1}. {name}", (x_text, y_text),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            y_text += 20
            cv2.putText(canvas, f"   置信度: {conf:.1%}", (x_text, y_text),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        if save_path:
            cv2.imwrite(save_path, canvas)
        
        return canvas


def create_visualizer(output_dir: str = "outputs/visualizations") -> FeatureVisualizer:
    """创建特征可视化器"""
    return FeatureVisualizer(output_dir)


def create_detection_visualizer(output_dir: str = "outputs/detections") -> DetectionVisualizer:
    """创建检测可视化器"""
    return DetectionVisualizer(output_dir)

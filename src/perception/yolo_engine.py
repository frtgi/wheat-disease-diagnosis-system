# -*- coding: utf-8 -*-
"""
YOLOv8 引擎优化 (YOLOv8 Engine Optimization)

实现小麦病害检测的优化功能：
1. ROI 定位精度提升（注意力机制）
2. 病斑特征提取优化（多尺度特征）
3. 小目标检测优化（病斑早期检测）

技术特性:
- CBAM 注意力机制增强 ROI 定位
- FPN+PAN 多尺度特征融合
- 小目标检测层优化
- 病斑细粒度特征提取
"""
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Optional, Tuple, Any
from ultralytics import YOLO
import numpy as np
from PIL import Image


class CBAM(nn.Module):
    """
    CBAM 注意力模块 (Convolutional Block Attention Module)
    
    结合通道注意力和空间注意力，提升 ROI 定位精度
    用于增强病斑区域的特征响应，抑制背景干扰
    """
    
    def __init__(self, channels: int, reduction: int = 16):
        """
        初始化 CBAM 模块
        
        :param channels: 输入通道数
        :param reduction: 通道缩减比例
        """
        super().__init__()
        
        # 通道注意力
        self.channel_pool_avg = nn.AdaptiveAvgPool2d(1)
        self.channel_pool_max = nn.AdaptiveMaxPool2d(1)
        self.channel_fc = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels, bias=False)
        )
        self.channel_sigmoid = nn.Sigmoid()
        
        # 空间注意力
        self.spatial_conv = nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False)
        self.spatial_sigmoid = nn.Sigmoid()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        :param x: 输入特征 [batch, channels, height, width]
        :return: 加权后的特征
        """
        batch_size, channels, _, _ = x.shape
        
        # 通道注意力
        avg_out = self.channel_pool_avg(x).view(batch_size, channels)
        max_out = self.channel_pool_max(x).view(batch_size, channels)
        avg_out = self.channel_fc(avg_out).view(batch_size, channels, 1, 1)
        max_out = self.channel_fc(max_out).view(batch_size, channels, 1, 1)
        channel_weight = self.channel_sigmoid(avg_out + max_out)
        x_weighted = x * channel_weight
        
        # 空间注意力
        avg_out_spatial = torch.mean(x_weighted, dim=1, keepdim=True)
        max_out_spatial, _ = torch.max(x_weighted, dim=1, keepdim=True)
        spatial_input = torch.cat([avg_out_spatial, max_out_spatial], dim=1)
        spatial_weight = self.spatial_sigmoid(self.spatial_conv(spatial_input))
        output = x_weighted * spatial_weight
        
        return output


class MultiScaleFeatureExtractor(nn.Module):
    """
    多尺度特征提取器
    
    实现 FPN+PAN 结构的多尺度特征融合：
    - 捕获不同尺度的病斑特征
    - 增强小病斑的检测能力
    - 提升早期病害识别精度
    """
    
    def __init__(self, in_channels: List[int], out_channels: int = 256):
        """
        初始化多尺度特征提取器
        
        :param in_channels: 输入通道数列表（对应不同尺度）
        :param out_channels: 输出通道数
        """
        super().__init__()
        
        # 横向连接（1x1 卷积调整通道）
        self.lateral_convs = nn.ModuleList([
            nn.Conv2d(ch, out_channels, kernel_size=1)
            for ch in in_channels
        ])
        
        # 输出卷积
        self.output_conv = nn.Sequential(
            nn.Conv2d(out_channels * len(in_channels), out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
        
        # 上采样和下采样
        self.upsample = nn.Upsample(scale_factor=2, mode='nearest')
        self.downsample = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=2, padding=1)
    
    def forward(self, features: List[torch.Tensor]) -> torch.Tensor:
        """
        前向传播
        
        :param features: 多尺度特征列表（从浅层到深层）
        :return: 融合后的多尺度特征
        """
        # 横向连接调整通道
        lateral_features = []
        for i, feat in enumerate(features):
            lateral = self.lateral_convs[i](feat)
            lateral_features.append(lateral)
        
        # 自顶向下融合（FPN）
        fused_top_down = []
        for i in range(len(lateral_features) - 1, -1, -1):
            if i == len(lateral_features) - 1:
                fused_top_down.append(lateral_features[i])
            else:
                upsampled = self.upsample(fused_top_down[-1])
                merged = upsampled + lateral_features[i]
                fused_top_down.append(merged)
        
        # 反转顺序（从浅到深）
        fused_top_down.reverse()
        
        # 自底向上融合（PAN）
        fused_features = []
        for i, feat in enumerate(fused_top_down):
            if i == 0:
                fused_features.append(feat)
            else:
                downsampled = self.downsample(fused_features[-1])
                merged = downsampled + feat
                fused_features.append(merged)
        
        # 拼接所有尺度的特征
        concatenated = torch.cat(fused_features, dim=1)
        output = self.output_conv(concatenated)
        
        return output


class SmallObjectDetectionHead(nn.Module):
    """
    小目标检测头优化
    
    针对早期病斑小目标进行优化：
    - 增加小目标检测层
    - 提升浅层特征权重
    - 优化锚框尺寸
    """
    
    def __init__(self, in_channels: int, num_classes: int = 4, anchor_sizes: List[int] = None):
        """
        初始化小目标检测头
        
        :param in_channels: 输入通道数
        :param num_classes: 病害类别数
        :param anchor_sizes: 锚框尺寸列表
        """
        super().__init__()
        
        if anchor_sizes is None:
            anchor_sizes = [8, 16, 32]
        
        self.num_classes = num_classes
        self.anchor_sizes = anchor_sizes
        
        # 小目标检测层（针对浅层高分辨率特征）
        self.small_detect_conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels, in_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True)
        )
        
        # 分类头
        self.classifier = nn.Conv2d(in_channels, num_classes * len(anchor_sizes), kernel_size=1)
        
        # 回归头
        self.regressor = nn.Conv2d(in_channels, 4 * len(anchor_sizes), kernel_size=1)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        :param x: 输入特征 [batch, channels, height, width]
        :return: (分类预测，边界框回归)
        """
        features = self.small_detect_conv(x)
        
        cls_pred = self.classifier(features)
        reg_pred = self.regressor(features)
        
        return cls_pred, reg_pred


class YOLOEngine:
    """
    YOLOv8 引擎优化类
    
    实现小麦病害检测的完整优化方案：
    1. ROI 定位精度提升（CBAM 注意力）
    2. 病斑特征提取优化（多尺度特征）
    3. 小目标检测优化（早期病斑检测）
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        enable_attention: bool = True,
        enable_multi_scale: bool = True,
        enable_small_object: bool = True,
        device: Optional[str] = None
    ):
        """
        初始化 YOLOv8 引擎
        
        :param model_path: 模型路径
        :param enable_attention: 启用注意力机制
        :param enable_multi_scale: 启用多尺度特征
        :param enable_small_object: 启用小目标检测
        :param device: 计算设备
        """
        print("👁️ [YOLO Engine] 正在初始化优化引擎...")
        
        # 设备设置
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        print(f"   使用设备：{self.device}")
        
        # 加载基础 YOLOv8 模型
        self.model = self._load_model(model_path)
        
        # 优化模块
        self.enable_attention = enable_attention
        self.enable_multi_scale = enable_multi_scale
        self.enable_small_object = enable_small_object
        
        # 注意力模块
        self.attention_module = None
        if enable_attention:
            self.attention_module = CBAM(channels=512, reduction=16)
            self.attention_module.to(self.device)
            print("   ✅ CBAM 注意力模块已启用")
        
        # 多尺度特征提取器
        self.multi_scale_extractor = None
        if enable_multi_scale:
            self.multi_scale_extractor = MultiScaleFeatureExtractor(
                in_channels=[256, 512, 1024],
                out_channels=256
            )
            self.multi_scale_extractor.to(self.device)
            print("   ✅ 多尺度特征提取器已启用")
        
        # 小目标检测头
        self.small_object_head = None
        if enable_small_object:
            self.small_object_head = SmallObjectDetectionHead(
                in_channels=256,
                num_classes=4
            )
            self.small_object_head.to(self.device)
            print("   ✅ 小目标检测头已启用")
        
        # 统计信息
        self._stats = {
            'total_detections': 0,
            'small_object_detections': 0,
            'attention_enhanced_detections': 0
        }
        
        print("✅ [YOLO Engine] 优化引擎初始化完成\n")
    
    def _load_model(self, model_path: Optional[str]) -> YOLO:
        """
        加载 YOLOv8 模型
        
        :param model_path: 模型路径
        :return: YOLO 模型实例
        """
        if model_path and os.path.exists(model_path):
            print(f"   加载模型：{model_path}")
            return YOLO(model_path, task='detect')
        
        # 搜索候选模型路径
        candidates = [
            "D:/Project/WheatAgent/models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt",
            "D:/Project/WheatAgent/runs/detect/serpensgate_v2/weights/best.pt",
            "yolov8s.pt"
        ]
        
        for candidate in candidates:
            if os.path.exists(candidate):
                print(f"   找到模型：{candidate}")
                return YOLO(candidate, task='detect')
        
        print("   ⚠️ 未找到训练模型，使用 yolov8n.pt")
        return YOLO('yolov8n.pt')
    
    def extract_roi_features(
        self,
        image: Image.Image,
        detections: List[Dict[str, Any]],
        feature_scale: Tuple[int, int] = (64, 64)
    ) -> List[torch.Tensor]:
        """
        提取 ROI 区域特征（使用注意力机制）
        
        :param image: 输入图像
        :param detections: 检测结果列表
        :param feature_scale: 特征缩放尺寸
        :return: ROI 特征张量列表
        """
        if not self.enable_attention:
            return []
        
        image_tensor = self._image_to_tensor(image).to(self.device)
        roi_features = []
        
        for det in detections:
            bbox = det.get('bbox', [])
            if len(bbox) != 4:
                continue
            
            x1, y1, x2, y2 = map(int, bbox)
            roi = image_tensor[:, :, y1:y2, x1:x2]
            
            if roi.shape[2] < 4 or roi.shape[3] < 4:
                continue
            
            roi_resized = F.interpolate(roi, size=feature_scale, mode='bilinear', align_corners=False)
            
            with torch.no_grad():
                roi_enhanced = self.attention_module(roi_resized)
                roi_features.append(roi_enhanced)
            
            self._stats['attention_enhanced_detections'] += 1
        
        return roi_features
    
    def extract_multi_scale_features(
        self,
        image: Image.Image
    ) -> Optional[torch.Tensor]:
        """
        提取多尺度特征
        
        :param image: 输入图像
        :return: 融合后的多尺度特征
        """
        if not self.enable_multi_scale or self.multi_scale_extractor is None:
            return None
        
        image_tensor = self._image_to_tensor(image).to(self.device)
        
        with torch.no_grad():
            backbone_features = self._extract_backbone_features(image_tensor)
            
            if len(backbone_features) < 3:
                return None
            
            multi_scale_feat = self.multi_scale_extractor(backbone_features)
        
        return multi_scale_feat
    
    def detect_small_objects(
        self,
        image: Image.Image,
        conf_threshold: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        检测小目标病斑（早期病害）
        
        :param image: 输入图像
        :param conf_threshold: 置信度阈值
        :return: 小目标检测结果
        """
        if not self.enable_small_object or self.small_object_head is None:
            return []
        
        image_tensor = self._image_to_tensor(image).to(self.device)
        
        with torch.no_grad():
            backbone_features = self._extract_backbone_features(image_tensor)
            
            if len(backbone_features) == 0:
                return []
            
            shallow_feature = backbone_features[0]
            
            cls_pred, reg_pred = self.small_object_head(shallow_feature)
            
            small_detections = self._decode_detections(
                cls_pred, reg_pred, image.size, conf_threshold
            )
        
        self._stats['small_object_detections'] += len(small_detections)
        
        return small_detections
    
    def detect(
        self,
        image_path: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        use_enhanced: bool = True
    ) -> List[Dict[str, Any]]:
        """
        执行病害检测（增强模式）
        
        :param image_path: 图像路径
        :param conf_threshold: 置信度阈值
        :param iou_threshold: NMS IoU 阈值
        :param use_enhanced: 是否使用增强功能
        :return: 检测结果列表
        """
        if not os.path.exists(image_path):
            print(f"❌ 图像不存在：{image_path}")
            return []
        
        print(f"🔍 [YOLO Engine] 检测图像：{os.path.basename(image_path)}")
        
        image = Image.open(image_path).convert('RGB')
        
        results = self.model.predict(
            source=image,
            conf=conf_threshold,
            iou=iou_threshold,
            verbose=False
        )
        
        formatted_results = []
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for i, box in enumerate(boxes):
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].cpu().numpy()
                
                formatted_results.append({
                    'name': self.model.names.get(cls_id, f'类别{cls_id}'),
                    'confidence': conf,
                    'bbox': [float(x) for x in xyxy],
                    'class_id': cls_id
                })
        
        self._stats['total_detections'] += len(formatted_results)
        
        if use_enhanced and self.enable_small_object:
            small_dets = self.detect_small_objects(image, conf_threshold=0.15)
            formatted_results.extend(small_dets)
            print(f"   检测到 {len(small_dets)} 个小目标病斑")
        
        print(f"   共检测到 {len(formatted_results)} 个目标\n")
        
        return formatted_results
    
    def batch_detect(
        self,
        image_paths: List[str],
        conf_threshold: float = 0.25,
        batch_size: int = 4
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量检测
        
        :param image_paths: 图像路径列表
        :param conf_threshold: 置信度阈值
        :param batch_size: 批大小
        :return: {图像路径：检测结果} 字典
        """
        print(f"📦 [YOLO Engine] 批量检测 {len(image_paths)} 张图像")
        
        all_results = {}
        for i, image_path in enumerate(image_paths):
            results = self.detect(image_path, conf_threshold)
            all_results[image_path] = results
        
        print(f"✅ 批量检测完成\n")
        
        return all_results
    
    def get_enhanced_features(
        self,
        image_path: str
    ) -> Dict[str, Any]:
        """
        获取增强特征（用于融合）
        
        :param image_path: 图像路径
        :return: 特征字典
        """
        if not os.path.exists(image_path):
            return {}
        
        image = Image.open(image_path).convert('RGB')
        
        detections = self.detect(image_path, use_enhanced=True)
        
        features = {
            'detections': detections,
            'roi_features': [],
            'multi_scale_features': None,
            'small_object_features': None
        }
        
        if self.enable_attention and len(detections) > 0:
            roi_feats = self.extract_roi_features(image, detections)
            features['roi_features'] = roi_feats
        
        if self.enable_multi_scale:
            ms_feats = self.extract_multi_scale_features(image)
            features['multi_scale_features'] = ms_feats
        
        if self.enable_small_object:
            small_feats = self.detect_small_objects(image)
            features['small_object_features'] = small_feats
        
        return features
    
    def _image_to_tensor(self, image: Image.Image) -> torch.Tensor:
        """
        图像转张量
        
        :param image: PIL 图像
        :return: 张量 [1, 3, H, W]
        """
        transform = torch.transforms.Compose([
            torch.transforms.ToTensor(),
            torch.transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        tensor = transform(image).unsqueeze(0)
        return tensor
    
    def _extract_backbone_features(
        self,
        image_tensor: torch.Tensor
    ) -> List[torch.Tensor]:
        """
        提取骨干网络特征
        
        :param image_tensor: 图像张量
        :return: 特征列表
        """
        try:
            model = self.model.model
            
            x = image_tensor
            features = []
            
            for i, layer in enumerate(model.model[:10]):
                x = layer(x)
                if i in [3, 6, 9]:
                    features.append(x)
            
            return features
        except Exception as e:
            print(f"   ⚠️ 特征提取失败：{e}")
            return []
    
    def _decode_detections(
        self,
        cls_pred: torch.Tensor,
        reg_pred: torch.Tensor,
        image_size: Tuple[int, int],
        conf_threshold: float
    ) -> List[Dict[str, Any]]:
        """
        解码检测预测
        
        :param cls_pred: 分类预测
        :param reg_pred: 回归预测
        :param image_size: 图像尺寸
        :param conf_threshold: 置信度阈值
        :return: 检测结果
        """
        detections = []
        
        batch_size, _, height, width = cls_pred.shape
        
        cls_scores = cls_pred[0].permute(1, 2, 0).reshape(-1, self.small_object_head.num_classes)
        reg_boxes = reg_pred[0].permute(1, 2, 0).reshape(-1, 4)
        
        confidences, class_ids = torch.max(cls_scores, dim=1)
        
        for i in range(len(confidences)):
            conf = confidences[i].item()
            if conf < conf_threshold:
                continue
            
            cls_id = class_ids[i].item()
            box = reg_boxes[i].cpu().numpy()
            
            cx, cy, w, h = box
            x1 = max(0, (cx - w / 2) / width * image_size[0])
            y1 = max(0, (cy - h / 2) / height * image_size[1])
            x2 = min(image_size[0], (cx + w / 2) / width * image_size[0])
            y2 = min(image_size[1], (cy + h / 2) / height * image_size[1])
            
            detections.append({
                'name': f'病害类别{cls_id}',
                'confidence': conf,
                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                'class_id': cls_id,
                'is_small_object': True
            })
        
        return detections
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取统计信息
        
        :return: 统计字典
        """
        return self._stats.copy()
    
    def print_stats(self) -> None:
        """打印统计信息"""
        print("\n📊 [YOLO Engine] 统计信息")
        print("=" * 50)
        print(f"   总检测数：{self._stats['total_detections']}")
        print(f"   注意力增强检测：{self._stats['attention_enhanced_detections']}")
        print(f"   小目标检测：{self._stats['small_object_detections']}")
        print("=" * 50)

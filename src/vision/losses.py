# -*- coding: utf-8 -*-
"""
边界框回归损失函数模块

基于文档第3.4节：针对条锈病细长检测框的回归，采用CIoU损失函数
CIoU (Complete Intersection over Union) 相比IoU额外考虑了：
1. 检测框的中心点距离
2. 检测框的长宽比

作者: IWDDA团队
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Union


def bbox_iou(
    box1: torch.Tensor,
    box2: torch.Tensor,
    xywh: bool = True,
    GIoU: bool = False,
    DIoU: bool = False,
    CIoU: bool = False,
    eps: float = 1e-7
) -> torch.Tensor:
    """
    计算边界框的IoU及其变体（GIoU, DIoU, CIoU）
    
    Args:
        box1: 第一个边界框张量，形状为 (N, 4) 或 (4,)
        box2: 第二个边界框张量，形状为 (N, 4) 或 (4,)
        xywh: 输入格式是否为 (x, y, w, h)，False则为 (x1, y1, x2, y2)
        GIoU: 是否计算GIoU
        DIoU: 是否计算DIoU
        CIoU: 是否计算CIoU
        eps: 数值稳定性常数
    
    Returns:
        IoU值张量，形状为 (N,) 或标量
    
    参考文档3.4节：
    CIoU = IoU - (d²/c²) - αv
    其中：
    - d: 预测框和真实框中心点的欧氏距离
    - c: 覆盖两个框的最小闭包区域的对角线长度
    - v: 衡量长宽比的一致性
    - α: 权重参数
    """
    # 转换坐标格式
    if xywh:
        # 将 (x, y, w, h) 转换为 (x1, y1, x2, y2)
        x1y1x2y2_box1 = torch.zeros_like(box1)
        x1y1x2y2_box2 = torch.zeros_like(box2)
        
        # box1: (cx, cy, w, h) -> (x1, y1, x2, y2)
        x1y1x2y2_box1[..., 0] = box1[..., 0] - box1[..., 2] / 2  # x1
        x1y1x2y2_box1[..., 1] = box1[..., 1] - box1[..., 3] / 2  # y1
        x1y1x2y2_box1[..., 2] = box1[..., 0] + box1[..., 2] / 2  # x2
        x1y1x2y2_box1[..., 3] = box1[..., 1] + box1[..., 3] / 2  # y2
        
        # box2: (cx, cy, w, h) -> (x1, y1, x2, y2)
        x1y1x2y2_box2[..., 0] = box2[..., 0] - box2[..., 2] / 2
        x1y1x2y2_box2[..., 1] = box2[..., 1] - box2[..., 3] / 2
        x1y1x2y2_box2[..., 2] = box2[..., 0] + box2[..., 2] / 2
        x1y1x2y2_box2[..., 3] = box2[..., 1] + box2[..., 3] / 2
        
        box1 = x1y1x2y2_box1
        box2 = x1y1x2y2_box2
    
    # 计算交集
    inter_x1 = torch.max(box1[..., 0], box2[..., 0])
    inter_y1 = torch.max(box1[..., 1], box2[..., 1])
    inter_x2 = torch.min(box1[..., 2], box2[..., 2])
    inter_y2 = torch.min(box1[..., 3], box2[..., 3])
    
    inter_w = (inter_x2 - inter_x1).clamp(min=0)
    inter_h = (inter_y2 - inter_y1).clamp(min=0)
    inter_area = inter_w * inter_h
    
    # 计算各框面积
    area1 = (box1[..., 2] - box1[..., 0]) * (box1[..., 3] - box1[..., 1])
    area2 = (box2[..., 2] - box2[..., 0]) * (box2[..., 3] - box2[..., 1])
    
    # 计算并集
    union_area = area1 + area2 - inter_area + eps
    
    # 计算IoU
    iou = inter_area / union_area
    
    if GIoU or DIoU or CIoU:
        # 计算最小闭包区域
        closure_x1 = torch.min(box1[..., 0], box2[..., 0])
        closure_y1 = torch.min(box1[..., 1], box2[..., 1])
        closure_x2 = torch.max(box1[..., 2], box2[..., 2])
        closure_y2 = torch.max(box1[..., 3], box2[..., 3])
        
        closure_w = closure_x2 - closure_x1
        closure_h = closure_y2 - closure_y1
        
        if GIoU:
            # GIoU = IoU - (closure_area - union_area) / closure_area
            closure_area = closure_w * closure_h + eps
            giou = iou - (closure_area - union_area) / closure_area
            return giou
        
        if DIoU or CIoU:
            # 计算中心点距离
            # box1中心点
            cx1 = (box1[..., 0] + box1[..., 2]) / 2
            cy1 = (box1[..., 1] + box1[..., 3]) / 2
            # box2中心点
            cx2 = (box2[..., 0] + box2[..., 2]) / 2
            cy2 = (box2[..., 1] + box2[..., 3]) / 2
            
            # 中心点距离的平方
            center_dist_sq = (cx1 - cx2) ** 2 + (cy1 - cy2) ** 2
            
            # 闭包区域对角线长度的平方
            closure_diag_sq = closure_w ** 2 + closure_h ** 2 + eps
            
            if DIoU:
                # DIoU = IoU - d²/c²
                diou = iou - center_dist_sq / closure_diag_sq
                return diou
            
            if CIoU:
                # 计算长宽比一致性因子v
                # v = (4/π²) * (arctan(w_gt/h_gt) - arctan(w_pred/h_pred))²
                w1 = box1[..., 2] - box1[..., 0]  # 预测框宽度
                h1 = box1[..., 3] - box1[..., 1]  # 预测框高度
                w2 = box2[..., 2] - box2[..., 0]  # 真实框宽度
                h2 = box2[..., 3] - box2[..., 1]  # 真实框高度
                
                # 使用clamp避免除零
                h1_safe = h1.clamp(min=eps)
                h2_safe = h2.clamp(min=eps)
                
                v = (4 / (math.pi ** 2)) * torch.pow(
                    torch.atan(w2 / h2_safe) - torch.atan(w1 / h1_safe), 2
                )
                
                # 计算权重参数α
                # α = v / (1 - IoU + v + eps)
                alpha = v / (1 - iou + v + eps)
                
                # CIoU = IoU - d²/c² - αv
                ciou = iou - center_dist_sq / closure_diag_sq - alpha * v
                return ciou
    
    return iou


class CIoULoss(nn.Module):
    """
    CIoU损失函数
    
    针对条锈病细长检测框的回归优化
    
    参考文档3.4节：
    相比于IoU，CIoU额外考虑了检测框的中心点距离和长宽比，
    对于小麦条锈病等细长病斑的检测具有更好的定位精度。
    
    公式：
    L_CIoU = 1 - CIoU = 1 - IoU + d²/c² + αv
    
    优势：
    1. 直接优化IoU指标
    2. 考虑中心点对齐，加速收敛
    3. 考虑长宽比一致性，适合细长目标
    """
    
    def __init__(self, eps: float = 1e-7, reduction: str = 'mean'):
        """
        初始化CIoU损失函数
        
        Args:
            eps: 数值稳定性常数
            reduction: 损失聚合方式，可选 'none', 'mean', 'sum'
        """
        super().__init__()
        self.eps = eps
        self.reduction = reduction
    
    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        xywh: bool = True
    ) -> torch.Tensor:
        """
        计算CIoU损失
        
        Args:
            pred: 预测边界框，形状为 (N, 4)
            target: 目标边界框，形状为 (N, 4)
            xywh: 输入格式是否为 (x, y, w, h)
        
        Returns:
            CIoU损失值
        """
        ciou = bbox_iou(pred, target, xywh=xywh, CIoU=True, eps=self.eps)
        loss = 1.0 - ciou
        
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss


class DIoULoss(nn.Module):
    """
    DIoU损失函数
    
    Distance IoU Loss，考虑中心点距离但不考虑长宽比
    
    参考文档3.4节：
    DIoU是CIoU的简化版本，仅考虑中心点距离
    公式：L_DIoU = 1 - IoU + d²/c²
    """
    
    def __init__(self, eps: float = 1e-7, reduction: str = 'mean'):
        """
        初始化DIoU损失函数
        
        Args:
            eps: 数值稳定性常数
            reduction: 损失聚合方式
        """
        super().__init__()
        self.eps = eps
        self.reduction = reduction
    
    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        xywh: bool = True
    ) -> torch.Tensor:
        """
        计算DIoU损失
        
        Args:
            pred: 预测边界框
            target: 目标边界框
            xywh: 输入格式是否为 (x, y, w, h)
        
        Returns:
            DIoU损失值
        """
        diou = bbox_iou(pred, target, xywh=xywh, DIoU=True, eps=self.eps)
        loss = 1.0 - diou
        
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss


class GIoULoss(nn.Module):
    """
    GIoU损失函数
    
    Generalized IoU Loss，考虑闭包区域
    
    参考文档3.4节：
    GIoU解决了IoU在不重叠情况下梯度为0的问题
    公式：L_GIoU = 1 - GIoU = 1 - IoU + (closure_area - union_area) / closure_area
    """
    
    def __init__(self, eps: float = 1e-7, reduction: str = 'mean'):
        """
        初始化GIoU损失函数
        
        Args:
            eps: 数值稳定性常数
            reduction: 损失聚合方式
        """
        super().__init__()
        self.eps = eps
        self.reduction = reduction
    
    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        xywh: bool = True
    ) -> torch.Tensor:
        """
        计算GIoU损失
        
        Args:
            pred: 预测边界框
            target: 目标边界框
            xywh: 输入格式是否为 (x, y, w, h)
        
        Returns:
            GIoU损失值
        """
        giou = bbox_iou(pred, target, xywh=xywh, GIoU=True, eps=self.eps)
        loss = 1.0 - giou
        
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss


class IoULoss(nn.Module):
    """
    标准IoU损失函数
    
    公式：L_IoU = 1 - IoU
    """
    
    def __init__(self, eps: float = 1e-7, reduction: str = 'mean'):
        """
        初始化IoU损失函数
        
        Args:
            eps: 数值稳定性常数
            reduction: 损失聚合方式
        """
        super().__init__()
        self.eps = eps
        self.reduction = reduction
    
    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        xywh: bool = True
    ) -> torch.Tensor:
        """
        计算IoU损失
        
        Args:
            pred: 预测边界框
            target: 目标边界框
            xywh: 输入格式是否为 (x, y, w, h)
        
        Returns:
            IoU损失值
        """
        iou = bbox_iou(pred, target, xywh=xywh, eps=self.eps)
        loss = 1.0 - iou
        
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss


class FocalLoss(nn.Module):
    """
    Focal Loss损失函数
    
    用于解决类别不平衡问题
    
    公式：FL(p_t) = -α_t * (1 - p_t)^γ * log(p_t)
    
    参考文档3.4节：
    针对小麦病害检测中正负样本不平衡问题
    """
    
    def __init__(
        self,
        alpha: float = 0.25,
        gamma: float = 2.0,
        reduction: str = 'mean'
    ):
        """
        初始化Focal Loss
        
        Args:
            alpha: 平衡因子
            gamma: 聚焦参数
            reduction: 损失聚合方式
        """
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
    
    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """
        计算Focal Loss
        
        Args:
            pred: 预测概率，形状为 (N, C) 或 (N,)
            target: 目标标签，形状为 (N,)
        
        Returns:
            Focal Loss值
        """
        # 计算交叉熵
        ce_loss = F.cross_entropy(pred, target, reduction='none')
        
        # 计算预测概率
        pt = torch.exp(-ce_loss)
        
        # 计算Focal Loss
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss


class WheatDiseaseDetectionLoss(nn.Module):
    """
    小麦病害检测综合损失函数
    
    集成多种损失函数，针对小麦病害检测任务优化
    
    参考文档3.4节：
    总损失 = λ_box * L_CIoU + λ_cls * L_cls + λ_obj * L_obj
    
    其中：
    - L_CIoU: 边界框回归损失（CIoU）
    - L_cls: 分类损失（Focal Loss）
    - L_obj: 目标置信度损失（BCE Loss）
    """
    
    def __init__(
        self,
        num_classes: int = 16,
        box_weight: float = 7.5,
        cls_weight: float = 0.5,
        obj_weight: float = 1.0,
        focal_alpha: float = 0.25,
        focal_gamma: float = 2.0
    ):
        """
        初始化小麦病害检测损失函数
        
        Args:
            num_classes: 类别数量（小麦病害种类）
            box_weight: 边界框损失权重
            cls_weight: 分类损失权重
            obj_weight: 目标置信度损失权重
            focal_alpha: Focal Loss的alpha参数
            focal_gamma: Focal Loss的gamma参数
        """
        super().__init__()
        self.num_classes = num_classes
        self.box_weight = box_weight
        self.cls_weight = cls_weight
        self.obj_weight = obj_weight
        
        # 初始化各损失函数
        self.box_loss = CIoULoss(reduction='none')
        self.cls_loss = FocalLoss(alpha=focal_alpha, gamma=focal_gamma, reduction='none')
        self.obj_loss = nn.BCEWithLogitsLoss(reduction='none')
    
    def forward(
        self,
        pred_boxes: torch.Tensor,
        pred_scores: torch.Tensor,
        pred_cls: torch.Tensor,
        target_boxes: torch.Tensor,
        target_cls: torch.Tensor,
        target_obj: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        计算小麦病害检测综合损失
        
        Args:
            pred_boxes: 预测边界框，形状为 (N, 4)
            pred_scores: 预测目标置信度，形状为 (N, 1)
            pred_cls: 预测类别分数，形状为 (N, num_classes)
            target_boxes: 目标边界框，形状为 (N, 4)
            target_cls: 目标类别，形状为 (N,)
            target_obj: 目标置信度，形状为 (N, 1)
        
        Returns:
            total_loss: 总损失
            box_loss: 边界框损失
            cls_loss: 分类损失
            obj_loss: 目标置信度损失
        """
        # 计算边界框损失（CIoU）
        box_loss = self.box_loss(pred_boxes, target_boxes, xywh=True)
        box_loss = box_loss.mean() * self.box_weight
        
        # 计算分类损失（Focal Loss）
        cls_loss = self.cls_loss(pred_cls, target_cls)
        cls_loss = cls_loss.mean() * self.cls_weight
        
        # 计算目标置信度损失
        obj_loss = self.obj_loss(pred_scores.squeeze(-1), target_obj.squeeze(-1))
        obj_loss = obj_loss.mean() * self.obj_weight
        
        # 总损失
        total_loss = box_loss + cls_loss + obj_loss
        
        return total_loss, box_loss, cls_loss, obj_loss


class SIoULoss(nn.Module):
    """
    SIoU损失函数
    
    SIoU (SCYLLA-IoU) 进一步考虑了角度因素
    
    公式：SIoU = IoU - (d²/c²) - (θ/π) * αv
    
    参考文档3.4节扩展：
    SIoU在某些场景下比CIoU收敛更快
    """
    
    def __init__(self, eps: float = 1e-7, theta: float = 4.0, reduction: str = 'mean'):
        """
        初始化SIoU损失函数
        
        Args:
            eps: 数值稳定性常数
            theta: 角度惩罚系数
            reduction: 损失聚合方式
        """
        super().__init__()
        self.eps = eps
        self.theta = theta
        self.reduction = reduction
    
    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        xywh: bool = True
    ) -> torch.Tensor:
        """
        计算SIoU损失
        
        Args:
            pred: 预测边界框
            target: 目标边界框
            xywh: 输入格式是否为 (x, y, w, h)
        
        Returns:
            SIoU损失值
        """
        # 转换坐标格式
        if xywh:
            box1 = torch.zeros_like(pred)
            box2 = torch.zeros_like(target)
            
            box1[..., 0] = pred[..., 0] - pred[..., 2] / 2
            box1[..., 1] = pred[..., 1] - pred[..., 3] / 2
            box1[..., 2] = pred[..., 0] + pred[..., 2] / 2
            box1[..., 3] = pred[..., 1] + pred[..., 3] / 2
            
            box2[..., 0] = target[..., 0] - target[..., 2] / 2
            box2[..., 1] = target[..., 1] - target[..., 3] / 2
            box2[..., 2] = target[..., 0] + target[..., 2] / 2
            box2[..., 3] = target[..., 1] + target[..., 3] / 2
            
            pred = box1
            target = box2
        
        # 计算交集
        inter_x1 = torch.max(pred[..., 0], target[..., 0])
        inter_y1 = torch.max(pred[..., 1], target[..., 1])
        inter_x2 = torch.min(pred[..., 2], target[..., 2])
        inter_y2 = torch.min(pred[..., 3], target[..., 3])
        
        inter_w = (inter_x2 - inter_x1).clamp(min=0)
        inter_h = (inter_y2 - inter_y1).clamp(min=0)
        inter_area = inter_w * inter_h
        
        # 计算面积
        area1 = (pred[..., 2] - pred[..., 0]) * (pred[..., 3] - pred[..., 1])
        area2 = (target[..., 2] - target[..., 0]) * (target[..., 3] - target[..., 1])
        union_area = area1 + area2 - inter_area + self.eps
        
        # IoU
        iou = inter_area / union_area
        
        # 闭包区域
        closure_x1 = torch.min(pred[..., 0], target[..., 0])
        closure_y1 = torch.min(pred[..., 1], target[..., 1])
        closure_x2 = torch.max(pred[..., 2], target[..., 2])
        closure_y2 = torch.max(pred[..., 3], target[..., 3])
        
        closure_w = closure_x2 - closure_x1
        closure_h = closure_y2 - closure_y1
        
        # 中心点
        cx1 = (pred[..., 0] + pred[..., 2]) / 2
        cy1 = (pred[..., 1] + pred[..., 3]) / 2
        cx2 = (target[..., 0] + target[..., 2]) / 2
        cy2 = (target[..., 1] + target[..., 3]) / 2
        
        # 水平和垂直距离
        sigma_h = (cx1 - cx2) ** 2
        sigma_w = (cy1 - cy2) ** 2
        sigma = sigma_h + sigma_w + self.eps
        
        # 角度惩罚
        sin_alpha = torch.abs(sigma_h - sigma_w) / torch.sqrt(sigma + self.eps)
        sin_beta = torch.min(sigma_h, sigma_w) / torch.sqrt(sigma + self.eps)
        sin_alpha = torch.clamp(sin_alpha, 0, 1)
        threshold = pow(2, 0.5) / 2
        angle_cost = torch.where(
            sin_alpha > threshold,
            sin_alpha,
            sin_beta
        )
        
        # 距离惩罚
        gamma = 2.0 - angle_cost
        closure_diag_sq = closure_w ** 2 + closure_h ** 2 + self.eps
        rho = sigma / closure_diag_sq
        distance_cost = (1 - torch.exp(-gamma * rho)) * 0.5
        
        # 形状惩罚
        w1 = pred[..., 2] - pred[..., 0]
        h1 = pred[..., 3] - pred[..., 1]
        w2 = target[..., 2] - target[..., 0]
        h2 = target[..., 3] - target[..., 1]
        
        omega_w = torch.abs(w1 - w2) / torch.max(w1, w2).clamp(min=self.eps)
        omega_h = torch.abs(h1 - h2) / torch.max(h1, h2).clamp(min=self.eps)
        shape_cost = torch.pow(1 - torch.exp(-omega_w), self.theta) + \
                     torch.pow(1 - torch.exp(-omega_h), self.theta)
        
        # SIoU
        siou = iou - distance_cost - shape_cost * 0.5
        loss = 1.0 - siou
        
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss


def get_loss_function(loss_type: str = 'ciou', **kwargs) -> nn.Module:
    """
    获取损失函数的工厂方法
    
    Args:
        loss_type: 损失函数类型，可选 'iou', 'giou', 'diou', 'ciou', 'siou'
        **kwargs: 损失函数的额外参数
    
    Returns:
        对应的损失函数模块
    
    示例:
        >>> loss_fn = get_loss_function('ciou', eps=1e-6)
        >>> loss = loss_fn(pred_boxes, target_boxes)
    """
    loss_dict = {
        'iou': IoULoss,
        'giou': GIoULoss,
        'diou': DIoULoss,
        'ciou': CIoULoss,
        'siou': SIoULoss,
    }
    
    loss_type = loss_type.lower()
    if loss_type not in loss_dict:
        raise ValueError(f"不支持的损失函数类型: {loss_type}，可选: {list(loss_dict.keys())}")
    
    return loss_dict[loss_type](**kwargs)


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 测试损失函数模块")
    print("=" * 70)
    
    # 创建测试数据
    batch_size = 8
    pred_boxes = torch.rand(batch_size, 4) * 100
    pred_boxes[:, 2:] = pred_boxes[:, 2:].clamp(min=10)  # w, h > 10
    target_boxes = torch.rand(batch_size, 4) * 100
    target_boxes[:, 2:] = target_boxes[:, 2:].clamp(min=10)
    
    print("\n1. 测试各IoU变体损失函数:")
    
    # IoU Loss
    iou_loss = IoULoss()
    loss_iou = iou_loss(pred_boxes, target_boxes)
    print(f"   IoU Loss: {loss_iou.item():.4f}")
    
    # GIoU Loss
    giou_loss = GIoULoss()
    loss_giou = giou_loss(pred_boxes, target_boxes)
    print(f"   GIoU Loss: {loss_giou.item():.4f}")
    
    # DIoU Loss
    diou_loss = DIoULoss()
    loss_diou = diou_loss(pred_boxes, target_boxes)
    print(f"   DIoU Loss: {loss_diou.item():.4f}")
    
    # CIoU Loss (推荐用于小麦病害检测)
    ciou_loss = CIoULoss()
    loss_ciou = ciou_loss(pred_boxes, target_boxes)
    print(f"   CIoU Loss: {loss_ciou.item():.4f}")
    
    # SIoU Loss
    siou_loss = SIoULoss()
    loss_siou = siou_loss(pred_boxes, target_boxes)
    print(f"   SIoU Loss: {loss_siou.item():.4f}")
    
    print("\n2. 测试Focal Loss:")
    pred_cls = torch.randn(batch_size, 16)
    target_cls = torch.randint(0, 16, (batch_size,))
    focal_loss = FocalLoss()
    loss_focal = focal_loss(pred_cls, target_cls)
    print(f"   Focal Loss: {loss_focal.item():.4f}")
    
    print("\n3. 测试小麦病害检测综合损失:")
    pred_scores = torch.randn(batch_size, 1)
    target_obj = torch.rand(batch_size, 1)
    
    wheat_loss = WheatDiseaseDetectionLoss(num_classes=16)
    total_loss, box_l, cls_l, obj_l = wheat_loss(
        pred_boxes, pred_scores, pred_cls,
        target_boxes, target_cls, target_obj
    )
    print(f"   总损失: {total_loss.item():.4f}")
    print(f"   边界框损失: {box_l.item():.4f}")
    print(f"   分类损失: {cls_l.item():.4f}")
    print(f"   置信度损失: {obj_l.item():.4f}")
    
    print("\n4. 测试工厂方法:")
    loss_fn = get_loss_function('ciou')
    loss = loss_fn(pred_boxes, target_boxes)
    print(f"   工厂方法创建的CIoU Loss: {loss.item():.4f}")
    
    print("\n" + "=" * 70)
    print("✅ 所有损失函数测试通过！")
    print("=" * 70)

# -*- coding: utf-8 -*-
"""
不确定性量化损失函数模块 (Uncertainty Quantification Loss)

实现基于贝叶斯神经网络的不确定性量化：
1. 异方差不确定性损失 (Heteroscedastic Uncertainty Loss)
2. 认知不确定性估计 (Epistemic Uncertainty Estimation)
3. 蒙特卡洛 Dropout (Monte Carlo Dropout)
4. 置信度校准损失 (Confidence Calibration Loss)

技术特性:
- 模型输出置信度
- 环境数据与图像特征冲突时的低置信度预警
- 减少误报
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, Union
import math


class HeteroscedasticUncertaintyLoss(nn.Module):
    """
    异方差不确定性损失
    
    让模型同时预测均值和方差，实现数据依赖的不确定性估计
    """
    
    def __init__(
        self,
        num_classes: int = 15,
        reduction: str = 'mean'
    ):
        """
        初始化异方差不确定性损失
        
        :param num_classes: 类别数量
        :param reduction: 归约方式
        """
        super().__init__()
        
        self.num_classes = num_classes
        self.reduction = reduction
        
    def forward(
        self,
        logits: torch.Tensor,
        log_variance: torch.Tensor,
        targets: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        前向传播
        
        :param logits: 模型输出 logits [batch, num_classes]
        :param log_variance: 预测的对数方差 [batch, num_classes]
        :param targets: 目标标签 [batch]
        :return: 损失值和统计信息
        """
        # 计算异方差损失
        # L = 0.5 * exp(-log_var) * (target - pred)^2 + 0.5 * log_var
        
        # 获取目标类别的 logit
        target_logits = logits.gather(1, targets.unsqueeze(1)).squeeze(1)
        target_log_var = log_variance.gather(1, targets.unsqueeze(1)).squeeze(1)
        
        # 计算损失
        precision = torch.exp(-target_log_var)
        loss = 0.5 * precision * F.cross_entropy(logits, targets, reduction='none') + 0.5 * target_log_var
        
        if self.reduction == 'mean':
            loss = loss.mean()
        elif self.reduction == 'sum':
            loss = loss.sum()
        
        # 计算不确定性
        uncertainty = torch.exp(log_variance).mean().item()
        
        stats = {
            'loss': loss.item(),
            'uncertainty': uncertainty,
            'precision': precision.mean().item()
        }
        
        return loss, stats


class EpistemicUncertaintyEstimator(nn.Module):
    """
    认知不确定性估计器
    
    使用蒙特卡洛 Dropout 估计模型不确定性
    """
    
    def __init__(
        self,
        dropout_rate: float = 0.1,
        num_samples: int = 10
    ):
        """
        初始化认知不确定性估计器
        
        :param dropout_rate: Dropout 比率
        :param num_samples: 蒙特卡洛采样次数
        """
        super().__init__()
        
        self.dropout_rate = dropout_rate
        self.num_samples = num_samples
        self.dropout = nn.Dropout(dropout_rate)
        
    def forward(
        self,
        model: nn.Module,
        x: torch.Tensor,
        return_predictions: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        前向传播
        
        :param model: 模型
        :param x: 输入张量
        :param return_predictions: 是否返回所有预测
        :return: 不确定性估计结果
        """
        model.train()  # 启用 Dropout
        
        predictions = []
        
        for _ in range(self.num_samples):
            with torch.no_grad():
                pred = model(x)
                if isinstance(pred, tuple):
                    pred = pred[0]
                predictions.append(F.softmax(pred, dim=-1))
        
        # 堆叠预测
        predictions = torch.stack(predictions, dim=0)  # [num_samples, batch, num_classes]
        
        # 计算均值预测
        mean_prediction = predictions.mean(dim=0)
        
        # 计算预测方差（认知不确定性）
        predictive_variance = predictions.var(dim=0)
        epistemic_uncertainty = predictive_variance.mean(dim=-1)
        
        # 计算熵（总体不确定性）
        entropy = -torch.sum(mean_prediction * torch.log(mean_prediction + 1e-8), dim=-1)
        
        result = {
            'mean_prediction': mean_prediction,
            'epistemic_uncertainty': epistemic_uncertainty,
            'predictive_variance': predictive_variance,
            'entropy': entropy
        }
        
        if return_predictions:
            result['all_predictions'] = predictions
        
        model.eval()  # 恢复评估模式
        
        return result


class ConfidenceCalibrationLoss(nn.Module):
    """
    置信度校准损失
    
    确保模型输出的置信度与实际准确率一致
    """
    
    def __init__(
        self,
        temperature: float = 1.0,
        learn_temperature: bool = True
    ):
        """
        初始化置信度校准损失
        
        :param temperature: 温度参数
        :param learn_temperature: 是否学习温度参数
        """
        super().__init__()
        
        if learn_temperature:
            self.temperature = nn.Parameter(torch.tensor(temperature))
        else:
            self.register_buffer('temperature', torch.tensor(temperature))
        
    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        前向传播
        
        :param logits: 模型输出 logits [batch, num_classes]
        :param targets: 目标标签 [batch]
        :return: 校准损失和统计信息
        """
        # 温度缩放
        scaled_logits = logits / self.temperature
        
        # 计算交叉熵损失
        loss = F.cross_entropy(scaled_logits, targets)
        
        # 计算置信度
        probs = F.softmax(scaled_logits, dim=-1)
        confidence = probs.max(dim=-1)[0]
        
        # 计算准确率
        predictions = probs.argmax(dim=-1)
        accuracy = (predictions == targets).float().mean()
        
        # 计算 ECE (Expected Calibration Error)
        ece = self._compute_ece(confidence, predictions, targets)
        
        stats = {
            'loss': loss.item(),
            'confidence': confidence.mean().item(),
            'accuracy': accuracy.item(),
            'ece': ece,
            'temperature': self.temperature.item()
        }
        
        return loss, stats
    
    def _compute_ece(
        self,
        confidence: torch.Tensor,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        num_bins: int = 10
    ) -> float:
        """
        计算期望校准误差
        
        :param confidence: 置信度
        :param predictions: 预测标签
        :param targets: 目标标签
        :param num_bins: 分箱数量
        :return: ECE 值
        """
        bin_boundaries = torch.linspace(0, 1, num_bins + 1)
        ece = 0.0
        
        for i in range(num_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]
            
            # 找到在当前 bin 中的样本
            in_bin = (confidence > bin_lower) & (confidence <= bin_upper)
            prop_in_bin = in_bin.float().mean()
            
            if prop_in_bin > 0:
                # 计算该 bin 中的准确率
                accuracy_in_bin = (predictions[in_bin] == targets[in_bin]).float().mean()
                
                # 计算该 bin 中的平均置信度
                avg_confidence_in_bin = confidence[in_bin].mean()
                
                # 累加 ECE
                ece += torch.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
        
        return ece.item()


class EnvironmentConflictLoss(nn.Module):
    """
    环境冲突损失
    
    当环境数据与图像特征冲突时，降低模型置信度
    """
    
    def __init__(
        self,
        conflict_threshold: float = 0.3,
        uncertainty_weight: float = 0.5
    ):
        """
        初始化环境冲突损失
        
        :param conflict_threshold: 冲突阈值
        :param uncertainty_weight: 不确定性权重
        """
        super().__init__()
        
        self.conflict_threshold = conflict_threshold
        self.uncertainty_weight = uncertainty_weight
        
    def forward(
        self,
        vision_confidence: torch.Tensor,
        environment_confidence: torch.Tensor,
        vision_prediction: torch.Tensor,
        environment_prediction: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        前向传播
        
        :param vision_confidence: 视觉模型置信度 [batch]
        :param environment_confidence: 环境模型置信度 [batch]
        :param vision_prediction: 视觉模型预测 [batch]
        :param environment_prediction: 环境模型预测 [batch]
        :return: 冲突损失和统计信息
        """
        # 计算预测差异
        prediction_diff = (vision_prediction != environment_prediction).float()
        
        # 计算置信度差异
        confidence_diff = torch.abs(vision_confidence - environment_confidence)
        
        # 计算冲突程度
        conflict_score = prediction_diff * confidence_diff
        
        # 计算损失（当冲突时增加不确定性）
        loss = self.uncertainty_weight * conflict_score.mean()
        
        # 计算冲突率
        conflict_rate = prediction_diff.mean().item()
        
        stats = {
            'loss': loss.item(),
            'conflict_rate': conflict_rate,
            'avg_confidence_diff': confidence_diff.mean().item(),
            'conflict_score': conflict_score.mean().item()
        }
        
        return loss, stats


class UncertaintyQuantificationLoss(nn.Module):
    """
    综合不确定性量化损失
    
    整合多种不确定性损失：
    1. 异方差不确定性损失
    2. 置信度校准损失
    3. 环境冲突损失
    """
    
    def __init__(
        self,
        num_classes: int = 15,
        use_heteroscedastic: bool = True,
        use_calibration: bool = True,
        use_environment_conflict: bool = True,
        heteroscedastic_weight: float = 1.0,
        calibration_weight: float = 0.5,
        conflict_weight: float = 0.3
    ):
        """
        初始化综合不确定性量化损失
        
        :param num_classes: 类别数量
        :param use_heteroscedastic: 是否使用异方差损失
        :param use_calibration: 是否使用校准损失
        :param use_environment_conflict: 是否使用环境冲突损失
        :param heteroscedastic_weight: 异方差损失权重
        :param calibration_weight: 校准损失权重
        :param conflict_weight: 冲突损失权重
        """
        super().__init__()
        
        self.num_classes = num_classes
        self.use_heteroscedastic = use_heteroscedastic
        self.use_calibration = use_calibration
        self.use_environment_conflict = use_environment_conflict
        
        self.heteroscedastic_weight = heteroscedastic_weight
        self.calibration_weight = calibration_weight
        self.conflict_weight = conflict_weight
        
        # 初始化各损失模块
        if use_heteroscedastic:
            self.heteroscedastic_loss = HeteroscedasticUncertaintyLoss(num_classes)
        
        if use_calibration:
            self.calibration_loss = ConfidenceCalibrationLoss()
        
        if use_environment_conflict:
            self.conflict_loss = EnvironmentConflictLoss()
        
        # 基础分类损失
        self.ce_loss = nn.CrossEntropyLoss()
        
    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
        log_variance: Optional[torch.Tensor] = None,
        vision_confidence: Optional[torch.Tensor] = None,
        environment_confidence: Optional[torch.Tensor] = None,
        vision_prediction: Optional[torch.Tensor] = None,
        environment_prediction: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        前向传播
        
        :param logits: 模型输出 logits [batch, num_classes]
        :param targets: 目标标签 [batch]
        :param log_variance: 预测的对数方差（可选）
        :param vision_confidence: 视觉模型置信度（可选）
        :param environment_confidence: 环境模型置信度（可选）
        :param vision_prediction: 视觉模型预测（可选）
        :param environment_prediction: 环境模型预测（可选）
        :return: 总损失和统计信息
        """
        total_loss = 0.0
        stats = {}
        
        # 基础分类损失
        ce_loss = self.ce_loss(logits, targets)
        total_loss = total_loss + ce_loss
        stats['ce_loss'] = ce_loss.item()
        
        # 异方差不确定性损失
        if self.use_heteroscedastic and log_variance is not None:
            het_loss, het_stats = self.heteroscedastic_loss(logits, log_variance, targets)
            total_loss = total_loss + self.heteroscedastic_weight * het_loss
            stats['heteroscedastic_loss'] = het_loss.item()
            stats['uncertainty'] = het_stats['uncertainty']
        
        # 置信度校准损失
        if self.use_calibration:
            cal_loss, cal_stats = self.calibration_loss(logits, targets)
            total_loss = total_loss + self.calibration_weight * cal_loss
            stats['calibration_loss'] = cal_loss.item()
            stats['confidence'] = cal_stats['confidence']
            stats['ece'] = cal_stats['ece']
        
        # 环境冲突损失
        if (self.use_environment_conflict and 
            vision_confidence is not None and 
            environment_confidence is not None):
            conf_loss, conf_stats = self.conflict_loss(
                vision_confidence, environment_confidence,
                vision_prediction, environment_prediction
            )
            total_loss = total_loss + self.conflict_weight * conf_loss
            stats['conflict_loss'] = conf_loss.item()
            stats['conflict_rate'] = conf_stats['conflict_rate']
        
        stats['total_loss'] = total_loss.item()
        
        return total_loss, stats


class UncertaintyAwareDiagnosisHead(nn.Module):
    """
    不确定性感知诊断头
    
    同时输出诊断结果和不确定性估计
    """
    
    def __init__(
        self,
        input_dim: int,
        num_classes: int = 15,
        hidden_dim: int = 512,
        dropout: float = 0.1
    ):
        """
        初始化不确定性感知诊断头
        
        :param input_dim: 输入维度
        :param num_classes: 类别数量
        :param hidden_dim: 隐藏层维度
        :param dropout: Dropout 比率
        """
        super().__init__()
        
        self.num_classes = num_classes
        
        # 共享特征层
        self.shared_layer = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        
        # 分类头
        self.classifier = nn.Linear(hidden_dim, num_classes)
        
        # 不确定性头（预测对数方差）
        self.uncertainty_head = nn.Linear(hidden_dim, num_classes)
        
        # 初始化不确定性头为小值
        nn.init.constant_(self.uncertainty_head.bias, -2.0)  # 初始低不确定性
        nn.init.normal_(self.uncertainty_head.weight, std=0.01)
        
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        前向传播
        
        :param x: 输入特征 [batch, input_dim]
        :return: 包含 logits、不确定性等的字典
        """
        # 共享特征
        features = self.shared_layer(x)
        
        # 分类 logits
        logits = self.classifier(features)
        
        # 不确定性（对数方差）
        log_variance = self.uncertainty_head(features)
        
        # 计算概率和置信度
        probs = F.softmax(logits, dim=-1)
        confidence = probs.max(dim=-1)[0]
        
        # 计算预测不确定性
        uncertainty = torch.exp(log_variance).mean(dim=-1)
        
        return {
            'logits': logits,
            'log_variance': log_variance,
            'probs': probs,
            'confidence': confidence,
            'uncertainty': uncertainty,
            'features': features
        }


def create_uncertainty_loss(
    num_classes: int = 15,
    use_all_components: bool = True
) -> UncertaintyQuantificationLoss:
    """
    创建不确定性量化损失
    
    :param num_classes: 类别数量
    :param use_all_components: 是否使用所有组件
    :return: 不确定性量化损失实例
    """
    return UncertaintyQuantificationLoss(
        num_classes=num_classes,
        use_heteroscedastic=use_all_components,
        use_calibration=use_all_components,
        use_environment_conflict=use_all_components
    )


def test_uncertainty_loss():
    """测试不确定性量化损失模块"""
    print("\n" + "=" * 60)
    print("不确定性量化损失模块测试")
    print("=" * 60)
    
    try:
        print("\n[测试 1] 异方差不确定性损失")
        het_loss = HeteroscedasticUncertaintyLoss(num_classes=15)
        
        batch_size = 4
        logits = torch.randn(batch_size, 15)
        log_variance = torch.randn(batch_size, 15)
        targets = torch.randint(0, 15, (batch_size,))
        
        loss, stats = het_loss(logits, log_variance, targets)
        print(f"[OK] 异方差损失: {loss.item():.4f}")
        print(f"[OK] 不确定性: {stats['uncertainty']:.4f}")
        
        print("\n[测试 2] 置信度校准损失")
        cal_loss = ConfidenceCalibrationLoss(learn_temperature=True)
        
        loss, stats = cal_loss(logits, targets)
        print(f"[OK] 校准损失: {loss.item():.4f}")
        print(f"[OK] ECE: {stats['ece']:.4f}")
        print(f"[OK] 温度: {stats['temperature']:.4f}")
        
        print("\n[测试 3] 环境冲突损失")
        conflict_loss = EnvironmentConflictLoss()
        
        vision_conf = torch.tensor([0.9, 0.8, 0.7, 0.6])
        env_conf = torch.tensor([0.5, 0.8, 0.3, 0.9])
        vision_pred = torch.tensor([1, 2, 3, 4])
        env_pred = torch.tensor([1, 2, 1, 5])
        
        loss, stats = conflict_loss(vision_conf, env_conf, vision_pred, env_pred)
        print(f"[OK] 冲突损失: {loss.item():.4f}")
        print(f"[OK] 冲突率: {stats['conflict_rate']:.4f}")
        
        print("\n[测试 4] 综合不确定性量化损失")
        total_loss = create_uncertainty_loss(num_classes=15)
        
        loss, stats = total_loss(
            logits=logits,
            targets=targets,
            log_variance=log_variance,
            vision_confidence=vision_conf,
            environment_confidence=env_conf,
            vision_prediction=vision_pred,
            environment_prediction=env_pred
        )
        print(f"[OK] 总损失: {loss.item():.4f}")
        print(f"[OK] 统计信息: {stats}")
        
        print("\n[测试 5] 不确定性感知诊断头")
        diagnosis_head = UncertaintyAwareDiagnosisHead(input_dim=768, num_classes=15)
        
        features = torch.randn(batch_size, 768)
        result = diagnosis_head(features)
        
        print(f"[OK] Logits 维度: {result['logits'].shape}")
        print(f"[OK] 置信度: {result['confidence']}")
        print(f"[OK] 不确定性: {result['uncertainty']}")
        
        print("\n[OK] 所有测试通过!")
        
    except Exception as e:
        print(f"\n[错误] 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_uncertainty_loss()

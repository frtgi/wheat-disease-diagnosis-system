# -*- coding: utf-8 -*-
"""
双引擎融合模块 (Dual Engine Fusion)

实现 YOLOv8 和 Qwen3-VL 双引擎特征融合：
1. Early Fusion 策略（早期融合）
2. 联合特征输出（concat + attention）
3. Gating Mechanism（门控权重学习）

技术特性:
- 多模态早期特征融合
- 跨模态注意力机制
- 自适应权重学习
- 特征增强与选择
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Optional, Tuple, Any
import numpy as np

try:
    from PIL import Image
except ImportError:
    Image = None


class GatingMechanism(nn.Module):
    """
    门控机制模块
    
    学习 YOLOv8 和 Qwen3-VL 双引擎的融合权重：
    - 自适应权重分配
    - 动态特征选择
    - 多尺度门控
    """
    
    def __init__(
        self,
        yolo_dim: int = 512,
        qwen_dim: int = 512,
        hidden_dim: int = 256,
        num_gates: int = 3
    ):
        """
        初始化门控机制
        
        :param yolo_dim: YOLO 特征维度
        :param qwen_dim: Qwen 特征维度
        :param hidden_dim: 隐藏层维度
        :param num_gates: 门控数量
        """
        super().__init__()
        
        self.num_gates = num_gates
        
        # YOLO 特征门控
        self.yolo_gate = nn.Sequential(
            nn.Linear(yolo_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, num_gates),
            nn.Sigmoid()
        )
        
        # Qwen 特征门控
        self.qwen_gate = nn.Sequential(
            nn.Linear(qwen_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, num_gates),
            nn.Sigmoid()
        )
        
        # 跨模态注意力门控
        self.cross_gate = nn.Sequential(
            nn.Linear(yolo_dim + qwen_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, num_gates),
            nn.Sigmoid()
        )
    
    def forward(
        self,
        yolo_features: torch.Tensor,
        qwen_features: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        :param yolo_features: YOLO 特征 [batch, seq_len, yolo_dim]
        :param qwen_features: Qwen 特征 [batch, seq_len, qwen_dim]
        :return: (YOLO 门控权重，Qwen 门控权重，交叉门控权重)
        """
        yolo_pooled = yolo_features.mean(dim=1)
        qwen_pooled = qwen_features.mean(dim=1)
        
        yolo_weights = self.yolo_gate(yolo_pooled)
        qwen_weights = self.qwen_gate(qwen_pooled)
        
        combined = torch.cat([yolo_pooled, qwen_pooled], dim=-1)
        cross_weights = self.cross_gate(combined)
        
        return yolo_weights, qwen_weights, cross_weights


class EarlyFusionModule(nn.Module):
    """
    Early Fusion 模块
    
    在特征提取阶段进行深度融合：
    - 特征拼接
    - 跨模态注意力
    - 特征变换
    """
    
    def __init__(
        self,
        yolo_dim: int = 512,
        qwen_dim: int = 512,
        fusion_dim: int = 1024,
        num_heads: int = 8,
        num_layers: int = 2
    ):
        """
        初始化 Early Fusion 模块
        
        :param yolo_dim: YOLO 特征维度
        :param qwen_dim: Qwen 特征维度
        :param fusion_dim: 融合后维度
        :param num_heads: 注意力头数
        :param num_layers: Transformer 层数
        """
        super().__init__()
        
        # 特征投影
        self.yolo_proj = nn.Linear(yolo_dim, fusion_dim // 2)
        self.qwen_proj = nn.Linear(qwen_dim, fusion_dim // 2)
        
        # Transformer 编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=fusion_dim,
            nhead=num_heads,
            dim_feedforward=fusion_dim * 2,
            dropout=0.1,
            activation='gelu',
            batch_first=True,
            norm_first=True
        )
        
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )
        
        # 输出投影
        self.output_proj = nn.Sequential(
            nn.Linear(fusion_dim, fusion_dim),
            nn.LayerNorm(fusion_dim),
            nn.ReLU(inplace=True),
            nn.Linear(fusion_dim, fusion_dim)
        )
        
        # 位置编码
        self.position_encoding = nn.Parameter(
            torch.randn(1, 100, fusion_dim) * 0.02
        )
    
    def forward(
        self,
        yolo_features: torch.Tensor,
        qwen_features: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        前向传播
        
        :param yolo_features: YOLO 特征 [batch, seq_len, yolo_dim]
        :param qwen_features: Qwen 特征 [batch, seq_len, qwen_dim]
        :param attention_mask: 注意力掩码
        :return: 融合特征 [batch, seq_len, fusion_dim]
        """
        yolo_proj = self.yolo_proj(yolo_features)
        qwen_proj = self.qwen_proj(qwen_features)
        
        fused = torch.cat([yolo_proj, qwen_proj], dim=-1)
        
        seq_len = fused.shape[1]
        pos_enc = self.position_encoding[:, :seq_len, :]
        fused = fused + pos_enc
        
        if attention_mask is not None:
            fused = self.transformer(fused, src_key_padding_mask=attention_mask)
        else:
            fused = self.transformer(fused)
        
        output = self.output_proj(fused)
        
        return output


class CrossModalAttention(nn.Module):
    """
    跨模态注意力模块
    
    实现 YOLO 和 Qwen 特征之间的交互：
    - 双向注意力
    - 特征增强
    - 信息互补
    """
    
    def __init__(
        self,
        yolo_dim: int = 512,
        qwen_dim: int = 512,
        hidden_dim: int = 256,
        num_heads: int = 8
    ):
        """
        初始化跨模态注意力
        
        :param yolo_dim: YOLO 特征维度
        :param qwen_dim: Qwen 特征维度
        :param hidden_dim: 隐藏层维度
        :param num_heads: 注意力头数
        """
        super().__init__()
        
        # YOLO -> Qwen 注意力
        self.yolo_to_qwen = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            batch_first=True
        )
        
        # Qwen -> YOLO 注意力
        self.qwen_to_yolo = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            batch_first=True
        )
        
        # 特征投影
        self.yolo_proj = nn.Linear(yolo_dim, hidden_dim)
        self.qwen_proj = nn.Linear(qwen_dim, hidden_dim)
        
        # 输出投影
        self.yolo_out = nn.Linear(hidden_dim, yolo_dim)
        self.qwen_out = nn.Linear(hidden_dim, qwen_dim)
        
        # 层归一化
        self.norm_yolo = nn.LayerNorm(yolo_dim)
        self.norm_qwen = nn.LayerNorm(qwen_dim)
    
    def forward(
        self,
        yolo_features: torch.Tensor,
        qwen_features: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        :param yolo_features: YOLO 特征 [batch, seq_len, yolo_dim] 或 [batch, yolo_dim, H, W]
        :param qwen_features: Qwen 特征 [batch, seq_len, qwen_dim] 或 [batch, qwen_dim, H, W]
        :return: (增强后的 YOLO 特征，增强后的 Qwen 特征)
        """
        # 处理 4D 张量 (batch, dim, H, W) -> 3D (batch, seq_len, dim)
        yolo_3d = yolo_features
        qwen_3d = qwen_features
        
        if yolo_features.dim() == 4:
            b, c, h, w = yolo_features.shape
            yolo_3d = yolo_features.permute(0, 2, 3, 1).reshape(b, h * w, c)
        
        if qwen_features.dim() == 4:
            b, c, h, w = qwen_features.shape
            qwen_3d = qwen_features.permute(0, 2, 3, 1).reshape(b, h * w, c)
        
        # 层归一化
        yolo_norm = self.norm_yolo(yolo_3d)
        qwen_norm = self.norm_qwen(qwen_3d)
        
        # 特征投影
        yolo_proj = self.yolo_proj(yolo_norm)
        qwen_proj = self.qwen_proj(qwen_norm)
        
        # 跨模态注意力
        yolo_attended, _ = self.yolo_to_qwen(
            query=yolo_proj,
            key=qwen_proj,
            value=qwen_proj
        )
        
        qwen_attended, _ = self.qwen_to_yolo(
            query=qwen_proj,
            key=yolo_proj,
            value=yolo_proj
        )
        
        # 输出投影
        yolo_enhanced_3d = yolo_3d + self.yolo_out(yolo_attended)
        qwen_enhanced_3d = qwen_3d + self.qwen_out(qwen_attended)
        
        # 恢复原始维度
        if yolo_features.dim() == 4:
            b, c, h, w = yolo_features.shape
            yolo_enhanced = yolo_enhanced_3d.reshape(b, h, w, c).permute(0, 3, 1, 2)
        else:
            yolo_enhanced = yolo_enhanced_3d
        
        if qwen_features.dim() == 4:
            b, c, h, w = qwen_features.shape
            qwen_enhanced = qwen_enhanced_3d.reshape(b, h, w, c).permute(0, 3, 1, 2)
        else:
            qwen_enhanced = qwen_enhanced_3d
        
        return yolo_enhanced, qwen_enhanced


class DualEngineFusion:
    """
    双引擎融合类
    
    实现 YOLOv8 和 Qwen3-VL 的完整融合流程：
    1. Early Fusion 策略
    2. 联合特征输出
    3. Gating Mechanism 权重学习
    """
    
    def __init__(
        self,
        yolo_dim: int = 512,
        qwen_dim: int = 512,
        fusion_dim: int = 1024,
        enable_early_fusion: bool = True,
        enable_gating: bool = True,
        enable_cross_attention: bool = True,
        device: Optional[str] = None
    ):
        """
        初始化双引擎融合
        
        :param yolo_dim: YOLO 特征维度
        :param qwen_dim: Qwen 特征维度
        :param fusion_dim: 融合维度
        :param enable_early_fusion: 启用早期融合
        :param enable_gating: 启用门控机制
        :param enable_cross_attention: 启用跨模态注意力
        :param device: 计算设备
        """
        print("🔗 [Dual Fusion] 正在初始化双引擎融合模块...")
        
        # 设备设置
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        print(f"   使用设备：{self.device}")
        
        # 功能开关
        self.enable_early_fusion = enable_early_fusion
        self.enable_gating = enable_gating
        self.enable_cross_attention = enable_cross_attention
        
        # Early Fusion 模块
        self.early_fusion = None
        if enable_early_fusion:
            self.early_fusion = EarlyFusionModule(
                yolo_dim=yolo_dim,
                qwen_dim=qwen_dim,
                fusion_dim=fusion_dim
            )
            self.early_fusion.to(self.device)
            print("   ✅ Early Fusion 模块已启用")
        
        # Gating Mechanism
        self.gating = None
        if enable_gating:
            self.gating = GatingMechanism(
                yolo_dim=yolo_dim,
                qwen_dim=qwen_dim,
                hidden_dim=256
            )
            self.gating.to(self.device)
            print("   ✅ Gating Mechanism 已启用")
        
        # Cross-Modal Attention
        self.cross_attention = None
        if enable_cross_attention:
            self.cross_attention = CrossModalAttention(
                yolo_dim=yolo_dim,
                qwen_dim=qwen_dim,
                hidden_dim=256
            )
            self.cross_attention.to(self.device)
            print("   ✅ Cross-Modal Attention 已启用")
        
        # 特征对齐投影
        self.yolo_align = nn.Linear(512, yolo_dim).to(self.device)
        self.qwen_align = nn.Linear(512, qwen_dim).to(self.device)
        
        # 统计信息
        self._stats = {
            'total_fusions': 0,
            'early_fusion_count': 0,
            'gating_enhanced_count': 0
        }
        
        print("✅ [Dual Fusion] 双引擎融合初始化完成\n")
    
    def fuse_features(
        self,
        yolo_features: Dict[str, Any],
        qwen_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行特征融合
        
        :param yolo_features: YOLO 特征字典
        :param qwen_features: Qwen 特征字典
        :return: 融合后的特征
        """
        print("🔗 [Dual Fusion] 执行特征融合...")
        
        yolo_tensor = self._extract_yolo_tensor(yolo_features)
        qwen_tensor = self._extract_qwen_tensor(qwen_features)
        
        if yolo_tensor is None or qwen_tensor is None:
            print("   ⚠️ 特征提取失败，返回原始特征")
            return {
                'yolo_features': yolo_features,
                'qwen_features': qwen_features,
                'fused_features': None
            }
        
        yolo_tensor = yolo_tensor.to(self.device)
        qwen_tensor = qwen_tensor.to(self.device)
        
        yolo_enhanced = yolo_tensor
        qwen_enhanced = qwen_tensor
        
        if self.enable_cross_attention and self.cross_attention is not None:
            with torch.no_grad():
                yolo_enhanced, qwen_enhanced = self.cross_attention(
                    yolo_tensor, qwen_tensor
                )
        
        fused_tensor = None
        if self.enable_early_fusion and self.early_fusion is not None:
            with torch.no_grad():
                fused_tensor = self.early_fusion(yolo_enhanced, qwen_enhanced)
                self._stats['early_fusion_count'] += 1
        
        gating_weights = None
        if self.enable_gating and self.gating is not None:
            with torch.no_grad():
                gating_weights = self.gating(yolo_enhanced, qwen_enhanced)
                self._stats['gating_enhanced_count'] += 1
        
        self._stats['total_fusions'] += 1
        
        result = {
            'yolo_features': yolo_enhanced,
            'qwen_features': qwen_enhanced,
            'fused_features': fused_tensor,
            'gating_weights': gating_weights
        }
        
        print(f"   ✅ 融合完成，融合特征维度：{fused_tensor.shape if fused_tensor is not None else 'N/A'}\n")
        
        return result
    
    def diagnose_with_fusion(
        self,
        yolo_results: List[Dict[str, Any]],
        qwen_results: List[Dict[str, Any]],
        image: Optional[Image.Image] = None
    ) -> Dict[str, Any]:
        """
        基于融合特征的病害诊断
        
        :param yolo_results: YOLO 检测结果
        :param qwen_results: Qwen 候选结果
        :param image: 输入图像
        :return: 融合诊断结果
        """
        print("🔍 [Dual Fusion] 执行融合诊断...")
        
        combined_detections = []
        
        yolo_names = set()
        for yolo_det in yolo_results:
            disease_name = yolo_det.get('name', '未知')
            confidence = yolo_det.get('confidence', 0.0)
            yolo_names.add(disease_name)
            combined_detections.append({
                'source': 'YOLO',
                'name': disease_name,
                'confidence': confidence,
                'bbox': yolo_det.get('bbox', None)
            })
        
        for qwen_cand in qwen_results:
            disease_name = qwen_cand.get('name', '未知')
            confidence = qwen_cand.get('confidence', 0.0)
            alignment_score = qwen_cand.get('alignment_score', 0.0)
            
            if disease_name in yolo_names:
                for det in combined_detections:
                    if det['name'] == disease_name:
                        det['confidence'] = (det['confidence'] + confidence) / 2
                        det['alignment_score'] = alignment_score
            else:
                combined_detections.append({
                    'source': 'QwenVL',
                    'name': disease_name,
                    'confidence': confidence,
                    'alignment_score': alignment_score
                })
        
        combined_detections.sort(
            key=lambda x: x['confidence'] * (1 + x.get('alignment_score', 0)),
            reverse=True
        )
        
        primary_diagnosis = combined_detections[0] if combined_detections else None
        
        fusion_result = {
            'primary_diagnosis': primary_diagnosis['name'] if primary_diagnosis else '未知',
            'primary_confidence': primary_diagnosis['confidence'] if primary_diagnosis else 0.0,
            'all_detections': combined_detections,
            'yolo_count': len(yolo_results),
            'qwen_count': len(qwen_results),
            'fusion_improved': len(combined_detections) < len(yolo_results) + len(qwen_results)
        }
        
        self._stats['total_fusions'] += 1
        
        print(f"   ✅ 融合诊断完成：{fusion_result['primary_diagnosis']} "
              f"(置信度：{fusion_result['primary_confidence']:.2%})\n")
        
        return fusion_result
    
    def _extract_yolo_tensor(
        self,
        yolo_features: Dict[str, Any]
    ) -> Optional[torch.Tensor]:
        """
        提取 YOLO 张量特征
        
        :param yolo_features: YOLO 特征字典
        :return: YOLO 张量
        """
        if 'roi_features' in yolo_features and len(yolo_features['roi_features']) > 0:
            roi_feats = yolo_features['roi_features']
            if isinstance(roi_feats[0], torch.Tensor):
                return torch.cat(roi_feats, dim=0)
        
        if 'multi_scale_features' in yolo_features and yolo_features['multi_scale_features'] is not None:
            ms_feat = yolo_features['multi_scale_features']
            if isinstance(ms_feat, torch.Tensor):
                batch_size = ms_feat.shape[0]
                feat_proj = self.yolo_align(ms_feat.mean(dim=[2, 3]).view(batch_size, -1))
                return feat_proj.unsqueeze(1)
        
        detections = yolo_features.get('detections', [])
        if len(detections) > 0:
            det_tensor = torch.zeros(1, len(detections), 512)
            for i, det in enumerate(detections):
                conf = det.get('confidence', 0.5)
                bbox = det.get('bbox', [0, 0, 0, 0])
                feat_vec = torch.tensor([conf] + bbox + [0.0] * 506)
                det_tensor[0, i, :5] = feat_vec[:5]
            return det_tensor
        
        return torch.randn(1, 1, 512)
    
    def _extract_qwen_tensor(
        self,
        qwen_features: Dict[str, Any]
    ) -> Optional[torch.Tensor]:
        """
        提取 Qwen 张量特征
        
        :param qwen_features: Qwen 特征字典
        :return: Qwen 张量
        """
        if 'candidates' in qwen_features and len(qwen_features['candidates']) > 0:
            candidates = qwen_features['candidates']
            cand_tensor = torch.zeros(1, len(candidates), 512)
            for i, cand in enumerate(candidates):
                conf = cand.get('confidence', 0.5)
                align_score = cand.get('alignment_score', 0.0)
                feat_vec = torch.tensor([conf, align_score] + [0.0] * 510)
                cand_tensor[0, i, :2] = feat_vec[:2]
            return cand_tensor
        
        if 'visual_features' in qwen_features and qwen_features['visual_features'] is not None:
            vis_feat = qwen_features['visual_features']
            if isinstance(vis_feat, torch.Tensor):
                return self.qwen_align(vis_feat.mean(dim=1).unsqueeze(0))
        
        return torch.randn(1, 1, 512)
    
    def get_fusion_weights(
        self,
        yolo_features: torch.Tensor,
        qwen_features: torch.Tensor
    ) -> Dict[str, float]:
        """
        获取融合权重
        
        :param yolo_features: YOLO 特征
        :param qwen_features: Qwen 特征
        :return: 权重的字典
        """
        if self.gating is None:
            return {'yolo_weight': 0.5, 'qwen_weight': 0.5}
        
        with torch.no_grad():
            yolo_weights, qwen_weights, cross_weights = self.gating(
                yolo_features, qwen_features
            )
            
            yolo_avg = yolo_weights.mean().item()
            qwen_avg = qwen_weights.mean().item()
            cross_avg = cross_weights.mean().item()
        
        total = yolo_avg + qwen_avg
        if total > 0:
            yolo_ratio = yolo_avg / total
            qwen_ratio = qwen_avg / total
        else:
            yolo_ratio = 0.5
            qwen_ratio = 0.5
        
        return {
            'yolo_weight': yolo_ratio,
            'qwen_weight': qwen_ratio,
            'cross_attention_weight': cross_avg
        }
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取统计信息
        
        :return: 统计字典
        """
        return self._stats.copy()
    
    def print_stats(self) -> None:
        """打印统计信息"""
        print("\n📊 [Dual Fusion] 统计信息")
        print("=" * 50)
        print(f"   总融合数：{self._stats['total_fusions']}")
        print(f"   Early Fusion 次数：{self._stats['early_fusion_count']}")
        print(f"   Gating 增强次数：{self._stats['gating_enhanced_count']}")
        print("=" * 50)


def create_dual_fusion(
    yolo_dim: int = 512,
    qwen_dim: int = 512,
    fusion_dim: int = 1024,
    enable_all: bool = True,
    device: Optional[str] = None
) -> DualEngineFusion:
    """
    创建双引擎融合的工厂函数
    
    :param yolo_dim: YOLO 特征维度
    :param qwen_dim: Qwen 特征维度
    :param fusion_dim: 融合维度
    :param enable_all: 启用所有功能
    :param device: 计算设备
    :return: DualEngineFusion 实例
    """
    return DualEngineFusion(
        yolo_dim=yolo_dim,
        qwen_dim=qwen_dim,
        fusion_dim=fusion_dim,
        enable_early_fusion=enable_all,
        enable_gating=enable_all,
        enable_cross_attention=enable_all,
        device=device
    )


def test_dual_fusion():
    """测试双引擎融合"""
    print("\n" + "=" * 60)
    print("双引擎融合测试")
    print("=" * 60)
    
    try:
        print("\n[测试 1] 初始化融合模块")
        fusion = create_dual_fusion(enable_all=True)
        print("[OK] 融合模块初始化成功")
        
        print("\n[测试 2] 特征融合测试")
        yolo_feat = {
            'detections': [
                {'name': '条锈病', 'confidence': 0.85, 'bbox': [100, 100, 200, 200]}
            ],
            'roi_features': [torch.randn(1, 512, 64, 64)],
            'multi_scale_features': torch.randn(1, 256, 32, 32)
        }
        
        qwen_feat = {
            'candidates': [
                {'name': '条锈病', 'confidence': 0.78, 'alignment_score': 0.65}
            ]
        }
        
        result = fusion.fuse_features(yolo_feat, qwen_feat)
        print(f"[OK] 特征融合成功")
        print(f"   融合特征维度：{result['fused_features'].shape if result['fused_features'] is not None else 'N/A'}")
        
        print("\n[测试 3] 融合诊断测试")
        yolo_results = [
            {'name': '条锈病', 'confidence': 0.85, 'bbox': [100, 100, 200, 200]}
        ]
        qwen_results = [
            {'name': '条锈病', 'confidence': 0.78, 'alignment_score': 0.65},
            {'name': '叶锈病', 'confidence': 0.45, 'alignment_score': 0.32}
        ]
        
        diagnosis = fusion.diagnose_with_fusion(yolo_results, qwen_results)
        print(f"[OK] 融合诊断成功")
        print(f"   主要诊断：{diagnosis['primary_diagnosis']}")
        print(f"   置信度：{diagnosis['primary_confidence']:.2%}")
        
        print("\n[OK] 所有测试通过!")
        
    except Exception as e:
        print(f"\n[错误] 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_dual_fusion()

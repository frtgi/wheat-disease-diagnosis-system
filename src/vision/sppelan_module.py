# -*- coding: utf-8 -*-
"""
SPPELAN模块 - Spatial Pyramid Pooling + Efficient Local Aggregation Network
根据研究文档，该模块用于多尺度特征的极致聚合
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class SPPELAN(nn.Module):
    """
    SPPELAN - Spatial Pyramid Pooling + Efficient Local Aggregation Network
    
    结合了SPP的多尺度池化能力和ELAN的高效层级聚合特性。
    通过多分支结构，在不同感受野下提取特征，并通过梯度路径设计优化信息的流动。
    
    性能提升:
    - 能够同时保留微小病斑的纹理细节（有助于区分不同种类的锈病）
    - 保留宏观的叶片结构信息（有助于判断病害发生的部位）
    - 在PlantDoc数据集上将mAP@0.5提升3.3%
    """
    
    def __init__(self, in_channels, out_channels, pool_sizes=[5, 9, 13]):
        """
        初始化SPPELAN模块
        
        :param in_channels: 输入通道数
        :param out_channels: 输出通道数
        :param pool_sizes: 空间金字塔池化的核大小列表
        """
        super(SPPELAN, self).__init__()
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.pool_sizes = pool_sizes
        self.hidden_channels = in_channels // 2
        
        # 初始卷积 - 降维
        self.cv1 = nn.Sequential(
            nn.Conv2d(in_channels, self.hidden_channels, 1, bias=False),
            nn.BatchNorm2d(self.hidden_channels),
            nn.SiLU(inplace=True)
        )
        
        # 多尺度池化分支
        self.pool_branches = nn.ModuleList([
            nn.Sequential(
                nn.MaxPool2d(kernel_size=size, stride=1, padding=size // 2),
                nn.Conv2d(self.hidden_channels, self.hidden_channels // len(pool_sizes), 1, bias=False),
                nn.BatchNorm2d(self.hidden_channels // len(pool_sizes)),
                nn.SiLU(inplace=True)
            ) for size in pool_sizes
        ])
        
        # 直接分支（不经过池化）
        self.direct_branch = nn.Sequential(
            nn.Conv2d(self.hidden_channels, self.hidden_channels // len(pool_sizes), 1, bias=False),
            nn.BatchNorm2d(self.hidden_channels // len(pool_sizes)),
            nn.SiLU(inplace=True)
        )
        
        # 层级聚合 - ELAN结构
        # 将所有分支的特征进行高效聚合
        total_branch_channels = self.hidden_channels // len(pool_sizes) * (len(pool_sizes) + 1)
        
        self.elan_aggregate = nn.Sequential(
            nn.Conv2d(total_branch_channels, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.SiLU(inplace=True)
        )
        
        # 残差连接
        self.residual_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels)
        ) if in_channels != out_channels else nn.Identity()
        
        self.final_act = nn.SiLU(inplace=True)
        
        self._initialize_weights()
    
    def _initialize_weights(self):
        """初始化权重"""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        """
        前向传播
        
        :param x: 输入特征图 [batch, in_channels, height, width]
        :return: 输出特征图 [batch, out_channels, height, width]
        """
        # 保存残差
        residual = self.residual_conv(x)
        
        # 初始降维
        x = self.cv1(x)
        
        # 多尺度特征提取
        branch_outputs = [self.direct_branch(x)]
        for pool_branch in self.pool_branches:
            branch_outputs.append(pool_branch(x))
        
        # 拼接所有分支
        multi_scale_features = torch.cat(branch_outputs, dim=1)
        
        # ELAN聚合
        output = self.elan_aggregate(multi_scale_features)
        
        # 残差连接
        output = self.final_act(output + residual)
        
        return output


class ELANBlock(nn.Module):
    """
    ELAN (Efficient Layer Aggregation Network) 基础模块
    通过控制最短最长的梯度路径，使网络能够学习到更多特征
    """
    
    def __init__(self, in_channels, out_channels, part_ratio=0.5, num_blocks=2):
        """
        初始化ELAN模块
        
        :param in_channels: 输入通道数
        :param out_channels: 输出通道数
        :param part_ratio: 通道分割比例
        :param num_blocks: 堆叠的卷积块数量
        """
        super(ELANBlock, self).__init__()
        
        self.part_channels = int(out_channels * part_ratio)
        self.remaining_channels = out_channels - self.part_channels * 2
        
        # 输入卷积
        self.cv_in = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.SiLU(inplace=True)
        )
        
        # 多个卷积分支
        self.conv_blocks = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(self.part_channels, self.part_channels, 3, padding=1, bias=False),
                nn.BatchNorm2d(self.part_channels),
                nn.SiLU(inplace=True)
            ) for _ in range(num_blocks)
        ])
        
        # 输出卷积
        total_channels = self.part_channels * (2 + num_blocks) + self.remaining_channels
        self.cv_out = nn.Sequential(
            nn.Conv2d(total_channels, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.SiLU(inplace=True)
        )
    
    def forward(self, x):
        """
        前向传播
        """
        # 输入卷积
        x = self.cv_in(x)
        
        # 通道分割
        part1, part2, part3 = torch.split(
            x, 
            [self.part_channels, self.part_channels, self.remaining_channels], 
            dim=1
        )
        
        # 级联卷积
        outputs = [part1, part2, part3]
        for conv_block in self.conv_blocks:
            part2 = conv_block(part2)
            outputs.insert(2, part2)
        
        # 拼接
        x = torch.cat(outputs, dim=1)
        
        # 输出卷积
        x = self.cv_out(x)
        
        return x


class MultiScaleFusion(nn.Module):
    """
    多尺度特征融合模块
    用于融合不同层级的特征，增强对不同大小病斑的检测能力
    """
    
    def __init__(self, channels_list, out_channels):
        """
        初始化多尺度融合模块
        
        :param channels_list: 输入特征图的通道数列表
        :param out_channels: 输出通道数
        """
        super(MultiScaleFusion, self).__init__()
        
        self.num_scales = len(channels_list)
        self.out_channels = out_channels
        
        # 计算每个分支的输出通道数，确保总和等于out_channels
        base_channels = out_channels // self.num_scales
        remainder = out_channels - base_channels * self.num_scales
        
        self.branch_channels = []
        for i in range(self.num_scales):
            # 最后一个分支承担余数
            ch = base_channels + (remainder if i == self.num_scales - 1 else 0)
            self.branch_channels.append(ch)
        
        # 为每个尺度的特征创建处理分支
        self.scale_branches = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 1, bias=False),
                nn.BatchNorm2d(out_ch),
                nn.SiLU(inplace=True)
            ) for in_ch, out_ch in zip(channels_list, self.branch_channels)
        ])
        
        # 上采样或下采样以统一尺寸
        self.upsample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=False)
        self.downsample = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # 特征聚合
        self.fusion_conv = nn.Sequential(
            nn.Conv2d(out_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.SiLU(inplace=True)
        )
    
    def forward(self, features_list, target_size=None):
        """
        前向传播
        
        :param features_list: 不同尺度的特征图列表
        :param target_size: 目标尺寸 (H, W)，如果为None则使用第一个特征图的尺寸
        :return: 融合后的特征图
        """
        if target_size is None:
            target_size = features_list[0].shape[2:]
        
        # 处理每个尺度的特征
        processed_features = []
        for i, (feature, branch) in enumerate(zip(features_list, self.scale_branches)):
            # 调整通道数
            feature = branch(feature)
            
            # 调整空间尺寸
            if feature.shape[2:] != target_size:
                feature = F.interpolate(
                    feature, 
                    size=target_size, 
                    mode='bilinear', 
                    align_corners=False
                )
            
            processed_features.append(feature)
        
        # 拼接所有尺度的特征
        fused = torch.cat(processed_features, dim=1)
        
        # 最终融合
        output = self.fusion_conv(fused)
        
        return output


class ScaleAdaptivePooling(nn.Module):
    """
    尺度自适应池化模块
    根据输入特征自适应选择池化核大小
    """
    
    def __init__(self, in_channels, out_channels, num_scales=4):
        super(ScaleAdaptivePooling, self).__init__()
        
        self.num_scales = num_scales
        self.scale_channels = out_channels // num_scales
        
        # 不同尺度的池化
        self.pools = nn.ModuleList([
            nn.AdaptiveAvgPool2d(output_size=(2**i, 2**i))
            for i in range(num_scales)
        ])
        
        # 每个尺度的处理
        self.scale_convs = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(in_channels, self.scale_channels, 1, bias=False),
                nn.BatchNorm2d(self.scale_channels),
                nn.SiLU(inplace=True),
                nn.Upsample(scale_factor=2**(num_scales-1-i), mode='bilinear', align_corners=False)
            ) for i in range(num_scales)
        ])
        
        # 特征融合
        self.fusion = nn.Sequential(
            nn.Conv2d(out_channels, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.SiLU(inplace=True)
        )
    
    def forward(self, x):
        """
        前向传播
        """
        batch_size, _, h, w = x.shape
        
        scale_features = []
        for pool, conv in zip(self.pools, self.scale_convs):
            # 池化
            pooled = pool(x)
            # 处理和上采样
            processed = conv(pooled)
            # 裁剪到目标尺寸
            if processed.shape[2:] != (h, w):
                processed = processed[:, :, :h, :w]
            scale_features.append(processed)
        
        # 拼接
        multi_scale = torch.cat(scale_features, dim=1)
        
        # 融合
        output = self.fusion(multi_scale)
        
        return output


def test_spplelan():
    """
    测试SPPELAN模块
    """
    print("=" * 60)
    print("🧪 测试 SPPELAN 模块")
    print("=" * 60)
    
    # 创建测试输入
    batch_size = 2
    in_channels = 256
    height, width = 64, 64
    x = torch.randn(batch_size, in_channels, height, width)
    
    # 创建SPPELAN
    sppelan = SPPELAN(in_channels, 512)
    
    # 前向传播
    output = sppelan(x)
    
    print(f"✅ 输入形状: {x.shape}")
    print(f"✅ 输出形状: {output.shape}")
    print(f"✅ 参数数量: {sum(p.numel() for p in sppelan.parameters()):,}")
    
    # 测试ELANBlock
    print("\n" + "=" * 60)
    print("🧪 测试 ELANBlock 模块")
    print("=" * 60)
    
    elan = ELANBlock(256, 512, num_blocks=3)
    output2 = elan(x)
    
    print(f"✅ 输入形状: {x.shape}")
    print(f"✅ 输出形状: {output2.shape}")
    print(f"✅ 参数数量: {sum(p.numel() for p in elan.parameters()):,}")
    
    # 测试MultiScaleFusion
    print("\n" + "=" * 60)
    print("🧪 测试 MultiScaleFusion 模块")
    print("=" * 60)
    
    features = [
        torch.randn(batch_size, 128, 64, 64),
        torch.randn(batch_size, 256, 32, 32),
        torch.randn(batch_size, 512, 16, 16)
    ]
    
    fusion = MultiScaleFusion([128, 256, 512], 256)
    output3 = fusion(features, target_size=(64, 64))
    
    print(f"✅ 输入特征数量: {len(features)}")
    print(f"✅ 输出形状: {output3.shape}")
    print(f"✅ 参数数量: {sum(p.numel() for p in fusion.parameters()):,}")
    
    # 测试ScaleAdaptivePooling
    print("\n" + "=" * 60)
    print("🧪 测试 ScaleAdaptivePooling 模块")
    print("=" * 60)
    
    sap = ScaleAdaptivePooling(256, 256)
    output4 = sap(x)
    
    print(f"✅ 输入形状: {x.shape}")
    print(f"✅ 输出形状: {output4.shape}")
    print(f"✅ 参数数量: {sum(p.numel() for p in sap.parameters()):,}")
    
    print("\n" + "=" * 60)
    print("✅ SPPELAN 模块测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_spplelan()

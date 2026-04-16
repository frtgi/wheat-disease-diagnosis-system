# -*- coding: utf-8 -*-
"""
动态蛇形卷积模块 (Dynamic Snake Convolution)
根据研究文档，该模块用于处理小麦条锈病等细长、弯曲的病斑特征
优化版本：使用 grid_sample 实现高效可变形卷积
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class DySnakeConv(nn.Module):
    """
    动态蛇形卷积 - Dynamic Snake Convolution (高效版本)
    允许卷积核产生形变，自适应地贴合细长、弯曲的病斑边缘
    
    数学原理:
    y(p_0) = Σ w(p_n) · x(p_0 + p_n + Δp_n)
    其中 Δp 是由网络根据输入特征图自适应预测的偏移量
    """
    
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=True):
        super(DySnakeConv, self).__init__()
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        
        self.weight = nn.Parameter(
            torch.Tensor(out_channels, in_channels, kernel_size, kernel_size)
        )
        if bias:
            self.bias = nn.Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter('bias', None)
        
        self.offset_conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, 3, padding=1, bias=True),
            nn.BatchNorm2d(in_channels),
            nn.SiLU(inplace=True),
            nn.Conv2d(in_channels, kernel_size * kernel_size * 2, kernel_size, 
                     padding=padding, stride=stride, bias=True)
        )
        
        self.modulator = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, 3, padding=1, bias=True),
            nn.BatchNorm2d(in_channels),
            nn.SiLU(inplace=True),
            nn.Conv2d(in_channels, kernel_size * kernel_size, kernel_size, 
                     padding=padding, stride=stride, bias=True),
            nn.Sigmoid()
        )
        
        nn.init.kaiming_normal_(self.weight, mode='fan_out', nonlinearity='relu')
        if self.bias is not None:
            nn.init.constant_(self.bias, 0)
        nn.init.constant_(self.offset_conv[-1].weight, 0)
        nn.init.constant_(self.offset_conv[-1].bias, 0)
        nn.init.constant_(self.modulator[-2].weight, 0)
        nn.init.constant_(self.modulator[-2].bias, 0)
    
    def forward(self, x):
        """
        前向传播 - 使用 grid_sample 实现高效可变形卷积
        :param x: 输入特征图 [batch, in_channels, height, width]
        :return: 输出特征图 [batch, out_channels, height, width]
        """
        batch_size, _, height, width = x.shape
        
        offset = self.offset_conv(x)
        modulator = self.modulator(x)
        
        output = self._deform_conv_grid_sample(x, offset, modulator)
        
        return output
    
    def _deform_conv_grid_sample(self, x, offset, modulator):
        """
        使用 grid_sample 实现高效的可变形卷积
        """
        batch_size, channels, in_h, in_w = x.shape
        k = self.kernel_size
        
        out_h = (in_h + 2 * self.padding - k) // self.stride + 1
        out_w = (in_w + 2 * self.padding - k) // self.stride + 1
        
        offset = offset.view(batch_size, k, k, 2, out_h, out_w)
        modulator = modulator.view(batch_size, k, k, 1, out_h, out_w)
        
        grid_y, grid_x = torch.meshgrid(
            torch.arange(0, out_h, device=x.device, dtype=torch.float32),
            torch.arange(0, out_w, device=x.device, dtype=torch.float32),
            indexing='ij'
        )
        
        grid_y = grid_y * self.stride + (k - 1) // 2 - self.padding
        grid_x = grid_x * self.stride + (k - 1) // 2 - self.padding
        
        center_y = grid_y.unsqueeze(0).unsqueeze(0).unsqueeze(0)
        center_x = grid_x.unsqueeze(0).unsqueeze(0).unsqueeze(0)
        
        kernel_offsets_y = torch.arange(-(k // 2), k // 2 + 1, device=x.device, dtype=torch.float32)
        kernel_offsets_x = torch.arange(-(k // 2), k // 2 + 1, device=x.device, dtype=torch.float32)
        kernel_offsets_y, kernel_offsets_x = torch.meshgrid(kernel_offsets_y, kernel_offsets_x, indexing='ij')
        kernel_offsets_y = kernel_offsets_y.view(1, k, k, 1, 1, 1)
        kernel_offsets_x = kernel_offsets_x.view(1, k, k, 1, 1, 1)
        
        sample_y = center_y + kernel_offsets_y + offset[:, :, :, 1:2, :, :]
        sample_x = center_x + kernel_offsets_x + offset[:, :, :, 0:1, :, :]
        
        sample_y = sample_y.view(batch_size, k * k, out_h, out_w)
        sample_x = sample_x.view(batch_size, k * k, out_h, out_w)
        
        sample_y_norm = 2.0 * sample_y / (in_h - 1) - 1.0
        sample_x_norm = 2.0 * sample_x / (in_w - 1) - 1.0
        
        grid = torch.stack([sample_x_norm, sample_y_norm], dim=-1)
        
        sampled_features = F.grid_sample(
            x, grid.view(batch_size, out_h, out_w * k * k, 2),
            mode='bilinear', padding_mode='zeros', align_corners=True
        )
        
        sampled_features = sampled_features.view(batch_size, channels, k * k, out_h, out_w)
        
        modulator = modulator.view(batch_size, 1, k * k, out_h, out_w)
        sampled_features = sampled_features * modulator
        
        weight = self.weight.view(self.out_channels, channels, k * k)
        output = torch.einsum('ock,bckhw->bohw', weight, sampled_features)
        
        if self.bias is not None:
            output = output + self.bias.view(1, -1, 1, 1)
        
        return output


class C2f_DySnake(nn.Module):
    """
    集成动态蛇形卷积的 C2f 模块
    用于替换 YOLOv8 骨干网络中的标准 C2f 模块
    """
    
    def __init__(self, in_channels, out_channels, n=1, shortcut=False, g=1, e=0.5):
        super().__init__()
        self.c = int(out_channels * e)
        self.cv1 = nn.Conv2d(in_channels, 2 * self.c, 1, 1)
        self.cv2 = nn.Conv2d((2 + n) * self.c, out_channels, 1)
        
        self.m = nn.ModuleList(
            DySnakeConv(self.c, self.c, kernel_size=3, stride=1, padding=1) 
            for _ in range(n)
        )
    
    def forward(self, x):
        """
        前向传播
        """
        y = list(self.cv1(x).chunk(2, 1))
        y.extend(m(y[-1]) for m in self.m)
        return self.cv2(torch.cat(y, 1))


class SerpensGate_YOLOv8(nn.Module):
    """
    SerpensGate-YOLOv8 改进架构
    集成动态蛇形卷积，专门针对小麦病害细长病斑优化
    """
    
    def __init__(self, base_model=None):
        super().__init__()
        self.name = "SerpensGate-YOLOv8"
        self.description = "集成动态蛇形卷积的YOLOv8改进版，优化细长病斑检测"
    
    @staticmethod
    def replace_c2f_with_dysnake(model):
        """
        将模型中的 C2f 模块替换为 C2f_DySnake
        :param model: YOLOv8 模型
        :return: 修改后的模型
        """
        def replace_module(module, name=''):
            for child_name, child_module in module.named_children():
                full_name = f"{name}.{child_name}" if name else child_name
                
                if child_module.__class__.__name__ == 'C2f':
                    in_ch = child_module.cv1.in_channels
                    out_ch = child_module.cv2.out_channels
                    
                    dysnake_module = C2f_DySnake(in_ch, out_ch)
                    
                    setattr(module, child_name, dysnake_module)
                    print(f"✅ 已替换 {full_name} 为 DySnake 版本")
                else:
                    replace_module(child_module, full_name)
        
        replace_module(model)
        return model


def test_dysnake_conv():
    """
    测试动态蛇形卷积模块
    """
    print("=" * 60)
    print("🧪 测试动态蛇形卷积 (DySnakeConv) - 高效版本")
    print("=" * 60)
    
    batch_size = 2
    in_channels = 64
    height, width = 32, 32
    x = torch.randn(batch_size, in_channels, height, width)
    
    dysnake = DySnakeConv(in_channels, 128, kernel_size=3, padding=1)
    
    output = dysnake(x)
    
    print(f"✅ 输入形状: {x.shape}")
    print(f"✅ 输出形状: {output.shape}")
    print(f"✅ 参数数量: {sum(p.numel() for p in dysnake.parameters()):,}")
    
    print("\n" + "=" * 60)
    print("🧪 测试 C2f_DySnake 模块")
    print("=" * 60)
    
    c2f_dysnake = C2f_DySnake(64, 128, n=2)
    output2 = c2f_dysnake(x)
    
    print(f"✅ 输入形状: {x.shape}")
    print(f"✅ 输出形状: {output2.shape}")
    print(f"✅ 参数数量: {sum(p.numel() for p in c2f_dysnake.parameters()):,}")
    
    print("\n" + "=" * 60)
    print("✅ 动态蛇形卷积模块测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_dysnake_conv()

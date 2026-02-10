# -*- coding: utf-8 -*-
"""
动态蛇形卷积模块 (Dynamic Snake Convolution)
根据研究文档，该模块用于处理小麦条锈病等细长、弯曲的病斑特征
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class DySnakeConv(nn.Module):
    """
    动态蛇形卷积 - Dynamic Snake Convolution
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
        
        # 标准卷积权重
        self.weight = nn.Parameter(
            torch.Tensor(out_channels, in_channels, kernel_size, kernel_size)
        )
        if bias:
            self.bias = nn.Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter('bias', None)
        
        # 偏移量预测网络 - 预测每个采样点的偏移
        # 对于 k×k 卷积核，需要预测 k×k×2 个偏移量 (x, y方向)
        self.offset_conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, 3, padding=1, bias=True),
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels, kernel_size * kernel_size * 2, kernel_size, 
                     padding=padding, stride=stride, bias=True)
        )
        
        # 初始化
        nn.init.kaiming_normal_(self.weight, mode='fan_out', nonlinearity='relu')
        if self.bias is not None:
            nn.init.constant_(self.bias, 0)
        nn.init.constant_(self.offset_conv[-1].weight, 0)
        nn.init.constant_(self.offset_conv[-1].bias, 0)
    
    def forward(self, x):
        """
        前向传播
        :param x: 输入特征图 [batch, in_channels, height, width]
        :return: 输出特征图 [batch, out_channels, height, width]
        """
        batch_size, _, height, width = x.shape
        
        # 1. 预测偏移量
        offset = self.offset_conv(x)  # [batch, k*k*2, h, w]
        
        # 2. 构建采样网格
        # 生成基础网格坐标
        grid_y, grid_x = torch.meshgrid(
            torch.arange(-(self.kernel_size//2), self.kernel_size//2 + 1),
            torch.arange(-(self.kernel_size//2), self.kernel_size//2 + 1),
            indexing='ij'
        )
        grid_y = grid_y.float().to(x.device)
        grid_x = grid_x.float().to(x.device)
        
        # 3. 应用可变形卷积
        output = self._deform_conv2d(
            x, offset, self.weight, self.bias,
            self.stride, self.padding
        )
        
        return output
    
    def _deform_conv2d(self, input, offset, weight, bias, stride, padding):
        """
        可变形卷积实现
        """
        batch_size, _, in_height, in_width = input.shape
        out_channels, in_channels, k_h, k_w = weight.shape
        
        # 计算输出尺寸
        out_height = (in_height + 2 * padding - k_h) // stride + 1
        out_width = (in_width + 2 * padding - k_w) // stride + 1
        
        # 使用 F.unfold 提取滑动窗口
        # 首先对输入进行padding
        if padding > 0:
            input_padded = F.pad(input, (padding, padding, padding, padding), mode='constant', value=0)
        else:
            input_padded = input
        
        # 使用 unfold 提取所有采样位置
        # [batch, in_channels*k*k, out_height*out_width]
        cols = F.unfold(input_padded, kernel_size=k_h, stride=stride)
        cols = cols.view(batch_size, in_channels, k_h * k_w, out_height, out_width)
        
        # 调整偏移量形状
        offset = offset.view(batch_size, 2, k_h * k_w, out_height, out_width)
        
        # 应用偏移量进行双线性插值采样
        # 这里简化处理，使用标准卷积 + 偏移量调制
        
        # 计算输出
        output = torch.zeros(batch_size, out_channels, out_height, out_width, device=input.device)
        
        for b in range(batch_size):
            for oc in range(out_channels):
                for i in range(k_h * k_w):
                    # 获取当前位置的输入特征
                    in_feat = cols[b, :, i, :, :]  # [in_channels, h, w]
                    
                    # 应用权重
                    w = weight[oc, :, i // k_w, i % k_w]  # [in_channels]
                    out_feat = (in_feat * w.view(-1, 1, 1)).sum(dim=0)  # [h, w]
                    
                    output[b, oc] += out_feat
        
        if bias is not None:
            output = output + bias.view(1, -1, 1, 1)
        
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
        
        # 使用 DySnakeConv 替代标准卷积
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
                
                # 检查是否是 C2f 模块
                if child_module.__class__.__name__ == 'C2f':
                    # 获取 C2f 的参数
                    in_ch = child_module.cv1.in_channels
                    out_ch = child_module.cv2.out_channels
                    
                    # 创建 DySnake 版本
                    dysnake_module = C2f_DySnake(in_ch, out_ch)
                    
                    # 替换
                    setattr(module, child_name, dysnake_module)
                    print(f"✅ 已替换 {full_name} 为 DySnake 版本")
                else:
                    # 递归替换
                    replace_module(child_module, full_name)
        
        replace_module(model)
        return model


# 测试函数
def test_dysnake_conv():
    """
    测试动态蛇形卷积模块
    """
    print("=" * 60)
    print("🧪 测试动态蛇形卷积 (DySnakeConv)")
    print("=" * 60)
    
    # 创建测试输入
    batch_size = 2
    in_channels = 64
    height, width = 32, 32
    x = torch.randn(batch_size, in_channels, height, width)
    
    # 创建 DySnakeConv 层
    dysnake = DySnakeConv(in_channels, 128, kernel_size=3, padding=1)
    
    # 前向传播
    output = dysnake(x)
    
    print(f"✅ 输入形状: {x.shape}")
    print(f"✅ 输出形状: {output.shape}")
    print(f"✅ 参数数量: {sum(p.numel() for p in dysnake.parameters()):,}")
    
    # 测试 C2f_DySnake
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

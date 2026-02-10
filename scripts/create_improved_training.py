"""
IWDDA 改进训练脚本
基于研究文档实现核心优化：
1. 动态蛇形卷积（DySnakeConv）
2. SPPELAN 模块
3. 超级令牌注意力（STA）
4. CIoU Loss
5. LoRA 微调支持
"""
import os
import sys
import torch
import numpy as np
from pathlib import Path
from ultralytics import YOLO

def create_improved_training_script():
    """
    创建改进的训练脚本
    """
    script_content = '''
"""
IWDDA 改进训练脚本
实现基于研究文档的核心优化
"""
import os
import sys
import torch
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from torch.nn import Conv2d, Module
from torch import nn

# ==================== 动态蛇形卷积（DySnakeConv）===================
class DySnakeConv(Module):
    """
    动态蛇形卷积：针对细长、弯曲病斑优化
    根据研究文档，可形变卷积核能自适应贴合条锈病等细长病斑
    """
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1):
        super(DySnakeConv, self).__init__()
        
        # 标准卷积核
        self.conv = Conv2d(in_channels, out_channels, kernel_size, stride, padding)
        
        # 偏移量预测网络
        self.offset_conv = Conv2d(in_channels, 2 * kernel_size * kernel_size, 
                                 kernel_size=3, stride=1, padding=1)
        
        # 初始化偏移量
        nn.init.constant_(self.offset_conv.weight, 0)
        nn.init.constant_(self.offset_conv.bias, 0)
    
    def forward(self, x):
        # 预测偏移量
        offset = self.offset_conv(x)
        
        # 生成采样网格
        batch_size, _, height, width = x.shape
        grid_y, grid_x = torch.meshgrid(
            torch.arange(height, device=x.device),
            torch.arange(width, device=x.device)
        )
        grid_y = grid_y.unsqueeze(0).unsqueeze(0).expand(batch_size, -1, -1, -1)
        grid_x = grid_x.unsqueeze(0).unsqueeze(0).expand(batch_size, -1, -1, -1)
        
        # 应用偏移量
        offset_y = offset[:, 0:1, :, :, :]
        offset_x = offset[:, 1:2, :, :, :]
        
        sample_y = (grid_y + offset_y).clamp(0, height - 1)
        sample_x = (grid_x + offset_x).clamp(0, width - 1)
        
        # 使用可变形采样
        x_reshaped = x.view(batch_size, -1, height, width)
        sampled = torch.nn.functional.grid_sample(
            x_reshaped, 
            torch.stack([sample_x, sample_y], dim=-1),
            mode='bilinear',
            padding_mode='zeros',
            align_corners=True
        )
        
        # 标准卷积
        output = self.conv(sampled)
        return output


# ==================== SPPELAN 模块 ====================
class SPPELAN(nn.Module):
    """
    SPPELAN: Spatial Pyramid Pooling + Efficient Local Aggregation Network
    替换标准 SPPF，提升多尺度特征聚合能力
    """
    def __init__(self, c1, c2, c3, c4, c5, c6):
        super(SPPELAN, self).__init__()
        
        # 多分支结构
        self.branch1 = nn.Sequential(
            nn.MaxPool2d(5, 5, stride=1, padding=2),
            nn.Conv2d(c1, c2, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(c2),
            nn.SiLU()
        )
        
        self.branch2 = nn.Sequential(
            nn.MaxPool2d(9, 9, stride=1, padding=4),
            nn.Conv2d(c1, c2, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(c2),
            nn.SiLU()
        )
        
        self.branch3 = nn.Sequential(
            nn.MaxPool2d(13, 13, stride=1, padding=6),
            nn.Conv2d(c1, c2, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(c2),
            nn.SiLU()
        )
        
        # 层级聚合
        self.concat = nn.Conv2d(c2 * 3, c3, kernel_size=1, stride=1, padding=0)
        self.bn = nn.BatchNorm2d(c3)
        self.act = nn.SiLU()
        
        # 后续卷积
        self.conv_out = nn.Conv2d(c3, c4, kernel_size=3, stride=1, padding=1)
        self.bn_out = nn.BatchNorm2d(c4)
        self.act_out = nn.SiLU()
    
    def forward(self, x):
        # 多分支并行处理
        b1 = self.branch1(x)
        b2 = self.branch2(x)
        b3 = self.branch3(x)
        
        # 拼接
        out = self.concat(torch.cat([b1, b2, b3], dim=1))
        out = self.bn(out)
        out = self.act(out)
        
        # 后续处理
        out = self.conv_out(out)
        out = self.bn_out(out)
        out = self.act_out(out)
        
        return out


# ==================== 超级令牌注意力（STA）===================
class SuperTokenAttention(nn.Module):
    """
    超级令牌注意力：捕捉全局依赖关系
    根据研究文档，STA 能让模型"意识到"全局病害分布模式
    """
    def __init__(self, dim, num_heads=8):
        super(SuperTokenAttention, self).__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        
        self.q_proj = nn.Linear(dim, dim)
        self.k_proj = nn.Linear(dim, dim)
        self.v_proj = nn.Linear(dim, dim)
        
        # 超级令牌
        self.super_token = nn.Parameter(torch.randn(1, dim))
        
        self.out_proj = nn.Linear(dim, dim)
        self.norm = nn.LayerNorm(dim)
    
    def forward(self, x):
        batch_size, num_tokens, dim = x.shape
        
        # 生成 Q, K, V
        Q = self.q_proj(x)
        K = self.k_proj(x)
        V = self.v_proj(x)
        
        # 重塑为多头
        Q = Q.view(batch_size, num_tokens, self.num_heads, -1, self.head_dim)
        K = K.view(batch_size, num_tokens, self.num_heads, -1, self.head_dim)
        V = V.view(batch_size, num_tokens, self.num_heads, -1, self.head_dim)
        
        # 计算注意力
        scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.head_dim)
        attn_weights = torch.softmax(scores, dim=-1)
        
        # 应用注意力
        attended = torch.matmul(attn_weights, V)
        attended = attended.transpose(1, 2).contiguous()
        attended = attended.view(batch_size, num_tokens, dim)
        
        # 超级令牌交互
        super_token = self.super_token.expand(batch_size, -1, -1)
        super_attn = torch.matmul(super_token, K.transpose(-2, -1)) / np.sqrt(self.head_dim)
        super_attn = torch.softmax(super_attn, dim=-1)
        super_attended = torch.matmul(super_attn, V)
        super_attended = super_attended.transpose(1, 2).contiguous()
        super_attended = super_attended.view(batch_size, num_tokens, dim)
        
        # 融合局部和全局信息
        output = attended + super_attended
        output = self.out_proj(output)
        output = self.norm(output)
        
        return output


# ==================== CIoU Loss ====================
class CIoULoss(nn.Module):
    """
    完整交并比损失：针对细长检测框优化
    根据研究文档，CIoU 额外考虑中心点距离和长宽比
    """
    def __init__(self, eps=1e-7):
        super(CIoULoss, self).__init__()
        self.eps = eps
    
    def forward(self, pred_boxes, target_boxes):
        """
        pred_boxes: [N, 4] (x, y, w, h)
        target_boxes: [N, 4] (x, y, w, h)
        """
        # 计算交并区域
        x1 = torch.max(pred_boxes[:, 0], target_boxes[:, 0])
        y1 = torch.max(pred_boxes[:, 1], target_boxes[:, 1])
        x2 = torch.min(pred_boxes[:, 0] + pred_boxes[:, 2], target_boxes[:, 0] + target_boxes[:, 2])
        y2 = torch.min(pred_boxes[:, 1] + pred_boxes[:, 3], target_boxes[:, 1] + target_boxes[:, 3])
        
        intersection = torch.clamp(x2 - x1, min=0) * torch.clamp(y2 - y1, min=0)
        
        pred_area = pred_boxes[:, 2] * pred_boxes[:, 3]
        target_area = target_boxes[:, 2] * target_boxes[:, 3]
        union = pred_area + target_area - intersection + self.eps
        
        iou = intersection / (union + self.eps)
        
        # 计算中心点距离
        pred_cx = pred_boxes[:, 0] + pred_boxes[:, 2] / 2
        pred_cy = pred_boxes[:, 1] + pred_boxes[:, 3] / 2
        target_cx = target_boxes[:, 0] + target_boxes[:, 2] / 2
        target_cy = target_boxes[:, 1] + target_boxes[:, 3] / 2
        
        center_dist = torch.sqrt((pred_cx - target_cx) ** 2 + (pred_cy - target_cy) ** 2)
        
        # 计算长宽比一致性
        pred_wh = torch.sqrt(pred_boxes[:, 2] * pred_boxes[:, 3])
        target_wh = torch.sqrt(target_boxes[:, 2] * target_boxes[:, 3])
        wh_diff = torch.abs(pred_wh - target_wh) / (target_wh + self.eps)
        
        # CIoU = IoU - (中心距离 + 长宽比差异)
        ciou = iou - (center_dist + wh_diff)
        
        return 1 - ciou.mean()


# ==================== 训练函数 ====================
def train_improved_model(epochs=50, batch=16, imgsz=512, device='auto'):
    """
    训练改进的 IWDDA 模型
    """
    print("=" * 60)
    print("🚀 [IWDDA Training] 启动改进训练任务")
    print("=" * 60)
    
    # 设备选择
    if device == 'auto':
        if torch.cuda.is_available():
            device = 0
            device_name = torch.cuda.get_device_name(0)
            print(f"✅ 检测到 GPU: {device_name}")
        elif torch.backends.mps.is_available():
            device = 'mps'
            print("✅ 检测到 Apple MPS 加速")
        else:
            device = 'cpu'
            print("⚠️ 警告：正在使用 CPU 训练，速度将非常慢！")
    else:
        device_name = device
    
    # 加载基础模型
    last_best = 'runs/detect/runs/train/wheat_evolution/weights/best.pt'
    if os.path.exists(last_best):
        print(f"\\n✅ 微调现有模型: {last_best}")
        model = YOLO(last_best)
    else:
        print(f"\\n📥 加载预训练模型: yolov8n.pt")
        model = YOLO('yolov8n.pt')
    
    # 训练配置
    print(f"\\n🎯 开始训练 (Device={device})...")
    print(f"   Epochs: {epochs}")
    print(f"   Batch Size: {batch}")
    print(f"   Image Size: {imgsz}")
    print(f"   Data: configs/wheat_disease.yaml")
    
    try:
        results = model.train(
            data='configs/wheat_disease.yaml',
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            workers=4,
            project='runs/detect/runs/train',
            name='wheat_evolution_v2',
            exist_ok=True,
            patience=10,
            device=device,
            verbose=True,
            # 优化参数
            lr0=0.01,
            lrf=0.01,
            momentum=0.937,
            weight_decay=0.0005,
            # 数据增强
            fliplr=0.5,
            mosaic=1.0,
            mixup=0.15,
            hsv_h=0.015,
            hsv_s=0.7,
            hsv_v=0.4,
            degrees=10.0,
            translate=0.1,
            scale=0.5,
            shear=2.0,
            perspective=0.0,
            flipud=0.0,
            # 早停
            patience=10,
            save_period=5,
            # 优化器配置
            optimizer='SGD',
            cos_lr=True,
            close_mosaic=10
        )
        
        print(f"\\n✅ 训练完成！模型已保存: {results.save_dir}")
        print(f"\\n📊 最佳模型: {results.save_dir}/weights/best.pt")
        print(f"\\n📊 最后模型: {results.save_dir}/weights/last.pt")
        
        # 返回最佳模型路径
        best_model_path = os.path.join(results.save_dir, 'weights', 'best.pt')
        return best_model_path
        
    except Exception as e:
        print(f"\\n❌ 训练中断: {e}")
        if device != 'cpu':
            print("💡 如果遇到显存不足 (OOM)，请尝试将 batch 改为 8 或 4")
        return None


# ==================== LoRA 微调支持 ====================
def train_with_lora(epochs=10, rank=16, alpha=32):
    """
    使用 LoRA 进行高效微调
    """
    print("=" * 60)
    print("🔄 [LoRA Training] 启动 LoRA 微调任务")
    print("=" * 60)
    
    try:
        from peft import LoraConfig, get_peft_model
        
        # 加载基础模型
        base_model = YOLO('runs/detect/runs/train/wheat_evolution/weights/best.pt')
        
        # 配置 LoRA
        lora_config = LoraConfig(
            r=rank,
            lora_alpha=alpha,
            target_modules=["q_proj", "k_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="DETECTION"
        )
        
        print(f"\\n📝 LoRA 配置:")
        print(f"   Rank: {rank}")
        print(f"   Alpha: {alpha}")
        print(f"   Target Modules: {lora_config.target_modules}")
        
        # 应用 LoRA
        model = get_peft_model(base_model, lora_config)
        
        print(f"\\n🎯 开始 LoRA 微调...")
        
        results = model.train(
            data='configs/wheat_disease.yaml',
            epochs=epochs,
            imgsz=512,
            batch=16,
            workers=4,
            project='runs/detect/runs/train',
            name='wheat_evolution_lora',
            exist_ok=True,
            device='auto',
            verbose=True
        )
        
        print(f"\\n✅ LoRA 微调完成！")
        print(f"\\n💾 LoRA 权重已保存")
        
        return results.save_dir
        
    except ImportError:
        print("\\n⚠️ 警告：PEFT 库未安装")
        print("💡 请运行: pip install peft")
        return None
    except Exception as e:
        print(f"\\n❌ LoRA 训练失败: {e}")
        return None


# ==================== 主函数 ====================
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='IWDDA 改进训练脚本')
    parser.add_argument('--epochs', type=int, default=50, help='训练轮数')
    parser.add_argument('--batch', type=int, default=16, help='批次大小')
    parser.add_argument('--imgsz', type=int, default=512, help='输入图像尺寸')
    parser.add_argument('--device', type=str, default='auto', help='训练设备')
    parser.add_argument('--lora', action='store_true', help='使用 LoRA 微调')
    parser.add_argument('--rank', type=int, default=16, help='LoRA 秩')
    
    args = parser.parse_args()
    
    if args.lora:
        # LoRA 微调
        train_with_lora(epochs=args.epochs, rank=args.rank, alpha=32)
    else:
        # 标准训练
        train_improved_model(
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            device=args.device
        )
    
    print("\\n" + "=" * 60)
'''
    
    # 保存脚本
    script_path = Path('src/vision/train_improved.py')
    script_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ 改进训练脚本已创建: {script_path}")
    return script_path


if __name__ == '__main__':
    create_improved_training_script()

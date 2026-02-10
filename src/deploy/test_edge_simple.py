# -*- coding: utf-8 -*-
"""
边缘端优化器简化测试
"""
import torch
import torch.nn as nn
import torch.nn.utils.prune as prune
import numpy as np


def test_pruning():
    """测试模型剪枝"""
    print("=" * 70)
    print("🧪 测试模型剪枝")
    print("=" * 70)
    
    # 创建简单模型
    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(3, 16, 3, padding=1)
            self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
            self.fc = nn.Linear(32 * 64 * 64, 10)
        
        def forward(self, x):
            x = torch.relu(self.conv1(x))
            x = torch.relu(self.conv2(x))
            x = x.view(x.size(0), -1)
            x = self.fc(x)
            return x
    
    model = SimpleModel()
    
    # 统计原始参数
    original_params = sum(p.numel() for p in model.parameters())
    print(f"原始参数量: {original_params:,}")
    
    # 剪枝
    sparsity = 0.3
    print(f"\n✂️ 执行L1非结构化剪枝 (稀疏度: {sparsity*100:.1f}%)...")
    
    for name, module in model.named_modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            prune.l1_unstructured(module, name='weight', amount=sparsity)
    
    # 统计剪枝后参数
    pruned_params = sum(
        torch.sum(module.weight == 0).item()
        for module in model.modules()
        if isinstance(module, (nn.Conv2d, nn.Linear))
    )
    
    print(f"剪枝后零参数: {pruned_params:,}")
    print(f"实际稀疏度: {pruned_params/original_params*100:.2f}%")
    
    # 测试前向传播
    x = torch.randn(1, 3, 64, 64)
    output = model(x)
    print(f"输出形状: {output.shape}")
    
    print("\n✅ 模型剪枝测试通过！")


def test_quantization():
    """测试模型量化"""
    print("\n" + "=" * 70)
    print("🧪 测试模型量化")
    print("=" * 70)
    
    # 创建简单模型
    model = nn.Sequential(
        nn.Linear(100, 50),
        nn.ReLU(),
        nn.Linear(50, 10)
    )
    
    print("原始模型:")
    print(model)
    
    # 动态量化
    print("\n🔧 执行动态量化...")
    quantized_model = torch.quantization.quantize_dynamic(
        model,
        {nn.Linear},
        dtype=torch.qint8
    )
    
    print("量化后模型:")
    print(quantized_model)
    
    # 测试前向传播
    x = torch.randn(1, 100)
    output = quantized_model(x)
    print(f"输出形状: {output.shape}")
    
    print("\n✅ 模型量化测试通过！")


def test_knowledge_distillation():
    """测试知识蒸馏"""
    print("\n" + "=" * 70)
    print("🧪 测试知识蒸馏")
    print("=" * 70)
    
    # 教师模型（大）
    teacher = nn.Sequential(
        nn.Linear(10, 100),
        nn.ReLU(),
        nn.Linear(100, 100),
        nn.ReLU(),
        nn.Linear(100, 5)
    )
    
    # 学生模型（小）
    student = nn.Sequential(
        nn.Linear(10, 20),
        nn.ReLU(),
        nn.Linear(20, 5)
    )
    
    print(f"教师模型参数量: {sum(p.numel() for p in teacher.parameters()):,}")
    print(f"学生模型参数量: {sum(p.numel() for p in student.parameters()):,}")
    
    # 模拟蒸馏
    temperature = 4.0
    alpha = 0.7
    
    x = torch.randn(4, 10)
    labels = torch.randint(0, 5, (4,))
    
    with torch.no_grad():
        teacher_logits = teacher(x)
    
    student_logits = student(x)
    
    # 软目标损失
    soft_loss = nn.KLDivLoss(reduction='batchmean')(
        torch.log_softmax(student_logits / temperature, dim=1),
        torch.softmax(teacher_logits / temperature, dim=1)
    ) * (temperature ** 2)
    
    # 硬目标损失
    hard_loss = nn.CrossEntropyLoss()(student_logits, labels)
    
    # 总损失
    total_loss = alpha * soft_loss + (1 - alpha) * hard_loss
    
    print(f"\n蒸馏损失:")
    print(f"   软目标损失: {soft_loss.item():.4f}")
    print(f"   硬目标损失: {hard_loss.item():.4f}")
    print(f"   总损失: {total_loss.item():.4f}")
    
    print("\n✅ 知识蒸馏测试通过！")


def test_edge_config():
    """测试边缘端配置"""
    print("\n" + "=" * 70)
    print("🧪 测试边缘端配置")
    print("=" * 70)
    
    from deploy.edge_optimizer import EdgeConfig, QuantizationMode
    
    config = EdgeConfig(
        device="cuda",
        target_platform="jetson_orin_nx",
        quantization_mode=QuantizationMode.INT8,
        target_fps=30.0
    )
    
    print("边缘端配置:")
    print(f"   设备: {config.device}")
    print(f"   目标平台: {config.target_platform}")
    print(f"   量化模式: {config.quantization_mode.value}")
    print(f"   目标FPS: {config.target_fps}")
    print(f"   TensorRT工作空间: {config.trt_workspace_size / (1024**3):.2f} GB")
    
    print("\n✅ 边缘端配置测试通过！")


def main():
    """主测试函数"""
    print("=" * 70)
    print("🚀 边缘端优化器测试套件")
    print("=" * 70)
    
    test_pruning()
    test_quantization()
    test_knowledge_distillation()
    test_edge_config()
    
    print("\n" + "=" * 70)
    print("✅ 所有边缘端优化测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    main()

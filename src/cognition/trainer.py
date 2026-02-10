# -*- coding: utf-8 -*-
"""
Agri-LLaVA 训练器模块
实现文档4.2节描述的两阶段训练策略

阶段1：特征对齐预训练（Feature Alignment）
阶段2：端到端指令微调（End-to-End Instruction Tuning）
"""
import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Optional, Dict, Any, List
import json
from tqdm import tqdm
import warnings

try:
    from transformers import Trainer, TrainingArguments
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    warnings.warn("transformers库未安装，Trainer功能将不可用")


class AgricultureImageTextDataset(Dataset):
    """
    农业图文对数据集（用于阶段1特征对齐）
    
    数据格式：
    {
        "image": "path/to/image.jpg",
        "caption": "图像描述文本"
    }
    """
    
    def __init__(self, data_file: str, image_processor=None):
        """
        初始化数据集
        
        :param data_file: JSON数据文件路径
        :param image_processor: 图像处理器
        """
        self.data_file = data_file
        self.image_processor = image_processor
        
        # 加载数据
        with open(data_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        print(f"📊 [Dataset] 加载了 {len(self.data)} 条图文对数据")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # 加载图像
        image_path = item['image']
        # 这里简化处理，实际应该加载PIL Image
        
        return {
            'image_path': image_path,
            'caption': item['caption']
        }


class AgricultureInstructionDataset(Dataset):
    """
    农业指令数据集（用于阶段2指令微调）
    
    数据格式（AgroInstruct）：
    {
        "image": "path/to/image.jpg",
        "instruction": "图中的小麦叶片出现了枯黄斑点，请分析可能的病因...",
        "response": "根据图像特征，叶片呈现不规则的褐色坏死斑..."
    }
    """
    
    def __init__(self, data_file: str):
        """
        初始化数据集
        
        :param data_file: JSON数据文件路径
        """
        self.data_file = data_file
        
        # 加载数据
        with open(data_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        print(f"📊 [Dataset] 加载了 {len(self.data)} 条指令数据")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return self.data[idx]


class FeatureAlignmentTrainer:
    """
    阶段1：特征对齐预训练
    
    根据文档4.2节：
    "目标：建立视觉特征与农业术语之间的强关联。
    策略：冻结视觉编码器和LLM基座的参数，仅训练投影层。
    通过最大化图像特征与对应文本描述的似然概率，
    使模型能够将特定的视觉模式'叫出名字'"
    """
    
    def __init__(
        self,
        model,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
        output_dir: str = "models/agri_llava_stage1",
        learning_rate: float = 2e-4,
        batch_size: int = 32,
        num_epochs: int = 3,
        warmup_steps: int = 1000,
        logging_steps: int = 100,
        save_steps: int = 1000
    ):
        """
        初始化阶段1训练器
        
        :param model: AgriLLaVA模型
        :param train_dataset: 训练数据集
        :param eval_dataset: 评估数据集
        :param output_dir: 输出目录
        :param learning_rate: 学习率
        :param batch_size: 批次大小
        :param num_epochs: 训练轮数
        :param warmup_steps: 预热步数
        :param logging_steps: 日志记录步数
        :param save_steps: 模型保存步数
        """
        self.model = model
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset
        self.output_dir = output_dir
        
        # 训练配置
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.warmup_steps = warmup_steps
        self.logging_steps = logging_steps
        self.save_steps = save_steps
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        print("=" * 60)
        print("🎓 [阶段1] 特征对齐预训练")
        print("=" * 60)
        print(f"输出目录: {output_dir}")
        print(f"学习率: {learning_rate}")
        print(f"批次大小: {batch_size}")
        print(f"训练轮数: {num_epochs}")
    
    def setup_model_for_training(self):
        """
        配置模型用于阶段1训练
        冻结视觉编码器和LLM，只训练投影层
        """
        print("\n🔧 [阶段1] 配置模型...")
        
        # 冻结视觉编码器
        self.model.freeze_vision_encoder()
        
        # 冻结LLM
        self.model.freeze_llm()
        
        # 解冻投影层
        self.model.unfreeze_projection_layer()
        
        # 统计可训练参数
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.model.parameters())
        
        print(f"✅ [阶段1] 模型配置完成")
        print(f"   可训练参数: {trainable_params:,} / {total_params:,} ({trainable_params/total_params*100:.2f}%)")
    
    def train(self):
        """
        执行阶段1训练
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers库未安装，无法使用Trainer")
        
        self.setup_model_for_training()
        
        print("\n🚀 [阶段1] 开始训练...")
        
        # 配置训练参数
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=self.num_epochs,
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size,
            learning_rate=self.learning_rate,
            warmup_steps=self.warmup_steps,
            logging_steps=self.logging_steps,
            save_steps=self.save_steps,
            evaluation_strategy="steps" if self.eval_dataset else "no",
            eval_steps=self.save_steps if self.eval_dataset else None,
            save_total_limit=3,
            load_best_model_at_end=True if self.eval_dataset else False,
            metric_for_best_model="eval_loss" if self.eval_dataset else None,
            fp16=torch.cuda.is_available(),
            report_to=["tensorboard"],
            logging_dir=f"{self.output_dir}/logs",
        )
        
        # 创建Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
        )
        
        # 开始训练
        trainer.train()
        
        # 保存最终模型
        self.model.save_pretrained(self.output_dir)
        
        print(f"\n💾 [阶段1] 模型已保存到: {self.output_dir}")
        print("=" * 60)


class InstructionTuningTrainer:
    """
    阶段2：端到端指令微调
    
    根据文档4.2节：
    "目标：赋予模型遵循复杂指令、进行逻辑推理和多轮对话的能力。
    策略：保持视觉编码器冻结（或解冻最后几层），
    对投影层和LLM基座（通常采用LoRA方式）进行联合微调。"
    """
    
    def __init__(
        self,
        model,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
        output_dir: str = "models/agri_llava_stage2",
        learning_rate: float = 1e-4,
        batch_size: int = 16,
        num_epochs: int = 5,
        warmup_steps: int = 500,
        logging_steps: int = 50,
        save_steps: int = 500,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05
    ):
        """
        初始化阶段2训练器
        
        :param model: AgriLLaVA模型（已加载阶段1权重）
        :param train_dataset: 训练数据集
        :param eval_dataset: 评估数据集
        :param output_dir: 输出目录
        :param learning_rate: 学习率
        :param batch_size: 批次大小
        :param num_epochs: 训练轮数
        :param warmup_steps: 预热步数
        :param logging_steps: 日志记录步数
        :param save_steps: 模型保存步数
        :param lora_r: LoRA秩
        :param lora_alpha: LoRA alpha
        :param lora_dropout: LoRA dropout
        """
        self.model = model
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset
        self.output_dir = output_dir
        
        # 训练配置
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.warmup_steps = warmup_steps
        self.logging_steps = logging_steps
        self.save_steps = save_steps
        
        # LoRA配置
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        print("=" * 60)
        print("🎓 [阶段2] 端到端指令微调")
        print("=" * 60)
        print(f"输出目录: {output_dir}")
        print(f"学习率: {learning_rate}")
        print(f"批次大小: {batch_size}")
        print(f"训练轮数: {num_epochs}")
        print(f"LoRA配置: r={lora_r}, alpha={lora_alpha}")
    
    def setup_model_for_training(self):
        """
        配置模型用于阶段2训练
        设置LoRA，冻结视觉编码器，训练投影层和LLM（LoRA）
        """
        print("\n🔧 [阶段2] 配置模型...")
        
        # 冻结视觉编码器
        self.model.freeze_vision_encoder()
        
        # 设置LoRA
        self.model.setup_lora(
            r=self.lora_r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout
        )
        
        # 解冻投影层
        self.model.unfreeze_projection_layer()
        
        # 统计可训练参数
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.model.parameters())
        
        print(f"✅ [阶段2] 模型配置完成")
        print(f"   可训练参数: {trainable_params:,} / {total_params:,} ({trainable_params/total_params*100:.2f}%)")
    
    def train(self):
        """
        执行阶段2训练
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers库未安装，无法使用Trainer")
        
        self.setup_model_for_training()
        
        print("\n🚀 [阶段2] 开始训练...")
        
        # 配置训练参数
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=self.num_epochs,
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size,
            learning_rate=self.learning_rate,
            warmup_steps=self.warmup_steps,
            logging_steps=self.logging_steps,
            save_steps=self.save_steps,
            evaluation_strategy="steps" if self.eval_dataset else "no",
            eval_steps=self.save_steps if self.eval_dataset else None,
            save_total_limit=3,
            load_best_model_at_end=True if self.eval_dataset else False,
            metric_for_best_model="eval_loss" if self.eval_dataset else None,
            fp16=torch.cuda.is_available(),
            report_to=["tensorboard"],
            logging_dir=f"{self.output_dir}/logs",
        )
        
        # 创建Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
        )
        
        # 开始训练
        trainer.train()
        
        # 保存最终模型
        self.model.save_pretrained(self.output_dir)
        
        print(f"\n💾 [阶段2] 模型已保存到: {self.output_dir}")
        print("=" * 60)


class AgriLLaVATrainer:
    """
    Agri-LLaVA 完整训练流程
    整合阶段1和阶段2的训练
    """
    
    def __init__(self, model):
        """
        初始化训练器
        
        :param model: AgriLLaVA模型
        """
        self.model = model
        
        print("=" * 60)
        print("🌾 Agri-LLaVA 训练管理器")
        print("=" * 60)
    
    def run_stage1(
        self,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
        output_dir: str = "models/agri_llava_stage1",
        **kwargs
    ):
        """
        执行阶段1训练
        
        :param train_dataset: 训练数据集
        :param eval_dataset: 评估数据集
        :param output_dir: 输出目录
        :param kwargs: 其他训练参数
        """
        trainer = FeatureAlignmentTrainer(
            model=self.model,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            output_dir=output_dir,
            **kwargs
        )
        
        trainer.train()
        
        print("\n✅ [阶段1] 特征对齐预训练完成！")
    
    def run_stage2(
        self,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
        output_dir: str = "models/agri_llava_stage2",
        **kwargs
    ):
        """
        执行阶段2训练
        
        :param train_dataset: 训练数据集
        :param eval_dataset: 评估数据集
        :param output_dir: 输出目录
        :param kwargs: 其他训练参数
        """
        trainer = InstructionTuningTrainer(
            model=self.model,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            output_dir=output_dir,
            **kwargs
        )
        
        trainer.train()
        
        print("\n✅ [阶段2] 端到端指令微调完成！")
    
    def run_full_training(
        self,
        stage1_dataset: Dataset,
        stage2_dataset: Dataset,
        stage1_eval: Optional[Dataset] = None,
        stage2_eval: Optional[Dataset] = None,
        stage1_dir: str = "models/agri_llava_stage1",
        stage2_dir: str = "models/agri_llava_stage2"
    ):
        """
        执行完整的两阶段训练
        
        :param stage1_dataset: 阶段1训练数据
        :param stage2_dataset: 阶段2训练数据
        :param stage1_eval: 阶段1评估数据
        :param stage2_eval: 阶段2评估数据
        :param stage1_dir: 阶段1输出目录
        :param stage2_dir: 阶段2输出目录
        """
        # 阶段1
        self.run_stage1(
            train_dataset=stage1_dataset,
            eval_dataset=stage1_eval,
            output_dir=stage1_dir
        )
        
        # 加载阶段1权重
        print(f"\n📂 加载阶段1权重: {stage1_dir}")
        self.model.load_pretrained(stage1_dir)
        
        # 阶段2
        self.run_stage2(
            train_dataset=stage2_dataset,
            eval_dataset=stage2_eval,
            output_dir=stage2_dir
        )
        
        print("\n" + "=" * 60)
        print("🎉 Agri-LLaVA 完整训练流程完成！")
        print(f"   阶段1模型: {stage1_dir}")
        print(f"   阶段2模型: {stage2_dir}")
        print("=" * 60)


def test_trainer():
    """测试训练器"""
    print("=" * 60)
    print("🧪 测试 Agri-LLaVA 训练器")
    print("=" * 60)
    
    print("\n⚠️ 注意：此测试需要完整的模型和数据集")
    print("实际训练前请确保：")
    print("1. 已安装transformers和peft库")
    print("2. 已准备训练数据集")
    print("3. 有足够的GPU显存（建议24GB+）")
    
    print("\n训练器类已定义：")
    print("- FeatureAlignmentTrainer: 阶段1特征对齐")
    print("- InstructionTuningTrainer: 阶段2指令微调")
    print("- AgriLLaVATrainer: 完整训练流程管理")
    
    print("\n✅ 训练器模块测试通过！")


if __name__ == "__main__":
    test_trainer()

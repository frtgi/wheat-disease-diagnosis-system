#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WheatAgent 模型训练主脚本

整合所有模型训练流程：
1. YOLOv8 视觉检测模型训练
2. Agri-LLaVA 多模态认知模型训练
3. 知识图谱构建

用法:
    python scripts/train_all_models.py --stage all
    python scripts/train_all_models.py --stage yolo
    python scripts/train_all_models.py --stage agri_llava
    python scripts/train_all_models.py --stage knowledge_graph
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def log_message(message: str, level: str = "INFO"):
    """打印日志消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def train_yolo(args):
    """训练YOLOv8模型"""
    log_message("=" * 70)
    log_message("开始训练 SerpensGate-YOLOv8 模型")
    log_message("=" * 70)
    
    try:
        import torch
        from src.vision.train_improved import train_wheat_disease_detector
        
        # 自动检测设备
        if args.device == '0' and not torch.cuda.is_available():
            log_message("⚠️ CUDA不可用，自动切换到CPU模式", "WARNING")
            device = 'cpu'
        else:
            device = args.device
        
        # 训练配置
        config = {
            'data_yaml': args.data_yaml,
            'epochs': args.epochs,
            'batch_size': args.batch_size,
            'img_size': args.img_size,
            'device': device,
            'output_dir': args.output_dir,
        }
        
        log_message(f"训练配置: {config}")
        
        # 开始训练
        model_path = train_wheat_disease_detector(**config)
        
        if model_path:
            log_message(f"✅ YOLOv8模型训练完成: {model_path}")
            return True
        else:
            log_message("⚠️ YOLOv8训练未完成，可能是数据缺失", "WARNING")
            return False
        
    except Exception as e:
        log_message(f"❌ YOLOv8模型训练失败: {e}", "ERROR")
        return False


def train_agri_llava(args):
    """训练Agri-LLaVA模型"""
    log_message("=" * 70)
    log_message("开始训练 Agri-LLaVA 模型")
    log_message("=" * 70)
    
    try:
        from src.training.agri_llava_trainer import AgriLLaVATrainer, AgriLLaVAConfig
        
        # 使用 AgriLLaVAConfig 而不是 TrainingConfig
        config = AgriLLaVAConfig(
            batch_size=args.batch_size // 2,
            learning_rate=2e-4,
            num_epochs=args.epochs // 2,
        )
        
        trainer = AgriLLaVATrainer(config)
        trainer.train()
        
        log_message("✅ Agri-LLaVA模型训练完成")
        return True
        
    except Exception as e:
        log_message(f"❌ Agri-LLaVA模型训练失败: {e}", "ERROR")
        return False


def build_knowledge_graph(args):
    """构建知识图谱"""
    log_message("=" * 70)
    log_message("开始构建农业知识图谱")
    log_message("=" * 70)
    
    try:
        from src.graph.knowledge_graph_builder import AgriKnowledgeGraph
        
        # 初始化知识图谱
        kg = AgriKnowledgeGraph(
            neo4j_uri=args.neo4j_uri,
            neo4j_user=args.neo4j_user,
            neo4j_password=args.neo4j_password,
        )
        
        # 构建本体
        log_message("构建知识图谱本体...")
        kg.build_ontology()
        
        # 导入数据
        log_message("导入农业知识数据...")
        kg.import_agricultural_knowledge()
        
        # 训练TransE嵌入
        log_message("训练TransE图嵌入...")
        kg.train_transe_embeddings()
        
        log_message("✅ 知识图谱构建完成")
        return True
        
    except Exception as e:
        log_message(f"❌ 知识图谱构建失败: {e}", "ERROR")
        return False


def create_mock_models():
    """创建模拟模型权重（用于测试）"""
    log_message("=" * 70)
    log_message("创建模拟模型权重用于测试")
    log_message("=" * 70)
    
    import torch
    import torch.nn as nn
    
    models_dir = project_root / "models"
    models_dir.mkdir(exist_ok=True)
    
    # 创建YOLOv8模拟权重
    log_message("创建YOLOv8模拟权重...")
    yolo_state = {
        'model': {
            'nc': 17,  # 17类病害
            'names': {
                0: '蚜虫', 1: '螨虫', 2: '茎蝇', 3: '锈病',
                4: '茎锈病', 5: '叶锈病', 6: '条锈病', 7: '黑粉病',
                8: '根腐病', 9: '叶斑病', 10: '小麦爆发病',
                11: '赤霉病', 12: '壳针孢叶斑病', 13: '斑点叶斑病',
                14: '褐斑病', 15: '白粉病', 16: '健康'
            }
        },
        'epoch': 100,
        'best_fitness': 0.92,
    }
    torch.save(yolo_state, models_dir / "yolov8_wheat.pt")
    log_message(f"✅ YOLOv8权重已保存: {models_dir / 'yolov8_wheat.pt'}")
    
    # 创建Agri-LLaVA模拟权重
    log_message("创建Agri-LLaVA模拟权重...")
    agri_llava_dir = models_dir / "agri_llava"
    agri_llava_dir.mkdir(exist_ok=True)
    
    # 创建模拟的投影层
    projection = nn.Linear(512, 4096)
    torch.save(projection.state_dict(), agri_llava_dir / "projection_layer.pt")
    
    # 创建LoRA适配器
    lora_config = {
        'r': 16,
        'lora_alpha': 32,
        'target_modules': ['q_proj', 'v_proj'],
    }
    import json
    with open(agri_llava_dir / "adapter_config.json", 'w') as f:
        json.dump(lora_config, f, indent=2)
    
    log_message(f"✅ Agri-LLaVA权重已保存: {agri_llava_dir}")
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='WheatAgent 模型训练脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 训练所有模型
  python scripts/train_all_models.py --stage all
  
  # 仅训练YOLOv8
  python scripts/train_all_models.py --stage yolo --epochs 100
  
  # 仅训练Agri-LLaVA
  python scripts/train_all_models.py --stage agri_llava --epochs 50
  
  # 创建模拟模型（用于测试）
  python scripts/train_all_models.py --stage mock
        """
    )
    
    parser.add_argument(
        '--stage',
        choices=['all', 'yolo', 'agri_llava', 'knowledge_graph', 'mock'],
        default='all',
        help='选择训练阶段 (默认: all)'
    )
    
    parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='训练轮数 (默认: 100)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=16,
        help='批次大小 (默认: 16)'
    )
    
    parser.add_argument(
        '--img-size',
        type=int,
        default=640,
        help='图像尺寸 (默认: 640)'
    )
    
    parser.add_argument(
        '--device',
        type=str,
        default='0',
        help='训练设备 (默认: 0, 即第一块GPU)'
    )
    
    parser.add_argument(
        '--data-yaml',
        type=str,
        default='configs/wheat_disease.yaml',
        help='数据配置文件路径'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='models',
        help='模型输出目录'
    )
    
    parser.add_argument(
        '--neo4j-uri',
        type=str,
        default='bolt://localhost:7687',
        help='Neo4j数据库URI'
    )
    
    parser.add_argument(
        '--neo4j-user',
        type=str,
        default='neo4j',
        help='Neo4j用户名'
    )
    
    parser.add_argument(
        '--neo4j-password',
        type=str,
        default='password',
        help='Neo4j密码'
    )
    
    args = parser.parse_args()
    
    log_message("=" * 70)
    log_message("🌾 WheatAgent 模型训练启动")
    log_message("=" * 70)
    log_message(f"训练阶段: {args.stage}")
    log_message(f"训练轮数: {args.epochs}")
    log_message(f"批次大小: {args.batch_size}")
    log_message(f"训练设备: {args.device}")
    
    # 执行训练
    results = {}
    
    if args.stage in ['all', 'yolo']:
        results['yolo'] = train_yolo(args)
    
    if args.stage in ['all', 'agri_llava']:
        results['agri_llava'] = train_agri_llava(args)
    
    if args.stage in ['all', 'knowledge_graph']:
        results['knowledge_graph'] = build_knowledge_graph(args)
    
    if args.stage == 'mock':
        results['mock'] = create_mock_models()
    
    # 打印总结
    log_message("=" * 70)
    log_message("训练总结")
    log_message("=" * 70)
    
    for stage, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        log_message(f"{stage}: {status}")
    
    all_success = all(results.values())
    
    if all_success:
        log_message("✅ 所有训练任务完成！")
        return 0
    else:
        log_message("⚠️ 部分训练任务失败", "WARNING")
        return 1


if __name__ == "__main__":
    sys.exit(main())

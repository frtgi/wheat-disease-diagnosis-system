# -*- coding: utf-8 -*-
"""
模型验证与知识图谱同步脚本

验证模型性能并同步更新知识图谱
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def validate_model():
    """验证模型性能"""
    print("=" * 60)
    print("模型验证")
    print("=" * 60)
    
    try:
        from ultralytics import YOLO
        import torch
    except ImportError as e:
        print(f"导入错误: {e}")
        return None
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n设备: {device}")
    
    # 加载模型
    model_path = PROJECT_ROOT / "models" / "yolov8_wheat.pt"
    if not model_path.exists():
        print(f"模型不存在: {model_path}")
        return None
    
    print(f"加载模型: {model_path}")
    model = YOLO(str(model_path))
    
    # 验证
    config_path = PROJECT_ROOT / "configs" / "wheat_disease.yaml"
    
    print("\n开始验证...")
    try:
        results = model.val(
            data=str(config_path),
            device=device,
            batch=8,
            imgsz=640,
            verbose=True
        )
        
        print(f"\n验证结果:")
        print(f"  mAP@0.5: {results.box.map50:.4f}")
        print(f"  mAP@0.5:0.95: {results.box.map:.4f}")
        print(f"  Precision: {results.box.mp:.4f}")
        print(f"  Recall: {results.box.mr:.4f}")
        
        return {
            "map50": float(results.box.map50),
            "map": float(results.box.map),
            "precision": float(results.box.mp),
            "recall": float(results.box.mr)
        }
        
    except Exception as e:
        print(f"验证错误: {e}")
        return None


def sync_knowledge_graph(validation_results):
    """同步更新知识图谱"""
    print("\n" + "=" * 60)
    print("知识图谱同步更新")
    print("=" * 60)
    
    kg_path = PROJECT_ROOT / "checkpoints" / "knowledge_graph"
    entities_file = kg_path / "entities.json"
    
    if not entities_file.exists():
        print(f"知识图谱不存在: {entities_file}")
        return
    
    with open(entities_file, "r", encoding="utf-8") as f:
        entities = json.load(f)
    
    # 更新版本信息
    version_file = kg_path / "VERSION.md"
    if version_file.exists():
        with open(version_file, "r", encoding="utf-8") as f:
            version_content = f.read()
        
        # 添加验证结果
        if validation_results:
            update_section = f"""

## 验证结果 ({datetime.now().strftime("%Y-%m-%d")})

| 指标 | 数值 |
|------|------|
| mAP@0.5 | {validation_results['map50']:.4f} |
| mAP@0.5:0.95 | {validation_results['map']:.4f} |
| Precision | {validation_results['precision']:.4f} |
| Recall | {validation_results['recall']:.4f} |
"""
            version_content += update_section
            
            with open(version_file, "w", encoding="utf-8") as f:
                f.write(version_content)
            
            print(f"版本信息已更新: {version_file}")
    
    # 更新实体置信度（示例）
    print(f"\n知识图谱状态:")
    print(f"  实体数量: {len(entities)}")
    
    entity_types = {}
    for entity in entities.values():
        entity_type = entity.get("type", "Unknown")
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
    
    print(f"  实体类型分布:")
    for t, count in sorted(entity_types.items()):
        print(f"    {t}: {count}")
    
    return entities


def main():
    """主函数"""
    # 验证模型
    validation_results = validate_model()
    
    # 同步知识图谱
    sync_knowledge_graph(validation_results)
    
    # 保存结果
    if validation_results:
        results_path = PROJECT_ROOT / "logs" / "validation_results.json"
        results_path.parent.mkdir(exist_ok=True)
        
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "validation": validation_results
        }
        
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n验证结果已保存: {results_path}")
    
    print("\n" + "=" * 60)
    print("验证与同步完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

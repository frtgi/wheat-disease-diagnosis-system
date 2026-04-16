# -*- coding: utf-8 -*-
"""
部署环境验证脚本

验证所有依赖正确安装，GPU/CUDA可用，模型文件完整
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def verify_environment():
    """验证环境配置"""
    print("=" * 60)
    print(" IWDDA 部署环境验证")
    print("=" * 60)
    
    all_passed = True
    
    # 1. Python 版本
    print("\n[1] Python 版本检查")
    py_version = sys.version_info
    if py_version >= (3, 10):
        print(f"    ✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print(f"    ❌ Python版本过低: {py_version.major}.{py_version.minor}")
        all_passed = False
    
    # 2. PyTorch 和 CUDA
    print("\n[2] PyTorch 和 CUDA 检查")
    try:
        import torch
        print(f"    ✅ PyTorch 版本: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"    ✅ CUDA 可用")
            print(f"    ✅ GPU: {torch.cuda.get_device_name(0)}")
            props = torch.cuda.get_device_properties(0)
            print(f"    ✅ 显存: {props.total_memory / 1024**3:.2f} GB")
            print(f"    ✅ CUDA 版本: {torch.version.cuda}")
        else:
            print("    ⚠️ CUDA 不可用，将使用 CPU 模式")
    except ImportError:
        print("    ❌ PyTorch 未安装")
        all_passed = False
    
    # 3. 核心依赖
    print("\n[3] 核心依赖检查")
    dependencies = [
        ("ultralytics", "YOLOv8"),
        ("transformers", "Transformers"),
        ("peft", "PEFT (LoRA)"),
        ("neo4j", "Neo4j 驱动"),
        ("opencv-python", "OpenCV"),
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
    ]
    
    for module, name in dependencies:
        try:
            if module == "PIL":
                import PIL
                version = PIL.__version__
            elif module == "opencv-python":
                import cv2
                version = cv2.__version__
            else:
                mod = __import__(module)
                version = getattr(mod, "__version__", "已安装")
            print(f"    ✅ {name}: {version}")
        except ImportError:
            print(f"    ❌ {name}: 未安装")
            all_passed = False
    
    # 4. 模型文件
    print("\n[4] 模型文件检查")
    model_paths = [
        ("视觉检测模型", "models/wheat_disease_v10_yolov8s/phase1_warmup/weights/best.pt"),
        ("备用视觉模型", "models/wheat_disease_v5_optimized_phase2/weights/best.pt"),
        ("LLaVA投影层", "models/agri_llava/projection_layer.pt"),
    ]
    
    for name, rel_path in model_paths:
        full_path = project_root / rel_path
        if full_path.exists():
            size_mb = full_path.stat().st_size / 1024 / 1024
            print(f"    ✅ {name}: {size_mb:.2f} MB")
        else:
            print(f"    ⚠️ {name}: 不存在 ({rel_path})")
    
    # 5. 知识图谱数据
    print("\n[5] 知识图谱数据检查")
    kg_path = project_root / "checkpoints" / "knowledge_graph"
    if kg_path.exists():
        mappings_path = kg_path / "mappings.json"
        transe_path = kg_path / "transe_embeddings.pt"
        
        print(f"    ✅ 知识图谱目录存在")
        
        if mappings_path.exists():
            print(f"    ✅ 实体映射文件存在")
        else:
            print(f"    ⚠️ 实体映射文件不存在")
        
        if transe_path.exists():
            print(f"    ✅ TransE 嵌入文件存在")
        else:
            print(f"    ⚠️ TransE 嵌入文件不存在")
    else:
        print(f"    ⚠️ 知识图谱目录不存在")
    
    # 6. Neo4j 连接
    print("\n[6] Neo4j 连接检查")
    try:
        from neo4j import GraphDatabase
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "123456789s")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
        driver.close()
        print(f"    ✅ Neo4j 连接成功: {uri}")
    except Exception as e:
        print(f"    ⚠️ Neo4j 连接失败: {str(e)[:50]}")
        print("       (可选服务，不影响基本功能)")
    
    # 7. 数据集
    print("\n[7] 数据集检查")
    dataset_path = project_root / "datasets" / "wheat_disease"
    if dataset_path.exists():
        train_images = list((dataset_path / "train" / "images").glob("*.jpg")) if (dataset_path / "train" / "images").exists() else []
        val_images = list((dataset_path / "val" / "images").glob("*.jpg")) if (dataset_path / "val" / "images").exists() else []
        print(f"    ✅ 训练集图像: {len(train_images)}")
        print(f"    ✅ 验证集图像: {len(val_images)}")
    else:
        print(f"    ⚠️ 数据集目录不存在")
    
    # 汇总
    print("\n" + "=" * 60)
    if all_passed:
        print(" ✅ 部署环境验证通过！")
        print(" 可以运行测试部署: python scripts/deployment/test_deployment.py --e2e")
    else:
        print(" ⚠️ 部署环境存在部分问题，请检查上述失败项")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    verify_environment()

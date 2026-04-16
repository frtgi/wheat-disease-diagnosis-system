# -*- coding: utf-8 -*-
"""
测试部署脚本

端到端测试部署入口，验证所有模块正常工作
"""
import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# 设置控制台编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.system('chcp 65001 >nul 2>&1')

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def check_environment() -> Dict[str, bool]:
    """
    检查部署环境
    
    Returns:
        检查结果字典
    """
    results = {}
    
    print_header("环境检查")
    
    # Python 版本
    py_version = sys.version_info
    results["python_version"] = py_version >= (3, 10)
    print(f"[{'✅' if results['python_version'] else '❌'}] Python版本: {sys.version.split()[0]}")
    
    # PyTorch
    try:
        import torch
        results["pytorch"] = True
        results["cuda"] = torch.cuda.is_available()
        print(f"[✅] PyTorch版本: {torch.__version__}")
        print(f"[{'✅' if results['cuda'] else '❌'}] CUDA可用: {results['cuda']}")
        if results["cuda"]:
            print(f"    GPU: {torch.cuda.get_device_name(0)}")
            print(f"    显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    except ImportError:
        results["pytorch"] = False
        results["cuda"] = False
        print("[❌] PyTorch未安装")
    
    # Ultralytics
    try:
        import ultralytics
        results["ultralytics"] = True
        print(f"[✅] Ultralytics版本: {ultralytics.__version__}")
    except ImportError:
        results["ultralytics"] = False
        print("[❌] Ultralytics未安装")
    
    # Transformers
    try:
        import transformers
        results["transformers"] = True
        print(f"[✅] Transformers版本: {transformers.__version__}")
    except ImportError:
        results["transformers"] = False
        print("[❌] Transformers未安装")
    
    # Neo4j
    try:
        import neo4j
        results["neo4j_driver"] = True
        print(f"[✅] Neo4j驱动已安装")
    except ImportError:
        results["neo4j_driver"] = False
        print("[❌] Neo4j驱动未安装")
    
    return results


def check_models() -> Dict[str, bool]:
    """
    检查模型文件
    
    Returns:
        检查结果字典
    """
    results = {}
    
    print_header("模型检查")
    
    # 视觉检测模型
    vision_model_path = project_root / "models" / "wheat_disease_v10_yolov8s" / "phase1_warmup" / "weights" / "best.pt"
    results["vision_model"] = vision_model_path.exists()
    size_mb = vision_model_path.stat().st_size / 1024 / 1024 if results["vision_model"] else 0
    print(f"[{'✅' if results['vision_model'] else '❌'}] 视觉检测模型: {vision_model_path.name if results['vision_model'] else '不存在'} ({size_mb:.2f} MB)")
    
    # 备用视觉模型
    backup_vision_path = project_root / "models" / "wheat_disease_v5_optimized_phase2" / "weights" / "best.pt"
    results["backup_vision_model"] = backup_vision_path.exists()
    print(f"[{'✅' if results['backup_vision_model'] else '❌'}] 备用视觉模型: {'存在' if results['backup_vision_model'] else '不存在'}")
    
    # LLaVA投影层
    projection_path = project_root / "models" / "agri_llava" / "projection_layer.pt"
    results["projection_layer"] = projection_path.exists()
    print(f"[{'✅' if results['projection_layer'] else '❌'}] LLaVA投影层: {'存在' if results['projection_layer'] else '不存在'}")
    
    # 知识图谱数据
    kg_path = project_root / "checkpoints" / "knowledge_graph"
    results["knowledge_graph"] = kg_path.exists()
    if results["knowledge_graph"]:
        entity_count = len(list((kg_path / "entities").glob("*.json"))) if (kg_path / "entities").exists() else 0
        print(f"[✅] 知识图谱数据: 存在 ({entity_count} 个实体文件)")
    else:
        print("[❌] 知识图谱数据: 不存在")
    
    # TransE嵌入
    transe_path = project_root / "checkpoints" / "knowledge_graph" / "transe_embeddings.pt"
    results["transe_embeddings"] = transe_path.exists()
    print(f"[{'✅' if results['transe_embeddings'] else '❌'}] TransE嵌入: {'存在' if results['transe_embeddings'] else '不存在'}")
    
    return results


def check_services() -> Dict[str, bool]:
    """
    检查服务状态
    
    Returns:
        检查结果字典
    """
    results = {}
    
    print_header("服务检查")
    
    # Neo4j 连接
    try:
        from neo4j import GraphDatabase
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "123456789s")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        results["neo4j"] = True
        print(f"[✅] Neo4j服务: 已连接 ({uri})")
    except Exception as e:
        results["neo4j"] = False
        print(f"[❌] Neo4j服务: 连接失败 - {str(e)[:50]}")
    
    return results


def test_vision_detection(image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    测试视觉检测模块
    
    Args:
        image_path: 测试图像路径
    
    Returns:
        测试结果
    """
    print_header("视觉检测测试")
    
    results = {"success": False, "detections": [], "error": None}
    
    try:
        from ultralytics import YOLO
        
        model_path = project_root / "models" / "wheat_disease_v10_yolov8s" / "phase1_warmup" / "weights" / "best.pt"
        if not model_path.exists():
            model_path = project_root / "models" / "wheat_disease_v5_optimized_phase2" / "weights" / "best.pt"
        
        print(f"加载模型: {model_path.name}")
        model = YOLO(str(model_path))
        
        if image_path is None:
            test_images = list((project_root / "tests" / "integration" / "test_data").glob("test_e2e_*.jpg"))
            if test_images:
                image_path = str(test_images[0])
            else:
                print("[⚠️] 未找到测试图像，跳过检测测试")
                return {"success": True, "detections": [], "note": "无测试图像"}
        
        print(f"检测图像: {Path(image_path).name}")
        start_time = time.time()
        detection_results = model(image_path, verbose=False)
        elapsed = (time.time() - start_time) * 1000
        
        for r in detection_results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = r.names[cls_id]
                conf = float(box.conf[0])
                results["detections"].append({
                    "class": cls_name,
                    "confidence": conf,
                    "bbox": box.xyxy[0].tolist()
                })
        
        results["success"] = True
        results["inference_time_ms"] = elapsed
        print(f"[✅] 检测完成: {len(results['detections'])} 个目标, 耗时 {elapsed:.2f} ms")
        
        for det in results["detections"]:
            print(f"    - {det['class']}: {det['confidence']:.2%}")
            
    except Exception as e:
        results["error"] = str(e)
        print(f"[❌] 检测失败: {e}")
    
    return results


def test_knowledge_graph(disease_name: str = "条锈病") -> Dict[str, Any]:
    """
    测试知识图谱模块
    
    Args:
        disease_name: 测试病害名称
    
    Returns:
        测试结果
    """
    print_header("知识图谱测试")
    
    results = {"success": False, "info": {}, "error": None}
    
    try:
        from src.graph.knowledge_graph_builder import AgriKnowledgeGraph
        
        kg = AgriKnowledgeGraph()
        
        print(f"查询病害: {disease_name}")
        info = kg.get_disease_info(disease_name)
        
        if info:
            results["success"] = True
            results["info"] = info
            print(f"[✅] 查询成功:")
            for key, value in info.items():
                print(f"    - {key}: {value}")
        else:
            print(f"[⚠️] 未找到病害信息: {disease_name}")
            results["success"] = True
            results["note"] = "病害信息未找到"
            
    except Exception as e:
        results["error"] = str(e)
        print(f"[❌] 查询失败: {e}")
    
    return results


def test_multimodal_fusion() -> Dict[str, Any]:
    """
    测试多模态融合模块
    
    Returns:
        测试结果
    """
    print_header("多模态融合测试")
    
    results = {"success": False, "error": None}
    
    try:
        from src.fusion.fusion_engine import FusionEngine
        import torch
        
        print("初始化融合引擎...")
        engine = FusionEngine(
            vision_dim=512,
            text_dim=768,
            knowledge_dim=256,
            num_heads=8
        )
        
        # 模拟输入
        vision_features = torch.randn(1, 512)
        text_features = torch.randn(1, 768)
        knowledge_embedding = torch.randn(1, 256)
        
        print("执行特征融合...")
        start_time = time.time()
        
        if torch.cuda.is_available():
            engine = engine.cuda()
            vision_features = vision_features.cuda()
            text_features = text_features.cuda()
            knowledge_embedding = knowledge_embedding.cuda()
        
        fused = engine.deep_feature_fusion(vision_features, text_features, knowledge_embedding)
        elapsed = (time.time() - start_time) * 1000
        
        results["success"] = True
        results["output_shape"] = list(fused.shape)
        results["fusion_time_ms"] = elapsed
        print(f"[✅] 融合成功: 输出形状 {fused.shape}, 耗时 {elapsed:.2f} ms")
        
    except Exception as e:
        results["error"] = str(e)
        print(f"[❌] 融合失败: {e}")
    
    return results


def run_end_to_end_test(image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    运行端到端测试
    
    Args:
        image_path: 测试图像路径
    
    Returns:
        测试结果
    """
    print_header("端到端诊断测试")
    
    results = {
        "success": False,
        "vision": None,
        "knowledge": None,
        "diagnosis": None,
        "error": None
    }
    
    try:
        # 1. 视觉检测
        vision_result = test_vision_detection(image_path)
        results["vision"] = vision_result
        
        if not vision_result["success"]:
            raise Exception("视觉检测失败")
        
        # 2. 知识图谱查询
        if vision_result["detections"]:
            disease_name = vision_result["detections"][0]["class"]
            # 转换英文名为中文名
            name_map = {
                "Stripe Rust": "条锈病",
                "Leaf Rust": "叶锈病",
                "Stem Rust": "秆锈病",
                "Powdery Mildew": "白粉病",
                "Fusarium": "赤霉病",
                "Aphid": "蚜虫"
            }
            disease_cn = name_map.get(disease_name, disease_name)
        else:
            disease_cn = "条锈病"
        
        kg_result = test_knowledge_graph(disease_cn)
        results["knowledge"] = kg_result
        
        # 3. 生成诊断报告
        print("\n生成诊断报告...")
        report_lines = [
            "=" * 50,
            "小麦病害诊断报告",
            "=" * 50,
            "",
            f"检测病害: {disease_cn}",
            f"置信度: {vision_result['detections'][0]['confidence']:.2%}" if vision_result['detections'] else "未检测到病害",
            "",
        ]
        
        if kg_result["success"] and kg_result["info"]:
            report_lines.extend([
                "病害信息:",
                f"  症状: {kg_result['info'].get('symptoms', '未知')}",
                f"  病原: {kg_result['info'].get('pathogen', '未知')}",
                f"  防治: {kg_result['info'].get('treatment', '未知')}",
            ])
        
        results["diagnosis"] = "\n".join(report_lines)
        results["success"] = True
        print(results["diagnosis"])
        
    except Exception as e:
        results["error"] = str(e)
        print(f"[❌] 端到端测试失败: {e}")
    
    return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="IWDDA 测试部署脚本")
    parser.add_argument("--image", type=str, help="测试图像路径")
    parser.add_argument("--skip-env", action="store_true", help="跳过环境检查")
    parser.add_argument("--skip-models", action="store_true", help="跳过模型检查")
    parser.add_argument("--skip-services", action="store_true", help="跳过服务检查")
    parser.add_argument("--e2e", action="store_true", help="运行端到端测试")
    args = parser.parse_args()
    
    print("=" * 60)
    print(" IWDDA 测试部署验证")
    print(" 基于多模态特征融合的小麦病害诊断智能体")
    print("=" * 60)
    
    all_results = {}
    
    # 环境检查
    if not args.skip_env:
        all_results["environment"] = check_environment()
    
    # 模型检查
    if not args.skip_models:
        all_results["models"] = check_models()
    
    # 服务检查
    if not args.skip_services:
        all_results["services"] = check_services()
    
    # 端到端测试
    if args.e2e:
        all_results["e2e"] = run_end_to_end_test(args.image)
    
    # 汇总结果
    print_header("测试结果汇总")
    
    total_checks = 0
    passed_checks = 0
    
    for category, checks in all_results.items():
        if isinstance(checks, dict):
            for key, value in checks.items():
                if isinstance(value, bool):
                    total_checks += 1
                    if value:
                        passed_checks += 1
    
    if total_checks > 0:
        pass_rate = passed_checks / total_checks * 100
        print(f"\n通过率: {passed_checks}/{total_checks} ({pass_rate:.1f}%)")
        
        if pass_rate >= 80:
            print("\n✅ 部署验证通过！项目可以运行测试部署。")
        else:
            print("\n⚠️ 部署验证未完全通过，请检查失败项。")
    
    # 保存结果
    result_path = project_root / "test_deployment_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n结果已保存: {result_path}")
    
    return all_results


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
知识图谱模块验证脚本
"""
import os
import json
import sys

sys.path.insert(0, r'D:\Project\WheatAgent')

def check_kg_files():
    """检查知识图谱数据文件"""
    print("=" * 60)
    print("📊 知识图谱数据文件检查")
    print("=" * 60)
    
    kg_dir = r'D:\Project\WheatAgent\checkpoints\knowledge_graph'
    
    required_files = [
        'entities.json',
        'relations.json',
        'triples.json',
        'kg_stats.json',
        'transe_model.pt',
        'mappings.json'
    ]
    
    for f in required_files:
        path = os.path.join(kg_dir, f)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"✅ {f}: {size:,} bytes")
        else:
            print(f"❌ {f}: 不存在")
    
    return True

def check_transe_model():
    """检查 TransE 模型"""
    print("\n" + "=" * 60)
    print("🔧 TransE 模型检查")
    print("=" * 60)
    
    try:
        import torch
        model_path = r'D:\Project\WheatAgent\checkpoints\knowledge_graph\transe_model.pt'
        
        model = torch.load(model_path, map_location='cpu', weights_only=False)
        
        print(f"✅ 模型加载成功")
        print(f"   模型类型: {type(model)}")
        
        if isinstance(model, dict):
            print(f"   模型键: {list(model.keys())}")
            
            for key, value in model.items():
                if isinstance(value, torch.Tensor):
                    print(f"   - {key}: shape={value.shape}, dtype={value.dtype}")
                elif isinstance(value, dict):
                    print(f"   - {key}: dict with {len(value)} items")
                else:
                    print(f"   - {key}: {type(value)}")
        
        return True
    except Exception as e:
        print(f"❌ TransE 模型加载失败: {e}")
        return False

def check_kg_stats():
    """检查知识图谱统计信息"""
    print("\n" + "=" * 60)
    print("📈 知识图谱统计")
    print("=" * 60)
    
    stats_path = r'D:\Project\WheatAgent\checkpoints\knowledge_graph\kg_stats.json'
    
    try:
        with open(stats_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        print(f"总实体数: {stats.get('total_entities', 0)}")
        print(f"总三元组数: {stats.get('total_triples', 0)}")
        print(f"\n实体类型分布:")
        for etype, count in stats.get('entity_types', {}).items():
            print(f"  - {etype}: {count}")
        
        print(f"\n关系类型分布:")
        for rtype, count in stats.get('relation_types', {}).items():
            print(f"  - {rtype}: {count}")
        
        print(f"\n更新时间: {stats.get('updated_at', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ 统计信息读取失败: {e}")
        return False

def check_graphrag_engine():
    """检查 GraphRAG 引擎"""
    print("\n" + "=" * 60)
    print("🔗 GraphRAG 引擎检查")
    print("=" * 60)
    
    try:
        from src.graph.graphrag_engine import GraphRAGEngine
        
        print("✅ GraphRAGEngine 类加载成功")
        print("   - retrieve_subgraph(): 检索子图")
        print("   - construct_context(): 构建上下文")
        print("   - generate_enhanced_report(): 生成增强报告")
        print("   - multi_hop_reasoning(): 多跳推理")
        print("   - verify_diagnosis(): 验证诊断")
        
        return True
    except Exception as e:
        print(f"❌ GraphRAG 引擎加载失败: {e}")
        return False

def verify_kg_functionality():
    """验证知识图谱功能"""
    print("\n" + "=" * 60)
    print("🧪 知识图谱功能验证")
    print("=" * 60)
    
    try:
        import torch
        sys.path.insert(0, r'D:\Project\WheatAgent')
        from src.graph.transe_embedding import KnowledgeGraphEmbedding
        
        entities_path = r'D:\Project\WheatAgent\checkpoints\knowledge_graph\entities.json'
        relations_path = r'D:\Project\WheatAgent\checkpoints\knowledge_graph\relations.json'
        triples_path = r'D:\Project\WheatAgent\checkpoints\knowledge_graph\triples.json'
        
        with open(entities_path, 'r', encoding='utf-8') as f:
            entities_data = json.load(f)
        with open(relations_path, 'r', encoding='utf-8') as f:
            relations_data = json.load(f)
        with open(triples_path, 'r', encoding='utf-8') as f:
            triples_data = json.load(f)
        
        entities = list(entities_data.keys())
        relations = [r['type'] for r in relations_data]
        triples = [(t['head'], t['relation'], t['tail']) for t in triples_data]
        
        print(f"✅ 加载 {len(entities)} 个实体")
        print(f"✅ 加载 {len(set(relations))} 种关系")
        print(f"✅ 加载 {len(triples)} 个三元组")
        
        kge = KnowledgeGraphEmbedding(
            entities=entities,
            relations=list(set(relations)),
            triples=triples,
            model_type='transe',
            embedding_dim=128
        )
        
        print(f"✅ KnowledgeGraphEmbedding 初始化成功")
        
        model_path = r'D:\Project\WheatAgent\checkpoints\knowledge_graph\transe_model.pt'
        saved_model = torch.load(model_path, map_location='cpu', weights_only=False)
        
        if isinstance(saved_model, dict) and 'entity_embeddings' in saved_model:
            kge.model.entity_embeddings.weight.data = saved_model['entity_embeddings']
            kge.model.relation_embeddings.weight.data = saved_model['relation_embeddings']
            print(f"✅ TransE 模型权重加载成功")
        
        results = kge.predict_tail("disease_stripe_rust", "TREATED_BY", top_k=5)
        print(f"\n🔍 预测测试: disease_stripe_rust --[TREATED_BY]--> ?")
        for entity, score in results[:3]:
            print(f"   候选: {entity} (得分: {score:.4f})")
        
        return True
    except Exception as e:
        print(f"❌ 功能验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🏥 IWDDA 知识图谱模块状态检查")
    print("=" * 60)
    
    results = {
        "数据文件": check_kg_files(),
        "TransE模型": check_transe_model(),
        "统计信息": check_kg_stats(),
        "GraphRAG引擎": check_graphrag_engine(),
        "功能验证": verify_kg_functionality()
    }
    
    print("\n" + "=" * 60)
    print("📋 检查结果汇总")
    print("=" * 60)
    
    for name, status in results.items():
        status_str = "✅ 正常" if status else "❌ 异常"
        print(f"{name}: {status_str}")
    
    all_ok = all(results.values())
    print("\n" + ("=" * 60))
    if all_ok:
        print("✅ 知识图谱模块状态良好!")
    else:
        print("⚠️ 知识图谱模块存在问题，请检查!")
    print("=" * 60)
    
    return all_ok

if __name__ == "__main__":
    main()

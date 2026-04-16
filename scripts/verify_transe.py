# -*- coding: utf-8 -*-
"""
验证TransE嵌入模型
"""
import torch
from pathlib import Path

def verify_transe_model():
    """验证TransE模型"""
    model_path = Path(__file__).parent.parent / "checkpoints" / "knowledge_graph" / "transe_model.pt"
    
    if not model_path.exists():
        print(f"错误: 模型文件不存在: {model_path}")
        return False
    
    model = torch.load(model_path, weights_only=False)
    
    print("=" * 60)
    print("TransE嵌入模型验证")
    print("=" * 60)
    print(f"实体数量: {model['num_entities']}")
    print(f"关系数量: {model['num_relations']}")
    print(f"嵌入维度: {model['embedding_dim']}")
    print(f"实体映射数量: {len(model['entity2id'])}")
    print(f"关系映射数量: {len(model['relation2id'])}")
    
    entity_emb = model['model_state_dict']['entity_embeddings.weight']
    relation_emb = model['model_state_dict']['relation_embeddings.weight']
    
    print(f"实体嵌入形状: {entity_emb.shape}")
    print(f"关系嵌入形状: {relation_emb.shape}")
    
    print("\n实体类型统计:")
    entity_types = {}
    for entity_id in model['entity2id'].keys():
        entity_type = entity_id.split('_')[0]
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
    
    for etype, count in sorted(entity_types.items(), key=lambda x: -x[1]):
        print(f"  {etype}: {count}")
    
    print("\n关系类型:")
    for rel_id, rel_idx in sorted(model['relation2id'].items(), key=lambda x: x[1]):
        print(f"  {rel_idx}: {rel_id}")
    
    print("\n验证结果:")
    if model['num_entities'] == 106:
        print("  ✓ 实体数量正确 (106)")
    else:
        print(f"  ✗ 实体数量不正确 (期望106, 实际{model['num_entities']})")
    
    if model['num_relations'] == 15:
        print("  ✓ 关系数量正确 (15)")
    else:
        print(f"  ✗ 关系数量不正确 (期望15, 实际{model['num_relations']})")
    
    if entity_emb.shape == (106, 100):
        print("  ✓ 实体嵌入形状正确 (106, 100)")
    else:
        print(f"  ✗ 实体嵌入形状不正确 (期望(106, 100), 实际{entity_emb.shape})")
    
    print("=" * 60)
    return True

if __name__ == "__main__":
    verify_transe_model()

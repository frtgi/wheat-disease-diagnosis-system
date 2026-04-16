# -*- coding: utf-8 -*-
"""TransE模型详细检查脚本"""
import torch

state = torch.load('checkpoints/knowledge_graph/transe_model.pt', map_location='cpu', weights_only=False)

print('=' * 60)
print('TransE 模型详细分析')
print('=' * 60)

print('\n模型文件顶层键:', list(state.keys()))

if 'model_state_dict' in state:
    model_state = state['model_state_dict']
    print('\n模型状态字典键:', list(model_state.keys()))
    
    for key, value in model_state.items():
        if hasattr(value, 'shape'):
            print(f'\n{key}:')
            print(f'  形状: {list(value.shape)}')
            print(f'  数据类型: {value.dtype}')
            print(f'  值范围: [{value.min().item():.6f}, {value.max().item():.6f}]')
            print(f'  均值: {value.mean().item():.6f}')
            print(f'  标准差: {value.std().item():.6f}')

print('\n模型元数据:')
print(f'  嵌入维度: {state.get("embedding_dim", "N/A")}')
print(f'  实体数量: {state.get("num_entities", "N/A")}')
print(f'  关系数量: {state.get("num_relations", "N/A")}')

if 'model_state_dict' in state:
    model_state = state['model_state_dict']
    
    if 'entity_embeddings.weight' in model_state:
        entity_emb = model_state['entity_embeddings.weight']
        print('\n实体嵌入质量分析:')
        print(f'  实体数量: {entity_emb.shape[0]}')
        print(f'  嵌入维度: {entity_emb.shape[1]}')
        
        norms = torch.norm(entity_emb, dim=1)
        print(f'  L2范数范围: [{norms.min().item():.4f}, {norms.max().item():.4f}]')
        print(f'  L2范数均值: {norms.mean().item():.4f}')
        
        if norms.mean().item() > 0.9 and norms.mean().item() < 1.1:
            print('  ✅ 实体嵌入已归一化 (L2范数接近1)')
        else:
            print('  ⚠️ 实体嵌入未完全归一化')

    if 'relation_embeddings.weight' in model_state:
        rel_emb = model_state['relation_embeddings.weight']
        print('\n关系嵌入质量分析:')
        print(f'  关系数量: {rel_emb.shape[0]}')
        print(f'  嵌入维度: {rel_emb.shape[1]}')
        
        norms = torch.norm(rel_emb, dim=1)
        print(f'  L2范数范围: [{norms.min().item():.4f}, {norms.max().item():.4f}]')
        print(f'  L2范数均值: {norms.mean().item():.4f}')

print('\n' + '=' * 60)

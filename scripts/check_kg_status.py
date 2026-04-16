# -*- coding: utf-8 -*-
"""
知识图谱模块状态检查脚本

检查项目:
1. Neo4j连接状态和配置
2. TransE嵌入模型质量
3. 知识图谱数据统计
4. 数据完整性检查
"""
import os
import json
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)


def check_neo4j():
    """检查Neo4j连接状态"""
    print('\n[1] Neo4j 连接状态检查')
    print('-' * 50)
    
    try:
        from neo4j import GraphDatabase
        print('  ✅ neo4j 库已安装')
        
        uri = 'bolt://localhost:7687'
        user = 'neo4j'
        password = '123456789s'
        
        print(f'  URI: {uri}')
        print(f'  用户: {user}')
        
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                result = session.run('RETURN 1 as test')
                result.single()
            print('  ✅ Neo4j 连接成功!')
            
            with driver.session() as session:
                node_result = session.run('MATCH (n) RETURN count(n) as count')
                node_count = node_result.single()['count']
                
                rel_result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
                rel_count = rel_result.single()['count']
                
                print(f'  节点数量: {node_count}')
                print(f'  关系数量: {rel_count}')
                
                label_result = session.run('''
                    MATCH (n)
                    RETURN labels(n)[0] as label, count(n) as count
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                print('  节点类型分布 (Top 10):')
                for record in label_result:
                    print(f'    - {record["label"]}: {record["count"]}')
            
            driver.close()
            return 'connected', {'nodes': node_count, 'relations': rel_count}
            
        except Exception as e:
            print(f'  ❌ Neo4j 连接失败: {e}')
            return 'disconnected', {'error': str(e)}
            
    except ImportError:
        print('  ⚠️ neo4j 库未安装')
        return 'not_installed', {}


def check_transe():
    """检查TransE嵌入模型"""
    print('\n[2] TransE 嵌入模型检查')
    print('-' * 50)
    
    transe_path = 'checkpoints/knowledge_graph/transe_model.pt'
    if not os.path.exists(transe_path):
        print(f'  ❌ 模型文件不存在: {transe_path}')
        return 'not_found', {}
    
    print(f'  ✅ 模型文件存在: {transe_path}')
    
    import torch
    try:
        state_dict = torch.load(transe_path, map_location='cpu', weights_only=True)
        
        print('  模型参数:')
        for key, value in state_dict.items():
            if hasattr(value, 'shape'):
                print(f'    - {key}: shape={list(value.shape)}, dtype={value.dtype}')
        
        result = {}
        
        if 'entity_embeddings.weight' in state_dict:
            entity_emb = state_dict['entity_embeddings.weight']
            print(f'\n  实体嵌入分析:')
            print(f'    - 实体数量: {entity_emb.shape[0]}')
            print(f'    - 嵌入维度: {entity_emb.shape[1]}')
            print(f'    - 值范围: [{entity_emb.min().item():.4f}, {entity_emb.max().item():.4f}]')
            print(f'    - 均值: {entity_emb.mean().item():.4f}')
            print(f'    - 标准差: {entity_emb.std().item():.4f}')
            
            norms = torch.norm(entity_emb, dim=1)
            print(f'    - 嵌入范数范围: [{norms.min().item():.4f}, {norms.max().item():.4f}]')
            
            result['entity_count'] = entity_emb.shape[0]
            result['embedding_dim'] = entity_emb.shape[1]
            result['entity_emb_mean'] = entity_emb.mean().item()
            result['entity_emb_std'] = entity_emb.std().item()
            
        if 'relation_embeddings.weight' in state_dict:
            rel_emb = state_dict['relation_embeddings.weight']
            print(f'\n  关系嵌入分析:')
            print(f'    - 关系数量: {rel_emb.shape[0]}')
            print(f'    - 嵌入维度: {rel_emb.shape[1]}')
            print(f'    - 值范围: [{rel_emb.min().item():.4f}, {rel_emb.max().item():.4f}]')
            print(f'    - 均值: {rel_emb.mean().item():.4f}')
            print(f'    - 标准差: {rel_emb.std().item():.4f}')
            
            result['relation_count'] = rel_emb.shape[0]
            result['relation_emb_mean'] = rel_emb.mean().item()
            result['relation_emb_std'] = rel_emb.std().item()
        
        return 'loaded', result
        
    except Exception as e:
        print(f'  ❌ 模型加载失败: {e}')
        return 'error', {'error': str(e)}


def check_kg_stats():
    """检查知识图谱统计信息"""
    print('\n[3] 知识图谱数据统计')
    print('-' * 50)
    
    kg_dir = 'checkpoints/knowledge_graph'
    stats_file = os.path.join(kg_dir, 'kg_stats.json')
    
    if not os.path.exists(stats_file):
        print(f'  ❌ 统计文件不存在: {stats_file}')
        return {}
    
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    print(f'  原始实体数: {stats.get("original_entities", 0)}')
    print(f'  原始三元组数: {stats.get("original_triples", 0)}')
    print(f'  新增实体数: {stats.get("new_entities", 0)}')
    print(f'  新增三元组数: {stats.get("new_triples", 0)}')
    print(f'  总实体数: {stats.get("total_entities", 0)}')
    print(f'  总三元组数: {stats.get("total_triples", 0)}')
    print(f'  更新时间: {stats.get("updated_at", "N/A")}')
    
    print('\n  实体类型分布:')
    entity_types = stats.get('entity_types', {})
    for etype, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
        print(f'    - {etype}: {count}')
    
    print('\n  关系类型分布:')
    relation_types = stats.get('relation_types', {})
    for rtype, count in sorted(relation_types.items(), key=lambda x: x[1], reverse=True):
        print(f'    - {rtype}: {count}')
    
    return stats


def check_data_integrity():
    """检查数据完整性"""
    print('\n[4] 数据完整性检查')
    print('-' * 50)
    
    kg_dir = 'checkpoints/knowledge_graph'
    
    files_to_check = [
        'entities.json',
        'relations.json', 
        'triples.json',
        'mappings.json',
        'transe_model.pt',
        'kg_stats.json',
        'VERSION.md'
    ]
    
    results = {}
    
    for fname in files_to_check:
        fpath = os.path.join(kg_dir, fname)
        if os.path.exists(fpath):
            size = os.path.getsize(fpath)
            if fname.endswith('.json'):
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        print(f'  ✅ {fname}: {len(data)} 条记录, {size/1024:.1f} KB')
                        results[fname] = {'count': len(data), 'size_kb': size/1024}
                    elif isinstance(data, dict):
                        print(f'  ✅ {fname}: {len(data)} 个键, {size/1024:.1f} KB')
                        results[fname] = {'count': len(data), 'size_kb': size/1024}
                    else:
                        print(f'  ✅ {fname}: {size/1024:.1f} KB')
                        results[fname] = {'size_kb': size/1024}
            else:
                print(f'  ✅ {fname}: {size/1024:.1f} KB')
                results[fname] = {'size_kb': size/1024}
        else:
            print(f'  ❌ {fname}: 不存在')
            results[fname] = {'exists': False}
    
    return results


def main():
    """主函数"""
    print('=' * 70)
    print('知识图谱模块状态检查')
    print('=' * 70)
    
    neo4j_status, neo4j_info = check_neo4j()
    transe_status, transe_info = check_transe()
    kg_stats = check_kg_stats()
    integrity = check_data_integrity()
    
    print('\n' + '=' * 70)
    print('状态汇总')
    print('=' * 70)
    print(f'  Neo4j 状态: {neo4j_status}')
    print(f'  TransE 状态: {transe_status}')
    print(f'  实体总数: {kg_stats.get("total_entities", 0)}')
    print(f'  三元组总数: {kg_stats.get("total_triples", 0)}')
    print('=' * 70)
    print('检查完成!')
    print('=' * 70)


if __name__ == '__main__':
    main()

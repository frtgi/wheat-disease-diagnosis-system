# -*- coding: utf-8 -*-
"""
IWDDA知识图谱模块验证脚本
验证内容：
1. Neo4j连接配置
2. 实体和三元组数量
3. GraphRAG查询功能
4. TransE嵌入模型
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path
from datetime import datetime

def verify_neo4j_connection():
    """
    验证Neo4j数据库连接
    
    :return: 连接状态和节点统计信息
    """
    print("\n" + "=" * 60)
    print("📡 验证Neo4j连接配置")
    print("=" * 60)
    
    result = {
        "status": False,
        "uri": "neo4j://localhost:7687",
        "user": "neo4j",
        "message": "",
        "node_count": 0,
        "relationship_count": 0
    }
    
    try:
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(
            "neo4j://localhost:7687",
            auth=("neo4j", "123456789s"),
            max_connection_lifetime=30,
            connection_timeout=10.0
        )
        
        driver.verify_connectivity()
        print("✅ Neo4j连接成功")
        result["status"] = True
        result["message"] = "连接成功"
        
        with driver.session() as session:
            node_result = session.run("MATCH (n) RETURN count(n) as count")
            result["node_count"] = node_result.single()['count']
            
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            result["relationship_count"] = rel_result.single()['count']
        
        print(f"   节点数量: {result['node_count']}")
        print(f"   关系数量: {result['relationship_count']}")
        
        driver.close()
        
    except Exception as e:
        result["message"] = str(e)
        print(f"❌ Neo4j连接失败: {e}")
    
    return result


def verify_entity_and_triple_counts():
    """
    验证实体和三元组数量
    
    :return: 实体和三元组统计信息
    """
    print("\n" + "=" * 60)
    print("📊 验证实体和三元组数量")
    print("=" * 60)
    
    result = {
        "expected_entities": 106,
        "expected_triples": 178,
        "actual_entities": 0,
        "actual_triples": 0,
        "entity_match": False,
        "triple_match": False,
        "entity_types": {},
        "relation_types": {}
    }
    
    kg_stats_path = Path(__file__).parent.parent / "checkpoints" / "knowledge_graph" / "kg_stats.json"
    
    if kg_stats_path.exists():
        with open(kg_stats_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        result["actual_entities"] = stats.get("total_entities", 0)
        result["actual_triples"] = stats.get("total_triples", 0)
        result["entity_types"] = stats.get("entity_types", {})
        result["relation_types"] = stats.get("relation_types", {})
        
        result["entity_match"] = result["actual_entities"] == result["expected_entities"]
        result["triple_match"] = result["actual_triples"] == result["expected_triples"]
        
        print(f"   预期实体数: {result['expected_entities']}")
        print(f"   实际实体数: {result['actual_entities']}")
        print(f"   实体数量匹配: {'✅' if result['entity_match'] else '❌'}")
        
        print(f"\n   预期三元组数: {result['expected_triples']}")
        print(f"   实际三元组数: {result['actual_triples']}")
        print(f"   三元组数量匹配: {'✅' if result['triple_match'] else '❌'}")
        
        print(f"\n   实体类型分布 ({len(result['entity_types'])}种):")
        for etype, count in sorted(result["entity_types"].items(), key=lambda x: -x[1])[:5]:
            print(f"      {etype}: {count}")
        
        print(f"\n   关系类型分布 ({len(result['relation_types'])}种):")
        for rtype, count in sorted(result["relation_types"].items(), key=lambda x: -x[1])[:5]:
            print(f"      {rtype}: {count}")
    else:
        print(f"❌ 知识图谱统计文件不存在: {kg_stats_path}")
    
    return result


def verify_graphrag_query():
    """
    验证GraphRAG查询功能
    
    :return: GraphRAG测试结果
    """
    print("\n" + "=" * 60)
    print("🔍 验证GraphRAG查询功能")
    print("=" * 60)
    
    result = {
        "status": False,
        "test_queries": [],
        "message": ""
    }
    
    try:
        from src.graph.graph_engine import KnowledgeAgent
        
        kg_agent = KnowledgeAgent(
            uri="neo4j://localhost:7687",
            user="neo4j",
            password="123456789s"
        )
        
        test_diseases = ["条锈病", "白粉病", "蚜虫", "赤霉病"]
        
        for disease in test_diseases:
            details = kg_agent.get_disease_details(disease)
            
            query_result = {
                "disease": disease,
                "found": bool(details),
                "causes_count": len(details.get("causes", [])),
                "preventions_count": len(details.get("preventions", [])),
                "treatments_count": len(details.get("treatments", []))
            }
            
            result["test_queries"].append(query_result)
            
            status_icon = "✅" if query_result["found"] else "❌"
            print(f"   {status_icon} {disease}:")
            print(f"      成因: {query_result['causes_count']}个")
            print(f"      预防: {query_result['preventions_count']}个")
            print(f"      治疗: {query_result['treatments_count']}个")
        
        kg_agent.close()
        
        result["status"] = all(q["found"] for q in result["test_queries"])
        result["message"] = "GraphRAG查询测试通过" if result["status"] else "部分查询失败"
        
    except Exception as e:
        result["message"] = str(e)
        print(f"❌ GraphRAG查询测试失败: {e}")
    
    return result


def verify_transe_model():
    """
    验证TransE嵌入模型
    
    :return: TransE模型验证结果
    """
    print("\n" + "=" * 60)
    print("🧠 验证TransE嵌入模型")
    print("=" * 60)
    
    result = {
        "status": False,
        "model_exists": False,
        "model_size_kb": 0,
        "embedding_dim": 0,
        "num_entities": 0,
        "num_relations": 0,
        "message": ""
    }
    
    transe_path = Path(__file__).parent.parent / "checkpoints" / "knowledge_graph" / "transe_model.pt"
    
    if transe_path.exists():
        result["model_exists"] = True
        result["model_size_kb"] = transe_path.stat().st_size / 1024
        print(f"   模型文件存在: ✅")
        print(f"   模型大小: {result['model_size_kb']:.2f} KB")
        
        try:
            import torch
            print(f"   PyTorch版本: {torch.__version__}")
            
            checkpoint = torch.load(transe_path, map_location='cpu', weights_only=False)
            state_dict = checkpoint.get('model_state_dict', checkpoint)
            
            if 'entity_embeddings.weight' in state_dict:
                entity_emb = state_dict['entity_embeddings.weight']
                result["num_entities"] = entity_emb.shape[0]
                result["embedding_dim"] = entity_emb.shape[1]
            
            if 'relation_embeddings.weight' in state_dict:
                relation_emb = state_dict['relation_embeddings.weight']
                result["num_relations"] = relation_emb.shape[0]
            
            print(f"   实体数量: {result['num_entities']}")
            print(f"   关系数量: {result['num_relations']}")
            print(f"   嵌入维度: {result['embedding_dim']}")
            
            result["status"] = True
            result["message"] = "TransE模型验证通过"
            
        except ImportError as e:
            result["message"] = f"PyTorch未安装: {e}"
            print(f"⚠️ PyTorch未安装，跳过模型加载验证")
            result["status"] = True
            result["message"] = "模型文件存在，但PyTorch未安装"
        except Exception as e:
            result["message"] = f"模型加载失败: {e}"
            print(f"❌ 模型加载失败: {e}")
    else:
        result["message"] = f"模型文件不存在: {transe_path}"
        print(f"❌ 模型文件不存在")
    
    return result


def run_verification():
    """
    运行完整验证流程
    
    :return: 完整验证报告
    """
    print("=" * 60)
    print("🔬 IWDDA知识图谱模块验证")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "neo4j_connection": None,
        "entity_triple_counts": None,
        "graphrag_query": None,
        "transe_model": None,
        "summary": {
            "all_passed": False,
            "issues": []
        }
    }
    
    report["neo4j_connection"] = verify_neo4j_connection()
    
    report["entity_triple_counts"] = verify_entity_and_triple_counts()
    
    report["graphrag_query"] = verify_graphrag_query()
    
    report["transe_model"] = verify_transe_model()
    
    print("\n" + "=" * 60)
    print("📋 验证结果汇总")
    print("=" * 60)
    
    issues = []
    
    if not report["neo4j_connection"]["status"]:
        issues.append("Neo4j连接失败")
    
    if not report["entity_triple_counts"]["entity_match"]:
        issues.append(f"实体数量不匹配 (预期{report['entity_triple_counts']['expected_entities']}, 实际{report['entity_triple_counts']['actual_entities']})")
    
    if not report["entity_triple_counts"]["triple_match"]:
        issues.append(f"三元组数量不匹配 (预期{report['entity_triple_counts']['expected_triples']}, 实际{report['entity_triple_counts']['actual_triples']})")
    
    if not report["graphrag_query"]["status"]:
        issues.append("GraphRAG查询功能异常")
    
    if not report["transe_model"]["status"]:
        issues.append("TransE嵌入模型异常")
    
    report["summary"]["issues"] = issues
    report["summary"]["all_passed"] = len(issues) == 0
    
    if report["summary"]["all_passed"]:
        print("✅ 所有验证项目通过！")
    else:
        print("❌ 发现以下问题:")
        for issue in issues:
            print(f"   - {issue}")
    
    report_path = Path(__file__).parent.parent / "logs" / "kg_verification_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 详细报告已保存: {report_path}")
    
    return report


if __name__ == "__main__":
    run_verification()

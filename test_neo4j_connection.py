# -*- coding: utf-8 -*-
"""
Neo4j 连接验证测试脚本
用于验证 Neo4j 知识图谱数据库的连接状态
"""
from neo4j import GraphDatabase


def test_neo4j_connection():
    """
    测试 Neo4j 数据库连接并返回基本信息
    
    :return: 连接状态和统计信息
    """
    uri = "neo4j://localhost:7687"
    user = "neo4j"
    password = "123456789s"
    
    print("=" * 60)
    print("Neo4j 知识图谱连接验证")
    print("=" * 60)
    print(f"\n📡 连接地址: {uri}")
    print(f"👤 用户名: {user}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("✅ 连接状态: 成功")
        
        with driver.session() as session:
            entity_count_result = session.run("""
                MATCH (n)
                RETURN count(n) as count
            """)
            entity_count = entity_count_result.single()["count"]
            
            relation_count_result = session.run("""
                MATCH ()-[r]->()
                RETURN count(r) as count
            """)
            relation_count = relation_count_result.single()["count"]
            
            label_result = session.run("""
                CALL db.labels() YIELD label
                RETURN label, count { (n) WHERE label IN labels(n) } as count
                ORDER BY count DESC
            """)
            labels = [(record["label"], record["count"]) for record in label_result]
            
            rel_type_result = session.run("""
                CALL db.relationshipTypes() YIELD relationshipType
                RETURN relationshipType
            """)
            rel_types = [record["relationshipType"] for record in rel_type_result]
        
        print("\n" + "-" * 60)
        print("📊 数据库统计信息")
        print("-" * 60)
        print(f"  实体总数: {entity_count}")
        print(f"  关系总数: {relation_count}")
        
        print("\n📋 实体类型分布:")
        for label, count in labels:
            print(f"  - {label}: {count} 个")
        
        print(f"\n🔗 关系类型 (共 {len(rel_types)} 种):")
        for rel_type in rel_types[:10]:
            print(f"  - {rel_type}")
        if len(rel_types) > 10:
            print(f"  ... 还有 {len(rel_types) - 10} 种关系类型")
        
        driver.close()
        
        return {
            "success": True,
            "uri": uri,
            "user": user,
            "entity_count": entity_count,
            "relation_count": relation_count,
            "labels": labels,
            "relationship_types": rel_types
        }
        
    except Exception as e:
        print(f"\n❌ 连接状态: 失败")
        print(f"❌ 错误信息: {e}")
        return {
            "success": False,
            "uri": uri,
            "user": user,
            "error": str(e)
        }


if __name__ == "__main__":
    result = test_neo4j_connection()
    print("\n" + "=" * 60)
    if result["success"]:
        print("✅ Neo4j 连接验证完成")
    else:
        print("❌ Neo4j 连接验证失败")
    print("=" * 60)

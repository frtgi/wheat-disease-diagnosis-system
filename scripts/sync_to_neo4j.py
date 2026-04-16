# -*- coding: utf-8 -*-
"""
Neo4j知识图谱同步脚本

将本地知识图谱数据同步到Neo4j数据库
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Neo4jSync:
    """Neo4j同步器"""
    
    def __init__(
        self,
        kg_path: str = "checkpoints/knowledge_graph",
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "123456789s"
    ):
        """
        初始化同步器
        
        :param kg_path: 知识图谱路径
        :param uri: Neo4j连接URI
        :param user: 用户名
        :param password: 密码
        """
        self.kg_path = Path(kg_path)
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
        self.entities = {}
        self.relations = []
        self.triples = []
        
        print("=" * 60)
        print("Neo4j知识图谱同步工具")
        print("=" * 60)
        print(f"知识图谱路径: {kg_path}")
        print(f"Neo4j URI: {uri}")
        print(f"用户: {user}")
    
    def load_knowledge_graph(self):
        """加载知识图谱数据"""
        print("\n加载知识图谱...")
        
        entities_file = self.kg_path / "entities.json"
        relations_file = self.kg_path / "relations.json"
        triples_file = self.kg_path / "triples.json"
        
        if entities_file.exists():
            with open(entities_file, 'r', encoding='utf-8') as f:
                self.entities = json.load(f)
            print(f"  实体数量: {len(self.entities)}")
        
        if relations_file.exists():
            with open(relations_file, 'r', encoding='utf-8') as f:
                self.relations = json.load(f)
            print(f"  关系数量: {len(self.relations)}")
        
        if triples_file.exists():
            with open(triples_file, 'r', encoding='utf-8') as f:
                self.triples = json.load(f)
            print(f"  三元组数量: {len(self.triples)}")
    
    def connect_neo4j(self) -> bool:
        """
        连接Neo4j数据库
        
        :return: 是否连接成功
        """
        print("\n连接Neo4j数据库...")
        
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            print("  ✅ 连接成功")
            return True
            
        except ImportError:
            print("  ⚠️ neo4j库未安装，请运行: pip install neo4j")
            return False
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            return False
    
    def clear_database(self):
        """清空数据库"""
        print("\n清空数据库...")
        
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        print("  ✅ 数据库已清空")
    
    def create_constraints(self):
        """创建约束"""
        print("\n创建约束...")
        
        entity_types = set()
        for entity in self.entities.values():
            entity_types.add(entity.get('type', 'Entity'))
        
        with self.driver.session() as session:
            for entity_type in entity_types:
                try:
                    session.run(f"""
                        CREATE CONSTRAINT IF NOT EXISTS FOR (n:{entity_type})
                        REQUIRE n.id IS UNIQUE
                    """)
                except Exception as e:
                    pass
        
        print(f"  ✅ 创建了 {len(entity_types)} 个约束")
    
    def create_entities(self):
        """创建实体节点"""
        print("\n创建实体节点...")
        
        created = 0
        with self.driver.session() as session:
            for entity_id, entity_data in self.entities.items():
                entity_type = entity_data.get('type', 'Entity')
                properties = entity_data.get('properties', {})
                properties['id'] = entity_id
                properties['name'] = entity_data.get('name', entity_id)
                
                props_str = ", ".join([f"n.{k} = ${k}" for k in properties.keys()])
                
                session.run(f"""
                    MERGE (n:{entity_type} {{id: $id}})
                    SET {props_str}
                """, **properties)
                
                created += 1
        
        print(f"  ✅ 创建了 {created} 个实体节点")
    
    def create_relations(self):
        """创建关系"""
        print("\n创建关系...")
        
        created = 0
        with self.driver.session() as session:
            for triple in self.triples:
                head = triple.get('head')
                relation = triple.get('relation')
                tail = triple.get('tail')
                
                if not all([head, relation, tail]):
                    continue
                
                head_type = self.entities.get(head, {}).get('type', 'Entity')
                tail_type = self.entities.get(tail, {}).get('type', 'Entity')
                
                relation_clean = relation.replace(' ', '_').upper()
                
                try:
                    session.run(f"""
                        MATCH (h:{head_type} {{id: $head}})
                        MATCH (t:{tail_type} {{id: $tail}})
                        MERGE (h)-[r:{relation_clean}]->(t)
                    """, head=head, tail=tail)
                    
                    created += 1
                except Exception as e:
                    print(f"  ⚠️ 创建关系失败: {head}-{relation}->{tail}: {e}")
        
        print(f"  ✅ 创建了 {created} 条关系")
    
    def verify_sync(self):
        """验证同步结果"""
        print("\n验证同步结果...")
        
        with self.driver.session() as session:
            node_result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = node_result.single()['count']
            
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_result.single()['count']
            
            print(f"  节点数量: {node_count}")
            print(f"  关系数量: {rel_count}")
            
            type_result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """)
            
            print("\n  节点类型统计:")
            for record in type_result:
                print(f"    {record['type']}: {record['count']}")
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
    
    def run(self, clear: bool = True):
        """
        运行同步流程
        
        :param clear: 是否清空数据库
        """
        print("\n开始同步...")
        
        self.load_knowledge_graph()
        
        if not self.connect_neo4j():
            print("\n❌ 无法连接Neo4j，同步失败")
            return False
        
        try:
            if clear:
                self.clear_database()
            
            self.create_constraints()
            self.create_entities()
            self.create_relations()
            self.verify_sync()
            
            print("\n" + "=" * 60)
            print("✅ 同步完成!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ 同步失败: {e}")
            return False
        
        finally:
            self.close()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="同步知识图谱到Neo4j")
    parser.add_argument('--kg-path', default='checkpoints/knowledge_graph', help='知识图谱路径')
    parser.add_argument('--uri', default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--user', default='neo4j', help='用户名')
    parser.add_argument('--password', default='123456789s', help='密码')
    parser.add_argument('--no-clear', action='store_true', help='不清空数据库')
    
    args = parser.parse_args()
    
    sync = Neo4jSync(
        kg_path=args.kg_path,
        uri=args.uri,
        user=args.user,
        password=args.password
    )
    
    sync.run(clear=not args.no_clear)


if __name__ == "__main__":
    main()

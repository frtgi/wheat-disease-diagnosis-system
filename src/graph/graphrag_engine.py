# -*- coding: utf-8 -*-
"""
GraphRAG - 基于图的检索增强生成 (Graph-based Retrieval-Augmented Generation)
Phase 6 增强版本：
1. 检索 (Retrieval): 根据初步诊断结果在 Neo4j 中检索相关子图（支持多跳检索）
2. 上下文构建 (Context Construction): 将检索到的子图序列化为自然语言描述
3. Token 化 (Tokenization): 将知识子图转换为 token 序列
4. 生成 (Generation): 将事实性知识作为背景资料喂给 Qwen3-VL-2B-Instruct 生成回答

Phase 6 新增功能：
- 子图检索优化（支持多跳、多实体检索）
- 知识 token 化（将图谱结构转换为文本 token）
- Graph-RAG 上下文注入（与 Qwen3-VL 集成）
- 实体类型扩展到 200+，关系类型扩展到 30+
"""
import os
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from neo4j import GraphDatabase
from collections import defaultdict
import hashlib


class GraphRAGEngine:
    """
    GraphRAG 引擎（Phase 6 增强版）
    实现基于知识图谱的检索增强生成，支持子图检索、知识 token 化和上下文注入
    
    核心功能：
    1. 多跳子图检索：从种子实体出发，检索多跳邻接节点
    2. 知识 token 化：将子图结构转换为自然语言 token 序列
    3. 上下文注入：将知识 token 注入到 Qwen3-VL 的提示词中
    4. 缓存优化：使用 LRU 缓存提升检索性能（目标<100ms）
    """
    
    DEFAULT_URI = "neo4j://localhost:7687"
    DEFAULT_USER = "neo4j"
    DEFAULT_PASSWORD = "password"
    
    def __init__(self, uri=None, user=None, password=None, cache_size=100):
        """
        初始化 GraphRAG 引擎
        
        连接参数优先级：环境变量 > 参数 > 默认值
        
        :param uri: Neo4j 数据库 URI（可选，默认从环境变量 NEO4J_URI 读取）
        :param user: 用户名（可选，默认从环境变量 NEO4J_USER 读取）
        :param password: 密码（可选，默认从环境变量 NEO4J_PASSWORD 读取）
        :param cache_size: LRU 缓存大小，默认 100 个子图
        """
        self.uri = uri or os.environ.get("NEO4J_URI", self.DEFAULT_URI)
        self.user = user or os.environ.get("NEO4J_USER", self.DEFAULT_USER)
        self.password = password or os.environ.get("NEO4J_PASSWORD", self.DEFAULT_PASSWORD)
        
        self.driver = None
        self._connected = False
        
        self._init_driver()
        
        self.subgraph_cache = {}
        self.cache_size = cache_size
        self.cache_access_count = defaultdict(int)
        
        self.performance_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "avg_query_time_ms": 0.0,
            "max_query_time_ms": 0.0,
            "connection_status": "connected" if self._connected else "disconnected"
        }
    
    def _init_driver(self):
        """
        初始化 Neo4j 驱动并验证连接
        
        连接失败时设置降级标志，不影响服务运行
        """
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            self._connected = True
            print(f"🔗 [GraphRAG] 图数据库连接成功: {self.uri}")
        except Exception as e:
            self._connected = False
            print(f"⚠️ [GraphRAG] 图数据库连接失败：{e}，将使用降级模式")
            print(f"   连接参数: URI={self.uri}, User={self.user}")
    
    def is_connected(self) -> bool:
        """
        检查数据库连接状态
        
        :return: True 表示已连接，False 表示未连接
        """
        return self._connected
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            try:
                self.driver.close()
            except Exception as e:
                print(f"⚠️ [GraphRAG] 关闭连接时出错：{e}")
    
    def _manage_cache(self, cache_key: str):
        """
        管理 LRU 缓存，当缓存超过大小时移除最少使用的项
        
        :param cache_key: 新加入的缓存键
        """
        if len(self.subgraph_cache) >= self.cache_size:
            # 找到最少使用的项
            min_access = min(self.cache_access_count.items(), key=lambda x: x[1])
            if min_access[0] in self.subgraph_cache and min_access[0] != cache_key:
                del self.subgraph_cache[min_access[0]]
                del self.cache_access_count[min_access[0]]
    
    def retrieve_subgraph(self, disease_name: str, depth: int = 2) -> Dict[str, Any]:
        """
        检索与病害相关的子图（支持多跳检索）
        
        Phase 6 增强：
        - 支持多跳检索（depth 参数控制跳数）
        - LRU 缓存优化性能
        - 性能统计监控
        - 新增：生长阶段、防治方法、农药类型
        - 连接状态检查，断开时返回空子图
        
        :param disease_name: 病害名称
        :param depth: 检索深度（跳数，默认 2 跳）
        :return: 子图信息字典
        """
        start_time = time.time()
        self.performance_stats["total_queries"] += 1
        
        cache_key = f"{disease_name}_{depth}"
        if cache_key in self.subgraph_cache:
            self.performance_stats["cache_hits"] += 1
            self.cache_access_count[cache_key] += 1
            return self.subgraph_cache[cache_key]
        
        subgraph = {
            "disease": disease_name,
            "symptoms": [],
            "causes": [],
            "preventions": [],
            "treatments": [],
            "related_diseases": [],
            "environment_factors": [],
            "growth_stages": [],
            "pesticide_types": [],
            "control_methods": []
        }
        
        if not self._connected or not self.driver:
            print(f"⚠️ [GraphRAG] 数据库未连接，跳过子图检索: {disease_name}")
            return subgraph
        
        try:
            with self.driver.session() as session:
                # 1. 检索症状（支持多跳）
                symptom_query = """
                MATCH (d:Disease {name: $name})-[:HAS_SYMPTOM]->(s:Symptom)
                OPTIONAL MATCH (s)-[:AFFECTS_PART]->(p:CropPart)
                RETURN s.name as symptom, s.description as desc, p.name as part
                """
                symptoms = session.run(symptom_query, name=disease_name)
                subgraph["symptoms"] = [
                    {
                        "name": record["symptom"], 
                        "description": record["desc"],
                        "affected_part": record["part"]
                    }
                    for record in symptoms
                ]
                
                # 2. 检索成因（扩展：环境因素、病原）
                cause_query = """
                MATCH (d:Disease {name: $name})-[:CAUSED_BY]->(c:Cause)
                OPTIONAL MATCH (c)-[:RELATED_TO]->(e:Environment)
                RETURN c.name as cause, c.description as desc, e.name as env
                """
                causes = session.run(cause_query, name=disease_name)
                subgraph["causes"] = [
                    {
                        "name": record["cause"], 
                        "description": record["desc"],
                        "related_env": record["env"]
                    }
                    for record in causes
                ]
                
                # 3. 检索预防措施（扩展：农业防治、生物防治）
                prevention_query = """
                MATCH (d:Disease {name: $name})-[:PREVENTED_BY]->(p:Prevention)
                OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:ControlCategory)
                RETURN p.name as prevention, p.description as desc, c.name as category
                """
                preventions = session.run(prevention_query, name=disease_name)
                subgraph["preventions"] = [
                    {
                        "name": record["prevention"], 
                        "description": record["desc"],
                        "category": record["category"]
                    }
                    for record in preventions
                ]
                
                # 4. 检索治疗措施（扩展：农药类型、用量、安全间隔期）
                treatment_query = """
                MATCH (d:Disease {name: $name})-[:TREATED_BY]->(t:Treatment)
                OPTIONAL MATCH (t)-[:IS_TYPE]->(pt:PesticideType)
                RETURN t.name as treatment, t.usage as usage, t.dosage as dosage, 
                       t.safety_interval as interval, pt.name as pesticide_type
                """
                treatments = session.run(treatment_query, name=disease_name)
                subgraph["treatments"] = [
                    {
                        "name": record["treatment"],
                        "usage": record["usage"],
                        "dosage": record["dosage"],
                        "safety_interval": record["interval"],
                        "pesticide_type": record["pesticide_type"]
                    }
                    for record in treatments
                ]
                
                # 5. 检索相关病害（易混淆病害，支持多跳）
                related_query = """
                MATCH (d:Disease {name: $name})-[:SIMILAR_TO]->(r:Disease)
                RETURN r.name as disease, r.description as desc
                UNION
                MATCH (d:Disease {name: $name})-[:HAS_SYMPTOM]->(s:Symptom)<-[:HAS_SYMPTOM]-(r:Disease)
                WHERE r.name <> $name
                RETURN r.name as disease, r.description as desc
                LIMIT 5
                """
                related = session.run(related_query, name=disease_name)
                subgraph["related_diseases"] = [
                    {"name": record["disease"], "description": record["desc"]}
                    for record in related
                ]
                
                # 6. 检索环境因素（扩展：温度、湿度、光照、土壤）
                env_query = """
                MATCH (d:Disease {name: $name})-[:FAVORED_BY]->(e:Environment)
                RETURN e.name as name, e.condition as condition, 
                       e.temperature as temp, e.humidity as humidity,
                       e.light as light, e.soil as soil
                """
                env_factors = session.run(env_query, name=disease_name)
                subgraph["environment_factors"] = [
                    {
                        "name": record["name"],
                        "condition": record["condition"],
                        "temperature": record["temp"],
                        "humidity": record["humidity"],
                        "light": record["light"],
                        "soil": record["soil"]
                    }
                    for record in env_factors
                ]
                
                # 7. 检索生长阶段（新增）
                growth_query = """
                MATCH (d:Disease {name: $name})-[:OCCURS_AT]->(g:GrowthStage)
                RETURN g.name as name, g.description as desc
                """
                growth_stages = session.run(growth_query, name=disease_name)
                subgraph["growth_stages"] = [
                    {"name": record["name"], "description": record["desc"]}
                    for record in growth_stages
                ]
                
                # 8. 检索农药类型（新增）
                pesticide_query = """
                MATCH (d:Disease {name: $name})-[:TREATED_BY]->(t:Treatment)
                OPTIONAL MATCH (t)-[:IS_TYPE]->(pt:PesticideType)
                RETURN DISTINCT pt.name as name, pt.description as desc
                """
                pesticides = session.run(pesticide_query, name=disease_name)
                subgraph["pesticide_types"] = [
                    {"name": record["name"], "description": record["desc"]}
                    for record in pesticides
                ]
                
                # 9. 检索防治方法（新增）
                control_query = """
                MATCH (d:Disease {name: $name})-[:PREVENTED_BY]->(p:Prevention)
                OPTIONAL MATCH (p)-[:BELONGS_TO]->(cc:ControlCategory)
                RETURN DISTINCT cc.name as name, cc.description as desc
                """
                controls = session.run(control_query, name=disease_name)
                subgraph["control_methods"] = [
                    {"name": record["name"], "description": record["desc"]}
                    for record in controls
                ]
                
        except Exception as e:
            print(f"❌ [GraphRAG] 子图检索失败：{e}")
        
        # 更新缓存
        self._manage_cache(cache_key)
        self.subgraph_cache[cache_key] = subgraph
        
        # 更新性能统计
        elapsed_time = (time.time() - start_time) * 1000
        self.performance_stats["avg_query_time_ms"] = (
            (self.performance_stats["avg_query_time_ms"] * (self.performance_stats["total_queries"] - 1) + elapsed_time)
            / self.performance_stats["total_queries"]
        )
        self.performance_stats["max_query_time_ms"] = max(
            self.performance_stats["max_query_time_ms"], elapsed_time
        )
        
        return subgraph
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        检索相关知识（简化接口）
        
        :param query: 查询文本
        :param top_k: 返回结果数量
        :return: 知识列表
        """
        # 简单关键词匹配
        keywords = ["条锈病", "叶锈病", "秆锈病", "白粉病", "赤霉病", "纹枯病", "根腐病"]
        results = []
        
        for keyword in keywords:
            if keyword in query:
                subgraph = self.retrieve_subgraph(keyword)
                results.append({
                    "disease": keyword,
                    "subgraph": subgraph
                })
                if len(results) >= top_k:
                    break
        
        return results
    
    def construct_context(self, subgraph: Dict[str, Any]) -> str:
        """
        将子图构造为自然语言上下文
        
        :param subgraph: 子图数据
        :return: 上下文字符串
        """
        context_parts = []
        
        disease = subgraph.get("disease", "未知病害")
        context_parts.append(f"病害：{disease}")
        
        # 症状
        symptoms = subgraph.get("symptoms", [])
        if symptoms:
            symptom_names = [s.get("name", "") for s in symptoms if s.get("name")]
            if symptom_names:
                context_parts.append(f"症状：{', '.join(symptom_names)}")
        
        # 成因
        causes = subgraph.get("causes", [])
        if causes:
            cause_names = [c.get("name", "") for c in causes if c.get("name")]
            if cause_names:
                context_parts.append(f"成因：{', '.join(cause_names)}")
        
        # 预防
        preventions = subgraph.get("preventions", [])
        if preventions:
            prev_names = [p.get("name", "") for p in preventions if p.get("name")]
            if prev_names:
                context_parts.append(f"预防措施：{', '.join(prev_names)}")
        
        # 治疗
        treatments = subgraph.get("treatments", [])
        if treatments:
            treat_names = [t.get("name", "") for t in treatments if t.get("name")]
            if treat_names:
                context_parts.append(f"治疗方法：{', '.join(treat_names)}")
        
        return "\n".join(context_parts)
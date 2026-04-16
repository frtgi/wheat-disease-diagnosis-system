# 文件路径: WheatAgent/src/graph/graph_engine.py
import os
from neo4j import GraphDatabase
import warnings


def get_neo4j_config():
    """
    获取 Neo4j 连接配置
    
    :return: 包含 uri, user, password 的配置字典
    """
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "123456789s"),
        "database": os.getenv("NEO4J_DATABASE", "neo4j"),
        "max_connection_pool_size": int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50")),
        "connection_timeout": int(os.getenv("NEO4J_CONNECTION_TIMEOUT", "30"))
    }


class KnowledgeAgent:
    def __init__(self, uri=None, user=None, password=None, force_init=False):
        """
        初始化知识图谱代理
        
        :param uri: Neo4j连接URI (可选，默认从环境变量读取)
        :param user: 用户名 (可选，默认从环境变量读取)
        :param password: 密码 (可选，默认从环境变量读取)
        :param force_init: 是否强制重新初始化知识库
        """
        config = get_neo4j_config()
        uri = uri or config["uri"]
        user = user or config["user"]
        password = password or config["password"]
        max_pool_size = config["max_connection_pool_size"]
        connection_timeout = config["connection_timeout"]
        
        print(f"📚 [KnowledgeAgent] 正在连接Neo4j数据库: {uri}", flush=True)
        
        print("   [KG] 创建Neo4j驱动...", flush=True)
        self.driver = GraphDatabase.driver(
            uri, 
            auth=(user, password),
            max_connection_lifetime=30,
            max_connection_pool_size=max_pool_size,
            connection_timeout=float(connection_timeout)
        )
        print("   [KG] Neo4j驱动创建完成", flush=True)
        self.force_init = force_init
        
        try:
            print("   [KG] 验证连接...", flush=True)
            self.driver.verify_connectivity()
            print("✅ [KnowledgeAgent] Neo4j连接成功", flush=True)
            print("   [KG] 检查知识库状态...", flush=True)
            self._check_and_init_knowledge_base()
        except Exception as e:
            print(f"❌ 图数据库连接失败: {e}", flush=True)
            raise

    def close(self):
        self.driver.close()
    
    def _check_and_init_knowledge_base(self):
        """检查并初始化知识库（避免重复清空）"""
        with self.driver.session() as session:
            # 检查是否已有数据
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()['count']
            
            if count > 0 and not self.force_init:
                print(f"✅ 知识库已存在 {count} 个节点，跳过初始化")
                return
            
            if self.force_init and count > 0:
                print(f"🔄 强制重新初始化知识库（当前 {count} 个节点）")
            
            self._init_knowledge_base()

    def _init_knowledge_base(self):
        print("📥 [初始化] 正在注入全维度小麦病害知识库 (含成因与预防)...")
        
        # 1. 清空语句
        clear_query = "MATCH (n) DETACH DELETE n"
        
        # 2. 初始化语句
        init_query = """
        // --- 1. 定义核心病害节点 (16类) ---
        CREATE (d0:Disease {name: '蚜虫', type: 'Insect'})
        CREATE (d1:Disease {name: '螨虫', type: 'Insect'})
        CREATE (d2:Disease {name: '茎蝇', type: 'Insect'})
        CREATE (d3:Disease {name: '锈病', type: 'Fungus'})
        CREATE (d4:Disease {name: '茎锈病', type: 'Fungus'})
        CREATE (d5:Disease {name: '叶锈病', type: 'Fungus'})
        CREATE (d6:Disease {name: '条锈病', type: 'Fungus'})
        CREATE (d7:Disease {name: '黑粉病', type: 'Fungus'})
        CREATE (d8:Disease {name: '根腐病', type: 'Fungus'})
        CREATE (d9:Disease {name: '叶斑病', type: 'Fungus'})
        CREATE (d10:Disease {name: '小麦爆发病', type: 'Fungus'})
        CREATE (d11:Disease {name: '赤霉病', type: 'Fungus'})
        CREATE (d12:Disease {name: '壳针孢叶斑病', type: 'Fungus'})
        CREATE (d13:Disease {name: '斑点叶斑病', type: 'Fungus'})
        CREATE (d14:Disease {name: '褐斑病', type: 'Fungus'})
        CREATE (d15:Disease {name: '白粉病', type: 'Fungus'})

        // --- 2. 定义环境成因 (Causes) ---
        CREATE (c_humid:Cause {name: '高湿环境', desc: '相对湿度>80%'})
        CREATE (c_temp_low:Cause {name: '低温寡照', desc: '气温9-15℃'})
        CREATE (c_temp_high:Cause {name: '高温干旱', desc: '气温>25℃且干旱'})
        CREATE (c_soil:Cause {name: '土壤连作', desc: '菌源积累'})
        CREATE (c_wind:Cause {name: '气流传播', desc: '孢子随风扩散'})

        // --- 3. 定义预防措施 (Prevention) ---
        CREATE (p_seed:Prevention {name: '抗病选种', desc: '选用抗病良种'})
        CREATE (p_rot:Prevention {name: '轮作倒茬', desc: '与非禾本科作物轮作'})
        CREATE (p_drain:Prevention {name: '清沟沥水', desc: '降低田间湿度'})
        CREATE (p_clean:Prevention {name: '清除病残体', desc: '减少越冬菌源'})

        // --- 4. 建立关联 ---
        // 条锈病/叶锈病/白粉病 -> 喜湿、气流传播
        FOREACH (d IN [d6, d5, d15] | 
            MERGE (d)-[:CAUSED_BY]->(c_humid)
            MERGE (d)-[:CAUSED_BY]->(c_wind)
            MERGE (d)-[:PREVENTED_BY]->(p_seed)
            MERGE (d)-[:PREVENTED_BY]->(p_drain)
        )
        
        // 赤霉病 -> 扬花期遇雨 (高湿)
        MERGE (d11)-[:CAUSED_BY]->(c_humid)
        MERGE (d11)-[:PREVENTED_BY]->(p_seed)
        MERGE (d11)-[:PREVENTED_BY]->(p_clean)

        // 蚜虫/螨虫 -> 高温干旱
        FOREACH (d IN [d0, d1] | 
            MERGE (d)-[:CAUSED_BY]->(c_temp_high)
            MERGE (d)-[:PREVENTED_BY]->(p_clean)
        )

        // 根腐病/黑粉病 -> 土壤连作
        FOREACH (d IN [d8, d7] | 
            MERGE (d)-[:CAUSED_BY]->(c_soil)
            MERGE (d)-[:PREVENTED_BY]->(p_rot)
            MERGE (d)-[:PREVENTED_BY]->(p_seed)
        )

        // --- 5. 药剂 (Treatments) ---
        CREATE (t_triazole:Treatment {name: '三唑酮/戊唑醇', usage: '喷雾'})
        CREATE (t_insect:Treatment {name: '吡虫啉', usage: '喷雾'})
        CREATE (t_scab:Treatment {name: '氰烯菌酯', usage: '花期喷雾'})
        
        // 简单关联药剂
        FOREACH (d IN [d3,d4,d5,d6,d9,d12,d13,d14,d15] | MERGE (d)-[:TREATED_BY]->(t_triazole))
        FOREACH (d IN [d0,d1,d2] | MERGE (d)-[:TREATED_BY]->(t_insect))
        MERGE (d11)-[:TREATED_BY]->(t_scab)
        """
        
        with self.driver.session() as session:
            # 关键修改：分两步执行
            session.run(clear_query)  # 第一步：清空
            session.run(init_query)   # 第二步：注入
            print("✅ 知识库升级完毕！(已注入成因与预防体系)")

    def get_disease_details(self, disease_name):
        """获取病害的全方位详情：成因、预防、治疗"""
        name_map = {
            "Aphids": "蚜虫", "Mites": "螨虫", "Stem Fly": "茎蝇", 
            "Stem Rust": "茎锈病", "Leaf Rust": "叶锈病", "Stripe Rust": "条锈病",
            "Powdery Mildew": "白粉病", "Fusarium Head Blight": "赤霉病",
            "Smuts": "黑粉病", "Root Rot": "根腐病"
        }
        search_name = name_map.get(disease_name, disease_name)
        
        query = """
        MATCH (d:Disease {name: $name})
        OPTIONAL MATCH (d)-[:CAUSED_BY]->(c:Cause)
        OPTIONAL MATCH (d)-[:PREVENTED_BY]->(p:Prevention)
        OPTIONAL MATCH (d)-[:TREATED_BY]->(t:Treatment)
        RETURN 
            collect(DISTINCT c.name) as causes, 
            collect(DISTINCT p.name + '(' + p.desc + ')') as preventions,
            collect(DISTINCT t.name + '(' + t.usage + ')') as treatments
        """
        with self.driver.session() as session:
            result = session.run(query, name=search_name).single()
            if not result:
                return {}
            return {
                "name": search_name,
                "causes": result["causes"],
                "preventions": result["preventions"],
                "treatments": result["treatments"]
            }

    # 保留旧接口兼容性
    def verify_consistency(self, disease_name, symptom_text):
        return True 

    def get_treatment_info(self, disease_name):
        # 兼容旧代码调用
        details = self.get_disease_details(disease_name)
        if not details or not details.get('treatments'):
            return "建议咨询农技站。"
        return ", ".join(details['treatments'])
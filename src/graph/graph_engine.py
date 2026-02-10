# 文件路径: WheatAgent/src/graph/graph_engine.py
from neo4j import GraphDatabase

class KnowledgeAgent:
    def __init__(self, uri="neo4j://localhost:7687", user="neo4j", password="123456789s"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        try:
            self.driver.verify_connectivity()
            # 初始化知识库
            self._init_knowledge_base()
        except Exception as e:
            print(f"❌ 图数据库连接失败: {e}")

    def close(self):
        self.driver.close()

    def _init_knowledge_base(self):
        print("📥 [初始化] 正在注入全维度小麦病害知识库 (含成因与预防)...")
        
        # 1. 拆分出的清空语句
        clear_query = "MATCH (n) DETACH DELETE n"
        
        # 2. 初始化语句 (去掉开头的 clear 语句)
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
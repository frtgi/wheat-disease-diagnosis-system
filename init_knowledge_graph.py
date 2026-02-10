# -*- coding: utf-8 -*-
# 文件路径: WheatAgent/init_knowledge_graph.py
"""
知识图谱数据初始化脚本
用于初始化 Neo4j 知识图谱，包含所有小麦病害的详细信息
"""

from neo4j import GraphDatabase
import sys

def init_knowledge_graph(uri="neo4j://localhost:7687", user="neo4j", password="123456789s"):
    """
    初始化知识图谱数据库
    """
    print("📥 [初始化] 正在注入全维度小麦病害知识库...")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        driver.verify_connectivity()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 图数据库连接失败: {e}")
        sys.exit(1)
    
    with driver.session() as session:
        # 1. 清空现有数据
        print("🗑️ 清空现有数据...")
        session.run("MATCH (n) DETACH DELETE n")
        
        # 2. 创建病害节点（16类）
        print("🌱 创建病害节点...")
        diseases_query = """
        CREATE (d0:Disease {name: '蚜虫', type: 'Insect', description: '黑色或绿色小虫，分泌蜜露'})
        CREATE (d1:Disease {name: '螨虫', type: 'Insect', description: '叶片卷曲发黄，植株矮小'})
        CREATE (d2:Disease {name: '茎蝇', type: 'Insect', description: '茎秆有蛀孔，植株枯萎'})
        CREATE (d3:Disease {name: '锈病', type: 'Fungus', description: '叶片上有黄色或红褐色粉末孢子堆'})
        CREATE (d4:Disease {name: '茎锈病', type: 'Fungus', description: '茎秆上有红褐色锈斑'})
        CREATE (d5:Disease {name: '叶锈病', type: 'Fungus', description: '叶片上有红褐色粉末状斑点'})
        CREATE (d6:Disease {name: '条锈病', type: 'Fungus', description: '叶片上有黄色条纹状锈斑'})
        CREATE (d7:Disease {name: '黑粉病', type: 'Fungus', description: '穗部变成黑粉'})
        CREATE (d8:Disease {name: '根腐病', type: 'Fungus', description: '根部腐烂变黑'})
        CREATE (d9:Disease {name: '叶斑病', type: 'Fungus', description: '褐色病斑'})
        CREATE (d10:Disease {name: '小麦爆发病', type: 'Fungus', description: '穗部枯萎，有灰色霉层'})
        CREATE (d11:Disease {name: '赤霉病', type: 'Fungus', description: '穗部枯白，粉红色霉层'})
        CREATE (d12:Disease {name: '壳针孢叶斑病', type: 'Fungus', description: '叶片上有褐色小斑点'})
        CREATE (d13:Disease {name: '斑点叶斑病', type: 'Fungus', description: '叶片上有不规则斑点'})
        CREATE (d14:Disease {name: '褐斑病', type: 'Fungus', description: '叶片上有褐色圆形病斑'})
        CREATE (d15:Disease {name: '白粉病', type: 'Fungus', description: '白色绒毛状霉层'})
        CREATE (d16:Disease {name: '健康', type: 'Healthy', description: '植株生长正常，无病害症状'})
        """
        session.run(diseases_query)
        print("✅ 病害节点创建完成")
        
        # 3. 创建环境成因节点
        print("🌧️ 创建环境成因节点...")
        causes_query = """
        CREATE (c_humid:Cause {name: '高湿环境', desc: '相对湿度>80%', keywords: ['潮湿', '多雨', '高湿', '湿度']})
        CREATE (c_temp_low:Cause {name: '低温寡照', desc: '气温9-15℃', keywords: ['低温', '寒冷', '寡照']})
        CREATE (c_temp_high:Cause {name: '高温干旱', desc: '气温>25℃且干旱', keywords: ['高温', '干旱', '炎热']})
        CREATE (c_soil:Cause {name: '土壤连作', desc: '菌源积累', keywords: ['连作', '重茬', '土壤']})
        CREATE (c_wind:Cause {name: '气流传播', desc: '孢子随风扩散', keywords: ['风', '气流', '传播']})
        CREATE (c_flower:Cause {name: '扬花期遇雨', desc: '扬花期降雨', keywords: ['扬花', '花期', '雨']})
        """
        session.run(causes_query)
        print("✅ 环境成因节点创建完成")
        
        # 4. 创建预防措施节点
        print("🛡️ 创建预防措施节点...")
        preventions_query = """
        CREATE (p_seed:Prevention {name: '抗病选种', desc: '选用抗病良种', keywords: ['选种', '抗病', '良种']})
        CREATE (p_rot:Prevention {name: '轮作倒茬', desc: '与非禾本科作物轮作', keywords: ['轮作', '倒茬', '间作']})
        CREATE (p_drain:Prevention {name: '清沟沥水', desc: '降低田间湿度', keywords: ['排水', '沥水', '清沟']})
        CREATE (p_clean:Prevention {name: '清除病残体', desc: '减少越冬菌源', keywords: ['清除', '病残体', '清洁']})
        CREATE (p_fertilizer:Prevention {name: '合理施肥', desc: '增施有机肥，控制氮肥', keywords: ['施肥', '肥料', '氮肥']})
        CREATE (p_density:Prevention {name: '合理密植', desc: '控制种植密度', keywords: ['密植', '密度', '间距']})
        """
        session.run(preventions_query)
        print("✅ 预防措施节点创建完成")
        
        # 5. 创建治疗药剂节点
        print("💊 创建治疗药剂节点...")
        treatments_query = """
        CREATE (t_triazole:Treatment {name: '三唑酮/戊唑醇', usage: '喷雾', keywords: ['三唑酮', '戊唑醇', '三唑']})
        CREATE (t_insect:Treatment {name: '吡虫啉', usage: '喷雾', keywords: ['吡虫啉', '杀虫剂']})
        CREATE (t_scab:Treatment {name: '氰烯菌酯', usage: '花期喷雾', keywords: ['氰烯菌酯', '赤霉病']})
        CREATE (t_manco:Treatment {name: '代森锰锌', usage: '喷雾', keywords: ['代森锰锌', '保护剂']})
        CREATE (t_carb:Treatment {name: '多菌灵', usage: '喷雾', keywords: ['多菌灵', '广谱']})
        CREATE (t_sulfur:Treatment {name: '硫磺粉', usage: '喷雾', keywords: ['硫磺', '白粉病']})
        """
        session.run(treatments_query)
        print("✅ 治疗药剂节点创建完成")
        
        # 6. 建立病害与成因的关联
        print("🔗 建立病害与成因的关联...")
        
        # 条锈病/叶锈病/白粉病 -> 高湿环境
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['条锈病', '叶锈病', '白粉病']
            MATCH (c:Cause {name: '高湿环境'})
            MERGE (d)-[:CAUSED_BY]->(c)
        """)
        
        # 条锈病/叶锈病/白粉病 -> 气流传播
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['条锈病', '叶锈病', '白粉病']
            MATCH (c:Cause {name: '气流传播'})
            MERGE (d)-[:CAUSED_BY]->(c)
        """)
        
        # 赤霉病 -> 高湿环境
        session.run("""
            MATCH (d:Disease {name: '赤霉病'})
            MATCH (c:Cause {name: '高湿环境'})
            MERGE (d)-[:CAUSED_BY]->(c)
        """)
        
        # 赤霉病 -> 扬花期遇雨
        session.run("""
            MATCH (d:Disease {name: '赤霉病'})
            MATCH (c:Cause {name: '扬花期遇雨'})
            MERGE (d)-[:CAUSED_BY]->(c)
        """)
        
        # 蚜虫/螨虫 -> 高温干旱
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['蚜虫', '螨虫']
            MATCH (c:Cause {name: '高温干旱'})
            MERGE (d)-[:CAUSED_BY]->(c)
        """)
        
        # 根腐病/黑粉病 -> 土壤连作
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['根腐病', '黑粉病']
            MATCH (c:Cause {name: '土壤连作'})
            MERGE (d)-[:CAUSED_BY]->(c)
        """)
        
        # 茎锈病 -> 低温寡照
        session.run("""
            MATCH (d:Disease {name: '茎锈病'})
            MATCH (c:Cause {name: '低温寡照'})
            MERGE (d)-[:CAUSED_BY]->(c)
        """)
        
        # 茎蝇 -> 高温干旱
        session.run("""
            MATCH (d:Disease {name: '茎蝇'})
            MATCH (c:Cause {name: '高温干旱'})
            MERGE (d)-[:CAUSED_BY]->(c)
        """)
        
        print("✅ 病害与成因关联建立完成")
        
        # 7. 建立病害与预防措施的关联
        print("🔗 建立病害与预防措施的关联...")
        
        # 条锈病/叶锈病/白粉病 -> 抗病选种
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['条锈病', '叶锈病', '白粉病']
            MATCH (p:Prevention {name: '抗病选种'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 条锈病/叶锈病/白粉病 -> 清沟沥水
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['条锈病', '叶锈病', '白粉病']
            MATCH (p:Prevention {name: '清沟沥水'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 条锈病/叶锈病/白粉病 -> 清除病残体
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['条锈病', '叶锈病', '白粉病']
            MATCH (p:Prevention {name: '清除病残体'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 赤霉病 -> 抗病选种
        session.run("""
            MATCH (d:Disease {name: '赤霉病'})
            MATCH (p:Prevention {name: '抗病选种'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 赤霉病 -> 清除病残体
        session.run("""
            MATCH (d:Disease {name: '赤霉病'})
            MATCH (p:Prevention {name: '清除病残体'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 赤霉病 -> 清沟沥水
        session.run("""
            MATCH (d:Disease {name: '赤霉病'})
            MATCH (p:Prevention {name: '清沟沥水'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 蚜虫/螨虫 -> 清除病残体
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['蚜虫', '螨虫']
            MATCH (p:Prevention {name: '清除病残体'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 蚜虫/螨虫 -> 合理密植
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['蚜虫', '螨虫']
            MATCH (p:Prevention {name: '合理密植'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 根腐病/黑粉病 -> 轮作倒茬
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['根腐病', '黑粉病']
            MATCH (p:Prevention {name: '轮作倒茬'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 根腐病/黑粉病 -> 抗病选种
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['根腐病', '黑粉病']
            MATCH (p:Prevention {name: '抗病选种'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 根腐病/黑粉病 -> 合理施肥
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['根腐病', '黑粉病']
            MATCH (p:Prevention {name: '合理施肥'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 茎锈病 -> 抗病选种
        session.run("""
            MATCH (d:Disease {name: '茎锈病'})
            MATCH (p:Prevention {name: '抗病选种'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        # 茎蝇 -> 清除病残体
        session.run("""
            MATCH (d:Disease {name: '茎蝇'})
            MATCH (p:Prevention {name: '清除病残体'})
            MERGE (d)-[:PREVENTED_BY]->(p)
        """)
        
        print("✅ 病害与预防措施关联建立完成")
        
        # 8. 建立病害与治疗药剂的关联
        print("🔗 建立病害与治疗药剂的关联...")
        
        # 锈病类 -> 三唑酮/戊唑醇
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['锈病', '茎锈病', '叶锈病', '条锈病']
            MATCH (t:Treatment {name: '三唑酮/戊唑醇'})
            MERGE (d)-[:TREATED_BY]->(t)
        """)
        
        # 叶斑病类 -> 三唑酮/戊唑醇
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['叶斑病', '壳针孢叶斑病', '斑点叶斑病', '褐斑病']
            MATCH (t:Treatment {name: '三唑酮/戊唑醇'})
            MERGE (d)-[:TREATED_BY]->(t)
        """)
        
        # 叶斑病类 -> 代森锰锌
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['叶斑病', '壳针孢叶斑病', '斑点叶斑病', '褐斑病']
            MATCH (t:Treatment {name: '代森锰锌'})
            MERGE (d)-[:TREATED_BY]->(t)
        """)
        
        # 白粉病 -> 三唑酮/戊唑醇
        session.run("""
            MATCH (d:Disease {name: '白粉病'})
            MATCH (t:Treatment {name: '三唑酮/戊唑醇'})
            MERGE (d)-[:TREATED_BY]->(t)
        """)
        
        # 白粉病 -> 硫磺粉
        session.run("""
            MATCH (d:Disease {name: '白粉病'})
            MATCH (t:Treatment {name: '硫磺粉'})
            MERGE (d)-[:TREATED_BY]->(t)
        """)
        
        # 赤霉病 -> 氰烯菌酯
        session.run("""
            MATCH (d:Disease {name: '赤霉病'})
            MATCH (t:Treatment {name: '氰烯菌酯'})
            MERGE (d)-[:TREATED_BY]->(t)
        """)
        
        # 蚜虫/螨虫/茎蝇 -> 吡虫啉
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['蚜虫', '螨虫', '茎蝇']
            MATCH (t:Treatment {name: '吡虫啉'})
            MERGE (d)-[:TREATED_BY]->(t)
        """)
        
        # 根腐病/黑粉病 -> 多菌灵
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['根腐病', '黑粉病']
            MATCH (t:Treatment {name: '多菌灵'})
            MERGE (d)-[:TREATED_BY]->(t)
        """)
        
        # 小麦爆发病 -> 多菌灵
        session.run("""
            MATCH (d:Disease {name: '小麦爆发病'})
            MATCH (t:Treatment {name: '多菌灵'})
            MERGE (d)-[:TREATED_BY]->(t)
        """)
        
        print("✅ 病害与治疗药剂关联建立完成")
        
        # 9. 创建症状关键词节点
        print("📝 创建症状关键词节点...")
        symptoms_query = """
        CREATE (s_yellow:Symptom {name: '黄色条纹', keywords: ['黄色', '条纹', '条锈', '鲜黄']})
        CREATE (s_rust:Symptom {name: '锈斑', keywords: ['锈斑', '锈病', '红褐', '粉末']})
        CREATE (s_white:Symptom {name: '白色霉层', keywords: ['白色', '霉层', '绒毛', '白粉']})
        CREATE (s_black:Symptom {name: '黑粉', keywords: ['黑粉', '黑色', '黑病']})
        CREATE (s_rot:Symptom {name: '腐烂', keywords: ['腐烂', '根腐', '变黑', '软腐']})
        CREATE (s_spot:Symptom {name: '病斑', keywords: ['病斑', '斑点', '褐斑', '叶斑']})
        CREATE (s_insect:Symptom {name: '虫害', keywords: ['虫', '蚜虫', '螨虫', '蛀孔']})
        CREATE (s_pink:Symptom {name: '粉红色霉层', keywords: ['粉红', '粉色', '霉层', '赤霉']})
        """
        session.run(symptoms_query)
        print("✅ 症状关键词节点创建完成")
        
        # 10. 建立病害与症状的关联
        print("🔗 建立病害与症状的关联...")
        
        # 条锈病 -> 黄色条纹
        session.run("""
            MATCH (d:Disease {name: '条锈病'})
            MATCH (s:Symptom {name: '黄色条纹'})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
        """)
        
        # 锈病类 -> 锈斑
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['锈病', '茎锈病', '叶锈病']
            MATCH (s:Symptom {name: '锈斑'})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
        """)
        
        # 白粉病 -> 白色霉层
        session.run("""
            MATCH (d:Disease {name: '白粉病'})
            MATCH (s:Symptom {name: '白色霉层'})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
        """)
        
        # 黑粉病 -> 黑粉
        session.run("""
            MATCH (d:Disease {name: '黑粉病'})
            MATCH (s:Symptom {name: '黑粉'})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
        """)
        
        # 根腐病 -> 腐烂
        session.run("""
            MATCH (d:Disease {name: '根腐病'})
            MATCH (s:Symptom {name: '腐烂'})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
        """)
        
        # 叶斑病类 -> 病斑
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['叶斑病', '壳针孢叶斑病', '斑点叶斑病', '褐斑病']
            MATCH (s:Symptom {name: '病斑'})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
        """)
        
        # 蚜虫/螨虫/茎蝇 -> 虫害
        session.run("""
            MATCH (d:Disease) WHERE d.name IN ['蚜虫', '螨虫', '茎蝇']
            MATCH (s:Symptom {name: '虫害'})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
        """)
        
        # 赤霉病 -> 粉红色霉层
        session.run("""
            MATCH (d:Disease {name: '赤霉病'})
            MATCH (s:Symptom {name: '粉红色霉层'})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
        """)
        
        print("✅ 病害与症状关联建立完成")
        
        # 11. 验证数据
        print("🔍 验证数据...")
        result = session.run("MATCH (n) RETURN count(n) as total_count")
        total = result.single()["total_count"]
        print(f"✅ 总共创建了 {total} 个节点")
        
        result = session.run("MATCH ()-[r]->() RETURN count(r) as total_count")
        total = result.single()["total_count"]
        print(f"✅ 总共创建了 {total} 条关系")
        
    driver.close()
    print("\n🎉 知识图谱初始化完成！")

if __name__ == "__main__":
    init_knowledge_graph()

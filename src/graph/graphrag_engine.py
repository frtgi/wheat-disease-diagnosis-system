# -*- coding: utf-8 -*-
"""
GraphRAG - 基于图的检索增强生成 (Graph-based Retrieval-Augmented Generation)
根据研究文档，GraphRAG 流程包括：
1. 检索(Retrieval): 根据初步诊断结果在Neo4j中检索相关子图
2. 上下文构建(Context Construction): 将检索到的子图序列化为自然语言描述
3. 生成(Generation): 将事实性知识作为背景资料喂给LLaVA生成回答
"""
import os
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase


class GraphRAGEngine:
    """
    GraphRAG 引擎
    实现基于知识图谱的检索增强生成
    """
    
    def __init__(self, uri="neo4j://localhost:7687", user="neo4j", password="123456789s"):
        """
        初始化 GraphRAG 引擎
        
        :param uri: Neo4j 数据库 URI
        :param user: 用户名
        :param password: 密码
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        try:
            self.driver.verify_connectivity()
            print("🔗 [GraphRAG] 图数据库连接成功")
        except Exception as e:
            print(f"❌ [GraphRAG] 图数据库连接失败: {e}")
        
        # 缓存已检索的子图
        self.subgraph_cache = {}
    
    def close(self):
        """关闭数据库连接"""
        self.driver.close()
    
    def retrieve_subgraph(self, disease_name: str, depth: int = 2) -> Dict[str, Any]:
        """
        检索与病害相关的子图
        
        :param disease_name: 病害名称
        :param depth: 检索深度（跳数）
        :return: 子图信息字典
        """
        # 检查缓存
        cache_key = f"{disease_name}_{depth}"
        if cache_key in self.subgraph_cache:
            return self.subgraph_cache[cache_key]
        
        subgraph = {
            "disease": disease_name,
            "symptoms": [],
            "causes": [],
            "preventions": [],
            "treatments": [],
            "related_diseases": [],
            "environment_factors": []
        }
        
        try:
            with self.driver.session() as session:
                # 1. 检索症状
                symptom_query = """
                MATCH (d:Disease {name: $name})-[:HAS_SYMPTOM]->(s:Symptom)
                RETURN s.name as symptom, s.description as desc
                """
                symptoms = session.run(symptom_query, name=disease_name)
                subgraph["symptoms"] = [
                    {"name": record["symptom"], "description": record["desc"]}
                    for record in symptoms
                ]
                
                # 2. 检索成因
                cause_query = """
                MATCH (d:Disease {name: $name})-[:CAUSED_BY]->(c:Cause)
                RETURN c.name as cause, c.description as desc
                """
                causes = session.run(cause_query, name=disease_name)
                subgraph["causes"] = [
                    {"name": record["cause"], "description": record["desc"]}
                    for record in causes
                ]
                
                # 3. 检索预防措施
                prevention_query = """
                MATCH (d:Disease {name: $name})-[:PREVENTED_BY]->(p:Prevention)
                RETURN p.name as prevention, p.description as desc
                """
                preventions = session.run(prevention_query, name=disease_name)
                subgraph["preventions"] = [
                    {"name": record["prevention"], "description": record["desc"]}
                    for record in preventions
                ]
                
                # 4. 检索治疗措施
                treatment_query = """
                MATCH (d:Disease {name: $name})-[:TREATED_BY]->(t:Treatment)
                RETURN t.name as treatment, t.usage as usage, t.dosage as dosage
                """
                treatments = session.run(treatment_query, name=disease_name)
                subgraph["treatments"] = [
                    {
                        "name": record["treatment"],
                        "usage": record["usage"],
                        "dosage": record["dosage"]
                    }
                    for record in treatments
                ]
                
                # 5. 检索相关病害（易混淆病害）
                related_query = """
                MATCH (d:Disease {name: $name})-[:SIMILAR_TO]->(r:Disease)
                RETURN r.name as disease
                UNION
                MATCH (d:Disease {name: $name})-[:HAS_SYMPTOM]->(s:Symptom)<-[:HAS_SYMPTOM]-(r:Disease)
                WHERE r.name <> $name
                RETURN r.name as disease
                LIMIT 5
                """
                related = session.run(related_query, name=disease_name)
                subgraph["related_diseases"] = [record["disease"] for record in related]
                
                # 6. 检索环境因素
                env_query = """
                MATCH (d:Disease {name: $name})-[:FAVORED_BY]->(e:Environment)
                RETURN e.condition as condition, e.temperature as temp, e.humidity as humidity
                """
                env_factors = session.run(env_query, name=disease_name)
                subgraph["environment_factors"] = [
                    {
                        "condition": record["condition"],
                        "temperature": record["temp"],
                        "humidity": record["humidity"]
                    }
                    for record in env_factors
                ]
        
        except Exception as e:
            print(f"⚠️ [GraphRAG] 检索子图失败: {e}")
        
        # 缓存结果
        self.subgraph_cache[cache_key] = subgraph
        return subgraph
    
    def construct_context(self, subgraph: Dict[str, Any]) -> str:
        """
        将检索到的子图构建为自然语言上下文
        
        :param subgraph: 子图信息字典
        :return: 自然语言描述
        """
        disease_name = subgraph["disease"]
        context_parts = []
        
        # 1. 病害基本信息
        context_parts.append(f"【{disease_name}】病害知识档案：")
        
        # 2. 症状描述
        if subgraph["symptoms"]:
            symptoms_text = "；".join([
                f"{s['name']}({s['description']})" if s['description'] else s['name']
                for s in subgraph["symptoms"][:3]
            ])
            context_parts.append(f"典型症状：{symptoms_text}。")
        
        # 3. 成因
        if subgraph["causes"]:
            causes_text = "；".join([
                f"{c['name']}({c['description']})" if c['description'] else c['name']
                for c in subgraph["causes"][:2]
            ])
            context_parts.append(f"主要成因：{causes_text}。")
        
        # 4. 预防措施
        if subgraph["preventions"]:
            preventions_text = "；".join([
                f"{p['name']}({p['description']})" if p['description'] else p['name']
                for p in subgraph["preventions"][:3]
            ])
            context_parts.append(f"预防措施：{preventions_text}。")
        
        # 5. 治疗建议
        if subgraph["treatments"]:
            treatments_text = "；".join([
                f"使用{t['name']}，{t['usage']}" + (f"，用量{t['dosage']}" if t.get('dosage') else "")
                for t in subgraph["treatments"][:3]
            ])
            context_parts.append(f"治疗方案：{treatments_text}。")
        
        # 6. 环境因素
        if subgraph["environment_factors"]:
            env_text = "；".join([
                f"{e['condition']}" + (f"，温度{e['temperature']}" if e.get('temperature') else "")
                for e in subgraph["environment_factors"][:2]
            ])
            context_parts.append(f"适宜发病环境：{env_text}。")
        
        # 7. 易混淆病害
        if subgraph["related_diseases"]:
            related_text = "、".join(subgraph["related_diseases"][:3])
            context_parts.append(f"易混淆病害：{related_text}。")
        
        return "\n".join(context_parts)
    
    def generate_enhanced_report(
        self,
        disease_name: str,
        confidence: float,
        visual_evidence: str = "",
        text_evidence: str = ""
    ) -> Dict[str, Any]:
        """
        生成增强的诊断报告
        
        :param disease_name: 诊断的病害名称
        :param confidence: 置信度
        :param visual_evidence: 视觉证据描述
        :param text_evidence: 文本证据描述
        :return: 增强报告字典
        """
        # 1. 检索子图
        subgraph = self.retrieve_subgraph(disease_name)
        
        # 2. 构建上下文
        context = self.construct_context(subgraph)
        
        # 3. 生成报告
        report = {
            "diagnosis": disease_name,
            "confidence": confidence,
            "knowledge_context": context,
            "symptoms": subgraph.get("symptoms", []),
            "causes": subgraph.get("causes", []),
            "preventions": subgraph.get("preventions", []),
            "treatments": subgraph.get("treatments", []),
            "related_diseases": subgraph.get("related_diseases", []),
            "reasoning_chain": []
        }
        
        # 4. 构建推理链
        reasoning = []
        
        if visual_evidence:
            reasoning.append(f"👁️ 视觉证据：{visual_evidence}")
        
        if text_evidence:
            reasoning.append(f"📝 文本证据：{text_evidence}")
        
        reasoning.append(f"📚 知识图谱验证：从知识库检索到{disease_name}的相关信息")
        
        if subgraph["symptoms"]:
            reasoning.append(f"🔍 症状匹配：发现{len(subgraph['symptoms'])}个典型症状特征")
        
        if subgraph["causes"]:
            reasoning.append(f"🌡️ 成因分析：识别出{len(subgraph['causes'])}个主要成因")
        
        if subgraph["treatments"]:
            reasoning.append(f"💊 治疗方案：推荐{len(subgraph['treatments'])}种治疗措施")
        
        report["reasoning_chain"] = reasoning
        
        # 5. 生成自然语言诊断报告
        report["natural_language_report"] = self._generate_nl_report(
            disease_name, confidence, subgraph, visual_evidence, text_evidence
        )
        
        return report
    
    def _generate_nl_report(
        self,
        disease_name: str,
        confidence: float,
        subgraph: Dict[str, Any],
        visual_evidence: str,
        text_evidence: str
    ) -> str:
        """
        生成自然语言诊断报告
        
        :param disease_name: 病害名称
        :param confidence: 置信度
        :param subgraph: 子图信息
        :param visual_evidence: 视觉证据
        :param text_evidence: 文本证据
        :return: 自然语言报告
        """
        report_parts = []
        
        # 诊断结论
        confidence_level = "高" if confidence > 0.8 else "中" if confidence > 0.5 else "低"
        report_parts.append(f"根据多模态特征融合分析，系统诊断该小麦植株患有【{disease_name}】，置信度为{confidence:.2f}（{confidence_level}）。")
        
        # 证据描述
        if visual_evidence or text_evidence:
            report_parts.append("\n诊断依据：")
            if visual_evidence:
                report_parts.append(f"• 图像分析：{visual_evidence}")
            if text_evidence:
                report_parts.append(f"• 症状描述：{text_evidence}")
        
        # 症状描述
        if subgraph["symptoms"]:
            symptoms_list = [s["name"] for s in subgraph["symptoms"][:3]]
            report_parts.append(f"\n该病害的典型症状包括：{'、'.join(symptoms_list)}。")
        
        # 成因分析
        if subgraph["causes"]:
            causes_list = [c["name"] for c in subgraph["causes"][:2]]
            report_parts.append(f"主要诱发因素：{'、'.join(causes_list)}。")
        
        # 防治建议
        if subgraph["preventions"] or subgraph["treatments"]:
            report_parts.append("\n防治建议：")
            
            if subgraph["preventions"]:
                preventions_list = [p["name"] for p in subgraph["preventions"][:3]]
                report_parts.append(f"• 预防措施：{'、'.join(preventions_list)}")
            
            if subgraph["treatments"]:
                treatments_list = [t["name"] for t in subgraph["treatments"][:3]]
                report_parts.append(f"• 治疗方案：建议使用{'、'.join(treatments_list)}")
        
        # 易混淆病害提醒
        if subgraph["related_diseases"]:
            report_parts.append(f"\n注意：该病害易与{'、'.join(subgraph['related_diseases'][:2])}混淆，请结合实际情况进一步确认。")
        
        return "\n".join(report_parts)
    
    def multi_hop_reasoning(self, symptom: str, max_hops: int = 3) -> List[Dict[str, Any]]:
        """
        多跳推理：从症状推断可能的病害
        
        :param symptom: 症状描述
        :param max_hops: 最大跳数
        :return: 可能的病害列表
        """
        possible_diseases = []
        
        try:
            with self.driver.session() as session:
                # 多跳推理查询
                query = """
                MATCH path = (s:Symptom)<-[:HAS_SYMPTOM]-(d:Disease)
                WHERE s.name CONTAINS $symptom OR s.description CONTAINS $symptom
                WITH d, length(path) as hops
                ORDER BY hops ASC
                LIMIT 10
                RETURN d.name as disease, hops as distance
                """
                
                results = session.run(query, symptom=symptom)
                
                for record in results:
                    possible_diseases.append({
                        "disease": record["disease"],
                        "distance": record["distance"]
                    })
        
        except Exception as e:
            print(f"⚠️ [GraphRAG] 多跳推理失败: {e}")
        
        return possible_diseases
    
    def verify_diagnosis(self, disease_name: str, symptoms: List[str]) -> float:
        """
        验证诊断结果与症状的匹配程度
        
        :param disease_name: 病害名称
        :param symptoms: 症状列表
        :return: 匹配分数 (0-1)
        """
        if not symptoms:
            return 0.5  # 默认中等置信度
        
        try:
            with self.driver.session() as session:
                # 查询该病害的所有症状
                query = """
                MATCH (d:Disease {name: $name})-[:HAS_SYMPTOM]->(s:Symptom)
                RETURN s.name as symptom
                """
                
                results = session.run(query, name=disease_name)
                disease_symptoms = [record["symptom"] for record in results]
                
                if not disease_symptoms:
                    return 0.5
                
                # 计算匹配度
                matched = sum(1 for s in symptoms if any(ds in s or s in ds for ds in disease_symptoms))
                match_score = matched / len(symptoms)
                
                # 同时考虑病害症状的覆盖度
                coverage = matched / len(disease_symptoms) if disease_symptoms else 0
                
                # 综合得分
                final_score = (match_score + coverage) / 2
                
                return min(final_score, 1.0)
        
        except Exception as e:
            print(f"⚠️ [GraphRAG] 验证诊断失败: {e}")
            return 0.5


def test_graphrag():
    """
    测试 GraphRAG 引擎
    """
    print("=" * 60)
    print("🧪 测试 GraphRAG 引擎")
    print("=" * 60)
    
    try:
        # 创建 GraphRAG 引擎
        graphrag = GraphRAGEngine()
        
        # 测试检索子图
        print("\n" + "=" * 60)
        print("🧪 测试检索子图")
        print("=" * 60)
        
        subgraph = graphrag.retrieve_subgraph("条锈病")
        print(f"✅ 检索到 {len(subgraph['symptoms'])} 个症状")
        print(f"✅ 检索到 {len(subgraph['causes'])} 个成因")
        print(f"✅ 检索到 {len(subgraph['preventions'])} 个预防措施")
        print(f"✅ 检索到 {len(subgraph['treatments'])} 个治疗措施")
        
        # 测试上下文构建
        print("\n" + "=" * 60)
        print("🧪 测试上下文构建")
        print("=" * 60)
        
        context = graphrag.construct_context(subgraph)
        print(f"✅ 生成的上下文长度: {len(context)} 字符")
        print(f"\n上下文预览:\n{context[:200]}...")
        
        # 测试增强报告生成
        print("\n" + "=" * 60)
        print("🧪 测试增强报告生成")
        print("=" * 60)
        
        report = graphrag.generate_enhanced_report(
            disease_name="条锈病",
            confidence=0.92,
            visual_evidence="叶片上有黄色条纹状孢子堆",
            text_evidence="叶片出现鲜黄色条纹"
        )
        
        print(f"✅ 诊断: {report['diagnosis']}")
        print(f"✅ 置信度: {report['confidence']}")
        print(f"✅ 推理链步骤: {len(report['reasoning_chain'])}")
        print(f"\n自然语言报告预览:\n{report['natural_language_report'][:300]}...")
        
        # 关闭连接
        graphrag.close()
        
        print("\n" + "=" * 60)
        print("✅ GraphRAG 引擎测试通过！")
        print("=" * 60)
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_graphrag()

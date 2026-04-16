# -*- coding: utf-8 -*-
"""
知识图谱功能测试脚本

测试内容：
1. 测试知识查询接口 - GET /api/v1/knowledge/search
2. 测试病害信息检索 - 条锈病、叶锈病、白粉病等
3. 测试知识图谱连接 - Neo4j 数据库连接
"""
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)


class KnowledgeGraphTester:
    """知识图谱测试类"""
    
    def __init__(self):
        """初始化测试器"""
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "api_tests": {},
            "neo4j_tests": {},
            "graphrag_tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
        self.api_base_url = "http://localhost:8000/api/v1"
        self.neo4j_config = {
            "uri": os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            "user": os.environ.get("NEO4J_USER", "neo4j"),
            "password": os.environ.get("NEO4J_PASSWORD", "123456789s")
        }
    
    def _update_summary(self, status: str):
        """
        更新测试摘要
        
        Args:
            status: 测试状态 (passed/failed/warning)
        """
        self.results["summary"]["total_tests"] += 1
        if status == "passed":
            self.results["summary"]["passed"] += 1
        elif status == "failed":
            self.results["summary"]["failed"] += 1
        elif status == "warning":
            self.results["summary"]["warnings"] += 1
    
    def test_neo4j_connection(self) -> Dict[str, Any]:
        """
        测试 Neo4j 数据库连接
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        print("\n" + "=" * 60)
        print("[测试 1] Neo4j 数据库连接")
        print("=" * 60)
        
        result = {
            "test_name": "Neo4j 连接测试",
            "status": "failed",
            "message": "",
            "details": {}
        }
        
        try:
            from neo4j import GraphDatabase
            
            print(f"  连接参数:")
            print(f"    URI: {self.neo4j_config['uri']}")
            print(f"    用户: {self.neo4j_config['user']}")
            
            driver = GraphDatabase.driver(
                self.neo4j_config["uri"],
                auth=(self.neo4j_config["user"], self.neo4j_config["password"]),
                max_connection_lifetime=30,
                connection_timeout=10.0
            )
            
            driver.verify_connectivity()
            print("  [OK] Neo4j 连接成功")
            result["status"] = "passed"
            result["message"] = "连接成功"
            
            with driver.session() as session:
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_result.single()['count']
                
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = rel_result.single()['count']
                
                result["details"]["node_count"] = node_count
                result["details"]["relationship_count"] = rel_count
                
                print(f"  节点数量: {node_count}")
                print(f"  关系数量: {rel_count}")
                
                label_result = session.run('''
                    MATCH (n)
                    RETURN labels(n)[0] as label, count(n) as count
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                
                print("  节点类型分布 (Top 10):")
                label_counts = []
                for record in label_result:
                    label_counts.append({"label": record["label"], "count": record["count"]})
                    print(f"    - {record['label']}: {record['count']}")
                
                result["details"]["label_distribution"] = label_counts
            
            driver.close()
            
        except ImportError as e:
            result["status"] = "failed"
            result["message"] = f"neo4j 库未安装: {e}"
            print(f"  [FAIL] neo4j 库未安装: {e}")
            
        except Exception as e:
            result["status"] = "failed"
            result["message"] = str(e)
            print(f"  [FAIL] Neo4j 连接失败: {e}")
        
        self._update_summary(result["status"])
        self.results["neo4j_tests"]["connection"] = result
        return result
    
    def test_knowledge_api_search(self) -> Dict[str, Any]:
        """
        测试知识查询 API 接口
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        print("\n" + "=" * 60)
        print("[测试 2] 知识查询 API 接口")
        print("=" * 60)
        
        result = {
            "test_name": "知识查询 API 测试",
            "status": "failed",
            "message": "",
            "details": {}
        }
        
        try:
            import requests
            
            test_queries = [
                {"keyword": "条锈病", "description": "搜索条锈病"},
                {"keyword": "叶锈病", "description": "搜索叶锈病"},
                {"keyword": "白粉病", "description": "搜索白粉病"},
                {"keyword": "锈病", "description": "模糊搜索锈病"},
                {"category": "真菌病害", "description": "按分类搜索"},
            ]
            
            api_url = f"{self.api_base_url}/knowledge/search"
            print(f"  API 地址: {api_url}")
            
            query_results = []
            
            for query in test_queries:
                try:
                    params = {}
                    if "keyword" in query:
                        params["keyword"] = query["keyword"]
                    if "category" in query:
                        params["category"] = query["category"]
                    
                    print(f"\n  测试: {query['description']}")
                    print(f"    参数: {params}")
                    
                    start_time = time.time()
                    response = requests.get(api_url, params=params, timeout=10)
                    elapsed_time = (time.time() - start_time) * 1000
                    
                    query_result = {
                        "query": query,
                        "status_code": response.status_code,
                        "elapsed_ms": round(elapsed_time, 2),
                        "success": False
                    }
                    
                    if response.status_code == 200:
                        data = response.json()
                        query_result["success"] = True
                        query_result["result_count"] = len(data) if isinstance(data, list) else 1
                        query_result["sample"] = data[0] if isinstance(data, list) and len(data) > 0 else data
                        
                        print(f"    [OK] 成功 (HTTP {response.status_code})")
                        print(f"    响应时间: {elapsed_time:.2f}ms")
                        print(f"    结果数量: {query_result['result_count']}")
                        
                        if isinstance(data, list) and len(data) > 0:
                            sample = data[0]
                            print(f"    示例结果:")
                            print(f"      - 名称: {sample.get('name', 'N/A')}")
                            print(f"      - 分类: {sample.get('category', 'N/A')}")
                            symptoms = sample.get('symptoms', 'N/A')
                            if symptoms and len(symptoms) > 50:
                                symptoms = symptoms[:50] + "..."
                            print(f"      - 症状: {symptoms}")
                    else:
                        query_result["error"] = response.text
                        print(f"    [FAIL] 失败 (HTTP {response.status_code})")
                        print(f"    错误: {response.text[:100]}")
                    
                    query_results.append(query_result)
                    
                except requests.exceptions.ConnectionError:
                    query_result = {"query": query, "error": "无法连接到 API 服务"}
                    query_results.append(query_result)
                    print(f"    [FAIL] 无法连接到 API 服务")
                    print(f"    请确保后端服务已启动: python run_web.py")
                    
                except Exception as e:
                    query_result = {"query": query, "error": str(e)}
                    query_results.append(query_result)
                    print(f"    [FAIL] 请求失败: {e}")
            
            result["details"]["queries"] = query_results
            
            success_count = sum(1 for q in query_results if q.get("success"))
            if success_count == len(test_queries):
                result["status"] = "passed"
                result["message"] = f"所有 {len(test_queries)} 个查询测试通过"
            elif success_count > 0:
                result["status"] = "warning"
                result["message"] = f"{success_count}/{len(test_queries)} 个查询测试通过"
            else:
                result["status"] = "failed"
                result["message"] = "所有查询测试失败"
            
        except ImportError as e:
            result["status"] = "failed"
            result["message"] = f"requests 库未安装: {e}"
            print(f"  [FAIL] requests 库未安装: {e}")
            
        except Exception as e:
            result["status"] = "failed"
            result["message"] = str(e)
            print(f"  [FAIL] API 测试失败: {e}")
        
        self._update_summary(result["status"])
        self.results["api_tests"]["search"] = result
        return result
    
    def test_disease_retrieval(self) -> Dict[str, Any]:
        """
        测试病害信息检索
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        print("\n" + "=" * 60)
        print("[测试 3] 病害信息检索")
        print("=" * 60)
        
        result = {
            "test_name": "病害信息检索测试",
            "status": "failed",
            "message": "",
            "details": {}
        }
        
        test_diseases = [
            "小麦条锈病",
            "小麦叶锈病",
            "小麦白粉病",
            "小麦赤霉病",
            "小麦根腐病"
        ]
        
        disease_results = []
        
        try:
            from src.graph.graphrag_engine import GraphRAGEngine
            
            engine = GraphRAGEngine(
                uri=self.neo4j_config["uri"],
                user=self.neo4j_config["user"],
                password=self.neo4j_config["password"]
            )
            
            if not engine.is_connected():
                print("  [WARN] GraphRAG 引擎未连接到 Neo4j，使用降级模式")
                result["status"] = "warning"
                result["message"] = "Neo4j 未连接，使用降级模式"
            
            for disease_name in test_diseases:
                print(f"\n  测试病害: {disease_name}")
                
                disease_result = {
                    "disease": disease_name,
                    "found": False,
                    "symptoms_count": 0,
                    "causes_count": 0,
                    "treatments_count": 0,
                    "preventions_count": 0,
                    "completeness": 0
                }
                
                try:
                    subgraph = engine.retrieve_subgraph(disease_name)
                    
                    symptoms = subgraph.get("symptoms", [])
                    causes = subgraph.get("causes", [])
                    treatments = subgraph.get("treatments", [])
                    preventions = subgraph.get("preventions", [])
                    
                    disease_result["symptoms_count"] = len(symptoms)
                    disease_result["causes_count"] = len(causes)
                    disease_result["treatments_count"] = len(treatments)
                    disease_result["preventions_count"] = len(preventions)
                    
                    total_fields = 4
                    filled_fields = sum([
                        1 if symptoms else 0,
                        1 if causes else 0,
                        1 if treatments else 0,
                        1 if preventions else 0
                    ])
                    disease_result["completeness"] = filled_fields / total_fields
                    disease_result["found"] = filled_fields > 0
                    
                    print(f"    症状: {len(symptoms)} 条")
                    print(f"    病因: {len(causes)} 条")
                    print(f"    治疗: {len(treatments)} 条")
                    print(f"    预防: {len(preventions)} 条")
                    print(f"    完整度: {disease_result['completeness']*100:.0f}%")
                    
                    if disease_result["found"]:
                        print(f"    [OK] 检索成功")
                    else:
                        print(f"    [WARN] 未找到相关信息")
                    
                except Exception as e:
                    disease_result["error"] = str(e)
                    print(f"    [FAIL] 检索失败: {e}")
                
                disease_results.append(disease_result)
            
            engine.close()
            
            found_count = sum(1 for d in disease_results if d["found"])
            avg_completeness = sum(d["completeness"] for d in disease_results) / len(disease_results)
            
            result["details"]["diseases"] = disease_results
            result["details"]["found_count"] = found_count
            result["details"]["avg_completeness"] = round(avg_completeness, 2)
            
            if found_count == len(test_diseases) and avg_completeness >= 0.75:
                result["status"] = "passed"
                result["message"] = f"所有 {len(test_diseases)} 个病害检索成功，平均完整度 {avg_completeness*100:.0f}%"
            elif found_count > 0:
                result["status"] = "warning"
                result["message"] = f"{found_count}/{len(test_diseases)} 个病害检索成功，平均完整度 {avg_completeness*100:.0f}%"
            else:
                result["status"] = "failed"
                result["message"] = "所有病害检索失败"
            
        except ImportError as e:
            result["status"] = "failed"
            result["message"] = f"GraphRAG 引擎导入失败: {e}"
            print(f"  [FAIL] GraphRAG 引擎导入失败: {e}")
            
        except Exception as e:
            result["status"] = "failed"
            result["message"] = str(e)
            print(f"  [FAIL] 病害检索测试失败: {e}")
        
        self._update_summary(result["status"])
        self.results["graphrag_tests"]["disease_retrieval"] = result
        return result
    
    def test_graphrag_service(self) -> Dict[str, Any]:
        """
        测试 GraphRAG 服务
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        print("\n" + "=" * 60)
        print("[测试 4] GraphRAG 服务")
        print("=" * 60)
        
        result = {
            "test_name": "GraphRAG 服务测试",
            "status": "failed",
            "message": "",
            "details": {}
        }
        
        try:
            from src.web.backend.app.services.graphrag_service import GraphRAGService, get_graphrag_service
            
            service = get_graphrag_service()
            
            init_status = "[OK] 已初始化" if service._initialized else "[WARN] 未初始化"
            print(f"  服务初始化状态: {init_status}")
            result["details"]["initialized"] = service._initialized
            
            test_cases = [
                {"symptoms": "叶片出现黄色条纹状病斑", "disease_hint": "小麦条锈病"},
                {"symptoms": "叶片上有白色粉状霉层", "disease_hint": "小麦白粉病"},
                {"symptoms": "穗部出现粉红色霉层", "disease_hint": "小麦赤霉病"},
            ]
            
            retrieval_results = []
            
            for case in test_cases:
                print(f"\n  测试案例:")
                print(f"    症状: {case['symptoms']}")
                print(f"    病害提示: {case['disease_hint']}")
                
                context = service.retrieve_knowledge(
                    symptoms=case["symptoms"],
                    disease_hint=case["disease_hint"]
                )
                
                retrieval_result = {
                    "case": case,
                    "triples_count": len(context.triples),
                    "entities_count": len(context.entities),
                    "has_tokens": bool(context.tokens),
                    "tokens_preview": context.tokens[:200] if context.tokens else ""
                }
                
                print(f"    三元组数量: {len(context.triples)}")
                print(f"    实体数量: {len(context.entities)}")
                token_status = "[OK] 已生成" if context.tokens else "[FAIL] 未生成"
                print(f"    Token 文本: {token_status}")
                
                if context.tokens:
                    print(f"    Token 预览:")
                    for line in context.tokens.split('\n')[:5]:
                        print(f"      {line}")
                
                retrieval_results.append(retrieval_result)
            
            result["details"]["retrievals"] = retrieval_results
            
            stats = service.get_stats()
            result["details"]["stats"] = stats
            print(f"\n  服务统计:")
            print(f"    {json.dumps(stats, ensure_ascii=False, indent=4)}")
            
            success_count = sum(1 for r in retrieval_results if r["triples_count"] > 0)
            if success_count == len(test_cases):
                result["status"] = "passed"
                result["message"] = f"所有 {len(test_cases)} 个检索测试通过"
            elif success_count > 0:
                result["status"] = "warning"
                result["message"] = f"{success_count}/{len(test_cases)} 个检索测试通过"
            else:
                result["status"] = "failed"
                result["message"] = "所有检索测试失败"
            
        except ImportError as e:
            result["status"] = "failed"
            result["message"] = f"GraphRAG 服务导入失败: {e}"
            print(f"  [FAIL] GraphRAG 服务导入失败: {e}")
            
        except Exception as e:
            result["status"] = "failed"
            result["message"] = str(e)
            print(f"  [FAIL] GraphRAG 服务测试失败: {e}")
        
        self._update_summary(result["status"])
        self.results["graphrag_tests"]["service"] = result
        return result
    
    def test_knowledge_database(self) -> Dict[str, Any]:
        """
        测试知识库数据库
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        print("\n" + "=" * 60)
        print("[测试 5] 知识库数据库")
        print("=" * 60)
        
        result = {
            "test_name": "知识库数据库测试",
            "status": "failed",
            "message": "",
            "details": {}
        }
        
        try:
            from src.web.backend.app.core.database import SessionLocal
            from src.web.backend.app.models.disease import Disease
            
            db = SessionLocal()
            
            try:
                total_count = db.query(Disease).count()
                print(f"  知识库总记录数: {total_count}")
                result["details"]["total_count"] = total_count
                
                categories = db.query(Disease.category).filter(
                    Disease.category.isnot(None)
                ).distinct().all()
                category_list = [cat[0] for cat in categories if cat[0]]
                result["details"]["categories"] = category_list
                print(f"  病害分类: {category_list}")
                
                sample_diseases = db.query(Disease).limit(5).all()
                sample_data = []
                print(f"\n  示例病害 (前5条):")
                for disease in sample_diseases:
                    sample_data.append({
                        "id": disease.id,
                        "name": disease.name,
                        "category": disease.category,
                        "has_symptoms": bool(disease.symptoms),
                        "has_treatments": bool(disease.treatments),
                        "has_prevention": bool(disease.prevention)
                    })
                    print(f"    - {disease.name} ({disease.category or '未分类'})")
                    print(f"      症状: {'[OK]' if disease.symptoms else '[FAIL]'}")
                    print(f"      治疗: {'[OK]' if disease.treatments else '[FAIL]'}")
                    print(f"      预防: {'[OK]' if disease.prevention else '[FAIL]'}")
                
                result["details"]["samples"] = sample_data
                
                if total_count > 0:
                    result["status"] = "passed"
                    result["message"] = f"知识库包含 {total_count} 条记录"
                else:
                    result["status"] = "warning"
                    result["message"] = "知识库为空"
                
            finally:
                db.close()
            
        except ImportError as e:
            result["status"] = "failed"
            result["message"] = f"数据库模块导入失败: {e}"
            print(f"  [FAIL] 数据库模块导入失败: {e}")
            
        except Exception as e:
            result["status"] = "failed"
            result["message"] = str(e)
            print(f"  [FAIL] 数据库测试失败: {e}")
        
        self._update_summary(result["status"])
        self.results["api_tests"]["database"] = result
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        运行所有测试
        
        Returns:
            Dict[str, Any]: 完整测试报告
        """
        print("=" * 70)
        print("[知识图谱功能测试]")
        print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        self.test_neo4j_connection()
        self.test_knowledge_api_search()
        self.test_disease_retrieval()
        self.test_graphrag_service()
        self.test_knowledge_database()
        
        print("\n" + "=" * 70)
        print("[测试结果汇总]")
        print("=" * 70)
        
        summary = self.results["summary"]
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  [PASS] 通过: {summary['passed']}")
        print(f"  [FAIL] 失败: {summary['failed']}")
        print(f"  [WARN] 警告: {summary['warnings']}")
        
        pass_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        print(f"  通过率: {pass_rate:.1f}%")
        
        if summary['failed'] == 0 and summary['warnings'] == 0:
            print("\n[OK] 所有测试通过！")
        elif summary['failed'] == 0:
            print("\n[WARN] 测试完成，但有警告")
        else:
            print("\n[FAIL] 部分测试失败")
        
        report_path = os.path.join(project_root, "logs", "knowledge_graph_test_report.json")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n[报告] 详细报告已保存: {report_path}")
        
        return self.results


def main():
    """主函数"""
    tester = KnowledgeGraphTester()
    results = tester.run_all_tests()
    
    if results["summary"]["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

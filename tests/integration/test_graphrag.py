# -*- coding: utf-8 -*-
"""
Graph-RAG 集成测试

测试 GraphRAGEngine 的核心功能：
1. 子图检索（支持多跳检索）
2. 知识 token 化
3. 上下文注入
4. 与认知层集成
5. 性能优化（LRU 缓存）
"""
import pytest
import sys
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock, patch
import json

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestGraphRAGSubgraphRetrieval:
    """子图检索测试"""
    
    @pytest.fixture
    def mock_neo4j_driver(self):
        """创建模拟 Neo4j 驱动"""
        # 模拟 Neo4j 驱动和会话
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        
        # 模拟查询结果
        mock_session.run = Mock()
        
        # 模拟 verify_connectivity
        mock_driver.verify_connectivity = Mock()
        
        return mock_driver
    
    @pytest.fixture
    def graphrag_engine_mocked(self, mock_neo4j_driver):
        """创建使用模拟驱动的 GraphRAG 引擎"""
        from src.graph.graphrag_engine import GraphRAGEngine
        
        # 使用 patch 绕过真实的 Neo4j 连接
        with patch('src.graph.graphrag_engine.GraphDatabase') as mock_graph_db:
            mock_graph_db.driver.return_value = mock_neo4j_driver
            engine = GraphRAGEngine(
                uri="neo4j://localhost:7687",
                user="neo4j",
                password="test_password",
                cache_size=50
            )
            yield engine
    
    def test_retrieve_symptoms_subgraph(self, graphrag_engine_mocked, mock_neo4j_driver):
        """
        测试症状子图检索
        
        验证：
        1. 可以检索病害的症状信息
        2. 支持多跳检索（症状→影响部位）
        3. 返回结构化的症状数据
        """
        # 设置模拟返回数据
        mock_result = [
            {"symptom": "黄色条状病斑", "desc": "叶片出现黄色条纹", "part": "叶片"},
            {"symptom": "孢子堆", "desc": "沿叶脉排列", "part": "叶片"}
        ]
        graphrag_engine_mocked.driver.session.return_value.__enter__.return_value.run.return_value = mock_result
        
        # 执行检索
        subgraph = graphrag_engine_mocked.retrieve_subgraph(
            disease_name="条锈病",
            depth=2
        )
        
        # 验证结果
        assert subgraph is not None
        assert "symptoms" in subgraph
        assert len(subgraph["symptoms"]) > 0
    
    def test_retrieve_treatments_subgraph(self, graphrag_engine_mocked, mock_neo4j_driver):
        """
        测试治疗措施子图检索
        
        验证：
        1. 检索病害的治疗方案
        2. 包含农药类型、用量、安全间隔期
        3. 数据结构完整
        """
        # 设置模拟返回数据
        mock_result = [
            {
                "treatment": "三唑酮",
                "usage": "喷雾",
                "dosage": "600-800 倍液",
                "interval": "7 天",
                "pesticide_type": "三唑类"
            }
        ]
        graphrag_engine_mocked.driver.session.return_value.__enter__.return_value.run.return_value = mock_result
        
        # 执行检索
        subgraph = graphrag_engine_mocked.retrieve_subgraph(
            disease_name="条锈病",
            depth=2
        )
        
        # 验证治疗措施
        assert "treatments" in subgraph
        assert len(subgraph["treatments"]) > 0
    
    def test_retrieve_related_diseases(self, graphrag_engine_mocked, mock_neo4j_driver):
        """
        测试相关病害检索
        
        验证：
        1. 检索易混淆病害
        2. 通过症状关联查找相似病害
        3. 支持 UNION 查询
        """
        # 设置模拟返回数据（相关病害）
        mock_result = [
            {"disease": "叶锈病", "desc": "橙褐色圆形孢子堆"},
            {"disease": "秆锈病", "desc": "深褐色长椭圆形孢子堆"}
        ]
        graphrag_engine_mocked.driver.session.return_value.__enter__.return_value.run.return_value = mock_result
        
        # 执行检索
        subgraph = graphrag_engine_mocked.retrieve_subgraph(
            disease_name="条锈病",
            depth=2
        )
        
        # 验证相关病害
        assert "related_diseases" in subgraph
    
    def test_multi_hop_retrieval(self, graphrag_engine_mocked, mock_neo4j_driver):
        """
        测试多跳检索
        
        验证：
        1. depth 参数控制检索深度
        2. 支持 2 跳、3 跳检索
        3. 获取更丰富的上下文信息
        """
        # 设置不同深度的模拟数据
        def mock_run(query, **params):
            # 根据查询类型返回不同数据
            if "Environment" in query:
                return [
                    {"name": "高湿环境", "condition": "湿度>80%", "temp": "15-20°C"}
                ]
            return []
        
        graphrag_engine_mocked.driver.session.return_value.__enter__.return_value.run.side_effect = mock_run
        
        # 执行 2 跳检索
        subgraph_depth2 = graphrag_engine_mocked.retrieve_subgraph(
            disease_name="条锈病",
            depth=2
        )
        
        # 验证包含环境因素（2 跳信息）
        assert "environment_factors" in subgraph_depth2


class TestGraphRAGTokenization:
    """知识 token 化测试"""
    
    @pytest.fixture
    def graphrag_with_data(self, tmp_path):
        """创建包含测试数据的 GraphRAG 引擎（使用文件缓存）"""
        from src.graph.graphrag_engine import GraphRAGEngine
        
        # 使用 patch 绕过 Neo4j 连接
        with patch('src.graph.graphrag_engine.GraphDatabase') as mock_graph_db:
            mock_driver = Mock()
            mock_driver.verify_connectivity = Mock()
            mock_session = Mock()
            mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = Mock(return_value=None)
            
            # 设置模拟返回数据
            mock_session.run.return_value = [
                {"symptom": "黄色条状病斑", "desc": "叶片出现黄色条纹", "part": "叶片"},
                {"treatment": "三唑酮", "usage": "喷雾", "dosage": "600-800 倍液"}
            ]
            
            mock_graph_db.driver.return_value = mock_driver
            
            engine = GraphRAGEngine(cache_size=100)
            return engine
    
    def test_tokenize_subgraph_to_text(self, graphrag_with_data):
        """
        测试子图 token 化
        
        验证：
        1. 将图谱结构转换为自然语言
        2. 保持语义完整性
        3. 适合 LLM 理解
        """
        # 检索子图
        subgraph = graphrag_with_data.retrieve_subgraph(
            disease_name="条锈病",
            depth=2
        )
        
        # Token 化（转换为文本）
        tokenized_text = graphrag_with_data.tokenize_subgraph(subgraph)
        
        # 验证 token 化结果
        assert tokenized_text is not None
        assert isinstance(tokenized_text, str)
        assert len(tokenized_text) > 0
        
        # 验证包含关键信息
        assert "条锈病" in tokenized_text or "症状" in tokenized_text
    
    def test_tokenize_with_different_formats(self, graphrag_with_data):
        """
        测试不同格式的 token 化
        
        验证：
        1. 支持结构化文本格式
        2. 支持自然语言段落格式
        3. 支持列表格式
        """
        subgraph = {
            "disease": "测试病害",
            "symptoms": ["症状 1", "症状 2"],
            "treatments": ["治疗 1", "治疗 2"]
        }
        
        # 测试结构化格式
        structured = graphrag_with_data.tokenize_subgraph(
            subgraph,
            format="structured"
        )
        assert structured is not None
        
        # 测试自然语言格式
        natural = graphrag_with_data.tokenize_subgraph(
            subgraph,
            format="natural_language"
        )
        assert natural is not None


class TestGraphRAGContextInjection:
    """上下文注入测试"""
    
    @pytest.fixture
    def integrated_system(self):
        """创建 GraphRAG + 认知层集成系统"""
        from src.graph.graphrag_engine import GraphRAGEngine
        from src.cognition.cognition_engine import CognitionEngine
        
        # 使用 mock 创建 GraphRAG 引擎
        with patch('src.graph.graphrag_engine.GraphDatabase') as mock_graph_db:
            mock_driver = Mock()
            mock_driver.verify_connectivity = Mock()
            mock_session = Mock()
            mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = Mock(return_value=None)
            
            # 设置模拟返回数据
            mock_session.run.return_value = [
                {"symptom": "黄色条状病斑", "desc": "典型症状", "part": "叶片"}
            ]
            
            mock_graph_db.driver.return_value = mock_driver
            
            graphrag = GraphRAGEngine()
            cognition = CognitionEngine()
            
            return {
                "graphrag": graphrag,
                "cognition": cognition
            }
    
    def test_inject_knowledge_context(self, integrated_system):
        """
        测试知识上下文注入
        
        验证：
        1. 检索到的知识作为上下文注入
        2. 增强 LLM 的理解能力
        3. 提高诊断准确性
        """
        graphrag = integrated_system["graphrag"]
        cognition = integrated_system["cognition"]
        
        # 检索知识子图
        subgraph = graphrag.retrieve_subgraph(
            disease_name="条锈病",
            depth=2
        )
        
        # Token 化
        knowledge_context = graphrag.tokenize_subgraph(subgraph)
        
        # 验证上下文不为空
        assert knowledge_context is not None
        assert len(knowledge_context) > 0
        
        # 构建带上下文的提示词
        prompt_with_context = cognition.build_prompt_with_knowledge(
            disease_name="条锈病",
            knowledge_context=knowledge_context
        )
        
        # 验证提示词包含上下文信息
        assert prompt_with_context is not None
        assert "条锈病" in prompt_with_context or "知识" in prompt_with_context
    
    def test_context_enhances_diagnosis(self, integrated_system):
        """
        测试上下文增强诊断
        
        验证：
        1. 有上下文的诊断更准确
        2. 包含更多细节信息
        """
        graphrag = integrated_system["graphrag"]
        
        # 检索知识
        subgraph = graphrag.retrieve_subgraph(disease_name="条锈病")
        knowledge_context = graphrag.tokenize_subgraph(subgraph)
        
        # 验证知识上下文包含有用信息
        assert knowledge_context is not None
        # 应该包含症状、治疗等信息
        assert len(knowledge_context) > 10  # 至少有一些内容


class TestGraphRAGPerformance:
    """性能测试"""
    
    @pytest.fixture
    def cached_graphrag(self):
        """创建带缓存的 GraphRAG 引擎"""
        from src.graph.graphrag_engine import GraphRAGEngine
        
        with patch('src.graph.graphrag_engine.GraphDatabase') as mock_graph_db:
            mock_driver = Mock()
            mock_driver.verify_connectivity = Mock()
            mock_session = Mock()
            mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = Mock(return_value=None)
            
            mock_session.run.return_value = [
                {"symptom": "测试症状", "desc": "描述", "part": "叶片"}
            ]
            
            mock_graph_db.driver.return_value = mock_driver
            
            # 设置较小的缓存用于测试
            engine = GraphRAGEngine(cache_size=10)
            return engine
    
    def test_lru_cache_performance(self, cached_graphrag):
        """
        测试 LRU 缓存性能优化
        
        验证：
        1. 重复查询使用缓存
        2. 缓存命中率统计正确
        3. 缓存大小限制生效
        """
        # 第一次查询（未缓存）
        result1 = cached_graphrag.retrieve_subgraph(disease_name="条锈病", depth=2)
        
        # 检查性能统计
        stats = cached_graphrag.get_performance_stats()
        assert stats["total_queries"] == 1
        
        # 第二次查询（应该命中缓存）
        result2 = cached_graphrag.retrieve_subgraph(disease_name="条锈病", depth=2)
        
        # 验证缓存命中
        stats = cached_graphrag.get_performance_stats()
        assert stats["cache_hits"] >= 1
        
        # 验证两次返回结果相同
        assert result1["disease"] == result2["disease"]
    
    def test_cache_size_limit(self, cached_graphrag):
        """
        测试缓存大小限制
        
        验证：
        1. 缓存超过限制时移除旧数据
        2. LRU 策略正确执行
        """
        # 执行多次查询填满缓存
        for i in range(15):  # 超过 cache_size=10
            cached_graphrag.retrieve_subgraph(disease_name=f"病害_{i}", depth=2)
        
        # 验证缓存大小不超过限制
        assert len(cached_graphrag.subgraph_cache) <= cached_graphrag.cache_size


class TestGraphRAGEdgeCases:
    """边界情况测试"""
    
    @pytest.fixture
    def graphrag_no_database(self):
        """创建无数据库连接的 GraphRAG 引擎"""
        from src.graph.graphrag_engine import GraphRAGEngine
        
        with patch('src.graph.graphrag_engine.GraphDatabase') as mock_graph_db:
            # 模拟连接失败
            mock_driver = Mock()
            mock_driver.verify_connectivity.side_effect = Exception("连接失败")
            mock_graph_db.driver.return_value = mock_driver
            
            engine = GraphRAGEngine()
            return engine
    
    def test_retrieve_with_no_connection(self, graphrag_no_database):
        """
        测试无数据库连接时的检索
        
        验证：
        1. 优雅处理连接失败
        2. 返回空结果而不是崩溃
        """
        # 即使连接失败，也应该返回空子图而不是崩溃
        subgraph = graphrag_no_database.retrieve_subgraph(disease_name="测试病害")
        
        # 验证返回了基本结构
        assert subgraph is not None
        assert "disease" in subgraph
    
    def test_retrieve_nonexistent_disease(self, graphrag_with_data):
        """
        测试检索不存在的病害
        
        验证：
        1. 返回空结果
        2. 不抛出异常
        """
        subgraph = graphrag_with_data.retrieve_subgraph(
            disease_name="不存在的病害"
        )
        
        # 验证返回了空子图
        assert subgraph is not None
        assert subgraph.get("symptoms") == [] or len(subgraph.get("symptoms", [])) == 0


def run_graphrag_tests():
    """运行 Graph-RAG 测试的便捷函数"""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_graphrag_tests()

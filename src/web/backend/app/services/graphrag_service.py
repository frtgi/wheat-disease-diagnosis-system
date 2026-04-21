# -*- coding: utf-8 -*-
"""
GraphRAG 知识增强服务
提供知识子图检索、知识 Token 化、上下文注入功能
"""
import logging
import sys
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DISEASE_NAME_MAPPING = {
    "Yellow Rust": "小麦条锈病",
    "Brown Rust": "小麦叶锈病",
    "Black Rust": "小麦秆锈病",
    "Mildew": "小麦白粉病",
    "Fusarium Head Blight": "小麦赤霉病",
    "Common Root Rot": "小麦根腐病",
    "Leaf Blight": "小麦叶枯病",
    "Smut": "小麦黑粉病",
    "Tan spot": "小麦褐斑病",
    "Septoria": "小麦壳针孢叶斑病"
}

@dataclass
class KnowledgeTriple:
    """
    知识三元组数据结构
    
    Attributes:
        head: 头实体（如病害名称）
        relation: 关系类型（如 HAS_SYMPTOM）
        tail: 尾实体（如症状描述）
        confidence: 置信度
        source: 知识来源
    """
    head: str
    relation: str
    tail: str
    confidence: float = 1.0
    source: str = "knowledge_graph"


@dataclass
class KnowledgeContext:
    """
    知识上下文数据结构
    
    Attributes:
        triples: 知识三元组列表
        tokens: Token 化后的知识文本
        entities: 涉及的实体列表
        citations: 引用信息列表
    """
    triples: List[KnowledgeTriple] = field(default_factory=list)
    tokens: str = ""
    entities: List[str] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)


class GraphRAGService:
    """
    GraphRAG 知识增强服务
    
    核心功能：
    1. 知识子图检索：基于症状关键词检索相关知识
    2. 知识 Token 化：将知识三元组转换为 Token 序列
    3. 上下文注入：将知识 Token 注入到诊断上下文
    4. 引用溯源：提供知识来源追溯
    5. 病害名称映射：支持 YOLO 检测结果到知识图谱的名称转换
    """
    
    @staticmethod
    def map_disease_name(disease_name: str) -> str:
        """
        将病害英文名称映射为中文名称
        
        Args:
            disease_name: 病害名称（英文或中文）
            
        Returns:
            str: 中文病害名称
        """
        if not disease_name:
            return disease_name
        
        if disease_name in DISEASE_NAME_MAPPING:
            mapped_name = DISEASE_NAME_MAPPING[disease_name]
            logger.debug(f"病害名称映射: {disease_name} -> {mapped_name}")
            return mapped_name
        
        return disease_name
    
    def __init__(self):
        """
        初始化 GraphRAG 服务
        """
        self._graphrag_engine = None
        self._initialized = False
        
        self._init_engine()
    
    def _init_engine(self):
        """
        初始化 GraphRAG 引擎
        
        将 wheatagent 项目的根目录添加到 sys.path，
        然后从 src.graph 模块导入 GraphRAGEngine。
        如果导入失败，服务将进入降级模式运行。
        """
        try:
            current_file = os.path.abspath(__file__)
            wheatagent_root = os.path.normpath(
                os.path.join(current_file, '..', '..', '..', '..', '..', '..')
            )
            
            if wheatagent_root not in sys.path:
                sys.path.insert(0, wheatagent_root)
            
            from src.graph.graphrag_engine import GraphRAGEngine
            
            self._graphrag_engine = GraphRAGEngine()
            self._initialized = True
            logger.info(f"GraphRAG 引擎初始化成功，路径: {wheatagent_root}")
        except Exception as e:
            logger.warning(f"GraphRAG 引擎初始化失败：{e}，将使用降级模式")
            self._initialized = False
    
    def retrieve_knowledge(self, symptoms: str, disease_hint: Optional[str] = None) -> KnowledgeContext:
        """
        检索相关知识
        
        Args:
            symptoms: 症状描述
            disease_hint: 病害提示（可选，用于精确检索，支持英文名称自动映射）
            
        Returns:
            KnowledgeContext: 知识上下文
        """
        logger.info(f"开始知识检索: symptoms='{symptoms[:50]}...', disease_hint='{disease_hint}'")
        
        context = KnowledgeContext()
        
        if not self._initialized or not self._graphrag_engine:
            logger.warning("GraphRAG 引擎未初始化，使用降级模式")
            return self._fallback_retrieve(symptoms, disease_hint)
        
        try:
            if disease_hint:
                mapped_disease = self.map_disease_name(disease_hint)
                logger.debug(f"病害名称映射: '{disease_hint}' -> '{mapped_disease}'")
                
                subgraph = self._graphrag_engine.retrieve_subgraph(mapped_disease)
                context = self._subgraph_to_context(subgraph)
                logger.info(f"子图检索完成: 病害={mapped_disease}, 三元组数={len(context.triples)}")
            else:
                keywords = self._extract_keywords(symptoms)
                logger.debug(f"提取关键词: {keywords}")
                context = self._retrieve_by_keywords(keywords)
            
            logger.info(f"知识检索完成：{len(context.triples)} 个三元组, {len(context.entities)} 个实体")
            return context
            
        except Exception as e:
            logger.error(f"知识检索失败：{e}", exc_info=True)
            return self._fallback_retrieve(symptoms, disease_hint)
    
    def retrieve_disease_knowledge(self, disease_name: str) -> KnowledgeContext:
        """
        检索病害相关知识
        
        Args:
            disease_name: 病害名称（支持英文名称自动映射）
            
        Returns:
            KnowledgeContext: 知识上下文
        """
        logger.debug(f"检索病害知识: disease_name='{disease_name}'")
        
        if not self._initialized or not self._graphrag_engine:
            logger.warning("GraphRAG 引擎未初始化，返回空上下文")
            return KnowledgeContext()
        
        try:
            mapped_name = self.map_disease_name(disease_name)
            if mapped_name != disease_name:
                logger.info(f"病害名称映射: '{disease_name}' -> '{mapped_name}'")
            
            subgraph = self._graphrag_engine.retrieve_subgraph(mapped_name)
            context = self._subgraph_to_context(subgraph)
            logger.info(f"病害知识检索完成: {mapped_name}, 三元组数={len(context.triples)}")
            return context
        except Exception as e:
            logger.error(f"病害知识检索失败：{e}", exc_info=True)
            return KnowledgeContext()
    
    def _subgraph_to_context(self, subgraph: Dict[str, Any]) -> KnowledgeContext:
        """
        将子图转换为知识上下文
        
        Args:
            subgraph: 子图数据
            
        Returns:
            KnowledgeContext: 知识上下文
        """
        context = KnowledgeContext()
        disease_name = subgraph.get("disease", "未知病害")
        context.entities.append(disease_name)
        
        for symptom in subgraph.get("symptoms", []):
            triple = KnowledgeTriple(
                head=disease_name,
                relation="症状",
                tail=symptom.get("name", ""),
                confidence=0.9,
                source="知识图谱"
            )
            context.triples.append(triple)
            if symptom.get("name"):
                context.entities.append(symptom["name"])
        
        for cause in subgraph.get("causes", []):
            triple = KnowledgeTriple(
                head=disease_name,
                relation="病因",
                tail=cause.get("name", ""),
                confidence=0.85,
                source="知识图谱"
            )
            context.triples.append(triple)
            if cause.get("name"):
                context.entities.append(cause["name"])
        
        for prevention in subgraph.get("preventions", []):
            triple = KnowledgeTriple(
                head=disease_name,
                relation="预防",
                tail=prevention.get("name", ""),
                confidence=0.8,
                source="知识图谱"
            )
            context.triples.append(triple)
            if prevention.get("name"):
                context.entities.append(prevention["name"])
        
        for treatment in subgraph.get("treatments", []):
            triple = KnowledgeTriple(
                head=disease_name,
                relation="治疗",
                tail=treatment.get("name", ""),
                confidence=0.9,
                source="知识图谱"
            )
            context.triples.append(triple)
            if treatment.get("name"):
                context.entities.append(treatment["name"])
        
        for env in subgraph.get("environment_factors", []):
            triple = KnowledgeTriple(
                head=disease_name,
                relation="易发环境",
                tail=env.get("name", ""),
                confidence=0.75,
                source="知识图谱"
            )
            context.triples.append(triple)
            if env.get("name"):
                context.entities.append(env["name"])
        
        context.tokens = self._triples_to_tokens(context.triples)
        
        context.citations = [
            {
                "entity_id": f"KG_{i}",
                "entity_name": t.head,
                "relation": t.relation,
                "tail": t.tail,
                "source": t.source,
                "confidence": t.confidence
            }
            for i, t in enumerate(context.triples)
        ]
        
        return context
    
    def _triples_to_tokens(self, triples: List[KnowledgeTriple]) -> str:
        """
        将知识三元组转换为 Token 文本
        
        Args:
            triples: 知识三元组列表
            
        Returns:
            str: Token 文本
        """
        if not triples:
            return ""
        
        token_lines = []
        token_lines.append("【知识图谱信息】")
        
        grouped = {}
        for triple in triples:
            if triple.head not in grouped:
                grouped[triple.head] = {}
            if triple.relation not in grouped[triple.head]:
                grouped[triple.head][triple.relation] = []
            grouped[triple.head][triple.relation].append(triple.tail)
        
        for entity, relations in grouped.items():
            token_lines.append(f"\n病害：{entity}")
            
            if "症状" in relations:
                symptoms = relations["症状"]
                token_lines.append(f"  症状：{', '.join(symptoms[:5])}")
            
            if "病因" in relations:
                causes = relations["病因"]
                token_lines.append(f"  病因：{', '.join(causes[:3])}")
            
            if "治疗" in relations:
                treatments = relations["治疗"]
                token_lines.append(f"  治疗：{', '.join(treatments[:5])}")
            
            if "预防" in relations:
                preventions = relations["预防"]
                token_lines.append(f"  预防：{', '.join(preventions[:5])}")
            
            if "易发环境" in relations:
                envs = relations["易发环境"]
                token_lines.append(f"  易发环境：{', '.join(envs[:3])}")
        
        return "\n".join(token_lines)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        
        优化版本：
        - 支持病害名称直接匹配
        - 支持症状关键词匹配
        - 支持英文病害名称映射
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 关键词列表
        """
        if not text:
            return []
        
        found_keywords = []
        
        disease_keywords = [
            "条锈病", "叶锈病", "秆锈病", "白粉病", "赤霉病",
            "根腐病", "叶枯病", "黑粉病", "褐斑病", "纹枯病",
            "全蚀病", "缺素症", "黄花叶病"
        ]
        
        for keyword in disease_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        for eng_name, chn_name in DISEASE_NAME_MAPPING.items():
            if eng_name.lower() in text.lower():
                found_keywords.append(chn_name)
        
        symptom_keywords = [
            "黄化", "枯萎", "斑点", "锈病", "白粉", "霉层", "腐烂",
            "条纹", "褪绿", "坏死", "畸形", "矮化", "徒长", "倒伏",
            "叶片", "茎秆", "穗部", "根部", "叶鞘", "孢子堆"
        ]
        
        for keyword in symptom_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        unique_keywords = list(dict.fromkeys(found_keywords))
        logger.debug(f"从文本提取关键词: {unique_keywords}")
        
        return unique_keywords
    
    def _retrieve_by_keywords(self, keywords: List[str]) -> KnowledgeContext:
        """
        基于关键词检索知识
        
        Args:
            keywords: 关键词列表
            
        Returns:
            KnowledgeContext: 知识上下文
        """
        context = KnowledgeContext()
        
        if not keywords:
            logger.debug("无关键词，返回空上下文")
            return context
        
        disease_mapping = {
            "条锈病": "小麦条锈病",
            "叶锈病": "小麦叶锈病",
            "秆锈病": "小麦秆锈病",
            "锈病": "小麦条锈病",
            "条纹": "小麦条锈病",
            "白粉": "小麦白粉病",
            "霉层": "小麦赤霉病",
            "腐烂": "小麦根腐病",
            "枯萎": "小麦全蚀病",
            "斑点": "小麦叶枯病",
            "叶枯": "小麦叶枯病",
            "黑粉": "小麦黑粉病",
            "褐斑": "小麦褐斑病",
            "黄化": "小麦缺素症"
        }
        
        for keyword in keywords:
            if keyword in disease_mapping:
                disease_name = disease_mapping[keyword]
                logger.debug(f"关键词映射: '{keyword}' -> '{disease_name}'")
                sub_context = self.retrieve_disease_knowledge(disease_name)
                context.triples.extend(sub_context.triples)
                context.entities.extend(sub_context.entities)
                context.citations.extend(sub_context.citations)
                break
        
        context.tokens = self._triples_to_tokens(context.triples)
        logger.info(f"关键词检索完成: 关键词={keywords}, 三元组数={len(context.triples)}")
        return context
    
    def _fallback_retrieve(self, symptoms: str, disease_hint: Optional[str] = None) -> KnowledgeContext:
        """
        降级模式：当 GraphRAG 引擎不可用时使用
        
        增强版本：
        - 支持更多病害知识
        - 支持英文病害名称映射
        - 更详细的知识内容
        
        Args:
            symptoms: 症状描述
            disease_hint: 病害提示
            
        Returns:
            KnowledgeContext: 知识上下文
        """
        logger.info(f"使用降级模式检索知识: disease_hint='{disease_hint}'")
        
        context = KnowledgeContext()
        
        fallback_knowledge = {
            "小麦条锈病": {
                "symptoms": ["黄色条纹状病斑", "叶片褪绿", "条状孢子堆", "夏孢子堆呈橙黄色"],
                "causes": ["条形柄锈菌感染", "低温高湿环境", "品种抗性差"],
                "treatments": ["喷洒三唑酮", "喷施烯唑醇", "喷施丙环唑", "喷施戊唑醇"],
                "preventions": ["选用抗病品种", "轮作倒茬", "适期播种", "清除病残体", "合理密植"]
            },
            "小麦叶锈病": {
                "symptoms": ["橙褐色圆形病斑", "叶片褪绿", "锈褐色孢子堆", "病斑散生"],
                "causes": ["小麦叶锈菌感染", "温暖湿润环境", "氮肥过量"],
                "treatments": ["喷洒三唑酮", "喷施丙环唑", "喷施腈菌唑"],
                "preventions": ["清除病残体", "合理密植", "选用抗病品种", "控制氮肥用量"]
            },
            "小麦秆锈病": {
                "symptoms": ["茎秆红褐色病斑", "大而明显的孢子堆", "植株矮化", "茎秆折断"],
                "causes": ["禾柄锈菌感染", "高温高湿环境", "品种感病"],
                "treatments": ["喷洒三唑酮", "喷施戊唑醇", "喷施烯唑醇"],
                "preventions": ["选用抗病品种", "清除转主寄主", "适期播种"]
            },
            "小麦白粉病": {
                "symptoms": ["白色粉状霉层", "叶片褪绿", "后期变黑", "植株矮化"],
                "causes": ["禾本科布氏白粉菌感染", "氮肥过量", "种植密度过大"],
                "treatments": ["喷洒三唑酮", "喷施腈菌唑", "喷施丙环唑", "喷施戊唑醇"],
                "preventions": ["选用抗病品种", "控制氮肥", "合理密植", "清除病残体"]
            },
            "小麦赤霉病": {
                "symptoms": ["粉红色霉层", "穗部枯萎", "籽粒干瘪", "穗部腐烂"],
                "causes": ["禾谷镰刀菌感染", "抽穗扬花期遇雨", "品种感病"],
                "treatments": ["喷洒多菌灵", "喷施戊唑醇", "喷施咪鲜胺", "喷施氰烯菌酯"],
                "preventions": ["适期播种", "清除病残体", "选用抗病品种", "合理施肥"]
            },
            "小麦根腐病": {
                "symptoms": ["根部腐烂", "植株矮化", "叶片黄化", "分蘖减少"],
                "causes": ["禾旋孢腔菌感染", "土壤湿度过大", "连作"],
                "treatments": ["种子包衣处理", "喷施多菌灵", "喷施戊唑醇"],
                "preventions": ["轮作倒茬", "选用抗病品种", "种子处理", "排水降渍"]
            },
            "小麦叶枯病": {
                "symptoms": ["叶片枯死", "褐色病斑", "叶尖干枯", "病斑扩展"],
                "causes": ["小麦链格孢菌感染", "高温高湿", "氮肥过量"],
                "treatments": ["喷施多菌灵", "喷施代森锰锌", "喷施百菌清"],
                "preventions": ["清除病残体", "合理施肥", "选用抗病品种", "轮作倒茬"]
            },
            "小麦黑粉病": {
                "symptoms": ["穗部黑粉", "籽粒被破坏", "植株矮化", "穗部畸形"],
                "causes": ["小麦腥黑粉菌感染", "种子带菌", "土壤带菌"],
                "treatments": ["种子包衣处理", "喷施戊唑醇", "喷施三唑酮"],
                "preventions": ["种子处理", "选用无病种子", "轮作倒茬", "清除病株"]
            },
            "小麦褐斑病": {
                "symptoms": ["褐色斑点", "叶片枯黄", "病斑边缘明显", "病斑融合"],
                "causes": ["小麦德氏霉菌感染", "高温高湿", "品种感病"],
                "treatments": ["喷施多菌灵", "喷施代森锰锌", "喷施丙环唑"],
                "preventions": ["清除病残体", "合理密植", "选用抗病品种", "平衡施肥"]
            },
            "小麦壳针孢叶斑病": {
                "symptoms": ["叶斑", "褐色小点", "病斑扩大", "叶片枯死"],
                "causes": ["小麦壳针孢菌感染", "高湿环境", "氮肥过量"],
                "treatments": ["喷施多菌灵", "喷施戊唑醇", "喷施丙环唑"],
                "preventions": ["清除病残体", "轮作倒茬", "选用抗病品种", "合理施肥"]
            }
        }
        
        disease_name = disease_hint
        if disease_hint:
            disease_name = self.map_disease_name(disease_hint)
        
        if not disease_name or disease_name not in fallback_knowledge:
            disease_name = "小麦条锈病"
        
        if disease_name in fallback_knowledge:
            knowledge = fallback_knowledge[disease_name]
            context.entities.append(disease_name)
            logger.info(f"降级模式使用知识库: {disease_name}")
            
            for symptom in knowledge.get("symptoms", []):
                context.triples.append(KnowledgeTriple(
                    head=disease_name,
                    relation="症状",
                    tail=symptom,
                    confidence=0.8,
                    source="知识图谱(降级)"
                ))
            
            for cause in knowledge.get("causes", []):
                context.triples.append(KnowledgeTriple(
                    head=disease_name,
                    relation="病因",
                    tail=cause,
                    confidence=0.75,
                    source="知识图谱(降级)"
                ))
            
            for treatment in knowledge.get("treatments", []):
                context.triples.append(KnowledgeTriple(
                    head=disease_name,
                    relation="治疗",
                    tail=treatment,
                    confidence=0.85,
                    source="知识图谱(降级)"
                ))
            
            for prevention in knowledge.get("preventions", []):
                context.triples.append(KnowledgeTriple(
                    head=disease_name,
                    relation="预防",
                    tail=prevention,
                    confidence=0.8,
                    source="知识图谱(降级)"
                ))
        
        context.tokens = self._triples_to_tokens(context.triples)
        
        context.citations = [
            {
                "entity_id": f"FB_{i}",
                "entity_name": t.head,
                "relation": t.relation,
                "tail": t.tail,
                "source": t.source,
                "confidence": t.confidence
            }
            for i, t in enumerate(context.triples)
        ]
        
        logger.info(f"降级模式检索完成: {len(context.triples)} 个三元组")
        
        return context
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取服务统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if self._initialized and self._graphrag_engine:
            return self._graphrag_engine.performance_stats
        return {
            "initialized": self._initialized,
            "status": "fallback_mode" if not self._initialized else "normal"
        }


_graphrag_service: Optional[GraphRAGService] = None


def get_graphrag_service() -> GraphRAGService:
    """
    获取 GraphRAG 服务单例
    
    Returns:
        GraphRAGService: GraphRAG 服务实例
    """
    global _graphrag_service
    if _graphrag_service is None:
        _graphrag_service = GraphRAGService()
    return _graphrag_service

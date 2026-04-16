# -*- coding: utf-8 -*-
"""
iText2KG - 增量式文本到知识图谱转换框架

根据文档5.2节：知识抽取与图谱构建自动化
"手动构建图谱效率低下且难以覆盖海量文献。我们利用iText2KG框架实现自动化的知识抽取与图谱更新。"

功能：
1. 文档蒸馏（Document Distillation）：LangChain文本分块
2. 增量式实体关系抽取：LLM提取三元组
3. Neo4j存储：自动去重和融合实体
"""
import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import warnings


class EntityType(Enum):
    """实体类型枚举 - 根据文档5.1节本体设计"""
    CROP = "Crop"
    DISEASE = "Disease"
    SYMPTOM = "Symptom"
    PATHOGEN = "Pathogen"
    ENVIRONMENT = "Environment"
    CONTROL_MEASURE = "ControlMeasure"
    CHEMICAL = "Chemical"
    CROP_PART = "CropPart"


class RelationType(Enum):
    """关系类型枚举 - 根据文档5.1节语义关系边"""
    HAS_SYMPTOM = "HAS_SYMPTOM"
    HAS_PATHOGEN = "HAS_PATHOGEN"
    CAUSED_BY = "CAUSED_BY"
    TREATED_BY = "TREATED_BY"
    PREVENTED_BY = "PREVENTED_BY"
    FAVORED_BY = "FAVORED_BY"
    MANIFESTS_AS = "MANIFESTS_AS"
    OCCURS_IN = "OCCURS_IN"
    SIMILAR_TO = "SIMILAR_TO"


@dataclass
class Triple:
    """三元组数据结构"""
    head: str
    head_type: str
    relation: str
    tail: str
    tail_type: str
    confidence: float = 1.0
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "head": self.head,
            "head_type": self.head_type,
            "relation": self.relation,
            "tail": self.tail,
            "tail_type": self.tail_type,
            "confidence": self.confidence,
            "source": self.source
        }
    
    def to_cypher(self) -> str:
        """转换为Cypher语句"""
        return f"""
        MERGE (h:{self.head_type} {{name: '{self.head}'}})
        MERGE (t:{self.tail_type} {{name: '{self.tail}'}})
        MERGE (h)-[:{self.relation}]->(t)
        """


@dataclass
class ExtractedEntity:
    """提取的实体"""
    name: str
    entity_type: str
    description: str = ""
    confidence: float = 1.0
    source_text: str = ""


class TextChunker:
    """
    文本分块器
    
    根据文档5.2节：
    "系统自动抓取农业科技论文、植保手册等PDF或HTML文档，
    利用LangChain进行文本分块（Chunking）"
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: List[str] = None
    ):
        """
        初始化文本分块器
        
        :param chunk_size: 块大小（字符数）
        :param chunk_overlap: 重叠大小
        :param separators: 分隔符列表
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", "；", "，", " "]
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        将文本分块
        
        :param text: 输入文本
        :return: 文本块列表
        """
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                chunk_text = text[start:]
                if chunk_text.strip():
                    chunks.append({
                        "id": chunk_id,
                        "text": chunk_text.strip(),
                        "start": start,
                        "end": len(text)
                    })
                break
            
            best_end = end
            for sep in self.separators:
                last_sep = text.rfind(sep, start, end + 100)
                if last_sep > start and last_sep < end + 100:
                    best_end = last_sep + len(sep)
                    break
            
            chunk_text = text[start:best_end]
            if chunk_text.strip():
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text.strip(),
                    "start": start,
                    "end": best_end
                })
                chunk_id += 1
            
            start = best_end - self.chunk_overlap
            if start < 0:
                start = 0
        
        return chunks
    
    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        分块文档
        
        :param document: 文档字典，包含title, content, source等
        :return: 带元数据的文本块列表
        """
        chunks = self.chunk_text(document.get("content", ""))
        
        for chunk in chunks:
            chunk["title"] = document.get("title", "")
            chunk["source"] = document.get("source", "")
            chunk["doc_id"] = document.get("id", "")
        
        return chunks


class EntityExtractor:
    """
    实体抽取器
    
    根据文档2.3节：
    "实体识别（NER）：从文本中提取关键实体，如'病害名称'、'症状特征'、'农药名称'"
    """
    
    ENTITY_PATTERNS = {
        EntityType.DISEASE: [
            r"(\w+锈病)", r"(\w+霉病)", r"(\w+枯病)", r"(\w+斑病)",
            r"(蚜虫)", r"(螨虫)", r"(黑粉病)", r"(根腐病)",
            r"(白粉病)", r"(条锈病)", r"(叶锈病)", r"(秆锈病)",
            r"(赤霉病)", r"(叶斑病)", r"(全蚀病)"
        ],
        EntityType.SYMPTOM: [
            r"(\w+褪绿)", r"(\w+枯萎)", r"(\w+黄化)", r"(\w+斑点)",
            r"(黄色条状\w+)", r"(白色霉层)", r"(褐色病斑)", r"(穗部漂白)",
            r"(叶片卷曲)", r"(植株矮化)"
        ],
        EntityType.PATHOGEN: [
            r"(\w+锈菌)", r"(\w+镰刀菌)", r"(\w+柄锈菌)",
            r"(Puccinia\s+\w+)", r"(Fusarium\s+\w+)", r"(Blumeria\s+\w+)"
        ],
        EntityType.CHEMICAL: [
            r"(三唑酮)", r"(戊唑醇)", r"(多菌灵)", r"(吡虫啉)",
            r"(丙环唑)", r"(腈菌唑)", r"(醚菌酯)", r"(粉锈宁)",
            r"(\w+可湿性粉剂)", r"(\w+乳油)", r"(\w+悬浮剂)"
        ],
        EntityType.ENVIRONMENT: [
            r"(高湿\w*)", r"(低温\w*)", r"(高温\w*)", r"(连阴雨)",
            r"(干旱\w*)", r"(多雨\w*)", r"(寡照)"
        ],
        EntityType.CONTROL_MEASURE: [
            r"(抗病选种)", r"(轮作倒茬)", r"(清沟沥水)", r"(清除病残体)",
            r"(合理密植)", r"(适时播种)", r"(科学施肥)"
        ]
    }
    
    def __init__(self, use_llm: bool = False, llm_client=None):
        """
        初始化实体抽取器
        
        :param use_llm: 是否使用LLM增强
        :param llm_client: LLM客户端
        """
        self.use_llm = use_llm
        self.llm_client = llm_client
    
    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        从文本中提取实体
        
        :param text: 输入文本
        :return: 实体列表
        """
        entities = []
        
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entity_name = match.group(1)
                    if entity_name and len(entity_name) >= 2:
                        entities.append(ExtractedEntity(
                            name=entity_name,
                            entity_type=entity_type.value,
                            source_text=text[max(0, match.start()-20):match.end()+20]
                        ))
        
        if self.use_llm and self.llm_client:
            llm_entities = self._extract_with_llm(text)
            entities.extend(llm_entities)
        
        return self._deduplicate_entities(entities)
    
    def _extract_with_llm(self, text: str) -> List[ExtractedEntity]:
        """
        使用LLM提取实体
        
        :param text: 输入文本
        :return: 实体列表
        """
        if not self.llm_client:
            return []
        
        prompt = f"""
请从以下农业文本中提取实体，包括：
- 病害名称 (Disease)
- 症状描述 (Symptom)
- 病原体 (Pathogen)
- 防治药剂 (Chemical)
- 环境条件 (Environment)
- 防治措施 (ControlMeasure)

文本：
{text}

请以JSON格式输出，格式如下：
[
  {{"name": "实体名称", "type": "实体类型", "description": "简短描述"}}
]
"""
        
        try:
            response = self.llm_client.generate(prompt)
            entities_data = json.loads(response)
            return [
                ExtractedEntity(
                    name=e["name"],
                    entity_type=e["type"],
                    description=e.get("description", "")
                )
                for e in entities_data
            ]
        except Exception as e:
            print(f"⚠️ LLM实体提取失败: {e}")
            return []
    
    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """
        去重实体
        
        :param entities: 实体列表
        :return: 去重后的实体列表
        """
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity.name, entity.entity_type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities


class RelationExtractor:
    """
    关系抽取器
    
    根据文档2.3节：
    "关系抽取（RE）：识别实体间的关系，如'导致'（CAUSES）、'表现为'（MANIFESTS_AS）"
    """
    
    RELATION_PATTERNS = {
        RelationType.HAS_SYMPTOM: [
            r"(\w+病).*(?:表现为|症状为|出现).{0,10}(\w+)",
            r"(\w+病).*(?:伴有|伴随).{0,10}(\w+)"
        ],
        RelationType.HAS_PATHOGEN: [
            r"(\w+病).*(?:由|病原为|病原体是).{0,10}(\w+菌|\w+)",
            r"(\w+菌).*(?:引起|导致|侵染).{0,10}(\w+病)"
        ],
        RelationType.CAUSED_BY: [
            r"(\w+病).*(?:由于|因为|由).{0,10}(\w+)",
            r"(\w+).*(?:导致|引起|诱发).{0,10}(\w+病)"
        ],
        RelationType.TREATED_BY: [
            r"(\w+病).*(?:使用|用|喷施).{0,10}(\w+)",
            r"(\w+).*(?:防治|治疗|抑制).{0,10}(\w+病)"
        ],
        RelationType.FAVORED_BY: [
            r"(\w+病).*(?:易发于|多发于|适宜).{0,10}(\w+)",
            r"(\w+).*(?:有利于|促进).{0,10}(\w+病)"
        ]
    }
    
    def __init__(self, use_llm: bool = False, llm_client=None):
        """
        初始化关系抽取器
        
        :param use_llm: 是否使用LLM增强
        :param llm_client: LLM客户端
        """
        self.use_llm = use_llm
        self.llm_client = llm_client
    
    def extract_relations(
        self,
        text: str,
        entities: List[ExtractedEntity]
    ) -> List[Triple]:
        """
        从文本中提取关系
        
        :param text: 输入文本
        :param entities: 已提取的实体列表
        :return: 三元组列表
        """
        triples = []
        
        entity_dict = {}
        for entity in entities:
            entity_dict[entity.name] = entity.entity_type
        
        for relation_type, patterns in self.RELATION_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    head = match.group(1)
                    tail = match.group(2)
                    
                    head_type = entity_dict.get(head, self._infer_entity_type(head, is_head=True, relation=relation_type))
                    tail_type = entity_dict.get(tail, self._infer_entity_type(tail, is_head=False, relation=relation_type))
                    
                    if head and tail and head != tail:
                        triples.append(Triple(
                            head=head,
                            head_type=head_type,
                            relation=relation_type.value,
                            tail=tail,
                            tail_type=tail_type,
                            source_text=text[max(0, match.start()-10):match.end()+10]
                        ))
        
        if self.use_llm and self.llm_client:
            llm_triples = self._extract_with_llm(text, entities)
            triples.extend(llm_triples)
        
        return self._deduplicate_triples(triples)
    
    def _infer_entity_type(self, name: str, is_head: bool, relation: RelationType) -> str:
        """
        推断实体类型
        
        :param name: 实体名称
        :param is_head: 是否是头实体
        :param relation: 关系类型
        :return: 实体类型
        """
        if relation == RelationType.HAS_SYMPTOM:
            return "Disease" if is_head else "Symptom"
        elif relation == RelationType.HAS_PATHOGEN:
            return "Disease" if is_head else "Pathogen"
        elif relation == RelationType.CAUSED_BY:
            return "Disease" if is_head else "Environment"
        elif relation == RelationType.TREATED_BY:
            return "Disease" if is_head else "Chemical"
        elif relation == RelationType.FAVORED_BY:
            return "Disease" if is_head else "Environment"
        return "Entity"
    
    def _extract_with_llm(
        self,
        text: str,
        entities: List[ExtractedEntity]
    ) -> List[Triple]:
        """
        使用LLM提取关系
        
        :param text: 输入文本
        :param entities: 实体列表
        :return: 三元组列表
        """
        if not self.llm_client:
            return []
        
        entity_list = [f"{e.name}({e.entity_type})" for e in entities]
        
        prompt = f"""
请从以下农业文本中提取实体之间的关系三元组。

文本：
{text}

已知实体：
{chr(10).join(entity_list)}

请提取关系，支持的关系类型：
- HAS_SYMPTOM: 病害具有症状
- HAS_PATHOGEN: 病害由病原体引起
- CAUSED_BY: 由环境因素导致
- TREATED_BY: 使用药剂治疗
- FAVORED_BY: 易发于某种环境

请以JSON格式输出：
[
  {{"head": "头实体", "head_type": "类型", "relation": "关系类型", "tail": "尾实体", "tail_type": "类型"}}
]
"""
        
        try:
            response = self.llm_client.generate(prompt)
            triples_data = json.loads(response)
            return [
                Triple(
                    head=t["head"],
                    head_type=t["head_type"],
                    relation=t["relation"],
                    tail=t["tail"],
                    tail_type=t["tail_type"]
                )
                for t in triples_data
            ]
        except Exception as e:
            print(f"⚠️ LLM关系提取失败: {e}")
            return []
    
    def _deduplicate_triples(self, triples: List[Triple]) -> List[Triple]:
        """
        去重三元组
        
        :param triples: 三元组列表
        :return: 去重后的三元组列表
        """
        seen = set()
        unique_triples = []
        
        for triple in triples:
            key = (triple.head, triple.relation, triple.tail)
            if key not in seen:
                seen.add(key)
                unique_triples.append(triple)
        
        return unique_triples


class IText2KG:
    """
    iText2KG - 增量式文本到知识图谱转换框架
    
    根据文档5.2节完整实现：
    1. 文档蒸馏
    2. 增量式实体关系抽取
    3. Neo4j存储
    """
    
    def __init__(
        self,
        neo4j_driver=None,
        use_llm: bool = False,
        llm_client=None,
        chunk_size: int = 500
    ):
        """
        初始化iText2KG框架
        
        :param neo4j_driver: Neo4j驱动
        :param use_llm: 是否使用LLM增强
        :param llm_client: LLM客户端
        :param chunk_size: 文本块大小
        """
        self.neo4j_driver = neo4j_driver
        self.use_llm = use_llm
        self.llm_client = llm_client
        
        self.chunker = TextChunker(chunk_size=chunk_size)
        self.entity_extractor = EntityExtractor(use_llm=use_llm, llm_client=llm_client)
        self.relation_extractor = RelationExtractor(use_llm=use_llm, llm_client=llm_client)
        
        self.extraction_stats = {
            "documents_processed": 0,
            "entities_extracted": 0,
            "relations_extracted": 0,
            "triples_written": 0
        }
        
        print("🔧 [iText2KG] 增量式知识抽取框架初始化完成")
    
    def process_document(
        self,
        document: Dict[str, Any],
        write_to_neo4j: bool = True
    ) -> Dict[str, Any]:
        """
        处理单个文档
        
        根据文档5.2节流程：
        1. 文档蒸馏（分块）
        2. 实体关系抽取
        3. Neo4j存储
        
        :param document: 文档字典
        :param write_to_neo4j: 是否写入Neo4j
        :return: 处理结果
        """
        print(f"📄 [iText2KG] 处理文档: {document.get('title', 'Unknown')}")
        
        all_entities = []
        all_triples = []
        
        chunks = self.chunker.chunk_document(document)
        print(f"   分块完成: {len(chunks)} 个文本块")
        
        for chunk in chunks:
            entities = self.entity_extractor.extract_entities(chunk["text"])
            all_entities.extend(entities)
            
            triples = self.relation_extractor.extract_relations(chunk["text"], entities)
            all_triples.extend(triples)
        
        all_entities = self._deduplicate(all_entities, key=lambda e: (e.name, e.entity_type))
        all_triples = self._deduplicate(all_triples, key=lambda t: (t.head, t.relation, t.tail))
        
        print(f"   提取实体: {len(all_entities)} 个")
        print(f"   提取关系: {len(all_triples)} 个")
        
        if write_to_neo4j and self.neo4j_driver:
            written = self._write_to_neo4j(all_triples)
            print(f"   写入Neo4j: {written} 个三元组")
            self.extraction_stats["triples_written"] += written
        
        self.extraction_stats["documents_processed"] += 1
        self.extraction_stats["entities_extracted"] += len(all_entities)
        self.extraction_stats["relations_extracted"] += len(all_triples)
        
        return {
            "document": document.get("title", ""),
            "chunks": len(chunks),
            "entities": [e.to_dict() if hasattr(e, 'to_dict') else {"name": e.name, "type": e.entity_type} for e in all_entities],
            "triples": [t.to_dict() for t in all_triples],
            "stats": self.extraction_stats
        }
    
    def process_documents(
        self,
        documents: List[Dict[str, Any]],
        write_to_neo4j: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量处理文档
        
        :param documents: 文档列表
        :param write_to_neo4j: 是否写入Neo4j
        :return: 处理结果列表
        """
        results = []
        for doc in documents:
            result = self.process_document(doc, write_to_neo4j)
            results.append(result)
        return results
    
    def _write_to_neo4j(self, triples: List[Triple]) -> int:
        """
        将三元组写入Neo4j
        
        根据文档5.2节：
        "通过Neo4j Python Driver将抽取的三元组写入图数据库，
        并利用Neo4j的约束机制（Constraints）自动去重和融合实体"
        
        :param triples: 三元组列表
        :return: 写入数量
        """
        if not self.neo4j_driver:
            return 0
        
        written = 0
        
        try:
            with self.neo4j_driver.session() as session:
                for triple in triples:
                    try:
                        cypher = f"""
                        MERGE (h:{triple.head_type} {{name: $head_name}})
                        MERGE (t:{triple.tail_type} {{name: $tail_name}})
                        MERGE (h)-[r:{triple.relation}]->(t)
                        SET r.confidence = $confidence,
                            r.source = $source
                        """
                        session.run(
                            cypher,
                            head_name=triple.head,
                            tail_name=triple.tail,
                            confidence=triple.confidence,
                            source=triple.source
                        )
                        written += 1
                    except Exception as e:
                        print(f"   ⚠️ 写入三元组失败: {e}")
        except Exception as e:
            print(f"❌ Neo4j写入错误: {e}")
        
        return written
    
    def _deduplicate(self, items: List, key) -> List:
        """
        去重列表
        
        :param items: 列表
        :param key: 键函数
        :return: 去重后的列表
        """
        seen = set()
        unique = []
        for item in items:
            k = key(item)
            if k not in seen:
                seen.add(k)
                unique.append(item)
        return unique
    
    def extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        从纯文本提取知识
        
        :param text: 输入文本
        :return: 提取结果
        """
        entities = self.entity_extractor.extract_entities(text)
        triples = self.relation_extractor.extract_relations(text, entities)
        
        return {
            "entities": [e.to_dict() if hasattr(e, 'to_dict') else {"name": e.name, "type": e.entity_type} for e in entities],
            "triples": [t.to_dict() for t in triples]
        }
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """
        process_text 别名方法，兼容旧接口
        
        :param text: 输入文本
        :return: 抽取的知识三元组
        """
        return self.extract_from_text(text)
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取统计信息
        
        :return: 统计字典
        """
        return self.extraction_stats.copy()


def demo_itext2kg():
    """
    演示iText2KG框架
    """
    print("=" * 70)
    print("📊 iText2KG 增量式知识抽取演示")
    print("=" * 70)
    
    itext2kg = IText2KG(use_llm=False)
    
    sample_document = {
        "id": "doc_001",
        "title": "小麦条锈病防治技术",
        "source": "农业技术推广公报",
        "content": """
小麦条锈病是由条形柄锈菌引起的真菌性病害，主要危害小麦叶片。
该病害在低温高湿环境下易发生流行。

主要症状表现为：叶片出现黄色条状孢子堆，沿叶脉排列，严重时导致叶片枯死。
在适宜温度9-16°C、高湿度条件下，病害发展迅速。

防治建议：
1. 使用三唑酮或戊唑醇进行化学防治
2. 选用抗病品种，如济麦22
3. 合理密植，改善田间通风
4. 及时清除病残体，减少菌源

预防措施包括抗病选种、适时播种、清沟沥水降低田间湿度。
"""
    }
    
    result = itext2kg.process_document(sample_document, write_to_neo4j=False)
    
    print(f"\n📄 文档: {result['document']}")
    print(f"📊 文本块数: {result['chunks']}")
    
    print(f"\n🔍 提取的实体 ({len(result['entities'])} 个):")
    for entity in result['entities'][:10]:
        print(f"   - {entity['name']} ({entity['type']})")
    
    print(f"\n🔗 提取的三元组 ({len(result['triples'])} 个):")
    for triple in result['triples'][:10]:
        print(f"   - ({triple['head']}) --[{triple['relation']}]--> ({triple['tail']})")
    
    print(f"\n📈 统计信息: {result['stats']}")
    
    print("\n" + "=" * 70)
    print("✅ iText2KG 演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo_itext2kg()

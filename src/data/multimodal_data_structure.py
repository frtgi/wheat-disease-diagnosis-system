# -*- coding: utf-8 -*-
"""
多模态数据结构模块 (Multimodal Data Structure)

扩展数据 JSON 结构，支持 metadata 字段：
1. 图像 + 对话 + 元数据结构
2. 环境数据验证
3. 知识图谱关联
4. 数据增强支持

技术特性:
- 结构化数据格式
- 数据验证
- 元数据解析
- 知识图谱三元组嵌入
"""
import json
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid


@dataclass
class EnvironmentMetadata:
    """
    环境元数据结构
    
    包含温度、湿度、生长阶段、地理位置等环境信息
    """
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    growth_stage: Optional[str] = None
    location: Optional[str] = None
    region_id: Optional[int] = None
    province_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    light_intensity: Optional[float] = None
    soil_moisture: Optional[float] = None
    wind_speed: Optional[float] = None
    precipitation: Optional[float] = None
    weather_condition: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentMetadata':
        """从字典创建"""
        return cls(
            temperature=data.get('temperature'),
            humidity=data.get('humidity'),
            growth_stage=data.get('growth_stage'),
            location=data.get('location'),
            region_id=data.get('region_id'),
            province_id=data.get('province_id'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            light_intensity=data.get('light_intensity'),
            soil_moisture=data.get('soil_moisture'),
            wind_speed=data.get('wind_speed'),
            precipitation=data.get('precipitation'),
            weather_condition=data.get('weather_condition'),
            timestamp=data.get('timestamp')
        )


@dataclass
class KnowledgeGraphTriple:
    """
    知识图谱三元组结构
    
    用于在训练数据中植入农业知识图谱信息
    """
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'subject': self.subject,
            'predicate': self.predicate,
            'object': self.object,
            'confidence': self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeGraphTriple':
        """从字典创建"""
        return cls(
            subject=data['subject'],
            predicate=data['predicate'],
            object=data['object'],
            confidence=data.get('confidence', 1.0)
        )


@dataclass
class Conversation:
    """
    对话结构
    
    包含人类问题和 GPT 回答
    """
    from_role: str
    value: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'from': self.from_role,
            'value': self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """从字典创建"""
        return cls(
            from_role=data['from'],
            value=data['value']
        )


@dataclass
class MultimodalDataSample:
    """
    多模态数据样本结构
    
    扩展的 JSON 结构，包含：
    - id: 样本唯一标识
    - image: 图像路径
    - metadata: 环境元数据
    - conversations: 对话列表
    - knowledge_triples: 知识图谱三元组（可选）
    """
    id: str
    image: str
    conversations: List[Conversation]
    metadata: Optional[EnvironmentMetadata] = None
    knowledge_triples: List[KnowledgeGraphTriple] = field(default_factory=list)
    disease_name: Optional[str] = None
    disease_severity: Optional[str] = None
    confidence: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'id': self.id,
            'image': self.image,
            'conversations': [c.to_dict() for c in self.conversations]
        }
        
        if self.metadata:
            result['metadata'] = self.metadata.to_dict()
        
        if self.knowledge_triples:
            result['knowledge_triples'] = [t.to_dict() for t in self.knowledge_triples]
        
        if self.disease_name:
            result['disease_name'] = self.disease_name
        
        if self.disease_severity:
            result['disease_severity'] = self.disease_severity
        
        if self.confidence is not None:
            result['confidence'] = self.confidence
        
        result['created_at'] = self.created_at
        result['updated_at'] = self.updated_at
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultimodalDataSample':
        """从字典创建"""
        conversations = [Conversation.from_dict(c) for c in data.get('conversations', [])]
        
        metadata = None
        if 'metadata' in data:
            metadata = EnvironmentMetadata.from_dict(data['metadata'])
        
        knowledge_triples = []
        if 'knowledge_triples' in data:
            knowledge_triples = [KnowledgeGraphTriple.from_dict(t) for t in data['knowledge_triples']]
        
        return cls(
            id=data['id'],
            image=data['image'],
            conversations=conversations,
            metadata=metadata,
            knowledge_triples=knowledge_triples,
            disease_name=data.get('disease_name'),
            disease_severity=data.get('disease_severity'),
            confidence=data.get('confidence'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


class MultimodalDatasetBuilder:
    """
    多模态数据集构建器
    
    用于构建符合新结构的数据集
    """
    
    def __init__(self, output_dir: str = "data/processed"):
        """
        初始化数据集构建器
        
        :param output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.samples: List[MultimodalDataSample] = []
        
        # 生长阶段列表
        self.growth_stages = [
            "苗期", "分蘖期", "越冬期", "返青期", "起身期",
            "拔节期", "孕穗期", "抽穗期", "开花期", "灌浆期", "成熟期"
        ]
        
        # 病害列表
        self.diseases = [
            "条锈病", "叶锈病", "秆锈病", "白粉病", "赤霉病",
            "纹枯病", "根腐病", "蚜虫", "麦蜘蛛", "吸浆虫"
        ]
        
        # 地区列表
        self.regions = {
            "河南郑州": {"region_id": 1, "province_id": 16},
            "山东济南": {"region_id": 2, "province_id": 14},
            "河北石家庄": {"region_id": 3, "province_id": 5},
            "江苏南京": {"region_id": 4, "province_id": 9},
            "安徽合肥": {"region_id": 5, "province_id": 10}
        }
    
    def add_sample(
        self,
        image_path: str,
        human_question: str,
        gpt_answer: str,
        metadata: Optional[Dict[str, Any]] = None,
        knowledge_triples: Optional[List[Dict[str, Any]]] = None,
        disease_name: Optional[str] = None,
        disease_severity: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> str:
        """
        添加样本
        
        :param image_path: 图像路径
        :param human_question: 人类问题
        :param gpt_answer: GPT 回答
        :param metadata: 元数据
        :param knowledge_triples: 知识图谱三元组
        :param disease_name: 病害名称
        :param disease_severity: 病害严重程度
        :param confidence: 置信度
        :return: 样本 ID
        """
        sample_id = str(uuid.uuid4())
        
        # 创建对话
        conversations = [
            Conversation(from_role='human', value=human_question),
            Conversation(from_role='gpt', value=gpt_answer)
        ]
        
        # 创建元数据
        env_metadata = None
        if metadata:
            env_metadata = EnvironmentMetadata.from_dict(metadata)
        
        # 创建知识三元组
        kg_triples = []
        if knowledge_triples:
            kg_triples = [KnowledgeGraphTriple.from_dict(t) for t in knowledge_triples]
        
        # 创建样本
        sample = MultimodalDataSample(
            id=sample_id,
            image=image_path,
            conversations=conversations,
            metadata=env_metadata,
            knowledge_triples=kg_triples,
            disease_name=disease_name,
            disease_severity=disease_severity,
            confidence=confidence
        )
        
        self.samples.append(sample)
        return sample_id
    
    def create_sample_with_environment(
        self,
        image_path: str,
        disease_name: str,
        temperature: float,
        humidity: float,
        growth_stage: str,
        location: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> MultimodalDataSample:
        """
        创建带环境信息的样本
        
        :param image_path: 图像路径
        :param disease_name: 病害名称
        :param temperature: 温度
        :param humidity: 湿度
        :param growth_stage: 生长阶段
        :param location: 地点
        :param additional_info: 额外信息
        :return: 数据样本
        """
        sample_id = str(uuid.uuid4())
        
        # 获取地区信息
        region_info = self.regions.get(location, {"region_id": 0, "province_id": 0})
        
        # 创建元数据
        metadata = EnvironmentMetadata(
            temperature=temperature,
            humidity=humidity,
            growth_stage=growth_stage,
            location=location,
            region_id=region_info.get('region_id'),
            province_id=region_info.get('province_id')
        )
        
        if additional_info:
            for key, value in additional_info.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
        
        # 创建问题
        human_question = f"当前环境湿度 {humidity}%，温度 {temperature}℃，生长阶段为{growth_stage}，请诊断叶片病害。"
        
        # 创建回答
        gpt_answer = f"结合高湿环境和叶片病斑特征，诊断为小麦{disease_name}。建议及时采取防治措施。"
        
        # 创建对话
        conversations = [
            Conversation(from_role='human', value=human_question),
            Conversation(from_role='gpt', value=gpt_answer)
        ]
        
        # 创建样本
        sample = MultimodalDataSample(
            id=sample_id,
            image=image_path,
            conversations=conversations,
            metadata=metadata,
            disease_name=disease_name,
            knowledge_triples=self._get_disease_knowledge_triples(disease_name)
        )
        
        return sample
    
    def _get_disease_knowledge_triples(self, disease_name: str) -> List[KnowledgeGraphTriple]:
        """
        获取病害相关知识三元组
        
        :param disease_name: 病害名称
        :return: 知识三元组列表
        """
        # 简化的知识三元组
        triples = [
            KnowledgeGraphTriple(
                subject=disease_name,
                predicate="属于",
                object="小麦病害"
            ),
            KnowledgeGraphTriple(
                subject=disease_name,
                predicate="影响部位",
                object="叶片"
            )
        ]
        return triples
    
    def save_dataset(self, filename: str = "multimodal_dataset.json") -> str:
        """
        保存数据集
        
        :param filename: 文件名
        :return: 文件路径
        """
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, filename)
        
        data = [sample.to_dict() for sample in self.samples]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def load_dataset(self, filepath: str) -> List[MultimodalDataSample]:
        """
        加载数据集
        
        :param filepath: 文件路径
        :return: 数据样本列表
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.samples = [MultimodalDataSample.from_dict(item) for item in data]
        return self.samples


def create_sample_json_example() -> str:
    """
    创建示例 JSON 数据
    
    :return: JSON 字符串
    """
    sample = {
        "id": "wheat_001",
        "image": "images/wheat_rust_001.jpg",
        "metadata": {
            "temperature": 25.5,
            "humidity": 80,
            "growth_stage": "抽穗期",
            "location": "河南郑州",
            "region_id": 1,
            "province_id": 16,
            "latitude": 34.7466,
            "longitude": 113.6253,
            "light_intensity": 50000,
            "soil_moisture": 65,
            "wind_speed": 2.5,
            "precipitation": 0,
            "weather_condition": "多云",
            "timestamp": "2026-03-17T10:30:00"
        },
        "conversations": [
            {
                "from": "human",
                "value": "当前环境湿度 80%，温度 25.5℃，生长阶段为抽穗期，请诊断叶片病害。"
            },
            {
                "from": "gpt",
                "value": "结合高湿环境和叶片病斑特征，诊断为小麦条锈病。建议及时清除病残体，喷施粉锈宁可湿性粉剂进行防治。"
            }
        ],
        "knowledge_triples": [
            {
                "subject": "条锈病",
                "predicate": "致病菌",
                "object": "条形柄锈菌",
                "confidence": 0.95
            },
            {
                "subject": "条锈病",
                "predicate": "适宜温度",
                "object": "10-15℃",
                "confidence": 0.9
            },
            {
                "subject": "条锈病",
                "predicate": "防治方法",
                "object": "喷施粉锈宁",
                "confidence": 0.85
            }
        ],
        "disease_name": "条锈病",
        "disease_severity": "中度",
        "confidence": 0.92,
        "created_at": "2026-03-17T10:30:00",
        "updated_at": "2026-03-17T10:30:00"
    }
    
    return json.dumps(sample, ensure_ascii=False, indent=2)


def test_data_structure():
    """测试数据结构"""
    print("\n" + "=" * 60)
    print("多模态数据结构测试")
    print("=" * 60)
    
    try:
        print("\n[测试 1] 创建示例 JSON 数据")
        example_json = create_sample_json_example()
        print(example_json)
        
        print("\n[测试 2] 解析 JSON 数据")
        data = json.loads(example_json)
        sample = MultimodalDataSample.from_dict(data)
        print(f"[OK] 样本 ID: {sample.id}")
        print(f"[OK] 图像路径: {sample.image}")
        print(f"[OK] 对话数量: {len(sample.conversations)}")
        print(f"[OK] 元数据温度: {sample.metadata.temperature}")
        print(f"[OK] 知识三元组数量: {len(sample.knowledge_triples)}")
        
        print("\n[测试 3] 数据集构建器")
        builder = MultimodalDatasetBuilder(output_dir="data/test")
        
        sample = builder.create_sample_with_environment(
            image_path="images/test_001.jpg",
            disease_name="白粉病",
            temperature=22.0,
            humidity=75.0,
            growth_stage="拔节期",
            location="山东济南"
        )
        
        print(f"[OK] 创建样本 ID: {sample.id}")
        print(f"[OK] 元数据: {sample.metadata.to_dict()}")
        
        print("\n[测试 4] 添加自定义样本")
        sample_id = builder.add_sample(
            image_path="images/custom_001.jpg",
            human_question="这片叶子上的黄色斑点是什么？",
            gpt_answer="根据图像特征，可能是小麦叶锈病。",
            metadata={"temperature": 20, "humidity": 70},
            disease_name="叶锈病"
        )
        print(f"[OK] 添加样本 ID: {sample_id}")
        print(f"[OK] 当前样本数量: {len(builder.samples)}")
        
        print("\n[OK] 所有测试通过!")
        
    except Exception as e:
        print(f"\n[错误] 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_data_structure()

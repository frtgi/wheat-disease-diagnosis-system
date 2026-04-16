# -*- coding: utf-8 -*-
"""
知识图谱本体设计模块

基于文档第5.1节：知识图谱本体设计

定义小麦病害知识图谱的本体结构，包括：
1. 实体类型（Entity Types）
2. 关系类型（Relation Types）
3. 属性定义（Property Definitions）
4. 本体约束（Ontology Constraints）

作者: IWDDA团队
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime


class EntityType(Enum):
    """
    实体类型枚举
    
    参考文档5.1节：
    小麦病害知识图谱包含8类核心实体
    """
    CROP = "Crop"                       # 作物
    DISEASE = "Disease"                 # 病害
    SYMPTOM = "Symptom"                 # 症状
    PATHOGEN = "Pathogen"               # 病原
    ENVIRONMENT = "Environment"         # 环境因素
    CONTROL_MEASURE = "ControlMeasure"  # 防治措施
    CHEMICAL = "Chemical"               # 化学药剂
    CROP_PART = "CropPart"              # 作物部位


class RelationType(Enum):
    """
    关系类型枚举
    
    参考文档5.1节：
    定义实体间的语义关系
    """
    # 病害相关关系
    HAS_SYMPTOM = "HAS_SYMPTOM"         # 病害-症状
    HAS_PATHOGEN = "HAS_PATHOGEN"       # 病害-病原
    CAUSED_BY = "CAUSED_BY"             # 病害-成因
    AFFECTS = "AFFECTS"                 # 病害-影响部位
    
    # 防治相关关系
    TREATED_BY = "TREATED_BY"           # 病害-治疗
    PREVENTED_BY = "PREVENTED_BY"       # 病害-预防
    APPLIED_TO = "APPLIED_TO"           # 药剂-适用病害
    
    # 环境相关关系
    OCCURS_IN = "OCCURS_IN"             # 病害-发生环境
    FAVORS = "FAVORS"                   # 环境-利于病害
    
    # 因果关系
    CAUSES = "CAUSES"                   # 病原-导致病害
    INDICATES = "INDICATES"             # 症状-指示病害
    
    # 层级关系
    IS_A = "IS_A"                       # 继承关系
    PART_OF = "PART_OF"                 # 部分关系
    RELATED_TO = "RELATED_TO"           # 相关关系


@dataclass
class PropertyDefinition:
    """属性定义"""
    name: str
    data_type: str
    required: bool = False
    default: Any = None
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityDefinition:
    """实体定义"""
    entity_type: EntityType
    properties: List[PropertyDefinition]
    description: str = ""
    parent_type: Optional[EntityType] = None


@dataclass
class RelationDefinition:
    """关系定义"""
    relation_type: RelationType
    domain: EntityType                  # 定义域实体类型
    range: EntityType                   # 值域实体类型
    properties: List[PropertyDefinition] = field(default_factory=list)
    description: str = ""
    inverse_relation: Optional[RelationType] = None


class WheatDiseaseOntology:
    """
    小麦病害知识图谱本体
    
    参考文档5.1节：
    完整定义小麦病害领域的本体结构
    
    本体包含：
    - 8类实体类型
    - 12类关系类型
    - 完整的属性定义
    - 本体约束规则
    """
    
    def __init__(self):
        """初始化本体定义"""
        self.entity_definitions = self._define_entities()
        self.relation_definitions = self._define_relations()
        self.constraints = self._define_constraints()
    
    def _define_entities(self) -> Dict[EntityType, EntityDefinition]:
        """定义实体类型"""
        definitions = {}
        
        # 1. 作物实体
        definitions[EntityType.CROP] = EntityDefinition(
            entity_type=EntityType.CROP,
            properties=[
                PropertyDefinition("name", "string", True, description="作物名称"),
                PropertyDefinition("scientific_name", "string", description="学名"),
                PropertyDefinition("variety", "string", description="品种"),
                PropertyDefinition("growth_stage", "string", description="生长阶段"),
            ],
            description="小麦等作物实体"
        )
        
        # 2. 病害实体
        definitions[EntityType.DISEASE] = EntityDefinition(
            entity_type=EntityType.DISEASE,
            properties=[
                PropertyDefinition("name", "string", True, description="病害名称"),
                PropertyDefinition("scientific_name", "string", description="学名"),
                PropertyDefinition("disease_type", "string", description="病害类型（真菌/细菌/病毒/虫害）"),
                PropertyDefinition("severity", "string", description="严重程度分级"),
                PropertyDefinition("occurrence_season", "string", description="发生季节"),
                PropertyDefinition("incidence_rate", "float", description="发病率"),
                PropertyDefinition("description", "string", description="病害描述"),
            ],
            description="小麦病害实体"
        )
        
        # 3. 症状实体
        definitions[EntityType.SYMPTOM] = EntityDefinition(
            entity_type=EntityType.SYMPTOM,
            properties=[
                PropertyDefinition("name", "string", True, description="症状名称"),
                PropertyDefinition("description", "string", description="症状描述"),
                PropertyDefinition("visual_features", "string", description="视觉特征"),
                PropertyDefinition("location", "string", description="发生部位"),
                PropertyDefinition("stage", "string", description="发病阶段"),
            ],
            description="病害症状实体"
        )
        
        # 4. 病原实体
        definitions[EntityType.PATHOGEN] = EntityDefinition(
            entity_type=EntityType.PATHOGEN,
            properties=[
                PropertyDefinition("name", "string", True, description="病原名称"),
                PropertyDefinition("scientific_name", "string", description="学名"),
                PropertyDefinition("pathogen_type", "string", description="病原类型（真菌/细菌/病毒/昆虫）"),
                PropertyDefinition("survival_mode", "string", description="越冬方式"),
                PropertyDefinition("transmission_mode", "string", description="传播方式"),
            ],
            description="病害病原实体"
        )
        
        # 5. 环境因素实体
        definitions[EntityType.ENVIRONMENT] = EntityDefinition(
            entity_type=EntityType.ENVIRONMENT,
            properties=[
                PropertyDefinition("name", "string", True, description="环境因素名称"),
                PropertyDefinition("factor_type", "string", description="因素类型（温度/湿度/光照/土壤）"),
                PropertyDefinition("optimal_range", "string", description="适宜范围"),
                PropertyDefinition("description", "string", description="详细描述"),
            ],
            description="影响病害发生的环境因素"
        )
        
        # 6. 防治措施实体
        definitions[EntityType.CONTROL_MEASURE] = EntityDefinition(
            entity_type=EntityType.CONTROL_MEASURE,
            properties=[
                PropertyDefinition("name", "string", True, description="措施名称"),
                PropertyDefinition("measure_type", "string", description="措施类型（农业/化学/生物）"),
                PropertyDefinition("timing", "string", description="实施时机"),
                PropertyDefinition("method", "string", description="实施方法"),
                PropertyDefinition("effectiveness", "float", description="防治效果"),
                PropertyDefinition("description", "string", description="详细说明"),
            ],
            description="病害防治措施"
        )
        
        # 7. 化学药剂实体
        definitions[EntityType.CHEMICAL] = EntityDefinition(
            entity_type=EntityType.CHEMICAL,
            properties=[
                PropertyDefinition("name", "string", True, description="药剂名称"),
                PropertyDefinition("chemical_type", "string", description="药剂类型（杀菌剂/杀虫剂）"),
                PropertyDefinition("active_ingredient", "string", description="有效成分"),
                PropertyDefinition("usage_method", "string", description="使用方法"),
                PropertyDefinition("dosage", "string", description="用量"),
                PropertyDefinition("safety_interval", "int", description="安全间隔期（天）"),
                PropertyDefinition("toxicity", "string", description="毒性等级"),
            ],
            description="化学防治药剂"
        )
        
        # 8. 作物部位实体
        definitions[EntityType.CROP_PART] = EntityDefinition(
            entity_type=EntityType.CROP_PART,
            properties=[
                PropertyDefinition("name", "string", True, description="部位名称"),
                PropertyDefinition("description", "string", description="部位描述"),
                PropertyDefinition("susceptibility", "string", description="易感病程度"),
            ],
            description="作物各部位"
        )
        
        return definitions
    
    def _define_relations(self) -> Dict[RelationType, RelationDefinition]:
        """定义关系类型"""
        definitions = {}
        
        # 病害-症状关系
        definitions[RelationType.HAS_SYMPTOM] = RelationDefinition(
            relation_type=RelationType.HAS_SYMPTOM,
            domain=EntityType.DISEASE,
            range=EntityType.SYMPTOM,
            properties=[
                PropertyDefinition("severity", "string", description="症状严重程度"),
                PropertyDefinition("frequency", "float", description="出现频率"),
            ],
            description="病害表现出的症状",
            inverse_relation=RelationType.INDICATES
        )
        
        # 症状-病害关系（反向）
        definitions[RelationType.INDICATES] = RelationDefinition(
            relation_type=RelationType.INDICATES,
            domain=EntityType.SYMPTOM,
            range=EntityType.DISEASE,
            description="症状指示的病害",
            inverse_relation=RelationType.HAS_SYMPTOM
        )
        
        # 病害-病原关系
        definitions[RelationType.HAS_PATHOGEN] = RelationDefinition(
            relation_type=RelationType.HAS_PATHOGEN,
            domain=EntityType.DISEASE,
            range=EntityType.PATHOGEN,
            description="病害的致病病原",
            inverse_relation=RelationType.CAUSES
        )
        
        # 病原-病害关系（反向）
        definitions[RelationType.CAUSES] = RelationDefinition(
            relation_type=RelationType.CAUSES,
            domain=EntityType.PATHOGEN,
            range=EntityType.DISEASE,
            description="病原导致的病害",
            inverse_relation=RelationType.HAS_PATHOGEN
        )
        
        # 病害-成因关系
        definitions[RelationType.CAUSED_BY] = RelationDefinition(
            relation_type=RelationType.CAUSED_BY,
            domain=EntityType.DISEASE,
            range=EntityType.ENVIRONMENT,
            description="病害发生的环境成因"
        )
        
        # 病害-影响部位关系
        definitions[RelationType.AFFECTS] = RelationDefinition(
            relation_type=RelationType.AFFECTS,
            domain=EntityType.DISEASE,
            range=EntityType.CROP_PART,
            description="病害影响的作物部位"
        )
        
        # 病害-治疗关系
        definitions[RelationType.TREATED_BY] = RelationDefinition(
            relation_type=RelationType.TREATED_BY,
            domain=EntityType.DISEASE,
            range=EntityType.CHEMICAL,
            properties=[
                PropertyDefinition("effectiveness", "float", description="治疗效果"),
                PropertyDefinition("timing", "string", description="施药时机"),
            ],
            description="病害的治疗药剂",
            inverse_relation=RelationType.APPLIED_TO
        )
        
        # 药剂-适用病害关系（反向）
        definitions[RelationType.APPLIED_TO] = RelationDefinition(
            relation_type=RelationType.APPLIED_TO,
            domain=EntityType.CHEMICAL,
            range=EntityType.DISEASE,
            description="药剂适用的病害",
            inverse_relation=RelationType.TREATED_BY
        )
        
        # 病害-预防关系
        definitions[RelationType.PREVENTED_BY] = RelationDefinition(
            relation_type=RelationType.PREVENTED_BY,
            domain=EntityType.DISEASE,
            range=EntityType.CONTROL_MEASURE,
            properties=[
                PropertyDefinition("effectiveness", "float", description="预防效果"),
            ],
            description="病害的预防措施"
        )
        
        # 病害-发生环境关系
        definitions[RelationType.OCCURS_IN] = RelationDefinition(
            relation_type=RelationType.OCCURS_IN,
            domain=EntityType.DISEASE,
            range=EntityType.ENVIRONMENT,
            description="病害发生的环境条件"
        )
        
        # 环境-利于病害关系
        definitions[RelationType.FAVORS] = RelationDefinition(
            relation_type=RelationType.FAVORS,
            domain=EntityType.ENVIRONMENT,
            range=EntityType.DISEASE,
            description="环境因素利于发生的病害"
        )
        
        # 继承关系
        definitions[RelationType.IS_A] = RelationDefinition(
            relation_type=RelationType.IS_A,
            domain=EntityType.DISEASE,
            range=EntityType.DISEASE,
            description="病害类型的继承关系"
        )
        
        # 相关关系
        definitions[RelationType.RELATED_TO] = RelationDefinition(
            relation_type=RelationType.RELATED_TO,
            domain=EntityType.DISEASE,
            range=EntityType.DISEASE,
            properties=[
                PropertyDefinition("relation_strength", "float", description="关联强度"),
            ],
            description="病害间的相关关系"
        )
        
        return definitions
    
    def _define_constraints(self) -> List[Dict[str, Any]]:
        """定义本体约束"""
        return [
            {
                "name": "unique_disease_name",
                "type": "uniqueness",
                "entity_type": EntityType.DISEASE,
                "property": "name",
                "description": "病害名称必须唯一"
            },
            {
                "name": "valid_disease_type",
                "type": "enumeration",
                "entity_type": EntityType.DISEASE,
                "property": "disease_type",
                "values": ["Fungus", "Bacteria", "Virus", "Insect", "Other"],
                "description": "病害类型必须是有效枚举值"
            },
            {
                "name": "valid_severity",
                "type": "enumeration",
                "entity_type": EntityType.DISEASE,
                "property": "severity",
                "values": ["轻度", "中度", "重度", "严重"],
                "description": "严重程度必须是有效枚举值"
            },
            {
                "name": "confidence_range",
                "type": "range",
                "property": "effectiveness",
                "min": 0.0,
                "max": 1.0,
                "description": "效果值必须在0-1之间"
            },
            {
                "name": "required_symptom_for_disease",
                "type": "cardinality",
                "relation": RelationType.HAS_SYMPTOM,
                "min": 1,
                "description": "每个病害至少有一个症状"
            },
        ]
    
    def get_entity_definition(self, entity_type: EntityType) -> Optional[EntityDefinition]:
        """获取实体定义"""
        return self.entity_definitions.get(entity_type)
    
    def get_relation_definition(self, relation_type: RelationType) -> Optional[RelationDefinition]:
        """获取关系定义"""
        return self.relation_definitions.get(relation_type)
    
    def get_valid_relations(
        self,
        domain_type: EntityType
    ) -> List[RelationDefinition]:
        """获取指定实体类型可发出的关系"""
        return [
            rel_def for rel_def in self.relation_definitions.values()
            if rel_def.domain == domain_type
        ]
    
    def validate_entity(
        self,
        entity_type: EntityType,
        properties: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        验证实体属性是否符合本体定义
        
        Args:
            entity_type: 实体类型
            properties: 属性字典
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        definition = self.entity_definitions.get(entity_type)
        
        if definition is None:
            return False, [f"未知的实体类型: {entity_type}"]
        
        # 检查必需属性
        for prop_def in definition.properties:
            if prop_def.required and prop_def.name not in properties:
                errors.append(f"缺少必需属性: {prop_def.name}")
        
        # 检查约束
        for constraint in self.constraints:
            if constraint["type"] == "enumeration":
                prop_name = constraint["property"]
                if prop_name in properties:
                    if properties[prop_name] not in constraint["values"]:
                        errors.append(
                            f"属性 {prop_name} 的值 '{properties[prop_name]}' "
                            f"不在有效值列表中: {constraint['values']}"
                        )
            
            elif constraint["type"] == "range":
                prop_name = constraint["property"]
                if prop_name in properties:
                    value = properties[prop_name]
                    if not (constraint["min"] <= value <= constraint["max"]):
                        errors.append(
                            f"属性 {prop_name} 的值 {value} "
                            f"超出范围 [{constraint['min']}, {constraint['max']}]"
                        )
        
        return len(errors) == 0, errors
    
    def to_cypher_schema(self) -> str:
        """
        生成Neo4j Cypher模式创建语句
        
        Returns:
            Cypher语句字符串
        """
        cypher_lines = []
        
        # 创建实体节点约束
        cypher_lines.append("// === 实体节点约束 ===")
        for entity_type, definition in self.entity_definitions.items():
            cypher_lines.append(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{entity_type.value}) "
                f"REQUIRE n.name IS UNIQUE;"
            )
        
        # 创建索引
        cypher_lines.append("\n// === 实体节点索引 ===")
        for entity_type, definition in self.entity_definitions.items():
            for prop in definition.properties:
                if prop.required:
                    cypher_lines.append(
                        f"CREATE INDEX IF NOT EXISTS FOR (n:{entity_type.value}) "
                        f"ON (n.{prop.name});"
                    )
        
        return "\n".join(cypher_lines)


class KnowledgeGraphInitializer:
    """
    知识图谱初始化器
    
    根据本体定义初始化知识图谱数据
    """
    
    def __init__(self, ontology: WheatDiseaseOntology):
        """
        初始化
        
        Args:
            ontology: 本体定义
        """
        self.ontology = ontology
    
    def get_initial_entities(self) -> Dict[EntityType, List[Dict[str, Any]]]:
        """
        获取初始实体数据
        
        Returns:
            各类型实体的初始数据
        """
        entities = {
            EntityType.DISEASE: [
                {
                    "name": "条锈病",
                    "scientific_name": "Stripe Rust",
                    "disease_type": "Fungus",
                    "severity": "中度",
                    "occurrence_season": "春季",
                    "description": "由条形柄锈菌引起的小麦真菌性病害"
                },
                {
                    "name": "叶锈病",
                    "scientific_name": "Leaf Rust",
                    "disease_type": "Fungus",
                    "severity": "轻度",
                    "occurrence_season": "春末夏初",
                    "description": "由小麦隐匿柄锈菌引起的病害"
                },
                {
                    "name": "白粉病",
                    "scientific_name": "Powdery Mildew",
                    "disease_type": "Fungus",
                    "severity": "中度",
                    "occurrence_season": "春季",
                    "description": "由禾本科布氏白粉菌引起的病害"
                },
                {
                    "name": "赤霉病",
                    "scientific_name": "Fusarium Head Blight",
                    "disease_type": "Fungus",
                    "severity": "重度",
                    "occurrence_season": "扬花期",
                    "description": "由禾谷镰刀菌引起的穗部病害"
                },
                {
                    "name": "纹枯病",
                    "scientific_name": "Sheath Blight",
                    "disease_type": "Fungus",
                    "severity": "中度",
                    "occurrence_season": "拔节期",
                    "description": "由立枯丝核菌引起的茎基部病害"
                },
                {
                    "name": "蚜虫",
                    "scientific_name": "Aphids",
                    "disease_type": "Insect",
                    "severity": "中度",
                    "occurrence_season": "春夏",
                    "description": "小麦主要虫害，吸食汁液传播病毒"
                },
                {
                    "name": "茎锈病",
                    "scientific_name": "Stem Rust",
                    "disease_type": "Fungus",
                    "severity": "重度",
                    "occurrence_season": "夏季",
                    "description": "由小麦秆锈菌引起的茎秆病害"
                },
                {
                    "name": "全蚀病",
                    "scientific_name": "Take-all Disease",
                    "disease_type": "Fungus",
                    "severity": "重度",
                    "occurrence_season": "灌浆期",
                    "description": "由禾顶囊壳菌引起的根部病害"
                },
                {
                    "name": "根腐病",
                    "scientific_name": "Root Rot",
                    "disease_type": "Fungus",
                    "severity": "中度",
                    "occurrence_season": "苗期",
                    "description": "由多种真菌引起的根部病害"
                },
                {
                    "name": "黑穗病",
                    "scientific_name": "Smut",
                    "disease_type": "Fungus",
                    "severity": "中度",
                    "occurrence_season": "抽穗期",
                    "description": "由黑粉菌引起的穗部病害"
                },
                {
                    "name": "叶枯病",
                    "scientific_name": "Leaf Blight",
                    "disease_type": "Fungus",
                    "severity": "中度",
                    "occurrence_season": "灌浆期",
                    "description": "由链格孢菌引起的叶部病害"
                },
                {
                    "name": "颖枯病",
                    "scientific_name": "Glume Blotch",
                    "disease_type": "Fungus",
                    "severity": "轻度",
                    "occurrence_season": "抽穗期",
                    "description": "由颖枯壳针孢引起的颖壳病害"
                },
                {
                    "name": "红蜘蛛",
                    "scientific_name": "Spider Mite",
                    "disease_type": "Insect",
                    "severity": "中度",
                    "occurrence_season": "春夏",
                    "description": "小麦常见螨类害虫，吸食叶片汁液"
                },
                {
                    "name": "吸浆虫",
                    "scientific_name": "Wheat Midge",
                    "disease_type": "Insect",
                    "severity": "重度",
                    "occurrence_season": "抽穗期",
                    "description": "小麦重要害虫，幼虫吸食籽粒浆液"
                },
                {
                    "name": "麦叶蜂",
                    "scientific_name": "Wheat Sawfly",
                    "disease_type": "Insect",
                    "severity": "中度",
                    "occurrence_season": "春季",
                    "description": "小麦食叶害虫，幼虫啃食叶片"
                },
            ],
            
            EntityType.PATHOGEN: [
                {"name": "条形柄锈菌", "scientific_name": "Puccinia striiformis", "pathogen_type": "真菌"},
                {"name": "小麦隐匿柄锈菌", "scientific_name": "Puccinia triticina", "pathogen_type": "真菌"},
                {"name": "禾本科布氏白粉菌", "scientific_name": "Blumeria graminis", "pathogen_type": "真菌"},
                {"name": "禾谷镰刀菌", "scientific_name": "Fusarium graminearum", "pathogen_type": "真菌"},
                {"name": "立枯丝核菌", "scientific_name": "Rhizoctonia solani", "pathogen_type": "真菌"},
                {"name": "麦长管蚜", "scientific_name": "Sitobion avenae", "pathogen_type": "昆虫"},
                {"name": "小麦秆锈菌", "scientific_name": "Puccinia graminis", "pathogen_type": "真菌"},
                {"name": "禾顶囊壳菌", "scientific_name": "Gaeumannomyces graminis", "pathogen_type": "真菌"},
                {"name": "根腐离蠕孢", "scientific_name": "Bipolaris sorokiniana", "pathogen_type": "真菌"},
                {"name": "小麦黑粉菌", "scientific_name": "Ustilago tritici", "pathogen_type": "真菌"},
                {"name": "链格孢菌", "scientific_name": "Alternaria alternata", "pathogen_type": "真菌"},
                {"name": "颖枯壳针孢", "scientific_name": "Septoria nodorum", "pathogen_type": "真菌"},
                {"name": "麦岩螨", "scientific_name": "Petrobia latens", "pathogen_type": "螨类"},
                {"name": "麦红吸浆虫", "scientific_name": "Sitodiplosis mosellana", "pathogen_type": "昆虫"},
                {"name": "麦叶蜂幼虫", "scientific_name": "Dolerus tritici", "pathogen_type": "昆虫"},
            ],
            
            EntityType.SYMPTOM: [
                {"name": "条状锈斑", "description": "叶片上出现黄色条状病斑", "location": "叶片"},
                {"name": "圆形锈斑", "description": "叶片上出现橙黄色圆形病斑", "location": "叶片"},
                {"name": "白色粉状物", "description": "叶片表面覆盖白色粉状霉层", "location": "叶片"},
                {"name": "穗部枯白", "description": "穗部变白枯萎", "location": "穗部"},
                {"name": "云纹状病斑", "description": "叶鞘上出现云纹状病斑", "location": "叶鞘"},
                {"name": "叶片黄化", "description": "叶片变黄卷曲", "location": "叶片"},
                {"name": "茎秆锈斑", "description": "茎秆上出现红褐色锈斑", "location": "茎秆"},
                {"name": "根部腐烂", "description": "根部变黑腐烂", "location": "根部"},
                {"name": "籽粒黑粉", "description": "籽粒内充满黑粉", "location": "穗部"},
                {"name": "叶尖枯死", "description": "叶尖干枯变黄", "location": "叶片"},
                {"name": "颖壳褐斑", "description": "颖壳上出现褐色小斑点", "location": "穗部"},
                {"name": "叶片红点", "description": "叶片出现红色小斑点", "location": "叶片"},
                {"name": "籽粒空瘪", "description": "籽粒不饱满或空瘪", "location": "穗部"},
                {"name": "叶片缺刻", "description": "叶片边缘被啃食成缺刻", "location": "叶片"},
                {"name": "植株矮化", "description": "植株生长受阻矮小", "location": "整株"},
                {"name": "叶片褪绿", "description": "叶片颜色变浅褪绿", "location": "叶片"},
                {"name": "穗部粉红霉层", "description": "穗部出现粉红色霉层", "location": "穗部"},
                {"name": "茎基腐烂", "description": "茎基部腐烂变色", "location": "茎秆"},
            ],
            
            EntityType.ENVIRONMENT: [
                {"name": "高湿环境", "factor_type": "湿度", "optimal_range": "相对湿度>80%"},
                {"name": "低温寡照", "factor_type": "温度", "optimal_range": "气温9-15℃"},
                {"name": "高温干旱", "factor_type": "温度", "optimal_range": "气温>25℃且干旱"},
                {"name": "连阴雨", "factor_type": "降水", "optimal_range": "连续降雨>3天"},
                {"name": "温暖潮湿", "factor_type": "综合", "optimal_range": "气温15-25℃，湿度>70%"},
                {"name": "高温高湿", "factor_type": "综合", "optimal_range": "气温>25℃，湿度>80%"},
                {"name": "低温高湿", "factor_type": "综合", "optimal_range": "气温<15℃，湿度>80%"},
                {"name": "干旱少雨", "factor_type": "降水", "optimal_range": "长期无有效降雨"},
                {"name": "氮肥过量", "factor_type": "养分", "optimal_range": "氮肥施用过多"},
                {"name": "密植通风差", "factor_type": "栽培", "optimal_range": "种植密度过大"},
            ],
            
            EntityType.CHEMICAL: [
                {"name": "三唑酮", "chemical_type": "杀菌剂", "active_ingredient": "三唑酮", "usage_method": "喷雾", "dosage": "15%可湿性粉剂1000倍液"},
                {"name": "戊唑醇", "chemical_type": "杀菌剂", "active_ingredient": "戊唑醇", "usage_method": "喷雾", "dosage": "25%乳油3000倍液"},
                {"name": "多菌灵", "chemical_type": "杀菌剂", "active_ingredient": "多菌灵", "usage_method": "喷雾", "dosage": "50%可湿性粉剂500倍液"},
                {"name": "吡虫啉", "chemical_type": "杀虫剂", "active_ingredient": "吡虫啉", "usage_method": "喷雾", "dosage": "10%可湿性粉剂2000倍液"},
                {"name": "氰烯菌酯", "chemical_type": "杀菌剂", "active_ingredient": "氰烯菌酯", "usage_method": "花期喷雾", "dosage": "25%悬浮剂1500倍液"},
                {"name": "己唑醇", "chemical_type": "杀菌剂", "active_ingredient": "己唑醇", "usage_method": "喷雾", "dosage": "5%悬浮剂1500倍液"},
                {"name": "丙环唑", "chemical_type": "杀菌剂", "active_ingredient": "丙环唑", "usage_method": "喷雾", "dosage": "25%乳油2000倍液"},
                {"name": "阿维菌素", "chemical_type": "杀虫剂", "active_ingredient": "阿维菌素", "usage_method": "喷雾", "dosage": "1.8%乳油3000倍液"},
                {"name": "高效氯氟氰菊酯", "chemical_type": "杀虫剂", "active_ingredient": "高效氯氟氰菊酯", "usage_method": "喷雾", "dosage": "2.5%乳油1500倍液"},
                {"name": "噻虫嗪", "chemical_type": "杀虫剂", "active_ingredient": "噻虫嗪", "usage_method": "拌种或喷雾", "dosage": "70%种子处理剂"},
                {"name": "苯醚甲环唑", "chemical_type": "杀菌剂", "active_ingredient": "苯醚甲环唑", "usage_method": "喷雾", "dosage": "10%水分散粒剂1500倍液"},
                {"name": "氟环唑", "chemical_type": "杀菌剂", "active_ingredient": "氟环唑", "usage_method": "喷雾", "dosage": "12.5%悬浮剂2000倍液"},
            ],
            
            EntityType.CONTROL_MEASURE: [
                {"name": "抗病选种", "measure_type": "农业", "description": "选用抗病良种"},
                {"name": "轮作倒茬", "measure_type": "农业", "description": "与非禾本科作物轮作"},
                {"name": "清沟沥水", "measure_type": "农业", "description": "降低田间湿度"},
                {"name": "清除病残体", "measure_type": "农业", "description": "减少越冬菌源"},
                {"name": "适期播种", "measure_type": "农业", "description": "避开病害高发期"},
                {"name": "合理密植", "measure_type": "农业", "description": "控制种植密度改善通风"},
                {"name": "平衡施肥", "measure_type": "农业", "description": "氮磷钾合理配比"},
                {"name": "深翻土地", "measure_type": "农业", "description": "深翻减少土传病害"},
                {"name": "种子处理", "measure_type": "化学", "description": "药剂拌种预防病害"},
                {"name": "适时用药", "measure_type": "化学", "description": "发病初期及时用药"},
                {"name": "生物防治", "measure_type": "生物", "description": "利用天敌或生物农药"},
                {"name": "灯光诱杀", "measure_type": "物理", "description": "利用杀虫灯诱杀害虫"},
            ],
            
            EntityType.CROP_PART: [
                {"name": "叶片", "description": "小麦叶片", "susceptibility": "高"},
                {"name": "穗部", "description": "小麦穗部", "susceptibility": "中"},
                {"name": "茎秆", "description": "小麦茎秆", "susceptibility": "中"},
                {"name": "叶鞘", "description": "小麦叶鞘", "susceptibility": "中"},
                {"name": "根部", "description": "小麦根部", "susceptibility": "低"},
            ],
        }
        
        return entities
    
    def get_initial_relations(self) -> List[Dict[str, Any]]:
        """
        获取初始关系数据
        
        Returns:
            关系列表
        """
        relations = [
            # 病害-病原关系
            {"type": RelationType.HAS_PATHOGEN, "from": "条锈病", "to": "条形柄锈菌"},
            {"type": RelationType.HAS_PATHOGEN, "from": "叶锈病", "to": "小麦隐匿柄锈菌"},
            {"type": RelationType.HAS_PATHOGEN, "from": "白粉病", "to": "禾本科布氏白粉菌"},
            {"type": RelationType.HAS_PATHOGEN, "from": "赤霉病", "to": "禾谷镰刀菌"},
            {"type": RelationType.HAS_PATHOGEN, "from": "纹枯病", "to": "立枯丝核菌"},
            {"type": RelationType.HAS_PATHOGEN, "from": "蚜虫", "to": "麦长管蚜"},
            {"type": RelationType.HAS_PATHOGEN, "from": "茎锈病", "to": "小麦秆锈菌"},
            {"type": RelationType.HAS_PATHOGEN, "from": "全蚀病", "to": "禾顶囊壳菌"},
            {"type": RelationType.HAS_PATHOGEN, "from": "根腐病", "to": "根腐离蠕孢"},
            {"type": RelationType.HAS_PATHOGEN, "from": "黑穗病", "to": "小麦黑粉菌"},
            {"type": RelationType.HAS_PATHOGEN, "from": "叶枯病", "to": "链格孢菌"},
            {"type": RelationType.HAS_PATHOGEN, "from": "颖枯病", "to": "颖枯壳针孢"},
            {"type": RelationType.HAS_PATHOGEN, "from": "红蜘蛛", "to": "麦岩螨"},
            {"type": RelationType.HAS_PATHOGEN, "from": "吸浆虫", "to": "麦红吸浆虫"},
            {"type": RelationType.HAS_PATHOGEN, "from": "麦叶蜂", "to": "麦叶蜂幼虫"},
            
            # 病害-症状关系
            {"type": RelationType.HAS_SYMPTOM, "from": "条锈病", "to": "条状锈斑"},
            {"type": RelationType.HAS_SYMPTOM, "from": "叶锈病", "to": "圆形锈斑"},
            {"type": RelationType.HAS_SYMPTOM, "from": "白粉病", "to": "白色粉状物"},
            {"type": RelationType.HAS_SYMPTOM, "from": "赤霉病", "to": "穗部枯白"},
            {"type": RelationType.HAS_SYMPTOM, "from": "赤霉病", "to": "穗部粉红霉层"},
            {"type": RelationType.HAS_SYMPTOM, "from": "纹枯病", "to": "云纹状病斑"},
            {"type": RelationType.HAS_SYMPTOM, "from": "蚜虫", "to": "叶片黄化"},
            {"type": RelationType.HAS_SYMPTOM, "from": "茎锈病", "to": "茎秆锈斑"},
            {"type": RelationType.HAS_SYMPTOM, "from": "全蚀病", "to": "根部腐烂"},
            {"type": RelationType.HAS_SYMPTOM, "from": "全蚀病", "to": "植株矮化"},
            {"type": RelationType.HAS_SYMPTOM, "from": "根腐病", "to": "根部腐烂"},
            {"type": RelationType.HAS_SYMPTOM, "from": "黑穗病", "to": "籽粒黑粉"},
            {"type": RelationType.HAS_SYMPTOM, "from": "叶枯病", "to": "叶尖枯死"},
            {"type": RelationType.HAS_SYMPTOM, "from": "颖枯病", "to": "颖壳褐斑"},
            {"type": RelationType.HAS_SYMPTOM, "from": "红蜘蛛", "to": "叶片红点"},
            {"type": RelationType.HAS_SYMPTOM, "from": "吸浆虫", "to": "籽粒空瘪"},
            {"type": RelationType.HAS_SYMPTOM, "from": "麦叶蜂", "to": "叶片缺刻"},
            
            # 病害-环境关系
            {"type": RelationType.OCCURS_IN, "from": "条锈病", "to": "高湿环境"},
            {"type": RelationType.OCCURS_IN, "from": "条锈病", "to": "低温寡照"},
            {"type": RelationType.OCCURS_IN, "from": "白粉病", "to": "温暖潮湿"},
            {"type": RelationType.OCCURS_IN, "from": "赤霉病", "to": "连阴雨"},
            {"type": RelationType.OCCURS_IN, "from": "赤霉病", "to": "高温高湿"},
            {"type": RelationType.OCCURS_IN, "from": "蚜虫", "to": "高温干旱"},
            {"type": RelationType.OCCURS_IN, "from": "茎锈病", "to": "高温高湿"},
            {"type": RelationType.OCCURS_IN, "from": "全蚀病", "to": "低温高湿"},
            {"type": RelationType.OCCURS_IN, "from": "根腐病", "to": "低温高湿"},
            {"type": RelationType.OCCURS_IN, "from": "红蜘蛛", "to": "高温干旱"},
            {"type": RelationType.OCCURS_IN, "from": "白粉病", "to": "氮肥过量"},
            {"type": RelationType.OCCURS_IN, "from": "纹枯病", "to": "密植通风差"},
            
            # 病害-药剂关系
            {"type": RelationType.TREATED_BY, "from": "条锈病", "to": "三唑酮", "properties": {"effectiveness": 0.9}},
            {"type": RelationType.TREATED_BY, "from": "条锈病", "to": "戊唑醇", "properties": {"effectiveness": 0.92}},
            {"type": RelationType.TREATED_BY, "from": "叶锈病", "to": "三唑酮", "properties": {"effectiveness": 0.88}},
            {"type": RelationType.TREATED_BY, "from": "白粉病", "to": "三唑酮", "properties": {"effectiveness": 0.85}},
            {"type": RelationType.TREATED_BY, "from": "赤霉病", "to": "多菌灵", "properties": {"effectiveness": 0.85}},
            {"type": RelationType.TREATED_BY, "from": "赤霉病", "to": "氰烯菌酯", "properties": {"effectiveness": 0.92}},
            {"type": RelationType.TREATED_BY, "from": "蚜虫", "to": "吡虫啉", "properties": {"effectiveness": 0.95}},
            {"type": RelationType.TREATED_BY, "from": "茎锈病", "to": "戊唑醇", "properties": {"effectiveness": 0.90}},
            {"type": RelationType.TREATED_BY, "from": "纹枯病", "to": "己唑醇", "properties": {"effectiveness": 0.88}},
            {"type": RelationType.TREATED_BY, "from": "纹枯病", "to": "丙环唑", "properties": {"effectiveness": 0.85}},
            {"type": RelationType.TREATED_BY, "from": "全蚀病", "to": "苯醚甲环唑", "properties": {"effectiveness": 0.75}},
            {"type": RelationType.TREATED_BY, "from": "根腐病", "to": "多菌灵", "properties": {"effectiveness": 0.80}},
            {"type": RelationType.TREATED_BY, "from": "黑穗病", "to": "戊唑醇", "properties": {"effectiveness": 0.90}},
            {"type": RelationType.TREATED_BY, "from": "叶枯病", "to": "丙环唑", "properties": {"effectiveness": 0.85}},
            {"type": RelationType.TREATED_BY, "from": "红蜘蛛", "to": "阿维菌素", "properties": {"effectiveness": 0.92}},
            {"type": RelationType.TREATED_BY, "from": "吸浆虫", "to": "高效氯氟氰菊酯", "properties": {"effectiveness": 0.90}},
            {"type": RelationType.TREATED_BY, "from": "麦叶蜂", "to": "高效氯氟氰菊酯", "properties": {"effectiveness": 0.88}},
            {"type": RelationType.TREATED_BY, "from": "蚜虫", "to": "噻虫嗪", "properties": {"effectiveness": 0.93}},
            
            # 病害-预防措施关系
            {"type": RelationType.PREVENTED_BY, "from": "条锈病", "to": "抗病选种"},
            {"type": RelationType.PREVENTED_BY, "from": "条锈病", "to": "清沟沥水"},
            {"type": RelationType.PREVENTED_BY, "from": "赤霉病", "to": "抗病选种"},
            {"type": RelationType.PREVENTED_BY, "from": "赤霉病", "to": "清除病残体"},
            {"type": RelationType.PREVENTED_BY, "from": "纹枯病", "to": "轮作倒茬"},
            {"type": RelationType.PREVENTED_BY, "from": "白粉病", "to": "合理密植"},
            {"type": RelationType.PREVENTED_BY, "from": "白粉病", "to": "平衡施肥"},
            {"type": RelationType.PREVENTED_BY, "from": "全蚀病", "to": "深翻土地"},
            {"type": RelationType.PREVENTED_BY, "from": "根腐病", "to": "种子处理"},
            {"type": RelationType.PREVENTED_BY, "from": "黑穗病", "to": "种子处理"},
            {"type": RelationType.PREVENTED_BY, "from": "蚜虫", "to": "生物防治"},
            {"type": RelationType.PREVENTED_BY, "from": "吸浆虫", "to": "灯光诱杀"},
            
            # 病害-影响部位关系
            {"type": RelationType.AFFECTS, "from": "条锈病", "to": "叶片"},
            {"type": RelationType.AFFECTS, "from": "叶锈病", "to": "叶片"},
            {"type": RelationType.AFFECTS, "from": "白粉病", "to": "叶片"},
            {"type": RelationType.AFFECTS, "from": "赤霉病", "to": "穗部"},
            {"type": RelationType.AFFECTS, "from": "纹枯病", "to": "茎秆"},
            {"type": RelationType.AFFECTS, "from": "纹枯病", "to": "叶鞘"},
            {"type": RelationType.AFFECTS, "from": "茎锈病", "to": "茎秆"},
            {"type": RelationType.AFFECTS, "from": "全蚀病", "to": "根部"},
            {"type": RelationType.AFFECTS, "from": "根腐病", "to": "根部"},
            {"type": RelationType.AFFECTS, "from": "黑穗病", "to": "穗部"},
            {"type": RelationType.AFFECTS, "from": "叶枯病", "to": "叶片"},
            {"type": RelationType.AFFECTS, "from": "颖枯病", "to": "穗部"},
            {"type": RelationType.AFFECTS, "from": "红蜘蛛", "to": "叶片"},
            {"type": RelationType.AFFECTS, "from": "吸浆虫", "to": "穗部"},
            {"type": RelationType.AFFECTS, "from": "麦叶蜂", "to": "叶片"},
        ]
        
        return relations
    
    def generate_cypher_init_script(self) -> str:
        """
        生成完整的Neo4j初始化Cypher脚本
        
        Returns:
            Cypher脚本字符串
        """
        lines = []
        lines.append("// ========================================")
        lines.append("// 小麦病害知识图谱初始化脚本")
        lines.append(f"// 生成时间: {datetime.now().isoformat()}")
        lines.append("// ========================================\n")
        
        # 清空现有数据
        lines.append("// 清空现有数据")
        lines.append("MATCH (n) DETACH DELETE n;\n")
        
        # 创建实体节点
        entities = self.get_initial_entities()
        for entity_type, entity_list in entities.items():
            lines.append(f"// === 创建{entity_type.value}实体 ===")
            for i, entity in enumerate(entity_list):
                props_str = ", ".join([f'{k}: "{v}"' if isinstance(v, str) else f'{k}: {v}' 
                                       for k, v in entity.items()])
                lines.append(f"CREATE ({entity_type.value[0].lower()}{i}:{entity_type.value} {{{props_str}}})")
            lines.append("")
        
        # 创建关系
        relations = self.get_initial_relations()
        lines.append("// === 创建关系 ===")
        
        # 建立名称到变量名的映射
        entity_var_map = {}
        for entity_type, entity_list in entities.items():
            for i, entity in enumerate(entity_list):
                entity_var_map[entity["name"]] = f"{entity_type.value[0].lower()}{i}"
        
        for rel in relations:
            from_var = entity_var_map.get(rel["from"])
            to_var = entity_var_map.get(rel["to"])
            if from_var and to_var:
                rel_type = rel["type"].value
                if "properties" in rel:
                    props_str = ", ".join([f'{k}: {v}' if isinstance(v, (int, float)) else f'{k}: "{v}"' 
                                           for k, v in rel["properties"].items()])
                    lines.append(f"CREATE ({from_var})-[:{rel_type} {{{props_str}}}]->({to_var})")
                else:
                    lines.append(f"CREATE ({from_var})-[:{rel_type}]->({to_var})")
        
        lines.append("\n// === 初始化完成 ===")
        
        return "\n".join(lines)


def demo_ontology():
    """演示本体设计"""
    print("=" * 70)
    print("📊 小麦病害知识图谱本体演示")
    print("=" * 70)
    
    # 创建本体
    ontology = WheatDiseaseOntology()
    
    print("\n📋 实体类型定义:")
    for entity_type, definition in ontology.entity_definitions.items():
        print(f"\n   {entity_type.value}:")
        print(f"      描述: {definition.description}")
        print(f"      属性数: {len(definition.properties)}")
        for prop in definition.properties[:3]:
            required = "必需" if prop.required else "可选"
            print(f"         - {prop.name} ({prop.data_type}, {required})")
    
    print("\n📋 关系类型定义:")
    for relation_type, definition in ontology.relation_definitions.items():
        print(f"\n   {relation_type.value}:")
        print(f"      定义域: {definition.domain.value}")
        print(f"      值域: {definition.range.value}")
        print(f"      描述: {definition.description}")
    
    print("\n📋 实体验证示例:")
    # 验证有效实体
    valid, errors = ontology.validate_entity(
        EntityType.DISEASE,
        {"name": "测试病害", "disease_type": "Fungus", "severity": "中度"}
    )
    print(f"   有效实体验证: {valid}, 错误: {errors}")
    
    # 验证无效实体
    valid, errors = ontology.validate_entity(
        EntityType.DISEASE,
        {"name": "测试病害", "disease_type": "InvalidType"}
    )
    print(f"   无效实体验证: {valid}, 错误: {errors}")
    
    print("\n📋 初始化数据统计:")
    initializer = KnowledgeGraphInitializer(ontology)
    entities = initializer.get_initial_entities()
    relations = initializer.get_initial_relations()
    
    total_entities = sum(len(e) for e in entities.values())
    print(f"   实体总数: {total_entities}")
    for entity_type, entity_list in entities.items():
        print(f"      - {entity_type.value}: {len(entity_list)}")
    print(f"   关系总数: {len(relations)}")
    
    print("\n" + "=" * 70)
    print("✅ 本体设计演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo_ontology()

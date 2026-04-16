# -*- coding: utf-8 -*-
"""
知识图谱扩展脚本

扩展农业知识图谱，增加更多实体和关系：
1. 更多病害类型和变种
2. 更多环境因素
3. 更多防治措施
4. 地理区域信息
5. 抗病品种信息

使用方法:
    python expand_knowledge_graph.py --output_dir ./checkpoints/knowledge_graph
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def load_existing_kg(base_path: str) -> tuple:
    """
    加载现有知识图谱
    
    Args:
        base_path: 知识图谱基础路径
    
    Returns:
        (实体字典, 关系列表) 元组
    """
    entities_path = Path(base_path) / "entities.json"
    triples_path = Path(base_path) / "triples.json"
    
    with open(entities_path, 'r', encoding='utf-8') as f:
        entities = json.load(f)
    
    with open(triples_path, 'r', encoding='utf-8') as f:
        triples = json.load(f)
    
    return entities, triples


def get_new_entities() -> Dict[str, Dict]:
    """
    获取新增实体定义
    
    Returns:
        新增实体字典
    """
    return {
        "disease_barley_yellow_dwarf": {
            "id": "disease_barley_yellow_dwarf",
            "name": "大麦黄矮病",
            "type": "Disease",
            "properties": {
                "chinese_name": "大麦黄矮病",
                "english_name": "Barley Yellow Dwarf",
                "scientific_name": "BYDV",
                "severity_levels": ["轻度", "中度", "重度"],
                "high_risk_period": "秋季",
                "transmission": "蚜虫传播"
            }
        },
        "disease_wheat_spindle_streak": {
            "id": "disease_wheat_spindle_streak",
            "name": "小麦梭条斑花叶病",
            "type": "Disease",
            "properties": {
                "chinese_name": "小麦梭条斑花叶病",
                "english_name": "Wheat Spindle Streak Mosaic",
                "scientific_name": "WSSMV",
                "severity_levels": ["轻度", "中度", "重度"],
                "high_risk_period": "春季",
                "transmission": "土壤传播"
            }
        },
        "disease_take_all": {
            "id": "disease_take_all",
            "name": "全蚀病",
            "type": "Disease",
            "properties": {
                "chinese_name": "全蚀病",
                "english_name": "Take-all",
                "scientific_name": "Gaeumannomyces graminis",
                "severity_levels": ["轻度", "中度", "重度"],
                "high_risk_period": "灌浆期"
            }
        },
        "disease_eyespot": {
            "id": "disease_eyespot",
            "name": "眼斑病",
            "type": "Disease",
            "properties": {
                "chinese_name": "眼斑病",
                "english_name": "Eyespot",
                "scientific_name": "Oculimacula yallundae",
                "severity_levels": ["轻度", "中度", "重度"],
                "high_risk_period": "冬春季"
            }
        },
        "disease_snow_mold": {
            "id": "disease_snow_mold",
            "name": "雪霉病",
            "type": "Disease",
            "properties": {
                "chinese_name": "雪霉病",
                "english_name": "Snow Mold",
                "scientific_name": "Microdochium nivale",
                "severity_levels": ["轻度", "中度", "重度"],
                "high_risk_period": "融雪期"
            }
        },
        "pest_wheat_midge": {
            "id": "pest_wheat_midge",
            "name": "麦红吸浆虫",
            "type": "Pest",
            "properties": {
                "chinese_name": "麦红吸浆虫",
                "english_name": "Wheat Midge",
                "scientific_name": "Sitodiplosis mosellana",
                "damage_type": "吸汁性",
                "high_risk_period": "抽穗期"
            }
        },
        "pest_wireworm": {
            "id": "pest_wireworm",
            "name": "金针虫",
            "type": "Pest",
            "properties": {
                "chinese_name": "金针虫",
                "english_name": "Wireworm",
                "scientific_name": "Agriotes spp.",
                "damage_type": "地下害虫",
                "high_risk_period": "苗期"
            }
        },
        "pest_cutworm": {
            "id": "pest_cutworm",
            "name": "地老虎",
            "type": "Pest",
            "properties": {
                "chinese_name": "地老虎",
                "english_name": "Cutworm",
                "scientific_name": "Agrotis spp.",
                "damage_type": "地下害虫",
                "high_risk_period": "苗期"
            }
        },
        "pest_armyworm": {
            "id": "pest_armyworm",
            "name": "粘虫",
            "type": "Pest",
            "properties": {
                "chinese_name": "粘虫",
                "english_name": "Armyworm",
                "scientific_name": "Mythimna separata",
                "damage_type": "食叶性",
                "high_risk_period": "夏秋季"
            }
        },
        "symptom_yellow_dwarf": {
            "id": "symptom_yellow_dwarf",
            "name": "黄化矮缩",
            "type": "Symptom",
            "properties": {
                "description": "植株矮化，叶片黄化",
                "related_disease": "大麦黄矮病"
            }
        },
        "symptom_mosaic": {
            "id": "symptom_mosaic",
            "name": "花叶症状",
            "type": "Symptom",
            "properties": {
                "description": "叶片出现黄绿相间花叶",
                "related_disease": "小麦梭条斑花叶病"
            }
        },
        "symptom_whitehead": {
            "id": "symptom_whitehead",
            "name": "白穗",
            "type": "Symptom",
            "properties": {
                "description": "植株提前枯死，穗部变白",
                "related_disease": "全蚀病"
            }
        },
        "symptom_eye_lesion": {
            "id": "symptom_eye_lesion",
            "name": "眼状病斑",
            "type": "Symptom",
            "properties": {
                "description": "茎基部出现眼状病斑",
                "related_disease": "眼斑病"
            }
        },
        "symptom_pink_mold": {
            "id": "symptom_pink_mold",
            "name": "粉红色霉层",
            "type": "Symptom",
            "properties": {
                "description": "叶鞘和叶片出现粉红色霉层",
                "related_disease": "雪霉病"
            }
        },
        "symptom_shriveled_grain": {
            "id": "symptom_shriveled_grain",
            "name": "籽粒干瘪",
            "type": "Symptom",
            "properties": {
                "description": "籽粒发育不良，干瘪不饱满",
                "related_pest": "麦红吸浆虫"
            }
        },
        "symptom_seedling_death": {
            "id": "symptom_seedling_death",
            "name": "幼苗枯死",
            "type": "Symptom",
            "properties": {
                "description": "幼苗根部受害，枯萎死亡",
                "related_pest": "金针虫"
            }
        },
        "symptom_cut_stem": {
            "id": "symptom_cut_stem",
            "name": "茎秆切断",
            "type": "Symptom",
            "properties": {
                "description": "幼苗茎部被咬断",
                "related_pest": "地老虎"
            }
        },
        "symptom_leaf_defoliation": {
            "id": "symptom_leaf_defoliation",
            "name": "叶片被食",
            "type": "Symptom",
            "properties": {
                "description": "叶片被大量啃食",
                "related_pest": "粘虫"
            }
        },
        "pathogen_bydv": {
            "id": "pathogen_bydv",
            "name": "大麦黄矮病毒",
            "type": "Pathogen",
            "properties": {
                "scientific_name": "Barley Yellow Dwarf Virus",
                "type": "病毒",
                "spread_method": "蚜虫传播"
            }
        },
        "pathogen_wssmv": {
            "id": "pathogen_wssmv",
            "name": "小麦梭条斑花叶病毒",
            "type": "Pathogen",
            "properties": {
                "scientific_name": "Wheat Spindle Streak Mosaic Virus",
                "type": "病毒",
                "spread_method": "土壤传播"
            }
        },
        "pathogen_gaeumannomyces": {
            "id": "pathogen_gaeumannomyces",
            "name": "禾顶囊壳菌",
            "type": "Pathogen",
            "properties": {
                "scientific_name": "Gaeumannomyces graminis",
                "type": "真菌",
                "spread_method": "土壤传播"
            }
        },
        "pathogen_oculimacula": {
            "id": "pathogen_oculimacula",
            "name": "眼斑病菌",
            "type": "Pathogen",
            "properties": {
                "scientific_name": "Oculimacula yallundae",
                "type": "真菌",
                "spread_method": "残茬传播"
            }
        },
        "pathogen_microdochium": {
            "id": "pathogen_microdochium",
            "name": "雪腐病菌",
            "type": "Pathogen",
            "properties": {
                "scientific_name": "Microdochium nivale",
                "type": "真菌",
                "spread_method": "土壤传播"
            }
        },
        "env_cold_wet": {
            "id": "env_cold_wet",
            "name": "低温高湿",
            "type": "Environment",
            "properties": {
                "condition": "温度<10°C，湿度>85%",
                "favorable_for": ["雪霉病", "眼斑病"]
            }
        },
        "env_snow_cover": {
            "id": "env_snow_cover",
            "name": "积雪覆盖",
            "type": "Environment",
            "properties": {
                "condition": "长期积雪覆盖",
                "favorable_for": ["雪霉病"]
            }
        },
        "env_acidic_soil": {
            "id": "env_acidic_soil",
            "name": "酸性土壤",
            "type": "Environment",
            "properties": {
                "condition": "pH<6.0",
                "favorable_for": ["全蚀病"]
            }
        },
        "env_poor_drainage": {
            "id": "env_poor_drainage",
            "name": "排水不良",
            "type": "Environment",
            "properties": {
                "condition": "田间积水",
                "favorable_for": ["根腐病", "全蚀病"]
            }
        },
        "control_pyrethroid": {
            "id": "control_pyrethroid",
            "name": "拟除虫菊酯",
            "type": "ControlMeasure",
            "properties": {
                "type": "化学防治",
                "trade_name": "高效氯氰菊酯",
                "target_pests": ["蚜虫", "粘虫"],
                "application_rate": "每亩20-30毫升"
            }
        },
        "control_chlorpyrifos": {
            "id": "control_chlorpyrifos",
            "name": "毒死蜱",
            "type": "ControlMeasure",
            "properties": {
                "type": "化学防治",
                "trade_name": "毒死蜱",
                "target_pests": ["金针虫", "地老虎"],
                "application_rate": "每亩200-300毫升灌根"
            }
        },
        "control_flutriafol": {
            "id": "control_flutriafol",
            "name": "粉唑醇",
            "type": "ControlMeasure",
            "properties": {
                "type": "化学防治",
                "trade_name": "粉唑醇",
                "target_diseases": ["条锈病", "白粉病"],
                "application_rate": "每亩25-30毫升"
            }
        },
        "control_azoxystrobin": {
            "id": "control_azoxystrobin",
            "name": "嘧菌酯",
            "type": "ControlMeasure",
            "properties": {
                "type": "化学防治",
                "trade_name": "阿米西达",
                "target_diseases": ["条锈病", "叶锈病", "叶斑病"],
                "application_rate": "每亩60-80毫升"
            }
        },
        "control_phosphite": {
            "id": "control_phosphite",
            "name": "亚磷酸盐",
            "type": "ControlMeasure",
            "properties": {
                "type": "生物防治",
                "trade_name": "亚磷酸钾",
                "target_diseases": ["全蚀病", "根腐病"],
                "application_rate": "叶面喷施或灌根"
            }
        },
        "variety_zhengmai": {
            "id": "variety_zhengmai",
            "name": "郑麦系列",
            "type": "Variety",
            "properties": {
                "resistance": ["条锈病", "叶锈病"],
                "region": "黄淮麦区",
                "type": "冬小麦"
            }
        },
        "variety_jimai": {
            "id": "variety_jimai",
            "name": "济麦系列",
            "type": "Variety",
            "properties": {
                "resistance": ["白粉病", "赤霉病"],
                "region": "黄淮麦区",
                "type": "冬小麦"
            }
        },
        "variety_chuanmai": {
            "id": "variety_chuanmai",
            "name": "川麦系列",
            "type": "Variety",
            "properties": {
                "resistance": ["条锈病"],
                "region": "西南麦区",
                "type": "冬小麦"
            }
        },
        "variety_longchun": {
            "id": "variety_longchun",
            "name": "龙春系列",
            "type": "Variety",
            "properties": {
                "resistance": ["赤霉病"],
                "region": "东北麦区",
                "type": "春小麦"
            }
        },
        "region_huanghuai": {
            "id": "region_huanghuai",
            "name": "黄淮麦区",
            "type": "Region",
            "properties": {
                "provinces": ["河南", "山东", "河北", "江苏", "安徽"],
                "climate": "温带季风气候",
                "main_varieties": ["郑麦", "济麦"]
            }
        },
        "region_southwest": {
            "id": "region_southwest",
            "name": "西南麦区",
            "type": "Region",
            "properties": {
                "provinces": ["四川", "云南", "贵州", "重庆"],
                "climate": "亚热带季风气候",
                "main_varieties": ["川麦"]
            }
        },
        "region_northeast": {
            "id": "region_northeast",
            "name": "东北麦区",
            "type": "Region",
            "properties": {
                "provinces": ["黑龙江", "吉林", "辽宁"],
                "climate": "温带大陆性气候",
                "main_varieties": ["龙春"]
            }
        },
        "region_northwest": {
            "id": "region_northwest",
            "name": "西北麦区",
            "type": "Region",
            "properties": {
                "provinces": ["陕西", "甘肃", "宁夏", "新疆"],
                "climate": "温带大陆性气候",
                "main_varieties": ["西农"]
            }
        },
        "part_seed": {
            "id": "part_seed",
            "name": "种子",
            "type": "CropPart",
            "properties": {
                "description": "小麦种子，繁殖器官",
                "susceptible_to": ["黑粉病", "赤霉病"]
            }
        },
        "stage_overwintering": {
            "id": "stage_overwintering",
            "name": "越冬期",
            "type": "GrowthStage",
            "properties": {
                "description": "冬季休眠期",
                "risk_diseases": ["雪霉病"]
            }
        },
        "stage_maturity": {
            "id": "stage_maturity",
            "name": "成熟期",
            "type": "GrowthStage",
            "properties": {
                "description": "籽粒成熟期",
                "risk_diseases": ["赤霉病", "黑粉病"]
            }
        }
    }


def get_new_triples() -> List[Dict]:
    """
    获取新增关系定义
    
    Returns:
        新增关系列表
    """
    return [
        {"head": "disease_barley_yellow_dwarf", "relation": "HAS_SYMPTOM", "tail": "symptom_yellow_dwarf"},
        {"head": "disease_barley_yellow_dwarf", "relation": "CAUSED_BY", "tail": "pathogen_bydv"},
        {"head": "disease_barley_yellow_dwarf", "relation": "INFECTS", "tail": "crop_wheat"},
        {"head": "disease_barley_yellow_dwarf", "relation": "OCCURS_AT", "tail": "part_leaf"},
        {"head": "disease_barley_yellow_dwarf", "relation": "DURING", "tail": "stage_filling"},
        
        {"head": "disease_wheat_spindle_streak", "relation": "HAS_SYMPTOM", "tail": "symptom_mosaic"},
        {"head": "disease_wheat_spindle_streak", "relation": "CAUSED_BY", "tail": "pathogen_wssmv"},
        {"head": "disease_wheat_spindle_streak", "relation": "INFECTS", "tail": "crop_wheat"},
        {"head": "disease_wheat_spindle_streak", "relation": "OCCURS_AT", "tail": "part_leaf"},
        
        {"head": "disease_take_all", "relation": "HAS_SYMPTOM", "tail": "symptom_whitehead"},
        {"head": "disease_take_all", "relation": "CAUSED_BY", "tail": "pathogen_gaeumannomyces"},
        {"head": "disease_take_all", "relation": "INFECTS", "tail": "crop_wheat"},
        {"head": "disease_take_all", "relation": "OCCURS_AT", "tail": "part_root"},
        {"head": "disease_take_all", "relation": "DURING", "tail": "stage_filling"},
        
        {"head": "disease_eyespot", "relation": "HAS_SYMPTOM", "tail": "symptom_eye_lesion"},
        {"head": "disease_eyespot", "relation": "CAUSED_BY", "tail": "pathogen_oculimacula"},
        {"head": "disease_eyespot", "relation": "INFECTS", "tail": "crop_wheat"},
        {"head": "disease_eyespot", "relation": "OCCURS_AT", "tail": "part_stem"},
        
        {"head": "disease_snow_mold", "relation": "HAS_SYMPTOM", "tail": "symptom_pink_mold"},
        {"head": "disease_snow_mold", "relation": "CAUSED_BY", "tail": "pathogen_microdochium"},
        {"head": "disease_snow_mold", "relation": "INFECTS", "tail": "crop_wheat"},
        {"head": "disease_snow_mold", "relation": "OCCURS_AT", "tail": "part_leaf"},
        {"head": "disease_snow_mold", "relation": "DURING", "tail": "stage_overwintering"},
        
        {"head": "pest_wheat_midge", "relation": "HAS_SYMPTOM", "tail": "symptom_shriveled_grain"},
        {"head": "pest_wheat_midge", "relation": "INFECTS", "tail": "crop_wheat"},
        {"head": "pest_wheat_midge", "relation": "OCCURS_AT", "tail": "part_head"},
        {"head": "pest_wheat_midge", "relation": "DURING", "tail": "stage_heading"},
        
        {"head": "pest_wireworm", "relation": "HAS_SYMPTOM", "tail": "symptom_seedling_death"},
        {"head": "pest_wireworm", "relation": "INFECTS", "tail": "crop_wheat"},
        {"head": "pest_wireworm", "relation": "OCCURS_AT", "tail": "part_root"},
        {"head": "pest_wireworm", "relation": "DURING", "tail": "stage_seedling"},
        
        {"head": "pest_cutworm", "relation": "HAS_SYMPTOM", "tail": "symptom_cut_stem"},
        {"head": "pest_cutworm", "relation": "INFECTS", "tail": "crop_wheat"},
        {"head": "pest_cutworm", "relation": "OCCURS_AT", "tail": "part_stem"},
        {"head": "pest_cutworm", "relation": "DURING", "tail": "stage_seedling"},
        
        {"head": "pest_armyworm", "relation": "HAS_SYMPTOM", "tail": "symptom_leaf_defoliation"},
        {"head": "pest_armyworm", "relation": "INFECTS", "tail": "crop_wheat"},
        {"head": "pest_armyworm", "relation": "OCCURS_AT", "tail": "part_leaf"},
        
        {"head": "pathogen_bydv", "relation": "FAVORS", "tail": "env_warm_temp"},
        {"head": "pathogen_gaeumannomyces", "relation": "FAVORS", "tail": "env_acidic_soil"},
        {"head": "pathogen_gaeumannomyces", "relation": "FAVORS", "tail": "env_poor_drainage"},
        {"head": "pathogen_microdochium", "relation": "FAVORS", "tail": "env_cold_wet"},
        {"head": "pathogen_microdochium", "relation": "FAVORS", "tail": "env_snow_cover"},
        
        {"head": "control_pyrethroid", "relation": "TARGETS", "tail": "pest_aphid"},
        {"head": "control_pyrethroid", "relation": "TARGETS", "tail": "pest_armyworm"},
        {"head": "control_chlorpyrifos", "relation": "TARGETS", "tail": "pest_wireworm"},
        {"head": "control_chlorpyrifos", "relation": "TARGETS", "tail": "pest_cutworm"},
        {"head": "control_flutriafol", "relation": "TARGETS", "tail": "disease_stripe_rust"},
        {"head": "control_flutriafol", "relation": "TARGETS", "tail": "disease_powdery_mildew"},
        {"head": "control_azoxystrobin", "relation": "TARGETS", "tail": "disease_stripe_rust"},
        {"head": "control_azoxystrobin", "relation": "TARGETS", "tail": "disease_leaf_rust"},
        {"head": "control_phosphite", "relation": "TARGETS", "tail": "disease_take_all"},
        
        {"head": "variety_zhengmai", "relation": "RESISTANT_TO", "tail": "disease_stripe_rust"},
        {"head": "variety_zhengmai", "relation": "RESISTANT_TO", "tail": "disease_leaf_rust"},
        {"head": "variety_zhengmai", "relation": "GROWN_IN", "tail": "region_huanghuai"},
        
        {"head": "variety_jimai", "relation": "RESISTANT_TO", "tail": "disease_powdery_mildew"},
        {"head": "variety_jimai", "relation": "RESISTANT_TO", "tail": "disease_fusarium_head_blight"},
        {"head": "variety_jimai", "relation": "GROWN_IN", "tail": "region_huanghuai"},
        
        {"head": "variety_chuanmai", "relation": "RESISTANT_TO", "tail": "disease_stripe_rust"},
        {"head": "variety_chuanmai", "relation": "GROWN_IN", "tail": "region_southwest"},
        
        {"head": "variety_longchun", "relation": "RESISTANT_TO", "tail": "disease_fusarium_head_blight"},
        {"head": "variety_longchun", "relation": "GROWN_IN", "tail": "region_northeast"},
        
        {"head": "disease_stripe_rust", "relation": "PREVALENT_IN", "tail": "region_southwest"},
        {"head": "disease_stripe_rust", "relation": "PREVALENT_IN", "tail": "region_northwest"},
        {"head": "disease_fusarium_head_blight", "relation": "PREVALENT_IN", "tail": "region_huanghuai"},
        {"head": "disease_fusarium_head_blight", "relation": "PREVALENT_IN", "tail": "region_northeast"},
        {"head": "disease_snow_mold", "relation": "PREVALENT_IN", "tail": "region_northeast"},
        
        {"head": "pest_aphid", "relation": "DURING", "tail": "stage_filling"},
        {"head": "pest_aphid", "relation": "VECTOR_FOR", "tail": "disease_barley_yellow_dwarf"},
        
        {"head": "control_resistant_variety", "relation": "PREVENTS", "tail": "disease_take_all"},
        {"head": "control_crop_rotation", "relation": "PREVENTS", "tail": "disease_take_all"},
        {"head": "control_crop_rotation", "relation": "PREVENTS", "tail": "disease_eyespot"},
        
        {"head": "disease_barley_yellow_dwarf", "relation": "HAS_SEVERITY", "tail": "severity_mild"},
        {"head": "disease_barley_yellow_dwarf", "relation": "HAS_SEVERITY", "tail": "severity_moderate"},
        {"head": "disease_barley_yellow_dwarf", "relation": "HAS_SEVERITY", "tail": "severity_severe"},
        
        {"head": "disease_take_all", "relation": "HAS_SEVERITY", "tail": "severity_mild"},
        {"head": "disease_take_all", "relation": "HAS_SEVERITY", "tail": "severity_moderate"},
        {"head": "disease_take_all", "relation": "HAS_SEVERITY", "tail": "severity_severe"},
    ]


def expand_knowledge_graph(base_path: str, output_path: str = None) -> Dict:
    """
    扩展知识图谱
    
    Args:
        base_path: 现有知识图谱路径
        output_path: 输出路径，默认覆盖原路径
    
    Returns:
        扩展统计信息
    """
    if output_path is None:
        output_path = base_path
    
    entities, triples = load_existing_kg(base_path)
    
    original_entity_count = len(entities)
    original_triple_count = len(triples)
    
    new_entities = get_new_entities()
    new_triples = get_new_triples()
    
    entities.update(new_entities)
    triples.extend(new_triples)
    
    os.makedirs(output_path, exist_ok=True)
    
    with open(Path(output_path) / "entities.json", 'w', encoding='utf-8') as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    
    with open(Path(output_path) / "triples.json", 'w', encoding='utf-8') as f:
        json.dump(triples, f, indent=2, ensure_ascii=False)
    
    stats = {
        "original_entities": original_entity_count,
        "original_triples": original_triple_count,
        "new_entities": len(new_entities),
        "new_triples": len(new_triples),
        "total_entities": len(entities),
        "total_triples": len(triples),
        "entity_types": {},
        "relation_types": {},
        "updated_at": datetime.now().isoformat()
    }
    
    for entity in entities.values():
        entity_type = entity.get("type", "Unknown")
        stats["entity_types"][entity_type] = stats["entity_types"].get(entity_type, 0) + 1
    
    for triple in triples:
        relation = triple.get("relation", "Unknown")
        stats["relation_types"][relation] = stats["relation_types"].get(relation, 0) + 1
    
    with open(Path(output_path) / "kg_stats.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    return stats


def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="扩展农业知识图谱")
    parser.add_argument("--base_path", type=str, 
                        default="./checkpoints/knowledge_graph",
                        help="现有知识图谱路径")
    parser.add_argument("--output_path", type=str, default=None,
                        help="输出路径，默认覆盖原路径")
    args = parser.parse_args()
    
    print("=" * 70)
    print("📊 知识图谱扩展")
    print("=" * 70)
    
    stats = expand_knowledge_graph(args.base_path, args.output_path)
    
    print(f"\n📈 扩展统计:")
    print(f"   原有实体: {stats['original_entities']} → {stats['total_entities']} (+{stats['new_entities']})")
    print(f"   原有关系: {stats['original_triples']} → {stats['total_triples']} (+{stats['new_triples']})")
    
    print(f"\n📊 实体类型分布:")
    for entity_type, count in sorted(stats['entity_types'].items()):
        print(f"   {entity_type}: {count}")
    
    print(f"\n📊 关系类型分布:")
    for relation_type, count in sorted(stats['relation_types'].items(), key=lambda x: -x[1])[:10]:
        print(f"   {relation_type}: {count}")
    
    print(f"\n✅ 知识图谱扩展完成!")


if __name__ == "__main__":
    main()

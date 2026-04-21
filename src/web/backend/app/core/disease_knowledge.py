"""
病害分类知识库

提供病害的中英文名称、分类、防治建议和用药指导
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class DiseaseCategory(Enum):
    """病害分类枚举"""
    FUNGAL = "fungal"  # 真菌性病害
    BACTERIAL = "bacterial"  # 细菌性病害
    VIRAL = "viral"  # 病毒性病害
    PEST = "pest"  # 虫害
    NUTRITIONAL = "nutritional"  # 营养性病害
    HEALTHY = "healthy"  # 健康


@dataclass
class DiseaseInfo:
    """病害信息数据类"""
    name_en: str  # 英文名称
    name_cn: str  # 中文名称
    category: DiseaseCategory  # 病害分类
    description: str  # 病害描述
    symptoms: List[str]  # 症状特征
    causes: List[str]  # 发病原因
    prevention: List[str]  # 预防措施
    treatment: List[str]  # 治疗方法
    medicines: List[Dict[str, Any]]  # 推荐药物
    severity: str  # 严重程度 (low, medium, high)


DISEASE_KNOWLEDGE_BASE: Dict[str, DiseaseInfo] = {
    "Aphid": DiseaseInfo(
        name_en="Aphid",
        name_cn="蚜虫",
        category=DiseaseCategory.PEST,
        description="蚜虫是小麦常见的刺吸式害虫，通过吸食植物汁液造成危害",
        symptoms=[
            "叶片出现黄绿色斑点",
            "叶片卷曲变形",
            "植株生长受阻",
            "叶片表面有粘液（蜜露）",
            "严重时整株枯萎"
        ],
        causes=[
            "温暖干燥的气候条件",
            "田间杂草过多",
            "天敌数量减少",
            "连作种植"
        ],
        prevention=[
            "清除田间杂草，减少虫源",
            "保护利用天敌（如瓢虫、草蛉）",
            "合理轮作倒茬",
            "种植抗虫品种"
        ],
        treatment=[
            "发现蚜虫时及时喷药防治",
            "重点喷洒叶片背面和心叶",
            "严重时隔7-10天再喷一次"
        ],
        medicines=[
            {
                "name": "吡虫啉",
                "name_en": "Imidacloprid",
                "concentration": "10% 可湿性粉剂",
                "dosage": "1500-2000倍液",
                "method": "叶面喷雾",
                "frequency": "每7-10天一次",
                "safety_period": "收获前14天停止使用"
            },
            {
                "name": "啶虫脒",
                "name_en": "Acetamiprid",
                "concentration": "20% 可溶性粉剂",
                "dosage": "3000-4000倍液",
                "method": "叶面喷雾",
                "frequency": "每7-10天一次",
                "safety_period": "收获前7天停止使用"
            },
            {
                "name": "抗蚜威",
                "name_en": "Pirimicarb",
                "concentration": "50% 可湿性粉剂",
                "dosage": "2000-3000倍液",
                "method": "叶面喷雾",
                "frequency": "每7天一次",
                "safety_period": "收获前7天停止使用"
            }
        ],
        severity="medium"
    ),

    "Black Rust": DiseaseInfo(
        name_en="Black Rust",
        name_cn="秆锈病",
        category=DiseaseCategory.FUNGAL,
        description="秆锈病是由禾柄锈菌引起的小麦真菌性病害，主要危害茎秆和叶鞘",
        symptoms=[
            "茎秆和叶鞘出现红褐色夏孢子堆",
            "孢子堆较大，椭圆形或长条形",
            "后期出现黑色冬孢子堆",
            "严重时植株早枯",
            "籽粒秕瘦"
        ],
        causes=[
            "温暖多雨的气候条件",
            "品种抗病性差",
            "田间病残体多",
            "氮肥施用过多"
        ],
        prevention=[
            "种植抗病品种",
            "清除田间病残体",
            "合理密植，增强通风透光",
            "避免过量施用氮肥"
        ],
        treatment=[
            "发病初期及时喷药防治",
            "重点喷洒茎秆和叶鞘部位",
            "严重时隔7-10天再喷一次"
        ],
        medicines=[
            {
                "name": "三唑酮",
                "name_en": "Triadimefon",
                "concentration": "15% 可湿性粉剂",
                "dosage": "1000-1500倍液",
                "method": "叶面喷雾",
                "frequency": "每7-10天一次",
                "safety_period": "收获前21天停止使用"
            },
            {
                "name": "丙环唑",
                "name_en": "Propiconazole",
                "concentration": "25% 乳油",
                "dosage": "2000-3000倍液",
                "method": "叶面喷雾",
                "frequency": "每10-14天一次",
                "safety_period": "收获前28天停止使用"
            },
            {
                "name": "戊唑醇",
                "name_en": "Tebuconazole",
                "concentration": "43% 悬浮剂",
                "dosage": "3000-4000倍液",
                "method": "叶面喷雾",
                "frequency": "每10-14天一次",
                "safety_period": "收获前21天停止使用"
            }
        ],
        severity="high"
    ),

    "Blast": DiseaseInfo(
        name_en="Blast",
        name_cn="稻瘟病",
        category=DiseaseCategory.FUNGAL,
        description="稻瘟病是由稻瘟病菌引起的主要病害，可侵染叶片、节、穗等部位",
        symptoms=[
            "叶片出现纺锤形褐色病斑",
            "病斑中央灰白色，边缘褐色",
            "穗颈变黑腐烂",
            "谷粒变黑",
            "严重时全株枯死"
        ],
        causes=[
            "阴雨连绵的气候条件",
            "氮肥施用过多",
            "品种抗病性差",
            "田间菌源丰富"
        ],
        prevention=[
            "种植抗病品种",
            "合理施肥，避免偏施氮肥",
            "及时处理病稻草",
            "种子消毒处理"
        ],
        treatment=[
            "发病初期及时喷药防治",
            "穗期重点保护穗颈",
            "雨后及时补喷"
        ],
        medicines=[
            {
                "name": "稻瘟灵",
                "name_en": "Isoprothiolane",
                "concentration": "40% 乳油",
                "dosage": "1000倍液",
                "method": "叶面喷雾",
                "frequency": "每7天一次",
                "safety_period": "收获前14天停止使用"
            },
            {
                "name": "三环唑",
                "name_en": "Tricyclazole",
                "concentration": "75% 可湿性粉剂",
                "dosage": "2000-3000倍液",
                "method": "叶面喷雾",
                "frequency": "每7-10天一次",
                "safety_period": "收获前21天停止使用"
            },
            {
                "name": "春雷霉素",
                "name_en": "Kasugamycin",
                "concentration": "2% 液剂",
                "dosage": "500-600倍液",
                "method": "叶面喷雾",
                "frequency": "每5-7天一次",
                "safety_period": "收获前7天停止使用"
            }
        ],
        severity="high"
    ),

    "Brown Rust": DiseaseInfo(
        name_en="Brown Rust",
        name_cn="叶锈病",
        category=DiseaseCategory.FUNGAL,
        description="叶锈病是由小麦叶锈菌引起的真菌性病害，主要危害叶片",
        symptoms=[
            "叶片出现橙褐色夏孢子堆",
            "孢子堆较小，圆形或椭圆形",
            "叶片表皮破裂散出粉末",
            "严重时叶片枯黄",
            "影响光合作用"
        ],
        causes=[
            "温暖湿润的气候条件",
            "品种抗病性差",
            "田间病残体多",
            "种植密度过大"
        ],
        prevention=[
            "种植抗病品种",
            "清除田间病残体",
            "合理密植",
            "增施磷钾肥"
        ],
        treatment=[
            "发病初期及时喷药防治",
            "重点喷洒叶片正面",
            "严重时隔7-10天再喷一次"
        ],
        medicines=[
            {
                "name": "三唑酮",
                "name_en": "Triadimefon",
                "concentration": "15% 可湿性粉剂",
                "dosage": "1000-1500倍液",
                "method": "叶面喷雾",
                "frequency": "每7-10天一次",
                "safety_period": "收获前21天停止使用"
            },
            {
                "name": "烯唑醇",
                "name_en": "Diniconazole",
                "concentration": "12.5% 可湿性粉剂",
                "dosage": "2000-3000倍液",
                "method": "叶面喷雾",
                "frequency": "每10-14天一次",
                "safety_period": "收获前21天停止使用"
            }
        ],
        severity="medium"
    ),

    "Common Root Rot": DiseaseInfo(
        name_en="Common Root Rot",
        name_cn="根腐病",
        category=DiseaseCategory.FUNGAL,
        description="根腐病是由多种真菌引起的土传病害，危害小麦根系",
        symptoms=[
            "根部变褐腐烂",
            "植株矮小发黄",
            "分蘖减少",
            "叶片从下向上枯黄",
            "严重时全株死亡"
        ],
        causes=[
            "土壤湿度过大",
            "排水不良",
            "连作种植",
            "种子带菌"
        ],
        prevention=[
            "合理轮作倒茬",
            "种子消毒处理",
            "改善排水条件",
            "增施有机肥"
        ],
        treatment=[
            "发病初期用药剂灌根",
            "控制浇水，降低土壤湿度",
            "增施磷钾肥增强抗病力"
        ],
        medicines=[
            {
                "name": "多菌灵",
                "name_en": "Carbendazim",
                "concentration": "50% 可湿性粉剂",
                "dosage": "500倍液",
                "method": "灌根",
                "frequency": "每7天一次",
                "safety_period": "收获前14天停止使用"
            },
            {
                "name": "甲霜灵",
                "name_en": "Metalaxyl",
                "concentration": "25% 可湿性粉剂",
                "dosage": "800-1000倍液",
                "method": "灌根",
                "frequency": "每7-10天一次",
                "safety_period": "收获前14天停止使用"
            }
        ],
        severity="high"
    ),

    "Fusarium Head Blight": DiseaseInfo(
        name_en="Fusarium Head Blight",
        name_cn="赤霉病",
        category=DiseaseCategory.FUNGAL,
        description="赤霉病是由禾谷镰刀菌引起的真菌性病害，主要危害穗部",
        symptoms=[
            "穗部出现粉红色霉层",
            "小穗枯黄变白",
            "籽粒秕瘦",
            "籽粒含毒素",
            "严重影响产量和品质"
        ],
        causes=[
            "抽穗扬花期遇阴雨",
            "田间病残体多",
            "品种抗病性差",
            "施氮过多"
        ],
        prevention=[
            "种植抗病品种",
            "清除田间病残体",
            "合理施肥",
            "适期播种避开雨季"
        ],
        treatment=[
            "抽穗扬花期是防治关键期",
            "遇阴雨天气及时喷药",
            "重点保护穗部"
        ],
        medicines=[
            {
                "name": "多菌灵",
                "name_en": "Carbendazim",
                "concentration": "50% 可湿性粉剂",
                "dosage": "500-800倍液",
                "method": "穗部喷雾",
                "frequency": "扬花期喷1-2次",
                "safety_period": "收获前21天停止使用"
            },
            {
                "name": "戊唑醇",
                "name_en": "Tebuconazole",
                "concentration": "43% 悬浮剂",
                "dosage": "3000-4000倍液",
                "method": "穗部喷雾",
                "frequency": "扬花期喷1-2次",
                "safety_period": "收获前21天停止使用"
            },
            {
                "name": "氰烯菌酯",
                "name_en": "Phenamacril",
                "concentration": "25% 悬浮剂",
                "dosage": "1500-2000倍液",
                "method": "穗部喷雾",
                "frequency": "扬花期喷1-2次",
                "safety_period": "收获前14天停止使用"
            }
        ],
        severity="high"
    ),

    "Healthy": DiseaseInfo(
        name_en="Healthy",
        name_cn="健康",
        category=DiseaseCategory.HEALTHY,
        description="小麦生长健康，未发现明显病害症状",
        symptoms=[
            "叶片颜色正常",
            "生长健壮",
            "无病斑虫害"
        ],
        causes=[],
        prevention=[
            "继续保持良好的田间管理",
            "定期检查病虫害",
            "合理施肥灌溉"
        ],
        treatment=[
            "无需治疗，继续保持管理"
        ],
        medicines=[],
        severity="low"
    ),

    "Leaf Blight": DiseaseInfo(
        name_en="Leaf Blight",
        name_cn="叶枯病",
        category=DiseaseCategory.FUNGAL,
        description="叶枯病是由多种真菌引起的叶部病害",
        symptoms=[
            "叶片出现椭圆形褐色病斑",
            "病斑周围有黄色晕圈",
            "病斑可连成大斑",
            "叶片枯死",
            "严重时全株枯黄"
        ],
        causes=[
            "高温高湿条件",
            "田间病残体多",
            "品种抗病性差",
            "氮肥过多"
        ],
        prevention=[
            "种植抗病品种",
            "清除田间病残体",
            "合理施肥",
            "降低田间湿度"
        ],
        treatment=[
            "发病初期及时喷药",
            "重点保护功能叶",
            "严重时隔7-10天再喷一次"
        ],
        medicines=[
            {
                "name": "多菌灵",
                "name_en": "Carbendazim",
                "concentration": "50% 可湿性粉剂",
                "dosage": "500-800倍液",
                "method": "叶面喷雾",
                "frequency": "每7-10天一次",
                "safety_period": "收获前14天停止使用"
            },
            {
                "name": "代森锰锌",
                "name_en": "Mancozeb",
                "concentration": "70% 可湿性粉剂",
                "dosage": "600-800倍液",
                "method": "叶面喷雾",
                "frequency": "每7天一次",
                "safety_period": "收获前7天停止使用"
            }
        ],
        severity="medium"
    ),

    "Mildew": DiseaseInfo(
        name_en="Mildew",
        name_cn="白粉病",
        category=DiseaseCategory.FUNGAL,
        description="白粉病是由禾布氏白粉菌引起的真菌性病害，主要危害叶片和茎秆",
        symptoms=[
            "叶片表面出现白色粉状霉层",
            "后期霉层变为灰白色至浅褐色",
            "叶片褪绿变黄",
            "严重时叶片枯萎",
            "影响光合作用和产量"
        ],
        causes=[
            "温暖干燥的气候条件",
            "种植密度过大",
            "氮肥施用过多",
            "品种抗病性差"
        ],
        prevention=[
            "种植抗病品种",
            "合理密植，增强通风",
            "避免偏施氮肥",
            "清除田间病残体"
        ],
        treatment=[
            "发病初期及时喷药防治",
            "重点喷洒叶片正面",
            "严重时隔7-10天再喷一次"
        ],
        medicines=[
            {
                "name": "三唑酮",
                "name_en": "Triadimefon",
                "concentration": "15% 可湿性粉剂",
                "dosage": "1000-1500倍液",
                "method": "叶面喷雾",
                "frequency": "每7-10天一次",
                "safety_period": "收获前21天停止使用"
            },
            {
                "name": "腈菌唑",
                "name_en": "Myclobutanil",
                "concentration": "25% 乳油",
                "dosage": "3000-4000倍液",
                "method": "叶面喷雾",
                "frequency": "每10-14天一次",
                "safety_period": "收获前14天停止使用"
            },
            {
                "name": "丙环唑",
                "name_en": "Propiconazole",
                "concentration": "25% 乳油",
                "dosage": "2000-3000倍液",
                "method": "叶面喷雾",
                "frequency": "每10-14天一次",
                "safety_period": "收获前28天停止使用"
            }
        ],
        severity="medium"
    ),

    "Mite": DiseaseInfo(
        name_en="Mite",
        name_cn="螨虫",
        category=DiseaseCategory.PEST,
        description="螨虫是小麦常见的害虫，通过刺吸植物汁液造成危害",
        symptoms=[
            "叶片出现灰白色斑点",
            "叶片变黄枯萎",
            "植株矮小",
            "严重时整株枯死",
            "叶背面有丝网"
        ],
        causes=[
            "高温干燥气候",
            "田间杂草多",
            "天敌数量减少",
            "连作种植"
        ],
        prevention=[
            "清除田间杂草",
            "保护利用天敌",
            "合理轮作",
            "避免过度干旱"
        ],
        treatment=[
            "发现螨虫及时防治",
            "重点喷洒叶片背面",
            "严重时隔5-7天再喷一次"
        ],
        medicines=[
            {
                "name": "阿维菌素",
                "name_en": "Avermectin",
                "concentration": "1.8% 乳油",
                "dosage": "3000-4000倍液",
                "method": "叶面喷雾",
                "frequency": "每5-7天一次",
                "safety_period": "收获前7天停止使用"
            },
            {
                "name": "哒螨灵",
                "name_en": "Pyridaben",
                "concentration": "15% 乳油",
                "dosage": "2000-3000倍液",
                "method": "叶面喷雾",
                "frequency": "每7天一次",
                "safety_period": "收获前14天停止使用"
            }
        ],
        severity="medium"
    ),

    "Septoria": DiseaseInfo(
        name_en="Septoria",
        name_cn="壳针孢叶斑病",
        category=DiseaseCategory.FUNGAL,
        description="壳针孢叶斑病是由壳针孢菌引起的叶部病害",
        symptoms=[
            "叶片出现淡黄色小斑点",
            "斑点扩大成椭圆形病斑",
            "病斑中央灰白色",
            "病斑上有小黑点（分生孢子器）",
            "严重时叶片枯死"
        ],
        causes=[
            "温暖湿润气候",
            "田间病残体多",
            "品种抗病性差",
            "种植密度过大"
        ],
        prevention=[
            "种植抗病品种",
            "清除田间病残体",
            "合理密植",
            "增施磷钾肥"
        ],
        treatment=[
            "发病初期及时喷药",
            "重点保护功能叶",
            "严重时隔7-10天再喷一次"
        ],
        medicines=[
            {
                "name": "代森锰锌",
                "name_en": "Mancozeb",
                "concentration": "70% 可湿性粉剂",
                "dosage": "600-800倍液",
                "method": "叶面喷雾",
                "frequency": "每7天一次",
                "safety_period": "收获前7天停止使用"
            },
            {
                "name": "百菌清",
                "name_en": "Chlorothalonil",
                "concentration": "75% 可湿性粉剂",
                "dosage": "600-800倍液",
                "method": "叶面喷雾",
                "frequency": "每7-10天一次",
                "safety_period": "收获前7天停止使用"
            }
        ],
        severity="medium"
    ),

    "Smut": DiseaseInfo(
        name_en="Smut",
        name_cn="黑粉病",
        category=DiseaseCategory.FUNGAL,
        description="黑粉病是由黑粉菌引起的真菌性病害，主要危害穗部",
        symptoms=[
            "穗部变成黑粉包",
            "黑粉散落后只剩穗轴",
            "植株矮化",
            "分蘖增多",
            "严重影响产量"
        ],
        causes=[
            "种子带菌",
            "土壤带菌",
            "低温高湿条件",
            "品种抗病性差"
        ],
        prevention=[
            "种子消毒处理",
            "种植抗病品种",
            "轮作倒茬",
            "适期播种"
        ],
        treatment=[
            "发现病株及时拔除",
            "带出田外深埋或烧毁",
            "发病田块不宜留种"
        ],
        medicines=[
            {
                "name": "戊唑醇",
                "name_en": "Tebuconazole",
                "concentration": "2% 湿拌种剂",
                "dosage": "种子重量0.2-0.3%",
                "method": "拌种",
                "frequency": "播种前处理一次",
                "safety_period": "按说明使用"
            },
            {
                "name": "三唑酮",
                "name_en": "Triadimefon",
                "concentration": "15% 可湿性粉剂",
                "dosage": "种子重量0.2%",
                "method": "拌种",
                "frequency": "播种前处理一次",
                "safety_period": "按说明使用"
            }
        ],
        severity="high"
    ),

    "Stem fly": DiseaseInfo(
        name_en="Stem fly",
        name_cn="茎蝇",
        category=DiseaseCategory.PEST,
        description="茎蝇是小麦的主要害虫之一，幼虫蛀食茎秆造成危害",
        symptoms=[
            "植株矮小发黄",
            "茎秆内有虫道",
            "茎秆易折断",
            "白穗或瘪粒",
            "严重时全株枯死"
        ],
        causes=[
            "冬季温暖",
            "春季干旱",
            "连作种植",
            "天敌减少"
        ],
        prevention=[
            "深翻灭茬",
            "清除田间杂草",
            "保护利用天敌",
            "合理轮作"
        ],
        treatment=[
            "成虫期喷药防治",
            "幼虫孵化期是防治关键期",
            "重点喷洒茎基部"
        ],
        medicines=[
            {
                "name": "辛硫磷",
                "name_en": "Phoxim",
                "concentration": "50% 乳油",
                "dosage": "1000-1500倍液",
                "method": "喷雾或灌根",
                "frequency": "成虫期和幼虫期各喷一次",
                "safety_period": "收获前14天停止使用"
            },
            {
                "name": "毒死蜱",
                "name_en": "Chlorpyrifos",
                "concentration": "48% 乳油",
                "dosage": "1000-1500倍液",
                "method": "喷雾",
                "frequency": "成虫期喷一次",
                "safety_period": "收获前21天停止使用"
            }
        ],
        severity="high"
    ),

    "Tan spot": DiseaseInfo(
        name_en="Tan spot",
        name_cn="褐斑病",
        category=DiseaseCategory.FUNGAL,
        description="褐斑病是由德氏霉菌引起的叶部病害",
        symptoms=[
            "叶片出现淡褐色椭圆形病斑",
            "病斑周围有黄色晕圈",
            "病斑可愈合成大斑",
            "叶片枯黄",
            "严重时全株枯死"
        ],
        causes=[
            "温暖湿润条件",
            "田间病残体多",
            "品种抗病性差",
            "氮肥过多"
        ],
        prevention=[
            "种植抗病品种",
            "清除田间病残体",
            "合理施肥",
            "降低田间湿度"
        ],
        treatment=[
            "发病初期及时喷药",
            "重点保护功能叶",
            "严重时隔7-10天再喷一次"
        ],
        medicines=[
            {
                "name": "丙环唑",
                "name_en": "Propiconazole",
                "concentration": "25% 乳油",
                "dosage": "2000-3000倍液",
                "method": "叶面喷雾",
                "frequency": "每10-14天一次",
                "safety_period": "收获前28天停止使用"
            },
            {
                "name": "代森锰锌",
                "name_en": "Mancozeb",
                "concentration": "70% 可湿性粉剂",
                "dosage": "600-800倍液",
                "method": "叶面喷雾",
                "frequency": "每7天一次",
                "safety_period": "收获前7天停止使用"
            }
        ],
        severity="medium"
    ),

    "Yellow Rust": DiseaseInfo(
        name_en="Yellow Rust",
        name_cn="条锈病",
        category=DiseaseCategory.FUNGAL,
        description="条锈病是由条形柄锈菌引起的真菌性病害，是小麦最重要的病害之一",
        symptoms=[
            "叶片出现鲜黄色夏孢子堆",
            "孢子堆沿叶脉排列成条状",
            "后期出现黑色冬孢子堆",
            "叶片枯黄",
            "严重影响产量"
        ],
        causes=[
            "凉爽湿润的气候条件",
            "品种抗病性差",
            "田间菌源丰富",
            "种植密度过大"
        ],
        prevention=[
            "种植抗病品种",
            "清除田间病残体",
            "合理密植",
            "适期晚播"
        ],
        treatment=[
            "发病初期及时喷药防治",
            "重点保护功能叶",
            "严重时隔7-10天再喷一次"
        ],
        medicines=[
            {
                "name": "三唑酮",
                "name_en": "Triadimefon",
                "concentration": "15% 可湿性粉剂",
                "dosage": "1000-1500倍液",
                "method": "叶面喷雾",
                "frequency": "每7-10天一次",
                "safety_period": "收获前21天停止使用"
            },
            {
                "name": "戊唑醇",
                "name_en": "Tebuconazole",
                "concentration": "43% 悬浮剂",
                "dosage": "3000-4000倍液",
                "method": "叶面喷雾",
                "frequency": "每10-14天一次",
                "safety_period": "收获前21天停止使用"
            },
            {
                "name": "烯唑醇",
                "name_en": "Diniconazole",
                "concentration": "12.5% 可湿性粉剂",
                "dosage": "2000-3000倍液",
                "method": "叶面喷雾",
                "frequency": "每10-14天一次",
                "safety_period": "收获前21天停止使用"
            }
        ],
        severity="high"
    )
}


def get_disease_info(disease_name: str) -> Optional[DiseaseInfo]:
    """
    获取病害信息

    参数:
        disease_name: 病害名称（中文或英文）

    返回:
        DiseaseInfo 或 None
    """
    # 先尝试英文名称
    if disease_name in DISEASE_KNOWLEDGE_BASE:
        return DISEASE_KNOWLEDGE_BASE[disease_name]

    # 再尝试中文名称
    for info in DISEASE_KNOWLEDGE_BASE.values():
        if info.name_cn == disease_name:
            return info

    return None


def get_all_diseases() -> List[Dict[str, Any]]:
    """
    获取所有病害信息列表

    返回:
        病害信息列表
    """
    return [
        {
            "name_en": info.name_en,
            "name_cn": info.name_cn,
            "category": info.category.value,
            "severity": info.severity
        }
        for info in DISEASE_KNOWLEDGE_BASE.values()
    ]


def generate_recommendations(disease_name: str) -> Dict[str, Any]:
    """
    生成防治建议和用药指导

    参数:
        disease_name: 病害名称

    返回:
        包含防治建议和用药指导的字典
    """
    info = get_disease_info(disease_name)

    if not info:
        return {
            "disease_name": disease_name,
            "name_en": disease_name,
            "name_cn": disease_name,
            "prevention": ["未找到相关病害信息"],
            "treatment": [],
            "medicines": []
        }

    return {
        "disease_name": info.name_cn,
        "name_en": info.name_en,
        "name_cn": info.name_cn,
        "category": info.category.value,
        "description": info.description,
        "symptoms": info.symptoms,
        "causes": info.causes,
        "prevention": info.prevention,
        "treatment": info.treatment,
        "medicines": info.medicines,
        "severity": info.severity
    }

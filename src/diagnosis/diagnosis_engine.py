# -*- coding: utf-8 -*-
"""
IWDDA诊断引擎模块

基于多模态特征融合的小麦病害诊断智能体核心诊断流程
实现文档定义的诊断流程: 视觉感知 → 知识图谱检索 → 多模态融合 → 诊断报告生成
"""
import os
import sys
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class DiagnosisResult:
    """诊断结果数据结构"""
    disease_name: str = ""
    confidence: float = 0.0
    symptoms: List[str] = field(default_factory=list)
    pathogen: str = ""
    severity: str = "未知"
    environmental_factors: Dict[str, str] = field(default_factory=dict)
    treatment: Dict[str, List[str]] = field(default_factory=dict)
    prevention: List[str] = field(default_factory=list)
    reasoning_log: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "diagnosis": {
                "disease_name": self.disease_name,
                "confidence": self.confidence,
                "symptoms": self.symptoms,
                "pathogen": self.pathogen,
                "severity": self.severity
            },
            "environmental_factors": self.environmental_factors,
            "treatment": self.treatment,
            "prevention": self.prevention,
            "reasoning_log": self.reasoning_log,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class DiagnosisEngine:
    """
    IWDDA诊断引擎
    
    实现端到端诊断流程:
    1. 视觉特征提取 (YOLOv8 + DySnakeConv)
    2. 知识图谱检索 (Neo4j + GraphRAG)
    3. 多模态融合 (KAD-Former)
    4. 诊断报告生成
    """
    
    DISEASE_INFO = {
        "Yellow Rust": {
            "chinese_name": "条锈病",
            "pathogen": "条形柄锈菌 (Puccinia striiformis)",
            "symptoms": ["黄色条状孢子堆", "沿叶脉排列", "叶片褪绿"],
            "environment": {"temperature": "9-16°C", "humidity": "高湿度"},
            "treatment": {
                "chemical": ["三唑酮 (粉锈宁)", "戊唑醇", "丙环唑"],
                "biological": ["枯草芽孢杆菌制剂"],
                "cultural": ["清除病残体", "合理密植", "避免过量施氮"]
            },
            "prevention": ["选用抗病品种", "适时播种", "定期田间巡查"]
        },
        "Brown Rust": {
            "chinese_name": "叶锈病",
            "pathogen": "小麦叶锈菌 (Puccinia triticina)",
            "symptoms": ["橙褐色圆形孢子堆", "散生叶片表面"],
            "environment": {"temperature": "15-22°C", "humidity": "高湿度"},
            "treatment": {
                "chemical": ["三唑酮", "戊唑醇"],
                "biological": ["枯草芽孢杆菌制剂"],
                "cultural": ["清除病残体", "改善通风"]
            },
            "prevention": ["选用抗病品种", "合理施肥"]
        },
        "Black Rust": {
            "chinese_name": "秆锈病",
            "pathogen": "禾柄锈菌 (Puccinia graminis)",
            "symptoms": ["深褐色长椭圆形孢子堆", "茎秆破裂"],
            "environment": {"temperature": "20-30°C", "humidity": "高湿度"},
            "treatment": {
                "chemical": ["三唑酮", "戊唑醇"],
                "biological": [],
                "cultural": ["清除病残体", "轮作"]
            },
            "prevention": ["选用抗病品种", "及时防治"]
        },
        "Mildew": {
            "chinese_name": "白粉病",
            "pathogen": "禾布氏白粉菌 (Blumeria graminis)",
            "symptoms": ["白色粉状霉层", "叶片发黄", "黑色小点"],
            "environment": {"temperature": "15-20°C", "humidity": "中等湿度"},
            "treatment": {
                "chemical": ["三唑酮", "腈菌唑", "丙环唑"],
                "biological": ["枯草芽孢杆菌"],
                "cultural": ["合理密植", "改善通风"]
            },
            "prevention": ["选用抗病品种", "控制种植密度"]
        },
        "Fusarium Head Blight": {
            "chinese_name": "赤霉病",
            "pathogen": "禾谷镰刀菌 (Fusarium graminearum)",
            "symptoms": ["穗部漂白", "粉红色霉层", "籽粒干瘪"],
            "environment": {"temperature": "25-30°C", "humidity": "花期连阴雨"},
            "treatment": {
                "chemical": ["多菌灵", "戊唑醇"],
                "biological": [],
                "cultural": ["花期避雨", "及时收割"]
            },
            "prevention": ["选用抗病品种", "花期注意天气"]
        },
        "Aphid": {
            "chinese_name": "蚜虫",
            "pathogen": "麦长管蚜 (Sitobion avenae)",
            "symptoms": ["叶片卷曲", "蜜露", "黄化"],
            "environment": {"temperature": "全生育期", "humidity": "适中"},
            "treatment": {
                "chemical": ["吡虫啉", "阿维菌素"],
                "biological": ["瓢虫", "草蛉"],
                "cultural": ["清除杂草", "保护天敌"]
            },
            "prevention": ["早期监测", "保护天敌"]
        },
        "Mite": {
            "chinese_name": "螨虫",
            "pathogen": "麦岩螨 (Petrobia latens)",
            "symptoms": ["叶片黄化", "失绿", "白色斑点"],
            "environment": {"temperature": "干旱期", "humidity": "低湿度"},
            "treatment": {
                "chemical": ["阿维菌素", "哒螨灵"],
                "biological": [],
                "cultural": ["灌溉保湿"]
            },
            "prevention": ["保持田间湿度", "早期防治"]
        },
        "Healthy": {
            "chinese_name": "健康",
            "pathogen": "无",
            "symptoms": ["正常生长", "无病斑"],
            "environment": {},
            "treatment": {"chemical": [], "biological": [], "cultural": []},
            "prevention": ["继续监测", "保持良好管理"]
        }
    }
    
    SEVERITY_LEVELS = {
        "轻度": {"range": "0-10%", "action": "加强监测，预防扩散"},
        "中度": {"range": "10-30%", "action": "及时喷药防治"},
        "重度": {"range": ">30%", "action": "紧急防治，间隔7-10天再喷"}
    }
    
    def __init__(self, vision_agent=None, knowledge_agent=None, fusion_agent=None):
        """
        初始化诊断引擎
        
        :param vision_agent: 视觉智能体实例
        :param knowledge_agent: 知识图谱智能体实例
        :param fusion_agent: 融合智能体实例
        """
        print("🏥 [Diagnosis Engine] 初始化诊断引擎...")
        
        self.vision_agent = vision_agent
        self.knowledge_agent = knowledge_agent
        self.fusion_agent = fusion_agent
        
        self.diagnosis_history: List[DiagnosisResult] = []
        
        print("✅ [Diagnosis Engine] 诊断引擎就绪")
    
    def diagnose(
        self,
        image_path: str,
        user_description: str = "",
        environment_info: Optional[Dict[str, Any]] = None,
        conf_threshold: float = 0.25
    ) -> DiagnosisResult:
        """
        执行端到端诊断
        
        :param image_path: 图像路径
        :param user_description: 用户描述
        :param environment_info: 环境信息
        :param conf_threshold: 置信度阈值
        :return: 诊断结果
        """
        print(f"\n{'='*60}")
        print(f"🏥 [Diagnosis] 开始诊断: {os.path.basename(image_path)}")
        print(f"{'='*60}")
        
        result = DiagnosisResult()
        start_time = time.time()
        
        # 阶段1: 视觉感知
        print("\n👁️ [Stage 1] 视觉感知...")
        vision_result = self._vision_perception(image_path, conf_threshold)
        result.reasoning_log.append(f"视觉检测: {vision_result}")
        
        # 阶段2: 知识图谱检索
        print("\n📚 [Stage 2] 知识图谱检索...")
        knowledge_result = self._knowledge_retrieval(vision_result.get("label", ""))
        result.reasoning_log.append(f"知识检索: {knowledge_result}")
        
        # 阶段3: 多模态融合
        print("\n🔗 [Stage 3] 多模态融合...")
        fusion_result = self._multimodal_fusion(
            vision_result, 
            knowledge_result, 
            user_description
        )
        result.reasoning_log.append(f"融合决策: {fusion_result}")
        
        # 阶段4: 生成诊断报告
        print("\n📝 [Stage 4] 生成诊断报告...")
        self._generate_report(result, fusion_result, environment_info)
        
        elapsed_time = time.time() - start_time
        result.reasoning_log.append(f"诊断耗时: {elapsed_time:.2f}秒")
        
        # 保存历史
        self.diagnosis_history.append(result)
        
        print(f"\n{'='*60}")
        print(f"✅ [Diagnosis] 诊断完成: {result.disease_name} (置信度: {result.confidence:.2%})")
        print(f"{'='*60}")
        
        return result
    
    def _vision_perception(self, image_path: str, conf_threshold: float) -> Dict[str, Any]:
        """视觉感知阶段"""
        if self.vision_agent is None:
            return {"label": "未知", "confidence": 0.0, "detections": []}
        
        try:
            detections = self.vision_agent.detect(
                image_path, 
                conf_threshold=conf_threshold
            )
            
            if detections:
                best = max(detections, key=lambda x: x.get("confidence", 0))
                return {
                    "label": best.get("name", "未知"),
                    "confidence": best.get("confidence", 0),
                    "detections": detections
                }
        except Exception as e:
            print(f"⚠️ 视觉感知异常: {e}")
        
        return {"label": "未知", "confidence": 0.0, "detections": []}
    
    def _knowledge_retrieval(self, disease_label: str) -> Dict[str, Any]:
        """知识图谱检索阶段"""
        result = {
            "disease_info": {},
            "related_entities": [],
            "treatments": []
        }
        
        if disease_label in self.DISEASE_INFO:
            result["disease_info"] = self.DISEASE_INFO[disease_label]
        
        if self.knowledge_agent is not None:
            try:
                kg_result = self.knowledge_agent.query_disease(disease_label)
                result["related_entities"] = kg_result.get("entities", [])
                result["treatments"] = kg_result.get("treatments", [])
            except Exception as e:
                print(f"⚠️ 知识检索异常: {e}")
        
        return result
    
    def _multimodal_fusion(
        self,
        vision_result: Dict[str, Any],
        knowledge_result: Dict[str, Any],
        user_description: str
    ) -> Dict[str, Any]:
        """多模态融合阶段"""
        if self.fusion_agent is not None:
            try:
                return self.fusion_agent.fuse_and_decide(
                    vision_result,
                    {"label": vision_result.get("label", ""), "conf": 0},
                    user_description
                )
            except Exception as e:
                print(f"⚠️ 融合异常: {e}")
        
        # 简单融合逻辑
        label = vision_result.get("label", "未知")
        conf = vision_result.get("confidence", 0)
        
        return {
            "final_diagnosis": label,
            "final_confidence": conf,
            "fusion_method": "simple"
        }
    
    def _generate_report(
        self,
        result: DiagnosisResult,
        fusion_result: Dict[str, Any],
        environment_info: Optional[Dict[str, Any]]
    ):
        """生成诊断报告"""
        disease_name = fusion_result.get("final_diagnosis", "未知")
        confidence = fusion_result.get("final_confidence", 0)
        
        result.disease_name = disease_name
        result.confidence = confidence
        
        # 获取病害详细信息
        if disease_name in self.DISEASE_INFO:
            info = self.DISEASE_INFO[disease_name]
            result.symptoms = info.get("symptoms", [])
            result.pathogen = info.get("pathogen", "")
            result.environmental_factors = info.get("environment", {})
            result.treatment = info.get("treatment", {})
            result.prevention = info.get("prevention", [])
        
        # 确定严重程度
        if confidence >= 0.8:
            result.severity = "重度"
        elif confidence >= 0.5:
            result.severity = "中度"
        else:
            result.severity = "轻度"
        
        # 合并环境信息
        if environment_info:
            result.environmental_factors.update(environment_info)
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取诊断历史"""
        return [r.to_dict() for r in self.diagnosis_history[-limit:]]
    
    def export_report(self, result: DiagnosisResult, output_path: str):
        """导出诊断报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.to_json())
        print(f"📄 报告已导出: {output_path}")


def create_diagnosis_engine(config: Optional[Dict[str, Any]] = None) -> DiagnosisEngine:
    """
    工厂函数: 创建诊断引擎实例
    
    :param config: 配置字典
    :return: DiagnosisEngine实例
    """
    config = config or {}
    
    vision_agent = None
    knowledge_agent = None
    fusion_agent = None
    
    if config.get("load_vision", True):
        try:
            from src.vision.vision_engine import VisionAgent
            vision_agent = VisionAgent()
        except Exception as e:
            print(f"⚠️ 视觉模块加载失败: {e}")
    
    if config.get("load_knowledge", True):
        try:
            from src.graph.graph_engine import KnowledgeAgent
            knowledge_agent = KnowledgeAgent()
        except Exception as e:
            print(f"⚠️ 知识图谱模块加载失败: {e}")
    
    return DiagnosisEngine(
        vision_agent=vision_agent,
        knowledge_agent=knowledge_agent,
        fusion_agent=fusion_agent
    )

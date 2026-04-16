"""
Mock 诊断服务模块
用于测试环境的模拟诊断服务，无需依赖外部 tests 目录
"""
import random
from typing import Dict, List, Any


class MockDiagnosisService:
    """Mock 诊断服务类"""
    
    def __init__(self):
        """初始化 Mock 诊断服务"""
        self.disease_database = {
            "条锈病": {
                "disease_id": 1,
                "disease_name": "小麦条锈病",
                "scientific_name": "Puccinia striiformis f. sp. tritici",
                "symptoms": [
                    "叶片出现黄色条状孢子堆",
                    "沿叶脉平行排列",
                    "病斑呈鲜黄色",
                    "后期产生黑色夏孢子堆"
                ],
                "prevention_methods": [
                    "选用抗病品种",
                    "合理密植，改善通风",
                    "科学施肥，增强植株抗性"
                ],
                "treatment_methods": [
                    "喷洒 15% 三唑酮可湿性粉剂 1000 倍液",
                    "使用 12.5% 烯唑醇可湿性粉剂 2500 倍液",
                    "喷施 25% 丙环唑乳油 2000 倍液"
                ],
                "severity_thresholds": {
                    "low": 0.3,
                    "medium": 0.6,
                    "high": 1.0
                }
            },
            "白粉病": {
                "disease_id": 2,
                "disease_name": "小麦白粉病",
                "scientific_name": "Blumeria graminis f. sp. tritici",
                "symptoms": [
                    "叶片表面出现白色粉状斑点",
                    "逐渐扩大形成白色粉层",
                    "后期产生黑色小粒点"
                ],
                "prevention_methods": [
                    "选用抗病品种",
                    "控制氮肥施用",
                    "及时清除病残体"
                ],
                "treatment_methods": [
                    "喷洒 25% 三唑酮可湿性粉剂 1500 倍液",
                    "使用 40% 氟硅唑乳油 8000 倍液",
                    "喷施 10% 苯醚甲环唑水分散粒剂 1500 倍液"
                ],
                "severity_thresholds": {
                    "low": 0.3,
                    "medium": 0.6,
                    "high": 1.0
                }
            },
            "赤霉病": {
                "disease_id": 3,
                "disease_name": "小麦赤霉病",
                "scientific_name": "Fusarium graminearum",
                "symptoms": [
                    "穗部出现水渍状病斑",
                    "后期产生粉红色霉层",
                    "病穗枯白",
                    "籽粒干瘪"
                ],
                "prevention_methods": [
                    "选用抗病品种",
                    "及时排水降湿",
                    "合理施用氮肥"
                ],
                "treatment_methods": [
                    "喷洒 50% 多菌灵可湿性粉剂 1000 倍液",
                    "使用 70% 甲基硫菌灵可湿性粉剂 1500 倍液",
                    "喷施 25% 氰烯菌酯悬浮剂 2000 倍液"
                ],
                "severity_thresholds": {
                    "low": 0.3,
                    "medium": 0.6,
                    "high": 1.0
                }
            }
        }
    
    async def diagnose_by_text(self, symptoms: str, weather: str = "", growth_stage: str = "", affected_part: str = "") -> Dict[str, Any]:
        """
        文本诊断
        
        参数:
            symptoms: 症状描述文本
            weather: 天气条件（可选）
            growth_stage: 生长阶段（可选）
            affected_part: 发病部位（可选）
        
        返回:
            诊断结果字典
        """
        symptoms_lower = symptoms.lower()
        
        if "黄色" in symptoms and "条状" in symptoms:
            disease_key = "条锈病"
            confidence = 0.85 + random.uniform(0, 0.1)
        elif "白色" in symptoms and "粉状" in symptoms:
            disease_key = "白粉病"
            confidence = 0.85 + random.uniform(0, 0.1)
        elif "穗部" in symptoms or "枯白" in symptoms:
            disease_key = "赤霉病"
            confidence = 0.85 + random.uniform(0, 0.1)
        else:
            disease_key = "条锈病"
            confidence = 0.75 + random.uniform(0, 0.1)
        
        disease = self.disease_database[disease_key]
        
        return {
            "diagnosis_id": random.randint(1000, 9999),
            "disease_id": disease["disease_id"],
            "disease_name": disease["disease_name"],
            "scientific_name": disease["scientific_name"],
            "confidence": round(confidence, 3),
            "visual_confidence": 0.0,
            "textual_confidence": round(confidence, 3),
            "knowledge_confidence": 0.0,
            "severity": self._calculate_severity(confidence),
            "description": f"根据症状描述，{disease['symptoms'][0]}",
            "recommendations": disease["treatment_methods"],
            "prevention_methods": disease["prevention_methods"],
            "symptoms": disease["symptoms"],
            "knowledge_references": [],
            "reasoning_chain": [],
            "knowledge_links": [
                {
                    "title": f"{disease['disease_name']}防治方法",
                    "url": f"/knowledge/{disease['disease_id']}"
                }
            ]
        }
    
    async def diagnose_by_image(self, image_bytes: bytes, symptoms: str = "", weather: str = "", growth_stage: str = "", affected_part: str = "") -> Dict[str, Any]:
        """
        图像诊断
        
        参数:
            image_bytes: 图像字节数据
            symptoms: 症状描述文本（可选）
            weather: 天气条件（可选）
            growth_stage: 生长阶段（可选）
            affected_part: 发病部位（可选）
        
        返回:
            诊断结果字典
        """
        disease_key = random.choice(list(self.disease_database.keys()))
        disease = self.disease_database[disease_key]
        confidence = 0.90 + random.uniform(0, 0.08)
        
        x = random.randint(50, 200)
        y = random.randint(50, 200)
        width = random.randint(100, 300)
        height = random.randint(100, 300)
        box_confidence = round(0.85 + random.uniform(0, 0.1), 3)

        return {
            "diagnosis_id": random.randint(1000, 9999),
            "disease_id": disease["disease_id"],
            "disease_name": disease["disease_name"],
            "scientific_name": disease["scientific_name"],
            "confidence": round(confidence, 3),
            "visual_confidence": round(confidence, 3),
            "textual_confidence": 0.0,
            "knowledge_confidence": 0.0,
            "severity": self._calculate_severity(confidence),
            "description": f"图像分析显示：{disease['symptoms'][0]}",
            "recommendations": disease["treatment_methods"],
            "prevention_methods": disease["prevention_methods"],
            "symptoms": disease["symptoms"],
            "knowledge_references": [],
            "reasoning_chain": [],
            "bounding_boxes": [
                {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "confidence": box_confidence
                }
            ],
            "roi_boxes": [
                {
                    "box": [x, y, x + width, y + height],
                    "class_name": disease["disease_name"],
                    "confidence": box_confidence
                }
            ],
            "knowledge_links": [
                {
                    "title": f"{disease['disease_name']}防治方法",
                    "url": f"/knowledge/{disease['disease_id']}"
                }
            ]
        }
    
    def _calculate_severity(self, confidence: float) -> str:
        """
        根据置信度计算严重程度
        
        参数:
            confidence: 诊断置信度
        
        返回:
            严重程度字符串 (low/medium/high)
        """
        if confidence < 0.5:
            return "low"
        elif confidence < 0.8:
            return "medium"
        else:
            return "high"
    
    def get_disease_info(self, disease_id: int) -> Dict[str, Any]:
        """
        获取病害详细信息
        
        参数:
            disease_id: 病害 ID
        
        返回:
            病害信息字典
        """
        for disease in self.disease_database.values():
            if disease["disease_id"] == disease_id:
                return disease
        return None
    
    def search_diseases(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索病害
        
        参数:
            keyword: 搜索关键词
        
        返回:
            病害列表
        """
        results = []
        for disease in self.disease_database.values():
            if (keyword in disease["disease_name"] or 
                keyword in disease["scientific_name"] or
                any(keyword in symptom for symptom in disease["symptoms"])):
                results.append({
                    "disease_id": disease["disease_id"],
                    "disease_name": disease["disease_name"],
                    "scientific_name": disease["scientific_name"],
                    "confidence": 0.9
                })
        return results


mock_diagnosis_service = MockDiagnosisService()

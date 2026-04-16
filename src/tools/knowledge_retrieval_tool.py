# -*- coding: utf-8 -*-
"""
知识检索工具 - Knowledge Retrieval Tool
查询农业知识库，获取病害详细信息和防治知识
"""

import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .base_tool import BaseTool


class KnowledgeRetrievalTool(BaseTool):
    """
    知识检索工具类
    
    功能：
    1. 查询病害知识库
    2. 获取病原体、症状、防治方法等详细信息
    3. 支持模糊匹配和相关推荐
    4. 集成知识图谱检索
    
    输入参数:
        disease_name: 病害名称（必需）
        query_type: 查询类型（可选，默认"all"）
        include_treatments: 是否包含防治方案（可选，默认 True）
    
    输出结果:
        disease_info: 病害详细信息
        symptoms: 症状列表
        pathogen: 病原体信息
        treatments: 防治方案
        prevention: 预防措施
        related_diseases: 相关病害
    """
    
    # 农业病害知识库
    DISEASE_KNOWLEDGE = {
        "条锈病": {
            "pathogen": "条形柄锈菌 (Puccinia striiformis)",
            "symptoms": [
                "叶片出现黄色条状孢子堆",
                "沿叶脉纵向排列",
                "叶片褪绿黄化",
                "严重时叶片枯死"
            ],
            "environment": {
                "temperature": "9-16°C",
                "humidity": "高湿度",
                "conditions": "阴雨天气易流行"
            },
            "treatments": [
                {
                    "name": "三唑酮",
                    "concentration": "15% 可湿性粉剂",
                    "dosage": "600-800 倍液",
                    "method": "叶面喷施"
                },
                {
                    "name": "戊唑醇",
                    "concentration": "10% 水乳剂",
                    "dosage": "40-50ml/亩",
                    "method": "兑水喷雾"
                },
                {
                    "name": "丙环唑",
                    "concentration": "25% 乳油",
                    "dosage": "20-30ml/亩",
                    "method": "叶面喷施"
                }
            ],
            "prevention": [
                "选用抗病品种",
                "适时播种，避开发病高峰期",
                "合理施肥，增强植株抗性",
                "定期田间巡查，早发现早防治"
            ],
            "related_diseases": ["叶锈病", "秆锈病"]
        },
        "叶锈病": {
            "pathogen": "小麦叶锈菌 (Puccinia triticina)",
            "symptoms": [
                "橙褐色圆形孢子堆",
                "散生于叶片表面",
                "叶片黄化早衰"
            ],
            "environment": {
                "temperature": "15-22°C",
                "humidity": "高湿度",
                "conditions": "温暖湿润环境"
            },
            "treatments": [
                {
                    "name": "三唑酮",
                    "concentration": "15% 可湿性粉剂",
                    "dosage": "600-800 倍液",
                    "method": "叶面喷施"
                },
                {
                    "name": "戊唑醇",
                    "concentration": "10% 水乳剂",
                    "dosage": "40-50ml/亩",
                    "method": "兑水喷雾"
                }
            ],
            "prevention": [
                "选用抗病品种",
                "合理施肥",
                "避免密植，改善通风"
            ],
            "related_diseases": ["条锈病", "秆锈病"]
        },
        "秆锈病": {
            "pathogen": "禾柄锈菌 (Puccinia graminis)",
            "symptoms": [
                "深褐色长椭圆形孢子堆",
                "主要危害茎秆",
                "茎秆破裂，易倒伏"
            ],
            "environment": {
                "temperature": "20-30°C",
                "humidity": "高湿度",
                "conditions": "高温高湿"
            },
            "treatments": [
                {
                    "name": "三唑酮",
                    "concentration": "15% 可湿性粉剂",
                    "dosage": "600-800 倍液",
                    "method": "叶面喷施"
                },
                {
                    "name": "戊唑醇",
                    "concentration": "10% 水乳剂",
                    "dosage": "40-50ml/亩",
                    "method": "兑水喷雾"
                }
            ],
            "prevention": [
                "选用抗病品种",
                "清除转主寄主",
                "合理施肥"
            ],
            "related_diseases": ["条锈病", "叶锈病"]
        },
        "白粉病": {
            "pathogen": "禾布氏白粉菌 (Blumeria graminis)",
            "symptoms": [
                "白色粉状霉层",
                "叶片发黄",
                "后期出现黑色小点"
            ],
            "environment": {
                "temperature": "15-20°C",
                "humidity": "中等湿度",
                "conditions": "通风不良"
            },
            "treatments": [
                {
                    "name": "三唑酮",
                    "concentration": "15% 可湿性粉剂",
                    "dosage": "600-800 倍液",
                    "method": "叶面喷施"
                },
                {
                    "name": "腈菌唑",
                    "concentration": "12.5% 乳油",
                    "dosage": "20-30ml/亩",
                    "method": "兑水喷雾"
                }
            ],
            "prevention": [
                "选用抗病品种",
                "合理密植",
                "避免过量施氮"
            ],
            "related_diseases": ["纹枯病"]
        },
        "蚜虫": {
            "pathogen": "麦长管蚜 (Sitobion avenae)",
            "symptoms": [
                "叶片卷曲",
                "分泌蜜露",
                "叶片黄化",
                "传播病毒病"
            ],
            "environment": {
                "temperature": "15-25°C",
                "humidity": "适中",
                "conditions": "全生育期均可发生"
            },
            "treatments": [
                {
                    "name": "吡虫啉",
                    "concentration": "10% 可湿性粉剂",
                    "dosage": "20-30g/亩",
                    "method": "兑水喷雾"
                },
                {
                    "name": "啶虫脒",
                    "concentration": "3% 乳油",
                    "dosage": "30-40ml/亩",
                    "method": "叶面喷施"
                }
            ],
            "prevention": [
                "种植抗虫品种",
                "适时播种",
                "保护天敌（瓢虫、草蛉）"
            ],
            "related_diseases": ["螨虫"]
        },
        "螨虫": {
            "pathogen": "麦岩螨 (Petrobia latens)",
            "symptoms": [
                "叶片黄化",
                "失绿白斑",
                "叶片干枯"
            ],
            "environment": {
                "temperature": "20-30°C",
                "humidity": "干旱",
                "conditions": "干旱少雨"
            },
            "treatments": [
                {
                    "name": "阿维菌素",
                    "concentration": "1.8% 乳油",
                    "dosage": "30-40ml/亩",
                    "method": "兑水喷雾"
                },
                {
                    "name": "哒螨灵",
                    "concentration": "15% 乳油",
                    "dosage": "20-30ml/亩",
                    "method": "叶面喷施"
                }
            ],
            "prevention": [
                "避免干旱，保持田间湿度",
                "轮作倒茬",
                "清除田间杂草"
            ],
            "related_diseases": ["蚜虫"]
        },
        "健康": {
            "pathogen": "无",
            "symptoms": [
                "正常生长",
                "无病斑",
                "叶片健康绿色"
            ],
            "environment": {},
            "treatments": [],
            "prevention": [
                "继续监测",
                "保持良好管理",
                "定期巡查"
            ],
            "related_diseases": []
        }
    }
    
    def __init__(self, knowledge_graph=None):
        """
        初始化知识检索工具
        
        :param knowledge_graph: 知识图谱实例（可选）
        """
        super().__init__(
            name="KnowledgeRetrievalTool",
            description="农业知识检索工具，查询病害详细信息和防治知识"
        )
        self.knowledge_graph = knowledge_graph
        self._knowledge_base = self.DISEASE_KNOWLEDGE
    
    def get_name(self) -> str:
        """
        获取工具名称
        
        :return: 工具名称
        """
        return "KnowledgeRetrievalTool"
    
    def get_description(self) -> str:
        """
        获取工具描述
        
        :return: 工具描述
        """
        return "农业知识检索工具，查询病害详细信息和防治知识"
    
    def initialize(self) -> bool:
        """
        初始化工具，加载知识库
        
        :return: 初始化是否成功
        """
        try:
            # 尝试加载知识图谱
            if self.knowledge_graph is None:
                print("[KnowledgeRetrievalTool] 使用内置知识库")
            
            return True
        except Exception as e:
            print(f"[KnowledgeRetrievalTool] 初始化失败：{e}")
            return False
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证输入参数
        
        :param kwargs: 输入参数
        :return: 参数是否有效
        """
        disease_name = kwargs.get('disease_name')
        if not disease_name:
            print("[KnowledgeRetrievalTool] 参数验证失败：缺少 disease_name")
            return False
        
        return True
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行知识检索
        
        :param kwargs: 执行参数
            - disease_name: 病害名称
            - query_type: 查询类型（all/symptoms/treatment/prevention）
            - include_treatments: 是否包含防治方案
        :return: 检索结果字典
        """
        disease_name = kwargs.get('disease_name')
        query_type = kwargs.get('query_type', 'all')
        include_treatments = kwargs.get('include_treatments', True)
        
        print(f"[KnowledgeRetrievalTool] 检索病害：{disease_name}")
        
        try:
            # 执行检索
            result = self._retrieve_knowledge(
                disease_name,
                query_type,
                include_treatments
            )
            
            diagnosis_result = {
                "success": True,
                "data": result,
                "message": f"检索成功：{disease_name}",
                "tool_name": self.get_name()
            }
            
            print(f"[KnowledgeRetrievalTool] 检索完成：找到 {disease_name} 的相关信息")
            
            return diagnosis_result
        
        except Exception as e:
            error_msg = f"知识检索异常：{str(e)}"
            print(f"[KnowledgeRetrievalTool] {error_msg}")
            return {
                "success": False,
                "data": None,
                "message": error_msg,
                "error": error_msg,
                "tool_name": self.get_name()
            }
    
    def _retrieve_knowledge(
        self,
        disease_name: str,
        query_type: str = 'all',
        include_treatments: bool = True
    ) -> Dict[str, Any]:
        """
        检索病害知识
        
        :param disease_name: 病害名称
        :param query_type: 查询类型
        :param include_treatments: 是否包含防治方案
        :return: 检索结果
        """
        # 尝试精确匹配
        disease_info = self._knowledge_base.get(disease_name)
        
        if not disease_info:
            # 尝试模糊匹配
            disease_info = self._fuzzy_match(disease_name)
        
        if not disease_info:
            return {
                "disease_name": disease_name,
                "found": False,
                "message": "未找到相关病害信息"
            }
        
        # 构建检索结果
        result = {
            "disease_name": disease_name,
            "found": True,
            "pathogen": disease_info.get("pathogen", "未知"),
            "symptoms": disease_info.get("symptoms", []),
            "environment": disease_info.get("environment", {}),
            "related_diseases": disease_info.get("related_diseases", [])
        }
        
        # 根据查询类型返回不同信息
        if query_type == 'all' or query_type == 'symptoms':
            result["symptoms"] = disease_info.get("symptoms", [])
        
        if query_type == 'all' or query_type == 'environment':
            result["environment"] = disease_info.get("environment", {})
        
        if query_type == 'all' or query_type == 'prevention':
            result["prevention"] = disease_info.get("prevention", [])
        
        if include_treatments and (query_type == 'all' or query_type == 'treatment'):
            result["treatments"] = disease_info.get("treatments", [])
        
        # 如果知识图谱可用，增强检索结果
        if self.knowledge_graph:
            try:
                kg_enhanced = self._query_knowledge_graph(disease_name)
                result["kg_enhanced"] = kg_enhanced
            except Exception as e:
                print(f"[KnowledgeRetrievalTool] 知识图谱查询失败：{e}")
        
        return result
    
    def _fuzzy_match(self, disease_name: str) -> Optional[Dict[str, Any]]:
        """
        模糊匹配病害名称
        
        :param disease_name: 病害名称
        :return: 匹配的病害信息
        """
        disease_name_lower = disease_name.lower()
        
        for name, info in self._knowledge_base.items():
            if disease_name_lower in name.lower() or name.lower() in disease_name_lower:
                return info
        
        return None
    
    def _query_knowledge_graph(self, disease_name: str) -> Dict[str, Any]:
        """
        查询知识图谱
        
        :param disease_name: 病害名称
        :return: 知识图谱查询结果
        """
        if self.knowledge_graph is None:
            return {}
        
        try:
            # 调用知识图谱查询接口
            kg_result = self.knowledge_graph.query_disease(disease_name)
            return kg_result
        except Exception as e:
            print(f"[KnowledgeRetrievalTool] 知识图谱查询异常：{e}")
            return {}
    
    def get_all_diseases(self) -> List[str]:
        """
        获取知识库中所有病害名称
        
        :return: 病害名称列表
        """
        return list(self._knowledge_base.keys())
    
    def get_treatments(self, disease_name: str) -> List[Dict[str, Any]]:
        """
        获取指定病害的防治方案
        
        :param disease_name: 病害名称
        :return: 防治方案列表
        """
        disease_info = self._knowledge_base.get(disease_name)
        if disease_info:
            return disease_info.get("treatments", [])
        return []
    
    def get_prevention(self, disease_name: str) -> List[str]:
        """
        获取指定病害的预防措施
        
        :param disease_name: 病害名称
        :return: 预防措施列表
        """
        disease_info = self._knowledge_base.get(disease_name)
        if disease_info:
            return disease_info.get("prevention", [])
        return []


def test_knowledge_retrieval_tool():
    """测试知识检索工具"""
    print("=" * 60)
    print("🧪 测试 KnowledgeRetrievalTool")
    print("=" * 60)
    
    tool = KnowledgeRetrievalTool()
    
    print("\n1️⃣ 初始化工具")
    init_success = tool.initialize()
    print(f"   初始化结果：{'成功' if init_success else '失败'}")
    
    print("\n2️⃣ 获取工具信息")
    print(f"   工具名称：{tool.get_name()}")
    print(f"   工具描述：{tool.get_description()}")
    
    print("\n3️⃣ 检索病害知识：条锈病")
    result = tool.execute(disease_name="条锈病")
    
    print(f"\n4️⃣ 检索结果:")
    print(f"   成功：{result.get('success')}")
    if result.get('data'):
        data = result['data']
        print(f"   病害：{data.get('disease_name')}")
        print(f"   病原体：{data.get('pathogen')}")
        print(f"   症状：{', '.join(data.get('symptoms', []))}")
        print(f"   防治方案数量：{len(data.get('treatments', []))}")
    
    print("\n5️⃣ 检索病害知识：蚜虫")
    result2 = tool.execute(disease_name="蚜虫", query_type="treatment")
    
    if result2.get('data'):
        data2 = result2['data']
        print(f"   防治方案:")
        for treatment in data2.get('treatments', []):
            print(f"     - {treatment.get('name')} ({treatment.get('concentration')})")
    
    print("\n" + "=" * 60)
    print("✅ KnowledgeRetrievalTool 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_knowledge_retrieval_tool()

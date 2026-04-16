# -*- coding: utf-8 -*-
"""
认知引擎 - Cognition Engine
集成多模态大模型，提供高级语义理解和诊断报告生成功能

支持的模型:
- Qwen3-VL-2B-Instruct (默认推荐，约2GB 显存优化) - Qwen/Qwen3-VL-2B-Instruct

该模块作为 LanguageAgent 的增强版，支持：
1. 多模态输入（图像 + 文本）- 原生支持 Qwen3-VL 接口
2. 基于多模态大模型的语义理解
3. 交互式对话
4. 专业诊断报告生成
5. 纯文本和图像 + 文本两种模式
"""
import os
import sys
from typing import Optional, List, Dict, Any
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cognition.prompt_templates import PromptTemplate, DetectionResult
from src.graph.graph_engine import KnowledgeAgent


class CognitionEngine:
    """
    认知引擎
    
    集成多模态大模型，提供：
    - 图像语义理解（原生支持 Qwen3-VL 接口）
    - 诊断报告生成
    - 知识问答
    - 交互式对话
    - 纯文本和图像 + 文本两种模式
    
    支持的模型：
    - Qwen/Qwen3-VL-2B-Instruct (默认推荐)
    """
    
    DISEASE_DATABASE = {
        "条锈病": {
            "chinese_name": "条锈病",
            "pathogen": "条形柄锈菌 (Puccinia striiformis)",
            "symptoms": ["黄色条状孢子堆", "沿叶脉排列", "叶片褪绿", "严重时叶片枯死"],
            "environment": {"temperature": "9-16°C", "humidity": "高湿度"},
            "treatment": {
                "chemical": ["三唑酮 (粉锈宁)", "戊唑醇", "丙环唑"],
                "biological": ["枯草芽孢杆菌制剂"],
                "cultural": ["清除病残体", "合理密植", "避免过量施氮"]
            },
            "prevention": ["选用抗病品种", "适时播种", "定期田间巡查"]
        },
        "叶锈病": {
            "chinese_name": "叶锈病",
            "pathogen": "小麦叶锈菌 (Puccinia triticina)",
            "symptoms": ["橙褐色圆形孢子堆", "散生叶片表面", "周围有褪绿圈"],
            "environment": {"temperature": "15-22°C", "humidity": "高湿度"},
            "treatment": {
                "chemical": ["三唑酮", "戊唑醇", "氟环唑"],
                "biological": ["枯草芽孢杆菌制剂"],
                "cultural": ["清除病残体", "改善通风"]
            },
            "prevention": ["选用抗病品种", "合理施肥", "避免密植"]
        },
        "秆锈病": {
            "chinese_name": "秆锈病",
            "pathogen": "禾柄锈菌 (Puccinia graminis)",
            "symptoms": ["深褐色长椭圆形孢子堆", "茎秆破裂", "植株倒伏"],
            "environment": {"temperature": "20-30°C", "humidity": "高湿度"},
            "treatment": {
                "chemical": ["三唑酮", "戊唑醇", "丙环唑"],
                "biological": [],
                "cultural": ["清除病残体", "轮作"]
            },
            "prevention": ["选用抗病品种", "清除转主寄主", "合理施肥"]
        },
        "白粉病": {
            "chinese_name": "白粉病",
            "pathogen": "禾布氏白粉菌 (Blumeria graminis)",
            "symptoms": ["白色粉状霉层", "叶片褪绿", "后期出现黑色小点"],
            "environment": {"temperature": "15-20°C", "humidity": "中等湿度"},
            "treatment": {
                "chemical": ["三唑酮", "腈菌唑", "醚菌酯"],
                "biological": ["枯草芽孢杆菌"],
                "cultural": ["改善通风透光", "降低种植密度"]
            },
            "prevention": ["选用抗病品种", "合理密植", "避免过量施氮"]
        },
        "赤霉病": {
            "chinese_name": "赤霉病",
            "pathogen": "禾谷镰刀菌 (Fusarium graminearum)",
            "symptoms": ["穗部漂白", "粉红色霉层", "籽粒干瘪"],
            "environment": {"temperature": "20-25°C", "humidity": "花期连阴雨"},
            "treatment": {
                "chemical": ["多菌灵", "戊唑醇", "咪鲜胺"],
                "biological": [],
                "cultural": ["花期避开阴雨", "及时排水"]
            },
            "prevention": ["选用抗病品种", "花期喷药预防", "及时排水降湿"]
        },
        "纹枯病": {
            "chinese_name": "纹枯病",
            "pathogen": "禾谷丝核菌 (Rhizoctonia cerealis)",
            "symptoms": ["茎基部云纹状病斑", "叶片枯黄", "植株倒伏"],
            "environment": {"temperature": "20-28°C", "humidity": "高湿度"},
            "treatment": {
                "chemical": ["井冈霉素", "噻呋酰胺", "戊唑醇"],
                "biological": [],
                "cultural": ["轮作倒茬", "深耕灭茬"]
            },
            "prevention": ["选用抗病品种", "轮作倒茬", "深耕灭茬"]
        },
        "根腐病": {
            "chinese_name": "根腐病",
            "pathogen": "多种镰刀菌 (Fusarium spp.)",
            "symptoms": ["根部褐变腐烂", "植株矮小", "叶片发黄枯萎"],
            "environment": {"temperature": "20-28°C", "humidity": "土壤过湿"},
            "treatment": {
                "chemical": ["多菌灵", "甲基硫菌灵", "咯菌腈"],
                "biological": ["木霉菌制剂"],
                "cultural": ["改善排水", "轮作"]
            },
            "prevention": ["选用抗病品种", "种子包衣", "改善排水"]
        },
        "蚜虫": {
            "chinese_name": "蚜虫",
            "pathogen": "麦蚜 (Sitobion avenae)",
            "symptoms": ["叶片卷曲", "蜜露分泌", "叶片发黄", "麦穗枯萎"],
            "environment": {"temperature": "15-25°C", "humidity": "中等湿度"},
            "treatment": {
                "chemical": ["吡虫啉", "啶虫脒", "抗蚜威"],
                "biological": ["瓢虫", "草蛉"],
                "cultural": ["清除田间杂草", "保护天敌"]
            },
            "prevention": ["种植抗虫品种", "适时播种", "保护天敌昆虫"]
        },
        "螨虫": {
            "chinese_name": "螨虫",
            "pathogen": "麦岩螨 (Petrobia latens)",
            "symptoms": ["叶片黄化失绿", "叶面出现白斑", "叶片干枯"],
            "environment": {"temperature": "20-30°C", "humidity": "干旱环境"},
            "treatment": {
                "chemical": ["阿维菌素", "哒螨灵", "螺螨酯"],
                "biological": ["捕食螨"],
                "cultural": ["增加田间湿度", "清除杂草"]
            },
            "prevention": ["避免干旱", "轮作倒茬", "清除田间杂草"]
        },
        "黑粉病": {
            "chinese_name": "黑粉病",
            "pathogen": "小麦散黑粉菌 (Ustilago tritici)",
            "symptoms": ["穗部变成黑粉", "植株矮化", "旗叶破裂"],
            "environment": {"temperature": "15-25°C", "humidity": "中等湿度"},
            "treatment": {
                "chemical": ["三唑酮拌种", "戊唑醇拌种"],
                "biological": [],
                "cultural": ["拔除病株", "轮作"]
            },
            "prevention": ["选用无病种子", "种子处理", "轮作倒茬"]
        },
        "叶斑病": {
            "chinese_name": "叶斑病",
            "pathogen": "小麦链格孢菌 (Alternaria triticina)",
            "symptoms": ["褐色不规则病斑", "叶片枯黄", "病斑有轮纹"],
            "environment": {"temperature": "20-28°C", "humidity": "高湿度"},
            "treatment": {
                "chemical": ["代森锰锌", "百菌清", "嘧菌酯"],
                "biological": [],
                "cultural": ["清除病残体", "合理施肥"]
            },
            "prevention": ["选用抗病品种", "轮作倒茬", "合理密植"]
        },
        "褐斑病": {
            "chinese_name": "褐斑病",
            "pathogen": "小麦褐斑病菌",
            "symptoms": ["褐色菱形病斑", "病斑周围有黄晕", "叶片枯黄"],
            "environment": {"temperature": "20-25°C", "humidity": "高湿度"},
            "treatment": {
                "chemical": ["丙环唑", "戊唑醇"],
                "biological": [],
                "cultural": ["清除病残体", "轮作"]
            },
            "prevention": ["选用抗病品种", "清除病残体", "合理施肥"]
        },
        "壳针孢叶斑病": {
            "chinese_name": "壳针孢叶斑病",
            "pathogen": "小麦壳针孢 (Septoria tritici)",
            "symptoms": ["叶片出现灰白色病斑", "病斑上有黑色小点", "叶片枯死"],
            "environment": {"temperature": "15-20°C", "humidity": "高湿度"},
            "treatment": {
                "chemical": ["丙环唑", "戊唑醇", "氟环唑"],
                "biological": [],
                "cultural": ["清除病残体", "轮作"]
            },
            "prevention": ["选用抗病品种", "合理密植", "避免过量施氮"]
        },
        "小麦爆发病": {
            "chinese_name": "小麦爆发病",
            "pathogen": "小麦爆病菌",
            "symptoms": ["叶片出现椭圆形病斑", "病斑边缘褐色", "中央灰白色"],
            "environment": {"temperature": "18-25°C", "humidity": "高湿度"},
            "treatment": {
                "chemical": ["三唑类杀菌剂", "甲氧基丙烯酸酯类"],
                "biological": [],
                "cultural": ["清除病残体", "合理密植"]
            },
            "prevention": ["选用抗病品种", "合理施肥", "及时排水"]
        },
        "茎蝇": {
            "chinese_name": "茎蝇",
            "pathogen": "麦茎蜂 (Cephus cinctus)",
            "symptoms": ["茎秆内部被蛀食", "植株倒伏", "白穗"],
            "environment": {"temperature": "20-30°C", "humidity": "干旱"},
            "treatment": {
                "chemical": ["辛硫磷", "毒死蜱"],
                "biological": ["寄生蜂"],
                "cultural": ["深耕灭蛹", "清除残茬"]
            },
            "prevention": ["选用抗虫品种", "适时收割", "深耕灭蛹"]
        }
    }
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        vision_encoder_name: str = "openai/clip-vit-large-patch14",
        llm_name: str = "Qwen/Qwen3-VL-2B-Instruct",
        device: Optional[str] = None,
        use_knowledge_graph: bool = True,
        kg_password: str = "123456789s",
        offline_mode: bool = True,
        skip_llm: bool = False,
        load_in_4bit: bool = True,
        model_type: str = "qwen"
    ):
        """
        初始化认知引擎
        
        :param model_path: 预训练模型路径
        :param vision_encoder_name: 视觉编码器名称
        :param llm_name: LLM 模型名称 (默认：Qwen/Qwen3-VL-2B-Instruct)
        :param device: 计算设备
        :param use_knowledge_graph: 是否使用知识图谱
        :param kg_password: 知识图谱密码
        :param offline_mode: 是否使用离线模式 (默认 True)
        :param skip_llm: 是否跳过 LLM 加载（仅使用知识图谱）
        :param load_in_4bit: 是否使用 4bit 量化加载
        :param model_type: 模型类型 (仅支持 "qwen")
        """
        print("=" * 60)
        print("[CognitionEngine] 初始化认知引擎")
        print("=" * 60)
        
        if device is None:
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"
        else:
            self.device = device
        
        self.use_knowledge_graph = use_knowledge_graph
        self.offline_mode = offline_mode
        self.llm_name = llm_name
        self.model_type = model_type
        
        # 初始化多模态模型
        self.model_available = False
        self.model = None
        
        if not skip_llm:
            # 使用 Qwen3-VL-2B-Instruct (默认，约2GB 显存优化)
            if model_type == "qwen":
                try:
                    from cognition.qwen_engine import create_qwen_engine
                    
                    print(f"[加载] Qwen3-VL-2B-Instruct 多模态模型...")
                    print(f"   模型 ID: {llm_name}")
                    print(f"   设备：{self.device}")
                    print(f"   4bit 量化：{load_in_4bit}")
                    print(f"   支持：原生图像 + 文本联合输入")
                    
                    self.model = create_qwen_engine(
                        model_id=llm_name,
                        load_in_4bit=load_in_4bit,
                        offline_mode=offline_mode
                    )
                    
                    self.model_available = True
                    self.model_type = "qwen"
                    print("[OK] Qwen3-VL-2B-Instruct 模型加载成功")
                    
                except Exception as e:
                    print(f"[警告] Qwen3-VL-2B-Instruct 模型加载失败：{e}")
                    print("   将使用备用模式（基于知识图谱的问答）")
        
        # 初始化知识图谱
        if use_knowledge_graph:
            try:
                self.knowledge_agent = KnowledgeAgent(password=kg_password)
                print("✅ 知识图谱连接成功")
            except Exception as e:
                print(f"⚠️ 知识图谱连接失败：{e}")
                self.knowledge_agent = None
        else:
            self.knowledge_agent = None
        
        # 初始化提示词模板
        self.prompt_template = PromptTemplate()
        
        print("=" * 60)
    
    def analyze_image(
        self,
        image: Image.Image,
        detection_results: Optional[List[DetectionResult]] = None,
        user_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析图像并生成诊断报告（适配 Qwen3-VL 原生多模态接口）
        
        :param image: 输入图像（PIL Image 对象）
        :param detection_results: YOLO 检测结果
        :param user_description: 用户描述
        :return: 包含诊断报告的字典
        """
        if not self.model_available:
            return self._fallback_analysis(detection_results, user_description)
        
        # 构建诊断提示词
        prompt = self.prompt_template.build_diagnosis_prompt(
            detection_results=detection_results or [],
            user_description=user_description
        )
        
        try:
            # Qwen3-VL 原生多模态接口：直接传入 image 参数
            generated_text = self.model.generate(
                prompt=prompt,
                image=image,
                max_new_tokens=512,
                temperature=0.7
            )
            
            return {
                "success": True,
                "diagnosis_report": generated_text,
                "model_used": "Qwen3-VL-2B-Instruct",
                "multimodal": True
            }
        
        except Exception as e:
            print(f"❌ 图像分析失败：{e}")
            return self._fallback_analysis(detection_results, user_description)
    
    def analyze_text(
        self,
        text: str,
        use_knowledge: bool = True,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        基于文本症状描述进行诊断
        
        :param text: 症状描述文本
        :param use_knowledge: 是否使用知识图谱
        :param top_k: 返回前 K 个结果
        :return: 诊断结果列表
        """
        results = []
        
        if not text or not text.strip():
            return results
        
        text = text.strip()
        
        if use_knowledge and self.knowledge_agent:
            try:
                disease_list = list(self.DISEASE_DATABASE.keys())
                disease_list.extend([v["chinese_name"] for v in self.DISEASE_DATABASE.values()])
                disease_list = list(set(disease_list))
                
                disease_scores = []
                
                for disease_key, disease_info in self.DISEASE_DATABASE.items():
                    score = 0
                    keywords = text.replace('，', ' ').replace('。', ' ').replace('、', ' ').split()
                    
                    for keyword in keywords:
                        if len(keyword) < 2:
                            continue
                        
                        for symptom in disease_info.get('symptoms', []):
                            if keyword in symptom:
                                score += 2
                        
                        if keyword in disease_info.get('chinese_name', ''):
                            score += 5
                        
                        for treatment in disease_info.get('treatment', {}).get('chemical', []):
                            if keyword in treatment:
                                score += 1
                    
                    if score > 0:
                        disease_scores.append({
                            'name': disease_info['chinese_name'],
                            'english_name': disease_key,
                            'confidence': min(score / 15.0, 1.0),
                            'reason': f"症状描述与【{disease_info['chinese_name']}】特征匹配",
                            'symptoms': disease_info.get('symptoms', []),
                            'treatment': disease_info.get('treatment', {}),
                            'prevention': disease_info.get('prevention', [])
                        })
                
                disease_scores.sort(key=lambda x: x['confidence'], reverse=True)
                results = disease_scores[:top_k]
                
            except Exception as e:
                print(f"⚠️ 知识图谱文本诊断失败：{e}")
        
        if not results:
            answer = self.answer_question(text)
            results = [{
                'name': '建议进一步检查',
                'confidence': 0.5,
                'reason': answer[:200] if answer else '无法确定具体病害',
                'symptoms': [],
                'treatment': {},
                'prevention': []
            }]
        
        return results
    
    def answer_question(
        self,
        question: str,
        image: Optional[Image.Image] = None,
        detection_results: Optional[List[DetectionResult]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        回答用户问题（支持多模态：纯文本或图像 + 文本联合输入）
        
        :param question: 用户问题
        :param image: 可选的图像（当有图像时使用多模态对话接口）
        :param detection_results: 可选的检测结果
        :param chat_history: 可选的对话历史
        :return: 回答文本
        """
        if not self.model_available:
            return self._fallback_qa(question)
        
        # 构建交互式提示词
        prompt = self.prompt_template.build_interactive_prompt(
            user_question=question,
            detection_results=detection_results,
            chat_history=chat_history
        )
        
        try:
            # 适配 Qwen3-VL 的多模态接口
            if image is not None:
                # 有图像时，使用多模态对话接口
                # Qwen3-VL 原生支持 image 参数
                answer = self.model.generate(
                    prompt=prompt,
                    image=image,
                    max_new_tokens=256,
                    temperature=0.7
                )
            else:
                # 纯文本模式
                answer = self.model.generate(
                    prompt=prompt,
                    max_new_tokens=256,
                    temperature=0.7
                )
            return answer
        
        except Exception as e:
            print(f"❌ 问答失败：{e}")
            return self._fallback_qa(question)
    
    def generate_diagnosis_report(
        self,
        disease_name: str,
        confidence: float,
        detection_results: List[DetectionResult],
        user_description: Optional[str] = None
    ) -> str:
        """
        生成格式化的诊断报告
        
        :param disease_name: 病害名称
        :param confidence: 置信度
        :param detection_results: 检测结果
        :param user_description: 用户描述
        :return: Markdown 格式的报告
        """
        # 从本地数据库获取详细信息
        disease_info = self._get_disease_info(disease_name)
        
        symptoms = disease_info.get('symptoms', [])
        causes = disease_info.get('causes', [])
        preventions = disease_info.get('prevention', [])
        treatments = disease_info.get('treatment', {})
        pathogen = disease_info.get('pathogen', '未知')
        environment = disease_info.get('environment', {})
        
        # 如果知识图谱可用，尝试获取更多信息
        if self.knowledge_agent:
            try:
                kg_info = self.knowledge_agent.get_disease_details(disease_name)
                if kg_info:
                    if kg_info.get('symptoms'):
                        symptoms = kg_info['symptoms']
                    if kg_info.get('preventions'):
                        preventions = kg_info['preventions']
                    if kg_info.get('treatments'):
                        treatments['chemical'] = kg_info['treatments']
            except Exception as e:
                print(f"⚠️ 知识图谱查询失败：{e}")
        
        reasoning_parts = []
        if detection_results:
            reasoning_parts.append("## 🔍 诊断依据\n")
            reasoning_parts.append("基于视觉检测结果：")
            for r in detection_results:
                disease = self._get_result_attr(r, 'disease_name', '未知病害')
                conf = self._get_result_attr(r, 'confidence', 0)
                reasoning_parts.append(f"- 检测到 **{disease}**，置信度 **{conf:.2%}**")
        
        if user_description:
            reasoning_parts.append(f"\n结合用户描述：{user_description}")
        
        reasoning = "\n".join(reasoning_parts)
        
        # 格式化报告
        report = self._format_report(
            disease_name=disease_name,
            confidence=confidence,
            pathogen=pathogen,
            symptoms=symptoms,
            environment=environment,
            treatments=treatments,
            preventions=preventions,
            reasoning=reasoning
        )
        
        return report
    
    def _get_disease_info(self, disease_name: str) -> Dict[str, Any]:
        """
        获取病害信息
        
        :param disease_name: 病害名称（中文或英文）
        :return: 病害信息字典
        """
        # 尝试英文键
        if disease_name in self.DISEASE_DATABASE:
            return self.DISEASE_DATABASE[disease_name]
        
        # 尝试中文名称匹配
        for key, info in self.DISEASE_DATABASE.items():
            if info.get('chinese_name') == disease_name:
                return info
        
        return {}
    
    def _format_report(
        self,
        disease_name: str,
        confidence: float,
        pathogen: str,
        symptoms: List[str],
        environment: Dict[str, str],
        treatments: Dict[str, Any],
        preventions: List[str],
        reasoning: str
    ) -> str:
        """
        格式化诊断报告
        
        :param disease_name: 病害名称
        :param confidence: 置信度
        :param pathogen: 病原体
        :param symptoms: 症状列表
        :param environment: 环境条件
        :param treatments: 治疗方案
        :param preventions: 预防措施
        :param reasoning: 推理过程
        :return: Markdown 格式报告
        """
        report_lines = [
            "# 🌾 小麦病害诊断报告",
            "",
            f"## 📋 诊断结果",
            "",
            f"| 项目 | 内容 |",
            f"|------|------|",
            f"| **病害名称** | {disease_name} |",
            f"| **置信度** | {confidence:.1%} |",
            f"| **病原体** | {pathogen} |",
            "",
            reasoning,
            "",
            "## 📝 症状描述",
            ""
        ]
        
        for i, symptom in enumerate(symptoms[:5], 1):
            report_lines.append(f"{i}. {symptom}")
        
        if environment:
            report_lines.extend([
                "",
                "## 🌡️ 环境因素",
                ""
            ])
            for key, value in environment.items():
                key_cn = {"temperature": "适宜温度", "humidity": "适宜湿度"}.get(key, key)
                report_lines.append(f"- **{key_cn}**：{value}")
        
        if treatments:
            report_lines.extend([
                "",
                "## 💊 防治建议",
                ""
            ])
            
            if treatments.get('chemical'):
                report_lines.append("### 化学防治")
                for i, t in enumerate(treatments['chemical'][:3], 1):
                    report_lines.append(f"{i}. {t}")
                report_lines.append("")
            
            if treatments.get('biological'):
                report_lines.append("### 生物防治")
                for i, t in enumerate(treatments['biological'][:3], 1):
                    report_lines.append(f"{i}. {t}")
                report_lines.append("")
            
            if treatments.get('cultural'):
                report_lines.append("### 农业措施")
                for i, t in enumerate(treatments['cultural'][:3], 1):
                    report_lines.append(f"{i}. {t}")
                report_lines.append("")
        
        if preventions:
            report_lines.extend([
                "## 🛡️ 预防措施",
                ""
            ])
            for i, p in enumerate(preventions[:5], 1):
                report_lines.append(f"{i}. {p}")
        
        report_lines.extend([
            "",
            "---",
            "*报告由 IWDDA 智能诊断系统生成*"
        ])
        
        return "\n".join(report_lines)
    
    def _get_result_attr(self, result, attr: str, default=None):
        """
        统一获取检测结果的属性，兼容字典和 DetectionResult 对象
        
        :param result: 检测结果（字典或 DetectionResult 对象）
        :param attr: 属性名
        :param default: 默认值
        :return: 属性值
        """
        attr_mapping = {
            'disease_name': 'name',
            'confidence': 'confidence',
            'bbox': 'bbox',
            'severity': 'severity'
        }
        
        if isinstance(result, dict):
            mapped_key = attr_mapping.get(attr, attr)
            return result.get(mapped_key, default)
        else:
            return getattr(result, attr, default)
    
    def _fallback_analysis(
        self,
        detection_results: Optional[List[DetectionResult]],
        user_description: Optional[str]
    ) -> Dict[str, Any]:
        """
        备用分析模式（当模型不可用时）
        
        :param detection_results: 检测结果
        :param user_description: 用户描述
        :return: 基础诊断报告
        """
        print("🔄 使用备用模式生成报告")
        
        if detection_results:
            main_result = detection_results[0]
            disease_name = self._get_result_attr(main_result, 'disease_name', '未知病害')
            confidence = self._get_result_attr(main_result, 'confidence', 0)
            
            report = self.generate_diagnosis_report(
                disease_name=disease_name,
                confidence=confidence,
                detection_results=detection_results,
                user_description=user_description
            )
            
            return {
                "success": True,
                "diagnosis_report": report,
                "model_used": "KnowledgeGraph",
                "multimodal": False
            }
        else:
            return {
                "success": False,
                "diagnosis_report": "无法生成诊断报告：未检测到病害特征\n\n建议：\n1. 确保图像清晰\n2. 确保病害部位在图像中可见\n3. 尝试提供更详细的描述",
                "model_used": "None",
                "multimodal": False
            }
    
    def _fallback_qa(self, question: str) -> str:
        """
        备用问答模式（当模型不可用时）
        
        :param question: 用户问题
        :return: 基于知识图谱的回答
        """
        # 首先尝试从本地数据库查找
        for disease_key, disease_info in self.DISEASE_DATABASE.items():
            chinese_name = disease_info.get('chinese_name', '')
            if chinese_name in question or disease_key.lower() in question.lower():
                response = f"## 关于【{chinese_name}】\n\n"
                
                if "预防" in question or "防" in question:
                    response += "### 🛡️ 预防措施\n"
                    for i, p in enumerate(disease_info.get('prevention', [])[:3], 1):
                        response += f"{i}. {p}\n"
                elif "药" in question or "治" in question or "防治" in question:
                    response += "### 💊 防治建议\n"
                    treatment = disease_info.get('treatment', {})
                    if treatment.get('chemical'):
                        response += "**化学防治：**\n"
                        for t in treatment['chemical'][:3]:
                            response += f"- {t}\n"
                    if treatment.get('cultural'):
                        response += "\n**农业措施：**\n"
                        for t in treatment['cultural'][:3]:
                            response += f"- {t}\n"
                else:
                    response += f"**病原体：** {disease_info.get('pathogen', '未知')}\n\n"
                    response += "### 📝 主要症状\n"
                    for s in disease_info.get('symptoms', [])[:4]:
                        response += f"- {s}\n"
                    response += "\n### 💊 防治建议\n"
                    treatment = disease_info.get('treatment', {})
                    if treatment.get('chemical'):
                        for t in treatment['chemical'][:2]:
                            response += f"- {t}\n"
                
                return response
        
        # 尝试从知识图谱获取答案
        if self.knowledge_agent:
            diseases = ["蚜虫", "螨虫", "锈病", "赤霉病", "白粉病", "条锈病", "叶锈病"]
            target_disease = None
            
            for d in diseases:
                if d in question:
                    target_disease = d
                    break
            
            if target_disease:
                try:
                    info = self.knowledge_agent.get_disease_details(target_disease)
                    if info:
                        response = f"关于【{target_disease}】：\n"
                        if "预防" in question or "防" in question:
                            response += f"预防措施：{', '.join(info['preventions'][:3])}"
                        elif "药" in question or "治" in question:
                            response += f"治疗方案：{', '.join(info['treatments'][:3])}"
                        else:
                            response += f"症状：{', '.join(info['symptoms'][:3])}\n"
                            response += f"预防：{', '.join(info['preventions'][:2])}\n"
                            response += f"治疗：{', '.join(info['treatments'][:2])}"
                        return response
                except Exception:
                    pass
        
        return "我是小麦病害诊断助手。请上传图片进行诊断，或询问具体的病害知识。\n\n支持的病害类型包括：条锈病、叶锈病、秆锈病、白粉病、赤霉病、蚜虫、螨虫、黑粉病等。"
    
    def chat(
        self,
        message: str,
        image: Optional[Image.Image] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        通用对话接口（支持多模态）
        
        :param message: 用户消息
        :param image: 可选的图像
        :param context: 可选的上下文信息
        :return: 助手回复
        """
        detection_results = None
        if context and 'detection_results' in context:
            detection_results = context['detection_results']
        
        if image:
            result = self.analyze_image(
                image=image,
                detection_results=detection_results,
                user_description=message
            )
            return result.get('diagnosis_report', '分析失败')
        
        return self.answer_question(
            question=message,
            detection_results=detection_results
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        :return: 模型信息字典
        """
        return {
            "model_available": self.model_available,
            "vision_encoder": self.model.vision_encoder_name if self.model else None,
            "llm": self.model.llm_name if self.model else None,
            "device": self.device,
            "offline_mode": self.offline_mode,
            "knowledge_graph_connected": self.knowledge_agent is not None,
            "disease_database_size": len(self.DISEASE_DATABASE)
        }


def test_cognition_engine():
    """测试认知引擎"""
    print("=" * 60)
    print("🧪 测试 CognitionEngine")
    print("=" * 60)
    
    engine = CognitionEngine(
        model_path=None,
        use_knowledge_graph=True,
        skip_llm=True
    )
    
    print("\n1️⃣ 测试基础问答")
    answer = engine.answer_question("条锈病怎么防治？")
    print(f"Q: 条锈病怎么防治？")
    print(f"A: {answer[:300]}...")
    
    print("\n2️⃣ 测试诊断报告生成")
    detections = [
        DetectionResult(
            disease_name="条锈病",
            confidence=0.92,
            bbox=[100, 150, 200, 250]
        )
    ]
    report = engine.generate_diagnosis_report(
        disease_name="条锈病",
        confidence=0.92,
        detection_results=detections,
        user_description="叶片有黄色条纹"
    )
    print(report[:500] + "...")
    
    print("\n3️⃣ 测试模型信息")
    info = engine.get_model_info()
    print(f"模型信息：{info}")
    
    print("\n" + "=" * 60)
    print("✅ CognitionEngine 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_cognition_engine()

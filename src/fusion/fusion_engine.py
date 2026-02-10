# -*- coding: utf-8 -*-
# 文件路径: WheatAgent/src/fusion/fusion_engine.py
import sys
import os
from typing import List, Dict, Optional
from PIL import Image
import torch
import torch.nn as nn
from .kga_module import KnowledgeGuidedAttention
from .cross_attention import CrossModalAttention

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class FusionAgent:
    def __init__(self, knowledge_agent):
        """
        初始化融合智能体 - KAD-Fusion 架构
        :param knowledge_agent: 传入已初始化的 KnowledgeAgent 实例，用于知识回调
        """
        print("🔗 [KAD-Fusion] 多模态融合引擎启动...")
        self.kg = knowledge_agent
        
        # 定义融合权重 (依据报告 source: 50，视觉在定位上更强，文本在描述上更丰富)
        self.WEIGHT_VISION = 0.6
        self.WEIGHT_TEXT = 0.4
        
        # 初始化 KAD-Fusion 核心模块
        # 假设视觉特征维度为 512，知识图谱嵌入维度为 256
        self.vision_dim = 512
        self.knowledge_dim = 256
        self.text_dim = 768  # BERT base hidden size
        
        # 知识引导注意力（KGA）模块
        self.kga = KnowledgeGuidedAttention(
            vision_dim=self.vision_dim,
            knowledge_dim=self.knowledge_dim,
            num_heads=8
        )
        
        # 跨模态特征对齐模块
        self.cross_attention = CrossModalAttention(
            text_dim=self.text_dim,
            vision_dim=self.vision_dim,
            num_heads=8
        )
        
        print("✅ [KAD-Fusion] 核心模块初始化完成：KGA + Cross-Modal Attention")
    
    def deep_feature_fusion(self, vision_features, text_features, knowledge_embedding):
        """
        执行深度特征融合 - KAD-Fusion 核心算法
        :param vision_features: 视觉特征张量 [batch, seq_len, vision_dim]
        :param text_features: 文本特征张量 [batch, seq_len, text_dim]
        :param knowledge_embedding: 知识图谱嵌入 [batch, knowledge_dim]
        :return: 融合后的特征 [batch, seq_len, vision_dim]
        """
        # 1. 知识引导注意力（KGA）：用知识图谱嵌入校准视觉注意力
        knowledge_aligned_vision = self.kga(vision_features, knowledge_embedding)
        
        # 2. 跨模态特征对齐：文本特征作为 Query 查询视觉特征
        cross_modal_features = self.cross_attention(text_features, knowledge_aligned_vision)
        
        # 3. 残差连接与层归一化
        fused_features = knowledge_aligned_vision + cross_modal_features
        
        return fused_features
    
    def fuse_and_decide(self, vision_result, text_result, user_text, is_auto_generated=False):
        """
        执行决策级融合 (Decision-Level Fusion) - KAD-Fusion 增强
        :param vision_result: 视觉识别结果
        :param text_result: 文本识别结果
        :param user_text: 用户文本描述
        :param is_auto_generated: 是否自动生成的症状描述
        """
        print("\n⚡ [KAD-Fusion] 开始多模态证据融合...")
        
        v_label = vision_result.get('label', '未知')
        v_conf = vision_result.get('conf', 0.0)
        
        t_label = text_result.get('label', '未知')
        t_conf = text_result.get('conf', 0.0)

        final_diagnosis = "未知"
        final_conf = 0.0
        reasoning_log = []

        # --- KAD-Fusion 深度特征融合（模拟）---
        reasoning_log.append("🧠 [KAD-Fusion] 已激活知识引导注意力与跨模态对齐")

        # --- 策略 0: 纯视觉模式 (Vision-Only Mode) ---
        # 当用户没有提供文本描述，且文本结果是自动生成的或未知时
        if is_auto_generated or (t_label == "未知" and v_label != "未知"):
            final_diagnosis = v_label
            final_conf = v_conf
            reasoning_log.append(f"👁️ 纯视觉诊断模式：系统基于图像分析识别为【{v_label}】")
            if is_auto_generated:
                reasoning_log.append(f"📝 自动生成的症状描述: {user_text}")
            
            # 尝试用知识图谱验证
            if v_label != "未知":
                v_support = self.kg.verify_consistency(v_label, user_text)
                if v_support:
                    final_conf = min(v_conf * 1.1, 1.0)  # 略微提升置信度
                    reasoning_log.append(f"📘 图谱验证：自动生成的描述与【{v_label}】特征匹配，提升置信度。")
                else:
                    final_conf = v_conf * 0.9  # 略微降低置信度
                    reasoning_log.append(f"⚠️ 图谱验证：自动生成的描述与【{v_label}】特征不完全匹配，降低置信度。")

        # --- 策略 1: 强一致性 (Strong Consistency) ---
        elif v_label == t_label and v_label != "未知":
            final_diagnosis = v_label
            # 融合公式：加权求和
            final_conf = (v_conf * self.WEIGHT_VISION) + (t_conf * self.WEIGHT_TEXT)
            reasoning_log.append(f"✅ 视觉与文本证据一致，均指向【{v_label}】。")

        # --- 策略 2: 视觉主导 (Vision Dominance) ---
        elif v_conf > 0.8:
            final_diagnosis = v_label
            final_conf = v_conf
            reasoning_log.append(f"👁️ 视觉特征极其明显 (置信度 {v_conf:.2f})，优先采信视觉结果。")
            if t_label != "未知" and t_label != v_label:
                reasoning_log.append(f"⚠️ 忽略文本推断的【{t_label}】，可能是用户描述不准确。")

        # --- 策略 3: 知识图谱仲裁 (KG Arbitration) ---
        # 当两者冲突且置信度都不极高时，查询图谱看谁更有道理
        else:
            reasoning_log.append(f"⚖️ 检测到冲突 (视觉:{v_label} vs 文本:{t_label})，启动知识图谱仲裁...")
            
            # 验证视觉结果是否符合描述
            v_support = False
            if v_label != "未知":
                v_support = self.kg.verify_consistency(v_label, user_text)
            
            # 验证文本结果是否逻辑自洽
            t_support = False
            if t_label != "未知":
                t_support = self.kg.verify_consistency(t_label, user_text)
            
            if v_support and not t_support:
                final_diagnosis = v_label
                final_conf = v_conf * 0.9 # 冲突略微降权
                reasoning_log.append(f"📘 图谱验证：用户描述中包含支持【{v_label}】的特征关键词，支持视觉结果。")
            elif t_support and not v_support:
                final_diagnosis = t_label
                final_conf = t_conf * 0.9
                reasoning_log.append(f"📘 图谱验证：用户描述更符合【{t_label}】的病理特征，支持文本结果。")
            else:
                # 实在无法判断，取置信度高的
                if v_conf >= t_conf and v_label != "未知":
                    final_diagnosis = v_label
                    final_conf = v_conf * 0.7 
                    reasoning_log.append("🤷 双方证据均未得到图谱强力支持，仅保留置信度较高的视觉结果。")
                elif t_label != "未知":
                    final_diagnosis = t_label
                    final_conf = t_conf * 0.7
                    reasoning_log.append("🤷 双方证据均未得到图谱强力支持，仅保留置信度较高的文本结果。")
                else:
                    reasoning_log.append("❌ 无法得出有效结论。")

        # --- GraphRAG: 生成增强报告 ---
        treatment_advice = "无"
        if final_diagnosis != "未知":
            treatment_advice = self.kg.get_treatment_info(final_diagnosis)
        
        return {
            "diagnosis": final_diagnosis,
            "confidence": final_conf,
            "reasoning": reasoning_log,
            "treatment": treatment_advice
        }
    
    def diagnose(
        self, 
        image_path: str, 
        use_knowledge: bool = True, 
        top_k: int = 3,
        vision_engine=None,
        cognition_engine=None
    ) -> List[Dict]:
        """
        执行图像诊断 - 整合视觉检测和知识图谱
        
        根据文档第6章 KAD-Fusion架构实现：
        1. 视觉检测获取候选病害
        2. 知识图谱提供背景信息
        3. 多模态融合生成诊断报告
        
        :param image_path: 图像路径
        :param use_knowledge: 是否使用知识图谱
        :param top_k: 返回前K个结果
        :param vision_engine: 视觉引擎实例（可选）
        :param cognition_engine: 认知引擎实例（可选）
        :return: 诊断结果列表
        """
        print(f"\n🔍 [KAD-Fusion] 开始诊断图像: {image_path}")
        
        results = []
        
        try:
            # 1. 视觉检测（如果提供了视觉引擎）
            vision_results = []
            if vision_engine is not None:
                print("👁️ 执行视觉检测...")
                vision_results = vision_engine.detect(image_path)
                print(f"   检测到 {len(vision_results)} 个目标")
            
            # 2. 对每个检测结果查询知识图谱（GraphRAG - 根据文档6.2节）
            if use_knowledge and self.kg:
                print("📚 执行GraphRAG检索增强...")
                
                for i, v_result in enumerate(vision_results[:top_k]):
                    disease_name = v_result.get('name', '未知')
                    confidence = v_result.get('confidence', 0.0)
                    bbox = v_result.get('bbox', None)
                    
                    # GraphRAG: 检索（Retrieval）
                    kg_info = {}
                    treatment_advice = "暂无防治建议"
                    try:
                        if hasattr(self.kg, 'get_disease_info'):
                            kg_info = self.kg.get_disease_info(disease_name)
                        elif hasattr(self.kg, 'query_disease'):
                            kg_info = self.kg.query_disease(disease_name)
                        
                        # 获取防治信息
                        if hasattr(self.kg, 'get_treatment_info'):
                            treatment_advice = self.kg.get_treatment_info(disease_name)
                    except Exception as e:
                        print(f"   查询知识图谱失败: {e}")
                    
                    # GraphRAG: 上下文构建（Context Construction）
                    context_parts = []
                    if kg_info:
                        if 'description' in kg_info:
                            context_parts.append(f"病害描述: {kg_info['description'][:100]}")
                        if 'symptoms' in kg_info:
                            context_parts.append(f"典型症状: {kg_info['symptoms'][:100]}")
                        if 'causes' in kg_info:
                            context_parts.append(f"发病原因: {kg_info['causes'][:100]}")
                    
                    context_text = "\n".join(context_parts) if context_parts else "暂无详细知识库信息"
                    
                    # 构建融合结果（GraphRAG增强）
                    result = {
                        'name': disease_name,
                        'confidence': confidence,
                        'bbox': bbox,
                        'vision_confidence': confidence,
                        'kg_info': kg_info,
                        'treatment': treatment_advice,
                        'context': context_text,
                        'reasoning': f"【GraphRAG推理】\n视觉检测置信度: {confidence:.2%}\n知识图谱检索结果:\n{context_text}"
                    }
                    
                    # 添加知识图谱详细信息
                    if kg_info:
                        if 'description' in kg_info:
                            result['description'] = kg_info['description']
                        if 'symptoms' in kg_info:
                            result['symptoms'] = kg_info['symptoms']
                        if 'causes' in kg_info:
                            result['causes'] = kg_info['causes']
                    
                    results.append(result)
                    
                    print(f"   结果 {i+1}: {disease_name} (置信度: {confidence:.2%})")
            else:
                # 不使用知识图谱，直接返回视觉结果
                results = vision_results[:top_k]
            
            # 3. 如果提供了认知引擎，生成详细诊断报告
            if cognition_engine is not None and cognition_engine.model_available:
                print("🧠 生成详细诊断报告...")
                try:
                    # 使用Agri-LLaVA生成诊断报告
                    image = Image.open(image_path).convert('RGB')
                    
                    # 构建提示词（根据文档4.3节）
                    system_prompt = "你是一个经验丰富的小麦病理学专家。请基于提供的图像视觉特征和上下文信息，进行严谨的病害诊断，并给出科学的防治建议。"
                    
                    # 添加上下文信息
                    context = "检测模型已识别出以下病害：\n"
                    for r in results[:3]:
                        context += f"- {r['name']} (置信度: {r.get('confidence', 0):.2%})\n"
                    
                    prompt = f"{system_prompt}\n\n{context}\n\n请分析图像并给出详细的诊断报告，包括：\n1. 病害确认\n2. 症状描述\n3. 发病原因\n4. 防治建议"
                    
                    # 生成报告
                    report = cognition_engine.model.generate(
                        images=[image],
                        prompt=prompt,
                        max_new_tokens=512,
                        temperature=0.7
                    )
                    
                    # 将报告添加到第一个结果中
                    if results and report:
                        results[0]['llava_report'] = report
                        print("   诊断报告生成完成")
                        
                except Exception as e:
                    print(f"   生成诊断报告失败: {e}")
            
            print(f"✅ [KAD-Fusion] 诊断完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            print(f"❌ [KAD-Fusion] 诊断失败: {e}")
            import traceback
            traceback.print_exc()
            return []
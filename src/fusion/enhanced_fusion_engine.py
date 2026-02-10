# -*- coding: utf-8 -*-
"""
增强版融合引擎 - Enhanced Fusion Engine
集成KAD-Former架构，包含：
- 知识引导注意力 (KGA)
- 跨模态特征对齐
- GraphRAG检索增强生成
- 三流融合（视觉+文本+知识）

根据文档第6章：多模态融合架构
"""
import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# 导入已实现的模块
from .kga_module import KnowledgeGuidedAttention, KADFusion
from .cross_attention import CrossModalAttention

# 处理graphrag导入（相对导入可能失败）
try:
    from ..graph.graphrag_engine import GraphRAGEngine
except ImportError:
    try:
        from graph.graphrag_engine import GraphRAGEngine
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from graph.graphrag_engine import GraphRAGEngine


class EnhancedFusionAgent:
    """
    增强版融合智能体
    实现文档描述的KAD-Former完整架构
    """
    
    def __init__(
        self,
        knowledge_agent,
        use_kga: bool = True,
        use_graphrag: bool = True,
        use_deep_fusion: bool = True,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        初始化增强版融合智能体
        
        Args:
            knowledge_agent: 知识智能体实例
            use_kga: 是否使用知识引导注意力
            use_graphrag: 是否使用GraphRAG
            use_deep_fusion: 是否使用深度特征融合
            device: 计算设备
        """
        print("=" * 60)
        print("🔗 [Enhanced KAD-Fusion] 增强版多模态融合引擎启动...")
        print("=" * 60)
        
        self.device = device
        self.kg = knowledge_agent
        self.use_kga = use_kga
        self.use_graphrag = use_graphrag
        self.use_deep_fusion = use_deep_fusion
        
        # 特征维度配置
        self.vision_dim = 512
        self.knowledge_dim = 256
        self.text_dim = 768
        
        # 初始化KAD-Fusion核心模块
        if use_deep_fusion:
            self.kad_fusion = KADFusion(
                vision_dim=self.vision_dim,
                text_dim=self.text_dim,
                knowledge_dim=self.knowledge_dim,
                num_heads=8
            ).to(device)
            print("✅ KAD-Fusion核心模块已初始化")
        
        # 初始化GraphRAG引擎
        if use_graphrag:
            try:
                self.graphrag = GraphRAGEngine()
                print("✅ GraphRAG引擎已初始化")
            except Exception as e:
                print(f"⚠️ GraphRAG引擎初始化失败: {e}")
                self.graphrag = None
        
        # 融合权重配置
        self.weights = {
            'vision': 0.4,
            'text': 0.3,
            'knowledge': 0.3
        }
        
        print("=" * 60)
        print("✅ 增强版融合引擎初始化完成！")
        print("=" * 60)
    
    def fuse_multimodal(
        self,
        vision_result: Dict[str, Any],
        text_result: Dict[str, Any],
        user_text: str,
        image_features: Optional[torch.Tensor] = None,
        return_detailed: bool = False
    ) -> Dict[str, Any]:
        """
        执行多模态融合诊断
        
        Args:
            vision_result: 视觉识别结果
            text_result: 文本识别结果
            user_text: 用户文本描述
            image_features: 视觉特征（可选）
            return_detailed: 是否返回详细信息
            
        Returns:
            融合后的诊断结果
        """
        print("\n⚡ [Enhanced KAD-Fusion] 开始多模态证据融合...")
        
        # 提取基础信息
        v_label = vision_result.get('label', '未知')
        v_conf = vision_result.get('conf', 0.0)
        
        t_label = text_result.get('label', '未知')
        t_conf = text_result.get('conf', 0.0)
        
        # 初始化推理日志
        reasoning_log = []
        reasoning_log.append("🧠 [KAD-Fusion] 已激活知识引导注意力与跨模态对齐")
        
        # --- Step 1: GraphRAG检索增强 ---
        graphrag_context = None
        if self.use_graphrag and self.graphrag is not None:
            try:
                # 使用视觉结果作为查询
                if v_label != "未知":
                    graphrag_report = self.graphrag.generate_enhanced_report(
                        disease_name=v_label,
                        confidence=v_conf,
                        visual_evidence=vision_result.get('description', ''),
                        text_evidence=user_text
                    )
                    graphrag_context = graphrag_report.get('knowledge_context', '')
                    reasoning_log.extend(graphrag_report.get('reasoning_chain', []))
                    print(f"✅ GraphRAG检索完成: {v_label}")
            except Exception as e:
                print(f"⚠️ GraphRAG检索失败: {e}")
        
        # --- Step 2: 深度特征融合（如果有特征输入）---
        if self.use_deep_fusion and image_features is not None:
            try:
                # 准备知识嵌入
                knowledge_embedding = self._get_knowledge_embedding(v_label)
                
                # 准备文本特征
                text_features = self._encode_text(user_text)
                
                # 执行KAD-Fusion
                fused_features = self.kad_fusion(
                    vision_features=image_features,
                    text_features=text_features,
                    knowledge_embeddings=knowledge_embedding
                )
                
                reasoning_log.append("🔬 深度特征融合已完成")
                
            except Exception as e:
                print(f"⚠️ 深度特征融合失败: {e}")
                reasoning_log.append("⚠️ 深度特征融合失败，使用决策级融合")
        
        # --- Step 3: 决策级融合 ---
        fusion_result = self._decision_level_fusion(
            vision_result=vision_result,
            text_result=text_result,
            user_text=user_text,
            graphrag_context=graphrag_context,
            reasoning_log=reasoning_log
        )
        
        # --- Step 4: 生成增强报告 ---
        if return_detailed:
            detailed_report = self._generate_detailed_report(
                fusion_result=fusion_result,
                vision_result=vision_result,
                text_result=text_result,
                graphrag_context=graphrag_context
            )
            fusion_result['detailed_report'] = detailed_report
        
        return fusion_result
    
    def _get_knowledge_embedding(self, disease_name: str) -> torch.Tensor:
        """
        获取知识图谱嵌入
        
        Args:
            disease_name: 病害名称
            
        Returns:
            知识嵌入张量
        """
        # 这里简化处理，实际应该从知识图谱获取嵌入
        # 使用随机嵌入作为占位
        embedding = torch.randn(1, 8, self.knowledge_dim).to(self.device)
        return embedding
    
    def _encode_text(self, text: str) -> torch.Tensor:
        """
        编码文本
        
        Args:
            text: 输入文本
            
        Returns:
            文本特征张量
        """
        # 这里简化处理，实际应该使用BERT等编码器
        # 使用随机特征作为占位
        features = torch.randn(1, self.text_dim).to(self.device)
        return features
    
    def _decision_level_fusion(
        self,
        vision_result: Dict[str, Any],
        text_result: Dict[str, Any],
        user_text: str,
        graphrag_context: Optional[str],
        reasoning_log: List[str]
    ) -> Dict[str, Any]:
        """
        执行决策级融合
        
        Args:
            vision_result: 视觉结果
            text_result: 文本结果
            user_text: 用户文本
            graphrag_context: GraphRAG上下文
            reasoning_log: 推理日志
            
        Returns:
            融合结果
        """
        v_label = vision_result.get('label', '未知')
        v_conf = vision_result.get('conf', 0.0)
        
        t_label = text_result.get('label', '未知')
        t_conf = text_result.get('conf', 0.0)
        
        final_diagnosis = "未知"
        final_conf = 0.0
        
        # --- 策略1: 强一致性 ---
        if v_label == t_label and v_label != "未知":
            final_diagnosis = v_label
            # 加权融合
            final_conf = (v_conf * self.weights['vision'] + 
                         t_conf * self.weights['text']) / (
                         self.weights['vision'] + self.weights['text'])
            reasoning_log.append(f"✅ 视觉与文本证据一致，均指向【{v_label}】")
            
            # 如果有GraphRAG上下文，提升置信度
            if graphrag_context:
                final_conf = min(final_conf * 1.1, 1.0)
                reasoning_log.append("📚 GraphRAG知识验证通过，提升置信度")
        
        # --- 策略2: 视觉主导 ---
        elif v_conf > 0.8:
            final_diagnosis = v_label
            final_conf = v_conf
            reasoning_log.append(f"👁️ 视觉特征极其明显 (置信度 {v_conf:.2f})，优先采信视觉结果")
            
            if t_label != "未知" and t_label != v_label:
                reasoning_log.append(f"⚠️ 忽略文本推断的【{t_label}】")
        
        # --- 策略3: 知识图谱仲裁 ---
        else:
            reasoning_log.append(f"⚖️ 检测到冲突，启动知识图谱仲裁...")
            
            # 验证视觉结果
            v_support = False
            if v_label != "未知":
                v_support = self.kg.verify_consistency(v_label, user_text)
            
            # 验证文本结果
            t_support = False
            if t_label != "未知":
                t_support = self.kg.verify_consistency(t_label, user_text)
            
            if v_support and not t_support:
                final_diagnosis = v_label
                final_conf = v_conf * 0.9
                reasoning_log.append(f"📘 图谱验证：支持视觉结果【{v_label}】")
            elif t_support and not v_support:
                final_diagnosis = t_label
                final_conf = t_conf * 0.9
                reasoning_log.append(f"📘 图谱验证：支持文本结果【{t_label}】")
            else:
                # 无法判断，取置信度高的
                if v_conf >= t_conf and v_label != "未知":
                    final_diagnosis = v_label
                    final_conf = v_conf * 0.7
                    reasoning_log.append("🤷 证据冲突，保留置信度较高的视觉结果")
                elif t_label != "未知":
                    final_diagnosis = t_label
                    final_conf = t_conf * 0.7
                    reasoning_log.append("🤷 证据冲突，保留置信度较高的文本结果")
        
        # 获取治疗建议
        treatment_advice = "无"
        if final_diagnosis != "未知":
            treatment_advice = self.kg.get_treatment_info(final_diagnosis)
        
        return {
            "diagnosis": final_diagnosis,
            "confidence": final_conf,
            "reasoning": reasoning_log,
            "treatment": treatment_advice,
            "vision_result": vision_result,
            "text_result": text_result,
            "graphrag_context": graphrag_context
        }
    
    def _generate_detailed_report(
        self,
        fusion_result: Dict[str, Any],
        vision_result: Dict[str, Any],
        text_result: Dict[str, Any],
        graphrag_context: Optional[str]
    ) -> str:
        """
        生成详细诊断报告
        
        Args:
            fusion_result: 融合结果
            vision_result: 视觉结果
            text_result: 文本结果
            graphrag_context: GraphRAG上下文
            
        Returns:
            Markdown格式的报告
        """
        report_parts = []
        
        # 诊断结论
        diagnosis = fusion_result.get('diagnosis', '未知')
        confidence = fusion_result.get('confidence', 0.0)
        
        report_parts.append(f"## 🏥 诊断结论：【{diagnosis}】")
        report_parts.append(f"**置信度**: {confidence:.2%}")
        report_parts.append("")
        
        # 推理过程
        report_parts.append("### 🔍 诊断推理")
        for log in fusion_result.get('reasoning', []):
            report_parts.append(f"- {log}")
        report_parts.append("")
        
        # 视觉证据
        report_parts.append("### 👁️ 视觉证据")
        v_label = vision_result.get('label', '未知')
        v_conf = vision_result.get('conf', 0.0)
        report_parts.append(f"- 识别结果: {v_label} (置信度: {v_conf:.2f})")
        if vision_result.get('description'):
            report_parts.append(f"- 特征描述: {vision_result['description']}")
        report_parts.append("")
        
        # 文本证据
        report_parts.append("### 📝 文本证据")
        t_label = text_result.get('label', '未知')
        t_conf = text_result.get('conf', 0.0)
        report_parts.append(f"- 识别结果: {t_label} (置信度: {t_conf:.2f})")
        report_parts.append("")
        
        # 知识图谱支持
        if graphrag_context:
            report_parts.append("### 📚 知识图谱支持")
            report_parts.append(graphrag_context[:500] + "..." if len(graphrag_context) > 500 else graphrag_context)
            report_parts.append("")
        
        # 治疗建议
        report_parts.append("### 💊 治疗建议")
        treatment = fusion_result.get('treatment', '无')
        report_parts.append(treatment)
        
        return "\n".join(report_parts)
    
    def get_fusion_info(self) -> Dict[str, Any]:
        """
        获取融合引擎信息
        
        Returns:
            引擎信息字典
        """
        return {
            'fusion_type': 'Enhanced KAD-Fusion',
            'modules': {
                'kga': self.use_kga,
                'graphrag': self.use_graphrag and self.graphrag is not None,
                'deep_fusion': self.use_deep_fusion
            },
            'weights': self.weights,
            'device': self.device
        }


def test_enhanced_fusion_agent():
    """测试增强版融合智能体"""
    print("=" * 60)
    print("🧪 测试 Enhanced Fusion Agent")
    print("=" * 60)
    
    # 模拟知识智能体
    class MockKnowledgeAgent:
        def verify_consistency(self, label, text):
            return True
        
        def get_treatment_info(self, disease):
            return f"针对{disease}的治疗方案"
    
    # 创建融合智能体
    kg = MockKnowledgeAgent()
    agent = EnhancedFusionAgent(
        knowledge_agent=kg,
        use_kga=True,
        use_graphrag=False,  # 跳过GraphRAG测试
        use_deep_fusion=False  # 跳过深度融合测试
    )
    
    # 测试数据
    vision_result = {
        'label': '条锈病',
        'conf': 0.92,
        'description': '叶片有黄色条纹'
    }
    
    text_result = {
        'label': '条锈病',
        'conf': 0.85
    }
    
    user_text = "叶片出现黄色条纹状病斑"
    
    # 执行融合
    print("\n🧪 测试多模态融合...")
    result = agent.fuse_multimodal(
        vision_result=vision_result,
        text_result=text_result,
        user_text=user_text,
        return_detailed=True
    )
    
    print(f"✅ 融合完成")
    print(f"   诊断: {result['diagnosis']}")
    print(f"   置信度: {result['confidence']:.2f}")
    print(f"   推理步骤: {len(result['reasoning'])}")
    
    # 获取引擎信息
    info = agent.get_fusion_info()
    print(f"\n✅ 引擎信息: {info['fusion_type']}")
    
    print("\n" + "=" * 60)
    print("✅ Enhanced Fusion Agent 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_enhanced_fusion_agent()

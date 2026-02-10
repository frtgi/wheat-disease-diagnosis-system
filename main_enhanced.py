# -*- coding: utf-8 -*-
"""
IWDDA: 基于多模态特征融合的小麦病害诊断智能体 - 增强版

集成SerpensGate-YOLOv8和KAD-Former架构的完整实现
"""
import os
import sys
from typing import Optional, List, Dict, Any
import torch

# 路径设置
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 导入增强版Agent
from vision.enhanced_vision_engine import EnhancedVisionAgent
from text.enhanced_text_engine import EnhancedLanguageAgent
from graph.graph_engine import KnowledgeAgent
from fusion.enhanced_fusion_engine import EnhancedFusionAgent
from action.learner_engine import ActiveLearner
from action.enhanced_learner_engine import EnhancedActiveLearner
from action.feedback_integration import FeedbackLoopIntegrator, FeedbackLoopConfig

# 导入认知模块（用于多模态支持）
from cognition.prompt_templates import DetectionResult


class EnhancedWheatDoctor:
    """
    增强版小麦病害诊断智能体
    
    集成以下先进技术：
    - SerpensGate-YOLOv8（动态蛇形卷积、SPPELAN、STA）
    - Agri-LLaVA（多模态语义理解）
    - KAD-Former（知识引导注意力、GraphRAG）
    """
    
    def __init__(
        self,
        use_enhanced_vision: bool = True,
        use_enhanced_language: bool = True,
        use_enhanced_fusion: bool = True,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        初始化增强版诊断智能体
        
        Args:
            use_enhanced_vision: 是否使用增强版视觉Agent
            use_enhanced_language: 是否使用增强版语言Agent
            use_enhanced_fusion: 是否使用增强版融合Agent
            device: 计算设备
        """
        print("=" * 70)
        print("🤖 [Enhanced IWDDA System] 初始化全科小麦病害诊断智能体")
        print("   版本: v4.0 SerpensGate-KAD-Fusion版")
        print("=" * 70)
        
        self.device = device
        
        # 1. 初始化视觉智能体
        if use_enhanced_vision:
            print("\n👁️ 初始化增强版视觉智能体 (SerpensGate-YOLOv8)...")
            self.eye = EnhancedVisionAgent(
                use_dysnake=True,
                use_sppelan=True,
                use_sta=True,
                device=device
            )
        else:
            print("\n👁️ 初始化标准视觉智能体...")
            from vision.vision_engine import VisionAgent
            self.eye = VisionAgent()
        
        # 2. 初始化语言智能体
        if use_enhanced_language:
            print("\n🗣️ 初始化增强版语言智能体 (Agri-LLaVA)...")
            self.ear = EnhancedLanguageAgent(
                use_cognition=True,
                device=device
            )
        else:
            print("\n🗣️ 初始化标准语言智能体...")
            from text.text_engine import LanguageAgent
            self.ear = LanguageAgent()
        
        # 3. 初始化知识智能体
        print("\n🧠 初始化知识智能体 (Neo4j)...")
        self.brain = KnowledgeAgent(password="123456789s")
        
        # 4. 初始化融合智能体
        if use_enhanced_fusion:
            print("\n🔗 初始化增强版融合智能体 (KAD-Former)...")
            self.fusion_core = EnhancedFusionAgent(
                knowledge_agent=self.brain,
                use_kga=True,
                use_graphrag=True,
                use_deep_fusion=True,
                device=device
            )
        else:
            print("\n🔗 初始化标准融合智能体...")
            from fusion.fusion_engine import FusionAgent
            self.fusion_core = FusionAgent(knowledge_agent=self.brain)
        
        # 5. 初始化学习智能体（增强版）
        print("\n📚 初始化增强型学习智能体...")
        self.learner = EnhancedActiveLearner(
            data_root="datasets/feedback_data",
            replay_buffer_dir="data/experience_replay",
            buffer_capacity=1000,
            rehearsal_ratio=0.3,
            confidence_threshold=0.7,
            device=device
        )
        
        # 6. 初始化反馈闭环集成器
        print("\n🔄 初始化反馈闭环集成器...")
        feedback_config = FeedbackLoopConfig(
            high_uncertainty_threshold=0.6,
            critical_uncertainty_threshold=0.3,
            auto_learn_threshold=50,
            min_feedback_for_learning=10,
            replay_buffer_capacity=1000,
            rehearsal_ratio=0.3,
            extract_knowledge=True,
            update_knowledge_graph=True
        )
        self.feedback_loop = FeedbackLoopIntegrator(
            knowledge_agent=self.brain,
            config=feedback_config,
            device=device
        )
        
        print("\n" + "=" * 70)
        print("🚀 [System] 全栈服务就绪！增强版引擎已激活")
        print("   ✨ 集成: SerpensGate-YOLOv8 + Agri-LLaVA + KAD-Former + 反馈闭环")
        print("=" * 70)
    
    def run_diagnosis(
        self,
        image_path: str,
        user_text: str = "",
        return_features: bool = False
    ) -> dict:
        """
        执行增强版诊断
        
        Args:
            image_path: 图片路径
            user_text: 用户文本描述（可选）
            return_features: 是否返回特征信息
            
        Returns:
            诊断结果字典
        """
        print(f"\n⚡ 处理请求: {os.path.basename(image_path)}")
        if user_text:
            print(f"   用户描述: \"{user_text[:30]}...\"" if len(user_text) > 30 else f"   用户描述: \"{user_text}\"")
        else:
            print("   用户描述: 无")
        
        # --- Phase 1: 视觉感知（增强版）---
        print("\n--- Phase 1: 视觉感知 ---")
        vision_res, vision_features = self.eye.detect(
            image_path=image_path,
            conf_threshold=0.05,
            save_result=False,
            return_features=return_features
        )
        
        v_data = {'label': '未知', 'conf': 0.0}
        plotted_img = None
        detection_results = []  # 用于多模态融合
        
        # 解析视觉结果
        if vision_res and len(vision_res) > 0:
            result = vision_res[0]
            plotted_img = result.plot()[:, :, ::-1] if hasattr(result, 'plot') else None
            
            # 解析检测框
            if result.boxes is not None and len(result.boxes) > 0:
                try:
                    best_conf = 0.0
                    best_cls_id = -1
                    
                    for i, box in enumerate(result.boxes):
                        if box.cls.numel() > 0 and box.conf.numel() > 0:
                            cls_id = int(box.cls[0].item())
                            conf = float(box.conf[0].item())
                            
                            # 创建DetectionResult对象
                            bbox = box.xyxy[0].cpu().numpy().tolist() if hasattr(box, 'xyxy') else None
                            det_result = DetectionResult(
                                disease_name=self.eye.model.names.get(cls_id, f'类别{cls_id}'),
                                confidence=conf,
                                bbox=bbox
                            )
                            detection_results.append(det_result)
                            
                            if conf > best_conf:
                                best_conf = conf
                                best_cls_id = cls_id
                    
                    if best_cls_id >= 0:
                        v_name = self.eye.model.names.get(best_cls_id, f'类别{best_cls_id}')
                        v_data = {'label': v_name, 'conf': best_conf}
                        print(f"✅ 视觉识别: {v_name} (置信度: {best_conf:.2f})")
                        
                        # 自动生成症状描述
                        if not user_text:
                            auto_symptom = self._get_symptom_from_kg(v_name)
                            if auto_symptom:
                                user_text = auto_symptom
                                print(f"📝 自动生成症状: {user_text}")
                                
                except Exception as e:
                    print(f"⚠️ 解析检测框错误: {e}")
            else:
                print("🍃 未检测到病害目标")
        
        # 如果没有绘制图，读取原图
        if plotted_img is None:
            import cv2
            plotted_img = cv2.imread(image_path)
            if plotted_img is not None:
                plotted_img = plotted_img[:, :, ::-1]
        
        # --- Phase 2: 文本感知（增强版）---
        print("\n--- Phase 2: 文本感知 ---")
        
        # 使用增强版语言Agent进行语义理解
        if hasattr(self.ear, 'analyze_image') and detection_results:
            # 尝试使用多模态理解
            try:
                from PIL import Image
                pil_image = Image.open(image_path)
                text_analysis = self.ear.analyze_image(
                    image=pil_image,
                    detection_results=detection_results,
                    user_description=user_text
                )
                print(f"✅ 多模态文本分析完成")
            except Exception as e:
                print(f"⚠️ 多模态分析失败: {e}")
                text_analysis = None
        
        # 标准症状匹配
        t_data = self._analyze_text(user_text, v_data)
        
        # --- Phase 3: 多模态融合（增强版）---
        print("\n--- Phase 3: KAD-Fusion多模态融合 ---")
        
        # 使用增强版融合引擎
        if hasattr(self.fusion_core, 'fuse_multimodal'):
            fusion_result = self.fusion_core.fuse_multimodal(
                vision_result=v_data,
                text_result=t_data,
                user_text=user_text,
                image_features=vision_features if return_features else None,
                return_detailed=True
            )
            
            # 格式化报告
            report = {
                'diagnosis': fusion_result.get('diagnosis', '未知'),
                'confidence': fusion_result.get('confidence', 0.0),
                'reasoning': fusion_result.get('reasoning', []),
                'treatment': fusion_result.get('treatment', '无'),
                'detailed_report': fusion_result.get('detailed_report', '')
            }
        else:
            # 使用标准融合
            report = self.fusion_core.fuse_and_decide(v_data, t_data, user_text)
        
        print(f"✅ 融合诊断: {report['diagnosis']} (置信度: {report['confidence']:.2f})")
        
        return {
            "plotted_image": plotted_img,
            "vision_data": v_data,
            "text_data": t_data,
            "final_report": report,
            "detection_results": detection_results
        }
    
    def _analyze_text(self, user_text: str, v_data: dict) -> dict:
        """
        分析文本描述
        
        Args:
            user_text: 用户文本
            v_data: 视觉数据
            
        Returns:
            文本分析结果
        """
        if not user_text:
            return {'label': '未知', 'conf': 0.0}
        
        # 标准症状库
        standard_symptoms = {
            "蚜虫": "黑色或绿色小虫，分泌蜜露",
            "螨虫": "叶片卷曲发黄，植株矮小",
            "茎蝇": "茎秆有蛀孔，植株枯萎",
            "锈病": "叶片上有黄色或红褐色粉末孢子堆",
            "茎锈病": "茎秆上有红褐色锈斑",
            "叶锈病": "叶片上有红褐色粉末状斑点",
            "条锈病": "叶片上有黄色条纹状锈斑",
            "白粉病": "白色绒毛状霉层",
            "赤霉病": "穗部枯白，粉红色霉层",
            "黑粉病": "穗部变成黑粉",
            "根腐病": "根部腐烂变黑",
            "叶斑病": "褐色病斑",
            "小麦爆发病": "穗部枯萎，有灰色霉层",
            "壳针孢叶斑病": "叶片上有褐色小斑点",
            "斑点叶斑病": "叶片上有不规则斑点",
            "褐斑病": "叶片上有褐色圆形病斑",
            "健康": "植株生长正常，无病害症状"
        }
        
        best_match = "未知"
        best_score = 0.0
        
        # 计算相似度
        for disease, symptom in standard_symptoms.items():
            score = self.ear.compute_similarity(user_text, symptom)
            if score > best_score:
                best_score = score
                best_match = disease
        
        if best_score < 0.35:
            best_match = "未知"
        
        return {'label': best_match, 'conf': best_score}
    
    def _get_symptom_from_kg(self, disease_name: str) -> str:
        """
        从知识图谱获取症状描述
        
        Args:
            disease_name: 病害名称
            
        Returns:
            症状描述
        """
        try:
            details = self.brain.get_disease_details(disease_name)
            if details and 'symptoms' in details:
                return details['symptoms']
        except Exception as e:
            print(f"⚠️ 从知识图谱获取症状失败: {e}")
        
        # 备用标准库
        standard_symptoms = {
            "蚜虫": "叶片上有黑色或绿色小虫，分泌蜜露",
            "螨虫": "叶片卷曲发黄，植株矮小",
            "条锈病": "叶片上有黄色条纹状锈斑",
            "白粉病": "白色绒毛状霉层",
            "赤霉病": "穗部枯白，粉红色霉层"
        }
        return standard_symptoms.get(disease_name, "")
    
    def chat(self, message: str, image_path: str = None) -> str:
        """
        交互式对话
        
        Args:
            message: 用户消息
            image_path: 可选的图片路径
            
        Returns:
            助手回复
        """
        if hasattr(self.ear, 'chat'):
            if image_path and os.path.exists(image_path):
                from PIL import Image
                image = Image.open(image_path)
                return self.ear.chat(message, image=image)
            else:
                return self.ear.chat(message)
        else:
            return self.ear.answer_question(message)
    
    def get_system_info(self) -> dict:
        """
        获取系统信息
        
        Returns:
            系统信息字典
        """
        info = {
            "system": "Enhanced IWDDA",
            "version": "v4.0",
            "device": self.device
        }
        
        # 视觉Agent信息
        if hasattr(self.eye, 'get_model_info'):
            info["vision"] = self.eye.get_model_info()
        
        # 语言Agent信息
        if hasattr(self.ear, 'get_model_info'):
            info["language"] = self.ear.get_model_info()
        
        # 融合Agent信息
        if hasattr(self.fusion_core, 'get_fusion_info'):
            info["fusion"] = self.fusion_core.get_fusion_info()
        
        return info
    
    def submit_diagnosis_feedback(
        self,
        image_path: str,
        system_diagnosis: str,
        confidence: float,
        user_correction: Optional[str] = None,
        comments: str = "",
        reviewer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交诊断反馈
        
        将诊断结果提交到反馈闭环系统，根据置信度决定是否需要专家审核
        
        :param image_path: 图像路径
        :param system_diagnosis: 系统诊断结果
        :param confidence: 置信度
        :param user_correction: 用户修正（可选）
        :param comments: 评论
        :param reviewer_id: 审核人ID
        :return: 反馈处理结果
        """
        if user_correction is not None:
            # 直接提交专家反馈
            # 先处理诊断结果获取记录ID
            result = self.feedback_loop.process_diagnosis_result(
                image_path=image_path,
                diagnosis=system_diagnosis,
                confidence=confidence
            )
            
            if result.get('feedback_record_id'):
                return self.feedback_loop.submit_expert_feedback(
                    record_id=result['feedback_record_id'],
                    correction=user_correction,
                    comments=comments,
                    reviewer_id=reviewer_id
                )
            else:
                # 如果不需要审核，直接收集反馈
                return self.learner.collect_feedback(
                    image_path=image_path,
                    system_diagnosis=system_diagnosis,
                    confidence=confidence,
                    user_correction=user_correction,
                    comments=comments
                )
        else:
            # 提交诊断结果，由系统决定是否需要审核
            return self.feedback_loop.process_diagnosis_result(
                image_path=image_path,
                diagnosis=system_diagnosis,
                confidence=confidence
            )
    
    def get_pending_reviews(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取待审核列表
        
        :param limit: 数量限制
        :return: 待审核记录列表
        """
        return self.feedback_loop.get_pending_reviews(limit=limit)
    
    def submit_expert_review(
        self,
        record_id: str,
        correction: Optional[str] = None,
        comments: str = "",
        reviewer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交专家审核
        
        :param record_id: 记录ID
        :param correction: 修正结果
        :param comments: 评论
        :param reviewer_id: 审核人ID
        :return: 审核结果
        """
        return self.feedback_loop.submit_expert_feedback(
            record_id=record_id,
            correction=correction,
            comments=comments,
            reviewer_id=reviewer_id
        )
    
    def trigger_incremental_learning(
        self,
        model=None,
        optimizer=None,
        epochs: int = 5
    ) -> Dict[str, Any]:
        """
        触发增量学习
        
        :param model: 模型（可选）
        :param optimizer: 优化器（可选）
        :param epochs: 训练轮数
        :return: 学习结果
        """
        return self.feedback_loop.trigger_incremental_learning(
            model=model,
            optimizer=optimizer,
            epochs=epochs
        )
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        获取反馈统计信息
        
        :return: 统计信息字典
        """
        return self.feedback_loop.get_system_status()
    
    def generate_feedback_report(self, output_path: Optional[str] = None) -> str:
        """
        生成反馈闭环报告
        
        :param output_path: 输出路径
        :return: 报告路径
        """
        return self.feedback_loop.generate_report(output_path=output_path)
    
    def close(self):
        """关闭系统"""
        if hasattr(self.brain, 'close'):
            self.brain.close()
        print("\n👋 系统已关闭")


def test_enhanced_system():
    """测试增强版系统"""
    print("=" * 70)
    print("🧪 测试 Enhanced IWDDA System")
    print("=" * 70)
    
    # 创建增强版系统
    doctor = EnhancedWheatDoctor(
        use_enhanced_vision=True,
        use_enhanced_language=False,  # 使用备用模式测试
        use_enhanced_fusion=False     # 使用标准融合测试
    )
    
    # 获取系统信息
    print("\n📊 系统信息:")
    info = doctor.get_system_info()
    print(f"   版本: {info['version']}")
    print(f"   设备: {info['device']}")
    
    # 测试图片
    test_image = "datasets/wheat_data/images/train/Aphid_aphid_0.png"
    
    if os.path.exists(test_image):
        print("\n" + "=" * 70)
        print("测试 1：有文本描述")
        print("=" * 70)
        result = doctor.run_diagnosis(test_image, "叶片上有黑色小虫")
        print(f"\n诊断结果:")
        print(f"   病害: {result['final_report']['diagnosis']}")
        print(f"   置信度: {result['final_report']['confidence']:.2f}")
        
        print("\n" + "=" * 70)
        print("测试 2：无文本描述（纯视觉）")
        print("=" * 70)
        result = doctor.run_diagnosis(test_image, "")
        print(f"\n诊断结果:")
        print(f"   病害: {result['final_report']['diagnosis']}")
        print(f"   置信度: {result['final_report']['confidence']:.2f}")
    else:
        print(f"\n⚠️ 测试图片不存在: {test_image}")
    
    doctor.close()
    
    print("\n" + "=" * 70)
    print("✅ Enhanced IWDDA System 测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_enhanced_system()

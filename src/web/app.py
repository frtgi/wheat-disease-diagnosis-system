# -*- coding: utf-8 -*-
"""
WheatAgent Gradio Web 界面

提供用户友好的交互式诊断界面
"""
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

import gradio as gr
import numpy as np
from PIL import Image

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.vision.vision_engine import VisionAgent as VisionEngine
from src.cognition.cognition_engine import CognitionEngine
from src.fusion.fusion_engine import FusionAgent as FusionEngine
from src.graph.graph_engine import KnowledgeAgent as GraphEngine


class WheatAgentWebApp:
    """WheatAgent Web应用"""
    
    def __init__(self):
        """初始化应用"""
        self.vision_engine: Optional[VisionEngine] = None
        self.cognition_engine: Optional[CognitionEngine] = None
        self.fusion_engine: Optional[FusionEngine] = None
        self.graph_engine: Optional[GraphEngine] = None
        
        self._initialize_engines()
    
    def _initialize_engines(self):
        """初始化所有引擎"""
        print("🚀 初始化WheatAgent引擎...")
        
        try:
            # 知识图谱引擎（先初始化，因为融合引擎依赖它）
            print("  📚 加载知识图谱引擎...")
            self.graph_engine = GraphEngine()
            print("  ✅ 知识图谱引擎加载完成")
            
            # 视觉引擎
            print("  📷 加载视觉引擎...")
            self.vision_engine = VisionEngine()
            print("  ✅ 视觉引擎加载完成")
            
            # 认知引擎
            print("  🧠 加载认知引擎...")
            self.cognition_engine = CognitionEngine()
            print("  ✅ 认知引擎加载完成")
            
            # 融合引擎
            print("  🔗 加载融合引擎...")
            self.fusion_engine = FusionEngine(
                knowledge_agent=self.graph_engine
            )
            print("  ✅ 融合引擎加载完成")
            
            print("\n🎉 所有引擎初始化完成!")
            
        except Exception as e:
            print(f"\n⚠️ 引擎初始化警告: {e}")
            print("部分功能可能不可用")
    
    def diagnose_image(
        self,
        image: Optional[np.ndarray],
        use_knowledge: bool = True,
        top_k: int = 3
    ) -> Tuple[str, str]:
        """
        图像诊断
        
        :param image: 输入图像
        :param use_knowledge: 是否使用知识图谱
        :param top_k: 返回前K个结果
        :return: (诊断结果文本, 可视化图像)
        """
        if image is None:
            return "请先上传图像", None
        
        try:
            # 保存临时图像
            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = temp_dir / f"{timestamp}.jpg"
            
            # 转换numpy数组为PIL图像并保存
            pil_image = Image.fromarray(image.astype('uint8'))
            pil_image.save(image_path)
            
            # 执行诊断
            if self.fusion_engine and self.vision_engine:
                # 使用融合引擎进行多模态诊断
                results = self.fusion_engine.diagnose(
                    image_path=str(image_path),
                    use_knowledge=use_knowledge,
                    top_k=top_k,
                    vision_engine=self.vision_engine,
                    cognition_engine=self.cognition_engine
                )
                
                # 生成可视化结果（带检测框）
                _, vis_path = self.vision_engine.detect_and_visualize(
                    str(image_path), 
                    conf_threshold=0.05
                )
                
            elif self.vision_engine:
                # 仅使用视觉引擎
                results, vis_path = self.vision_engine.detect_and_visualize(
                    str(image_path),
                    conf_threshold=0.05
                )
            else:
                return "引擎未加载，无法诊断", None
            
            # 格式化结果
            result_text = self._format_diagnosis_results(results)
            
            # 加载可视化图像
            if vis_path and os.path.exists(vis_path):
                vis_image = Image.open(vis_path)
            else:
                vis_image = pil_image
            
            return result_text, vis_image
            
        except Exception as e:
            return f"诊断失败: {str(e)}", None
    
    def diagnose_text(
        self,
        text: str,
        use_knowledge: bool = True,
        top_k: int = 3
    ) -> str:
        """
        文本症状诊断
        
        :param text: 症状描述
        :param use_knowledge: 是否使用知识图谱
        :param top_k: 返回前K个结果
        :return: 诊断结果文本
        """
        if not text.strip():
            return "请输入症状描述"
        
        try:
            if not self.cognition_engine:
                return "认知引擎未加载"
            
            results = self.cognition_engine.analyze_text(
                text=text,
                use_knowledge=use_knowledge,
                top_k=top_k
            )
            
            return self._format_text_results(results)
            
        except Exception as e:
            return f"诊断失败: {str(e)}"
    
    def _format_diagnosis_results(self, results: List[Dict]) -> str:
        """格式化诊断结果"""
        if not results:
            return "未检测到病害"
        
        output = []
        output.append("=" * 60)
        output.append("🌾 小麦病害智能诊断报告")
        output.append("=" * 60)
        output.append("")
        
        # 1. 显示主要诊断结果
        output.append("【检测结果】")
        output.append("-" * 60)
        
        for i, result in enumerate(results[:5], 1):
            disease = result.get('name', '未知')
            confidence = result.get('confidence', 0)
            bbox = result.get('bbox', None)
            
            output.append(f"{i}. {disease}")
            output.append(f"   置信度: {confidence:.2%}")
            
            if bbox:
                output.append(f"   位置: [{', '.join([f'{x:.1f}' for x in bbox])}]")
            
            # 添加知识图谱信息
            if 'description' in result:
                output.append(f"   描述: {result['description'][:150]}...")
            if 'treatment' in result:
                output.append(f"   防治: {result['treatment'][:150]}...")
            if 'symptoms' in result:
                output.append(f"   症状: {result['symptoms'][:100]}...")
            
            output.append("")
        
        # 2. 显示Agri-LLaVA生成的详细报告（根据文档4.3节）
        if results and 'llava_report' in results[0]:
            output.append("-" * 60)
            output.append("【智能诊断分析】")
            output.append("-" * 60)
            output.append(results[0]['llava_report'])
            output.append("")
        
        # 3. 显示融合推理过程（根据文档第6章）
        if results and 'reasoning' in results[0]:
            output.append("-" * 60)
            output.append("【诊断推理过程】")
            output.append("-" * 60)
            output.append(results[0]['reasoning'])
            output.append("")
        
        output.append("=" * 60)
        output.append(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)
        
        return "\n".join(output)
    
    def _format_text_results(self, results: List[Dict]) -> str:
        """格式化文本诊断结果"""
        if not results:
            return "无法根据描述确定病害"
        
        output = []
        output.append("=" * 50)
        output.append("📝 基于症状的诊断结果")
        output.append("=" * 50)
        output.append("")
        
        for i, result in enumerate(results[:5], 1):
            disease = result.get('name', '未知')
            confidence = result.get('confidence', 0)
            reason = result.get('reason', '')
            
            output.append(f"{i}. {disease}")
            output.append(f"   匹配度: {confidence:.2%}")
            if reason:
                output.append(f"   依据: {reason}")
            output.append("")
        
        output.append("=" * 50)
        return "\n".join(output)
    
    def get_disease_list(self) -> str:
        """获取病害列表"""
        try:
            if not self.graph_engine:
                return "知识图谱引擎未加载"
            
            diseases = self.graph_engine.get_all_diseases()
            
            output = []
            output.append("=" * 50)
            output.append("📚 知识图谱病害列表")
            output.append("=" * 50)
            output.append(f"\n共 {len(diseases)} 种病害:\n")
            
            for i, disease in enumerate(diseases, 1):
                output.append(f"{i}. {disease}")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"获取病害列表失败: {str(e)}"
    
    def get_disease_detail(self, disease_name: str) -> str:
        """获取病害详细信息"""
        if not disease_name.strip():
            return "请输入病害名称"
        
        try:
            if not self.graph_engine:
                return "知识图谱引擎未加载"
            
            info = self.graph_engine.get_disease_info(disease_name)
            
            if not info:
                return f"未找到病害: {disease_name}"
            
            output = []
            output.append("=" * 50)
            output.append(f"🔍 {disease_name} 详细信息")
            output.append("=" * 50)
            output.append("")
            
            for key, value in info.items():
                output.append(f"{key}: {value}")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"获取病害信息失败: {str(e)}"


def create_app() -> gr.Blocks:
    """创建Gradio应用"""
    app = WheatAgentWebApp()
    
    # 自定义CSS
    css = """
    .container {
        max-width: 1200px;
        margin: 0 auto;
    }
    .header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .result-box {
        background: #f5f5f5;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #667eea;
    }
    """
    
    with gr.Blocks(title="WheatAgent - 小麦病害诊断智能体") as demo:
        # 标题
        gr.HTML("""
        <div class="header">
            <h1>🌾 WheatAgent</h1>
            <h3>基于多模态特征融合的小麦病害诊断智能体</h3>
            <p>融合视觉感知、语义理解和知识推理的智能诊断系统</p>
        </div>
        """)
        
        with gr.Tabs():
            # 图像诊断标签页
            with gr.TabItem("📷 图像诊断"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 上传小麦病害图像")
                        image_input = gr.Image(
                            label="上传图像",
                            type="numpy",
                            height=400
                        )
                        
                        with gr.Row():
                            use_knowledge_cb = gr.Checkbox(
                                label="使用知识图谱",
                                value=True
                            )
                            top_k_slider = gr.Slider(
                                label="返回结果数量",
                                minimum=1,
                                maximum=10,
                                value=3,
                                step=1
                            )
                        
                        diagnose_btn = gr.Button(
                            "🔍 开始诊断",
                            variant="primary",
                            size="lg"
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 诊断结果")
                        result_text = gr.Textbox(
                            label="诊断报告",
                            lines=20,
                            max_lines=30,
                            interactive=False
                        )
                        
                        gr.Markdown("### 可视化结果")
                        result_image = gr.Image(
                            label="检测结果",
                            type="pil",
                            height=400
                        )
                
                # 绑定事件
                diagnose_btn.click(
                    fn=app.diagnose_image,
                    inputs=[image_input, use_knowledge_cb, top_k_slider],
                    outputs=[result_text, result_image]
                )
            
            # 文本诊断标签页
            with gr.TabItem("📝 文本诊断"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 输入症状描述")
                        text_input = gr.Textbox(
                            label="症状描述",
                            placeholder="请描述小麦的症状，如：叶片出现黄色条纹、有白色霉层等...",
                            lines=10
                        )
                        
                        with gr.Row():
                            use_knowledge_text = gr.Checkbox(
                                label="使用知识图谱",
                                value=True
                            )
                            top_k_text = gr.Slider(
                                label="返回结果数量",
                                minimum=1,
                                maximum=10,
                                value=3,
                                step=1
                            )
                        
                        text_diagnose_btn = gr.Button(
                            "🔍 开始诊断",
                            variant="primary"
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 诊断结果")
                        text_result = gr.Textbox(
                            label="诊断报告",
                            lines=20,
                            max_lines=30,
                            interactive=False
                        )
                
                # 绑定事件
                text_diagnose_btn.click(
                    fn=app.diagnose_text,
                    inputs=[text_input, use_knowledge_text, top_k_text],
                    outputs=[text_result]
                )
            
            # 知识库查询标签页
            with gr.TabItem("📚 知识库"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 病害列表")
                        list_btn = gr.Button("📋 获取病害列表")
                        disease_list = gr.Textbox(
                            label="病害列表",
                            lines=20,
                            interactive=False
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 病害详情查询")
                        disease_name_input = gr.Textbox(
                            label="病害名称",
                            placeholder="输入病害名称，如：条锈病"
                        )
                        query_btn = gr.Button("🔍 查询详情")
                        disease_detail = gr.Textbox(
                            label="详细信息",
                            lines=20,
                            interactive=False
                        )
                
                # 绑定事件
                list_btn.click(
                    fn=app.get_disease_list,
                    outputs=[disease_list]
                )
                query_btn.click(
                    fn=app.get_disease_detail,
                    inputs=[disease_name_input],
                    outputs=[disease_detail]
                )
            
            # 使用说明标签页
            with gr.TabItem("❓ 使用说明"):
                gr.Markdown("""
                ## 🌾 WheatAgent 使用指南
                
                ### 图像诊断
                1. 在"图像诊断"标签页上传小麦病害图像
                2. 可选择是否使用知识图谱增强诊断
                3. 点击"开始诊断"按钮
                4. 查看诊断结果和可视化检测框
                
                ### 文本诊断
                1. 在"文本诊断"标签页输入症状描述
                2. 尽可能详细地描述症状特征
                3. 点击"开始诊断"按钮
                4. 查看基于症状的诊断建议
                
                ### 知识库查询
                - 查看系统中已知的所有小麦病害
                - 查询特定病害的详细信息、防治方法等
                
                ### 支持的病害类型
                系统支持17类常见小麦病害和虫害的识别与诊断。
                
                ### 注意事项
                - 图像质量会影响诊断准确性
                - 建议在自然光下拍摄清晰的叶片图像
                - 文本描述越详细，诊断结果越准确
                """)
        
        # 页脚
        gr.HTML("""
        <div style="text-align: center; padding: 20px; margin-top: 30px; color: #666;">
            <p>🌾 WheatAgent - 基于多模态特征融合的小麦病害诊断智能体</p>
            <p>Powered by YOLOv8 + Agri-LLaVA + Neo4j</p>
        </div>
        """)
    
    return demo


def main():
    """启动Web应用"""
    demo = create_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        show_error=True,
        css="""
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .result-box {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
        """
    )


if __name__ == "__main__":
    main()

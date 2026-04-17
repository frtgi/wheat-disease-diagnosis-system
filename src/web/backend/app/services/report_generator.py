"""
诊断报告生成服务
支持 PDF 和 HTML 格式的专业图文诊断报告
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import base64
import io

logger = logging.getLogger(__name__)


class ReportGenerator:
    """诊断报告生成器"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        初始化报告生成器
        
        参数:
            output_dir: 输出目录
        """
        self.output_dir = output_dir or Path(__file__).parent.parent.parent.parent / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"报告生成器初始化完成，输出目录：{self.output_dir}")
    
    def generate_pdf_report(self, diagnosis_result: Dict[str, Any], image_data: Optional[bytes] = None) -> Path:
        """
        生成 PDF 诊断报告
        
        参数:
            diagnosis_result: 诊断结果
            image_data: 原始图像数据（可选）
            
        返回:
            PDF 文件路径
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from reportlab.pdfgen import canvas
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diagnosis_report_{timestamp}.pdf"
            filepath = self.output_dir / filename
            
            # 创建 PDF 文档
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # 存储 PDF 内容的列表
            story = []
            
            # 样式
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.darkblue,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.darkblue,
                spaceAfter=12,
                spaceBefore=12
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.black,
                spaceAfter=6
            )
            
            # 标题
            story.append(Paragraph("小麦病害诊断报告", title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # 基本信息
            diagnosis = diagnosis_result.get("diagnosis", diagnosis_result.get("data", {}))
            story.append(Paragraph("基本信息", heading_style))
            
            basic_info = [
                ["报告时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ["病害名称:", diagnosis.get("disease_name", "未知")],
                ["置信度:", f"{diagnosis.get('confidence', 0):.1%}"],
                ["严重度:", diagnosis.get("severity", "未知")]
            ]
            
            basic_table = Table(basic_info, colWidths=[4*cm, 10*cm])
            basic_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(basic_table)
            story.append(Spacer(1, 0.3*inch))
            
            # 图像（如果有）
            if image_data:
                story.append(Paragraph("病害图像", heading_style))
                
                # 将图像数据转换为临时文件
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    tmp.write(image_data)
                    tmp_path = tmp.name
                
                try:
                    img = Image(tmp_path, width=12*cm, height=9*cm)
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
                finally:
                    import os
                    os.unlink(tmp_path)
            
            # 症状描述
            story.append(Paragraph("症状描述", heading_style))
            symptoms = diagnosis.get("symptoms", "无详细描述")
            story.append(Paragraph(symptoms, normal_style))
            story.append(Spacer(1, 0.3*inch))
            
            # 推理链（如果有）
            if diagnosis_result.get("reasoning_chain"):
                story.append(Paragraph("推理过程", heading_style))
                reasoning = diagnosis_result["reasoning_chain"].replace("\n", "<br/>")
                story.append(Paragraph(reasoning, normal_style))
                story.append(Spacer(1, 0.3*inch))
            
            # 防治建议
            story.append(Paragraph("防治建议", heading_style))
            
            prevention = diagnosis.get("prevention_methods", "请咨询专业农技人员")
            treatment = diagnosis.get("treatment_methods", "请咨询专业农技人员")
            
            prevention_table = Table([
                ["预防措施:", prevention],
                ["治疗方法:", treatment]
            ], colWidths=[4*cm, 10*cm])
            prevention_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ]))
            story.append(prevention_table)
            story.append(Spacer(1, 0.3*inch))
            
            # 置信度分析（如果有）
            if diagnosis_result.get("confidence_analysis"):
                story.append(Paragraph("置信度分析", heading_style))
                conf = diagnosis_result["confidence_analysis"]
                
                conf_table = Table([
                    ["总体置信度:", f"{conf.get('overall_confidence', 0):.1%}"],
                    ["视觉置信度:", f"{conf.get('visual_confidence', 0):.1%}"],
                    ["文本置信度:", f"{conf.get('textual_confidence', 0):.1%}"],
                ], colWidths=[4*cm, 10*cm])
                
                if conf.get('knowledge_confidence') is not None:
                    conf_table._cellvalues.append(("知识置信度:", f"{conf['knowledge_confidence']:.1%}"))
                
                conf_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(conf_table)
                story.append(Spacer(1, 0.3*inch))
            
            # 性能指标
            if diagnosis_result.get("performance"):
                story.append(Paragraph("性能指标", heading_style))
                perf = diagnosis_result["performance"]
                perf_text = f"推理时间：{perf.get('inference_time_ms', 0):.0f}ms"
                story.append(Paragraph(perf_text, normal_style))
            
            # 页脚
            story.append(Spacer(1, 1*inch))
            footer_text = f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | WheatAgent 智能诊断系统"
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            story.append(Paragraph(footer_text, footer_style))
            
            # 构建 PDF
            doc.build(story)
            
            logger.info(f"PDF 报告生成成功：{filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"PDF 报告生成失败：{e}")
            raise
    
    def generate_html_report(self, diagnosis_result: Dict[str, Any], image_data: Optional[bytes] = None) -> Path:
        """
        生成 HTML 诊断报告
        
        参数:
            diagnosis_result: 诊断结果
            image_data: 原始图像数据（可选）
            
        返回:
            HTML 文件路径
        """
        try:
            diagnosis = diagnosis_result.get("diagnosis", diagnosis_result.get("data", {}))

            # 图像 Base64 编码
            image_base64 = None
            if image_data:
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # HTML 模板
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小麦病害诊断报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        .section-title {{
            font-size: 20px;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .info-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .info-card strong {{
            color: #667eea;
            display: block;
            margin-bottom: 5px;
        }}
        
        .image-container {{
            text-align: center;
            margin: 20px 0;
        }}
        
        .image-container img {{
            max-width: 100%;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .confidence-bar {{
            background: #e9ecef;
            border-radius: 10px;
            height: 25px;
            margin: 10px 0;
            overflow: hidden;
        }}
        
        .confidence-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        
        .reasoning {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }}
        
        .reasoning ol {{
            margin-left: 20px;
        }}
        
        .reasoning li {{
            margin-bottom: 10px;
        }}
        
        .prevention {{
            background: #fff3cd;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌾 小麦病害诊断报告</h1>
            <p>WheatAgent 智能诊断系统</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2 class="section-title">基本信息</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <strong>报告时间</strong>
                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                    <div class="info-card">
                        <strong>病害名称</strong>
                        {diagnosis.get('disease_name', '未知')}
                    </div>
                    <div class="info-card">
                        <strong>严重度</strong>
                        {diagnosis.get('severity', '未知')}
                    </div>
                </div>
                
                <div class="info-card">
                    <strong>置信度</strong>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: {diagnosis.get('confidence', 0) * 100:.0f}%">
                            {diagnosis.get('confidence', 0) * 100:.1f}%
                        </div>
                    </div>
                </div>
            </div>
            
            {f'''
            <div class="section">
                <h2 class="section-title">病害图像</h2>
                <div class="image-container">
                    <img src="data:image/jpeg;base64,{image_base64}" alt="病害图像">
                </div>
            </div>
            ''' if image_base64 else ''}
            
            <div class="section">
                <h2 class="section-title">症状描述</h2>
                <p>{diagnosis.get('symptoms', '无详细描述')}</p>
            </div>
            
            {f'''
            <div class="section">
                <h2 class="section-title">推理过程</h2>
                <div class="reasoning">
                    {diagnosis_result.get('reasoning_chain', '').replace(chr(10), '<br/>• ')}
                </div>
            </div>
            ''' if diagnosis_result.get('reasoning_chain') else ''}
            
            <div class="section">
                <h2 class="section-title">防治建议</h2>
                <div class="prevention">
                    <h3>预防措施</h3>
                    <p>{diagnosis.get('prevention_methods', '请咨询专业农技人员')}</p>
                    
                    <h3>治疗方法</h3>
                    <p>{diagnosis.get('treatment_methods', '请咨询专业农技人员')}</p>
                </div>
            </div>
            
            {f'''
            <div class="section">
                <h2 class="section-title">置信度分析</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <strong>总体置信度</strong>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: {diagnosis_result['confidence_analysis'].get('overall_confidence', 0) * 100:.0f}%">
                                {diagnosis_result['confidence_analysis'].get('overall_confidence', 0) * 100:.1f}%
                            </div>
                        </div>
                    </div>
                    <div class="info-card">
                        <strong>视觉置信度</strong>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: {diagnosis_result['confidence_analysis'].get('visual_confidence', 0) * 100:.0f}%">
                                {diagnosis_result['confidence_analysis'].get('visual_confidence', 0) * 100:.1f}%
                            </div>
                        </div>
                    </div>
                    <div class="info-card">
                        <strong>文本置信度</strong>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: {diagnosis_result['confidence_analysis'].get('textual_confidence', 0) * 100:.0f}%">
                                {diagnosis_result['confidence_analysis'].get('textual_confidence', 0) * 100:.1f}%
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            ''' if diagnosis_result.get('confidence_analysis') else ''}
            
            {f'''
            <div class="section">
                <h2 class="section-title">性能指标</h2>
                <div class="info-card">
                    <strong>推理时间</strong>
                    {diagnosis_result['performance'].get('inference_time_ms', 0):.0f} ms
                </div>
            </div>
            ''' if diagnosis_result.get('performance') else ''}
        </div>
        
        <div class="footer">
            <p>报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | WheatAgent 智能诊断系统</p>
            <p>本诊断结果仅供参考，具体防治措施请咨询当地农业专家</p>
        </div>
    </div>
</body>
</html>
"""
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diagnosis_report_{timestamp}.html"
            filepath = self.output_dir / filename
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML 报告生成成功：{filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"HTML 报告生成失败：{e}")
            raise
    
    def generate_report(
        self,
        diagnosis_result: Dict[str, Any],
        image_data: Optional[bytes] = None,
        format: str = "both"
    ) -> Dict[str, Path]:
        """
        生成诊断报告（支持多种格式）
        
        参数:
            diagnosis_result: 诊断结果
            image_data: 原始图像数据
            format: 报告格式（pdf/html/both）
            
        返回:
            生成的文件路径字典
        """
        result = {}
        
        if format in ["pdf", "both"]:
            try:
                result["pdf"] = self.generate_pdf_report(diagnosis_result, image_data)
            except Exception as e:
                logger.error(f"PDF 生成失败：{e}")
        
        if format in ["html", "both"]:
            try:
                result["html"] = self.generate_html_report(diagnosis_result, image_data)
            except Exception as e:
                logger.error(f"HTML 生成失败：{e}")
        
        return result


# 全局实例
_report_generator = None


def get_report_generator() -> ReportGenerator:
    """获取报告生成器实例"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator

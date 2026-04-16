# -*- coding: utf-8 -*-
"""
IWDDA诊断报告生成器

根据文档规范生成结构化诊断报告
支持多种输出格式: JSON, Markdown, HTML
支持GraphRAG引用溯源功能
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ReportTemplate:
    """报告模板"""
    title: str = "小麦病害诊断报告"
    subtitle: str = "基于多模态特征融合的智能诊断"
    organization: str = "IWDDA智能诊断系统"
    version: str = "2.0.0"


@dataclass
class KnowledgeCitation:
    """知识引用"""
    source: str
    entity_type: str
    entity_name: str
    relation: str
    confidence: float = 1.0
    evidence: str = ""


@dataclass
class DiagnosisReport:
    """诊断报告数据结构"""
    disease_name: str = ""
    confidence: float = 0.0
    severity: str = "未知"
    pathogen: str = "未知"
    symptoms: List[str] = field(default_factory=list)
    causes: List[str] = field(default_factory=list)
    preventions: List[str] = field(default_factory=list)
    treatments: Dict[str, List[str]] = field(default_factory=dict)
    environmental_factors: Dict[str, str] = field(default_factory=dict)
    related_diseases: List[str] = field(default_factory=list)
    reasoning_chain: List[str] = field(default_factory=list)
    citations: List[KnowledgeCitation] = field(default_factory=list)
    knowledge_context: str = ""
    visual_evidence: str = ""
    text_evidence: str = ""


class ReportGenerator:
    """
    诊断报告生成器
    
    生成符合文档规范的结构化诊断报告
    支持GraphRAG引用溯源功能
    """
    
    def __init__(self, template: Optional[ReportTemplate] = None):
        """
        初始化报告生成器
        
        :param template: 报告模板
        """
        self.template = template or ReportTemplate()
        self._citations: List[KnowledgeCitation] = []
    
    def add_citation(
        self,
        source: str,
        entity_type: str,
        entity_name: str,
        relation: str,
        confidence: float = 1.0,
        evidence: str = ""
    ) -> None:
        """
        添加知识引用
        
        :param source: 知识来源（如"知识图谱"、"专家库"）
        :param entity_type: 实体类型（如"症状"、"成因"、"治疗"）
        :param entity_name: 实体名称
        :param relation: 关系类型
        :param confidence: 置信度
        :param evidence: 证据描述
        """
        citation = KnowledgeCitation(
            source=source,
            entity_type=entity_type,
            entity_name=entity_name,
            relation=relation,
            confidence=confidence,
            evidence=evidence
        )
        self._citations.append(citation)
    
    def clear_citations(self) -> None:
        """清空引用列表"""
        self._citations = []
    
    def get_citations(self) -> List[Dict[str, Any]]:
        """
        获取所有引用
        
        :return: 引用列表
        """
        return [
            {
                "source": c.source,
                "entity_type": c.entity_type,
                "entity_name": c.entity_name,
                "relation": c.relation,
                "confidence": c.confidence,
                "evidence": c.evidence
            }
            for c in self._citations
        ]
    
    def generate_from_graphrag(
        self,
        graphrag_report: Dict[str, Any],
        visual_evidence: str = "",
        text_evidence: str = ""
    ) -> DiagnosisReport:
        """
        从GraphRAG报告生成诊断报告
        
        :param graphrag_report: GraphRAG引擎生成的报告
        :param visual_evidence: 视觉证据
        :param text_evidence: 文本证据
        :return: DiagnosisReport实例
        """
        report = DiagnosisReport()
        
        report.disease_name = graphrag_report.get("diagnosis", "未知")
        report.confidence = graphrag_report.get("confidence", 0.0)
        report.knowledge_context = graphrag_report.get("knowledge_context", "")
        report.reasoning_chain = graphrag_report.get("reasoning_chain", [])
        report.related_diseases = graphrag_report.get("related_diseases", [])
        report.visual_evidence = visual_evidence
        report.text_evidence = text_evidence
        
        # 提取症状
        symptoms_data = graphrag_report.get("symptoms", [])
        report.symptoms = [
            s.get("name", "") if isinstance(s, dict) else str(s)
            for s in symptoms_data
        ]
        
        # 提取成因
        causes_data = graphrag_report.get("causes", [])
        report.causes = [
            c.get("name", "") if isinstance(c, dict) else str(c)
            for c in causes_data
        ]
        
        # 提取预防措施
        preventions_data = graphrag_report.get("preventions", [])
        report.preventions = [
            p.get("name", "") if isinstance(p, dict) else str(p)
            for p in preventions_data
        ]
        
        # 提取治疗措施
        treatments_data = graphrag_report.get("treatments", [])
        report.treatments = {
            "chemical": [],
            "biological": [],
            "cultural": []
        }
        
        for t in treatments_data:
            if isinstance(t, dict):
                name = t.get("name", "")
                usage = t.get("usage", "")
                if usage:
                    report.treatments["chemical"].append(f"{name}（{usage}）")
                else:
                    report.treatments["chemical"].append(name)
        
        # 生成引用
        self._generate_citations_from_graphrag(graphrag_report)
        report.citations = self._citations.copy()
        
        return report
    
    def _generate_citations_from_graphrag(self, graphrag_report: Dict[str, Any]) -> None:
        """
        从GraphRAG报告生成引用
        
        :param graphrag_report: GraphRAG报告
        """
        self.clear_citations()
        disease_name = graphrag_report.get("diagnosis", "")
        
        # 症状引用
        for s in graphrag_report.get("symptoms", []):
            if isinstance(s, dict):
                self.add_citation(
                    source="知识图谱",
                    entity_type="症状",
                    entity_name=s.get("name", ""),
                    relation="HAS_SYMPTOM",
                    evidence=f"{disease_name}的典型症状"
                )
        
        # 成因引用
        for c in graphrag_report.get("causes", []):
            if isinstance(c, dict):
                self.add_citation(
                    source="知识图谱",
                    entity_type="成因",
                    entity_name=c.get("name", ""),
                    relation="CAUSED_BY",
                    evidence=f"{disease_name}的诱发因素"
                )
        
        # 预防措施引用
        for p in graphrag_report.get("preventions", []):
            if isinstance(p, dict):
                self.add_citation(
                    source="知识图谱",
                    entity_type="预防措施",
                    entity_name=p.get("name", ""),
                    relation="PREVENTED_BY",
                    evidence=f"{disease_name}的预防方法"
                )
        
        # 治疗措施引用
        for t in graphrag_report.get("treatments", []):
            if isinstance(t, dict):
                self.add_citation(
                    source="知识图谱",
                    entity_type="治疗措施",
                    entity_name=t.get("name", ""),
                    relation="TREATED_BY",
                    evidence=f"{disease_name}的治疗方案"
                )
    
    def generate_json(self, diagnosis_result: Dict[str, Any]) -> str:
        """
        生成JSON格式报告
        
        :param diagnosis_result: 诊断结果字典
        :return: JSON字符串
        """
        report = {
            "report_info": {
                "title": self.template.title,
                "version": self.template.version,
                "generated_at": datetime.now().isoformat(),
                "organization": self.template.organization
            },
            **diagnosis_result
        }
        return json.dumps(report, ensure_ascii=False, indent=2)
    
    def generate_markdown(self, diagnosis_result: Dict[str, Any]) -> str:
        """
        生成Markdown格式报告
        
        :param diagnosis_result: 诊断结果字典
        :return: Markdown字符串
        """
        diagnosis = diagnosis_result.get("diagnosis", {})
        env_factors = diagnosis_result.get("environmental_factors", {})
        treatment = diagnosis_result.get("treatment", {})
        prevention = diagnosis_result.get("prevention", [])
        reasoning = diagnosis_result.get("reasoning_log", [])
        
        md = f"""# {self.template.title}

## 📋 基本信息

| 项目 | 内容 |
|------|------|
| 生成时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 系统版本 | {self.template.version} |
| 诊断机构 | {self.template.organization} |

## 🔬 诊断结果

| 项目 | 内容 |
|------|------|
| **病害名称** | {diagnosis.get("disease_name", "未知")} |
| **置信度** | {diagnosis.get("confidence", 0):.2%} |
| **严重程度** | {diagnosis.get("severity", "未知")} |
| **病原体** | {diagnosis.get("pathogen", "未知")} |

### 症状描述

"""
        symptoms = diagnosis.get("symptoms", [])
        if symptoms:
            for symptom in symptoms:
                md += f"- {symptom}\n"
        else:
            md += "- 暂无症状描述\n"
        
        md += f"""
### 环境因素分析

"""
        if env_factors:
            for key, value in env_factors.items():
                md += f"- **{key}**: {value}\n"
        else:
            md += "- 暂无环境因素分析\n"
        
        md += f"""
## 💊 防治建议

### 化学防治

"""
        chemical = treatment.get("chemical", [])
        if chemical:
            for i, drug in enumerate(chemical, 1):
                md += f"{i}. {drug}\n"
        else:
            md += "- 暂无化学防治建议\n"
        
        md += f"""
### 生物防治

"""
        biological = treatment.get("biological", [])
        if biological:
            for i, method in enumerate(biological, 1):
                md += f"{i}. {method}\n"
        else:
            md += "- 暂无生物防治建议\n"
        
        md += f"""
### 农业措施

"""
        cultural = treatment.get("cultural", [])
        if cultural:
            for i, measure in enumerate(cultural, 1):
                md += f"{i}. {measure}\n"
        else:
            md += "- 暂无农业措施建议\n"
        
        md += f"""
## 🛡️ 预防措施

"""
        if prevention:
            for i, p in enumerate(prevention, 1):
                md += f"{i}. {p}\n"
        else:
            md += "- 暂无预防措施\n"
        
        md += f"""
## 📝 诊断日志

```
"""
        for log in reasoning:
            md += f"{log}\n"
        
        md += f"""```

---

*本报告由 {self.template.organization} 自动生成*
*版本: {self.template.version}*
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        return md
    
    def generate_html(self, diagnosis_result: Dict[str, Any]) -> str:
        """
        生成HTML格式报告
        
        :param diagnosis_result: 诊断结果字典
        :return: HTML字符串
        """
        diagnosis = diagnosis_result.get("diagnosis", {})
        env_factors = diagnosis_result.get("environmental_factors", {})
        treatment = diagnosis_result.get("treatment", {})
        prevention = diagnosis_result.get("prevention", [])
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.template.title}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2e7d32;
            border-bottom: 3px solid #4caf50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #388e3c;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background: #4caf50;
            color: white;
        }}
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        .highlight {{
            background: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .confidence {{
            font-size: 24px;
            font-weight: bold;
            color: #2e7d32;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌾 {self.template.title}</h1>
        <p class="subtitle">{self.template.subtitle}</p>
        
        <h2>📋 诊断结果</h2>
        <table>
            <tr>
                <th>项目</th>
                <th>内容</th>
            </tr>
            <tr>
                <td><strong>病害名称</strong></td>
                <td>{diagnosis.get("disease_name", "未知")}</td>
            </tr>
            <tr>
                <td><strong>置信度</strong></td>
                <td class="confidence">{diagnosis.get("confidence", 0):.2%}</td>
            </tr>
            <tr>
                <td><strong>严重程度</strong></td>
                <td>{diagnosis.get("severity", "未知")}</td>
            </tr>
            <tr>
                <td><strong>病原体</strong></td>
                <td>{diagnosis.get("pathogen", "未知")}</td>
            </tr>
        </table>
        
        <h2>🔍 症状描述</h2>
        <div class="highlight">
            <ul>
"""
        symptoms = diagnosis.get("symptoms", [])
        for symptom in symptoms:
            html += f"                <li>{symptom}</li>\n"
        
        html += f"""            </ul>
        </div>
        
        <h2>💊 防治建议</h2>
        <h3>化学防治</h3>
        <ul>
"""
        chemical = treatment.get("chemical", [])
        for drug in chemical:
            html += f"            <li>{drug}</li>\n"
        
        html += f"""        </ul>
        
        <h3>农业措施</h3>
        <ul>
"""
        cultural = treatment.get("cultural", [])
        for measure in cultural:
            html += f"            <li>{measure}</li>\n"
        
        html += f"""        </ul>
        
        <h2>🛡️ 预防措施</h2>
        <ul>
"""
        for p in prevention:
            html += f"            <li>{p}</li>\n"
        
        html += f"""        </ul>
        
        <div class="footer">
            <p>本报告由 {self.template.organization} 自动生成</p>
            <p>版本: {self.template.version} | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def save_report(
        self,
        diagnosis_result: Dict[str, Any],
        output_path: str,
        format: str = "json"
    ) -> str:
        """
        保存报告到文件
        
        :param diagnosis_result: 诊断结果
        :param output_path: 输出路径
        :param format: 格式 (json/markdown/html)
        :return: 保存的文件路径
        """
        if format == "json":
            content = self.generate_json(diagnosis_result)
            ext = ".json"
        elif format == "markdown":
            content = self.generate_markdown(diagnosis_result)
            ext = ".md"
        elif format == "html":
            content = self.generate_html(diagnosis_result)
            ext = ".html"
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        if not output_path.endswith(ext):
            output_path += ext
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path


def create_report_generator(config: Optional[Dict[str, Any]] = None) -> ReportGenerator:
    """
    工厂函数: 创建报告生成器实例
    
    :param config: 配置字典
    :return: ReportGenerator实例
    """
    template = ReportTemplate()
    
    if config:
        template.title = config.get("title", template.title)
        template.subtitle = config.get("subtitle", template.subtitle)
        template.organization = config.get("organization", template.organization)
        template.version = config.get("version", template.version)
    
    return ReportGenerator(template)


def generate_report_with_citations(
    graphrag_report: Dict[str, Any],
    visual_evidence: str = "",
    text_evidence: str = "",
    output_format: str = "markdown"
) -> str:
    """
    生成带有引用溯源的诊断报告
    
    :param graphrag_report: GraphRAG引擎生成的报告
    :param visual_evidence: 视觉证据
    :param text_evidence: 文本证据
    :param output_format: 输出格式 (markdown/json/html)
    :return: 格式化的报告字符串
    """
    generator = ReportGenerator()
    
    # 从GraphRAG报告生成DiagnosisReport
    report = generator.generate_from_graphrag(
        graphrag_report,
        visual_evidence,
        text_evidence
    )
    
    # 获取引用
    citations = generator.get_citations()
    
    if output_format == "json":
        return _generate_json_with_citations(report, citations)
    elif output_format == "html":
        return _generate_html_with_citations(report, citations)
    else:
        return _generate_markdown_with_citations(report, citations)


def _generate_markdown_with_citations(
    report: DiagnosisReport,
    citations: List[Dict[str, Any]]
) -> str:
    """
    生成带有引用的Markdown报告
    
    :param report: 诊断报告
    :param citations: 引用列表
    :return: Markdown字符串
    """
    md = f"""# 小麦病害诊断报告

## 📋 基本信息

| 项目 | 内容 |
|------|------|
| 生成时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 系统版本 | 2.0.0 |
| 诊断机构 | IWDDA智能诊断系统 |

## 🔬 诊断结果

| 项目 | 内容 |
|------|------|
| **病害名称** | {report.disease_name} |
| **置信度** | {report.confidence:.2%} |
| **严重程度** | {report.severity} |
| **病原体** | {report.pathogen} |

### 症状描述

"""
    if report.symptoms:
        for symptom in report.symptoms:
            md += f"- {symptom}\n"
    else:
        md += "- 暂无症状描述\n"
    
    md += f"""
### 环境因素分析

"""
    if report.environmental_factors:
        for key, value in report.environmental_factors.items():
            md += f"- **{key}**: {value}\n"
    else:
        md += "- 暂无环境因素分析\n"
    
    md += f"""
## 💊 防治建议

### 化学防治

"""
    chemical = report.treatments.get("chemical", [])
    if chemical:
        for i, drug in enumerate(chemical, 1):
            md += f"{i}. {drug}\n"
    else:
        md += "- 暂无化学防治建议\n"
    
    md += f"""
### 生物防治

"""
    biological = report.treatments.get("biological", [])
    if biological:
        for i, method in enumerate(biological, 1):
            md += f"{i}. {method}\n"
    else:
        md += "- 暂无生物防治建议\n"
    
    md += f"""
### 农业措施

"""
    cultural = report.treatments.get("cultural", [])
    if cultural:
        for i, measure in enumerate(cultural, 1):
            md += f"{i}. {measure}\n"
    else:
        md += "- 暂无农业措施建议\n"
    
    md += f"""
## 🛡️ 预防措施

"""
    if report.preventions:
        for i, p in enumerate(report.preventions, 1):
            md += f"{i}. {p}\n"
    else:
        md += "- 暂无预防措施\n"
    
    # 添加引用溯源部分
    md += f"""
## 📚 知识引用溯源

> 本报告的诊断结论基于以下知识来源：

| 序号 | 来源 | 类型 | 实体 | 关系 | 证据 |
|------|------|------|------|------|------|
"""
    for i, c in enumerate(citations, 1):
        md += f"| {i} | {c['source']} | {c['entity_type']} | {c['entity_name']} | {c['relation']} | {c['evidence']} |\n"
    
    # 添加推理链
    md += f"""
## 🔍 推理链

```
"""
    for log in report.reasoning_chain:
        md += f"{log}\n"
    
    md += f"""```

---

*本报告由 IWDDA智能诊断系统 自动生成*
*版本: 2.0.0*
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    return md


def _generate_json_with_citations(
    report: DiagnosisReport,
    citations: List[Dict[str, Any]]
) -> str:
    """
    生成带有引用的JSON报告
    
    :param report: 诊断报告
    :param citations: 引用列表
    :return: JSON字符串
    """
    report_dict = {
        "report_info": {
            "title": "小麦病害诊断报告",
            "version": "2.0.0",
            "generated_at": datetime.now().isoformat(),
            "organization": "IWDDA智能诊断系统"
        },
        "diagnosis": {
            "disease_name": report.disease_name,
            "confidence": report.confidence,
            "severity": report.severity,
            "pathogen": report.pathogen
        },
        "symptoms": report.symptoms,
        "causes": report.causes,
        "preventions": report.preventions,
        "treatments": report.treatments,
        "environmental_factors": report.environmental_factors,
        "related_diseases": report.related_diseases,
        "reasoning_chain": report.reasoning_chain,
        "citations": citations,
        "knowledge_context": report.knowledge_context
    }
    return json.dumps(report_dict, ensure_ascii=False, indent=2)


def _generate_html_with_citations(
    report: DiagnosisReport,
    citations: List[Dict[str, Any]]
) -> str:
    """
    生成带有引用的HTML报告
    
    :param report: 诊断报告
    :param citations: 引用列表
    :return: HTML字符串
    """
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小麦病害诊断报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2e7d32;
            border-bottom: 3px solid #4caf50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #388e3c;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background: #4caf50;
            color: white;
        }}
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        .highlight {{
            background: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .confidence {{
            font-size: 24px;
            font-weight: bold;
            color: #2e7d32;
        }}
        .citation {{
            background: #fff3e0;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #ff9800;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌾 小麦病害诊断报告</h1>
        <p class="subtitle">基于多模态特征融合的智能诊断</p>
        
        <h2>📋 诊断结果</h2>
        <table>
            <tr>
                <th>项目</th>
                <th>内容</th>
            </tr>
            <tr>
                <td><strong>病害名称</strong></td>
                <td>{report.disease_name}</td>
            </tr>
            <tr>
                <td><strong>置信度</strong></td>
                <td class="confidence">{report.confidence:.2%}</td>
            </tr>
            <tr>
                <td><strong>严重程度</strong></td>
                <td>{report.severity}</td>
            </tr>
            <tr>
                <td><strong>病原体</strong></td>
                <td>{report.pathogen}</td>
            </tr>
        </table>
        
        <h2>🔍 症状描述</h2>
        <div class="highlight">
            <ul>
"""
    for symptom in report.symptoms:
        html += f"                <li>{symptom}</li>\n"
    
    html += f"""            </ul>
        </div>
        
        <h2>💊 防治建议</h2>
        <h3>化学防治</h3>
        <ul>
"""
    for drug in report.treatments.get("chemical", []):
        html += f"            <li>{drug}</li>\n"
    
    html += f"""        </ul>
        
        <h3>预防措施</h3>
        <ul>
"""
    for p in report.preventions:
        html += f"            <li>{p}</li>\n"
    
    # 添加引用溯源部分
    html += f"""        </ul>
        
        <h2>📚 知识引用溯源</h2>
        <div class="citation">
            <p><strong>本报告的诊断结论基于以下知识来源：</strong></p>
            <table>
                <tr>
                    <th>序号</th>
                    <th>来源</th>
                    <th>类型</th>
                    <th>实体</th>
                    <th>关系</th>
                </tr>
"""
    for i, c in enumerate(citations, 1):
        html += f"""                <tr>
                    <td>{i}</td>
                    <td>{c['source']}</td>
                    <td>{c['entity_type']}</td>
                    <td>{c['entity_name']}</td>
                    <td>{c['relation']}</td>
                </tr>
"""
    
    html += f"""            </table>
        </div>
        
        <div class="footer">
            <p>本报告由 IWDDA智能诊断系统 自动生成</p>
            <p>版本: 2.0.0 | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>
"""
    return html

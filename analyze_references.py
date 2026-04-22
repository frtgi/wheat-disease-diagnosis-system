#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开题报告参考文献分析脚本
"""
import re
import json
from docx import Document
from collections import defaultdict, Counter


def read_docx_content(file_path):
    """读取Word文档完整内容"""
    doc = Document(file_path)
    full_text = []
    paragraphs = []
    
    i = 0
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
            paragraphs.append({
                'index': i,
                'text': para.text,
                'style': para.style.name if para.style else ''
            })
            i += 1
    
    return '\n'.join(full_text), paragraphs


def extract_references(paragraphs):
    """提取所有参考文献信息"""
    references = []
    in_references_section = False
    ref_pattern = re.compile(r'^\[(\d+)\]\s*')
    
    for para in paragraphs:
        text = para['text'].strip()
        
        if '参考文献' in text or '参考文献' in text:
            in_references_section = True
            continue
        
        if in_references_section:
            match = ref_pattern.match(text)
            if match:
                ref_num = int(match.group(1))
                ref_content = text[match.end():].strip()
                references.append({
                    'number': ref_num,
                    'content': ref_content,
                    'raw_text': text
                })
            elif text and references:
                references[-1]['content'] += ' ' + text
    
    return references


def parse_reference_info(ref):
    """解析参考文献的详细信息"""
    info = {
        'number': ref['number'],
        'raw_text': ref['raw_text'],
        'content': ref['content'],
        'type': 'unknown',
        'authors': [],
        'title': '',
        'source': '',
        'year': '',
        'field': ''
    }
    
    text = ref['content']
    
    # 尝试识别参考文献类型
    if '期刊' in text or '学报' in text or '杂志' in text:
        info['type'] = '期刊论文'
    elif '会议' in text or 'Conference' in text or 'Proc' in text:
        info['type'] = '会议论文'
    elif '学位论文' in text or '硕士' in text or '博士' in text or '大学' in text and '论文' in text:
        info['type'] = '学位论文'
    elif '出版社' in text or 'Press' in text:
        info['type'] = '图书'
    elif 'http' in text.lower() or 'www' in text.lower():
        info['type'] = '网络资源'
    elif '专利' in text:
        info['type'] = '专利'
    else:
        info['type'] = '其他'
    
    # 提取年份
    year_match = re.search(r'(\d{4})', text)
    if year_match:
        info['year'] = year_match.group(1)
    
    # 识别领域
    if '小麦' in text or '病害' in text or '农业' in text or '植保' in text:
        info['field'] = '农业/植物保护'
    elif '深度学习' in text or '神经网络' in text or 'CNN' in text or 'YOLO' in text:
        info['field'] = '计算机视觉/深度学习'
    elif '多模态' in text or '融合' in text or '视觉' in text:
        info['field'] = '多模态融合'
    elif '知识图谱' in text or 'Graph' in text:
        info['field'] = '知识图谱'
    elif '诊断' in text or '检测' in text:
        info['field'] = '智能诊断/检测'
    else:
        info['field'] = '其他'
    
    return info


def find_citation_positions(paragraphs, references):
    """查找参考文献在正文中的引用位置"""
    citations = defaultdict(list)
    
    for para in paragraphs:
        text = para['text']
        para_index = para['index']
        
        # 查找引用标记 [数字]
        citation_matches = re.finditer(r'\[(\d+)\]', text)
        
        for match in citation_matches:
            ref_num = int(match.group(1))
            
            # 获取上下文（前后各100个字符）
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            
            citations[ref_num].append({
                'paragraph_index': para_index,
                'paragraph_text': text,
                'context': context,
                'position': match.start()
            })
    
    return citations


def analyze_references(doc_path, output_path):
    """主分析函数"""
    print(f"正在读取文档: {doc_path}")
    full_text, paragraphs = read_docx_content(doc_path)
    
    print("提取参考文献...")
    references = extract_references(paragraphs)
    print(f"找到 {len(references)} 篇参考文献")
    
    print("解析参考文献信息...")
    parsed_refs = []
    for ref in references:
        parsed_ref = parse_reference_info(ref)
        parsed_refs.append(parsed_ref)
    
    print("查找引用位置...")
    citations = find_citation_positions(paragraphs, references)
    
    print("生成分析报告...")
    report = []
    report.append("=" * 80)
    report.append("开题报告参考文献详细分析报告")
    report.append("=" * 80)
    report.append(f"分析日期: 2026-04-22")
    report.append(f"参考文献总数: {len(references)} 篇")
    report.append("")
    
    # 1. 参考文献详细信息
    report.append("-" * 80)
    report.append("一、参考文献详细信息")
    report.append("-" * 80)
    for ref in parsed_refs:
        report.append(f"\n[{ref['number']}. {ref['content']}")
        report.append(f"   类型: {ref['type']}")
        report.append(f"   年份: {ref['year']}")
        report.append(f"   领域: {ref['field']}")
        report.append(f"   完整原文: {ref['raw_text']}")
    
    # 2. 引用位置和上下文
    report.append("\n" + "-" * 80)
    report.append("二、参考文献引用位置和上下文")
    report.append("-" * 80)
    for ref_num in sorted(citations.keys()):
        report.append(f"\n参考文献 [{ref_num}] 被引用 {len(citations[ref_num])} 次:")
        for i, cite in enumerate(citations[ref_num], 1):
            report.append(f"  引用位置 {i}:")
            report.append(f"    段落索引: {cite['paragraph_index']}")
            report.append(f"    上下文: {cite['context']}")
    
    # 3. 引用格式说明
    report.append("\n" + "-" * 80)
    report.append("三、引用格式说明")
    report.append("-" * 80)
    report.append("\n引用格式采用顺序编码制：")
    report.append("1. 正文引用格式: [序号]")
    report.append("2. 参考文献列表格式: [序号] 作者. 标题. 来源. 年份.")
    report.append("3. 正文中的引用按出现顺序编号")
    
    # 4. 参考文献领域分布统计
    report.append("\n" + "-" * 80)
    report.append("四、参考文献领域分布统计")
    report.append("-" * 80)
    
    # 类型统计
    type_counts = Counter(ref['type'] for ref in parsed_refs)
    report.append("\n1. 参考文献类型分布:")
    for ref_type, count in type_counts.items():
        report.append(f"   {ref_type}: {count} 篇")
    
    # 领域统计
    field_counts = Counter(ref['field'] for ref in parsed_refs)
    report.append("\n2. 参考文献领域分布:")
    for field, count in field_counts.items():
        report.append(f"   {field}: {count} 篇")
    
    # 年份统计
    year_counts = Counter(ref['year'] for ref in parsed_refs if ref['year'])
    report.append("\n3. 参考文献年份分布:")
    for year in sorted(year_counts.keys()):
        report.append(f"   {year}年: {year_counts[year]} 篇")
    
    # 5. 参考文献与引用位置映射关系
    report.append("\n" + "-" * 80)
    report.append("五、参考文献与引用位置映射关系")
    report.append("-" * 80)
    
    for ref in parsed_refs:
        ref_num = ref['number']
        cite_count = len(citations.get(ref_num, []))
        report.append(f"\n[{ref_num}] {ref['title'] if ref['title'] else ref['content'][:50]}...")
        report.append(f"   引用次数: {cite_count}")
        if citations.get(ref_num):
            report.append(f"   引用段落索引: {[c['paragraph_index'] for c in citations[ref_num]]}")
    
    # 保存报告
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"分析完成！结果已保存到: {output_path}")
    
    return parsed_refs, citations


if __name__ == "__main__":
    doc_path = "/workspace/开题报告_2210122288 孙敬育_20260107.docx"
    output_path = "/workspace/参考文献详细分析.txt"
    
    analyze_references(doc_path, output_path)

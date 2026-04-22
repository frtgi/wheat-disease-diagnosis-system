#!/usr/bin/env python3
"""
提取开题报告中的参考文献
"""
import os
import sys

try:
    from docx import Document
except ImportError:
    print("正在安装python-docx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx"])
    from docx import Document

def extract_references(docx_path):
    """
    从Word文档中提取参考文献
    """
    if not os.path.exists(docx_path):
        print(f"错误: 文件 {docx_path} 不存在")
        return []
    
    doc = Document(docx_path)
    references = []
    
    # 遍历文档段落寻找参考文献
    in_references = False
    for para in doc.paragraphs:
        text = para.text.strip()
        
        # 检测参考文献标题
        if any(keyword in text for keyword in ["参考文献", "References", "REFERENCES"]):
            in_references = True
            continue
        
        # 如果在参考文献部分，提取内容
        if in_references and text:
            # 检查是否是新的章节标题
            if any(keyword in text for keyword in ["致谢", "附录", "Acknowledge", "Appendix", "========"]):
                break
            
            references.append(text)
    
    return references

if __name__ == "__main__":
    docx_path = "/workspace/开题报告_2210122288 孙敬育_20260107.docx"
    
    print("正在提取参考文献...")
    refs = extract_references(docx_path)
    
    if refs:
        print(f"成功提取 {len(refs)} 条参考文献:")
        print("=" * 80)
        for i, ref in enumerate(refs, 1):
            print(f"[{i}] {ref}")
        print("=" * 80)
        
        # 保存到文件
        output_path = "/workspace/references.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            for ref in refs:
                f.write(ref + "\n")
        print(f"参考文献已保存到: {output_path}")
    else:
        print("未能提取到参考文献，请检查文档格式")

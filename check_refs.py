#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from docx import Document

doc_path = "/workspace/开题报告_2210122288 孙敬育_20260107.docx"
doc = Document(doc_path)

print("检查参考文献区域:")
print("=" * 80)
for i, para in enumerate(doc.paragraphs):
    text = para.text.strip()
    if text:
        # 查找包含参考文献的段落
        if '参考文献' in text or i >= 80 and i <= 120:
            print(f"[{i}] {text}")
            print("-" * 80)

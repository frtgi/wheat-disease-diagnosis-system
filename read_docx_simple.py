#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from docx import Document

doc_path = "/workspace/开题报告_2210122288 孙敬育_20260107.docx"
doc = Document(doc_path)

print("文档段落内容:")
print("=" * 80)
for i, para in enumerate(doc.paragraphs):
    if para.text.strip():
        print(f"[{i}] {para.text}")
        print("-" * 80)

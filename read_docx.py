import docx
import os

# 读取文档
documents = [
    '/workspace/开题报告_2210122288 孙敬育_20260107.docx',
    '/workspace/基于多模态融合的小麦病害诊断系统.docx'
]

for doc_path in documents:
    if os.path.exists(doc_path):
        print(f"正在读取文档: {doc_path}")
        try:
            doc = docx.Document(doc_path)
            content = []
            for para in doc.paragraphs:
                content.append(para.text)
            
            output_path = f"/workspace/{os.path.basename(doc_path).replace('.docx', '.txt')}"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            print(f"文档内容已提取到 {output_path}")
        except Exception as e:
            print(f"读取文档时出错: {e}")
    else:
        print(f"文档不存在: {doc_path}")

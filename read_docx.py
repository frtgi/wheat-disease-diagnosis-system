import docx

def read_docx_content(file_path):
    try:
        doc = docx.Document(file_path)
        content = []
        for paragraph in doc.paragraphs:
            content.append(paragraph.text)
        return '\n'.join(content)
    except Exception as e:
        return f"Error reading file: {str(e)}"

def save_to_file(content, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Content saved to {output_path}")

if __name__ == "__main__":
    # 读取开题报告
    print("Reading proposal document...")
    proposal_path = "/workspace/开题报告_2210122288 孙敬育_20260107.docx"
    proposal_content = read_docx_content(proposal_path)
    save_to_file(proposal_content, "/workspace/开题报告_内容.txt")
    
    # 读取论文草稿
    print("Reading thesis draft document...")
    thesis_path = "/workspace/基于多模态融合的小麦病害诊断系统.docx"
    thesis_content = read_docx_content(thesis_path)
    save_to_file(thesis_content, "/workspace/论文草稿_内容.txt")
    
    print("All documents read successfully!")

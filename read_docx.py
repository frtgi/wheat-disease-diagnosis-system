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

if __name__ == "__main__":
    file_path = "/workspace/开题报告_2210122288 孙敬育_20260107.docx"
    content = read_docx_content(file_path)
    print(content[:5000])  # 只打印前5000字符，避免输出过多

import docx

# 读取开题报告
doc = docx.Document('/开题报告_2210122288 孙敬育_20260107.docx')

# 提取文本内容
content = []
for para in doc.paragraphs:
    content.append(para.text)

# 保存到文件
with open('/workspace/开题报告.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(content))

print('开题报告内容已提取到 /workspace/开题报告.txt')

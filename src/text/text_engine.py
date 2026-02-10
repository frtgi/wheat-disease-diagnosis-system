# 文件路径: WheatAgent/src/text/text_engine.py
import os
import torch
import torch.nn.functional as F
import logging
from transformers import AutoTokenizer, AutoModel, logging as hf_logging

# 1. 设置 HuggingFace 镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 2. 【优化】静默 Transformers 的繁杂警告
hf_logging.set_verbosity_error()
logging.getLogger("transformers").setLevel(logging.ERROR)

class LanguageAgent:
    def __init__(self, model_name='bert-base-chinese'):
        """
        初始化文本智能体
        """
        print(f"🗣️ [Language Agent] 正在加载文本模型: {model_name} ...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            print("✅ [Language Agent] 文本模型加载完毕！")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")

    def get_embedding(self, text):
        """将文本转化为向量 (Embedding)"""
        if not text:
            return torch.zeros(1, 768)
            
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # 取 [CLS] token 的输出作为句向量
        cls_embedding = outputs.last_hidden_state[:, 0, :]
        return cls_embedding

    def compute_similarity(self, text_a, text_b):
        """计算两段文本的语义相似度"""
        vec_a = self.get_embedding(text_a)
        vec_b = self.get_embedding(text_b)
        
        similarity = F.cosine_similarity(vec_a, vec_b)
        score = similarity.item()
        
        # 仅在调试时打印详细信息，保持界面整洁
        # print(f"🧮 [语义比对] '{text_a[:10]}...' vs '{text_b[:10]}...' -> {score:.4f}")
        return score
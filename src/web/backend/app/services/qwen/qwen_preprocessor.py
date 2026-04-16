"""
Qwen3-VL 输入预处理模块
提供图像预处理、提示词构建和聊天模板格式化功能
"""
import logging
from typing import Dict, List, Any, Optional
from PIL import Image

from .qwen_config import PROMPT_TEMPLATES

logger = logging.getLogger(__name__)


class QwenPreprocessor:
    """
    Qwen3-VL 输入预处理器

    职责：
    - 图像预处理和验证
    - 系统提示词构建
    - 多模态/图像/文本查询构建
    - Graph-RAG 上下文注入
    - 消息格式化和模板应用
    """

    def preprocess_image(self, image: Optional[Image.Image]) -> Optional[Image.Image]:
        """
        预处理输入图像

        对图像进行基本验证和格式转换，确保符合模型输入要求。

        Args:
            image: PIL Image 对象

        Returns:
            Optional[Image.Image]: 处理后的图像，如果输入为 None 则返回 None
        """
        if image is None:
            return None

        try:
            if image.mode != 'RGB':
                logger.debug(f"转换图像模式: {image.mode} -> RGB")
                image = image.convert('RGB')

            if image.size[0] < 32 or image.size[1] < 32:
                logger.warning(f"图像尺寸过小: {image.size}，可能影响诊断效果")

            return image

        except Exception as e:
            logger.error(f"图像预处理失败: {e}")
            raise ValueError(f"无效的图像数据: {e}")

    def build_system_prompt(self, enable_thinking: bool = True) -> str:
        """
        构建系统提示词

        根据是否启用 Thinking 模式，返回不同的系统提示词。

        Args:
            enable_thinking: 是否启用 Thinking 推理链模式

        Returns:
            str: 格式化的系统提示词
        """
        base_prompt = PROMPT_TEMPLATES["system_base"]

        if enable_thinking:
            thinking_prompt = PROMPT_TEMPLATES["system_thinking"]
            return base_prompt + thinking_prompt
        else:
            return base_prompt

    def build_multimodal_query(
        self,
        symptoms: str,
        graphrag_context: str = "",
        enable_thinking: bool = True
    ) -> str:
        """
        构建多模态查询（图像 + 文本）

        结合症状描述、Graph-RAG 上下文和 Thinking 模式后缀生成完整查询。

        Args:
            symptoms: 用户描述的症状文本
            graphrag_context: Graph-RAG 检索到的知识上下文
            enable_thinking: 是否启用 Thinking 模式

        Returns:
            str: 完整的多模态查询文本
        """
        query = PROMPT_TEMPLATES["multimodal_query"].format(symptoms=symptoms)

        if graphrag_context:
            query += PROMPT_TEMPLATES["graphrag_context"].format(context=graphrag_context)

        if enable_thinking:
            query += PROMPT_TEMPLATES["thinking_suffix"]

        return query

    def build_image_query(
        self,
        graphrag_context: str = "",
        enable_thinking: bool = True
    ) -> str:
        """
        构建仅图像查询

        Args:
            graphrag_context: Graph-RAG 检索到的知识上下文
            enable_thinking: 是否启用 Thinking 模式

        Returns:
            str: 图像查询文本
        """
        query = PROMPT_TEMPLATES["image_query"]

        if graphrag_context:
            query += PROMPT_TEMPLATES["graphrag_context"].format(context=graphrag_context)

        if enable_thinking:
            query += PROMPT_TEMPLATES["thinking_suffix"]

        return query

    def build_text_query(
        self,
        symptoms: str,
        graphrag_context: str = "",
        enable_thinking: bool = True
    ) -> str:
        """
        构建纯文本查询

        Args:
            symptoms: 用户描述的症状文本
            graphrag_context: Graph-RAG 检索到的知识上下文
            enable_thinking: 是否启用 Thinking 模式

        Returns:
            str: 文本查询文本
        """
        query = PROMPT_TEMPLATES["text_query"].format(symptoms=symptoms)

        if graphrag_context:
            query += PROMPT_TEMPLATES["graphrag_context"].format(context=graphrag_context)

        if enable_thinking:
            query += PROMPT_TEMPLATES["thinking_suffix"]

        return query

    def format_chat_template(
        self,
        image: Optional[Image.Image],
        system_prompt: str,
        query: str,
        has_image: bool = True
    ) -> List[Dict[str, Any]]:
        """
        格式化聊天消息模板

        根据 Qwen3-VL 要求的格式，将系统提示词和用户查询组装成消息列表。

        Args:
            image: 输入图像（可选）
            system_prompt: 系统提示词
            query: 用户查询文本
            has_image: 是否包含图像

        Returns:
            List[Dict]: 格式化后的消息列表，符合 Qwen3-VL 要求
        """
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": system_prompt}]
            }
        ]

        if has_image and image:
            user_content = [
                {"type": "image", "image": image},
                {"type": "text", "text": query}
            ]
        else:
            user_content = [{"type": "text", "text": query}]

        messages.append({
            "role": "user",
            "content": user_content
        })

        return messages


def get_preprocessor() -> QwenPreprocessor:
    """
    获取预处理器实例

    Returns:
        QwenPreprocessor: 预处理器实例
    """
    return QwenPreprocessor()

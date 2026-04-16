"""
Qwen3-VL 推理引擎模块
提供单图推理、批量推理和流式推理功能
"""
import logging
import time
from typing import Dict, Any, Optional, List, Generator
from PIL import Image

from .qwen_config import INFERENCE_PARAMS

logger = logging.getLogger(__name__)


class QwenInferencer:
    """
    Qwen3-VL 推理引擎

    职责：
    - 多模态响应生成（图像+文本）
    - 纯文本降级模式生成
    - 推理参数配置和管理
    - KV Cache 量化支持
    - 推理性能监控和日志记录
    """

    def __init__(
        self,
        max_new_tokens: int = 384,
        temperature_diagnosis: float = 0.1,
        temperature_thinking: float = 0.5,
        top_p: float = 0.85,
        do_sample: bool = False,
        repetition_penalty: float = 1.1,
        max_tokens_thinking: int = 768,
        max_tokens_normal: int = 384,
        kv_cache_quantization: bool = True,
        kv_cache_quantization_bits: int = 4,
        kv_cache_quantization_group_size: int = 64
    ):
        """
        初始化推理引擎

        Args:
            max_new_tokens: 最大生成 token 数
            temperature_diagnosis: 诊断任务温度
            temperature_thinking: Thinking 模式温度
            top_p: 核采样参数
            do_sample: 是否采样
            repetition_penalty: 重复惩罚
            max_tokens_thinking: Thinking 模式最大生成长度
            max_tokens_normal: 普通模式最大生成长度
            kv_cache_quantization: 是否启用 KV Cache 量化
            kv_cache_quantization_bits: KV Cache 量化位数
            kv_cache_quantization_group_size: KV Cache 量化组大小
        """
        self.max_new_tokens = max_new_tokens
        self.temperature_diagnosis = temperature_diagnosis
        self.temperature_thinking = temperature_thinking
        self.top_p = top_p
        self.do_sample = do_sample
        self.repetition_penalty = repetition_penalty
        self.max_tokens_thinking = max_tokens_thinking
        self.max_tokens_normal = max_tokens_normal
        self.kv_cache_quantization = kv_cache_quantization
        self.kv_cache_quantization_bits = kv_cache_quantization_bits
        self.kv_cache_quantization_group_size = kv_cache_quantization_group_size

    def infer_single(
        self,
        model: Any,
        processor: Any,
        image: Optional[Image.Image],
        messages: List[Dict],
        enable_thinking: bool = True
    ) -> str:
        """
        单图多模态推理

        使用 Qwen3-VL 模型生成多模态响应，支持 Thinking 模式和 KV Cache 量化。

        Args:
            model: Qwen3-VL 模型实例
            processor: 处理器实例
            image: 输入图像（可选）
            messages: 格式化的消息列表
            enable_thinking: 是否启用 Thinking 模式

        Returns:
            str: 生成的响应文本

        Raises:
            Exception: 推理过程中发生的错误
        """
        start_time = time.time()

        logger.info("[Qwen 推理] 开始处理输入...")
        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        )

        inputs = inputs.to(model.device)
        logger.info(f"[Qwen 推理] 输入已加载到设备: {model.device}")

        generation_config = self._build_generation_config(enable_thinking)

        logger.info(f"[Qwen 推理] 开始生成 (max_tokens={generation_config['max_new_tokens']}, temp={generation_config['temperature']}, do_sample={generation_config['do_sample']})...")
        logger.info("[Qwen 推理] 正在推理中，请稍候...")

        try:
            generated_ids = model.generate(**inputs, **generation_config)
        except Exception as e:
            error_msg = str(e).lower()
            if self.kv_cache_quantization and ("quantization" in error_msg or "ninja" in error_msg or "backend" in error_msg):
                logger.warning(f"[Qwen 推理] KV Cache 量化失败，回退到非量化模式: {e}")
                del generation_config["cache_implementation"]
                del generation_config["cache_config"]
                generated_ids = model.generate(**inputs, **generation_config)
            else:
                raise

        generation_time = time.time() - start_time
        logger.info(f"[Qwen 推理] 生成完成，耗时 {generation_time:.2f}秒")

        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        result = processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

        result_length = len(result)
        logger.info(f"[Qwen 推理] 响应长度: {result_length} 字符")

        return result

    def infer_batch(
        self,
        model: Any,
        processor: Any,
        batch_data: List[Dict[str, Any]],
        enable_thinking: bool = True
    ) -> List[str]:
        """
        批量推理

        对多个输入进行批量推理，提高吞吐量。

        Args:
            model: Qwen3-VL 模型实例
            processor: 处理器实例
            batch_data: 批量数据列表，每个元素包含 image 和 messages
            enable_thinking: 是否启用 Thinking 模式

        Returns:
            List[str]: 响应文本列表
        """
        results = []

        for idx, data in enumerate(batch_data):
            try:
                logger.info(f"[Qwen 批量推理] 处理第 {idx + 1}/{len(batch_data)} 个样本")
                result = self.infer_single(
                    model=model,
                    processor=processor,
                    image=data.get("image"),
                    messages=data.get("messages", []),
                    enable_thinking=enable_thinking
                )
                results.append(result)
            except Exception as e:
                logger.error(f"[Qwen 批量推理] 第 {idx + 1} 个样本处理失败: {e}")
                results.append("")

        return results

    def stream_infer(
        self,
        model: Any,
        processor: Any,
        image: Optional[Image.Image],
        messages: List[Dict],
        enable_thinking: bool = True
    ) -> Generator[str, None, None]:
        """
        流式推理（生成器）

        逐步生成响应，适用于实时展示的场景。

        Args:
            model: Qwen3-VL 模型实例
            processor: 处理器实例
            image: 输入图像（可选）
            messages: 格式化的消息列表
            enable_thinking: 是否启用 Thinking 模式

        Yields:
            str: 生成的文本片段
        """
        try:
            from transformers import TextIteratorStreamer
            from threading import Thread

            inputs = processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt"
            )

            inputs = inputs.to(model.device)

            generation_config = self._build_generation_config(enable_thinking)

            streamer = TextIteratorStreamer(
                processor.tokenizer,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )

            generation_config["streamer"] = streamer

            thread = Thread(target=model.generate, kwargs={**inputs, **generation_config})
            thread.start()

            for text in streamer:
                yield text

            thread.join()

        except ImportError:
            logger.warning("TextIteratorStreamer 不可用，回退到非流式模式")
            result = self.infer_single(model, processor, image, messages, enable_thinking)
            yield result
        except Exception as e:
            logger.error(f"[Qwen 流式推理] 失败: {e}")
            raise

    def _build_generation_config(self, enable_thinking: bool) -> Dict[str, Any]:
        """
        构建生成配置

        根据 Thinking 模式状态，返回不同的生成参数配置。

        Args:
            enable_thinking: 是否启用 Thinking 模式

        Returns:
            Dict[str, Any]: 生成配置字典
        """
        if enable_thinking:
            generation_config = {
                "max_new_tokens": self.max_tokens_thinking,
                "temperature": self.temperature_thinking,
                "do_sample": True,
                "top_p": self.top_p,
                "repetition_penalty": self.repetition_penalty
            }
            logger.info("[Qwen 推理] Thinking 模式已启用，可能需要更长时间...")
        else:
            generation_config = {
                "max_new_tokens": self.max_tokens_normal,
                "temperature": self.temperature_diagnosis,
                "do_sample": self.do_sample,
                "top_p": self.top_p,
                "repetition_penalty": self.repetition_penalty
            }

        if self.kv_cache_quantization:
            if self.kv_cache_quantization_bits in [2, 4]:
                backend = "quanto"
            else:
                backend = "HQQ"
            generation_config["cache_implementation"] = "quantized"
            generation_config["cache_config"] = {
                "backend": backend,
                "nbits": self.kv_cache_quantization_bits,
                "q_group_size": self.kv_cache_quantization_group_size,
                "residual_length": 128,
            }
            logger.info(f"[Qwen 推理] KV Cache 量化已启用 (backend={backend}, bits={self.kv_cache_quantization_bits}, group_size={self.kv_cache_quantization_group_size})")

        return generation_config


def get_inferencer(**kwargs) -> QwenInferencer:
    """
    获取推理引擎实例

    Args:
        **kwargs: 推理参数配置

    Returns:
        QwenInferencer: 推理引擎实例
    """
    return QwenInferencer(**kwargs)

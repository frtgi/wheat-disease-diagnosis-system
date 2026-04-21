"""
AI 服务配置模块
提供 AI 模型配置和参数管理
包含系统层优化配置：CUDA 内存分配、异步推理队列、图像预处理、动态批处理
"""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class AIConfig(BaseModel):
    """AI 服务配置类（增强版）

    包含以下配置模块：
    1. 模型路径配置
    2. 推理参数配置
    3. CUDA 内存分配策略配置
    4. 异步推理队列配置
    5. 图像预处理配置
    6. 动态批处理配置
    """

    # ==================== 模型路径配置 ====================
    # 模型路径（修正为正确的相对路径）
    # 当前文件路径：app/core/ai_config.py
    # 目录层级：app -> backend -> web -> src -> WheatAgent (项目根目录)
    # 需要 6 层 parent 才能到达项目根目录
    # 使用 2B 模型以优化 RTX 3050 (4GB 显存) 的性能
    QWEN_MODEL_PATH: Path = Path(__file__).parent.parent.parent.parent.parent.parent / "models" / "Qwen3-VL-2B-Instruct"

    # YOLO 模型路径配置
    # 优先使用训练好的模型，如果不存在则使用预训练模型
    _PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent.parent.parent
    _YOLO_TRAINED_MODEL: Path = _PROJECT_ROOT / "models" / "wheat_disease_v10_yolov8s" / "phase1_warmup" / "weights" / "best.pt"
    _YOLO_PRETRAINED_MODEL: str = "yolov8s.pt"

    YOLO_MODEL_PATH: Optional[Path] = None
    YOLO_USE_PRETRAINED: bool = False

    # YOLOv8 配置
    YOLO_MODEL_FILE: Optional[str] = "best.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.5
    YOLO_IOU_THRESHOLD: float = 0.45
    YOLO_MAX_DETECTIONS: int = 100

    # ==================== Qwen3-VL 配置 ====================
    QWEN_DEVICE: str = "cuda"  # cuda 或 cpu
    QWEN_MAX_LENGTH: int = 512  # 优化：减少到 512 以提升推理速度
    QWEN_TEMPERATURE: float = 0.7

    # 推理参数配置（诊断任务优化）
    # max_new_tokens: 优化从 768 降低到 384，减少生成长度以提升推理速度
    QWEN_MAX_NEW_TOKENS: int = 384

    # temperature: 优化从 0.2 降低到 0.1，进一步降低随机性提高确定性和速度
    QWEN_TEMPERATURE_DIAGNOSIS: float = 0.1

    # temperature: Thinking 模式下可适当提高，保持推理多样性
    QWEN_TEMPERATURE_THINKING: float = 0.5

    # top_p: 优化从 0.9 降低到 0.85，更严格过滤低概率 token
    QWEN_TOP_P: float = 0.85

    # do_sample: 诊断任务建议设为 False，使用贪婪解码提高确定性
    QWEN_DO_SAMPLE: bool = False

    # repetition_penalty: 防止重复生成，建议 1.1-1.2
    QWEN_REPETITION_PENALTY: float = 1.1

    # Thinking 模式下的生成长度（优化从 1024 降低到 768）
    QWEN_MAX_TOKENS_THINKING: int = 768

    # 普通模式下的生成长度（优化从 512 降低到 384）
    QWEN_MAX_TOKENS_NORMAL: int = 384

    # ==================== 高级特性配置 ====================
    QWEN_LOAD_IN_4BIT: bool = True  # 启用 INT4 量化以减少显存占用，使模型能完全在 GPU 上运行
    ENABLE_KAD_FORMER: bool = True  # KAD-Former 知识引导注意力
    ENABLE_GRAPH_RAG: bool = True  # Graph-RAG 上下文增强
    ENABLE_THINKING: bool = False  # 优化：默认禁用 Thinking 模式以提升推理速度
    ENABLE_DEEPSTACK: bool = True  # DeepStack 多层特征注入

    # ==================== 模型层优化配置 ====================
    # Flash Attention 2 加速（需要 flash-attn 包和 Ampere 架构 GPU）
    ENABLE_FLASH_ATTENTION: bool = True

    # KV Cache 量化配置
    KV_CACHE_QUANTIZATION: bool = True  # 启用 KV Cache 量化
    KV_CACHE_QUANTIZATION_BITS: int = 4  # 量化位数（quanto: 2/4, HQQ: 1/2/3/4/8）
    KV_CACHE_QUANTIZATION_GROUP_SIZE: int = 64  # 量化组大小

    # ==================== torch.compile 配置 ====================
    TORCH_COMPILE_ENABLE: bool = True  # 启用 torch.compile 优化
    TORCH_COMPILE_MODE: str = "reduce-overhead"  # 编译模式：reduce-overhead, default, max-autotune
    TORCH_COMPILE_FULLGRAPH: bool = False  # 是否编译完整图
    TORCH_COMPILE_DYNAMIC: bool = True  # 是否支持动态形状

    # ==================== 推理配置 ====================
    INFERENCE_TIMEOUT: int = 60  # 秒（增加到 60 支持复杂推理）
    BATCH_SIZE: int = 1

    # ==================== 缓存配置 ====================
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # 秒

    # ==================== 融合权重配置 ====================
    FUSION_WEIGHTS: dict = {
        "vision": 0.6,
        "text": 0.4,
        "knowledge": 0.3
    }

    # ==================== CUDA 内存分配策略配置 ====================
    # CUDA 内存分配器类型：'default' | 'pytorch' | 'cuda_malloc_async'
    CUDA_MEMORY_ALLOCATOR: str = "pytorch"

    # 是否启用 CUDA 内存碎片整理
    CUDA_ENABLE_MEMORY_FRAGMENTATION: bool = True

    # CUDA 内存增长模式：'incremental' | 'all_at_once'
    CUDA_MEMORY_GROWTH: str = "incremental"

    # CUDA 内存增长因子（incremental 模式下）
    CUDA_MEMORY_GROWTH_FACTOR: float = 1.5

    # 是否启用 CUDA 缓存分配器
    CUDA_ENABLE_CACHING_ALLOCATOR: bool = True

    # CUDA 缓存分配器最大分割大小（MB）
    CUDA_MAX_SPLIT_SIZE_MB: int = 512

    # 是否启用 CUDA 垃圾回收
    CUDA_ENABLE_GARBAGE_COLLECTION: bool = True

    # CUDA 垃圾回收阈值（MB）
    CUDA_GC_THRESHOLD_MB: int = 256

    # 是否启用显存监控
    CUDA_ENABLE_MEMORY_MONITORING: bool = True

    # 显存警告阈值（百分比）
    CUDA_MEMORY_WARNING_THRESHOLD: float = 0.85

    # 显存临界阈值（百分比）
    CUDA_MEMORY_CRITICAL_THRESHOLD: float = 0.95

    # ==================== 异步推理队列配置 ====================
    # 最大并发推理数
    INFERENCE_QUEUE_MAX_CONCURRENT: int = 2

    # 队列最大长度
    INFERENCE_QUEUE_MAX_SIZE: int = 100

    # 请求超时时间（秒）
    INFERENCE_QUEUE_TIMEOUT: int = 120

    # 是否启用结果缓存
    INFERENCE_QUEUE_ENABLE_CACHE: bool = True

    # 结果缓存 TTL（秒）
    INFERENCE_QUEUE_CACHE_TTL: int = 1800

    # 队列处理间隔（毫秒）
    INFERENCE_QUEUE_PROCESS_INTERVAL_MS: int = 50

    # 是否启用优先级队列
    INFERENCE_QUEUE_ENABLE_PRIORITY: bool = True

    # 优先级队列级别数
    INFERENCE_QUEUE_PRIORITY_LEVELS: int = 3

    # ==================== 图像预处理配置 ====================
    # 是否启用 GPU 加速预处理
    IMAGE_PREPROCESS_ENABLE_GPU: bool = True

    # 预处理目标尺寸
    IMAGE_PREPROCESS_TARGET_SIZE: tuple = (640, 640)

    # 是否保持宽高比
    IMAGE_PREPROCESS_KEEP_ASPECT_RATIO: bool = True

    # 填充颜色（RGB）
    IMAGE_PREPROCESS_PADDING_COLOR: tuple = (114, 114, 114)

    # 是否启用图像增强
    IMAGE_PREPROCESS_ENABLE_AUGMENTATION: bool = False

    # 图像格式：'RGB' | 'BGR'
    IMAGE_PREPROCESS_COLOR_MODE: str = "RGB"

    # 归一化参数
    IMAGE_PREPROCESS_NORMALIZE_MEAN: tuple = (0.485, 0.456, 0.406)
    IMAGE_PREPROCESS_NORMALIZE_STD: tuple = (0.229, 0.224, 0.225)

    # 是否启用预处理流水线并行化
    IMAGE_PREPROCESS_ENABLE_PIPELINE_PARALLEL: bool = True

    # 预处理流水线工作线程数
    IMAGE_PREPROCESS_PIPELINE_WORKERS: int = 2

    # 预处理批处理大小
    IMAGE_PREPROCESS_BATCH_SIZE: int = 8

    # 是否启用高效图像格式（WebP）
    IMAGE_PREPROCESS_ENABLE_WEBP: bool = False

    # WebP 压缩质量（1-100）
    IMAGE_PREPROCESS_WEBP_QUALITY: int = 85

    # ==================== 动态批处理配置 ====================
    # 是否启用动态批处理
    DYNAMIC_BATCH_ENABLE: bool = True

    # 最大批处理大小
    DYNAMIC_BATCH_MAX_SIZE: int = 16

    # 最小批处理大小
    DYNAMIC_BATCH_MIN_SIZE: int = 1

    # 最大等待时间（毫秒）
    DYNAMIC_BATCH_MAX_WAIT_MS: int = 50

    # 是否启用自适应批处理大小
    DYNAMIC_BATCH_ADAPTIVE_SIZE: bool = True

    # 自适应批处理最小显存（MB）
    DYNAMIC_BATCH_MIN_MEMORY_MB: int = 512

    # 批处理超时时间（秒）
    DYNAMIC_BATCH_TIMEOUT: int = 30

    # 是否启用批处理优先级
    DYNAMIC_BATCH_ENABLE_PRIORITY: bool = True

    # 批处理统计窗口大小
    DYNAMIC_BATCH_STATS_WINDOW: int = 100

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_paths()

    def _validate_paths(self):
        """
        验证模型路径并设置备用方案

        优先检查训练好的 YOLO 模型是否存在，如果不存在则使用预训练模型
        """
        if not self.QWEN_MODEL_PATH.exists():
            print(f"警告：Qwen 模型路径不存在：{self.QWEN_MODEL_PATH}")

        # 检查 YOLO 训练模型是否存在
        if self._YOLO_TRAINED_MODEL.exists():
            self.YOLO_MODEL_PATH = self._YOLO_TRAINED_MODEL
            self.YOLO_USE_PRETRAINED = False
            print(f"YOLO 模型：使用训练模型 {self.YOLO_MODEL_PATH}")
        else:
            # 训练模型不存在，使用预训练模型
            self.YOLO_MODEL_PATH = None
            self.YOLO_USE_PRETRAINED = True
            print(f"警告：YOLO 训练模型不存在：{self._YOLO_TRAINED_MODEL}")
            print(f"YOLO 模型：使用预训练模型 {self._YOLO_PRETRAINED_MODEL}")


# 创建全局配置实例
ai_config = AIConfig()

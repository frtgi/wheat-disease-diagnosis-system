"""
输入预处理瓶颈分析脚本
分析图像编码、tokenization 等预处理流程的性能瓶颈
"""
import time
import sys
import os
import io
import base64
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass, field

import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

_current_file = os.path.abspath(__file__)
_project_root = os.path.normpath(os.path.join(_current_file, '..', '..', '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


@dataclass
class TimingResult:
    """计时结果数据类"""
    operation: str
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "duration_ms": round(self.duration_ms, 3),
            "details": self.details
        }


@dataclass
class BottleneckAnalysis:
    """瓶颈分析结果"""
    category: str
    total_time_ms: float
    operations: List[TimingResult]
    bottleneck_ratio: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "total_time_ms": round(self.total_time_ms, 3),
            "bottleneck_ratio": round(self.bottleneck_ratio * 100, 2),
            "operations": [op.to_dict() for op in self.operations],
            "recommendations": self.recommendations
        }


def _create_test_image(width: int = 640, height: int = 480) -> 'Image.Image':
    """
    创建测试图像
    
    Args:
        width: 图像宽度
        height: 图像高度
        
    Returns:
        PIL Image 对象
    """
    if not PIL_AVAILABLE:
        raise ImportError("PIL 未安装，无法创建测试图像")
    
    np.random.seed(42)
    img_array = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(img_array)


def _time_operation(func, *args, iterations: int = 10, **kwargs) -> Tuple[float, Any]:
    """
    测量函数执行时间
    
    Args:
        func: 要测量的函数
        args: 函数参数
        iterations: 迭代次数
        kwargs: 函数关键字参数
        
    Returns:
        平均执行时间（毫秒）和最后一次执行结果
    """
    times = []
    result = None
    
    for _ in range(iterations):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    return sum(times) / len(times), result


def analyze_image_decoding() -> TimingResult:
    """
    分析图像解码耗时
    
    测量从字节流解码为 PIL Image 的时间
    
    Returns:
        TimingResult: 解码耗时结果
    """
    if not PIL_AVAILABLE:
        return TimingResult("image_decoding", 0, {"error": "PIL 不可用"})
    
    test_image = _create_test_image(1920, 1080)
    
    buffer = io.BytesIO()
    test_image.save(buffer, format="JPEG", quality=85)
    image_bytes = buffer.getvalue()
    
    def decode_image():
        buffer.seek(0)
        return Image.open(io.BytesIO(image_bytes))
    
    avg_time, _ = _time_operation(decode_image, iterations=50)
    
    return TimingResult(
        operation="image_decoding",
        duration_ms=avg_time,
        details={
            "image_size": f"{test_image.width}x{test_image.height}",
            "format": "JPEG",
            "bytes_size": len(image_bytes),
            "iterations": 50
        }
    )


def analyze_image_resize() -> TimingResult:
    """
    分析图像缩放耗时
    
    测量不同缩放算法和尺寸的耗时差异
    
    Returns:
        TimingResult: 缩放耗时结果
    """
    if not PIL_AVAILABLE:
        return TimingResult("image_resize", 0, {"error": "PIL 不可用"})
    
    test_image = _create_test_image(1920, 1080)
    target_sizes = [
        (224, 224),
        (640, 640),
        (1024, 1024)
    ]
    
    results = {}
    
    for target_size in target_sizes:
        def resize_image(img=test_image, size=target_size):
            return img.resize(size, Image.Resampling.LANCZOS)
        
        avg_time, _ = _time_operation(resize_image, iterations=30)
        results[f"{target_size[0]}x{target_size[1]}"] = {
            "avg_time_ms": round(avg_time, 3),
            "algorithm": "LANCZOS"
        }
    
    total_avg = sum(r["avg_time_ms"] for r in results.values()) / len(results)
    
    return TimingResult(
        operation="image_resize",
        duration_ms=total_avg,
        details={
            "source_size": "1920x1080",
            "target_sizes": results
        }
    )


def analyze_image_normalize() -> TimingResult:
    """
    分析图像归一化耗时
    
    测量 PIL Image 转换为 numpy 数组并归一化的时间
    
    Returns:
        TimingResult: 归一化耗时结果
    """
    if not PIL_AVAILABLE:
        return TimingResult("image_normalize", 0, {"error": "PIL 不可用"})
    
    test_image = _create_test_image(640, 480)
    
    def normalize_image():
        img_array = np.array(test_image, dtype=np.float32)
        img_array = img_array / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        normalized = (img_array - mean) / std
        return normalized
    
    avg_time, _ = _time_operation(normalize_image, iterations=100)
    
    return TimingResult(
        operation="image_normalize",
        duration_ms=avg_time,
        details={
            "image_size": "640x480",
            "normalization": "ImageNet标准",
            "iterations": 100
        }
    )


def analyze_base64_encoding() -> TimingResult:
    """
    分析 Base64 编码耗时
    
    测量图像编码为 Base64 字符串的时间
    
    Returns:
        TimingResult: Base64 编码耗时结果
    """
    if not PIL_AVAILABLE:
        return TimingResult("base64_encoding", 0, {"error": "PIL 不可用"})
    
    test_image = _create_test_image(640, 480)
    
    buffer = io.BytesIO()
    test_image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    
    def encode_base64():
        return base64.b64encode(image_bytes).decode("utf-8")
    
    avg_time, _ = _time_operation(encode_base64, iterations=100)
    
    return TimingResult(
        operation="base64_encoding",
        duration_ms=avg_time,
        details={
            "image_size": "640x480",
            "format": "PNG",
            "bytes_size": len(image_bytes),
            "iterations": 100
        }
    )


def analyze_image_hash() -> TimingResult:
    """
    分析图像哈希计算耗时
    
    测量 MD5 和感知哈希计算时间
    
    Returns:
        TimingResult: 哈希计算耗时结果
    """
    if not PIL_AVAILABLE:
        return TimingResult("image_hash", 0, {"error": "PIL 不可用"})
    
    test_image = _create_test_image(640, 480)
    
    buffer = io.BytesIO()
    test_image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    
    def compute_md5():
        return hashlib.md5(image_bytes).hexdigest()
    
    def compute_perceptual_hash():
        img = test_image.convert("L")
        img = img.resize((9, 8), Image.Resampling.LANCZOS)
        pixels = np.array(img)
        diff = pixels[:, 1:] > pixels[:, :-1]
        hash_int = int("".join(str(int(b)) for b in diff.flatten()), 2)
        return f"{hash_int:016x}"
    
    md5_time, _ = _time_operation(compute_md5, iterations=100)
    phash_time, _ = _time_operation(compute_perceptual_hash, iterations=100)
    
    return TimingResult(
        operation="image_hash",
        duration_ms=md5_time + phash_time,
        details={
            "md5_time_ms": round(md5_time, 3),
            "perceptual_hash_time_ms": round(phash_time, 3),
            "iterations": 100
        }
    )


def analyze_image_annotation() -> TimingResult:
    """
    分析图像标注耗时
    
    测量在图像上绘制检测框和标签的时间
    
    Returns:
        TimingResult: 图像标注耗时结果
    """
    if not PIL_AVAILABLE:
        return TimingResult("image_annotation", 0, {"error": "PIL 不可用"})
    
    test_image = _create_test_image(640, 480)
    
    detections = [
        {"bbox": [100, 100, 200, 200], "class_name": "条锈病", "confidence": 0.95},
        {"bbox": [250, 150, 350, 250], "class_name": "白粉病", "confidence": 0.88},
        {"bbox": [400, 200, 500, 300], "class_name": "叶锈病", "confidence": 0.82}
    ]
    
    def annotate_image():
        annotated = test_image.copy()
        draw = ImageDraw.Draw(annotated)
        
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        
        for idx, det in enumerate(detections):
            bbox = det["bbox"]
            color = colors[idx % len(colors)]
            
            draw.rectangle(bbox, outline=color, width=3)
            
            label = f"{det['class_name']} {det['confidence']:.2f}"
            draw.text((bbox[0], bbox[1] - 15), label, fill=color)
        
        buffer = io.BytesIO()
        annotated.save(buffer, format="PNG")
        return buffer.getvalue()
    
    avg_time, _ = _time_operation(annotate_image, iterations=50)
    
    return TimingResult(
        operation="image_annotation",
        duration_ms=avg_time,
        details={
            "image_size": "640x480",
            "detection_count": len(detections),
            "iterations": 50
        }
    )


def analyze_image_preprocessing() -> Dict[str, Any]:
    """
    分析图像预处理耗时
    
    综合分析图像解码、缩放、归一化、编码等预处理流程
    
    Returns:
        Dict: 图像预处理分析结果
    """
    operations = [
        analyze_image_decoding(),
        analyze_image_resize(),
        analyze_image_normalize(),
        analyze_base64_encoding(),
        analyze_image_hash(),
        analyze_image_annotation()
    ]
    
    total_time = sum(op.duration_ms for op in operations)
    
    return {
        "category": "image_preprocessing",
        "total_time_ms": round(total_time, 3),
        "operations": [op.to_dict() for op in operations],
        "bottleneck": max(operations, key=lambda x: x.duration_ms).operation
    }


def analyze_tokenization_basic() -> TimingResult:
    """
    分析基础文本处理耗时
    
    测量文本分割、拼接等基础操作时间
    
    Returns:
        TimingResult: 基础文本处理耗时结果
    """
    test_texts = [
        "叶片出现黄色条纹状病斑，边缘有黄色晕圈",
        "病斑逐渐扩大，融合成不规则形状",
        "严重时叶片枯黄，影响光合作用"
    ]
    
    def process_text():
        combined = " ".join(test_texts)
        words = combined.split()
        return len(words)
    
    avg_time, _ = _time_operation(process_text, iterations=1000)
    
    return TimingResult(
        operation="text_basic_processing",
        duration_ms=avg_time,
        details={
            "text_count": len(test_texts),
            "total_chars": sum(len(t) for t in test_texts),
            "iterations": 1000
        }
    )


def analyze_message_construction() -> TimingResult:
    """
    分析消息构建耗时
    
    测量构建 Qwen3-VL 消息格式的时间
    
    Returns:
        TimingResult: 消息构建耗时结果
    """
    system_prompt = """你是一位专业的小麦病害诊断专家，具备以下能力：
1. 准确识别小麦病害类型（真菌病害、虫害、病毒病害等）
2. 分析病害症状（病斑形状、颜色、分布等）
3. 提供科学的防治建议（农业防治、化学防治、生物防治）
4. 解释病害发生规律和环境因素

请以专业、准确、易懂的方式回答用户问题。"""
    
    symptoms = "叶片出现黄色条纹状病斑，边缘有黄色晕圈，病斑逐渐扩大，融合成不规则形状"
    
    knowledge_context = """
相关知识参考：
条锈病 - 由条形柄锈菌引起 - 主要危害叶片
条锈病 - 症状特征 - 黄色条纹状病斑
条锈病 - 防治方法 - 选用抗病品种
"""
    
    def build_messages():
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": system_prompt}]
            },
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": f"请分析这张小麦病害图像，并结合以下症状描述进行诊断：{symptoms}\n{knowledge_context}"}
                ]
            }
        ]
        return messages
    
    avg_time, _ = _time_operation(build_messages, iterations=1000)
    
    return TimingResult(
        operation="message_construction",
        duration_ms=avg_time,
        details={
            "system_prompt_length": len(system_prompt),
            "symptoms_length": len(symptoms),
            "knowledge_context_length": len(knowledge_context),
            "iterations": 1000
        }
    )


def analyze_prompt_building() -> TimingResult:
    """
    分析提示词构建耗时
    
    测量构建诊断提示词的时间
    
    Returns:
        TimingResult: 提示词构建耗时结果
    """
    symptoms = "叶片出现黄色条纹状病斑，边缘有黄色晕圈"
    graphrag_context = "条锈病 - 由条形柄锈菌引起 - 主要危害叶片"
    
    def build_prompt():
        query = f"请分析这张小麦病害图像，并结合以下症状描述进行诊断：{symptoms}"
        
        if graphrag_context:
            query += f"\n\n相关知识参考：\n{graphrag_context}\n"
        
        query += "\n\n请逐步推理并解释诊断依据。"
        
        return query
    
    avg_time, _ = _time_operation(build_prompt, iterations=1000)
    
    return TimingResult(
        operation="prompt_building",
        duration_ms=avg_time,
        details={
            "symptoms_length": len(symptoms),
            "context_length": len(graphrag_context),
            "iterations": 1000
        }
    )


def analyze_tokenization() -> Dict[str, Any]:
    """
    分析 tokenization 耗时
    
    综合分析文本处理和消息构建的时间
    
    Returns:
        Dict: tokenization 分析结果
    """
    operations = [
        analyze_tokenization_basic(),
        analyze_message_construction(),
        analyze_prompt_building()
    ]
    
    total_time = sum(op.duration_ms for op in operations)
    
    return {
        "category": "tokenization",
        "total_time_ms": round(total_time, 3),
        "operations": [op.to_dict() for op in operations],
        "bottleneck": max(operations, key=lambda x: x.duration_ms).operation
    }


def analyze_tensor_creation() -> TimingResult:
    """
    分析张量创建耗时
    
    测量从 numpy 数组创建 PyTorch 张量的时间
    
    Returns:
        TimingResult: 张量创建耗时结果
    """
    if not TORCH_AVAILABLE:
        return TimingResult("tensor_creation", 0, {"error": "PyTorch 不可用"})
    
    np.random.seed(42)
    
    sizes = [
        (1, 3, 224, 224),
        (1, 3, 640, 640),
        (1, 768),
        (1, 2560)
    ]
    
    results = {}
    
    for size in sizes:
        arr = np.random.randn(*size).astype(np.float32)
        
        def create_tensor(a=arr):
            return torch.from_numpy(a)
        
        avg_time, _ = _time_operation(create_tensor, iterations=100)
        results[str(size)] = round(avg_time, 3)
    
    total_avg = sum(results.values()) / len(results)
    
    return TimingResult(
        operation="tensor_creation",
        duration_ms=total_avg,
        details={
            "tensor_sizes": results,
            "iterations": 100
        }
    )


def analyze_cpu_to_gpu_transfer() -> TimingResult:
    """
    分析 CPU 到 GPU 数据传输耗时
    
    测量张量从 CPU 移动到 GPU 的时间
    
    Returns:
        TimingResult: CPU 到 GPU 传输耗时结果
    """
    if not TORCH_AVAILABLE:
        return TimingResult("cpu_to_gpu_transfer", 0, {"error": "PyTorch 不可用"})
    
    if not torch.cuda.is_available():
        return TimingResult("cpu_to_gpu_transfer", 0, {"error": "CUDA 不可用"})
    
    sizes = [
        (1, 3, 224, 224),
        (1, 3, 640, 640),
        (1, 768),
        (1, 2560)
    ]
    
    results = {}
    
    for size in sizes:
        tensor = torch.randn(*size, dtype=torch.float32)
        
        def transfer_to_gpu(t=tensor):
            return t.cuda()
        
        torch.cuda.synchronize()
        avg_time, _ = _time_operation(transfer_to_gpu, iterations=50)
        torch.cuda.synchronize()
        
        results[str(size)] = {
            "time_ms": round(avg_time, 3),
            "size_mb": round(tensor.element_size() * tensor.numel() / 1024 / 1024, 2)
        }
    
    total_avg = sum(r["time_ms"] for r in results.values()) / len(results)
    
    return TimingResult(
        operation="cpu_to_gpu_transfer",
        duration_ms=total_avg,
        details={
            "transfers": results,
            "iterations": 50,
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
        }
    )


def analyze_multimodal_fusion() -> TimingResult:
    """
    分析多模态特征融合耗时
    
    测量特征拼接和融合操作的时间
    
    Returns:
        TimingResult: 多模态融合耗时结果
    """
    if not TORCH_AVAILABLE:
        return TimingResult("multimodal_fusion", 0, {"error": "PyTorch 不可用"})
    
    visual_features = torch.randn(1, 10, 768)
    text_features = torch.randn(1, 1, 2560)
    knowledge_embeddings = torch.randn(1, 5, 256)
    
    visual_weight = torch.randn(768, 768)
    text_weight = torch.randn(768, 2560)
    knowledge_weight = torch.randn(768, 256)
    
    def fuse_features():
        visual_proj = torch.nn.functional.linear(
            visual_features, 
            visual_weight
        )
        text_proj = torch.nn.functional.linear(
            text_features, 
            text_weight
        )
        knowledge_proj = torch.nn.functional.linear(
            knowledge_embeddings, 
            knowledge_weight
        )
        
        attention_weights = torch.softmax(
            torch.randn(1, 10 + 1 + 5), 
            dim=-1
        )
        
        return attention_weights
    
    avg_time, _ = _time_operation(fuse_features, iterations=100)
    
    return TimingResult(
        operation="multimodal_fusion",
        duration_ms=avg_time,
        details={
            "visual_features": str(visual_features.shape),
            "text_features": str(text_features.shape),
            "knowledge_embeddings": str(knowledge_embeddings.shape),
            "iterations": 100
        }
    )


def analyze_multimodal_input() -> Dict[str, Any]:
    """
    分析多模态输入拼接开销
    
    综合分析张量创建、数据传输和特征融合的时间
    
    Returns:
        Dict: 多模态输入分析结果
    """
    operations = [
        analyze_tensor_creation(),
        analyze_cpu_to_gpu_transfer(),
        analyze_multimodal_fusion()
    ]
    
    total_time = sum(op.duration_ms for op in operations)
    
    return {
        "category": "multimodal_input",
        "total_time_ms": round(total_time, 3),
        "operations": [op.to_dict() for op in operations],
        "bottleneck": max(operations, key=lambda x: x.duration_ms).operation
    }


def analyze_json_serialization() -> TimingResult:
    """
    分析 JSON 序列化耗时
    
    测量诊断结果序列化为 JSON 的时间
    
    Returns:
        TimingResult: JSON 序列化耗时结果
    """
    diagnosis_result = {
        "disease_name": "条锈病",
        "confidence": 0.95,
        "visual_confidence": 0.92,
        "textual_confidence": 0.98,
        "knowledge_confidence": 0.88,
        "description": "叶片出现典型的黄色条纹状病斑，边缘有黄色晕圈，病斑沿叶脉方向排列，符合条锈病的典型症状特征。",
        "recommendations": [
            "选用抗病品种，如济麦22、郑麦9023等",
            "发病初期喷施15%三唑酮可湿性粉剂1000倍液",
            "加强田间管理，合理密植，增强通风透光",
            "清除田间病残体，减少初侵染源"
        ],
        "knowledge_references": [
            {"entity": "条锈病", "relation": "由...引起", "tail": "条形柄锈菌"},
            {"entity": "条锈病", "relation": "主要危害", "tail": "叶片"}
        ],
        "roi_boxes": [
            {"box": [100, 100, 200, 200], "class_name": "条锈病", "confidence": 0.95}
        ]
    }
    
    def serialize_json():
        return json.dumps(diagnosis_result, ensure_ascii=False)
    
    avg_time, _ = _time_operation(serialize_json, iterations=1000)
    
    return TimingResult(
        operation="json_serialization",
        duration_ms=avg_time,
        details={
            "result_keys": len(diagnosis_result),
            "approx_size_bytes": len(json.dumps(diagnosis_result, ensure_ascii=False)),
            "iterations": 1000
        }
    )


def analyze_data_transfer() -> Dict[str, Any]:
    """
    分析数据传输开销
    
    综合分析各种数据传输和序列化操作的时间
    
    Returns:
        Dict: 数据传输分析结果
    """
    operations = [
        analyze_json_serialization(),
        analyze_base64_encoding()
    ]
    
    if TORCH_AVAILABLE:
        operations.append(analyze_cpu_to_gpu_transfer())
    
    total_time = sum(op.duration_ms for op in operations)
    
    return {
        "category": "data_transfer",
        "total_time_ms": round(total_time, 3),
        "operations": [op.to_dict() for op in operations],
        "bottleneck": max(operations, key=lambda x: x.duration_ms).operation
    }


def analyze_knowledge_retrieval_simulation() -> TimingResult:
    """
    分析知识检索模拟耗时
    
    测量模拟 GraphRAG 知识检索的时间
    
    Returns:
        TimingResult: 知识检索耗时结果
    """
    knowledge_base = [
        {"head": "条锈病", "relation": "由...引起", "tail": "条形柄锈菌"},
        {"head": "条锈病", "relation": "主要危害", "tail": "叶片"},
        {"head": "条锈病", "relation": "症状特征", "tail": "黄色条纹状病斑"},
        {"head": "白粉病", "relation": "由...引起", "tail": "禾布氏白粉菌"},
        {"head": "白粉病", "relation": "症状特征", "tail": "白色粉状霉层"},
        {"head": "叶锈病", "relation": "由...引起", "tail": "小麦叶锈菌"},
        {"head": "叶锈病", "relation": "症状特征", "tail": "红褐色圆形病斑"},
    ]
    
    query = "叶片出现黄色条纹状病斑"
    
    def retrieve_knowledge():
        results = []
        query_words = set(query.split())
        
        for triple in knowledge_base:
            score = 0
            for word in query_words:
                if word in triple["tail"] or word in triple["head"]:
                    score += 1
            if score > 0:
                results.append({**triple, "score": score})
        
        return sorted(results, key=lambda x: x["score"], reverse=True)[:3]
    
    avg_time, _ = _time_operation(retrieve_knowledge, iterations=1000)
    
    return TimingResult(
        operation="knowledge_retrieval",
        duration_ms=avg_time,
        details={
            "knowledge_base_size": len(knowledge_base),
            "query_length": len(query),
            "iterations": 1000
        }
    )


def analyze_cache_operations() -> TimingResult:
    """
    分析缓存操作耗时
    
    测量缓存键生成和查询的时间
    
    Returns:
        TimingResult: 缓存操作耗时结果
    """
    test_image = _create_test_image(640, 480)
    
    buffer = io.BytesIO()
    test_image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    
    symptoms = "叶片出现黄色条纹状病斑，边缘有黄色晕圈"
    
    def cache_operations():
        image_hash = hashlib.md5(image_bytes).hexdigest()
        symptoms_hash = hashlib.md5(symptoms.encode()).hexdigest()[:8]
        cache_key = f"image_{image_hash}_{symptoms_hash}"
        return cache_key
    
    avg_time, _ = _time_operation(cache_operations, iterations=1000)
    
    return TimingResult(
        operation="cache_operations",
        duration_ms=avg_time,
        details={
            "image_size": len(image_bytes),
            "symptoms_length": len(symptoms),
            "iterations": 1000
        }
    )


def identify_bottlenecks() -> Dict[str, Any]:
    """
    识别预处理瓶颈
    
    综合分析所有预处理环节，识别主要瓶颈
    
    Returns:
        Dict: 瓶颈识别结果
    """
    all_analyses = [
        analyze_image_preprocessing(),
        analyze_tokenization(),
        analyze_multimodal_input(),
        analyze_data_transfer()
    ]
    
    total_time = sum(a["total_time_ms"] for a in all_analyses)
    
    bottlenecks = []
    for analysis in all_analyses:
        ratio = analysis["total_time_ms"] / total_time if total_time > 0 else 0
        bottlenecks.append({
            "category": analysis["category"],
            "time_ms": analysis["total_time_ms"],
            "ratio": round(ratio * 100, 2)
        })
    
    bottlenecks.sort(key=lambda x: x["ratio"], reverse=True)
    
    recommendations = []
    
    for bn in bottlenecks:
        if bn["category"] == "image_preprocessing" and bn["ratio"] > 30:
            recommendations.extend([
                "考虑使用 GPU 加速图像预处理（如 NVIDIA DALI）",
                "实现图像预处理流水线并行化",
                "使用更高效的图像格式（如 WebP）"
            ])
        elif bn["category"] == "multimodal_input" and bn["ratio"] > 30:
            recommendations.extend([
                "使用 CUDA Streams 实现异步数据传输",
                "预分配 GPU 内存减少分配开销",
                "考虑使用 TensorRT 优化推理"
            ])
        elif bn["category"] == "data_transfer" and bn["ratio"] > 30:
            recommendations.extend([
                "使用更高效的序列化格式（如 MessagePack）",
                "实现批量数据传输减少往返次数",
                "考虑使用共享内存"
            ])
    
    if not recommendations:
        recommendations.append("预处理流程整体均衡，无明显瓶颈")
    
    return {
        "total_preprocessing_time_ms": round(total_time, 3),
        "bottlenecks": bottlenecks,
        "recommendations": recommendations,
        "detailed_analyses": all_analyses
    }


def generate_report() -> str:
    """
    生成分析报告
    
    生成包含所有分析结果的详细报告
    
    Returns:
        str: 格式化的分析报告
    """
    print("=" * 70)
    print("输入预处理瓶颈分析报告")
    print("=" * 70)
    print()
    
    print("1. 图像预处理分析")
    print("-" * 50)
    image_analysis = analyze_image_preprocessing()
    print(f"   总耗时: {image_analysis['total_time_ms']:.3f} ms")
    print(f"   主要瓶颈: {image_analysis['bottleneck']}")
    for op in image_analysis['operations']:
        print(f"   - {op['operation']}: {op['duration_ms']:.3f} ms")
    print()
    
    print("2. Tokenization 分析")
    print("-" * 50)
    token_analysis = analyze_tokenization()
    print(f"   总耗时: {token_analysis['total_time_ms']:.3f} ms")
    print(f"   主要瓶颈: {token_analysis['bottleneck']}")
    for op in token_analysis['operations']:
        print(f"   - {op['operation']}: {op['duration_ms']:.3f} ms")
    print()
    
    print("3. 多模态输入拼接分析")
    print("-" * 50)
    multimodal_analysis = analyze_multimodal_input()
    print(f"   总耗时: {multimodal_analysis['total_time_ms']:.3f} ms")
    print(f"   主要瓶颈: {multimodal_analysis['bottleneck']}")
    for op in multimodal_analysis['operations']:
        print(f"   - {op['operation']}: {op['duration_ms']:.3f} ms")
    print()
    
    print("4. 数据传输分析")
    print("-" * 50)
    transfer_analysis = analyze_data_transfer()
    print(f"   总耗时: {transfer_analysis['total_time_ms']:.3f} ms")
    print(f"   主要瓶颈: {transfer_analysis['bottleneck']}")
    for op in transfer_analysis['operations']:
        print(f"   - {op['operation']}: {op['duration_ms']:.3f} ms")
    print()
    
    print("5. 瓶颈识别与优化建议")
    print("-" * 50)
    bottleneck_result = identify_bottlenecks()
    print(f"   预处理总耗时: {bottleneck_result['total_preprocessing_time_ms']:.3f} ms")
    print()
    print("   各环节耗时占比:")
    for bn in bottleneck_result['bottlenecks']:
        print(f"   - {bn['category']}: {bn['time_ms']:.3f} ms ({bn['ratio']:.1f}%)")
    print()
    print("   优化建议:")
    for i, rec in enumerate(bottleneck_result['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    print()
    print("=" * 70)
    print("分析完成")
    print("=" * 70)
    
    return json.dumps(bottleneck_result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    report_json = generate_report()
    print("\n完整 JSON 报告:")
    print(report_json)

"""
推理引擎瓶颈分析脚本
分析推理参数、KV Cache、批处理等引擎层面的性能瓶颈
"""
import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

_current_file = os.path.abspath(__file__)
_project_root = os.path.normpath(os.path.join(_current_file, '..', '..', '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


@dataclass
class BottleneckIssue:
    """瓶颈问题数据类"""
    severity: str
    category: str
    description: str
    current_value: str
    recommended_value: str
    impact: str
    solution: str


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    category: str
    status: str
    details: Dict[str, Any]
    issues: List[BottleneckIssue]


def analyze_inference_config() -> AnalysisResult:
    """
    分析推理配置参数
    
    检查 max_new_tokens、temperature、do_sample 等参数配置是否合理，
    识别可能导致性能问题的配置。
    
    Returns:
        AnalysisResult: 分析结果，包含配置详情和潜在问题
    """
    try:
        from app.core.ai_config import ai_config
        
        config = {
            "max_new_tokens": ai_config.QWEN_MAX_NEW_TOKENS,
            "temperature_diagnosis": ai_config.QWEN_TEMPERATURE_DIAGNOSIS,
            "temperature_thinking": ai_config.QWEN_TEMPERATURE_THINKING,
            "top_p": ai_config.QWEN_TOP_P,
            "do_sample": ai_config.QWEN_DO_SAMPLE,
            "repetition_penalty": ai_config.QWEN_REPETITION_PENALTY,
            "max_tokens_thinking": ai_config.QWEN_MAX_TOKENS_THINKING,
            "max_tokens_normal": ai_config.QWEN_MAX_TOKENS_NORMAL,
            "batch_size": ai_config.BATCH_SIZE,
            "inference_timeout": ai_config.INFERENCE_TIMEOUT,
            "load_in_4bit": ai_config.QWEN_LOAD_IN_4BIT,
            "enable_thinking": ai_config.ENABLE_THINKING
        }
    except Exception as e:
        config = {
            "error": str(e),
            "max_new_tokens": 768,
            "temperature_diagnosis": 0.2,
            "temperature_thinking": 0.5,
            "top_p": 0.9,
            "do_sample": False,
            "repetition_penalty": 1.1,
            "max_tokens_thinking": 1024,
            "max_tokens_normal": 512,
            "batch_size": 1,
            "inference_timeout": 60,
            "load_in_4bit": True,
            "enable_thinking": False
        }
    
    issues = []
    
    if config.get("max_tokens_thinking", 1024) > 1500:
        issues.append(BottleneckIssue(
            severity="medium",
            category="推理参数",
            description="Thinking 模式 max_tokens 过大",
            current_value=str(config.get("max_tokens_thinking", 1024)),
            recommended_value="512-1024",
            impact="增加推理延迟，可能超时",
            solution="降低 QWEN_MAX_TOKENS_THINKING 到 512-1024"
        ))
    
    if config.get("max_new_tokens", 768) > 1000:
        issues.append(BottleneckIssue(
            severity="medium",
            category="推理参数",
            description="默认 max_new_tokens 过大",
            current_value=str(config.get("max_new_tokens", 768)),
            recommended_value="512-768",
            impact="增加推理时间",
            solution="降低 QWEN_MAX_NEW_TOKENS 到 512-768"
        ))
    
    if config.get("batch_size", 1) == 1:
        issues.append(BottleneckIssue(
            severity="low",
            category="批处理",
            description="批处理大小为 1，无法利用批处理加速",
            current_value="1",
            recommended_value="2-4 (根据显存调整)",
            impact="无法并发处理请求，吞吐量低",
            solution="增加 BATCH_SIZE 到 2-4（需要足够显存）"
        ))
    
    if config.get("enable_thinking", False):
        issues.append(BottleneckIssue(
            severity="medium",
            category="推理参数",
            description="Thinking 模式已启用，会增加推理时间",
            current_value="True",
            recommended_value="False (生产环境)",
            impact="推理时间增加 2-3 倍",
            solution="生产环境禁用 ENABLE_THINKING 或按需启用"
        ))
    
    status = "good" if len(issues) == 0 else "warning" if any(i.severity == "medium" for i in issues) else "critical"
    
    return AnalysisResult(
        category="推理参数配置",
        status=status,
        details=config,
        issues=issues
    )


def check_flash_attention() -> AnalysisResult:
    """
    检查 Flash Attention 可用性
    
    Flash Attention 是一种高效的注意力计算方法，可以显著减少显存占用和计算时间。
    检查当前环境是否支持 Flash Attention。
    
    Returns:
        AnalysisResult: Flash Attention 可用性分析结果
    """
    details = {
        "flash_attn_available": False,
        "flash_attn_version": None,
        "torch_version": None,
        "cuda_version": None,
        "gpu_capability": None,
        "transformers_support": False,
        "model_support": False
    }
    
    issues = []
    
    try:
        import torch
        details["torch_version"] = torch.__version__
        details["cuda_version"] = torch.version.cuda if torch.cuda.is_available() else None
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_capability = torch.cuda.get_device_capability(0)
            details["gpu_capability"] = f"{gpu_capability[0]}.{gpu_capability[1]}"
            details["gpu_name"] = gpu_name
            
            if gpu_capability[0] < 8:
                issues.append(BottleneckIssue(
                    severity="medium",
                    category="Flash Attention",
                    description="GPU 计算能力低于 8.0，不支持 Flash Attention 2",
                    current_value=f"计算能力 {gpu_capability[0]}.{gpu_capability[1]}",
                    recommended_value="计算能力 >= 8.0 (如 RTX 30/40 系列)",
                    impact="无法使用 Flash Attention 2 加速",
                    solution="升级 GPU 或使用 Flash Attention 1 (如果支持)"
                ))
    except Exception as e:
        details["torch_error"] = str(e)
    
    try:
        import flash_attn
        details["flash_attn_available"] = True
        details["flash_attn_version"] = flash_attn.__version__
    except ImportError:
        issues.append(BottleneckIssue(
            severity="medium",
            category="Flash Attention",
            description="flash-attn 库未安装",
            current_value="未安装",
            recommended_value="pip install flash-attn --no-build-isolation",
            impact="无法使用 Flash Attention 加速，显存占用更高",
            solution="安装 flash-attn: pip install flash-attn --no-build-isolation"
        ))
    
    try:
        import transformers
        details["transformers_version"] = transformers.__version__
        
        version_parts = transformers.__version__.split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        
        if major > 4 or (major == 4 and minor >= 36):
            details["transformers_support"] = True
        else:
            issues.append(BottleneckIssue(
                severity="low",
                category="Flash Attention",
                description="transformers 版本过低，不支持 Flash Attention",
                current_value=transformers.__version__,
                recommended_value=">= 4.36.0",
                impact="无法使用 Flash Attention 集成",
                solution="升级 transformers: pip install transformers>=4.36.0"
            ))
    except Exception as e:
        details["transformers_error"] = str(e)
    
    try:
        from app.core.ai_config import ai_config
        model_path = ai_config.QWEN_MODEL_PATH
        if model_path.exists():
            config_file = model_path / "config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    model_config = json.load(f)
                    attn_implementation = model_config.get("_attn_implementation", "eager")
                    details["model_attn_implementation"] = attn_implementation
                    details["model_support"] = attn_implementation in ["flash_attention_2", "sdpa"]
                    
                    if attn_implementation == "eager":
                        issues.append(BottleneckIssue(
                            severity="medium",
                            category="Flash Attention",
                            description="模型使用默认 attention 实现，未启用优化",
                            current_value="eager",
                            recommended_value="flash_attention_2 或 sdpa",
                            impact="显存占用高，推理速度慢",
                            solution="加载模型时指定 attn_implementation='flash_attention_2'"
                        ))
    except Exception as e:
        details["model_check_error"] = str(e)
    
    status = "good" if details["flash_attn_available"] else "warning"
    
    return AnalysisResult(
        category="Flash Attention",
        status=status,
        details=details,
        issues=issues
    )


def analyze_kv_cache() -> AnalysisResult:
    """
    分析 KV Cache 使用情况
    
    KV Cache 是 Transformer 推理的关键优化技术。分析当前配置是否合理利用 KV Cache。
    
    Returns:
        AnalysisResult: KV Cache 分析结果
    """
    details = {
        "kv_cache_enabled": True,
        "kv_cache_dtype": None,
        "use_cache_config": None,
        "max_cache_size": None,
        "estimated_cache_memory_mb": None,
        "gpu_memory_status": None
    }
    
    issues = []
    
    try:
        import torch
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**2
            reserved = torch.cuda.memory_reserved() / 1024**2
            total = torch.cuda.get_device_properties(0).total_memory / 1024**2
            
            details["gpu_memory_status"] = {
                "allocated_mb": round(allocated, 2),
                "reserved_mb": round(reserved, 2),
                "total_mb": round(total, 2),
                "utilization_percent": round(allocated / total * 100, 2)
            }
            
            if allocated / total > 0.85:
                issues.append(BottleneckIssue(
                    severity="high",
                    category="KV Cache",
                    description="GPU 显存使用率过高",
                    current_value=f"{round(allocated/total*100, 1)}%",
                    recommended_value="< 80%",
                    impact="可能导致 OOM，KV Cache 空间不足",
                    solution="减少 batch_size 或启用 CPU Offload"
                ))
    except Exception as e:
        details["gpu_error"] = str(e)
    
    try:
        from app.core.ai_config import ai_config
        model_path = ai_config.QWEN_MODEL_PATH
        
        if model_path.exists():
            config_file = model_path / "config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    model_config = json.load(f)
                    
                    details["use_cache_config"] = model_config.get("use_cache", True)
                    details["kv_cache_dtype"] = model_config.get("torch_dtype", "float16")
                    
                    num_hidden_layers = model_config.get("num_hidden_layers", 28)
                    hidden_size = model_config.get("hidden_size", 2560)
                    num_attention_heads = model_config.get("num_attention_heads", 20)
                    
                    head_dim = hidden_size // num_attention_heads
                    bytes_per_element = 2 if "16" in str(details["kv_cache_dtype"]) else 4
                    
                    max_seq_len = ai_config.QWEN_MAX_NEW_TOKENS + 512
                    cache_per_token = 2 * num_hidden_layers * num_attention_heads * head_dim * bytes_per_element
                    estimated_cache = (cache_per_token * max_seq_len) / 1024**2
                    
                    details["max_cache_size"] = f"{max_seq_len} tokens"
                    details["estimated_cache_memory_mb"] = round(estimated_cache, 2)
                    
                    if estimated_cache > 1000:
                        issues.append(BottleneckIssue(
                            severity="medium",
                            category="KV Cache",
                            description="预估 KV Cache 显存占用较大",
                            current_value=f"{round(estimated_cache, 1)} MB",
                            recommended_value="< 500 MB",
                            impact="显存压力大，可能限制并发",
                            solution="减少 max_new_tokens 或使用 KV Cache 量化"
                        ))
    except Exception as e:
        details["config_error"] = str(e)
    
    try:
        from app.services.qwen_service import get_qwen_service
        service = get_qwen_service()
        
        if service.is_loaded and service.model is not None:
            if hasattr(service.model, 'config'):
                model_config = service.model.config
                details["model_use_cache"] = getattr(model_config, 'use_cache', True)
                
                if hasattr(service.model, 'generation_config'):
                    gen_config = service.model.generation_config
                    details["generation_use_cache"] = getattr(gen_config, 'use_cache', True)
    except Exception as e:
        details["service_error"] = str(e)
    
    issues.append(BottleneckIssue(
        severity="low",
        category="KV Cache",
        description="未配置 KV Cache 量化",
        current_value="FP16",
        recommended_value="INT8 或 FP8",
        impact="KV Cache 占用显存较多",
        solution="启用 KV Cache 量化: generation_config.cache_implementation='quantized'"
    ))
    
    status = "good"
    if any(i.severity == "high" for i in issues):
        status = "critical"
    elif any(i.severity == "medium" for i in issues):
        status = "warning"
    
    return AnalysisResult(
        category="KV Cache",
        status=status,
        details=details,
        issues=issues
    )


def analyze_batch_processing() -> AnalysisResult:
    """
    分析批处理策略
    
    检查当前批处理配置，分析是否可以有效利用批处理提升吞吐量。
    
    Returns:
        AnalysisResult: 批处理分析结果
    """
    details = {
        "current_batch_size": 1,
        "max_batch_size": None,
        "dynamic_batching": False,
        "padding_strategy": None,
        "memory_per_sample_mb": None,
        "recommended_batch_size": None
    }
    
    issues = []
    
    try:
        from app.core.ai_config import ai_config
        details["current_batch_size"] = ai_config.BATCH_SIZE
        details["inference_timeout"] = ai_config.INFERENCE_TIMEOUT
    except Exception as e:
        details["config_error"] = str(e)
    
    try:
        import torch
        if torch.cuda.is_available():
            total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**2
            gpu_name = torch.cuda.get_device_name(0)
            
            details["gpu_name"] = gpu_name
            details["gpu_total_memory_mb"] = round(total_memory, 2)
            
            if "3050" in gpu_name or "4050" in gpu_name:
                details["max_batch_size"] = 1
                details["memory_per_sample_mb"] = "~3500"
                details["recommended_batch_size"] = 1
            elif "3060" in gpu_name or "4060" in gpu_name:
                details["max_batch_size"] = 2
                details["memory_per_sample_mb"] = "~3000"
                details["recommended_batch_size"] = 2
            elif "3070" in gpu_name or "4070" in gpu_name:
                details["max_batch_size"] = 4
                details["memory_per_sample_mb"] = "~2500"
                details["recommended_batch_size"] = 2
            elif "3080" in gpu_name or "4080" in gpu_name:
                details["max_batch_size"] = 8
                details["memory_per_sample_mb"] = "~2000"
                details["recommended_batch_size"] = 4
            elif "3090" in gpu_name or "4090" in gpu_name:
                details["max_batch_size"] = 16
                details["memory_per_sample_mb"] = "~1500"
                details["recommended_batch_size"] = 8
            else:
                details["max_batch_size"] = max(1, int(total_memory / 4000))
                details["recommended_batch_size"] = max(1, int(total_memory / 6000))
    except Exception as e:
        details["gpu_error"] = str(e)
    
    if details["current_batch_size"] == 1:
        issues.append(BottleneckIssue(
            severity="medium",
            category="批处理",
            description="批处理大小为 1，无法利用并行加速",
            current_value="batch_size=1",
            recommended_value=f"batch_size={details.get('recommended_batch_size', 2)}",
            impact="吞吐量受限，无法并发处理请求",
            solution="根据 GPU 显存增加 BATCH_SIZE"
        ))
    
    if not details.get("dynamic_batching", False):
        issues.append(BottleneckIssue(
            severity="low",
            category="批处理",
            description="未启用动态批处理",
            current_value="静态批处理",
            recommended_value="动态批处理 (continuous batching)",
            impact="请求需要等待批处理填满，延迟增加",
            solution="实现动态批处理或使用 vLLM/TGI 等推理框架"
        ))
    
    try:
        from app.services.batch_processor import BatchProcessor
        details["batch_processor_available"] = True
    except ImportError:
        details["batch_processor_available"] = False
        issues.append(BottleneckIssue(
            severity="low",
            category="批处理",
            description="未找到专用批处理器",
            current_value="无",
            recommended_value="BatchProcessor 或 vLLM",
            impact="无法有效管理并发请求",
            solution="实现 BatchProcessor 或集成 vLLM 推理框架"
        ))
    
    status = "warning" if details["current_batch_size"] == 1 else "good"
    
    return AnalysisResult(
        category="批处理策略",
        status=status,
        details=details,
        issues=issues
    )


def analyze_model_optimization() -> AnalysisResult:
    """
    分析模型优化配置
    
    检查量化、编译优化等配置。
    
    Returns:
        AnalysisResult: 模型优化分析结果
    """
    details = {
        "quantization": None,
        "torch_compile": False,
        "bettertransformer": False,
        "offload_strategy": None,
        "dtype": None
    }
    
    issues = []
    
    try:
        from app.core.ai_config import ai_config
        details["quantization"] = "INT4" if ai_config.QWEN_LOAD_IN_4BIT else "BF16/FP16"
        details["offload_strategy"] = "CPU Offload" if True else "None"
    except Exception as e:
        details["config_error"] = str(e)
    
    try:
        import torch
        if hasattr(torch, 'compile'):
            details["torch_compile_available"] = True
            details["torch_compile"] = False
            
            issues.append(BottleneckIssue(
                severity="low",
                category="模型优化",
                description="未启用 torch.compile 优化",
                current_value="未启用",
                recommended_value="model = torch.compile(model)",
                impact="可能损失 10-30% 性能提升",
                solution="启用 torch.compile: model = torch.compile(model, mode='reduce-overhead')"
            ))
        else:
            details["torch_compile_available"] = False
    except Exception as e:
        details["torch_error"] = str(e)
    
    try:
        import transformers
        if hasattr(transformers, 'BetterTransformer'):
            details["bettertransformer_available"] = True
            details["bettertransformer"] = False
            
            issues.append(BottleneckIssue(
                severity="low",
                category="模型优化",
                description="未启用 BetterTransformer 优化",
                current_value="未启用",
                recommended_value="model = BetterTransformer.transform(model)",
                impact="可能损失 10-20% 性能提升",
                solution="启用 BetterTransformer: model = BetterTransformer.transform(model)"
            ))
        else:
            details["bettertransformer_available"] = False
    except Exception as e:
        details["transformers_error"] = str(e)
    
    try:
        import bitsandbytes as bnb
        details["bitsandbytes_available"] = True
        details["bitsandbytes_version"] = bnb.__version__
    except ImportError:
        details["bitsandbytes_available"] = False
        issues.append(BottleneckIssue(
            severity="medium",
            category="模型优化",
            description="bitsandbytes 未安装，无法使用 INT4 量化",
            current_value="未安装",
            recommended_value="pip install bitsandbytes",
            impact="无法使用 INT4 量化，显存占用更高",
            solution="安装 bitsandbytes: pip install bitsandbytes"
        ))
    
    status = "good" if details.get("quantization") == "INT4" else "warning"
    
    return AnalysisResult(
        category="模型优化",
        status=status,
        details=details,
        issues=issues
    )


def identify_bottlenecks() -> Dict[str, Any]:
    """
    识别推理引擎瓶颈
    
    综合分析所有方面的配置，识别主要性能瓶颈。
    
    Returns:
        Dict[str, Any]: 综合分析结果，包含所有问题和建议
    """
    results = {
        "inference_config": asdict(analyze_inference_config()),
        "flash_attention": asdict(check_flash_attention()),
        "kv_cache": asdict(analyze_kv_cache()),
        "batch_processing": asdict(analyze_batch_processing()),
        "model_optimization": asdict(analyze_model_optimization())
    }
    
    all_issues = []
    for category, result in results.items():
        for issue in result.get("issues", []):
            issue["category"] = result["category"]
            all_issues.append(issue)
    
    all_issues.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("severity", "low"), 2))
    
    critical_issues = [i for i in all_issues if i.get("severity") == "high"]
    medium_issues = [i for i in all_issues if i.get("severity") == "medium"]
    low_issues = [i for i in all_issues if i.get("severity") == "low"]
    
    overall_status = "critical" if critical_issues else "warning" if medium_issues else "good"
    
    results["summary"] = {
        "overall_status": overall_status,
        "total_issues": len(all_issues),
        "critical_count": len(critical_issues),
        "medium_count": len(medium_issues),
        "low_count": len(low_issues),
        "top_issues": all_issues[:5]
    }
    
    return results


def generate_report() -> str:
    """
    生成分析报告
    
    生成详细的推理引擎瓶颈分析报告，包含问题描述和优化建议。
    
    Returns:
        str: 格式化的分析报告
    """
    results = identify_bottlenecks()
    
    report_lines = [
        "=" * 80,
        "推理引擎性能瓶颈分析报告",
        "=" * 80,
        "",
        f"分析时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"整体状态: {results['summary']['overall_status'].upper()}",
        f"发现问题: {results['summary']['total_issues']} 个",
        f"  - 严重: {results['summary']['critical_count']} 个",
        f"  - 中等: {results['summary']['medium_count']} 个",
        f"  - 轻微: {results['summary']['low_count']} 个",
        "",
        "=" * 80,
        "详细分析",
        "=" * 80,
    ]
    
    for category, result in results.items():
        if category == "summary":
            continue
        
        report_lines.extend([
            "",
            f"【{result['category']}】状态: {result['status'].upper()}",
            "-" * 60,
        ])
        
        if result.get("details"):
            report_lines.append("配置详情:")
            for key, value in result["details"].items():
                if value is not None and not key.endswith("_error"):
                    report_lines.append(f"  - {key}: {value}")
        
        if result.get("issues"):
            report_lines.append("")
            report_lines.append("发现问题:")
            for i, issue in enumerate(result["issues"], 1):
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    issue.get("severity", "low"), "⚪"
                )
                report_lines.extend([
                    f"  {i}. {severity_icon} [{issue.get('severity', 'low').upper()}] {issue.get('description', '')}",
                    f"     当前值: {issue.get('current_value', 'N/A')}",
                    f"     建议值: {issue.get('recommended_value', 'N/A')}",
                    f"     影响: {issue.get('impact', 'N/A')}",
                    f"     解决方案: {issue.get('solution', 'N/A')}",
                ])
    
    report_lines.extend([
        "",
        "=" * 80,
        "优先优化建议",
        "=" * 80,
    ])
    
    if results["summary"]["top_issues"]:
        for i, issue in enumerate(results["summary"]["top_issues"], 1):
            report_lines.extend([
                f"",
                f"{i}. [{issue.get('severity', 'low').upper()}] {issue.get('description', '')}",
                f"   解决方案: {issue.get('solution', '')}",
            ])
    else:
        report_lines.append("")
        report_lines.append("未发现明显性能瓶颈，当前配置良好。")
    
    report_lines.extend([
        "",
        "=" * 80,
        "性能优化建议总结",
        "=" * 80,
        "",
        "1. 推理参数优化:",
        "   - 诊断任务使用 do_sample=False (贪婪解码)",
        "   - 温度设置为 0.1-0.3 提高确定性",
        "   - max_new_tokens 控制在 512-768",
        "",
        "2. KV Cache 优化:",
        "   - 启用 KV Cache (use_cache=True)",
        "   - 考虑 KV Cache 量化减少显存占用",
        "   - 监控显存使用避免 OOM",
        "",
        "3. Flash Attention 优化:",
        "   - 安装 flash-attn 库",
        "   - 加载模型时指定 attn_implementation='flash_attention_2'",
        "   - 需要 GPU 计算能力 >= 8.0",
        "",
        "4. 批处理优化:",
        "   - 根据 GPU 显存调整 batch_size",
        "   - 考虑实现动态批处理",
        "   - 使用 vLLM/TGI 等专业推理框架",
        "",
        "5. 模型优化:",
        "   - 使用 INT4 量化减少显存占用",
        "   - 启用 torch.compile 加速",
        "   - 启用 BetterTransformer (如支持)",
        "",
        "=" * 80,
    ])
    
    return "\n".join(report_lines)


def save_report_to_json(output_path: Optional[str] = None) -> str:
    """
    保存分析报告为 JSON 文件
    
    Args:
        output_path: 输出文件路径，默认保存到项目根目录
        
    Returns:
        str: 保存的文件路径
    """
    results = identify_bottlenecks()
    
    if output_path is None:
        output_path = os.path.join(_project_root, "inference_engine_bottleneck_report.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    return output_path


if __name__ == "__main__":
    print(generate_report())
    print("\n正在保存详细报告到 JSON 文件...")
    json_path = save_report_to_json()
    print(f"报告已保存到: {json_path}")

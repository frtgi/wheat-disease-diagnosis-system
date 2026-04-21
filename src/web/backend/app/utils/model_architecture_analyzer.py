"""
模型架构瓶颈分析脚本

分析 Qwen3-VL 模型架构特征，识别性能瓶颈
"""
import os
import json
from datetime import datetime


def analyze_model_architecture() -> dict:
    """
    分析模型架构

    返回:
        模型架构分析结果
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "model": {},
        "architecture": {},
        "bottlenecks": [],
        "recommendations": []
    }

    print("=" * 60)
    print("模型架构分析")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    model_path = os.path.join(base_dir, "models", "Qwen3-VL-2B-Instruct")

    print("\n[1] 模型路径检查")
    print("-" * 40)
    print(f"  模型路径: {model_path}")
    print(f"  路径存在: {os.path.exists(model_path)}")

    if os.path.exists(model_path):
        result["model"]["path"] = model_path
        files = os.listdir(model_path)
        print(f"  模型文件: {len(files)} 个")
        result["model"]["files_count"] = len(files)

        config_path = os.path.join(model_path, "config.json")
        if os.path.exists(config_path):
            print("  配置文件: 存在")
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                result["architecture"]["config"] = config

                print("\n[2] 模型架构参数")
                print("-" * 40)

                text_config = config.get("text_config", {})
                vision_config = config.get("vision_config", {})

                hidden_size = text_config.get("hidden_size", 2560)
                num_layers = text_config.get("num_hidden_layers", 36)
                num_heads = text_config.get("num_attention_heads", 32)
                num_kv_heads = text_config.get("num_key_value_heads", 8)
                vocab_size = text_config.get("vocab_size", 151936)
                intermediate_size = text_config.get("intermediate_size", 9728)
                head_dim = text_config.get("head_dim", 128)
                max_pos = text_config.get("max_position_embeddings", 262144)

                print(f"  隐藏层维度: {hidden_size}")
                print(f"  层数: {num_layers}")
                print(f"  注意力头数: {num_heads}")
                print(f"  KV 头数: {num_kv_heads}")
                print(f"  词表大小: {vocab_size}")
                print(f"  中间层维度: {intermediate_size}")
                print(f"  头维度: {head_dim}")
                print(f"  最大位置编码: {max_pos}")

                result["architecture"]["hidden_size"] = hidden_size
                result["architecture"]["num_layers"] = num_layers
                result["architecture"]["num_attention_heads"] = num_heads
                result["architecture"]["num_kv_heads"] = num_kv_heads
                result["architecture"]["vocab_size"] = vocab_size
                result["architecture"]["intermediate_size"] = intermediate_size
                result["architecture"]["head_dim"] = head_dim
                result["architecture"]["max_position_embeddings"] = max_pos

                print("\n[3] 视觉编码器参数")
                print("-" * 40)
                vision_hidden = vision_config.get("hidden_size", 1024)
                vision_layers = vision_config.get("depth", 24)
                vision_heads = vision_config.get("num_heads", 16)
                vision_config.get("intermediate_size", 4096)
                patch_size = vision_config.get("patch_size", 16)
                deepstack = vision_config.get("deepstack_visual_indexes", [5, 11, 17])

                print(f"  视觉隐藏层维度: {vision_hidden}")
                print(f"  视觉层数: {vision_layers}")
                print(f"  视觉注意力头数: {vision_heads}")
                print(f"  Patch 大小: {patch_size}")
                print(f"  DeepStack 索引: {deepstack}")

                result["architecture"]["vision"] = {
                    "hidden_size": vision_hidden,
                    "num_layers": vision_layers,
                    "num_heads": vision_heads,
                    "patch_size": patch_size,
                    "deepstack_indexes": deepstack
                }

                print("\n[4] 参数量估算")
                print("-" * 40)

                embed_params = vocab_size * hidden_size
                layer_params = 4 * hidden_size * hidden_size + 2 * hidden_size * intermediate_size
                total_params = embed_params + num_layers * layer_params
                total_params_b = total_params / 1e9

                print(f"  估算参数量: {total_params_b:.2f}B")
                result["architecture"]["estimated_parameters_b"] = round(total_params_b, 2)

                int4_memory_mb = total_params * 0.5 / (1024 ** 2)
                print(f"  INT4 显存估算: {int4_memory_mb:.0f}MB")
                result["architecture"]["int4_memory_mb"] = round(int4_memory_mb, 0)

                total_memory_mb = int4_memory_mb * 1.5
                print(f"  总显存估算（含 KV Cache）: {total_memory_mb:.0f}MB")
                result["architecture"]["total_memory_estimate_mb"] = round(total_memory_mb, 0)

                print("\n[5] 计算复杂度分析")
                print("-" * 40)

                seq_length = 1024
                attention_flops = num_layers * 4 * seq_length * hidden_size * hidden_size
                ffn_flops = num_layers * 2 * seq_length * hidden_size * intermediate_size
                total_flops = attention_flops + ffn_flops

                print(f"  注意力计算量: {attention_flops / 1e9:.2f} GFLOPs")
                print(f"  FFN 计算量: {ffn_flops / 1e9:.2f} GFLOPs")
                print(f"  总计算量: {total_flops / 1e9:.2f} GFLOPs")

                result["architecture"]["compute_complexity"] = {
                    "attention_gflops": round(attention_flops / 1e9, 2),
                    "ffn_gflops": round(ffn_flops / 1e9, 2),
                    "total_gflops": round(total_flops / 1e9, 2)
                }

                print("\n[6] 架构瓶颈分析")
                print("-" * 40)

                estimated_memory = result["architecture"].get("total_memory_estimate_mb", 0)
                if estimated_memory > 4000:
                    bottleneck = {
                        "type": "memory_overflow",
                        "severity": "critical",
                        "description": f"模型显存需求 ({estimated_memory:.0f}MB) 超过 GPU 显存 (4096MB)",
                        "impact": 0.95
                    }
                    result["bottlenecks"].append(bottleneck)
                    print(f"  [CRITICAL] 显存溢出 - 模型需要 {estimated_memory:.0f}MB，GPU 仅 4096MB")

                if num_layers > 30:
                    bottleneck = {
                        "type": "deep_network",
                        "severity": "medium",
                        "description": f"模型层数 ({num_layers}) 较多，推理延迟较高",
                        "impact": 0.6
                    }
                    result["bottlenecks"].append(bottleneck)
                    print(f"  [MEDIUM] 深层网络 - {num_layers} 层导致推理延迟")

                ffn_ratio = intermediate_size / hidden_size
                if ffn_ratio > 3:
                    bottleneck = {
                        "type": "large_ffn",
                        "severity": "medium",
                        "description": f"FFN 扩展比 ({ffn_ratio:.1f}x) 较大，计算开销高",
                        "impact": 0.5
                    }
                    result["bottlenecks"].append(bottleneck)
                    print(f"  [MEDIUM] 大型 FFN - 扩展比 {ffn_ratio:.1f}x")

            except Exception as e:
                print(f"  解析配置文件失败: {e}")
                result["model"]["config_error"] = str(e)
        else:
            print("  配置文件不存在")
    else:
        print("  模型路径不存在")
        result["model"]["path_exists"] = False

    print("\n[7] 优化建议")
    print("-" * 40)

    for b in result["bottlenecks"]:
        if b["type"] == "memory_overflow":
            rec = {
                "priority": "critical",
                "title": "显存优化（紧急）",
                "description": "模型显存需求超过 GPU 容量，必须采取措施",
                "expected_improvement": "可避免 OOM，但可能增加延迟"
            }
            result["recommendations"].append(rec)
            print(f"  [CRITICAL] {rec['title']}")

        elif b["type"] == "deep_network":
            rec = {
                "priority": "medium",
                "title": "减少推理层数",
                "description": "考虑使用早退策略或层剪枝",
                "expected_improvement": "可减少推理时间 20-30%"
            }
            result["recommendations"].append(rec)
            print(f"  [MEDIUM] {rec['title']}")

        elif b["type"] == "large_ffn":
            rec = {
                "priority": "medium",
                "title": "FFN 优化",
                "description": "考虑使用更小的 FFN 扩展比",
                "expected_improvement": "可减少计算量 20%"
            }
            result["recommendations"].append(rec)
            print(f"  [MEDIUM] {rec['title']}")

    print("\n" + "=" * 60)

    return result


if __name__ == "__main__":
    result = analyze_model_architecture()

    output_path = os.path.join(os.path.dirname(__file__), "model_architecture_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n分析结果已保存到: {output_path}")

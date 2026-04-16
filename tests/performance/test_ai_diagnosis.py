# -*- coding: utf-8 -*-
"""
AI 诊断 API 性能测试脚本
"""
import requests
import time
import json

base_url = 'http://127.0.0.1:8000'

def test_ai_text_diagnosis():
    """
    测试 AI 文本诊断 API 性能
    """
    print('测试 AI 文本诊断 API...')
    
    iterations = 5
    latencies = []
    
    for i in range(iterations):
        start = time.time()
        r = requests.post(
            f'{base_url}/api/v1/diagnosis/text',
            data={'symptoms': '小麦叶片出现黄色条纹，叶面有白色霉层'}
        )
        elapsed = (time.time() - start) * 1000
        latencies.append(elapsed)
        
        if i == 0:
            print(f'  状态码: {r.status_code}')
            if r.status_code == 200:
                result = r.json()
                print(f'  成功: {result.get("success")}')
                if 'data' in result:
                    data = result['data']
                    print(f'  诊断结果: {data.get("disease_name", "unknown")}')
                    print(f'  置信度: {data.get("confidence", 0):.2%}')
            else:
                print(f'  响应: {r.text[:200]}')
        
        print(f'  请求 {i+1}/{iterations}: {elapsed:.2f}ms')
    
    avg = sum(latencies) / len(latencies)
    print(f'\n  平均响应时间: {avg:.2f}ms')
    print(f'  目标: < 3000ms')
    print(f'  状态: {"✅ 通过" if avg < 3000 else "❌ 未达标"}')
    
    return latencies


def test_ai_multimodal_diagnosis():
    """
    测试 AI 多模态诊断 API 性能
    """
    print('\n测试 AI 多模态诊断 API...')
    
    iterations = 3
    latencies = []
    
    for i in range(iterations):
        start = time.time()
        r = requests.post(
            f'{base_url}/api/v1/diagnosis/multimodal',
            data={'symptoms': '小麦叶片出现黄色条纹'}
        )
        elapsed = (time.time() - start) * 1000
        latencies.append(elapsed)
        
        if i == 0:
            print(f'  状态码: {r.status_code}')
            if r.status_code == 200:
                result = r.json()
                print(f'  成功: {result.get("success")}')
                if 'data' in result:
                    data = result['data']
                    print(f'  诊断结果: {data.get("disease_name", "unknown")}')
            else:
                print(f'  响应: {r.text[:200]}')
        
        print(f'  请求 {i+1}/{iterations}: {elapsed:.2f}ms')
    
    avg = sum(latencies) / len(latencies)
    print(f'\n  平均响应时间: {avg:.2f}ms')
    
    return latencies


def check_gpu_memory():
    """
    检查 GPU 显存使用情况
    """
    print('\n检查 GPU 显存...')
    
    try:
        import torch
        if torch.cuda.is_available():
            print(f'  GPU: {torch.cuda.get_device_name(0)}')
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            allocated = torch.cuda.memory_allocated(0) / (1024**3)
            reserved = torch.cuda.memory_reserved(0) / (1024**3)
            print(f'  总显存: {total:.2f} GB')
            print(f'  已分配: {allocated:.2f} GB')
            print(f'  已预留: {reserved:.2f} GB')
            print(f'  使用率: {allocated/total*100:.1f}%')
        else:
            print('  CUDA 不可用')
    except ImportError:
        print('  PyTorch 未安装')


if __name__ == '__main__':
    print('=' * 60)
    print('🤖 AI 诊断 API 性能测试')
    print('=' * 60)
    
    text_latencies = test_ai_text_diagnosis()
    multimodal_latencies = test_ai_multimodal_diagnosis()
    check_gpu_memory()
    
    print('\n' + '=' * 60)
    print('📋 测试摘要')
    print('=' * 60)
    
    if text_latencies:
        avg_text = sum(text_latencies) / len(text_latencies)
        print(f'  文本诊断平均: {avg_text:.2f}ms (目标: < 3000ms)')
    
    if multimodal_latencies:
        avg_multi = sum(multimodal_latencies) / len(multimodal_latencies)
        print(f'  多模态诊断平均: {avg_multi:.2f}ms')

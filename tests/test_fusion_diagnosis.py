# -*- coding: utf-8 -*-
"""
KAD-Former + GraphRAG 融合诊断 API 测试脚本
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_fusion_diagnosis_text_only():
    """测试仅文本诊断"""
    print("\n=== 测试 1: 仅文本诊断 ===")
    
    url = f"{BASE_URL}/diagnosis/fusion"
    data = {
        "symptoms": "叶片出现黄色条纹状病斑，边缘有红色孢子堆",
        "enable_thinking": "true",
        "use_graph_rag": "true"
    }
    
    response = requests.post(url, data=data)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"成功: {result.get('success')}")
        print(f"消息: {result.get('message')}")
        
        diagnosis = result.get('diagnosis', {})
        print(f"\n病害名称: {diagnosis.get('disease_name', '未知')}")
        print(f"综合置信度: {diagnosis.get('confidence', 0)}")
        print(f"视觉置信度: {diagnosis.get('visual_confidence', 0)}")
        print(f"文本置信度: {diagnosis.get('textual_confidence', 0)}")
        print(f"知识置信度: {diagnosis.get('knowledge_confidence', 0)}")
        
        if diagnosis.get('recommendations'):
            print(f"\n防治建议:")
            for i, rec in enumerate(diagnosis.get('recommendations', [])[:3], 1):
                print(f"  {i}. {rec}")
        
        if result.get('reasoning_chain'):
            print(f"\n推理链:")
            for step in result.get('reasoning_chain', [])[:3]:
                print(f"  - {step}")
        
        performance = result.get('performance', {})
        print(f"\n性能指标:")
        print(f"  推理时间: {performance.get('inference_time_ms', 0)} ms")
        print(f"  缓存命中: {performance.get('cache_hit', False)}")
        print(f"  Thinking 模式: {performance.get('thinking_mode_enabled', False)}")
        print(f"  GraphRAG: {performance.get('graph_rag_enabled', False)}")
    else:
        print(f"错误: {response.text}")
    
    return response.status_code == 200

def test_fusion_diagnosis_with_image():
    """测试图像+文本联合诊断"""
    print("\n=== 测试 2: 图像+文本联合诊断 ===")
    
    # 创建一个测试图像
    from PIL import Image
    import io
    
    # 创建一个简单的测试图像
    img = Image.new('RGB', (224, 224), color='green')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    url = f"{BASE_URL}/diagnosis/fusion"
    files = {
        "image": ("test.png", img_bytes, "image/png")
    }
    data = {
        "symptoms": "叶片出现黄色条纹状病斑",
        "weather": "阴雨",
        "growth_stage": "抽穗期",
        "affected_part": "叶片",
        "enable_thinking": "true",
        "use_graph_rag": "true"
    }
    
    response = requests.post(url, files=files, data=data)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"成功: {result.get('success')}")
        print(f"消息: {result.get('message')}")
        
        diagnosis = result.get('diagnosis', {})
        print(f"\n病害名称: {diagnosis.get('disease_name', '未知')}")
        print(f"综合置信度: {diagnosis.get('confidence', 0)}")
        
        features = result.get('features', {})
        print(f"\n功能状态:")
        print(f"  视觉检测: {features.get('visual_detection', False)}")
        print(f"  文本分析: {features.get('textual_analysis', False)}")
        print(f"  GraphRAG: {features.get('graph_rag_enabled', False)}")
        
        if diagnosis.get('roi_boxes'):
            print(f"\n检测区域:")
            for roi in diagnosis.get('roi_boxes', [])[:3]:
                print(f"  - {roi.get('class_name')}: {roi.get('confidence'):.2%}")
    else:
        print(f"错误: {response.text}")
    
    return response.status_code == 200

def test_health_check():
    """测试健康检查"""
    print("\n=== 测试 3: AI 健康检查 ===")
    
    url = f"{BASE_URL}/diagnosis/health/ai"
    response = requests.get(url)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"状态: {result.get('status')}")
        
        services = result.get('services', {})
        for name, info in services.items():
            loaded = info.get('is_loaded', False)
            print(f"  {name}: {'已加载' if loaded else '未加载'}")
    else:
        print(f"错误: {response.text}")
    
    return response.status_code == 200

def main():
    print("=" * 60)
    print("KAD-Former + GraphRAG 融合诊断 API 测试")
    print("=" * 60)
    
    results = []
    
    # 测试健康检查
    results.append(("健康检查", test_health_check()))
    
    # 测试仅文本诊断
    results.append(("仅文本诊断", test_fusion_diagnosis_text_only()))
    
    # 测试图像+文本联合诊断
    results.append(("图像+文本诊断", test_fusion_diagnosis_with_image()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    passed_count = sum(1 for _, p in results if p)
    print(f"\n总计: {passed_count}/{len(results)} 通过")

if __name__ == "__main__":
    main()

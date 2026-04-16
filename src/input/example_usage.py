"""
输入模块使用示例

本文件展示如何使用 IWDDA Agent 的输入层模块。
"""

import sys
sys.path.insert(0, r'd:\Project\WheatAgent\src')

from input import InputParser, InputValidator, EnvironmentEncoder


def example_1_text_parsing():
    """示例 1: 文本症状解析"""
    print("=" * 60)
    print("示例 1: 文本症状解析")
    print("=" * 60)
    
    parser = InputParser()
    
    # 用户输入的文本描述
    text = "小麦叶片出现褐色椭圆形病斑，有轮纹，最近下雨后发现的"
    
    # 解析文本
    result = parser.parse_text(text)
    
    print(f"输入：{text}")
    print(f"提取的症状：{result['symptoms']}")
    print(f"发病部位：{result['disease_parts']}")
    print(f"严重程度：{result['severity']}")
    print()


def example_2_weather_encoding():
    """示例 2: 天气数据编码"""
    print("=" * 60)
    print("示例 2: 天气数据编码")
    print("=" * 60)
    
    encoder = EnvironmentEncoder()
    
    # 天气数据
    weather = {
        "temperature": 22,
        "humidity": 85,
        "precipitation": 10,
        "weather_condition": "小雨"
    }
    
    # 编码天气
    encoded = encoder.encode_weather(weather)
    
    print(f"天气数据：{weather}")
    print(f"温度：{encoded['temperature']['value']}°C - {encoded['temperature']['category']}")
    print(f"湿度：{encoded['humidity']['value']}% - {encoded['humidity']['category']}")
    print(f"天气风险评分：{encoded['risk_score']}")
    print()


def example_3_risk_assessment():
    """示例 3: 综合风险评估"""
    print("=" * 60)
    print("示例 3: 综合风险评估")
    print("=" * 60)
    
    encoder = EnvironmentEncoder()
    
    # 完整的环境数据
    weather = {
        "temperature": 20,
        "humidity": 88,
        "precipitation": 15,
        "weather_condition": "中雨"
    }
    growth_stage = "抽穗期"
    disease_parts = ["叶片", "叶鞘"]
    
    # 计算风险评分
    risk_info = encoder.calculate_environment_risk_score(
        weather, growth_stage, disease_parts
    )
    
    print(f"生长阶段：{growth_stage}")
    print(f"发病部位：{disease_parts}")
    print(f"综合风险评分：{risk_info['comprehensive_risk']}")
    print(f"风险等级：{risk_info['risk_level']}")
    print()


def example_4_image_validation():
    """示例 4: 图像质量验证"""
    print("=" * 60)
    print("示例 4: 图像质量验证")
    print("=" * 60)
    
    import cv2
    import numpy as np
    import os
    
    validator = InputValidator()
    
    # 创建测试图像
    test_path = r'd:\Project\WheatAgent\example_image.jpg'
    img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    cv2.imwrite(test_path, img)
    
    # 验证图像
    result = validator.validate_image(test_path)
    
    print(f"图像路径：{test_path}")
    print(f"验证结果：{'有效' if result['valid'] else '无效'}")
    print(f"质量评分：{result['quality_score']}")
    print(f"分辨率：{result['checks']['resolution']['message']}")
    print(f"亮度：{result['checks']['brightness']['message']}")
    print(f"清晰度：{result['checks']['blur']['message']}")
    
    # 清理
    os.remove(test_path)
    print()


def example_5_multimodal_fusion():
    """示例 5: 多模态输入融合"""
    print("=" * 60)
    print("示例 5: 多模态输入融合")
    print("=" * 60)
    
    parser = InputParser()
    
    # 多模态输入
    text = "叶片出现白色粉状霉层"
    structured = {
        "growth_stage": "拔节期",
        "disease_part": "叶片",
        "weather": {
            "temperature": 18,
            "humidity": 80
        }
    }
    
    # 融合多模态数据
    result = parser.parse_multimodal_input(
        text=text,
        structured_data=structured
    )
    
    print(f"输入组件：{result['components']}")
    print(f"融合后的症状：{result['fused']['symptoms']}")
    print(f"融合后的发病部位：{result['fused']['disease_parts']}")
    print(f"生长阶段：{result['fused']['growth_stage']}")
    print(f"环境数据：{result['fused']['environment']}")
    print()


def example_6_complete_workflow():
    """示例 6: 完整工作流程"""
    print("=" * 60)
    print("示例 6: 完整工作流程")
    print("=" * 60)
    
    parser = InputParser()
    validator = InputValidator()
    encoder = EnvironmentEncoder()
    
    # 1. 准备输入数据
    text = "小麦叶片出现褐色病斑，有霉层，情况严重"
    structured = {
        "location": "河南省郑州市",
        "time": "2024 年 3 月 15 日",
        "weather": {
            "temperature": 20,
            "humidity": 85,
            "precipitation": 10
        },
        "growth_stage": "抽穗期",
        "disease_part": "叶片"
    }
    
    # 2. 验证输入
    validation = validator.validate_input(
        text=text,
        structured_data=structured
    )
    
    print(f"输入验证结果：{'有效' if validation['valid'] else '无效'}")
    print(f"总体评分：{validation['overall_score']}")
    
    if not validation['valid']:
        print(f"错误：{validation['errors']}")
        return
    
    # 3. 解析输入
    parsed = parser.parse_multimodal_input(
        text=text,
        structured_data=structured
    )
    
    print(f"解析后的症状：{parsed['fused']['symptoms']}")
    
    # 4. 环境编码和风险评估
    weather = structured['weather']
    growth_stage = structured['growth_stage']
    disease_parts = parsed['fused']['disease_parts']
    
    risk_info = encoder.calculate_environment_risk_score(
        weather, growth_stage, disease_parts
    )
    
    print(f"环境风险等级：{risk_info['risk_level']}")
    print(f"综合风险评分：{risk_info['comprehensive_risk']}")
    
    # 5. 生成建议
    print("\n【诊断建议】")
    if risk_info['comprehensive_risk'] >= 0.7:
        print("⚠️ 高风险环境，建议立即进行病害防治")
        print("⚠️ 推荐使用杀菌剂：戊唑醇、苯醚甲环唑等")
    else:
        print("✓ 风险较低，保持常规监测即可")
    
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("IWDDA Agent Phase 9: 用户输入层增强 - 使用示例")
    print("=" * 60 + "\n")
    
    example_1_text_parsing()
    example_2_weather_encoding()
    example_3_risk_assessment()
    example_4_image_validation()
    example_5_multimodal_fusion()
    example_6_complete_workflow()
    
    print("=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

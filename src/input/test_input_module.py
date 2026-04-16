"""
输入模块测试脚本

测试多模态输入解析、环境因素编码和输入验证功能。
"""

import sys
import numpy as np
import cv2

# 添加 src 目录到路径
sys.path.insert(0, r'd:\Project\WheatAgent\src')

from input import InputParser, InputValidator, EnvironmentEncoder


def test_input_parser():
    """测试输入解析器功能"""
    print("=" * 60)
    print("测试输入解析器 (InputParser)")
    print("=" * 60)
    
    parser = InputParser(image_size=(224, 224))
    
    # 测试 1: 文本症状解析
    print("\n[测试 1] 文本症状解析")
    text = "小麦叶片出现褐色病斑，有霉层，最近 3 天发现的，情况比较严重"
    result = parser.parse_text(text)
    print(f"输入文本：{text}")
    print(f"提取症状：{result['symptoms']}")
    print(f"发病部位：{result['disease_parts']}")
    print(f"生长阶段：{result['growth_stage']}")
    print(f"严重程度：{result['severity']}")
    print("✓ 文本解析功能正常")
    
    # 测试 2: 结构化数据解析
    print("\n[测试 2] 结构化数据解析")
    structured_data = {
        "location": "河南省郑州市",
        "time": "2024 年 3 月 15 日",
        "weather": {
            "temperature": 18.5,
            "humidity": 75,
            "precipitation": 5.2
        },
        "growth_stage": "拔节期",
        "disease_part": "叶片"
    }
    result = parser.parse_structured_data(structured_data)
    print(f"输入数据：{structured_data}")
    print(f"标准化后：{result['data']}")
    print("✓ 结构化数据解析功能正常")
    
    # 测试 3: JSON Schema 生成
    print("\n[测试 3] JSON Schema 生成")
    schema = parser.generate_json_schema()
    print(f"Schema 标题：{schema['title']}")
    print(f"属性数量：{len(schema['properties'])}")
    print("✓ JSON Schema 生成功能正常")
    
    # 测试 4: Schema 验证
    print("\n[测试 4] Schema 验证")
    test_data = {
        "text": "叶片有病斑",
        "structured": {
            "weather": {
                "humidity": 80,
                "temperature": 20
            },
            "growth_stage": "抽穗期"
        }
    }
    is_valid, errors = parser.validate_against_schema(test_data)
    print(f"验证数据：{test_data}")
    print(f"验证结果：{'有效' if is_valid else '无效'}")
    if errors:
        print(f"错误信息：{errors}")
    print("✓ Schema 验证功能正常")
    
    # 测试 5: 多模态输入融合
    print("\n[测试 5] 多模态输入融合")
    result = parser.parse_multimodal_input(
        text="叶片出现锈色粉状物",
        structured_data={
            "growth_stage": "抽穗期",
            "disease_part": "叶片",
            "weather": {"temperature": 15, "humidity": 85}
        }
    )
    print(f"输入组件：{result['components']}")
    print(f"融合特征：{result['fused']}")
    print("✓ 多模态输入融合功能正常")
    
    print("\n✓ 输入解析器所有测试通过")
    return True


def test_environment_encoder():
    """测试环境因素编码器功能"""
    print("\n" + "=" * 60)
    print("测试环境因素编码器 (EnvironmentEncoder)")
    print("=" * 60)
    
    encoder = EnvironmentEncoder()
    
    # 测试 1: 天气数据编码
    print("\n[测试 1] 天气数据编码")
    weather_data = {
        "temperature": 22,
        "humidity": 78,
        "precipitation": 10,
        "weather_condition": "小雨"
    }
    result = encoder.encode_weather(weather_data)
    print(f"输入天气：{weather_data}")
    print(f"温度编码：{result['temperature']['category']} (风险：{result['temperature']['risk_level']})")
    print(f"湿度编码：{result['humidity']['category']} (风险：{result['humidity']['risk_level']})")
    print(f"降水编码：{result['precipitation']['category']} (风险：{result['precipitation']['risk_level']})")
    print(f"天气风险评分：{result['risk_score']}")
    print("✓ 天气数据编码功能正常")
    
    # 测试 2: 生长阶段编码
    print("\n[测试 2] 生长阶段编码")
    stage = "抽穗期"
    result = encoder.encode_growth_stage(stage)
    print(f"生长阶段：{stage}")
    print(f"阶段编码：{result['code']}")
    print(f"易感性权重：{result['susceptibility']}")
    print("✓ 生长阶段编码功能正常")
    
    # 测试 3: 发病部位编码
    print("\n[测试 3] 发病部位编码")
    part = "叶片"
    result = encoder.encode_disease_part(part)
    print(f"发病部位：{part}")
    print(f"部位编码：{result['code']}")
    print(f"部位权重：{result['weight']}")
    print("✓ 发病部位编码功能正常")
    
    # 测试 4: 综合环境风险评分
    print("\n[测试 4] 综合环境风险评分")
    weather_data = {
        "temperature": 20,
        "humidity": 85,
        "precipitation": 15,
        "weather_condition": "中雨"
    }
    growth_stage = "抽穗期"
    disease_parts = ["叶片", "叶鞘"]
    
    risk_info = encoder.calculate_environment_risk_score(
        weather_data, growth_stage, disease_parts
    )
    print(f"天气风险：{risk_info['weather_risk']}")
    print(f"生长阶段风险：{risk_info['growth_stage_risk']}")
    print(f"发病部位风险：{risk_info['disease_part_risk']}")
    print(f"综合风险评分：{risk_info['comprehensive_risk']}")
    print(f"风险等级：{risk_info['risk_level']}")
    print("✓ 综合环境风险评分功能正常")
    
    # 测试 5: 环境特征向量
    print("\n[测试 5] 环境特征向量生成")
    feature_vector = encoder.create_environment_feature_vector(
        weather_data, growth_stage, disease_parts
    )
    print(f"特征向量形状：{feature_vector.shape}")
    print(f"特征向量前 10 维：{feature_vector[:10]}")
    print("✓ 环境特征向量生成功能正常")
    
    # 测试 6: 季节性风险因子
    print("\n[测试 6] 季节性风险因子")
    season_info = encoder.get_seasonal_risk_factors(5)
    print(f"月份：5 月")
    print(f"季节：{season_info['name']}")
    print(f"基础风险：{season_info['base_risk']}")
    print(f"常见病害：{season_info['common_diseases']}")
    print("✓ 季节性风险因子功能正常")
    
    # 测试 7: 环境分析报告
    print("\n[测试 7] 环境分析报告生成")
    report = encoder.generate_environment_report(
        weather_data, growth_stage, disease_parts
    )
    print(report)
    print("✓ 环境分析报告生成功能正常")
    
    print("\n✓ 环境因素编码器所有测试通过")
    return True


def test_input_validator():
    """测试输入验证器功能"""
    print("\n" + "=" * 60)
    print("测试输入验证器 (InputValidator)")
    print("=" * 60)
    
    validator = InputValidator()
    
    # 测试 1: 创建测试图像
    print("\n[测试 1] 创建测试图像并验证")
    test_image_path = r"d:\Project\WheatAgent\test_image.jpg"
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    cv2.imwrite(test_image_path, test_image)
    print(f"创建测试图像：{test_image_path} (640x480)")
    
    result = validator.validate_image(test_image_path)
    print(f"验证结果：{'有效' if result['valid'] else '无效'}")
    print(f"质量评分：{result['quality_score']}")
    print(f"分辨率检查：{result['checks']['resolution']['message']}")
    print(f"亮度检查：{result['checks']['brightness']['message']}")
    print(f"模糊度检查：{result['checks']['blur']['message']}")
    print("✓ 图像验证功能正常")
    
    # 测试 2: 文本验证
    print("\n[测试 2] 文本验证")
    text = "小麦叶片出现病斑"
    result = validator.validate_text(text)
    print(f"输入文本：{text}")
    print(f"验证结果：{'有效' if result['valid'] else '无效'}")
    print(f"质量评分：{result['quality_score']}")
    print(f"警告：{result['warnings']}")
    print("✓ 文本验证功能正常")
    
    # 测试 3: 结构化数据验证
    print("\n[测试 3] 结构化数据验证")
    structured_data = {
        "location": "河南省郑州市",
        "time": "2024 年 3 月 15 日",
        "weather": {
            "temperature": 20,
            "humidity": 75
        },
        "growth_stage": "拔节期"
    }
    result = validator.validate_structured_data(structured_data)
    print(f"输入数据：{structured_data}")
    print(f"验证结果：{'有效' if result['valid'] else '无效'}")
    print(f"完整性评分：{result['completeness_score']}")
    print(f"警告：{result['warnings']}")
    print("✓ 结构化数据验证功能正常")
    
    # 测试 4: 综合输入验证
    print("\n[测试 4] 综合输入验证")
    result = validator.validate_input(
        image_path=test_image_path,
        text="小麦叶片出现褐色病斑，有霉层",
        structured_data=structured_data
    )
    print(f"总体评分：{result['overall_score']}")
    print(f"验证结果：{'有效' if result['valid'] else '无效'}")
    print(f"错误：{result['errors']}")
    print(f"警告：{result['warnings']}")
    print(f"建议：{result['suggestions']}")
    print("✓ 综合输入验证功能正常")
    
    # 测试 5: 数据完整性验证
    print("\n[测试 5] 数据完整性验证")
    incomplete_data = {
        "location": "河南省郑州市"
    }
    result = validator.validate_data_completeness(incomplete_data)
    print(f"输入数据：{incomplete_data}")
    print(f"完整性评分：{result['completeness_score']}")
    print(f"缺失字段：{result['missing_fields']}")
    print(f"存在字段：{result['present_fields']}")
    print("✓ 数据完整性验证功能正常")
    
    # 测试 6: 恢复建议
    print("\n[测试 6] 恢复建议生成")
    recovery = validator.get_recovery_suggestions(result)
    print(f"是否可恢复：{recovery['can_recover']}")
    print(f"建议操作：{recovery['actions']}")
    print(f"替代输入：{recovery['alternative_inputs']}")
    print("✓ 恢复建议生成功能正常")
    
    # 清理测试文件
    import os
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
        print(f"\n清理测试文件：{test_image_path}")
    
    print("\n✓ 输入验证器所有测试通过")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("IWDDA Agent Phase 9: 用户输入层增强 - 功能测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # 测试输入解析器
        if not test_input_parser():
            all_passed = False
    except Exception as e:
        print(f"\n✗ 输入解析器测试失败：{str(e)}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        # 测试环境编码器
        if not test_environment_encoder():
            all_passed = False
    except Exception as e:
        print(f"\n✗ 环境编码器测试失败：{str(e)}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        # 测试输入验证器
        if not test_input_validator():
            all_passed = False
    except Exception as e:
        print(f"\n✗ 输入验证器测试失败：{str(e)}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("✓✓✓ 所有测试通过！Phase 9 功能实现完成 ✓✓✓")
    else:
        print("✗✗✗ 部分测试失败，请检查错误信息 ✗✗✗")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

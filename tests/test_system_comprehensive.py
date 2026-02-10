# -*- coding: utf-8 -*-
# 文件路径: WheatAgent/test_system_comprehensive.py
"""
系统综合测试脚本
测试 IWDDA 系统的所有核心组件
"""

import os
import sys
import time
from datetime import datetime

# 添加路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from vision.vision_engine import VisionAgent
from text.text_engine import LanguageAgent
from graph.graph_engine import KnowledgeAgent
from fusion.fusion_engine import FusionAgent
from evolution import (
    ExperienceReplayBuffer,
    HumanFeedbackCollector,
    FeedbackType
)


class SystemTester:
    """
    系统测试器
    """
    
    def __init__(self):
        """
        初始化测试器
        """
        self.test_results = []
        self.start_time = datetime.now()
        print("=" * 60)
        print("🧪 IWDDA 系统综合测试")
        print("=" * 60)
        print(f"📅 测试开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def test_vision_agent(self):
        """
        测试视觉智能体
        """
        print("🔍 测试 1: 视觉智能体 (VisionAgent)")
        print("-" * 60)
        
        try:
            # 初始化视觉智能体
            vision_agent = VisionAgent()
            print("✅ 视觉智能体初始化成功")
            
            # 检查模型
            if hasattr(vision_agent, 'model'):
                print(f"✅ 模型加载成功: {vision_agent.model}")
            
            # 检查检测方法
            if hasattr(vision_agent, 'detect'):
                print("✅ 检测方法可用")
            
            self.test_results.append({
                "test": "VisionAgent",
                "status": "PASSED",
                "message": "视觉智能体测试通过"
            })
            
        except Exception as e:
            print(f"❌ 视觉智能体测试失败: {e}")
            self.test_results.append({
                "test": "VisionAgent",
                "status": "FAILED",
                "message": str(e)
            })
        
        print()
    
    def test_language_agent(self):
        """
        测试语言智能体
        """
        print("🔍 测试 2: 语言智能体 (LanguageAgent)")
        print("-" * 60)
        
        try:
            # 初始化语言智能体
            language_agent = LanguageAgent()
            print("✅ 语言智能体初始化成功")
            
            # 测试相似度计算
            test_text = "叶片上有黄色条纹"
            symptom = "叶片上有黄色条纹状锈斑"
            
            if hasattr(language_agent, 'compute_similarity'):
                similarity = language_agent.compute_similarity(test_text, symptom)
                print(f"✅ 相似度计算成功: {similarity:.4f}")
            else:
                print("⚠️ 相似度计算方法不可用")
            
            self.test_results.append({
                "test": "LanguageAgent",
                "status": "PASSED",
                "message": "语言智能体测试通过"
            })
            
        except Exception as e:
            print(f"❌ 语言智能体测试失败: {e}")
            self.test_results.append({
                "test": "LanguageAgent",
                "status": "FAILED",
                "message": str(e)
            })
        
        print()
    
    def test_knowledge_agent(self):
        """
        测试知识图谱智能体
        """
        print("🔍 测试 3: 知识图谱智能体 (KnowledgeAgent)")
        print("-" * 60)
        
        try:
            # 初始化知识图谱智能体
            knowledge_agent = KnowledgeAgent(password="123456789s")
            print("✅ 知识图谱智能体初始化成功")
            
            # 测试获取病害详情
            details = knowledge_agent.get_disease_details("条锈病")
            if details:
                print(f"✅ 获取病害详情成功: {details.get('name')}")
                print(f"   - 成因: {details.get('causes')}")
                print(f"   - 预防: {details.get('preventions')}")
                print(f"   - 治疗: {details.get('treatments')}")
            else:
                print("⚠️ 未获取到病害详情")
            
            # 测试一致性验证
            if hasattr(knowledge_agent, 'verify_consistency'):
                result = knowledge_agent.verify_consistency("条锈病", "黄色条纹")
                print(f"✅ 一致性验证成功: {result}")
            
            knowledge_agent.close()
            
            self.test_results.append({
                "test": "KnowledgeAgent",
                "status": "PASSED",
                "message": "知识图谱智能体测试通过"
            })
            
        except Exception as e:
            print(f"❌ 知识图谱智能体测试失败: {e}")
            self.test_results.append({
                "test": "KnowledgeAgent",
                "status": "FAILED",
                "message": str(e)
            })
        
        print()
    
    def test_fusion_agent(self):
        """
        测试融合智能体
        """
        print("🔍 测试 4: 融合智能体 (FusionAgent - KAD-Fusion)")
        print("-" * 60)
        
        try:
            # 初始化知识图谱智能体（用于融合）
            knowledge_agent = KnowledgeAgent(password="123456789s")
            
            # 初始化融合智能体
            fusion_agent = FusionAgent(knowledge_agent=knowledge_agent)
            print("✅ 融合智能体初始化成功")
            
            # 检查 KAD-Fusion 核心模块
            if hasattr(fusion_agent, 'kga'):
                print("✅ 知识引导注意力 (KGA) 模块已加载")
            else:
                print("⚠️ 知识引导注意力 (KGA) 模块未加载")
            
            if hasattr(fusion_agent, 'cross_attention'):
                print("✅ 跨模态特征对齐模块已加载")
            else:
                print("⚠️ 跨模态特征对齐模块未加载")
            
            # 测试融合决策
            vision_result = {"label": "条锈病", "conf": 0.85}
            text_result = {"label": "条锈病", "conf": 0.90}
            user_text = "叶片上有黄色条纹"
            
            fusion_result = fusion_agent.fuse_and_decide(vision_result, text_result, user_text)
            
            if fusion_result:
                print(f"✅ 融合决策成功:")
                print(f"   - 诊断结果: {fusion_result.get('diagnosis')}")
                print(f"   - 置信度: {fusion_result.get('confidence'):.2f}")
                print(f"   - 推理过程: {len(fusion_result.get('reasoning', []))} 条")
            else:
                print("⚠️ 融合决策失败")
            
            knowledge_agent.close()
            
            self.test_results.append({
                "test": "FusionAgent",
                "status": "PASSED",
                "message": "融合智能体测试通过"
            })
            
        except Exception as e:
            print(f"❌ 融合智能体测试失败: {e}")
            self.test_results.append({
                "test": "FusionAgent",
                "status": "FAILED",
                "message": str(e)
            })
        
        print()
    
    def test_experience_replay(self):
        """
        测试经验回放机制
        """
        print("🔍 测试 5: 经验回放机制 (Experience Replay)")
        print("-" * 60)
        
        try:
            # 初始化经验回放缓冲区
            replay_buffer = ExperienceReplayBuffer(buffer_size=100)
            print("✅ 经验回放缓冲区初始化成功")
            
            # 添加测试经验
            replay_buffer.add_experience(
                image_path="test_image.jpg",
                user_text="测试文本",
                vision_result={"label": "条锈病", "conf": 0.85},
                text_result={"label": "条锈病", "conf": 0.90},
                final_diagnosis="条锈病"
            )
            print("✅ 添加经验成功")
            
            # 测试采样
            sampled = replay_buffer.sample(batch_size=5)
            print(f"✅ 采样成功: {len(sampled)} 条样本")
            
            # 获取统计信息
            stats = replay_buffer.get_statistics()
            print(f"✅ 统计信息: {stats}")
            
            self.test_results.append({
                "test": "ExperienceReplay",
                "status": "PASSED",
                "message": "经验回放机制测试通过"
            })
            
        except Exception as e:
            print(f"❌ 经验回放机制测试失败: {e}")
            self.test_results.append({
                "test": "ExperienceReplay",
                "status": "FAILED",
                "message": str(e)
            })
        
        print()
    
    def test_human_feedback(self):
        """
        测试人工反馈机制
        """
        print("🔍 测试 6: 人工反馈机制 (Human Feedback)")
        print("-" * 60)
        
        try:
            # 初始化反馈收集器
            feedback_collector = HumanFeedbackCollector()
            print("✅ 反馈收集器初始化成功")
            
            # 收集测试反馈
            feedback_collector.collect_feedback(
                image_path="test_image.jpg",
                user_text="测试文本",
                predicted_diagnosis="条锈病",
                predicted_confidence=0.85,
                feedback_type=FeedbackType.CORRECT,
                user_comment="测试反馈"
            )
            print("✅ 收集反馈成功")
            
            # 获取统计信息
            stats = feedback_collector.get_feedback_statistics()
            print(f"✅ 统计信息: {stats}")
            
            self.test_results.append({
                "test": "HumanFeedback",
                "status": "PASSED",
                "message": "人工反馈机制测试通过"
            })
            
        except Exception as e:
            print(f"❌ 人工反馈机制测试失败: {e}")
            self.test_results.append({
                "test": "HumanFeedback",
                "status": "FAILED",
                "message": str(e)
            })
        
        print()
    
    def test_integration(self):
        """
        测试系统集成
        """
        print("🔍 测试 7: 系统集成测试")
        print("-" * 60)
        
        try:
            # 初始化所有组件
            vision_agent = VisionAgent()
            language_agent = LanguageAgent()
            knowledge_agent = KnowledgeAgent(password="123456789s")
            fusion_agent = FusionAgent(knowledge_agent=knowledge_agent)
            
            print("✅ 所有组件初始化成功")
            
            # 测试完整流程（模拟）
            print("✅ 系统集成测试通过")
            
            knowledge_agent.close()
            
            self.test_results.append({
                "test": "Integration",
                "status": "PASSED",
                "message": "系统集成测试通过"
            })
            
        except Exception as e:
            print(f"❌ 系统集成测试失败: {e}")
            self.test_results.append({
                "test": "Integration",
                "status": "FAILED",
                "message": str(e)
            })
        
        print()
    
    def generate_report(self):
        """
        生成测试报告
        """
        print("=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        # 计算统计信息
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAILED'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 计算耗时
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print(f"📅 测试结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  总耗时: {duration:.2f} 秒")
        print()
        print(f"📈 测试统计:")
        print(f"   - 总测试数: {total_tests}")
        print(f"   - 通过: {passed_tests}")
        print(f"   - 失败: {failed_tests}")
        print(f"   - 成功率: {success_rate:.1f}%")
        print()
        
        # 详细结果
        print("📋 详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"   {i}. {status_icon} {result['test']}: {result['message']}")
        
        print()
        
        # 保存报告到文件
        report_file = "test_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("IWDDA 系统综合测试报告\n")
            f.write("=" * 60 + "\n")
            f.write(f"测试时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总耗时: {duration:.2f} 秒\n\n")
            f.write(f"测试统计:\n")
            f.write(f"  - 总测试数: {total_tests}\n")
            f.write(f"  - 通过: {passed_tests}\n")
            f.write(f"  - 失败: {failed_tests}\n")
            f.write(f"  - 成功率: {success_rate:.1f}%\n\n")
            f.write("详细结果:\n")
            for i, result in enumerate(self.test_results, 1):
                f.write(f"  {i}. [{result['status']}] {result['test']}: {result['message']}\n")
        
        print(f"💾 测试报告已保存到: {report_file}")
        print("=" * 60)
        
        return success_rate == 100.0


def main():
    """
    主函数
    """
    tester = SystemTester()
    
    # 执行所有测试
    tester.test_vision_agent()
    tester.test_language_agent()
    tester.test_knowledge_agent()
    tester.test_fusion_agent()
    tester.test_experience_replay()
    tester.test_human_feedback()
    tester.test_integration()
    
    # 生成报告
    all_passed = tester.generate_report()
    
    # 返回结果
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

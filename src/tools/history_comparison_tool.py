# -*- coding: utf-8 -*-
"""
历史对比工具 - History Comparison Tool
对比前后病情变化，评估防治效果
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .base_tool import BaseTool


class HistoryComparisonTool(BaseTool):
    """
    历史对比工具类
    
    功能：
    1. 加载历史病例数据
    2. 对比前后两次诊断结果
    3. 分析病情变化趋势
    4. 评估防治效果
    5. 生成对比报告
    
    输入参数:
        current_case: 当前病例（必需）
        previous_case_id: 历史病例 ID（可选）
        previous_case: 历史病例数据（可选）
        comparison_type: 对比类型（可选，默认"all"）
    
    输出结果:
        comparison_result: 对比结果
        disease_progression: 病情发展趋势
        treatment_effectiveness: 防治效果评估
        change_analysis: 变化分析
        recommendations: 后续建议
    """
    
    def __init__(self, case_database_path: str = None):
        """
        初始化历史对比工具
        
        :param case_database_path: 病例数据库路径（可选）
        """
        super().__init__(
            name="HistoryComparisonTool",
            description="历史对比工具，对比前后病情变化，评估防治效果"
        )
        
        # 设置默认病例数据库路径
        if case_database_path is None:
            base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
            self.case_database_path = os.path.join(base_dir, 'case_records')
        else:
            self.case_database_path = case_database_path
        
        self._case_database: List[Dict[str, Any]] = []
    
    def get_name(self) -> str:
        """
        获取工具名称
        
        :return: 工具名称
        """
        return "HistoryComparisonTool"
    
    def get_description(self) -> str:
        """
        获取工具描述
        
        :return: 工具描述
        """
        return "历史对比工具，对比前后病情变化，评估防治效果"
    
    def initialize(self) -> bool:
        """
        初始化工具，加载病例数据库
        
        :return: 初始化是否成功
        """
        try:
            self._load_case_database()
            print(f"[HistoryComparisonTool] 初始化完成，已加载 {len(self._case_database)} 个病例")
            return True
        except Exception as e:
            print(f"[HistoryComparisonTool] 初始化失败：{e}")
            return False
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证输入参数
        
        :param kwargs: 输入参数
        :return: 参数是否有效
        """
        current_case = kwargs.get('current_case')
        if not current_case:
            print("[HistoryComparisonTool] 参数验证失败：缺少 current_case")
            return False
        
        return True
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行历史对比
        
        :param kwargs: 执行参数
            - current_case: 当前病例
            - previous_case_id: 历史病例 ID
            - previous_case: 历史病例数据
            - comparison_type: 对比类型
        :return: 对比结果字典
        """
        current_case = kwargs.get('current_case')
        previous_case_id = kwargs.get('previous_case_id')
        previous_case = kwargs.get('previous_case')
        comparison_type = kwargs.get('comparison_type', 'all')
        
        print(f"[HistoryComparisonTool] 执行历史对比")
        
        try:
            # 获取历史病例
            if previous_case is None and previous_case_id:
                previous_case = self._get_case_by_id(previous_case_id)
            
            if previous_case is None:
                return {
                    "success": False,
                    "data": None,
                    "message": "未找到历史病例进行对比",
                    "error": "previous_case not found",
                    "tool_name": self.get_name()
                }
            
            # 执行对比分析
            comparison_result = self._compare_cases(
                current_case,
                previous_case,
                comparison_type
            )
            
            result = {
                "success": True,
                "data": comparison_result,
                "message": "历史对比完成",
                "tool_name": self.get_name()
            }
            
            print(f"[HistoryComparisonTool] 对比完成")
            
            return result
        
        except Exception as e:
            error_msg = f"历史对比异常：{str(e)}"
            print(f"[HistoryComparisonTool] {error_msg}")
            return {
                "success": False,
                "data": None,
                "message": error_msg,
                "error": error_msg,
                "tool_name": self.get_name()
            }
    
    def _load_case_database(self) -> None:
        """
        加载病例数据库
        """
        try:
            if not os.path.exists(self.case_database_path):
                print(f"[HistoryComparisonTool] 病例目录不存在：{self.case_database_path}")
                return
            
            # 遍历所有子目录
            for date_dir in os.listdir(self.case_database_path):
                date_path = os.path.join(self.case_database_path, date_dir)
                if not os.path.isdir(date_path):
                    continue
                
                # 读取 JSON 文件
                for filename in os.listdir(date_path):
                    if filename.endswith('.json'):
                        file_path = os.path.join(date_path, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                case = json.load(f)
                                self._case_database.append(case)
                        except Exception as e:
                            print(f"[HistoryComparisonTool] 加载病例失败 {filename}: {e}")
        
        except Exception as e:
            print(f"[HistoryComparisonTool] 加载病例异常：{e}")
    
    def _get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        根据病例 ID 获取病例
        
        :param case_id: 病例 ID
        :return: 病例记录或 None
        """
        for case in self._case_database:
            if case.get('case_id') == case_id:
                return case
        return None
    
    def _compare_cases(
        self,
        current_case: Dict[str, Any],
        previous_case: Dict[str, Any],
        comparison_type: str
    ) -> Dict[str, Any]:
        """
        对比两个病例
        
        :param current_case: 当前病例
        :param previous_case: 历史病例
        :param comparison_type: 对比类型
        :return: 对比结果
        """
        # 提取关键信息
        current_diagnosis = current_case.get('diagnosis_info', {})
        previous_diagnosis = previous_case.get('diagnosis_info', {})
        
        current_severity = current_case.get('severity_info', {})
        previous_severity = previous_case.get('severity_info', {})
        
        # 对比分析
        comparison_result = {
            "comparison_time": datetime.now().isoformat(),
            "current_case_id": current_case.get('case_id', 'current'),
            "previous_case_id": previous_case.get('case_id', 'previous'),
            "time_interval": self._calculate_time_interval(
                current_case.get('record_time'),
                previous_case.get('record_time')
            ),
            "disease_comparison": self._compare_disease_info(
                current_diagnosis,
                previous_diagnosis
            ),
            "severity_comparison": self._compare_severity(
                current_severity,
                previous_severity
            ),
            "progression_analysis": self._analyze_progression(
                current_severity,
                previous_severity
            ),
            "treatment_effectiveness": self._evaluate_treatment(
                current_case,
                previous_case
            ),
            "recommendations": self._generate_recommendations(
                current_case,
                previous_case
            )
        }
        
        return comparison_result
    
    def _calculate_time_interval(
        self,
        current_time: str,
        previous_time: str
    ) -> Dict[str, Any]:
        """
        计算时间间隔
        
        :param current_time: 当前时间
        :param previous_time: 历史时间
        :return: 时间间隔信息
        """
        try:
            current_dt = datetime.fromisoformat(current_time)
            previous_dt = datetime.fromisoformat(previous_time)
            
            delta = current_dt - previous_dt
            days = delta.days
            
            return {
                "days": days,
                "description": f"间隔 {days} 天",
                "current_time": current_time,
                "previous_time": previous_time
            }
        except Exception:
            return {
                "days": 0,
                "description": "时间间隔未知",
                "current_time": current_time or "",
                "previous_time": previous_time or ""
            }
    
    def _compare_disease_info(
        self,
        current_diagnosis: Dict[str, Any],
        previous_diagnosis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        对比病害信息
        
        :param current_diagnosis: 当前诊断信息
        :param previous_diagnosis: 历史诊断信息
        :return: 对比结果
        """
        current_disease = current_diagnosis.get('disease_name', '未知')
        previous_disease = previous_diagnosis.get('disease_name', '未知')
        
        current_confidence = current_diagnosis.get('confidence', 0.0)
        previous_confidence = previous_diagnosis.get('confidence', 0.0)
        
        confidence_change = current_confidence - previous_confidence
        
        return {
            "current_disease": current_disease,
            "previous_disease": previous_disease,
            "disease_changed": current_disease != previous_disease,
            "current_confidence": current_confidence,
            "previous_confidence": previous_confidence,
            "confidence_change": confidence_change,
            "confidence_trend": "上升" if confidence_change > 0 else ("下降" if confidence_change < 0 else "持平")
        }
    
    def _compare_severity(
        self,
        current_severity: Dict[str, Any],
        previous_severity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        对比严重度
        
        :param current_severity: 当前严重度
        :param previous_severity: 历史严重度
        :return: 对比结果
        """
        current_level = current_severity.get('severity_level', '未知')
        previous_level = previous_severity.get('severity_level', '未知')
        
        current_score = current_severity.get('severity_score', 0.0)
        previous_score = previous_severity.get('severity_score', 0.0)
        
        score_change = current_score - previous_score
        
        # 等级变化
        level_order = {"轻度": 0, "中度": 1, "重度": 2}
        level_change = level_order.get(current_level, 1) - level_order.get(previous_level, 1)
        
        if level_change < 0:
            level_trend = "减轻"
        elif level_change > 0:
            level_trend = "加重"
        else:
            level_trend = "持平"
        
        return {
            "current_level": current_level,
            "previous_level": previous_level,
            "level_trend": level_trend,
            "current_score": current_score,
            "previous_score": previous_score,
            "score_change": score_change,
            "change_percentage": f"{(score_change / previous_score * 100) if previous_score > 0 else 0:.1f}%"
        }
    
    def _analyze_progression(
        self,
        current_severity: Dict[str, Any],
        previous_severity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析病情发展趋势
        
        :param current_severity: 当前严重度
        :param previous_severity: 历史严重度
        :return: 发展趋势分析
        """
        score_change = (
            current_severity.get('severity_score', 0.0) -
            previous_severity.get('severity_score', 0.0)
        )
        
        if score_change < -0.2:
            progression = "显著好转"
            description = "病情明显好转，防治效果显著"
        elif score_change < 0:
            progression = "有所好转"
            description = "病情有所好转，继续当前防治措施"
        elif score_change < 0.2:
            progression = "基本稳定"
            description = "病情基本稳定，略有波动"
        elif score_change < 0.4:
            progression = "有所加重"
            description = "病情有所加重，需加强防治"
        else:
            progression = "显著加重"
            description = "病情显著加重，需立即调整防治方案"
        
        return {
            "progression": progression,
            "description": description,
            "severity_change": score_change,
            "trend": "好转" if score_change < 0 else ("加重" if score_change > 0 else "稳定")
        }
    
    def _evaluate_treatment(
        self,
        current_case: Dict[str, Any],
        previous_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估防治效果
        
        :param current_case: 当前病例
        :param previous_case: 历史病例
        :return: 防治效果评估
        """
        severity_change = (
            current_case.get('severity_info', {}).get('severity_score', 0.0) -
            previous_case.get('severity_info', {}).get('severity_score', 0.0)
        )
        
        if severity_change < -0.3:
            effectiveness = "非常有效"
            effectiveness_score = 90
        elif severity_change < -0.1:
            effectiveness = "有效"
            effectiveness_score = 75
        elif severity_change < 0.1:
            effectiveness = "基本有效"
            effectiveness_score = 60
        elif severity_change < 0.3:
            effectiveness = "效果一般"
            effectiveness_score = 45
        else:
            effectiveness = "效果较差"
            effectiveness_score = 30
        
        return {
            "effectiveness": effectiveness,
            "effectiveness_score": effectiveness_score,
            "severity_improvement": severity_change < 0,
            "recommendation": self._get_treatment_recommendation(effectiveness)
        }
    
    def _get_treatment_recommendation(self, effectiveness: str) -> str:
        """
        获取防治建议
        
        :param effectiveness: 防治效果
        :return: 防治建议
        """
        recommendations = {
            "非常有效": "继续保持当前防治方案，定期监测",
            "有效": "继续当前防治方案，可适当减少用药频率",
            "基本有效": "维持当前防治方案，加强监测",
            "效果一般": "考虑调整防治方案，增加防治措施",
            "效果较差": "建议立即调整防治方案，咨询专家意见"
        }
        return recommendations.get(effectiveness, "继续监测")
    
    def _generate_recommendations(
        self,
        current_case: Dict[str, Any],
        previous_case: Dict[str, Any]
    ) -> List[str]:
        """
        生成后续建议
        
        :param current_case: 当前病例
        :param previous_case: 历史病例
        :return: 建议列表
        """
        recommendations = []
        
        # 基于病情发展趋势的建议
        progression = self._analyze_progression(
            current_case.get('severity_info', {}),
            previous_case.get('severity_info', {})
        )
        
        if progression['trend'] == "好转":
            recommendations.append("病情好转，建议继续当前防治措施")
            recommendations.append("可适当减少用药频率，降低防治成本")
        elif progression['trend'] == "加重":
            recommendations.append("病情加重，建议加强防治力度")
            recommendations.append("考虑更换或轮换使用不同作用机理的药剂")
            recommendations.append("增加田间巡查频率，密切监测病情发展")
        else:
            recommendations.append("病情稳定，继续保持监测")
            recommendations.append("按计划进行常规防治")
        
        # 通用建议
        recommendations.append("记录防治措施和效果，为后续防治提供参考")
        recommendations.append("注意天气变化，选择适宜时机施药")
        
        return recommendations
    
    def generate_comparison_report(
        self,
        comparison_result: Dict[str, Any]
    ) -> str:
        """
        生成对比报告文本
        
        :param comparison_result: 对比结果
        :return: 报告文本
        """
        report_lines = [
            "=" * 60,
            "历史病情对比报告",
            "=" * 60,
            "",
            f"对比时间：{comparison_result.get('comparison_time', '未知')}",
            f"时间间隔：{comparison_result.get('time_interval', {}).get('description', '未知')}",
            "",
            "病害对比:",
            f"  当前：{comparison_result.get('disease_comparison', {}).get('current_disease', '未知')}",
            f"  历史：{comparison_result.get('disease_comparison', {}).get('previous_disease', '未知')}",
            "",
            "严重度对比:",
            f"  当前：{comparison_result.get('severity_comparison', {}).get('current_level', '未知')} "
            f"({comparison_result.get('severity_comparison', {}).get('current_score', 0):.2f})",
            f"  历史：{comparison_result.get('severity_comparison', {}).get('previous_level', '未知')} "
            f"({comparison_result.get('severity_comparison', {}).get('previous_score', 0):.2f})",
            f"  趋势：{comparison_result.get('severity_comparison', {}).get('level_trend', '未知')}",
            "",
            "病情发展:",
            f"  {comparison_result.get('progression_analysis', {}).get('description', '未知')}",
            "",
            "防治效果:",
            f"  {comparison_result.get('treatment_effectiveness', {}).get('effectiveness', '未知')} "
            f"(评分：{comparison_result.get('treatment_effectiveness', {}).get('effectiveness_score', 0)})",
            "",
            "后续建议:",
        ]
        
        for rec in comparison_result.get('recommendations', []):
            report_lines.append(f"  - {rec}")
        
        report_lines.extend([
            "",
            "=" * 60
        ])
        
        return "\n".join(report_lines)


def test_history_comparison_tool():
    """测试历史对比工具"""
    print("=" * 60)
    print("🧪 测试 HistoryComparisonTool")
    print("=" * 60)
    
    tool = HistoryComparisonTool()
    
    print("\n1️⃣ 初始化工具")
    init_success = tool.initialize()
    print(f"   初始化结果：{'成功' if init_success else '失败'}")
    
    print("\n2️⃣ 获取工具信息")
    print(f"   工具名称：{tool.get_name()}")
    print(f"   工具描述：{tool.get_description()}")
    
    print("\n3️⃣ 模拟历史对比")
    # 模拟历史病例
    previous_case = {
        "case_id": "CASE_20260302_0001",
        "record_time": "2026-03-02T10:00:00",
        "diagnosis_info": {
            "disease_name": "条锈病",
            "confidence": 0.88,
            "main_features": ["黄色条状孢子堆"]
        },
        "severity_info": {
            "severity_level": "中度",
            "severity_score": 0.55,
            "impact_assessment": "病斑中等"
        }
    }
    
    # 模拟当前病例
    current_case = {
        "case_id": "CASE_20260309_0002",
        "record_time": "2026-03-09T10:00:00",
        "diagnosis_info": {
            "disease_name": "条锈病",
            "confidence": 0.92,
            "main_features": ["黄色条状孢子堆减少"]
        },
        "severity_info": {
            "severity_level": "轻度",
            "severity_score": 0.25,
            "impact_assessment": "病斑减少"
        }
    }
    
    result = tool.execute(
        current_case=current_case,
        previous_case=previous_case
    )
    
    print(f"\n4️⃣ 对比结果:")
    print(f"   成功：{result.get('success')}")
    if result.get('data'):
        data = result['data']
        print(f"   时间间隔：{data.get('time_interval', {}).get('description', '未知')}")
        print(f"   病情趋势：{data.get('severity_comparison', {}).get('level_trend', '未知')}")
        print(f"   发展趋势：{data.get('progression_analysis', {}).get('description', '未知')}")
        print(f"   防治效果：{data.get('treatment_effectiveness', {}).get('effectiveness', '未知')}")
        
        # 生成报告
        report = tool.generate_comparison_report(data)
        print(f"\n5️⃣ 对比报告:")
        print(report)
    
    print("\n" + "=" * 60)
    print("✅ HistoryComparisonTool 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_history_comparison_tool()

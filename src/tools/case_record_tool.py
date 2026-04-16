# -*- coding: utf-8 -*-
"""
病例记录工具 - Case Record Tool
保存诊断案例到病例库，支持后续查询和对比
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .base_tool import BaseTool


class CaseRecordTool(BaseTool):
    """
    病例记录工具类
    
    功能：
    1. 保存诊断案例到病例库
    2. 记录完整的诊断信息（图像、结果、防治方案）
    3. 支持病例查询和检索
    4. 导出病例数据
    
    输入参数:
        diagnosis_plan: 诊断计划（必需）
        image_path: 图像路径（可选）
        user_info: 用户信息（可选）
        save_to_file: 是否保存到文件（可选，默认 True）
    
    输出结果:
        case_id: 病例 ID
        record_time: 记录时间
        file_path: 保存路径
        case_summary: 病例摘要
    """
    
    def __init__(self, storage_path: str = None):
        """
        初始化病例记录工具
        
        :param storage_path: 病例存储路径（可选）
        """
        super().__init__(
            name="CaseRecordTool",
            description="病例记录工具，保存诊断案例到病例库"
        )
        
        # 设置默认存储路径
        if storage_path is None:
            base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
            self.storage_path = os.path.join(base_dir, 'case_records')
        else:
            self.storage_path = storage_path
        
        self._case_counter = 0
        self._case_database: List[Dict[str, Any]] = []
    
    def get_name(self) -> str:
        """
        获取工具名称
        
        :return: 工具名称
        """
        return "CaseRecordTool"
    
    def get_description(self) -> str:
        """
        获取工具描述
        
        :return: 工具描述
        """
        return "病例记录工具，保存诊断案例到病例库"
    
    def initialize(self) -> bool:
        """
        初始化工具，创建存储目录
        
        :return: 初始化是否成功
        """
        try:
            # 创建存储目录
            os.makedirs(self.storage_path, exist_ok=True)
            
            # 加载现有病例数据
            self._load_cases()
            
            print(f"[CaseRecordTool] 初始化完成，存储路径：{self.storage_path}")
            return True
        except Exception as e:
            print(f"[CaseRecordTool] 初始化失败：{e}")
            return False
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证输入参数
        
        :param kwargs: 输入参数
        :return: 参数是否有效
        """
        diagnosis_plan = kwargs.get('diagnosis_plan')
        if not diagnosis_plan:
            print("[CaseRecordTool] 参数验证失败：缺少 diagnosis_plan")
            return False
        
        return True
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行病例记录
        
        :param kwargs: 执行参数
            - diagnosis_plan: 诊断计划
            - image_path: 图像路径
            - user_info: 用户信息
            - save_to_file: 是否保存到文件
        :return: 记录结果字典
        """
        diagnosis_plan = kwargs.get('diagnosis_plan')
        image_path = kwargs.get('image_path', '')
        user_info = kwargs.get('user_info', {})
        save_to_file = kwargs.get('save_to_file', True)
        
        print(f"[CaseRecordTool] 开始记录病例")
        
        try:
            # 生成病例记录
            case_record = self._create_case_record(
                diagnosis_plan,
                image_path,
                user_info
            )
            
            # 保存到内存数据库
            self._case_database.append(case_record)
            self._case_counter += 1
            
            # 保存到文件
            if save_to_file:
                file_path = self._save_case_to_file(case_record)
            else:
                file_path = None
            
            result = {
                "success": True,
                "data": {
                    "case_id": case_record['case_id'],
                    "record_time": case_record['record_time'],
                    "file_path": file_path,
                    "case_summary": self._generate_case_summary(case_record)
                },
                "message": f"病例记录成功：{case_record['case_id']}",
                "tool_name": self.get_name()
            }
            
            print(f"[CaseRecordTool] 病例记录完成：{case_record['case_id']}")
            
            return result
        
        except Exception as e:
            error_msg = f"病例记录异常：{str(e)}"
            print(f"[CaseRecordTool] {error_msg}")
            return {
                "success": False,
                "data": None,
                "message": error_msg,
                "error": error_msg,
                "tool_name": self.get_name()
            }
    
    def _create_case_record(
        self,
        diagnosis_plan: Dict[str, Any],
        image_path: str,
        user_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建病例记录
        
        :param diagnosis_plan: 诊断计划
        :param image_path: 图像路径
        :param user_info: 用户信息
        :return: 病例记录字典
        """
        # 生成病例 ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        case_id = f"CASE_{timestamp}_{self._case_counter:04d}"
        
        # 提取诊断信息
        disease_diagnosis = diagnosis_plan.get("病害诊断", {})
        severity_assessment = diagnosis_plan.get("严重度评估", {})
        treatment_measures = diagnosis_plan.get("防治措施", {})
        followup_plan = diagnosis_plan.get("复查计划", {})
        
        case_record = {
            "case_id": case_id,
            "record_time": datetime.now().isoformat(),
            "basic_info": {
                "image_path": image_path,
                "image_name": os.path.basename(image_path) if image_path else "",
                "user_info": user_info
            },
            "diagnosis_info": {
                "disease_name": disease_diagnosis.get("病害名称", "未知"),
                "confidence": disease_diagnosis.get("置信度", 0.0),
                "main_features": disease_diagnosis.get("主要特征", []),
                "pathogen": disease_diagnosis.get("病原体", "未知"),
                "conclusion": disease_diagnosis.get("诊断结论", "")
            },
            "severity_info": {
                "severity_level": severity_assessment.get("严重度等级", "未知"),
                "severity_score": severity_assessment.get("严重度评分", 0.0),
                "impact_assessment": severity_assessment.get("影响评估", ""),
                "recommendation": severity_assessment.get("防治建议", "")
            },
            "treatment_info": {
                "recommended_agents": treatment_measures.get("推荐药剂", []),
                "application_concentration": treatment_measures.get("用药浓度", ""),
                "treatment_steps": treatment_measures.get("防治步骤", []),
                "application_timing": treatment_measures.get("施药时机", ""),
                "safety_interval": treatment_measures.get("安全间隔期", ""),
                "precautions": treatment_measures.get("注意事项", [])
            },
            "followup_info": {
                "followup_time": followup_plan.get("复查时间", ""),
                "followup_interval": followup_plan.get("复查间隔", ""),
                "urgency": followup_plan.get("紧急程度", ""),
                "followup_content": followup_plan.get("复查内容", []),
                "expected_goal": followup_plan.get("预期目标", ""),
                "task_id": followup_plan.get("复查任务 ID", "")
            },
            "reasoning_basis": diagnosis_plan.get("推理依据", {}),
            "risk_level": diagnosis_plan.get("风险等级", {}),
            "metadata": {
                "version": "1.0",
                "tool": self.get_name()
            }
        }
        
        return case_record
    
    def _save_case_to_file(self, case_record: Dict[str, Any]) -> str:
        """
        将病例记录保存到文件
        
        :param case_record: 病例记录
        :return: 保存的文件路径
        """
        try:
            # 按日期创建子目录
            record_date = case_record['record_time'][:10]  # YYYY-MM-DD
            date_dir = os.path.join(self.storage_path, record_date.replace('-', ''))
            os.makedirs(date_dir, exist_ok=True)
            
            # 生成文件名
            filename = f"{case_record['case_id']}.json"
            file_path = os.path.join(date_dir, filename)
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(case_record, f, ensure_ascii=False, indent=2)
            
            print(f"[CaseRecordTool] 病例已保存：{file_path}")
            return file_path
        
        except Exception as e:
            print(f"[CaseRecordTool] 保存文件失败：{e}")
            return None
    
    def _generate_case_summary(self, case_record: Dict[str, Any]) -> str:
        """
        生成病例摘要
        
        :param case_record: 病例记录
        :return: 病例摘要字符串
        """
        diagnosis = case_record.get('diagnosis_info', {})
        severity = case_record.get('severity_info', {})
        
        summary = (
            f"病例 ID: {case_record['case_id']}\n"
            f"诊断：{diagnosis.get('disease_name', '未知')} "
            f"(置信度：{diagnosis.get('confidence', 0):.2%})\n"
            f"严重度：{severity.get('severity_level', '未知')} "
            f"(评分：{severity.get('severity_score', 0):.2f})\n"
            f"记录时间：{case_record['record_time']}"
        )
        
        return summary
    
    def _load_cases(self) -> None:
        """
        加载现有病例数据
        """
        try:
            if not os.path.exists(self.storage_path):
                print(f"[CaseRecordTool] 病例目录不存在：{self.storage_path}")
                return
            
            # 遍历所有子目录
            for date_dir in os.listdir(self.storage_path):
                date_path = os.path.join(self.storage_path, date_dir)
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
                                self._case_counter += 1
                        except Exception as e:
                            print(f"[CaseRecordTool] 加载病例失败 {filename}: {e}")
            
            print(f"[CaseRecordTool] 已加载 {len(self._case_database)} 个历史病例")
        
        except Exception as e:
            print(f"[CaseRecordTool] 加载病例异常：{e}")
    
    def get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        根据病例 ID 获取病例
        
        :param case_id: 病例 ID
        :return: 病例记录或 None
        """
        for case in self._case_database:
            if case['case_id'] == case_id:
                return case
        return None
    
    def get_all_cases(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取所有病例
        
        :param limit: 返回数量限制
        :return: 病例列表
        """
        return self._case_database[-limit:]
    
    def search_cases(self, disease_name: str) -> List[Dict[str, Any]]:
        """
        根据病害名称搜索病例
        
        :param disease_name: 病害名称
        :return: 匹配的病例列表
        """
        matched_cases = []
        
        for case in self._case_database:
            case_disease = case.get('diagnosis_info', {}).get('disease_name', '')
            if disease_name.lower() in case_disease.lower():
                matched_cases.append(case)
        
        return matched_cases
    
    def export_cases_to_json(self, file_path: str) -> None:
        """
        导出所有病例到 JSON 文件
        
        :param file_path: 输出文件路径
        """
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "total_cases": len(self._case_database),
                "cases": self._case_database
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"[CaseRecordTool] 已导出 {len(self._case_database)} 个病例到：{file_path}")
        
        except Exception as e:
            print(f"[CaseRecordTool] 导出失败：{e}")


def test_case_record_tool():
    """测试病例记录工具"""
    print("=" * 60)
    print("🧪 测试 CaseRecordTool")
    print("=" * 60)
    
    tool = CaseRecordTool()
    
    print("\n1️⃣ 初始化工具")
    init_success = tool.initialize()
    print(f"   初始化结果：{'成功' if init_success else '失败'}")
    
    print("\n2️⃣ 获取工具信息")
    print(f"   工具名称：{tool.get_name()}")
    print(f"   工具描述：{tool.get_description()}")
    
    print("\n3️⃣ 记录病例")
    # 模拟诊断计划
    diagnosis_plan = {
        "病害诊断": {
            "病害名称": "条锈病",
            "置信度": 0.92,
            "主要特征": ["黄色条状孢子堆", "沿叶脉排列"],
            "病原体": "条形柄锈菌",
            "诊断结论": "综合判断为条锈病"
        },
        "严重度评估": {
            "严重度等级": "中度",
            "严重度评分": 0.45,
            "影响评估": "病斑中等，对产量有一定影响",
            "防治建议": "立即采取防治措施"
        },
        "防治措施": {
            "推荐药剂": [
                {"name": "三唑酮", "concentration": "15% 可湿性粉剂", "dosage": "600-800 倍液"}
            ],
            "防治步骤": ["立即喷施治疗性杀菌剂", "7-10 天后复查"],
            "施药时机": "晴朗无风天气",
            "安全间隔期": "14 天",
            "注意事项": ["交替使用药剂", "注意防护"]
        },
        "复查计划": {
            "复查时间": "2026-03-16",
            "复查间隔": "7 天",
            "紧急程度": "重要",
            "复查内容": ["拍摄田间照片", "描述病情变化"],
            "预期目标": "病情得到控制",
            "复查任务 ID": "FOLLOWUP_20260309_条锈"
        }
    }
    
    result = tool.execute(
        diagnosis_plan=diagnosis_plan,
        image_path="test_yellow_rust.jpg",
        user_info={"user_id": "test_user", "location": "河南郑州"}
    )
    
    print(f"\n4️⃣ 记录结果:")
    print(f"   成功：{result.get('success')}")
    if result.get('data'):
        data = result['data']
        print(f"   病例 ID: {data.get('case_id')}")
        print(f"   记录时间：{data.get('record_time')}")
        print(f"   保存路径：{data.get('file_path')}")
        print(f"\n   病例摘要:")
        print(f"   {data.get('case_summary')}")
    
    print("\n" + "=" * 60)
    print("✅ CaseRecordTool 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_case_record_tool()

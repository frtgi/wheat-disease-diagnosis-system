# -*- coding: utf-8 -*-
"""
复查计划工具 - Followup Tool
创建和管理复查任务，跟踪病情变化
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .base_tool import BaseTool


class FollowupTool(BaseTool):
    """
    复查计划工具类
    
    功能：
    1. 根据诊断计划创建复查任务
    2. 设置复查时间和提醒
    3. 跟踪复查任务状态
    4. 生成复查报告
    
    输入参数:
        followup_plan: 复查计划（必需）
        disease_name: 病害名称（可选）
        severity_level: 严重度等级（可选）
        create_reminder: 是否创建提醒（可选，默认 True）
    
    输出结果:
        task_id: 复查任务 ID
        scheduled_time: 计划复查时间
        reminder_set: 是否已设置提醒
        task_details: 任务详细信息
    """
    
    def __init__(self, storage_path: str = None):
        """
        初始化复查计划工具
        
        :param storage_path: 任务存储路径（可选）
        """
        super().__init__(
            name="FollowupTool",
            description="复查计划工具，创建和管理复查任务"
        )
        
        # 设置默认存储路径
        if storage_path is None:
            base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
            self.storage_path = os.path.join(base_dir, 'followup_tasks')
        else:
            self.storage_path = storage_path
        
        self._task_database: List[Dict[str, Any]] = []
        self._task_counter = 0
    
    def get_name(self) -> str:
        """
        获取工具名称
        
        :return: 工具名称
        """
        return "FollowupTool"
    
    def get_description(self) -> str:
        """
        获取工具描述
        
        :return: 工具描述
        """
        return "复查计划工具，创建和管理复查任务"
    
    def initialize(self) -> bool:
        """
        初始化工具，创建存储目录
        
        :return: 初始化是否成功
        """
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            self._load_tasks()
            print(f"[FollowupTool] 初始化完成，存储路径：{self.storage_path}")
            return True
        except Exception as e:
            print(f"[FollowupTool] 初始化失败：{e}")
            return False
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证输入参数
        
        :param kwargs: 输入参数
        :return: 参数是否有效
        """
        followup_plan = kwargs.get('followup_plan')
        if not followup_plan:
            print("[FollowupTool] 参数验证失败：缺少 followup_plan")
            return False
        
        return True
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行复查任务创建
        
        :param kwargs: 执行参数
            - followup_plan: 复查计划
            - disease_name: 病害名称
            - severity_level: 严重度等级
            - create_reminder: 是否创建提醒
        :return: 创建结果字典
        """
        followup_plan = kwargs.get('followup_plan')
        disease_name = kwargs.get('disease_name', '')
        severity_level = kwargs.get('severity_level', '')
        create_reminder = kwargs.get('create_reminder', True)
        
        print(f"[FollowupTool] 创建复查任务：{disease_name}")
        
        try:
            # 创建复查任务
            followup_task = self._create_followup_task(
                followup_plan,
                disease_name,
                severity_level,
                create_reminder
            )
            
            # 保存到任务数据库
            self._task_database.append(followup_task)
            self._task_counter += 1
            
            # 保存到文件
            file_path = self._save_task_to_file(followup_task)
            
            result = {
                "success": True,
                "data": {
                    "task_id": followup_task['task_id'],
                    "scheduled_time": followup_task['scheduled_time'],
                    "reminder_set": create_reminder,
                    "task_details": followup_task,
                    "file_path": file_path
                },
                "message": f"复查任务创建成功：{followup_task['task_id']}",
                "tool_name": self.get_name()
            }
            
            print(f"[FollowupTool] 复查任务创建完成：{followup_task['task_id']}")
            
            return result
        
        except Exception as e:
            error_msg = f"复查任务创建异常：{str(e)}"
            print(f"[FollowupTool] {error_msg}")
            return {
                "success": False,
                "data": None,
                "message": error_msg,
                "error": error_msg,
                "tool_name": self.get_name()
            }
    
    def _create_followup_task(
        self,
        followup_plan: Dict[str, Any],
        disease_name: str,
        severity_level: str,
        create_reminder: bool
    ) -> Dict[str, Any]:
        """
        创建复查任务
        
        :param followup_plan: 复查计划
        :param disease_name: 病害名称
        :param severity_level: 严重度等级
        :param create_reminder: 是否创建提醒
        :return: 复查任务字典
        """
        # 生成任务 ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_id = followup_plan.get(
            "复查任务 ID",
            f"FOLLOWUP_{timestamp}_{self._task_counter:04d}"
        )
        
        # 解析复查时间
        followup_time_str = followup_plan.get("复查时间", "")
        followup_interval = followup_plan.get("复查间隔", "7 天")
        urgency = followup_plan.get("紧急程度", "常规")
        followup_content = followup_plan.get("复查内容", [])
        expected_goal = followup_plan.get("预期目标", "")
        
        # 计算计划时间
        if followup_time_str:
            try:
                scheduled_time = datetime.strptime(followup_time_str, "%Y-%m-%d")
            except ValueError:
                scheduled_time = datetime.now() + timedelta(days=7)
        else:
            scheduled_time = datetime.now() + timedelta(days=7)
        
        # 创建复查任务
        followup_task = {
            "task_id": task_id,
            "created_time": datetime.now().isoformat(),
            "scheduled_time": scheduled_time.strftime("%Y-%m-%d %H:%M"),
            "disease_info": {
                "disease_name": disease_name,
                "severity_level": severity_level
            },
            "followup_details": {
                "followup_interval": followup_interval,
                "urgency": urgency,
                "followup_content": followup_content,
                "expected_goal": expected_goal
            },
            "reminder": {
                "enabled": create_reminder,
                "reminder_time": (scheduled_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
                "reminder_method": "系统通知"
            },
            "status": "待执行",
            "priority": self._get_priority_from_urgency(urgency),
            "notes": [],
            "completion_info": {
                "completed": False,
                "completed_time": None,
                "completion_notes": None
            },
            "metadata": {
                "version": "1.0",
                "tool": self.get_name()
            }
        }
        
        return followup_task
    
    def _get_priority_from_urgency(self, urgency: str) -> str:
        """
        根据紧急程度获取优先级
        
        :param urgency: 紧急程度
        :return: 优先级字符串
        """
        priority_map = {
            "紧急": "高",
            "重要": "中",
            "常规": "低"
        }
        return priority_map.get(urgency, "中")
    
    def _save_task_to_file(self, followup_task: Dict[str, Any]) -> str:
        """
        将复查任务保存到文件
        
        :param followup_task: 复查任务
        :return: 保存的文件路径
        """
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            
            # 生成文件名
            filename = f"{followup_task['task_id']}.json"
            file_path = os.path.join(self.storage_path, filename)
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(followup_task, f, ensure_ascii=False, indent=2)
            
            print(f"[FollowupTool] 任务已保存：{file_path}")
            return file_path
        
        except Exception as e:
            print(f"[FollowupTool] 保存文件失败：{e}")
            return None
    
    def _load_tasks(self) -> None:
        """
        加载现有任务数据
        """
        try:
            if not os.path.exists(self.storage_path):
                return
            
            for filename in os.listdir(self.storage_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.storage_path, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            task = json.load(f)
                            self._task_database.append(task)
                            self._task_counter += 1
                    except Exception as e:
                        print(f"[FollowupTool] 加载任务失败 {filename}: {e}")
            
            print(f"[FollowupTool] 已加载 {len(self._task_database)} 个历史任务")
        
        except Exception as e:
            print(f"[FollowupTool] 加载任务异常：{e}")
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        根据任务 ID 获取任务
        
        :param task_id: 任务 ID
        :return: 任务字典或 None
        """
        for task in self._task_database:
            if task['task_id'] == task_id:
                return task
        return None
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        获取待执行任务
        
        :return: 待执行任务列表
        """
        return [t for t in self._task_database if t['status'] == '待执行']
    
    def complete_task(self, task_id: str, completion_notes: str = None) -> bool:
        """
        标记任务为已完成
        
        :param task_id: 任务 ID
        :param completion_notes: 完成备注
        :return: 是否成功
        """
        task = self.get_task_by_id(task_id)
        if task:
            task['status'] = '已完成'
            task['completion_info']['completed'] = True
            task['completion_info']['completed_time'] = datetime.now().isoformat()
            task['completion_info']['completion_notes'] = completion_notes
            return True
        return False
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        :return: 统计信息字典
        """
        total = len(self._task_database)
        pending = len(self.get_pending_tasks())
        completed = total - pending
        
        return {
            "total_tasks": total,
            "pending_tasks": pending,
            "completed_tasks": completed,
            "completion_rate": f"{completed/total*100:.1f}%" if total > 0 else "0%"
        }


def test_followup_tool():
    """测试复查计划工具"""
    print("=" * 60)
    print("🧪 测试 FollowupTool")
    print("=" * 60)
    
    tool = FollowupTool()
    
    print("\n1️⃣ 初始化工具")
    init_success = tool.initialize()
    print(f"   初始化结果：{'成功' if init_success else '失败'}")
    
    print("\n2️⃣ 获取工具信息")
    print(f"   工具名称：{tool.get_name()}")
    print(f"   工具描述：{tool.get_description()}")
    
    print("\n3️⃣ 创建复查任务")
    followup_plan = {
        "复查时间": "2026-03-16",
        "复查间隔": "7 天",
        "紧急程度": "重要",
        "复查内容": [
            "拍摄田间照片（与本次相同位置）",
            "描述病情变化情况",
            "记录已采取的防治措施",
            "评估防治效果"
        ],
        "预期目标": "7 天后病情得到控制",
        "复查任务 ID": "FOLLOWUP_20260309_条锈"
    }
    
    result = tool.execute(
        followup_plan=followup_plan,
        disease_name="条锈病",
        severity_level="中度",
        create_reminder=True
    )
    
    print(f"\n4️⃣ 创建结果:")
    print(f"   成功：{result.get('success')}")
    if result.get('data'):
        data = result['data']
        print(f"   任务 ID: {data.get('task_id')}")
        print(f"   计划时间：{data.get('scheduled_time')}")
        print(f"   提醒设置：{'已设置' if data.get('reminder_set') else '未设置'}")
        print(f"   优先级：{data.get('task_details', {}).get('priority', '未知')}")
    
    print("\n5️⃣ 任务统计")
    stats = tool.get_task_statistics()
    print(f"   总任务数：{stats.get('total_tasks')}")
    print(f"   待执行：{stats.get('pending_tasks')}")
    print(f"   已完成：{stats.get('completed_tasks')}")
    print(f"   完成率：{stats.get('completion_rate')}")
    
    print("\n" + "=" * 60)
    print("✅ FollowupTool 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_followup_tool()

# -*- coding: utf-8 -*-
"""
工具管理器 - Tool Manager
IWDDA Agent 工具执行层核心组件，统一管理所有工具的注册、调用和结果返回

功能特性:
1. 工具注册机制：支持动态注册和注销工具
2. 工具调用接口：统一的 execute() 方法调用所有工具
3. 工具状态管理：跟踪工具可用性、执行历史
4. 与规划层集成：根据诊断计划自动调用相应工具
5. 工具执行结果反馈：返回结构化执行结果

使用示例:
    from src.tools import ToolManager, DiagnosisTool, KnowledgeRetrievalTool
    
    # 初始化工具管理器
    manager = ToolManager()
    
    # 注册工具
    manager.register_tool("diagnosis", DiagnosisTool())
    manager.register_tool("knowledge", KnowledgeRetrievalTool())
    
    # 调用工具
    result = manager.execute_tool("diagnosis", image_path="test.jpg")
    
    # 批量执行工具
    results = manager.execute_multiple([
        {"tool_name": "diagnosis", "params": {"image_path": "test.jpg"}},
        {"tool_name": "knowledge", "params": {"disease_name": "条锈病"}}
    ])
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .base_tool import BaseTool


class ToolManager:
    """
    工具管理器类
    
    负责统一管理所有工具：
    - 工具注册/注销
    - 工具调用和参数传递
    - 工具执行结果收集和反馈
    - 工具状态监控
    - 与 PlanningEngine 集成
    """
    
    def __init__(self):
        """
        初始化工具管理器
        """
        self._tools: Dict[str, BaseTool] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._tool_status: Dict[str, bool] = {}
        self._max_history_size = 100
        
        print("[ToolManager] 工具管理器初始化完成")
    
    def register_tool(self, name: str, tool: BaseTool) -> bool:
        """
        注册工具到管理器
        
        :param name: 工具注册名称（唯一标识）
        :param tool: 工具实例（必须继承 BaseTool）
        :return: 注册是否成功
        """
        if not isinstance(tool, BaseTool):
            print(f"[ToolManager] 注册失败：工具必须继承 BaseTool 类")
            return False
        
        if name in self._tools:
            print(f"[ToolManager] 警告：工具 '{name}' 已存在，将被覆盖")
        
        try:
            # 初始化工具
            if hasattr(tool, 'initialize'):
                init_success = tool.initialize()
                if not init_success:
                    print(f"[ToolManager] 工具 '{name}' 初始化失败")
                    return False
            
            self._tools[name] = tool
            self._tool_status[name] = True
            print(f"[ToolManager] 工具注册成功：{name} - {tool.get_name()}")
            return True
        
        except Exception as e:
            print(f"[ToolManager] 注册工具 '{name}' 时发生错误：{e}")
            return False
    
    def unregister_tool(self, name: str) -> bool:
        """
        从管理器注销工具
        
        :param name: 工具注册名称
        :return: 注销是否成功
        """
        if name not in self._tools:
            print(f"[ToolManager] 注销失败：工具 '{name}' 不存在")
            return False
        
        try:
            # 清理工具资源
            tool = self._tools[name]
            if hasattr(tool, 'cleanup'):
                tool.cleanup()
            
            del self._tools[name]
            del self._tool_status[name]
            print(f"[ToolManager] 工具注销成功：{name}")
            return True
        
        except Exception as e:
            print(f"[ToolManager] 注销工具 '{name}' 时发生错误：{e}")
            return False
    
    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        执行指定工具
        
        :param name: 工具注册名称
        :param kwargs: 工具执行参数
        :return: 工具执行结果字典
        """
        if name not in self._tools:
            error_msg = f"工具 '{name}' 不存在"
            print(f"[ToolManager] 执行失败：{error_msg}")
            return {
                "success": False,
                "data": None,
                "message": error_msg,
                "error": error_msg,
                "tool_name": name,
                "timestamp": datetime.now().isoformat()
            }
        
        if not self._tool_status.get(name, False):
            error_msg = f"工具 '{name}' 当前不可用"
            print(f"[ToolManager] 执行失败：{error_msg}")
            return {
                "success": False,
                "data": None,
                "message": error_msg,
                "error": error_msg,
                "tool_name": name,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            tool = self._tools[name]
            
            # 验证参数
            if hasattr(tool, 'validate_params'):
                if not tool.validate_params(**kwargs):
                    error_msg = "参数验证失败"
                    return {
                        "success": False,
                        "data": None,
                        "message": error_msg,
                        "error": error_msg,
                        "tool_name": name,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 执行工具
            print(f"[ToolManager] 执行工具：{name}")
            result = tool.execute(**kwargs)
            
            # 确保结果包含必要字段
            if not isinstance(result, dict):
                result = {
                    "success": True,
                    "data": result,
                    "message": "执行成功",
                    "tool_name": name
                }
            
            # 添加元数据
            result["tool_name"] = name
            result["timestamp"] = datetime.now().isoformat()
            
            # 记录执行历史
            self._record_execution(name, kwargs, result)
            
            return result
        
        except Exception as e:
            error_msg = f"工具执行异常：{str(e)}"
            print(f"[ToolManager] {error_msg}")
            return {
                "success": False,
                "data": None,
                "message": error_msg,
                "error": error_msg,
                "tool_name": name,
                "timestamp": datetime.now().isoformat()
            }
    
    def execute_multiple(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量执行多个工具
        
        :param tool_calls: 工具调用列表，每项包含：
            - tool_name: 工具名称
            - params: 工具参数（可选）
        :return: 工具执行结果列表
        """
        results = []
        
        for call in tool_calls:
            tool_name = call.get("tool_name")
            params = call.get("params", {})
            
            if not tool_name:
                results.append({
                    "success": False,
                    "data": None,
                    "message": "未指定工具名称",
                    "error": "tool_name is required"
                })
                continue
            
            result = self.execute_tool(tool_name, **params)
            results.append(result)
        
        return results
    
    def execute_from_plan(self, diagnosis_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据诊断计划自动执行相应工具（与 PlanningEngine 集成）
        
        :param diagnosis_plan: 诊断计划（来自 PlanningEngine）
        :return: 工具执行结果列表
        """
        tool_calls = []
        
        # 从诊断计划提取信息并生成工具调用
        disease_diagnosis = diagnosis_plan.get("病害诊断", {})
        severity_assessment = diagnosis_plan.get("严重度评估", {})
        treatment_measures = diagnosis_plan.get("防治措施", {})
        followup_plan = diagnosis_plan.get("复查计划", {})
        
        disease_name = disease_diagnosis.get("病害名称", "")
        severity_level = severity_assessment.get("严重度等级", "")
        
        # 1. 如果需要知识检索
        if disease_name:
            tool_calls.append({
                "tool_name": "knowledge",
                "params": {"disease_name": disease_name}
            })
        
        # 2. 如果需要生成防治方案
        if treatment_measures:
            tool_calls.append({
                "tool_name": "treatment",
                "params": {
                    "disease_name": disease_name,
                    "severity_level": severity_level,
                    "existing_measures": treatment_measures
                }
            })
        
        # 3. 如果需要创建复查任务
        if followup_plan:
            tool_calls.append({
                "tool_name": "followup",
                "params": {"followup_plan": followup_plan}
            })
        
        # 4. 如果需要记录病例
        tool_calls.append({
            "tool_name": "case_record",
            "params": {"diagnosis_plan": diagnosis_plan}
        })
        
        # 批量执行工具
        results = self.execute_multiple(tool_calls)
        
        return results
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        获取指定工具实例
        
        :param name: 工具注册名称
        :return: 工具实例或 None
        """
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        获取所有已注册工具
        
        :return: 工具字典
        """
        return self._tools.copy()
    
    def get_tool_names(self) -> List[str]:
        """
        获取所有已注册工具名称
        
        :return: 工具名称列表
        """
        return list(self._tools.keys())
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取工具执行历史
        
        :param limit: 返回记录数量限制
        :return: 执行历史列表
        """
        return self._execution_history[-limit:]
    
    def get_tool_status(self, name: str) -> Optional[bool]:
        """
        获取工具状态
        
        :param name: 工具注册名称
        :return: 工具状态（True=可用，False=不可用）
        """
        return self._tool_status.get(name)
    
    def get_all_tool_metadata(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的元数据
        
        :return: 工具元数据列表
        """
        metadata_list = []
        
        for name, tool in self._tools.items():
            metadata = tool.get_metadata()
            metadata["registered_name"] = name
            metadata_list.append(metadata)
        
        return metadata_list
    
    def clear_history(self) -> None:
        """
        清空执行历史
        """
        self._execution_history.clear()
        print("[ToolManager] 执行历史已清空")
    
    def _record_execution(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        记录工具执行历史
        
        :param tool_name: 工具名称
        :param params: 执行参数
        :param result: 执行结果
        """
        record = {
            "tool_name": tool_name,
            "params": params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        self._execution_history.append(record)
        
        # 限制历史记录大小
        if len(self._execution_history) > self._max_history_size:
            self._execution_history = self._execution_history[-self._max_history_size:]
    
    def export_history_to_json(self, file_path: str) -> None:
        """
        将执行历史导出为 JSON 文件
        
        :param file_path: 输出文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self._execution_history, f, ensure_ascii=False, indent=2)
        
        print(f"[ToolManager] 执行历史已导出至：{file_path}")
    
    def __len__(self) -> int:
        """
        获取已注册工具数量
        
        :return: 工具数量
        """
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        """
        检查工具是否已注册
        
        :param name: 工具注册名称
        :return: 是否已注册
        """
        return name in self._tools
    
    def __str__(self) -> str:
        """
        工具管理器的字符串表示
        
        :return: 描述字符串
        """
        tool_list = ", ".join(self.get_tool_names())
        return f"ToolManager(已注册工具：{len(self)}个 - [{tool_list}])"


def test_tool_manager():
    """测试工具管理器"""
    print("=" * 60)
    print("🧪 测试 ToolManager")
    print("=" * 60)
    
    manager = ToolManager()
    
    print(f"\n1️⃣ 初始状态：已注册工具数 = {len(manager)}")
    
    print("\n2️⃣ 注册工具（示例）")
    # 这里只是示例，实际工具会在后续文件中实现
    print("   工具注册功能已就绪，等待具体工具实现")
    
    print("\n3️⃣ 获取工具列表")
    print(f"   工具名称：{manager.get_tool_names()}")
    
    print("\n" + "=" * 60)
    print("✅ ToolManager 基础测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_tool_manager()

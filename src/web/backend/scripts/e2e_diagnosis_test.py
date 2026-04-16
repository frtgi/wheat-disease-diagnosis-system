"""
端到端诊断流程测试脚本
验证从后端到前端的数据流完整性
"""
import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class TestResult:
    """
    单个测试用例的结果
    
    属性:
        name: 测试名称
        success: 是否成功
        message: 结果消息
        duration_ms: 执行耗时（毫秒）
        details: 详细信息字典
    """
    name: str
    success: bool
    message: str
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将测试结果转换为字典格式
        
        返回:
            Dict[str, Any]: 测试结果的字典表示
        """
        return {
            "name": self.name,
            "success": self.success,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "details": self.details
        }


@dataclass
class SSEEvent:
    """
    SSE 事件数据结构
    
    属性:
        event_type: 事件类型
        data: 事件数据
        raw: 原始事件字符串
    """
    event_type: str
    data: Dict[str, Any]
    raw: str = ""


class E2EDiagnosisTest:
    """
    端到端诊断测试类
    
    用于测试完整的诊断流程，包括：
    - 后端服务健康检查
    - SSE 流式诊断端点测试
    - 数据格式验证
    - 前端数据绑定验证
    """
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        """
        初始化测试器
        
        参数:
            base_url: API 基础 URL
        """
        self.base_url = base_url.rstrip("/")
        self.test_results: List[TestResult] = []
        self.timeout = 30.0
        
    def _create_test_image(self, width: int = 640, height: int = 480) -> bytes:
        """
        创建测试用的图像数据
        
        参数:
            width: 图像宽度
            height: 图像高度
            
        返回:
            bytes: PNG 格式的图像字节数据
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL 库未安装，无法创建测试图像")
        
        img = Image.new("RGB", (width, height), color=(139, 69, 19))
        for y in range(height):
            for x in range(width):
                if (x + y) % 50 < 25:
                    img.putpixel((x, y), (160, 82, 45))
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    
    async def test_health_check(self) -> TestResult:
        """
        测试服务健康检查
        
        验证后端服务是否正常运行，包括：
        - 基本健康状态
        - 就绪状态检查
        - 组件状态检查
        
        返回:
            TestResult: 测试结果
        """
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                ready_response = await client.get(f"{self.base_url}/health/ready")
                
                if ready_response.status_code != 200:
                    return TestResult(
                        name="健康检查",
                        success=False,
                        message=f"服务未就绪，状态码: {ready_response.status_code}",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                    )
                
                ready_data = ready_response.json()
                
                components_response = await client.get(f"{self.base_url}/health/components")
                components_data = components_response.json() if components_response.status_code == 200 else {}
                
                is_ready = ready_data.get("ready", False)
                critical_components = ready_data.get("critical_components", {})
                
                details = {
                    "ready": is_ready,
                    "status": ready_data.get("status"),
                    "critical_components": critical_components,
                    "components_summary": components_data.get("summary", {})
                }
                
                if is_ready:
                    return TestResult(
                        name="健康检查",
                        success=True,
                        message="服务健康，所有关键组件就绪",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                        details=details
                    )
                else:
                    return TestResult(
                        name="健康检查",
                        success=False,
                        message=f"服务未完全就绪，状态: {ready_data.get('status')}",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                        details=details
                    )
                    
        except httpx.ConnectError:
            return TestResult(
                name="健康检查",
                success=False,
                message="无法连接到后端服务，请确保服务已启动",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
        except Exception as e:
            return TestResult(
                name="健康检查",
                success=False,
                message=f"健康检查失败: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    def _parse_sse_events(self, content: str) -> List[SSEEvent]:
        """
        解析 SSE 事件流
        
        参数:
            content: SSE 响应内容
            
        返回:
            List[SSEEvent]: 解析后的事件列表
        """
        events = []
        current_event = None
        current_data = []
        
        for line in content.split("\n"):
            line = line.strip()
            
            if line.startswith("event:"):
                if current_event and current_data:
                    try:
                        data_str = "\n".join(current_data)
                        if data_str.startswith("data:"):
                            data_str = data_str[5:].strip()
                        event_data = json.loads(data_str)
                        events.append(SSEEvent(
                            event_type=current_event,
                            data=event_data,
                            raw=content
                        ))
                    except json.JSONDecodeError:
                        pass
                
                current_event = line[6:].strip()
                current_data = []
                
            elif line.startswith("data:"):
                current_data.append(line)
                
            elif line == "" and current_event and current_data:
                try:
                    data_str = "\n".join(current_data)
                    if data_str.startswith("data:"):
                        data_str = data_str[5:].strip()
                    event_data = json.loads(data_str)
                    events.append(SSEEvent(
                        event_type=current_event,
                        data=event_data,
                        raw=content
                    ))
                except json.JSONDecodeError:
                    pass
                current_event = None
                current_data = []
        
        if current_event and current_data:
            try:
                data_str = "\n".join(current_data)
                if data_str.startswith("data:"):
                    data_str = data_str[5:].strip()
                event_data = json.loads(data_str)
                events.append(SSEEvent(
                    event_type=current_event,
                    data=event_data,
                    raw=content
                ))
            except json.JSONDecodeError:
                pass
        
        return events
    
    async def test_sse_diagnosis(
        self,
        test_case: Dict[str, Any],
        case_name: str
    ) -> TestResult:
        """
        测试 SSE 诊断端点
        
        参数:
            test_case: 测试用例配置
                - image: 是否包含图像
                - symptoms: 症状描述
                - weather: 天气条件
                - growth_stage: 生长阶段
                - affected_part: 发病部位
            case_name: 测试用例名称
            
        返回:
            TestResult: 测试结果
        """
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {}
                data = {
                    "symptoms": test_case.get("symptoms", ""),
                    "weather": test_case.get("weather", ""),
                    "growth_stage": test_case.get("growth_stage", ""),
                    "affected_part": test_case.get("affected_part", ""),
                    "enable_thinking": "true",
                    "use_graph_rag": "true"
                }
                
                if test_case.get("image", False):
                    image_bytes = self._create_test_image()
                    files["image"] = ("test_image.png", image_bytes, "image/png")
                
                response = await client.post(
                    f"{self.base_url}/diagnosis/fusion/stream",
                    data=data,
                    files=files if files else None
                )
                
                if response.status_code != 200:
                    return TestResult(
                        name=f"SSE诊断测试 - {case_name}",
                        success=False,
                        message=f"请求失败，状态码: {response.status_code}",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                    )
                
                content_type = response.headers.get("content-type", "")
                if "text/event-stream" not in content_type:
                    return TestResult(
                        name=f"SSE诊断测试 - {case_name}",
                        success=False,
                        message=f"响应类型错误: {content_type}，期望 text/event-stream",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                    )
                
                events = self._parse_sse_events(response.text)
                
                if not events:
                    return TestResult(
                        name=f"SSE诊断测试 - {case_name}",
                        success=False,
                        message="未收到任何 SSE 事件",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                    )
                
                event_types = [e.event_type for e in events]
                has_start = "start" in event_types
                has_progress = "progress" in event_types
                has_complete = "complete" in event_types
                has_error = "error" in event_types
                
                details = {
                    "event_count": len(events),
                    "event_types": event_types,
                    "has_start": has_start,
                    "has_progress": has_progress,
                    "has_complete": has_complete,
                    "has_error": has_error
                }
                
                if has_error:
                    error_event = next((e for e in events if e.event_type == "error"), None)
                    error_msg = error_event.data.get("data", {}).get("message", "未知错误") if error_event else "未知错误"
                    return TestResult(
                        name=f"SSE诊断测试 - {case_name}",
                        success=False,
                        message=f"诊断过程中发生错误: {error_msg}",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                        details=details
                    )
                
                if not has_complete:
                    return TestResult(
                        name=f"SSE诊断测试 - {case_name}",
                        success=False,
                        message="未收到 complete 事件，诊断流程未完成",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                        details=details
                    )
                
                complete_event = next((e for e in events if e.event_type == "complete"), None)
                if complete_event:
                    details["complete_data"] = complete_event.data
                
                return TestResult(
                    name=f"SSE诊断测试 - {case_name}",
                    success=True,
                    message=f"SSE 事件流正常，共 {len(events)} 个事件",
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    details=details
                )
                
        except Exception as e:
            return TestResult(
                name=f"SSE诊断测试 - {case_name}",
                success=False,
                message=f"SSE 诊断测试失败: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    def validate_progress_event(self, event_data: Dict[str, Any]) -> tuple:
        """
        验证 progress 事件格式
        
        参数:
            event_data: 事件数据
            
        返回:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if "data" not in event_data:
            return False, "缺少 data 字段"
        
        data = event_data["data"]
        
        required_fields = ["stage", "progress", "message"]
        for field in required_fields:
            if field not in data:
                return False, f"缺少必需字段: {field}"
        
        progress = data.get("progress")
        if not isinstance(progress, (int, float)):
            return False, "progress 字段必须是数字"
        
        if not (0 <= progress <= 100):
            return False, f"progress 值超出范围: {progress}"
        
        return True, None
    
    def validate_complete_event(self, event_data: Dict[str, Any]) -> tuple:
        """
        验证 complete 事件格式
        
        参数:
            event_data: 事件数据
            
        返回:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if "data" not in event_data:
            return False, "缺少 data 字段"
        
        data = event_data["data"]
        
        if "success" not in data:
            return False, "缺少 success 字段"
        
        if not data.get("success"):
            if "error" not in data and "message" not in data:
                return False, "失败的响应缺少错误信息"
            return True, None
        
        if "diagnosis" not in data:
            return False, "缺少 diagnosis 字段"
        
        diagnosis = data["diagnosis"]
        
        required_diagnosis_fields = ["disease_name", "confidence"]
        for field in required_diagnosis_fields:
            if field not in diagnosis:
                return False, f"诊断结果缺少必需字段: {field}"
        
        confidence = diagnosis.get("confidence")
        if not isinstance(confidence, (int, float)):
            return False, "confidence 字段必须是数字"
        
        if not (0 <= confidence <= 1):
            return False, f"confidence 值超出范围: {confidence}"
        
        return True, None
    
    async def test_data_format(self, test_case: Dict[str, Any], case_name: str) -> TestResult:
        """
        验证数据格式
        
        测试 SSE 事件数据格式是否符合前端期望
        
        参数:
            test_case: 测试用例配置
            case_name: 测试用例名称
            
        返回:
            TestResult: 测试结果
        """
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {}
                data = {
                    "symptoms": test_case.get("symptoms", ""),
                    "weather": test_case.get("weather", ""),
                    "growth_stage": test_case.get("growth_stage", ""),
                    "affected_part": test_case.get("affected_part", ""),
                    "enable_thinking": "true",
                    "use_graph_rag": "true"
                }
                
                if test_case.get("image", False):
                    image_bytes = self._create_test_image()
                    files["image"] = ("test_image.png", image_bytes, "image/png")
                
                response = await client.post(
                    f"{self.base_url}/diagnosis/fusion/stream",
                    data=data,
                    files=files if files else None
                )
                
                if response.status_code != 200:
                    return TestResult(
                        name=f"数据格式验证 - {case_name}",
                        success=False,
                        message=f"请求失败，状态码: {response.status_code}",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                    )
                
                events = self._parse_sse_events(response.text)
                
                validation_errors = []
                progress_events = [e for e in events if e.event_type == "progress"]
                complete_events = [e for e in events if e.event_type == "complete"]
                
                for i, event in enumerate(progress_events):
                    is_valid, error = self.validate_progress_event(event.data)
                    if not is_valid:
                        validation_errors.append(f"Progress 事件 #{i+1}: {error}")
                
                for i, event in enumerate(complete_events):
                    is_valid, error = self.validate_complete_event(event.data)
                    if not is_valid:
                        validation_errors.append(f"Complete 事件 #{i+1}: {error}")
                
                details = {
                    "progress_events_count": len(progress_events),
                    "complete_events_count": len(complete_events),
                    "validation_errors": validation_errors
                }
                
                if validation_errors:
                    return TestResult(
                        name=f"数据格式验证 - {case_name}",
                        success=False,
                        message=f"数据格式验证失败: {'; '.join(validation_errors[:3])}",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                        details=details
                    )
                
                return TestResult(
                    name=f"数据格式验证 - {case_name}",
                    success=True,
                    message="所有事件数据格式验证通过",
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    details=details
                )
                
        except Exception as e:
            return TestResult(
                name=f"数据格式验证 - {case_name}",
                success=False,
                message=f"数据格式验证失败: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    def validate_frontend_binding(self, complete_data: Dict[str, Any]) -> tuple:
        """
        验证数据结构是否符合前端期望
        
        检查诊断结果是否包含前端组件所需的所有字段
        
        参数:
            complete_data: complete 事件的数据
            
        返回:
            tuple: (is_valid: bool, errors: List[str])
        """
        errors = []
        
        if not complete_data.get("success"):
            return True, []
        
        diagnosis = complete_data.get("diagnosis", {})
        
        frontend_required_fields = {
            "disease_name": "病害名称",
            "confidence": "置信度",
            "visual_confidence": "视觉置信度",
            "textual_confidence": "文本置信度",
            "description": "病害描述",
            "recommendations": "防治建议"
        }
        
        for field, desc in frontend_required_fields.items():
            if field not in diagnosis:
                errors.append(f"缺少前端必需字段: {field} ({desc})")
        
        if "recommendations" in diagnosis:
            if not isinstance(diagnosis["recommendations"], list):
                errors.append("recommendations 字段应为列表类型")
        
        if "knowledge_references" in diagnosis:
            if not isinstance(diagnosis["knowledge_references"], list):
                errors.append("knowledge_references 字段应为列表类型")
            else:
                for i, ref in enumerate(diagnosis["knowledge_references"]):
                    if not isinstance(ref, dict):
                        errors.append(f"knowledge_references[{i}] 应为字典类型")
                        break
        
        if "roi_boxes" in diagnosis:
            if not isinstance(diagnosis["roi_boxes"], list):
                errors.append("roi_boxes 字段应为列表类型")
            else:
                for i, box in enumerate(diagnosis["roi_boxes"]):
                    if not isinstance(box, dict):
                        errors.append(f"roi_boxes[{i}] 应为字典类型")
                        break
                    if "class_name" not in box or "confidence" not in box:
                        errors.append(f"roi_boxes[{i}] 缺少 class_name 或 confidence 字段")
                        break
        
        return len(errors) == 0, errors
    
    async def test_frontend_binding(self, test_case: Dict[str, Any], case_name: str) -> TestResult:
        """
        验证前端数据绑定
        
        测试返回数据是否可以直接用于前端组件渲染
        
        参数:
            test_case: 测试用例配置
            case_name: 测试用例名称
            
        返回:
            TestResult: 测试结果
        """
        start_time = datetime.now()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {}
                data = {
                    "symptoms": test_case.get("symptoms", ""),
                    "weather": test_case.get("weather", ""),
                    "growth_stage": test_case.get("growth_stage", ""),
                    "affected_part": test_case.get("affected_part", ""),
                    "enable_thinking": "true",
                    "use_graph_rag": "true"
                }
                
                if test_case.get("image", False):
                    image_bytes = self._create_test_image()
                    files["image"] = ("test_image.png", image_bytes, "image/png")
                
                response = await client.post(
                    f"{self.base_url}/diagnosis/fusion/stream",
                    data=data,
                    files=files if files else None
                )
                
                if response.status_code != 200:
                    return TestResult(
                        name=f"前端数据绑定验证 - {case_name}",
                        success=False,
                        message=f"请求失败，状态码: {response.status_code}",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                    )
                
                events = self._parse_sse_events(response.text)
                complete_event = next((e for e in events if e.event_type == "complete"), None)
                
                if not complete_event:
                    return TestResult(
                        name=f"前端数据绑定验证 - {case_name}",
                        success=False,
                        message="未收到 complete 事件",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                    )
                
                is_valid, errors = self.validate_frontend_binding(complete_event.data)
                
                details = {
                    "complete_data": complete_event.data,
                    "binding_errors": errors
                }
                
                if not is_valid:
                    return TestResult(
                        name=f"前端数据绑定验证 - {case_name}",
                        success=False,
                        message=f"前端数据绑定验证失败: {'; '.join(errors[:3])}",
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                        details=details
                    )
                
                return TestResult(
                    name=f"前端数据绑定验证 - {case_name}",
                    success=True,
                    message="前端数据绑定验证通过",
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    details=details
                )
                
        except Exception as e:
            return TestResult(
                name=f"前端数据绑定验证 - {case_name}",
                success=False,
                message=f"前端数据绑定验证失败: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def run_all_tests(self) -> None:
        """
        运行所有测试用例
        
        包括：
        1. 健康检查测试
        2. 纯图像诊断测试
        3. 纯文本诊断测试
        4. 多模态融合诊断测试
        5. 数据格式验证
        6. 前端数据绑定验证
        """
        print("=" * 60)
        print("端到端诊断流程测试")
        print("=" * 60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标服务: {self.base_url}")
        print("-" * 60)
        
        print("\n[1/4] 健康检查测试...")
        health_result = await self.test_health_check()
        self.test_results.append(health_result)
        self._print_result(health_result)
        
        if not health_result.success:
            print("\n服务未就绪，跳过后续测试")
            return
        
        test_cases = {
            "纯图像诊断": {
                "image": True,
                "symptoms": "",
                "weather": "晴朗",
                "growth_stage": "抽穗期",
                "affected_part": "叶片"
            },
            "纯文本诊断": {
                "image": False,
                "symptoms": "小麦叶片出现黄褐色条状锈斑，严重时叶片枯黄",
                "weather": "高温高湿",
                "growth_stage": "灌浆期",
                "affected_part": "叶片"
            },
            "多模态融合诊断": {
                "image": True,
                "symptoms": "叶片上有明显的锈色斑点，逐渐扩大成条状",
                "weather": "阴雨",
                "growth_stage": "拔节期",
                "affected_part": "叶片"
            }
        }
        
        print("\n[2/4] SSE 诊断端点测试...")
        for case_name, test_case in test_cases.items():
            result = await self.test_sse_diagnosis(test_case, case_name)
            self.test_results.append(result)
            self._print_result(result)
        
        print("\n[3/4] 数据格式验证测试...")
        for case_name, test_case in test_cases.items():
            result = await self.test_data_format(test_case, case_name)
            self.test_results.append(result)
            self._print_result(result)
        
        print("\n[4/4] 前端数据绑定验证测试...")
        for case_name, test_case in test_cases.items():
            result = await self.test_frontend_binding(test_case, case_name)
            self.test_results.append(result)
            self._print_result(result)
    
    def _print_result(self, result: TestResult) -> None:
        """
        打印单个测试结果
        
        参数:
            result: 测试结果对象
        """
        status = "✓ 通过" if result.success else "✗ 失败"
        print(f"  {status} - {result.name}")
        print(f"    消息: {result.message}")
        print(f"    耗时: {result.duration_ms:.2f}ms")
    
    def generate_report(self) -> str:
        """
        生成测试报告
        
        返回:
            str: 格式化的测试报告
        """
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(r.duration_ms for r in self.test_results)
        
        report_lines = [
            "=" * 60,
            "端到端诊断流程测试报告",
            "=" * 60,
            f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"目标服务: {self.base_url}",
            "-" * 60,
            "",
            "测试摘要:",
            f"  总测试数: {total_tests}",
            f"  通过: {passed_tests}",
            f"  失败: {failed_tests}",
            f"  通过率: {(passed_tests / total_tests * 100) if total_tests > 0 else 0:.1f}%",
            f"  总耗时: {total_duration:.2f}ms",
            "",
            "-" * 60,
            "详细结果:",
            ""
        ]
        
        for i, result in enumerate(self.test_results, 1):
            status = "✓ 通过" if result.success else "✗ 失败"
            report_lines.extend([
                f"[{i}] {result.name}",
                f"    状态: {status}",
                f"    消息: {result.message}",
                f"    耗时: {result.duration_ms:.2f}ms",
                ""
            ])
            
            if not result.success and result.details:
                report_lines.append("    详细信息:")
                for key, value in result.details.items():
                    if key in ["complete_data"]:
                        continue
                    report_lines.append(f"      {key}: {value}")
                report_lines.append("")
        
        if failed_tests > 0:
            report_lines.extend([
                "-" * 60,
                "失败测试详情:",
                ""
            ])
            
            for result in self.test_results:
                if not result.success:
                    report_lines.extend([
                        f"【{result.name}】",
                        f"  错误: {result.message}",
                        ""
                    ])
        
        report_lines.extend([
            "=" * 60,
            "测试完成",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
    
    def save_report(self, output_path: str) -> None:
        """
        保存测试报告到文件
        
        参数:
            output_path: 输出文件路径
        """
        report = self.generate_report()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n测试报告已保存到: {output_path}")


async def main():
    """
    主函数
    
    执行端到端测试并生成报告
    """
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    
    tester = E2EDiagnosisTest(base_url=base_url)
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return
    
    print("\n")
    print(tester.generate_report())
    
    output_dir = Path(__file__).parent / "reports"
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    tester.save_report(str(report_path))


if __name__ == "__main__":
    asyncio.run(main())

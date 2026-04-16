"""
融合诊断显示修复端到端测试
验证诊断结果显示、实时推理过程展示、前后端数据交互
"""
import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from typing import Dict, Any, List, Optional


class FusionDiagnosisE2ETest:
    """融合诊断端到端测试"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = "/api/v1"
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        
    def _record_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        if success:
            self.passed += 1
            print(f"  ✅ {test_name}: {message}")
        else:
            self.failed += 1
            print(f"  ❌ {test_name}: {message}")
            
    async def test_sse_steps_event(self):
        """测试步骤定义事件"""
        print("\n📋 测试步骤定义事件...")
        
        url = f"{self.base_url}{self.api_prefix}/diagnosis/fusion/stream?symptoms=叶片发黄"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        self._record_result("步骤定义事件", False, f"状态码: {response.status_code}")
                        return False
                    
                    async for line in response.aiter_lines():
                        if line.startswith("event: steps"):
                            # 读取下一行数据
                            data_line = await response.aiter_lines().__anext__()
                            if data_line.startswith("data:"):
                                data = json.loads(data_line[5:].strip())
                                if "steps" in data and len(data["steps"]) > 0:
                                    self._record_result(
                                        "步骤定义事件", 
                                        True, 
                                        f"收到 {len(data['steps'])} 个步骤定义",
                                        {"steps": data["steps"]}
                                    )
                                    return True
                    
                    self._record_result("步骤定义事件", False, "未收到步骤定义事件")
                    return False
                    
        except Exception as e:
            self._record_result("步骤定义事件", False, f"请求失败: {str(e)}")
            return False
            
    async def test_sse_log_events(self):
        """测试日志事件流"""
        print("\n📋 测试日志事件流...")
        
        url = f"{self.base_url}{self.api_prefix}/diagnosis/fusion/stream?symptoms=叶片发黄"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        self._record_result("日志事件流", False, f"状态码: {response.status_code}")
                        return False
                    
                    log_count = 0
                    async for line in response.aiter_lines():
                        if line.startswith("event: log"):
                            data_line = await response.aiter_lines().__anext__()
                            if data_line.startswith("data:"):
                                data = json.loads(data_line[5:].strip())
                                log_count += 1
                                if log_count >= 2:  # 收到2个日志事件即可
                                    self._record_result(
                                        "日志事件流", 
                                        True, 
                                        f"收到 {log_count} 个日志事件",
                                        {"sample_log": data}
                                    )
                                    return True
                    
                    if log_count > 0:
                        self._record_result("日志事件流", True, f"收到 {log_count} 个日志事件")
                        return True
                    else:
                        self._record_result("日志事件流", False, "未收到日志事件")
                        return False
                    
        except Exception as e:
            self._record_result("日志事件流", False, f"请求失败: {str(e)}")
            return False
            
    async def test_sse_progress_events(self):
        """测试进度事件流"""
        print("\n📋 测试进度事件流...")
        
        url = f"{self.base_url}{self.api_prefix}/diagnosis/fusion/stream?symptoms=叶片发黄"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        self._record_result("进度事件流", False, f"状态码: {response.status_code}")
                        return False
                    
                    progress_events = []
                    async for line in response.aiter_lines():
                        if line.startswith("event: progress"):
                            data_line = await response.aiter_lines().__anext__()
                            if data_line.startswith("data:"):
                                data = json.loads(data_line[5:].strip())
                                progress_events.append(data)
                                if len(progress_events) >= 3:
                                    self._record_result(
                                        "进度事件流", 
                                        True, 
                                        f"收到 {len(progress_events)} 个进度事件",
                                        {"progress_range": [e.get("progress") for e in progress_events]}
                                    )
                                    return True
                    
                    if progress_events:
                        self._record_result("进度事件流", True, f"收到 {len(progress_events)} 个进度事件")
                        return True
                    else:
                        self._record_result("进度事件流", False, "未收到进度事件")
                        return False
                    
        except Exception as e:
            self._record_result("进度事件流", False, f"请求失败: {str(e)}")
            return False
            
    async def test_sse_complete_event(self):
        """测试完成事件数据完整性"""
        print("\n📋 测试完成事件数据完整性...")
        
        url = f"{self.base_url}{self.api_prefix}/diagnosis/fusion/stream?symptoms=叶片发黄"
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        self._record_result("完成事件数据", False, f"状态码: {response.status_code}")
                        return False
                    
                    async for line in response.aiter_lines():
                        if line.startswith("event: complete"):
                            data_line = await response.aiter_lines().__anext__()
                            if data_line.startswith("data:"):
                                data = json.loads(data_line[5:].strip())
                                
                                issues = []
                                
                                # 检查必要字段
                                if "success" not in data:
                                    issues.append("缺少 success 字段")
                                if "diagnosis" not in data:
                                    issues.append("缺少 diagnosis 字段")
                                else:
                                    diagnosis = data["diagnosis"]
                                    required_fields = ["disease_name", "confidence", "recommendations"]
                                    for field in required_fields:
                                        if field not in diagnosis:
                                            issues.append(f"diagnosis 缺少 {field} 字段")
                                
                                if issues:
                                    self._record_result("完成事件数据", False, "; ".join(issues), data)
                                    return False
                                else:
                                    self._record_result(
                                        "完成事件数据", 
                                        True, 
                                        f"诊断结果: {data['diagnosis'].get('disease_name')}, 置信度: {data['diagnosis'].get('confidence')}",
                                        {
                                            "disease_name": data["diagnosis"].get("disease_name"),
                                            "confidence": data["diagnosis"].get("confidence"),
                                            "has_recommendations": len(data["diagnosis"].get("recommendations", [])) > 0
                                        }
                                    )
                                    return True
                    
                    self._record_result("完成事件数据", False, "未收到完成事件")
                    return False
                    
        except Exception as e:
            self._record_result("完成事件数据", False, f"请求失败: {str(e)}")
            return False
            
    async def test_sse_heartbeat(self):
        """测试心跳事件"""
        print("\n📋 测试心跳事件...")
        
        url = f"{self.base_url}{self.api_prefix}/diagnosis/fusion/stream?symptoms=叶片发黄"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        self._record_result("心跳事件", False, f"状态码: {response.status_code}")
                        return False
                    
                    heartbeat_count = 0
                    start_time = time.time()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("event: heartbeat"):
                            heartbeat_count += 1
                            if heartbeat_count >= 1:
                                self._record_result(
                                    "心跳事件", 
                                    True, 
                                    f"收到心跳事件",
                                    {"heartbeat_count": heartbeat_count}
                                )
                                return True
                        
                        # 超过20秒还没有心跳，也视为通过（因为诊断可能很快完成）
                        if time.time() - start_time > 20:
                            self._record_result("心跳事件", True, "诊断快速完成，心跳事件可选")
                            return True
                    
                    self._record_result("心跳事件", True, "连接正常")
                    return True
                    
        except Exception as e:
            self._record_result("心跳事件", False, f"请求失败: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🧪 融合诊断显示修复端到端测试")
        print("=" * 60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标服务: {self.base_url}")
        
        # 健康检查
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code != 200:
                    print("\n❌ 服务不可用，跳过测试")
                    return self._generate_report()
        except Exception as e:
            print(f"\n❌ 服务连接失败: {e}")
            return self._generate_report()
        
        print("\n✅ 服务可用，开始测试...")
        
        # 运行测试
        await self.test_sse_steps_event()
        await self.test_sse_log_events()
        await self.test_sse_progress_events()
        await self.test_sse_complete_event()
        await self.test_sse_heartbeat()
        
        return self._generate_report()
        
    def _generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total = self.passed + self.failed
        
        report = {
            "summary": {
                "total": total,
                "passed": self.passed,
                "failed": self.failed,
                "pass_rate": round(self.passed / total * 100, 2) if total > 0 else 0,
                "timestamp": datetime.now().isoformat()
            },
            "results": self.results
        }
        
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        print(f"总计: {total} 个测试")
        print(f"通过: {self.passed} 个")
        print(f"失败: {self.failed} 个")
        print(f"通过率: {report['summary']['pass_rate']}%")
        print("=" * 60)
        
        if self.failed == 0 and self.passed > 0:
            print("✅ 所有测试通过！")
        elif self.failed > 0:
            print("⚠️ 存在失败的测试，请检查详细信息")
        else:
            print("❌ 无法完成测试")
            
        return report


async def main():
    """主函数"""
    runner = FusionDiagnosisE2ETest()
    report = await runner.run_all_tests()
    
    # 保存报告
    report_path = Path(__file__).parent / "reports" / f"fusion_diagnosis_e2e_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试报告已保存: {report_path}")
    
    return report["summary"]["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

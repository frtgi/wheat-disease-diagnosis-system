"""
前后端集成测试脚本
验证所有修复是否正确生效
"""
import asyncio
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from typing import Dict, Any, List, Optional


class IntegrationTestRunner:
    """集成测试运行器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = "/api/v1"
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.test_user_id: Optional[int] = None
        
    def _record_result(self, test_name: str, success: bool, message: str, duration_ms: float = 0):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        if success:
            self.passed += 1
            print(f"  ✅ {test_name}: {message}")
        else:
            self.failed += 1
            print(f"  ❌ {test_name}: {message}")
        
    def _skip_result(self, test_name: str, reason: str):
        """记录跳过的测试"""
        self.skipped += 1
        self.results.append({
            "test_name": test_name,
            "success": None,
            "message": f"跳过: {reason}",
            "timestamp": datetime.now().isoformat()
        })
        print(f"  ⏭️ {test_name}: 跳过 - {reason}")
        
    async def test_health_check(self):
        """测试健康检查端点"""
        print("\n📋 测试健康检查端点...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = time.time()
                response = await client.get(f"{self.base_url}/health")
                duration = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    self._record_result(
                        "健康检查", 
                        True, 
                        f"服务状态: {data.get('status', 'unknown')}",
                        duration
                    )
                    return True
                else:
                    self._record_result("健康检查", False, f"状态码: {response.status_code}")
                    return False
        except Exception as e:
            self._record_result("健康检查", False, f"连接失败: {str(e)}")
            return False
            
    async def test_api_health_check(self):
        """测试 API 健康检查端点"""
        print("\n📋 测试 API 健康检查端点...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = time.time()
                response = await client.get(f"{self.base_url}{self.api_prefix}/health")
                duration = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    self._record_result(
                        "API 健康检查", 
                        True, 
                        f"状态: {data.get('status', 'unknown')}, 版本: {data.get('version', 'unknown')}",
                        duration
                    )
                    return True
                else:
                    self._record_result("API 健康检查", False, f"状态码: {response.status_code}")
                    return False
        except Exception as e:
            self._record_result("API 健康检查", False, f"连接失败: {str(e)}")
            return False
            
    async def test_user_registration(self):
        """测试用户注册接口"""
        print("\n📋 测试用户注册接口...")
        
        timestamp = int(time.time())
        test_user = {
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = time.time()
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/users/register",
                    json=test_user
                )
                duration = (time.time() - start) * 1000
                
                data = response.json()
                
                if "success" in data:
                    if data["success"]:
                        self.test_user_id = data.get("data", {}).get("id")
                        self._record_result(
                            "用户注册", 
                            True, 
                            f"用户ID: {self.test_user_id}, 用户名: {test_user['username']}",
                            duration
                        )
                        return True, test_user
                    else:
                        error_code = data.get("error_code", "unknown")
                        self._record_result("用户注册", False, f"错误: {data.get('error')} (代码: {error_code})")
                        return False, test_user
                else:
                    self._record_result("用户注册", False, f"响应格式错误: {data}")
                    return False, test_user
                    
        except Exception as e:
            self._record_result("用户注册", False, f"请求失败: {str(e)}")
            return False, test_user
            
    async def test_user_login(self, username: str, password: str):
        """测试用户登录接口"""
        print("\n📋 测试用户登录接口...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = time.time()
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/users/login",
                    json={"username": username, "password": password}
                )
                duration = (time.time() - start) * 1000
                
                data = response.json()
                
                if "success" in data:
                    if data["success"]:
                        self.access_token = data.get("data", {}).get("access_token")
                        self.refresh_token = data.get("data", {}).get("refresh_token")
                        user_data = data.get("data", {}).get("user", {})
                        self._record_result(
                            "用户登录", 
                            True, 
                            f"Token 获取成功, 用户: {user_data.get('username')}",
                            duration
                        )
                        return True
                    else:
                        error_code = data.get("error_code", "unknown")
                        self._record_result("用户登录", False, f"错误: {data.get('error')} (代码: {error_code})")
                        return False
                else:
                    self._record_result("用户登录", False, f"响应格式错误: {data}")
                    return False
                    
        except Exception as e:
            self._record_result("用户登录", False, f"请求失败: {str(e)}")
            return False
            
    async def test_duplicate_registration(self, existing_user: dict):
        """测试重复注册（应返回错误）"""
        print("\n📋 测试重复注册错误处理...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = time.time()
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/users/register",
                    json=existing_user
                )
                duration = (time.time() - start) * 1000
                
                data = response.json()
                
                if not data.get("success", True) and "error_code" in data:
                    self._record_result(
                        "重复注册错误处理", 
                        True, 
                        f"正确返回错误: {data.get('error_code')}",
                        duration
                    )
                    return True
                else:
                    self._record_result("重复注册错误处理", False, f"未正确处理重复注册, 响应: {data}")
                    return False
                    
        except Exception as e:
            self._record_result("重复注册错误处理", False, f"请求失败: {str(e)}")
            return False
            
    async def test_invalid_login(self):
        """测试无效登录（应返回错误）"""
        print("\n📋 测试无效登录错误处理...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = time.time()
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/users/login",
                    json={"username": "nonexistent_user", "password": "wrong_password"}
                )
                duration = (time.time() - start) * 1000
                
                data = response.json()
                
                if not data.get("success", True) and data.get("error_code") == "AUTH_002":
                    self._record_result(
                        "无效登录错误处理", 
                        True, 
                        f"正确返回错误: {data.get('error_code')}",
                        duration
                    )
                    return True
                else:
                    self._record_result("无效登录错误处理", False, f"错误处理不正确: {data}")
                    return False
                    
        except Exception as e:
            self._record_result("无效登录错误处理", False, f"请求失败: {str(e)}")
            return False
            
    async def test_sse_endpoint(self):
        """测试 SSE 端点连接"""
        print("\n📋 测试 SSE 端点连接...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                start = time.time()
                
                async with client.stream(
                    "GET",
                    f"{self.base_url}{self.api_prefix}/diagnosis/fusion/stream",
                    params={"symptoms": "叶片发黄"}
                ) as response:
                    duration = (time.time() - start) * 1000
                    
                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        if "text/event-stream" in content_type:
                            event_count = 0
                            async for line in response.aiter_lines():
                                if line.startswith("event:"):
                                    event_count += 1
                                    if event_count >= 2:
                                        break
                                        
                            self._record_result(
                                "SSE 端点连接", 
                                True, 
                                f"收到 {event_count} 个事件",
                                duration
                            )
                            return True
                        else:
                            self._record_result("SSE 端点连接", False, f"错误的 Content-Type: {content_type}")
                            return False
                    else:
                        self._record_result("SSE 端点连接", False, f"状态码: {response.status_code}")
                        return False
                        
        except Exception as e:
            self._record_result("SSE 端点连接", False, f"连接失败: {str(e)}")
            return False
            
    async def test_upload_endpoint(self):
        """测试文件上传端点"""
        print("\n📋 测试文件上传端点...")
        
        test_image_content = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                start = time.time()
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/upload/image",
                    files={"file": ("test.png", test_image_content, "image/png")}
                )
                duration = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("success"):
                        self._record_result(
                            "文件上传", 
                            True, 
                            f"文件URL: {data.get('url')}",
                            duration
                        )
                        return True
                    else:
                        self._record_result("文件上传", False, f"上传失败: {data}")
                        return False
                else:
                    self._record_result("文件上传", False, f"状态码: {response.status_code}")
                    return False
                    
        except httpx.TimeoutException:
            self._record_result("文件上传", False, "请求超时 (120s)")
            return False
        except Exception as e:
            self._record_result("文件上传", False, f"请求失败: {str(e)}")
            return False
            
    async def test_response_format_consistency(self):
        """测试响应格式一致性"""
        print("\n📋 测试响应格式一致性...")
        
        endpoints = [
            ("/health", "GET"),
            ("/api/v1/health", "GET"),
        ]
        
        all_consistent = True
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                for endpoint, method in endpoints:
                    try:
                        if method == "GET":
                            response = await client.get(f"{self.base_url}{endpoint}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            has_success = "success" in data or "status" in data
                            if has_success:
                                self._record_result(
                                    f"响应格式 - {endpoint}", 
                                    True, 
                                    "格式正确"
                                )
                            else:
                                self._record_result(
                                    f"响应格式 - {endpoint}", 
                                    False, 
                                    f"缺少必要字段: {list(data.keys())}"
                                )
                                all_consistent = False
                        else:
                            self._record_result(
                                f"响应格式 - {endpoint}", 
                                False, 
                                f"状态码: {response.status_code}"
                            )
                            all_consistent = False
                            
                    except httpx.TimeoutException:
                        self._record_result(f"响应格式 - {endpoint}", False, "请求超时 (60s)")
                        all_consistent = False
                    except Exception as e:
                        self._record_result(f"响应格式 - {endpoint}", False, f"错误: {str(e)}")
                        all_consistent = False
        except Exception as e:
            print(f"  ❌ 响应格式测试失败: {str(e)}")
            all_consistent = False
                    
        return all_consistent
        
    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🚀 前后端集成测试")
        print("=" * 60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标服务: {self.base_url}")
        
        health_ok = await self.test_health_check()
        
        if not health_ok:
            print("\n❌ 服务不可用，跳过后续测试")
            self._skip_result("所有后续测试", "服务不可用")
            return self._generate_report()
            
        await self.test_api_health_check()
        
        reg_ok, test_user = await self.test_user_registration()
        
        if reg_ok:
            await self.test_user_login(test_user["username"], test_user["password"])
            await self.test_duplicate_registration(test_user)
        await self.test_invalid_login()
        await asyncio.sleep(1)
        await self.test_sse_endpoint()
        await asyncio.sleep(1)
        await self.test_upload_endpoint()
        await asyncio.sleep(1)
        await self.test_response_format_consistency()
        
        return self._generate_report()
        
    def _generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total = self.passed + self.failed + self.skipped
        
        report = {
            "summary": {
                "total": total,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
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
        print(f"跳过: {self.skipped} 个")
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
    runner = IntegrationTestRunner()
    report = await runner.run_all_tests()
    
    report_path = Path(__file__).parent / "reports" / f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试报告已保存: {report_path}")
    
    return report["summary"]["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

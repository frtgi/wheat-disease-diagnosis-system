"""
小麦病害诊断功能测试脚本

测试内容：
1. 图像上传诊断测试
2. 多模态融合诊断测试
3. 诊断报告生成验证
4. 诊断历史记录查询测试
"""
import os
import sys
import json
import time
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiagnosisTester:
    """诊断功能测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化测试器
        
        参数:
            base_url: API 基础 URL
        """
        self.base_url = base_url
        self.test_results = {
            "test_time": datetime.now().isoformat(),
            "base_url": base_url,
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
        self.auth_token = None
        self.test_image_path = None
        
    def _add_result(self, test_name: str, success: bool, details: Dict[str, Any], 
                    error: Optional[str] = None, warning: Optional[str] = None):
        """
        添加测试结果
        
        参数:
            test_name: 测试名称
            success: 是否成功
            details: 测试详情
            error: 错误信息
            warning: 警告信息
        """
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
        if error:
            result["error"] = error
        if warning:
            result["warning"] = warning
            
        self.test_results["tests"].append(result)
        self.test_results["summary"]["total"] += 1
        
        if success:
            self.test_results["summary"]["passed"] += 1
            logger.info(f"✓ {test_name} - 通过")
        else:
            self.test_results["summary"]["failed"] += 1
            logger.error(f"✗ {test_name} - 失败: {error}")
            
        if warning:
            self.test_results["summary"]["warnings"] += 1
            logger.warning(f"⚠ {test_name} - 警告: {warning}")
    
    def _find_test_image(self) -> Optional[Path]:
        """
        查找测试图像
        
        返回:
            测试图像路径,如果未找到则返回 None
        """
        possible_paths = [
            Path("D:/Project/WheatAgent/datasets/wheat_data_unified/images/val/Aphid_0.png"),
            Path("D:/Project/WheatAgent/datasets/wheat_data_unified/images/val/Blast_0.jpg"),
            Path("D:/Project/WheatAgent/datasets/wheat_data_unified/images/val/Mite_0.png"),
            Path("D:/Project/WheatAgent/datasets/wheat_data_unified/images/val/Smut_0.jpg"),
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"找到测试图像: {path}")
                return path
        
        logger.warning("未找到测试图像,将使用 Mock 模式测试")
        return None
    
    async def _get_auth_token(self, session: aiohttp.ClientSession) -> Optional[str]:
        """
        获取认证令牌
        
        参数:
            session: aiohttp 会话
            
        返回:
            认证令牌,如果失败则返回 None
        """
        url = f"{self.base_url}/api/v1/user/login"
        
        try:
            data = {
                "username": "test_user",
                "password": "test_password123"
            }
            
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get("access_token")
                    if token:
                        logger.info("成功获取认证令牌")
                        return token
                elif response.status == 404:
                    logger.warning("登录接口不存在,尝试注册测试用户")
                    return await self._register_test_user(session)
                else:
                    logger.warning(f"登录失败 (状态码: {response.status}),将尝试注册测试用户")
                    return await self._register_test_user(session)
        except Exception as e:
            logger.warning(f"获取认证令牌失败: {e},将尝试注册测试用户")
            return await self._register_test_user(session)
        
        return None
    
    async def _register_test_user(self, session: aiohttp.ClientSession) -> Optional[str]:
        """
        注册测试用户并获取令牌
        
        参数:
            session: aiohttp 会话
            
        返回:
            认证令牌,如果失败则返回 None
        """
        url = f"{self.base_url}/api/v1/user/register"
        
        try:
            data = {
                "username": "test_user",
                "password": "test_password123",
                "email": "test@example.com"
            }
            
            async with session.post(url, json=data) as response:
                if response.status in [200, 201]:
                    logger.info("成功注册测试用户")
                    return await self._get_auth_token(session)
                else:
                    result = await response.json()
                    logger.warning(f"注册失败: {result}")
        except Exception as e:
            logger.warning(f"注册测试用户失败: {e}")
        
        return None
    
    async def test_health_check(self, session: aiohttp.ClientSession):
        """
        测试健康检查接口
        
        参数:
            session: aiohttp 会话
        """
        test_name = "健康检查测试"
        url = f"{self.base_url}/api/v1/health"
        
        try:
            start_time = time.time()
            async with session.get(url) as response:
                latency = (time.time() - start_time) * 1000
                result = await response.json()
                
                details = {
                    "status_code": response.status,
                    "latency_ms": round(latency, 2),
                    "response": result
                }
                
                if response.status == 200:
                    self._add_result(test_name, True, details)
                else:
                    self._add_result(test_name, False, details, 
                                   error=f"健康检查失败,状态码: {response.status}")
        except Exception as e:
            self._add_result(test_name, False, {}, error=str(e))
    
    async def test_image_diagnosis(self, session: aiohttp.ClientSession):
        """
        测试图像上传诊断
        
        参数:
            session: aiohttp 会话
        """
        test_name = "图像上传诊断测试"
        url = f"{self.base_url}/api/v1/diagnosis/image"
        
        try:
            if not self.test_image_path or not self.test_image_path.exists():
                self._add_result(test_name, False, {}, 
                               error="未找到测试图像文件",
                               warning="请确保测试图像存在或使用 Mock 模式")
                return
            
            data = aiohttp.FormData()
            data.add_field(
                "image",
                self.test_image_path.open("rb"),
                filename=self.test_image_path.name,
                content_type="image/jpeg" if self.test_image_path.suffix.lower() == ".jpg" else "image/png"
            )
            data.add_field("symptoms", "小麦叶片出现黄色斑点")
            
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            start_time = time.time()
            async with session.post(url, data=data, headers=headers) as response:
                latency = (time.time() - start_time) * 1000
                result = await response.json()
                
                details = {
                    "status_code": response.status,
                    "latency_ms": round(latency, 2),
                    "image_file": str(self.test_image_path),
                    "response": result
                }
                
                if response.status == 200:
                    if self._validate_diagnosis_response(result):
                        self._add_result(test_name, True, details)
                    else:
                        self._add_result(test_name, False, details, 
                                       error="诊断结果格式不完整")
                elif response.status == 401:
                    self._add_result(test_name, False, details, 
                                   error="未授权访问,需要认证令牌")
                else:
                    self._add_result(test_name, False, details, 
                                   error=f"诊断失败,状态码: {response.status}")
        except Exception as e:
            self._add_result(test_name, False, {}, error=str(e))
    
    async def test_multimodal_fusion_diagnosis(self, session: aiohttp.ClientSession):
        """
        测试多模态融合诊断
        
        参数:
            session: aiohttp 会话
        """
        test_name = "多模态融合诊断测试"
        url = f"{self.base_url}/api/v1/ai_diagnosis/fusion"
        
        try:
            data = aiohttp.FormData()
            
            if self.test_image_path and self.test_image_path.exists():
                data.add_field(
                    "image",
                    self.test_image_path.open("rb"),
                    filename=self.test_image_path.name,
                    content_type="image/jpeg" if self.test_image_path.suffix.lower() == ".jpg" else "image/png"
                )
            
            data.add_field("symptoms", "小麦叶片出现黄色条状锈斑,主要分布在叶片正面")
            data.add_field("weather", "高温高湿")
            data.add_field("growth_stage", "抽穗期")
            data.add_field("affected_part", "叶片")
            data.add_field("enable_thinking", "true")
            data.add_field("use_graph_rag", "true")
            data.add_field("use_cache", "false")
            
            start_time = time.time()
            async with session.post(url, data=data) as response:
                latency = (time.time() - start_time) * 1000
                result = await response.json()
                
                details = {
                    "status_code": response.status,
                    "latency_ms": round(latency, 2),
                    "has_image": self.test_image_path is not None and self.test_image_path.exists(),
                    "response": result
                }
                
                if response.status == 200:
                    if self._validate_fusion_diagnosis_response(result):
                        self._add_result(test_name, True, details)
                    else:
                        self._add_result(test_name, False, details, 
                                       error="融合诊断结果格式不完整",
                                       warning="部分字段可能缺失")
                else:
                    self._add_result(test_name, False, details, 
                                   error=f"融合诊断失败,状态码: {response.status}")
        except Exception as e:
            self._add_result(test_name, False, {}, error=str(e))
    
    async def test_multimodal_diagnosis(self, session: aiohttp.ClientSession):
        """
        测试 Qwen3-VL 多模态诊断
        
        参数:
            session: aiohttp 会话
        """
        test_name = "Qwen3-VL 多模态诊断测试"
        url = f"{self.base_url}/api/v1/ai_diagnosis/multimodal"
        
        try:
            data = aiohttp.FormData()
            
            if self.test_image_path and self.test_image_path.exists():
                data.add_field(
                    "image",
                    self.test_image_path.open("rb"),
                    filename=self.test_image_path.name,
                    content_type="image/jpeg" if self.test_image_path.suffix.lower() == ".jpg" else "image/png"
                )
            
            data.add_field("symptoms", "小麦叶片出现白色粉状霉层")
            data.add_field("thinking_mode", "true")
            data.add_field("use_graph_rag", "true")
            data.add_field("enable_kad_former", "true")
            data.add_field("use_cache", "false")
            
            start_time = time.time()
            async with session.post(url, data=data) as response:
                latency = (time.time() - start_time) * 1000
                result = await response.json()
                
                details = {
                    "status_code": response.status,
                    "latency_ms": round(latency, 2),
                    "has_image": self.test_image_path is not None and self.test_image_path.exists(),
                    "response": result
                }
                
                if response.status == 200:
                    if self._validate_multimodal_response(result):
                        self._add_result(test_name, True, details)
                    else:
                        self._add_result(test_name, False, details, 
                                       error="多模态诊断结果格式不完整")
                else:
                    self._add_result(test_name, False, details, 
                                   error=f"多模态诊断失败,状态码: {response.status}")
        except Exception as e:
            self._add_result(test_name, False, {}, error=str(e))
    
    async def test_diagnosis_history(self, session: aiohttp.ClientSession):
        """
        测试诊断历史记录查询
        
        参数:
            session: aiohttp 会话
        """
        test_name = "诊断历史记录查询测试"
        url = f"{self.base_url}/api/v1/diagnosis/records"
        
        try:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            params = {
                "skip": 0,
                "limit": 10
            }
            
            start_time = time.time()
            async with session.get(url, headers=headers, params=params) as response:
                latency = (time.time() - start_time) * 1000
                result = await response.json()
                
                details = {
                    "status_code": response.status,
                    "latency_ms": round(latency, 2),
                    "response": result
                }
                
                if response.status == 200:
                    if self._validate_history_response(result):
                        self._add_result(test_name, True, details)
                    else:
                        self._add_result(test_name, False, details, 
                                       error="历史记录格式不完整")
                elif response.status == 401:
                    self._add_result(test_name, False, details, 
                                   error="未授权访问,需要认证令牌")
                else:
                    self._add_result(test_name, False, details, 
                                   error=f"查询历史记录失败,状态码: {response.status}")
        except Exception as e:
            self._add_result(test_name, False, {}, error=str(e))
    
    async def test_text_diagnosis(self, session: aiohttp.ClientSession):
        """
        测试文本诊断
        
        参数:
            session: aiohttp 会话
        """
        test_name = "文本诊断测试"
        url = f"{self.base_url}/api/v1/ai_diagnosis/text"
        
        try:
            data = aiohttp.FormData()
            data.add_field("symptoms", "小麦叶片出现黄色条状锈斑,严重时叶片枯黄")
            
            start_time = time.time()
            async with session.post(url, data=data) as response:
                latency = (time.time() - start_time) * 1000
                result = await response.json()
                
                details = {
                    "status_code": response.status,
                    "latency_ms": round(latency, 2),
                    "response": result
                }
                
                if response.status == 200:
                    if self._validate_text_diagnosis_response(result):
                        self._add_result(test_name, True, details)
                    else:
                        self._add_result(test_name, False, details, 
                                       error="文本诊断结果格式不完整")
                else:
                    self._add_result(test_name, False, details, 
                                   error=f"文本诊断失败,状态码: {response.status}")
        except Exception as e:
            self._add_result(test_name, False, {}, error=str(e))
    
    async def test_ai_health(self, session: aiohttp.ClientSession):
        """
        测试 AI 服务健康检查
        
        参数:
            session: aiohttp 会话
        """
        test_name = "AI 服务健康检查测试"
        url = f"{self.base_url}/api/v1/ai_diagnosis/health/ai"
        
        try:
            start_time = time.time()
            async with session.get(url) as response:
                latency = (time.time() - start_time) * 1000
                result = await response.json()
                
                details = {
                    "status_code": response.status,
                    "latency_ms": round(latency, 2),
                    "response": result
                }
                
                if response.status == 200:
                    self._add_result(test_name, True, details)
                else:
                    self._add_result(test_name, False, details, 
                                   error=f"AI 健康检查失败,状态码: {response.status}")
        except Exception as e:
            self._add_result(test_name, False, {}, error=str(e))
    
    def _validate_diagnosis_response(self, response: Dict[str, Any]) -> bool:
        """
        验证诊断响应格式
        
        参数:
            response: 响应数据
            
        返回:
            是否有效
        """
        required_fields = ["disease_name", "confidence"]
        
        for field in required_fields:
            if field not in response:
                logger.warning(f"诊断响应缺少必需字段: {field}")
                return False
        
        if not isinstance(response.get("confidence"), (int, float)):
            logger.warning("置信度字段类型错误")
            return False
        
        if not (0 <= response.get("confidence", 0) <= 1):
            logger.warning("置信度值超出范围 [0, 1]")
            return False
        
        return True
    
    def _validate_fusion_diagnosis_response(self, response: Dict[str, Any]) -> bool:
        """
        验证融合诊断响应格式
        
        参数:
            response: 响应数据
            
        返回:
            是否有效
        """
        if not response.get("success"):
            logger.warning("融合诊断未成功")
            return False
        
        diagnosis = response.get("diagnosis", {})
        required_fields = ["disease_name", "confidence"]
        
        for field in required_fields:
            if field not in diagnosis:
                logger.warning(f"融合诊断响应缺少必需字段: {field}")
                return False
        
        if not isinstance(diagnosis.get("confidence"), (int, float)):
            logger.warning("置信度字段类型错误")
            return False
        
        return True
    
    def _validate_multimodal_response(self, response: Dict[str, Any]) -> bool:
        """
        验证多模态诊断响应格式
        
        参数:
            response: 响应数据
            
        返回:
            是否有效
        """
        if not response.get("success"):
            logger.warning("多模态诊断未成功")
            return False
        
        data = response.get("data", {})
        required_fields = ["disease_name", "confidence"]
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"多模态诊断响应缺少必需字段: {field}")
                return False
        
        return True
    
    def _validate_history_response(self, response: Dict[str, Any]) -> bool:
        """
        验证历史记录响应格式
        
        参数:
            response: 响应数据
            
        返回:
            是否有效
        """
        required_fields = ["records", "total"]
        
        for field in required_fields:
            if field not in response:
                logger.warning(f"历史记录响应缺少必需字段: {field}")
                return False
        
        if not isinstance(response.get("records"), list):
            logger.warning("records 字段类型错误")
            return False
        
        if not isinstance(response.get("total"), int):
            logger.warning("total 字段类型错误")
            return False
        
        return True
    
    def _validate_text_diagnosis_response(self, response: Dict[str, Any]) -> bool:
        """
        验证文本诊断响应格式
        
        参数:
            response: 响应数据
            
        返回:
            是否有效
        """
        if not response.get("success"):
            logger.warning("文本诊断未成功")
            return False
        
        data = response.get("data", {})
        required_fields = ["disease_name", "confidence"]
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"文本诊断响应缺少必需字段: {field}")
                return False
        
        return True
    
    def generate_report(self) -> str:
        """
        生成测试报告
        
        返回:
            测试报告 JSON 字符串
        """
        return json.dumps(self.test_results, indent=2, ensure_ascii=False)
    
    def save_report(self, output_path: str = "diagnosis_test_report.json"):
        """
        保存测试报告到文件
        
        参数:
            output_path: 输出文件路径
        """
        report = self.generate_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"测试报告已保存到: {output_path}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("开始执行小麦病害诊断功能测试")
        logger.info("=" * 60)
        
        self.test_image_path = self._find_test_image()
        
        async with aiohttp.ClientSession() as session:
            logger.info("\n步骤 1: 测试健康检查")
            await self.test_health_check(session)
            
            logger.info("\n步骤 2: 获取认证令牌")
            self.auth_token = await self._get_auth_token(session)
            if self.auth_token:
                logger.info("✓ 成功获取认证令牌")
            else:
                logger.warning("⚠ 未能获取认证令牌,部分测试可能失败")
            
            logger.info("\n步骤 3: 测试 AI 服务健康检查")
            await self.test_ai_health(session)
            
            logger.info("\n步骤 4: 测试图像上传诊断")
            await self.test_image_diagnosis(session)
            
            logger.info("\n步骤 5: 测试多模态融合诊断")
            await self.test_multimodal_fusion_diagnosis(session)
            
            logger.info("\n步骤 6: 测试 Qwen3-VL 多模态诊断")
            await self.test_multimodal_diagnosis(session)
            
            logger.info("\n步骤 7: 测试文本诊断")
            await self.test_text_diagnosis(session)
            
            logger.info("\n步骤 8: 测试诊断历史记录查询")
            await self.test_diagnosis_history(session)
        
        logger.info("\n" + "=" * 60)
        logger.info("测试执行完成")
        logger.info("=" * 60)
        
        summary = self.test_results["summary"]
        logger.info(f"\n测试摘要:")
        logger.info(f"  总计: {summary['total']} 个测试")
        logger.info(f"  通过: {summary['passed']} 个")
        logger.info(f"  失败: {summary['failed']} 个")
        logger.info(f"  警告: {summary['warnings']} 个")
        logger.info(f"  成功率: {summary['passed']/summary['total']*100:.1f}%")


async def main():
    """主函数"""
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    tester = DiagnosisTester(base_url=base_url)
    
    try:
        await tester.run_all_tests()
        
        output_path = "D:/Project/WheatAgent/diagnosis_test_report.json"
        tester.save_report(output_path)
        
        print("\n" + "=" * 60)
        print("详细测试报告:")
        print("=" * 60)
        print(tester.generate_report())
        
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
    except Exception as e:
        logger.error(f"\n测试执行出错: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())

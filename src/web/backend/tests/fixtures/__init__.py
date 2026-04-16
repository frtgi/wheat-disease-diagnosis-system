"""
测试 Fixtures 包
提供可复用的测试数据和工具函数
"""
from typing import Dict, Any, List
import random
import string


def generate_random_string(length: int = 10) -> str:
    """
    生成随机字符串
    
    参数:
        length: 字符串长度
    
    返回:
        随机字符串
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_email() -> str:
    """
    生成随机邮箱地址
    
    返回:
        随机邮箱地址
    """
    username = generate_random_string(8).lower()
    return f"{username}@test.com"


def generate_test_user_data(
    username: str = None,
    email: str = None,
    password: str = "testpass123",
    role: str = "farmer"
) -> Dict[str, Any]:
    """
    生成测试用户数据
    
    参数:
        username: 用户名，不提供则自动生成
        email: 邮箱，不提供则自动生成
        password: 密码
        role: 用户角色
    
    返回:
        用户数据字典
    """
    return {
        "username": username or f"test_{generate_random_string(6)}",
        "email": email or generate_random_email(),
        "password": password,
        "role": role,
    }


def generate_test_disease_data(
    name: str = None,
    category: str = "真菌病害"
) -> Dict[str, Any]:
    """
    生成测试病害数据
    
    参数:
        name: 病害名称，不提供则自动生成
        category: 病害类别
    
    返回:
        病害数据字典
    """
    return {
        "name": name or f"测试病害_{generate_random_string(4)}",
        "category": category,
        "symptoms": "测试症状描述",
        "cause": "测试病因",
        "treatment": "测试治疗方法",
        "prevention": "测试预防措施",
        "image_url": "http://example.com/test.jpg",
    }


def generate_test_diagnosis_data(
    user_id: int,
    disease_id: int = None,
    image_url: str = "http://example.com/test.jpg"
) -> Dict[str, Any]:
    """
    生成测试诊断数据
    
    参数:
        user_id: 用户 ID
        disease_id: 病害 ID
        image_url: 图片 URL
    
    返回:
        诊断数据字典
    """
    return {
        "user_id": user_id,
        "disease_id": disease_id,
        "image_url": image_url,
        "result": "测试诊断结果",
        "confidence": round(random.uniform(0.8, 0.99), 2),
        "status": "completed",
    }


def generate_batch_users(count: int = 10) -> List[Dict[str, Any]]:
    """
    批量生成测试用户数据
    
    参数:
        count: 用户数量
    
    返回:
        用户数据列表
    """
    users = []
    for i in range(count):
        users.append(generate_test_user_data(
            username=f"batch_user_{i}_{generate_random_string(4)}",
            email=f"batch_{i}_{generate_random_string(4)}@test.com"
        ))
    return users


def generate_batch_diseases(count: int = 10) -> List[Dict[str, Any]]:
    """
    批量生成测试病害数据
    
    参数:
        count: 病害数量
    
    返回:
        病害数据列表
    """
    diseases = []
    categories = ["真菌病害", "细菌病害", "病毒病害", "虫害", "生理性病害"]
    
    for i in range(count):
        diseases.append(generate_test_disease_data(
            name=f"测试病害_{i}_{generate_random_string(4)}",
            category=random.choice(categories)
        ))
    return diseases


class TestDataFactory:
    """测试数据工厂类"""
    
    @staticmethod
    def create_user(override: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        创建用户数据
        
        参数:
            override: 覆盖字段
        
        返回:
            用户数据字典
        """
        data = generate_test_user_data()
        if override:
            data.update(override)
        return data
    
    @staticmethod
    def create_disease(override: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        创建病害数据
        
        参数:
            override: 覆盖字段
        
        返回:
            病害数据字典
        """
        data = generate_test_disease_data()
        if override:
            data.update(override)
        return data
    
    @staticmethod
    def create_diagnosis(user_id: int, override: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        创建诊断数据
        
        参数:
            user_id: 用户 ID
            override: 覆盖字段
        
        返回:
            诊断数据字典
        """
        data = generate_test_diagnosis_data(user_id)
        if override:
            data.update(override)
        return data


__all__ = [
    "generate_random_string",
    "generate_random_email",
    "generate_test_user_data",
    "generate_test_disease_data",
    "generate_test_diagnosis_data",
    "generate_batch_users",
    "generate_batch_diseases",
    "TestDataFactory",
]

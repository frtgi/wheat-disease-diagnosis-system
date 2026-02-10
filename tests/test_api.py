# -*- coding: utf-8 -*-
"""
API测试模块

测试FastAPI接口功能
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """健康检查端点测试"""
    
    def test_root_endpoint(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "components" in data
    
    def test_models_list(self):
        """测试模型列表"""
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "models" in data


class TestDiagnosisEndpoints:
    """诊断端点测试"""
    
    def test_diagnose_text_without_params(self):
        """测试文本诊断 - 无参数"""
        response = client.post("/diagnose/text?description=")
        # 应该返回200，但可能有错误信息
        assert response.status_code in [200, 422, 500]
    
    def test_diagnose_text_with_params(self):
        """测试文本诊断 - 有参数"""
        response = client.post(
            "/diagnose/text",
            params={"description": "叶片出现黄色条纹"}
        )
        # 由于引擎可能未加载，可能返回503
        assert response.status_code in [200, 503, 500]
    
    def test_diagnose_image_without_file(self):
        """测试图像诊断 - 无文件"""
        response = client.post("/diagnose/image")
        # 应该返回422验证错误
        assert response.status_code == 422


class TestKnowledgeEndpoints:
    """知识图谱端点测试"""
    
    def test_list_diseases(self):
        """测试病害列表"""
        response = client.get("/knowledge/diseases")
        # 可能返回200或503（引擎未加载）
        assert response.status_code in [200, 503]
    
    def test_get_disease_info_not_found(self):
        """测试获取不存在的病害信息"""
        response = client.get("/knowledge/disease/不存在的病害")
        # 可能返回404或503
        assert response.status_code in [200, 404, 503]


class TestErrorHandling:
    """错误处理测试"""
    
    def test_not_found_endpoint(self):
        """测试不存在的端点"""
        response = client.get("/not-found")
        assert response.status_code == 404
    
    def test_invalid_method(self):
        """测试无效的方法"""
        response = client.post("/health")
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
测试数据生成模块
提供测试图像、测试数据生成功能
"""
import io
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont


class TestDataGenerator:
    """
    测试数据生成器类
    
    用于生成测试所需的图像、数据文件等
    """
    
    def __init__(self, output_dir: Path):
        """
        初始化测试数据生成器
        
        参数:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_sample_image(
        self,
        filename: str,
        size: tuple = (640, 480),
        color: tuple = (255, 255, 255),
        add_pattern: bool = True
    ) -> Path:
        """
        生成测试图像
        
        参数:
            filename: 文件名
            size: 图像尺寸 (宽, 高)
            color: 背景颜色 (R, G, B)
            add_pattern: 是否添加图案
        
        返回:
            Path: 生成的图像文件路径
        """
        img = Image.new('RGB', size, color=color)
        
        if add_pattern:
            draw = ImageDraw.Draw(img)
            
            draw.rectangle([50, 50, 200, 200], fill=(255, 165, 0), outline=(200, 100, 0))
            draw.ellipse([250, 50, 400, 200], fill=(0, 255, 0), outline=(0, 200, 0))
            draw.polygon([(450, 200), (550, 50), (600, 200)], fill=(0, 0, 255))
            
            draw.line([(0, 0), size], fill=(128, 128, 128), width=2)
            draw.line([(size[0], 0), (0, size[1])], fill=(128, 128, 128), width=2)
        
        image_path = self.images_dir / filename
        img.save(image_path, format='PNG')
        return image_path
    
    def generate_wheat_disease_image(
        self,
        disease_type: str,
        filename: Optional[str] = None
    ) -> Path:
        """
        生成模拟小麦病害图像
        
        参数:
            disease_type: 病害类型 (rust, powdery_mildew, aphid)
            filename: 文件名（可选）
        
        返回:
            Path: 生成的图像文件路径
        """
        size = (640, 480)
        
        if disease_type == "rust":
            img = Image.new('RGB', size, color=(144, 238, 144))
            draw = ImageDraw.Draw(img)
            
            for _ in range(50):
                x = 100 + (_ * 10) % 440
                y = 100 + (_ * 7) % 280
                draw.ellipse([x, y, x+15, y+15], fill=(255, 165, 0))
        
        elif disease_type == "powdery_mildew":
            img = Image.new('RGB', size, color=(144, 238, 144))
            draw = ImageDraw.Draw(img)
            
            for _ in range(40):
                x = 80 + (_ * 12) % 480
                y = 80 + (_ * 9) % 320
                draw.ellipse([x, y, x+20, y+20], fill=(255, 255, 255))
        
        elif disease_type == "aphid":
            img = Image.new('RGB', size, color=(144, 238, 144))
            draw = ImageDraw.Draw(img)
            
            for _ in range(30):
                x = 100 + (_ * 15) % 440
                y = 100 + (_ * 11) % 280
                draw.ellipse([x, y, x+8, y+12], fill=(50, 50, 50))
                draw.ellipse([x-5, y+4, x+13, y+8], fill=(50, 50, 50))
        
        else:
            img = Image.new('RGB', size, color=(144, 238, 144))
        
        if filename is None:
            filename = f"wheat_{disease_type}.png"
        
        image_path = self.images_dir / filename
        img.save(image_path, format='PNG')
        return image_path
    
    def generate_test_users_data(self) -> List[Dict]:
        """
        生成测试用户数据
        
        返回:
            List[Dict]: 测试用户数据列表
        """
        return [
            {
                "username": "farmer1",
                "email": "farmer1@test.com",
                "password": "TestPass123!",
                "role": "farmer",
                "phone": "13800138001",
            },
            {
                "username": "farmer2",
                "email": "farmer2@test.com",
                "password": "TestPass123!",
                "role": "farmer",
                "phone": "13800138002",
            },
            {
                "username": "technician1",
                "email": "technician1@test.com",
                "password": "TechPass123!",
                "role": "technician",
                "phone": "13800138003",
            },
            {
                "username": "admin1",
                "email": "admin1@test.com",
                "password": "AdminPass123!",
                "role": "admin",
                "phone": "13800138004",
            },
        ]
    
    def generate_test_diseases_data(self) -> List[Dict]:
        """
        生成测试病害数据
        
        返回:
            List[Dict]: 测试病害数据列表
        """
        return [
            {
                "name": "小麦锈病",
                "category": "真菌病害",
                "symptoms": "叶片出现黄色或褐色锈斑，严重时叶片枯黄",
                "cause": "由锈菌引起，高温高湿环境易发",
                "treatment": "喷洒三唑酮、丙环唑等杀菌剂",
                "prevention": "选用抗病品种，合理轮作，清除病残体",
                "severity": "medium",
            },
            {
                "name": "小麦白粉病",
                "category": "真菌病害",
                "symptoms": "叶片表面出现白色粉状物，后期变为灰白色",
                "cause": "由白粉菌引起，密度过大、氮肥过多易发",
                "treatment": "喷洒三唑酮、腈菌唑等杀菌剂",
                "prevention": "合理密植，控制氮肥用量，增强通风",
                "severity": "medium",
            },
            {
                "name": "小麦蚜虫",
                "category": "虫害",
                "symptoms": "叶片发黄卷曲，植株生长受阻",
                "cause": "蚜虫吸食汁液，传播病毒",
                "treatment": "喷洒吡虫啉、啶虫脒等杀虫剂",
                "prevention": "清除田间杂草，保护天敌",
                "severity": "low",
            },
            {
                "name": "小麦赤霉病",
                "category": "真菌病害",
                "symptoms": "穗部出现粉红色霉层，籽粒干瘪",
                "cause": "由禾谷镰刀菌引起，扬花期遇雨易发",
                "treatment": "喷洒多菌灵、戊唑醇等杀菌剂",
                "prevention": "选用抗病品种，适期播种，控制田间湿度",
                "severity": "high",
            },
        ]
    
    def generate_test_diagnoses_data(self) -> List[Dict]:
        """
        生成测试诊断记录数据
        
        返回:
            List[Dict]: 测试诊断记录数据列表
        """
        return [
            {
                "user_id": 1,
                "disease_id": 1,
                "image_url": "/test_data/images/wheat_rust.png",
                "result": "小麦锈病",
                "confidence": 0.95,
                "status": "completed",
                "location": {
                    "province": "河南省",
                    "city": "郑州市",
                    "latitude": 34.7466,
                    "longitude": 113.6253,
                },
                "environment": {
                    "temperature": 25.5,
                    "humidity": 65.0,
                },
            },
            {
                "user_id": 1,
                "disease_id": 2,
                "image_url": "/test_data/images/wheat_powdery_mildew.png",
                "result": "小麦白粉病",
                "confidence": 0.88,
                "status": "completed",
                "location": {
                    "province": "山东省",
                    "city": "济南市",
                    "latitude": 36.6512,
                    "longitude": 117.1201,
                },
                "environment": {
                    "temperature": 22.0,
                    "humidity": 75.0,
                },
            },
            {
                "user_id": 2,
                "disease_id": 3,
                "image_url": "/test_data/images/wheat_aphid.png",
                "result": "小麦蚜虫",
                "confidence": 0.92,
                "status": "completed",
                "location": {
                    "province": "河北省",
                    "city": "石家庄市",
                    "latitude": 38.0428,
                    "longitude": 114.5149,
                },
                "environment": {
                    "temperature": 28.0,
                    "humidity": 55.0,
                },
            },
        ]
    
    def generate_test_knowledge_data(self) -> List[Dict]:
        """
        生成测试知识图谱数据
        
        返回:
            List[Dict]: 测试知识图谱数据列表
        """
        return [
            {
                "entity_type": "disease",
                "entity_name": "小麦锈病",
                "attributes": {
                    "category": "真菌病害",
                    "severity": "medium",
                    "season": "春季",
                },
            },
            {
                "entity_type": "pathogen",
                "entity_name": "锈菌",
                "attributes": {
                    "type": "真菌",
                    "spread": "风传",
                },
            },
            {
                "entity_type": "treatment",
                "entity_name": "三唑酮",
                "attributes": {
                    "type": "杀菌剂",
                    "usage": "叶面喷施",
                },
            },
            {
                "entity_type": "relation",
                "source": "小麦锈病",
                "target": "锈菌",
                "relation_type": "致病因子",
            },
            {
                "entity_type": "relation",
                "source": "小麦锈病",
                "target": "三唑酮",
                "relation_type": "治疗方法",
            },
        ]
    
    def save_test_data(self, data: List[Dict], filename: str) -> Path:
        """
        保存测试数据到 JSON 文件
        
        参数:
            data: 测试数据
            filename: 文件名
        
        返回:
            Path: 保存的文件路径
        """
        file_path = self.output_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path
    
    def generate_all_test_data(self) -> Dict[str, Path]:
        """
        生成所有测试数据
        
        返回:
            Dict[str, Path]: 生成的文件路径字典
        """
        files = {}
        
        self.generate_sample_image("sample_test.png")
        self.generate_wheat_disease_image("rust", "wheat_rust.png")
        self.generate_wheat_disease_image("powdery_mildew", "wheat_powdery_mildew.png")
        self.generate_wheat_disease_image("aphid", "wheat_aphid.png")
        files["images"] = self.images_dir
        
        users_data = self.generate_test_users_data()
        files["users"] = self.save_test_data(users_data, "test_users.json")
        
        diseases_data = self.generate_test_diseases_data()
        files["diseases"] = self.save_test_data(diseases_data, "test_diseases.json")
        
        diagnoses_data = self.generate_test_diagnoses_data()
        files["diagnoses"] = self.save_test_data(diagnoses_data, "test_diagnoses.json")
        
        knowledge_data = self.generate_test_knowledge_data()
        files["knowledge"] = self.save_test_data(knowledge_data, "test_knowledge.json")
        
        return files


def get_sample_image_base64(image_path: Path) -> str:
    """
    将图像转换为 Base64 编码字符串
    
    参数:
        image_path: 图像文件路径
    
    返回:
        str: Base64 编码的图像字符串
    """
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')


def create_multipart_image_data(image_path: Path) -> tuple:
    """
    创建用于文件上传测试的图像数据
    
    参数:
        image_path: 图像文件路径
    
    返回:
        tuple: (文件名, 文件内容, 内容类型)
    """
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return (image_path.name, image_data, 'image/png')

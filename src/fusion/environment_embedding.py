# -*- coding: utf-8 -*-
"""
环境数据嵌入分支模块 (Environment Data Embedding Branch)

实现将温度、湿度、光照、地理位置等传感器数据编码为 Environment Embeddings：
1. 环境特征编码：温度、湿度、光照、地理位置等
2. 轻量级 MLP 映射到文本 Token 维度
3. 与图像/文本 Token 一起输入 Decoder
4. 模拟农业专家诊断逻辑

技术特性:
- 多类型环境数据编码
- 位置编码
- 特征融合
- 可学习的嵌入权重
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import math
import numpy as np


class TemperatureEncoder(nn.Module):
    """
    温度编码器
    
    将温度值编码为向量表示，包含：
    - 归一化温度值
    - 温度区间分类
    - 病害风险评分
    """
    
    def __init__(self, output_dim: int = 64):
        """
        初始化温度编码器
        
        :param output_dim: 输出维度
        """
        super().__init__()
        
        self.output_dim = output_dim
        
        # 温度区间定义（病害适宜温度）
        self.temp_ranges = {
            'low_risk': (-10, 5),      # 低温，病害风险低
            'moderate_risk': (5, 15),   # 中等风险
            'high_risk': (15, 25),      # 高风险（多数真菌病害适宜）
            'very_high_risk': (25, 35)  # 极高风险
        }
        
        # 嵌入层
        self.value_embed = nn.Sequential(
            nn.Linear(1, output_dim // 4),
            nn.ReLU(),
            nn.Linear(output_dim // 4, output_dim // 2)
        )
        
        # 风险编码
        self.risk_embed = nn.Embedding(4, output_dim // 4)
        
        # 最终投影
        self.proj = nn.Linear(output_dim // 2 + output_dim // 4, output_dim)
        
    def forward(self, temperature: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        :param temperature: 温度值 [batch, 1] 或 [batch]
        :return: 温度嵌入 [batch, output_dim]
        """
        if temperature.dim() == 1:
            temperature = temperature.unsqueeze(-1)
        
        # 归一化温度值
        normalized_temp = (temperature + 10) / 45  # 假设范围 [-10, 35]
        normalized_temp = torch.clamp(normalized_temp, 0, 1)
        
        # 值嵌入
        value_emb = self.value_embed(normalized_temp)
        
        # 计算风险等级
        risk_level = torch.zeros(temperature.shape[0], dtype=torch.long, device=temperature.device)
        temp_flat = temperature.squeeze(-1)
        risk_level[(temp_flat >= -10) & (temp_flat < 5)] = 0
        risk_level[(temp_flat >= 5) & (temp_flat < 15)] = 1
        risk_level[(temp_flat >= 15) & (temp_flat < 25)] = 2
        risk_level[(temp_flat >= 25) & (temp_flat <= 35)] = 3
        
        # 风险嵌入
        risk_emb = self.risk_embed(risk_level)
        
        # 合并
        combined = torch.cat([value_emb, risk_emb], dim=-1)
        output = self.proj(combined)
        
        return output


class HumidityEncoder(nn.Module):
    """
    湿度编码器
    
    将湿度值编码为向量表示
    """
    
    def __init__(self, output_dim: int = 64):
        """
        初始化湿度编码器
        
        :param output_dim: 输出维度
        """
        super().__init__()
        
        self.output_dim = output_dim
        
        # 嵌入层
        self.embed = nn.Sequential(
            nn.Linear(1, output_dim // 2),
            nn.ReLU(),
            nn.Linear(output_dim // 2, output_dim)
        )
        
        # 风险权重（高湿度增加病害风险）
        self.risk_weight = nn.Parameter(torch.tensor([1.0]))
        
    def forward(self, humidity: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        :param humidity: 湿度值 [batch, 1] 或 [batch]，范围 0-100
        :return: 湿度嵌入 [batch, output_dim]
        """
        if humidity.dim() == 1:
            humidity = humidity.unsqueeze(-1)
        
        # 归一化
        normalized = humidity / 100.0
        
        # 计算风险权重（湿度越高风险越大）
        risk_factor = torch.sigmoid(self.risk_weight) * (normalized ** 2)
        
        # 嵌入
        emb = self.embed(normalized)
        emb = emb * (1 + risk_factor)
        
        return emb


class LocationEncoder(nn.Module):
    """
    地理位置/地区编码器
    
    将地理位置信息编码为向量表示
    """
    
    def __init__(
        self,
        output_dim: int = 64,
        num_regions: int = 50,
        num_provinces: int = 34
    ):
        """
        初始化地理位置编码器
        
        :param output_dim: 输出维度
        :param num_regions: 区域数量
        :param num_provinces: 省份数量
        """
        super().__init__()
        
        self.output_dim = output_dim
        
        # 区域嵌入
        self.region_embed = nn.Embedding(num_regions, output_dim // 2)
        
        # 省份嵌入
        self.province_embed = nn.Embedding(num_provinces, output_dim // 2)
        
        # 经纬度编码
        self.coord_embed = nn.Sequential(
            nn.Linear(2, output_dim // 2),
            nn.ReLU(),
            nn.Linear(output_dim // 2, output_dim // 2)
        )
        
        # 融合层（三个嵌入，每个 output_dim // 2）
        self.fusion = nn.Linear(output_dim // 2 * 3, output_dim)
        
    def forward(
        self,
        region_id: Optional[torch.Tensor] = None,
        province_id: Optional[torch.Tensor] = None,
        coordinates: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        前向传播
        
        :param region_id: 区域ID [batch]
        :param province_id: 省份ID [batch]
        :param coordinates: 经纬度 [batch, 2]
        :return: 位置嵌入 [batch, output_dim]
        """
        batch_size = region_id.shape[0] if region_id is not None else province_id.shape[0]
        device = region_id.device if region_id is not None else province_id.device
        
        embeddings = []
        
        # 区域嵌入
        if region_id is not None:
            region_emb = self.region_embed(region_id)
            embeddings.append(region_emb)
        else:
            embeddings.append(torch.zeros(batch_size, self.output_dim // 2, device=device))
        
        # 省份嵌入
        if province_id is not None:
            province_emb = self.province_embed(province_id)
            embeddings.append(province_emb)
        else:
            embeddings.append(torch.zeros(batch_size, self.output_dim // 2, device=device))
        
        # 经纬度嵌入
        if coordinates is not None:
            coord_emb = self.coord_embed(coordinates)
            embeddings.append(coord_emb)
        else:
            embeddings.append(torch.zeros(batch_size, self.output_dim // 2, device=device))
        
        # 合并
        combined = torch.cat(embeddings, dim=-1)
        output = self.fusion(combined)
        
        return output


class GrowthStageEncoder(nn.Module):
    """
    生长阶段编码器
    
    将小麦生长阶段编码为向量表示
    """
    
    def __init__(self, output_dim: int = 64, num_stages: int = 11):
        """
        初始化生长阶段编码器
        
        :param output_dim: 输出维度
        :param num_stages: 生长阶段数量
        """
        super().__init__()
        
        self.output_dim = output_dim
        self.num_stages = num_stages
        
        # 生长阶段名称
        self.stage_names = [
            "苗期", "分蘖期", "越冬期", "返青期", "起身期",
            "拔节期", "孕穗期", "抽穗期", "开花期", "灌浆期", "成熟期"
        ]
        
        # 病害易感性权重
        self.susceptibility = torch.tensor([
            0.6, 0.7, 0.3, 0.5, 0.6, 0.8, 0.9, 1.0, 0.9, 0.8, 0.5
        ])
        
        # 阶段嵌入
        self.stage_embed = nn.Embedding(num_stages, output_dim // 2)
        
        # 易感性编码
        self.susceptibility_embed = nn.Sequential(
            nn.Linear(1, output_dim // 4),
            nn.ReLU(),
            nn.Linear(output_dim // 4, output_dim // 2)
        )
        
        # 融合层
        self.fusion = nn.Linear(output_dim, output_dim)
        
    def forward(self, stage_id: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        :param stage_id: 生长阶段ID [batch]
        :return: 生长阶段嵌入 [batch, output_dim]
        """
        # 阶段嵌入
        stage_emb = self.stage_embed(stage_id)
        
        # 易感性嵌入
        susceptibility = self.susceptibility[stage_id].unsqueeze(-1).float()
        sus_emb = self.susceptibility_embed(susceptibility)
        
        # 合并
        combined = torch.cat([stage_emb, sus_emb], dim=-1)
        output = self.fusion(combined)
        
        return output


class EnvironmentEmbeddingBranch(nn.Module):
    """
    环境数据嵌入分支
    
    将温度、湿度、光照、地理位置等传感器数据编码为 Environment Embeddings，
    通过轻量级 MLP 映射到与文本 Token 相同的维度
    """
    
    def __init__(
        self,
        output_dim: int = 768,
        hidden_dim: int = 256,
        dropout: float = 0.1
    ):
        """
        初始化环境数据嵌入分支
        
        :param output_dim: 输出维度（与文本 Token 维度相同）
        :param hidden_dim: 隐藏层维度
        :param dropout: Dropout 比率
        """
        super().__init__()
        
        self.output_dim = output_dim
        self.hidden_dim = hidden_dim
        
        # 各类环境数据编码器
        self.temp_encoder = TemperatureEncoder(output_dim=64)
        self.humidity_encoder = HumidityEncoder(output_dim=64)
        self.location_encoder = LocationEncoder(output_dim=64)
        self.growth_stage_encoder = GrowthStageEncoder(output_dim=64)
        
        # 光照编码器
        self.light_encoder = nn.Sequential(
            nn.Linear(1, 32),
            nn.ReLU(),
            nn.Linear(32, 64)
        )
        
        # 土壤湿度编码器
        self.soil_moisture_encoder = nn.Sequential(
            nn.Linear(1, 32),
            nn.ReLU(),
            nn.Linear(32, 64)
        )
        
        # 风速编码器
        self.wind_speed_encoder = nn.Sequential(
            nn.Linear(1, 32),
            nn.ReLU(),
            nn.Linear(32, 64)
        )
        
        # 融合 MLP
        self.fusion_mlp = nn.Sequential(
            nn.Linear(64 * 7, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim)
        )
        
        # 位置编码
        self.position_encoding = nn.Parameter(
            self._create_position_encoding(1, output_dim)
        )
        
        # 门控机制
        self.gate = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Sigmoid()
        )
        
    def _create_position_encoding(self, seq_len: int, dim: int) -> torch.Tensor:
        """
        创建位置编码
        
        :param seq_len: 序列长度
        :param dim: 维度
        :return: 位置编码张量
        """
        position = torch.arange(seq_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, dim, 2) * (-math.log(10000.0) / dim))
        pe = torch.zeros(1, dim)
        pe[0, 0::2] = torch.sin(position * div_term)
        pe[0, 1::2] = torch.cos(position * div_term)
        return pe
        
    def forward(
        self,
        temperature: Optional[torch.Tensor] = None,
        humidity: Optional[torch.Tensor] = None,
        region_id: Optional[torch.Tensor] = None,
        province_id: Optional[torch.Tensor] = None,
        coordinates: Optional[torch.Tensor] = None,
        growth_stage_id: Optional[torch.Tensor] = None,
        light_intensity: Optional[torch.Tensor] = None,
        soil_moisture: Optional[torch.Tensor] = None,
        wind_speed: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        前向传播
        
        :param temperature: 温度值 [batch]
        :param humidity: 湿度值 [batch]
        :param region_id: 区域ID [batch]
        :param province_id: 省份ID [batch]
        :param coordinates: 经纬度 [batch, 2]
        :param growth_stage_id: 生长阶段ID [batch]
        :param light_intensity: 光照强度 [batch]
        :param soil_moisture: 土壤湿度 [batch]
        :param wind_speed: 风速 [batch]
        :return: 环境嵌入字典
        """
        # 确定批次大小
        batch_size = temperature.shape[0] if temperature is not None else 1
        device = temperature.device if temperature is not None else torch.device('cpu')
        
        # 编码各类环境数据
        embeddings = []
        feature_names = []
        
        # 温度
        if temperature is not None:
            temp_emb = self.temp_encoder(temperature)
            embeddings.append(temp_emb)
            feature_names.append('temperature')
        else:
            embeddings.append(torch.zeros(batch_size, 64, device=device))
        
        # 湿度
        if humidity is not None:
            humidity_emb = self.humidity_encoder(humidity)
            embeddings.append(humidity_emb)
            feature_names.append('humidity')
        else:
            embeddings.append(torch.zeros(batch_size, 64, device=device))
        
        # 位置
        if region_id is not None or province_id is not None:
            location_emb = self.location_encoder(region_id, province_id, coordinates)
            embeddings.append(location_emb)
            feature_names.append('location')
        else:
            embeddings.append(torch.zeros(batch_size, 64, device=device))
        
        # 生长阶段
        if growth_stage_id is not None:
            stage_emb = self.growth_stage_encoder(growth_stage_id)
            embeddings.append(stage_emb)
            feature_names.append('growth_stage')
        else:
            embeddings.append(torch.zeros(batch_size, 64, device=device))
        
        # 光照
        if light_intensity is not None:
            if light_intensity.dim() == 1:
                light_intensity = light_intensity.unsqueeze(-1)
            light_emb = self.light_encoder(light_intensity)
            embeddings.append(light_emb)
            feature_names.append('light')
        else:
            embeddings.append(torch.zeros(batch_size, 64, device=device))
        
        # 土壤湿度
        if soil_moisture is not None:
            if soil_moisture.dim() == 1:
                soil_moisture = soil_moisture.unsqueeze(-1)
            soil_emb = self.soil_moisture_encoder(soil_moisture)
            embeddings.append(soil_emb)
            feature_names.append('soil_moisture')
        else:
            embeddings.append(torch.zeros(batch_size, 64, device=device))
        
        # 风速
        if wind_speed is not None:
            if wind_speed.dim() == 1:
                wind_speed = wind_speed.unsqueeze(-1)
            wind_emb = self.wind_speed_encoder(wind_speed)
            embeddings.append(wind_emb)
            feature_names.append('wind_speed')
        else:
            embeddings.append(torch.zeros(batch_size, 64, device=device))
        
        # 合并所有嵌入
        combined = torch.cat(embeddings, dim=-1)
        
        # MLP 映射
        env_emb = self.fusion_mlp(combined)
        
        # 添加位置编码
        env_emb = env_emb + self.position_encoding.to(env_emb.device)
        
        # 门控
        gate = self.gate(env_emb)
        env_emb = gate * env_emb
        
        return {
            'environment_embedding': env_emb,  # [batch, output_dim]
            'environment_embedding_3d': env_emb.unsqueeze(1),  # [batch, 1, output_dim]
            'feature_names': feature_names,
            'gate_values': gate,
            'raw_embeddings': embeddings
        }
    
    def get_environment_feature_vector(
        self,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        growth_stage: Optional[str] = None,
        **kwargs
    ) -> torch.Tensor:
        """
        从原始值获取环境特征向量
        
        :param temperature: 温度值
        :param humidity: 湿度值
        :param growth_stage: 生长阶段名称
        :return: 环境嵌入
        """
        # 转换为张量
        batch_size = 1
        device = next(self.parameters()).device
        
        temp_tensor = torch.tensor([temperature], device=device) if temperature is not None else None
        humidity_tensor = torch.tensor([humidity], device=device) if humidity is not None else None
        
        # 生长阶段转换
        if growth_stage is not None:
            stage_names = [
                "苗期", "分蘖期", "越冬期", "返青期", "起身期",
                "拔节期", "孕穗期", "抽穗期", "开花期", "灌浆期", "成熟期"
            ]
            stage_id = stage_names.index(growth_stage) if growth_stage in stage_names else 0
            stage_tensor = torch.tensor([stage_id], device=device)
        else:
            stage_tensor = None
        
        return self.forward(
            temperature=temp_tensor,
            humidity=humidity_tensor,
            growth_stage_id=stage_tensor
        )


def create_environment_embedding_branch(
    output_dim: int = 768,
    hidden_dim: int = 256
) -> EnvironmentEmbeddingBranch:
    """
    创建环境数据嵌入分支
    
    :param output_dim: 输出维度
    :param hidden_dim: 隐藏层维度
    :return: EnvironmentEmbeddingBranch 实例
    """
    return EnvironmentEmbeddingBranch(
        output_dim=output_dim,
        hidden_dim=hidden_dim
    )


def test_environment_embedding():
    """测试环境数据嵌入模块"""
    print("\n" + "=" * 60)
    print("环境数据嵌入分支测试")
    print("=" * 60)
    
    try:
        print("\n[测试 1] 初始化环境嵌入分支")
        env_branch = create_environment_embedding_branch(output_dim=768)
        print("[OK] 环境嵌入分支初始化成功")
        
        print("\n[测试 2] 完整环境数据编码")
        batch_size = 4
        
        result = env_branch.forward(
            temperature=torch.randn(batch_size) * 10 + 20,  # 10-30°C
            humidity=torch.rand(batch_size) * 40 + 40,       # 40-80%
            region_id=torch.randint(0, 50, (batch_size,)),
            province_id=torch.randint(0, 34, (batch_size,)),
            growth_stage_id=torch.randint(0, 11, (batch_size,)),
            light_intensity=torch.rand(batch_size) * 100,
            soil_moisture=torch.rand(batch_size) * 100,
            wind_speed=torch.rand(batch_size) * 10
        )
        
        print(f"[OK] 环境嵌入维度: {result['environment_embedding'].shape}")
        print(f"[OK] 3D嵌入维度: {result['environment_embedding_3d'].shape}")
        print(f"[OK] 特征名称: {result['feature_names']}")
        
        print("\n[测试 3] 部分环境数据编码")
        partial_result = env_branch.forward(
            temperature=torch.tensor([25.0, 15.0]),
            humidity=torch.tensor([80.0, 60.0])
        )
        print(f"[OK] 部分环境嵌入维度: {partial_result['environment_embedding'].shape}")
        
        print("\n[测试 4] 从原始值获取嵌入")
        raw_result = env_branch.get_environment_feature_vector(
            temperature=25.0,
            humidity=80.0,
            growth_stage="抽穗期"
        )
        print(f"[OK] 原始值嵌入维度: {raw_result['environment_embedding'].shape}")
        
        print("\n[OK] 所有测试通过!")
        
    except Exception as e:
        print(f"\n[错误] 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_environment_embedding()

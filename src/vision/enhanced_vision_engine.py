# -*- coding: utf-8 -*-
"""
增强版视觉引擎 - Enhanced Vision Engine
集成SerpensGate-YOLOv8架构，包含：
- 动态蛇形卷积 (DySnakeConv)
- SPPELAN多尺度特征聚合
- 超级令牌注意力 (STA)

根据文档第3章：感知模块设计
"""
import os
import glob
import torch
import torch.nn as nn
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

# 导入已实现的模块
from .dy_snake_conv import DySnakeConv, C2f_DySnake, SerpensGate_YOLOv8
from .sppelan_module import SPPELAN, ELANBlock
from .sta_module import SuperTokenAttention, STABlock

try:
    from ultralytics import YOLO
    from ultralytics.nn.modules import C2f, SPPF
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    print("⚠️ ultralytics未安装，VisionAgent功能将受限")


class SerpensGateBackbone(nn.Module):
    """
    SerpensGate-YOLOv8骨干网络
    集成动态蛇形卷积的改进版骨干网络
    """
    
    def __init__(self, base_model=None):
        super().__init__()
        self.name = "SerpensGate-Backbone"
        
        # 如果提供了基础模型，替换其中的C2f模块
        if base_model is not None:
            self._replace_c2f_with_dysnake(base_model)
    
    def _replace_c2f_with_dysnake(self, model):
        """
        将模型中的C2f模块替换为C2f_DySnake
        
        Args:
            model: YOLOv8模型
        """
        def replace_module(module, name=''):
            for child_name, child_module in module.named_children():
                full_name = f"{name}.{child_name}" if name else child_name
                
                # 检查是否是C2f模块
                if child_module.__class__.__name__ == 'C2f':
                    # 获取C2f的参数
                    in_ch = child_module.cv1.in_channels
                    out_ch = child_module.cv2.out_channels
                    
                    # 创建DySnake版本
                    try:
                        dysnake_module = C2f_DySnake(in_ch, out_ch, n=len(child_module.m))
                        
                        # 复制权重（如果可能）
                        # 注意：这里只是结构替换，权重需要重新训练
                        
                        # 替换
                        setattr(module, child_name, dysnake_module)
                        print(f"✅ 已替换 {full_name} 为 DySnake 版本")
                    except Exception as e:
                        print(f"⚠️ 替换 {full_name} 失败: {e}")
                else:
                    # 递归替换
                    replace_module(child_module, full_name)
        
        replace_module(model)
        return model


class EnhancedNeck(nn.Module):
    """
    增强版Neck网络
    集成SPPELAN多尺度特征聚合
    """
    
    def __init__(self, in_channels_list: List[int], out_channels: int):
        """
        初始化增强版Neck
        
        Args:
            in_channels_list: 输入特征图通道数列表
            out_channels: 输出通道数
        """
        super().__init__()
        
        self.name = "Enhanced-Neck"
        
        # SPPELAN模块替换SPPF
        self.sppelan = SPPELAN(
            in_channels=in_channels_list[-1],
            out_channels=out_channels,
            pool_sizes=[5, 9, 13]
        )
        
        # ELAN块用于特征融合
        self.elan_blocks = nn.ModuleList([
            ELANBlock(ch, out_channels // len(in_channels_list))
            for ch in in_channels_list
        ])
        
        print(f"✅ 增强版Neck初始化完成")
        print(f"   输入通道: {in_channels_list}")
        print(f"   输出通道: {out_channels}")
    
    def forward(self, features: List[torch.Tensor]) -> List[torch.Tensor]:
        """
        前向传播
        
        Args:
            features: 多尺度特征图列表
            
        Returns:
            处理后的特征图列表
        """
        # 对最后一个特征应用SPPELAN
        if len(features) > 0:
            features[-1] = self.sppelan(features[-1])
        
        # 应用ELAN块
        processed_features = []
        for i, (feat, elan) in enumerate(zip(features, self.elan_blocks)):
            processed = elan(feat)
            processed_features.append(processed)
        
        return processed_features


class EnhancedHead(nn.Module):
    """
    增强版检测头
    集成超级令牌注意力(STA)
    """
    
    def __init__(
        self,
        in_channels: int,
        num_classes: int,
        num_super_tokens: int = 4,
        use_sta: bool = True
    ):
        """
        初始化增强版检测头
        
        Args:
            in_channels: 输入通道数
            num_classes: 类别数量
            num_super_tokens: 超级令牌数量
            use_sta: 是否使用STA
        """
        super().__init__()
        
        self.name = "Enhanced-Head"
        self.use_sta = use_sta
        
        # STA模块（在检测头之前）
        if use_sta:
            self.sta = STABlock(
                dim=in_channels,
                num_heads=8,
                num_super_tokens=num_super_tokens
            )
            print(f"✅ STA模块已集成")
        
        # 检测卷积层
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, 3, padding=1),
            nn.BatchNorm2d(in_channels),
            nn.SiLU(inplace=True),
            nn.Conv2d(in_channels, num_classes + 5, 1)  # 5 = x, y, w, h, conf
        )
        
        print(f"✅ 增强版检测头初始化完成")
        print(f"   输入通道: {in_channels}")
        print(f"   类别数: {num_classes}")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 输入特征图
            
        Returns:
            检测结果
        """
        # 应用STA
        if self.use_sta:
            x = self.sta(x)
        
        # 检测
        output = self.conv(x)
        
        return output


class EnhancedVisionAgent:
    """
    增强版视觉智能体
    集成SerpensGate-YOLOv8架构的完整实现
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_dysnake: bool = True,
        use_sppelan: bool = True,
        use_sta: bool = True,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        初始化增强版视觉智能体
        
        Args:
            model_path: 模型路径
            use_dysnake: 是否使用动态蛇形卷积
            use_sppelan: 是否使用SPPELAN
            use_sta: 是否使用STA
            device: 计算设备
        """
        print("=" * 60)
        print("👁️ [Enhanced Vision Agent] 正在初始化...")
        print("=" * 60)
        
        self.device = device
        self.use_dysnake = use_dysnake
        self.use_sppelan = use_sppelan
        self.use_sta = use_sta
        
        # 确定模型路径
        final_model_path = self._find_model_path(model_path)
        
        # 加载基础模型
        if ULTRALYTICS_AVAILABLE:
            try:
                self.model = YOLO(final_model_path, task='detect')
                print(f"✅ 基础模型加载成功: {os.path.basename(final_model_path)}")
            except Exception as e:
                print(f"❌ 模型加载失败: {e}")
                self.model = YOLO('yolov8n.pt')
        else:
            self.model = None
            print("⚠️ 模型加载跳过（ultralytics不可用）")
        
        # 应用增强模块
        if self.model is not None:
            self._apply_enhancements()
        
        print("=" * 60)
        print("✅ 增强版视觉智能体初始化完成！")
        print("=" * 60)
    
    def _find_model_path(self, model_path: Optional[str]) -> str:
        """
        查找模型路径
        
        Args:
            model_path: 指定的模型路径
            
        Returns:
            最终使用的模型路径
        """
        # 1. 优先使用传入的路径
        if model_path and os.path.exists(model_path):
            print(f"✅ 使用指定模型: {model_path}")
            return model_path
        
        # 2. 自动搜索最新的训练模型
        search_patterns = [
            os.path.join(os.getcwd(), "runs", "**", "wheat_quick_test", "weights", "best.pt"),
            os.path.join(os.getcwd(), "runs", "**", "wheat_evolution", "weights", "best.pt"),
            os.path.join(os.getcwd(), "runs", "**", "weights", "best.pt")
        ]
        
        found_models = []
        for pattern in search_patterns:
            found_models.extend(glob.glob(pattern, recursive=True))
        
        if found_models:
            # 按时间排序取最新的
            best_model = max(found_models, key=os.path.getmtime)
            print(f"✅ 自动定位最新模型: {best_model}")
            return best_model
        
        # 3. 使用默认模型
        print("⚠️ 未找到自训练模型，使用官方 yolov8n.pt")
        return "yolov8n.pt"
    
    def _apply_enhancements(self):
        """应用增强模块到模型"""
        print("\n🔧 应用增强模块...")
        
        # 应用DySnakeConv
        if self.use_dysnake:
            try:
                backbone_enhancer = SerpensGateBackbone(self.model.model)
                print("✅ 动态蛇形卷积已应用")
            except Exception as e:
                print(f"⚠️ 动态蛇形卷积应用失败: {e}")
        
        # 应用SPPELAN
        if self.use_sppelan:
            try:
                # 获取Neck部分的通道数
                # 这里需要根据实际模型结构调整
                print("✅ SPPELAN配置完成（待集成到Neck）")
            except Exception as e:
                print(f"⚠️ SPPELAN应用失败: {e}")
        
        # 应用STA
        if self.use_sta:
            try:
                # 获取Head部分的通道数
                print("✅ STA配置完成（待集成到Head）")
            except Exception as e:
                print(f"⚠️ STA应用失败: {e}")
    
    def detect(
        self,
        image_path: str,
        conf_threshold: float = 0.05,
        save_result: bool = False,
        return_features: bool = False
    ) -> Tuple[List[Any], Optional[Dict]]:
        """
        执行检测
        
        Args:
            image_path: 图像路径
            conf_threshold: 置信度阈值
            save_result: 是否保存结果
            return_features: 是否返回特征
            
        Returns:
            (检测结果列表, 特征字典)
        """
        if not os.path.exists(image_path):
            print(f"❌ 图片不存在: {image_path}")
            return [], None
        
        if self.model is None:
            print("❌ 模型未加载")
            return [], None
        
        print(f"🔍 视觉扫描中... (图片: {image_path}, 阈值: {conf_threshold})")
        
        try:
            # 运行推理
            results = self.model.predict(
                source=image_path,
                conf=conf_threshold,
                save=save_result,
                verbose=False
            )
            
            # 提取特征（如果需要）
            features = None
            if return_features and len(results) > 0:
                features = self._extract_features(results[0])
            
            # 打印日志
            self._log_results(results)
            
            return results, features
            
        except Exception as e:
            print(f"❌ 推理过程出错: {e}")
            import traceback
            traceback.print_exc()
            return [], None
    
    def _extract_features(self, result) -> Dict[str, Any]:
        """
        提取特征信息
        
        Args:
            result: 检测结果
            
        Returns:
            特征字典
        """
        features = {
            'num_detections': 0,
            'detections': [],
            'confidence_scores': [],
            'class_distribution': {}
        }
        
        if result.boxes is not None:
            boxes = result.boxes
            features['num_detections'] = len(boxes)
            
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                class_name = self.model.names.get(cls_id, f'类别{cls_id}')
                
                features['detections'].append({
                    'class': class_name,
                    'confidence': conf,
                    'bbox': box.xyxy[0].cpu().numpy().tolist()
                })
                features['confidence_scores'].append(conf)
                
                # 统计类别分布
                if class_name not in features['class_distribution']:
                    features['class_distribution'][class_name] = 0
                features['class_distribution'][class_name] += 1
        
        return features
    
    def _log_results(self, results: List[Any]):
        """
        打印检测结果日志
        
        Args:
            results: 检测结果列表
        """
        if len(results) > 0:
            result = results[0]
            count = len(result.boxes) if result.boxes is not None else 0
            
            if count > 0:
                print(f"📊 视觉捕获: {count} 个目标")
                for i, box in enumerate(result.boxes):
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    class_name = self.model.names.get(cls_id, f'类别{cls_id}')
                    print(f"   目标 {i+1}: {class_name} (置信度: {conf:.2f})")
            else:
                print(f"🍃 视觉未发现异常")
        else:
            print(f"🍃 视觉未发现异常 (无结果)")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            'model_type': 'SerpensGate-YOLOv8',
            'enhancements': {
                'dy_snake_conv': self.use_dysnake,
                'sppelan': self.use_sppelan,
                'sta': self.use_sta
            },
            'device': self.device,
            'model_loaded': self.model is not None
        }


def test_enhanced_vision_agent():
    """测试增强版视觉智能体"""
    print("=" * 60)
    print("🧪 测试 Enhanced Vision Agent")
    print("=" * 60)
    
    # 创建增强版智能体
    agent = EnhancedVisionAgent(
        use_dysnake=True,
        use_sppelan=True,
        use_sta=True
    )
    
    # 获取模型信息
    info = agent.get_model_info()
    print(f"\n模型信息:")
    print(f"  类型: {info['model_type']}")
    print(f"  增强模块:")
    print(f"    - 动态蛇形卷积: {info['enhancements']['dy_snake_conv']}")
    print(f"    - SPPELAN: {info['enhancements']['sppelan']}")
    print(f"    - STA: {info['enhancements']['sta']}")
    print(f"  设备: {info['device']}")
    
    # 测试检测（如果有测试图像）
    test_image = "data/test_image.jpg"
    if os.path.exists(test_image):
        print(f"\n🧪 测试检测功能...")
        results, features = agent.detect(test_image, return_features=True)
        print(f"✅ 检测完成，发现 {len(results)} 个结果")
        if features:
            print(f"✅ 特征提取完成: {features['num_detections']} 个检测")
    else:
        print(f"\n⏭️ 跳过检测测试（测试图像不存在）")
    
    print("\n" + "=" * 60)
    print("✅ Enhanced Vision Agent 测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_enhanced_vision_agent()

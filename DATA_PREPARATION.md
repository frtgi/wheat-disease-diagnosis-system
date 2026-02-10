# 📊 IWDDA 数据准备指南

本文档详细说明如何准备和组织小麦病害诊断所需的数据集。

## 📋 目录

- [数据集概述](#数据集概述)
- [数据集结构](#数据集结构)
- [数据收集](#数据收集)
- [数据标注](#数据标注)
- [数据增强](#数据增强)
- [数据验证](#数据验证)
- [反馈数据管理](#反馈数据管理)

---

## 🎯 数据集概述

### 支持的病害类别

IWDDA 支持 17 类小麦病害和虫害的诊断：

| ID | 中文名称 | 英文名称 | 类型 | 特征描述 |
|----|---------|---------|------|---------|
| 0 | 蚜虫 | Aphids | 昆虫 | 黑色或绿色小虫，分泌蜜露 |
| 1 | 螨虫 | Mites | 昆虫 | 叶片卷曲发黄，植株矮小 |
| 2 | 茎蝇 | Stem Fly | 昆虫 | 茎秆有蛀孔，植株枯萎 |
| 3 | 锈病 | Rust | 真菌 | 叶片上有黄色或红褐色粉末孢子堆 |
| 4 | 茎锈病 | Stem Rust | 真菌 | 茎秆上有红褐色锈斑 |
| 5 | 叶锈病 | Leaf Rust | 真菌 | 叶片上有红褐色粉末状斑点 |
| 6 | 条锈病 | Stripe Rust | 真菌 | 叶片上有黄色条纹状锈斑 |
| 7 | 黑粉病 | Smuts | 真菌 | 穗部变成黑粉 |
| 8 | 根腐病 | Common Root Rot | 真菌 | 根部腐烂变黑 |
| 9 | 叶斑病 | Spot Blotch | 真菌 | 褐色病斑 |
| 10 | 小麦爆发病 | Wheat Blast | 真菌 | 穗部枯萎，有灰色霉层 |
| 11 | 赤霉病 | Fusarium Head Blight | 真菌 | 穗部枯白，粉红色霉层 |
| 12 | 壳针孢叶斑病 | Septoria Leaf Blotch | 真菌 | 叶片上有褐色小斑点 |
| 13 | 斑点叶斑病 | Speckled Leaf Blotch | 真菌 | 叶片上有不规则斑点 |
| 14 | 褐斑病 | Brown Spot | 真菌 | 叶片上有褐色圆形病斑 |
| 15 | 白粉病 | Powdery Mildew | 真菌 | 白色绒毛状霉层 |
| 16 | 健康 | Healthy | 正常 | 植株生长正常，无病害症状 |

### 数据分层架构

IWDDA 采用三层数据架构，服务于不同的训练阶段：

| 层级 | 数据内容 | 目标模块 | 数据来源 |
|------|---------|---------|---------|
| L1: 基础感知层 | 图像 + 基础类别标签 | YOLOv8 检测头、CLIP 视觉编码器 | PlantVillage, LWDCD2020 |
| L2: 任务量化层 | 图像 + 细粒度标注（边界框、严重度） | YOLOv8 定位回归、病害程度量化 | PlantDoc, WisWheat |
| L3: 决策认知层 | 图像 + 复杂文本描述（成因、防治） | LLaVA 指令微调、Neo4j 图谱构建 | AgroInstruct, 农业技术推广公报 |

---

## 📁 数据集结构

### 标准目录结构

```
datasets/wheat_data/
├── images/                      # 图像目录
│   ├── train/                   # 训练集图像
│   │   ├── aphid_0.jpg
│   │   ├── aphid_1.jpg
│   │   ├── mildew_0.jpg
│   │   └── ...
│   └── val/                     # 验证集图像
│       ├── aphid_0.jpg
│       ├── mildew_0.jpg
│       └── ...
├── labels/                      # 标签目录
│   ├── train/                   # 训练集标签
│   │   ├── aphid_0.txt
│   │   ├── aphid_1.txt
│   │   ├── mildew_0.txt
│   │   └── ...
│   └── val/                     # 验证集标签
│       ├── aphid_0.txt
│       ├── mildew_0.txt
│       └── ...
└── classes.txt                  # 类别名称文件
```

### 标签文件格式 (YOLO 格式)

每个 `.txt` 文件对应一张图片，每行一个目标：

```
<class_id> <x_center> <y_center> <width> <height>
```

**参数说明**：
- `class_id`: 类别 ID (0-16)
- `x_center`: 目标中心点 x 坐标（归一化，0-1）
- `y_center`: 目标中心点 y 坐标（归一化，0-1）
- `width`: 目标宽度（归一化，0-1）
- `height`: 目标高度（归一化，0-1）

**示例**：

```
6 0.5 0.5 0.9 0.9
```

表示：
- 类别 6（条锈病）
- 中心在图像中心 (0.5, 0.5)
- 宽度为图像宽度的 90%
- 高度为图像高度的 90%

### 多目标标注

如果一张图片有多个目标，每行一个：

```
6 0.3 0.4 0.2 0.3
15 0.7 0.6 0.15 0.2
16 0.5 0.8 0.1 0.1
```

---

## 📥 数据收集

### 公开数据集

#### 1. PlantVillage

**来源**: [PlantVillage Dataset](https://github.com/ipazc/PlantVillage)

**包含类别**:
- 小麦健康叶片
- 小麦锈病
- 小麦叶锈病

**下载方式**:
```bash
# 克隆仓库
git clone https://github.com/ipazc/PlantVillage.git

# 复制小麦相关图像
cp PlantVillage/dataset/color/Wheat_* datasets/wheat_data/images/train/
```

#### 2. LWDCD2020

**来源**: Leaf Wheat Disease Classification Dataset

**包含类别**:
- 条锈病
- 叶锈病
- 白粉病
- 健康

**下载方式**:
```bash
# 从 Kaggle 下载
kaggle datasets download -d leaf-wheat-disease-classification

# 解压并整理
unzip leaf-wheat-disease-classification.zip
```

#### 3. PlantDoc

**来源**: [PlantDoc Dataset](https://github.com/pratikbaruwa/PlantDoc)

**包含类别**:
- 多种作物病害（包括小麦）

**特点**:
- 包含边界框标注
- 适合目标检测任务

### 自定义数据收集

#### 1. 田间拍摄

**设备要求**:
- 相机：至少 1200万像素
- 光线：自然光或补光灯
- 背景：尽量单一，减少干扰

**拍摄技巧**:
- **角度**：正面拍摄，避免倾斜
- **距离**：距离目标 20-50cm
- **焦点**：确保病灶清晰对焦
- **光照**：避免强光直射和阴影

**命名规范**:
```
{类别}_{序号}.jpg
```

示例：
```
条锈病_001.jpg
白粉病_002.jpg
蚜虫_003.jpg
```

#### 2. 网络爬取

**注意事项**:
- 遵守网站版权政策
- 避免重复图像
- 确保图像质量

**工具推荐**:
- Python: `requests`, `BeautifulSoup`
- 专业工具: `Scrapy`

```python
import requests
from bs4 import BeautifulSoup

def download_images(url, save_dir):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    for img in soup.find_all('img'):
        img_url = img.get('src')
        # 下载并保存图像
        ...
```

---

## 🏷️ 数据标注

### 标注工具推荐

#### 1. LabelImg

**特点**:
- 轻量级，易于使用
- 支持 YOLO 格式
- 跨平台（Windows/Linux/macOS）

**安装**:
```bash
pip install labelImg
```

**使用**:
```bash
labelImg datasets/wheat_data/images/train datasets/wheat_data/labels/train
```

**快捷键**:
- `w`: 创建矩形框
- `d`: 下一张图片
- `a`: 上一张图片
- `Ctrl+s`: 保存

#### 2. CVAT

**特点**:
- 功能强大，支持团队协作
- 支持多种标注格式
- Web 界面

**部署**:
```bash
docker run -it -p 8080:8080 -v /data:/data cvat/cvat
```

#### 3. Roboflow

**特点**:
- 在线标注平台
- 自动标注辅助
- 数据增强功能

**访问**: [https://roboflow.com/](https://roboflow.com/)

### 标注流程

#### 1. 准备工作

```bash
# 创建标注目录
mkdir -p datasets/wheat_data/labels/train
mkdir -p datasets/wheat_data/labels/val

# 启动标注工具
labelImg datasets/wheat_data/images/train datasets/wheat_data/labels/train --classes classes.txt
```

#### 2. 标注步骤

1. **打开图像**
   - 选择要标注的图像
   - 观察病灶位置和特征

2. **绘制边界框**
   - 按 `w` 键
   - 围绕病灶绘制矩形框
   - 确保框尽量紧贴病灶

3. **选择类别**
   - 从类别列表中选择正确的病害类别
   - 确认类别 ID 正确

4. **保存标注**
   - 按 `Ctrl+s` 保存
   - 自动生成对应的 `.txt` 文件

5. **继续下一张**
   - 按 `d` 键进入下一张图像

#### 3. 质量检查

**检查项**:
- [ ] 边界框是否紧贴病灶
- [ ] 类别是否正确
- [ ] 是否有遗漏的病灶
- [ ] 是否有误标（背景噪声）

**批量检查脚本**:

```python
import os
from pathlib import Path

def check_labels(image_dir, label_dir):
    img_files = list(Path(image_dir).glob('*.jpg'))
    
    for img_file in img_files:
        label_file = Path(label_dir) / (img_file.stem + '.txt')
        
        if not label_file.exists():
            print(f"❌ 缺少标签: {img_file.name}")
        else:
            with open(label_file, 'r') as f:
                lines = f.readlines()
                if len(lines) == 0:
                    print(f"⚠️ 空标签: {img_file.name}")

check_labels('datasets/wheat_data/images/train', 
            'datasets/wheat_data/labels/train')
```

---

## 🎨 数据增强

### 为什么需要数据增强？

小麦病害在田间呈现出极高的形态多样性：
- **条锈病**：早期点状褪绿 → 中期黄色条纹 → 晚期叶片枯死
- **白粉病**：初期白色粉点 → 中期绒毛状霉层 → 晚期黑色小点
- **环境因素**：光照、天气、拍摄角度、背景等

### YOLOv8 内置增强

YOLOv8 训练时自动应用以下增强：

| 增强类型 | 参数 | 说明 |
|---------|------|------|
| Mosaic | 1.0 | 4张图像拼接 |
| Mixup | 0.0 | 图像混合 |
| 翻转 | 0.5 | 水平翻转概率 |
| HSV | 0.015 | 色调、饱和度、亮度调整 |
| 旋转 | 0.0 | 旋转角度 |
| 缩放 | 0.5 | 缩放范围 |
| 剪切 | 0.0 | 随机剪切 |

### 自定义增强策略

#### 1. 形态学增强

针对条锈病和叶锈病病斑细小的特点：

```python
import albumentations as A

transform = A.Compose([
    A.Mosaic(p=1.0),           # 马赛克拼接
    A.Mixup(p=0.5),             # 图像混合
    A.RandomRotate90(p=0.5),     # 随机旋转90度
])
```

**效果**:
- 模拟田间复杂的重叠遮挡情况
- 提高模型对密集种植环境的适应性

#### 2. 环境模拟增强

模拟不同天气和光照条件：

```python
transform = A.Compose([
    A.RandomBrightnessContrast(p=0.5),  # 亮度对比度
    A.HueSaturationValue(p=0.5),      # HSV调整
    A.RandomFog(p=0.3),                # 雾天模拟
    A.RandomRain(p=0.3),               # 雨天模拟
])
```

**效果**:
- 提高模型对光照变化的鲁棒性
- 模拟清晨露水导致的病斑反光

#### 3. 生成式合成

对于样本稀缺的病害（如小麦矮腥黑穗病），使用生成模型：

```python
from diffusers import StableDiffusionPipeline

pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")

prompt = "小麦叶片上覆盖白色粉状霉层，伴有黑色小点，白粉病晚期"
image = pipe(prompt).images[0]
image.save("synthetic_powdery_mildew.jpg")
```

**效果**:
- 扩充数据量
- 填补长尾分布中的样本空白

---

## ✅ 数据验证

### 数据集完整性检查

```python
def validate_dataset(data_root):
    """
    验证数据集完整性
    """
    img_train = list(Path(f"{data_root}/images/train").glob('*.jpg'))
    lbl_train = list(Path(f"{data_root}/labels/train").glob('*.txt'))
    
    img_val = list(Path(f"{data_root}/images/val").glob('*.jpg'))
    lbl_val = list(Path(f"{data_root}/labels/val").glob('*.txt'))
    
    print("=" * 50)
    print("数据集验证报告")
    print("=" * 50)
    print(f"训练集图像数量: {len(img_train)}")
    print(f"训练集标签数量: {len(lbl_train)}")
    print(f"验证集图像数量: {len(img_val)}")
    print(f"验证集标签数量: {len(lbl_val)}")
    print()
    
    # 检查一一对应
    train_match = len(img_train) == len(lbl_train)
    val_match = len(img_val) == len(lbl_val)
    
    print(f"训练集完整性: {'✅' if train_match else '❌'}")
    print(f"验证集完整性: {'✅' if val_match else '❌'}")
    
    if not train_match or not val_match:
        print("\n⚠️ 发现不匹配的文件！")
        
        # 找出缺失的标签
        img_names = {f.stem for f in img_train}
        lbl_names = {f.stem for f in lbl_train}
        
        missing_labels = img_names - lbl_names
        if missing_labels:
            print(f"缺失标签的图像: {len(missing_labels)} 个")
            for name in list(missing_labels)[:5]:
                print(f"  - {name}.jpg")

validate_dataset('datasets/wheat_data')
```

### 标签格式验证

```python
def validate_labels(label_dir):
    """
    验证标签文件格式
    """
    label_files = list(Path(label_dir).glob('*.txt'))
    
    errors = []
    for label_file in label_files:
        with open(label_file, 'r') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            parts = line.strip().split()
            
            # 检查字段数量
            if len(parts) != 5:
                errors.append(f"{label_file.name}:{line_num} - 字段数量错误")
                continue
            
            # 检查数值范围
            class_id = int(parts[0])
            x, y, w, h = map(float, parts[1:])
            
            if class_id < 0 or class_id > 16:
                errors.append(f"{label_file.name}:{line_num} - 类别ID超出范围")
            
            if not (0 <= x <= 1 and 0 <= y <= 1):
                errors.append(f"{label_file.name}:{line_num} - 坐标超出范围")
            
            if not (0 < w <= 1 and 0 < h <= 1):
                errors.append(f"{label_file.name}:{line_num} - 宽高超出范围")
    
    if errors:
        print(f"❌ 发现 {len(errors)} 个错误:")
        for error in errors[:10]:
            print(f"  {error}")
    else:
        print("✅ 所有标签格式正确")

validate_labels('datasets/wheat_data/labels/train')
```

### 类别分布统计

```python
def analyze_class_distribution(label_dir):
    """
    分析类别分布
    """
    label_files = list(Path(label_dir).glob('*.txt'))
    
    class_counts = [0] * 17
    
    for label_file in label_files:
        with open(label_file, 'r') as f:
            for line in f:
                class_id = int(line.split()[0])
                class_counts[class_id] += 1
    
    print("\n类别分布:")
    print("-" * 40)
    for class_id, count in enumerate(class_counts):
        if count > 0:
            print(f"类别 {class_id:2d}: {count:6d} 个目标")
    
    print("-" * 40)
    print(f"总计: {sum(class_counts)} 个目标")

analyze_class_distribution('datasets/wheat_data/labels/train')
```

---

## 🔄 反馈数据管理

### 反馈数据收集

当用户对系统诊断结果进行反馈时，数据会自动保存到 `datasets/feedback_data/` 目录。

### 反馈数据结构

```
datasets/feedback_data/
├── 条锈病/
│   ├── 20240110_143022_confirmed_条锈病.jpg
│   ├── 20240110_143523_err_白粉病_corr_条锈病.jpg
│   └── feedback_log.txt
├── 赤霉病/
│   └── ...
└── archived/  # 已处理的反馈数据
    ├── 条锈病/
    └── ...
```

### 反馈日志格式

```
[20240110_143022] Image: 20240110_143022_confirmed_条锈病.jpg | System: 条锈病 | Final: 条锈病 | Comment: 诊断正确
[20240110_143523] Image: 20240110_143523_err_白粉病_corr_条锈病.jpg | System: 白粉病 | Final: 条锈病 | Comment: 实际是条锈病，白粉病误判
```

### 反馈数据处理

系统会定期（或手动触发）处理反馈数据：

```python
from src.action.evolve import EvolutionEngine

engine = EvolutionEngine()
processed_count = engine.digest_feedback()
print(f"处理了 {processed_count} 个反馈样本")
```

**处理流程**:
1. 扫描反馈数据池
2. 将图像移动到训练集 `images/train/`
3. 生成 YOLO 格式标签（默认中心框）
4. 归档到 `archived/` 目录

### 弱监督标签优化

自动生成的标签是弱监督的（默认中心框），建议进行人工优化：

1. **使用 LabelImg 打开反馈图像**
```bash
labelImg datasets/wheat_data/images/train datasets/wheat_data/labels/train
```

2. **调整边界框**
   - 将默认的中心框调整为实际病灶位置
   - 确保框紧贴病灶

3. **保存优化后的标签**

---

## 📚 数据集推荐

### 最小数据集

| 类别 | 训练集 | 验证集 | 总计 |
|------|---------|---------|------|
| 每类 | 50 张 | 10 张 | 60 张 |
| 17 类 | 850 张 | 170 张 | 1020 张 |

**适用场景**: 快速原型开发、概念验证

### 推荐数据集

| 类别 | 训练集 | 验证集 | 总计 |
|------|---------|---------|------|
| 每类 | 200 张 | 50 张 | 250 张 |
| 17 类 | 3400 张 | 850 张 | 4250 张 |

**适用场景**: 正常训练、良好性能

### 理想数据集

| 类别 | 训练集 | 验证集 | 总计 |
|------|---------|---------|------|
| 每类 | 500 张 | 100 张 | 600 张 |
| 17 类 | 8500 张 | 1700 张 | 10200 张 |

**适用场景**: 生产环境、高精度要求

---

## 🔧 数据集配置

### 更新配置文件

编辑 `configs/wheat_disease.yaml`:

```yaml
# 数据集根目录
path: ../datasets/wheat_data

# 训练和验证集路径
train: images/train
val: images/val

# 类别数量
nc: 17

# 类别名称
names:
  0: 蚜虫 (Aphids)
  1: 螨虫 (Mites)
  2: 茎蝇 (Stem Fly)
  3: 锈病 (Rust)
  4: 茎锈病 (Stem Rust)
  5: 叶锈病 (Leaf Rust)
  6: 条锈病 (Stripe Rust)
  7: 黑粉病 (Smuts)
  8: 根腐病 (Common Root Rot)
  9: 叶斑病 (Spot Blotch)
  10: 小麦爆发病 (Wheat Blast)
  11: 赤霉病 (Fusarium Head Blight)
  12: 壳针孢叶斑病 (Septoria Leaf Blotch)
  13: 斑点叶斑病 (Speckled Leaf Blotch)
  14: 褐斑病 (Brown Spot)
  15: 白粉病 (Powdery Mildew)
  16: 健康 (Healthy)
```

### 验证配置

```python
import yaml

with open('configs/wheat_disease.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print(f"数据集路径: {config['path']}")
print(f"训练集: {config['train']}")
print(f"验证集: {config['val']}")
print(f"类别数量: {config['nc']}")
print(f"类别名称: {len(config['names'])} 个")
```

---

## 📞 常见问题

### Q1: 图像分辨率有要求吗？

**A**: 推荐使用 512x512 或 640x640 像素的图像。YOLOv8 会自动调整输入尺寸，但统一分辨率有助于训练稳定性。

### Q2: 标注文件必须与图像同名吗？

**A**: 是的。例如 `aphid_0.jpg` 对应的标签文件必须是 `aphid_0.txt`，文件扩展名除外。

### Q3: 如何处理多类别的图像？

**A**: 在标签文件中每行标注一个目标。例如：
```
6 0.3 0.4 0.2 0.3
15 0.7 0.6 0.15 0.2
```

### Q4: 数据集不平衡怎么办？

**A**: 可以通过以下方式解决：
1. 数据增强：对少数类进行更多增强
2. 过采样：复制少数类样本
3. 调整损失权重：给少数类更高的权重

### Q5: 如何验证标注质量？

**A**: 使用可视化工具检查标注：
```python
from ultralytics import YOLO
import cv2

model = YOLO('yolov8n.pt')
results = model.predict('datasets/wheat_data/images/train/aphid_0.jpg')
results[0].show()  # 显示标注结果
```

---

<div align="center">

**数据准备完成后，请阅读 [训练指南](TRAINING.md) 开始模型训练！**

</div>

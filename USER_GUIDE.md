# 🎉 IWDDA 系统使用指南

## 📋 目录

- [快速开始](#快速开始)
- [训练模型](#训练模型)
- [使用 Web 界面](#使用-web-界面)
- [命令行使用](#命令行使用)
- [故障排查](#故障排查)

---

## 🚀 快速开始

### 1. 启动 Web 界面

```bash
# 启动 Gradio Web 服务
python app.py
```

访问：**http://localhost:7860**

### 2. 训练模型（解决"未知"诊断问题）

```bash
# 基础训练（50 轮，预计 2-4 小时）
python src/vision/train_improved.py --epochs 50

# LoRA 微调（10 轮，预计 30 分钟）
python src/vision/train_improved.py --lora --epochs 10
```

### 3. 验证 Neo4j 连接

```bash
# 测试 Neo4j 连接
python test_neo4j.py
```

---

## 🎓 训练模型

### 训练参数说明

| 参数 | 默认值 | 说明 | 推荐范围 |
|------|---------|------|---------|
| --epochs | 50 | 训练轮数 | 50-200 |
| --batch | 16 | 批次大小 | 8-32 |
| --imgsz | 512 | 输入图像尺寸 | 416-640 |
| --device | auto | 训练设备 | cuda, cpu, mps |
| --lora | False | 是否使用 LoRA 微调 | - |
| --rank | 16 | LoRA 秩 | 8-32 |

### 训练命令示例

#### 1. 基础训练（推荐首次使用）

```bash
# 使用默认参数训练 50 轮
python src/vision/train_improved.py --epochs 50

# 自定义批次大小（如果显存不足）
python src/vision/train_improved.py --epochs 50 --batch 8

# 使用 CPU 训练（不推荐，速度很慢）
python src/vision/train_improved.py --epochs 50 --device cpu
```

#### 2. LoRA 微调（快速适配）

```bash
# LoRA 微调 10 轮
python src/vision/train_improved.py --lora --epochs 10

# 自定义 LoRA 秩
python src/vision/train_improved.py --lora --epochs 10 --rank 8
```

#### 3. 长时间训练（高精度）

```bash
# 训练 100 轮
python src/vision/train_improved.py --epochs 100 --batch 16

# 使用更大的图像尺寸
python src/vision/train_improved.py --epochs 100 --imgsz 640
```

### 训练监控

训练过程中，YOLOv8 会自动生成以下内容：

1. **TensorBoard 日志**
```bash
# 启动 TensorBoard
tensorboard --logdir runs/detect/runs/train/wheat_evolution_v2

# 浏览器访问
# http://localhost:6006
```

2. **训练进度**
```
Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
  1/50      2.38G      1.234      0.567      0.891        256         512
  2/50      2.41G      1.123      0.534      0.823        256         512
  ...
```

3. **验证指标**
```
      Class     Images  Instances      Box(P          R      mAP50  mAP50-95
        all       1000       5000      0.923      0.876      0.912      0.856
```

### 训练完成后

训练完成后，模型会保存在：
```
runs/detect/runs/train/wheat_evolution_v2/weights/
├── best.pt      # 最佳模型（用于推理）
└── last.pt      # 最后模型
```

系统会自动使用 `best.pt` 进行推理。

---

## 🌐 使用 Web 界面

### 访问地址

**主界面**：http://localhost:7860

### 功能模块

#### 1. 智能诊断

**步骤**：
1. 点击"智能诊断"标签页
2. 上传小麦叶片/麦穗图像
3. 输入症状描述（可选）
4. 点击"开始会诊"按钮
5. 查看诊断结果和防治建议

**输入**：
- **图像**：支持的格式包括 JPG、PNG、JPEG
- **症状描述**：例如"叶片上有黄色条纹"、"穗部漂白"等

**输出**：
- **病灶定位图**：标注检测框的可视化图像
- **诊断报告**：
  - 诊断结果：病害名称
  - 置信度：0-100%
  - 推理过程：详细的推理步骤
  - 治疗建议：具体的防治措施
  - 扩展建议：预防措施和环境诱因

#### 2. 专家咨询

**步骤**：
1. 点击"专家咨询"标签页
2. 在输入框中输入问题
3. 查看基于知识图谱的专业回答

**示例问题**：
- "赤霉病怎么预防？"
- "条锈病的成因是什么？"
- "白粉病用什么药？"
- "蚜虫如何防治？"

**输出**：
- 基于知识图谱的专业回答
- 包含病害成因、预防措施、治疗药剂等

#### 3. 系统管理

**显示内容**：
- 模型版本信息
- 数据集统计
- 反馈数据统计

---

## 💻 命令行使用

### Python API 使用

```python
from main import WheatDoctor

# 初始化诊断系统
doctor = WheatDoctor()

# 执行诊断
result = doctor.run_diagnosis(
    image_path="datasets/wheat_data/images/train/Yellow Rust/yellow_rust_0.png",
    user_text="叶片上有黄色条纹状锈斑"
)

# 查看结果
print(f"诊断结果: {result['final_report']['diagnosis']}")
print(f"置信度: {result['final_report']['confidence']:.2f}")
print(f"推理过程: {result['final_report']['reasoning']}")
print(f"治疗建议: {result['final_report']['treatment']}")

# 保存结果图像
from PIL import Image
Image.fromarray(result['plotted_image']).save('result.jpg')
print("结果图像已保存: result.jpg")

# 关闭系统
doctor.close()
```

### 批量诊断

```python
import os
from pathlib import Path
from main import WheatDoctor

def batch_diagnosis(image_dir, output_csv="results.csv"):
    """
    批量诊断图像目录中的所有图像
    """
    # 初始化系统
    doctor = WheatDoctor()
    
    # 获取所有图像
    image_files = list(Path(image_dir).glob('*.jpg')) + \
                  list(Path(image_dir).glob('*.png'))
    
    results_list = []
    
    print(f"找到 {len(image_files)} 张图像，开始批量诊断...")
    
    for i, image_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] 处理: {image_path.name}")
        
        try:
            # 执行诊断
            result = doctor.run_diagnosis(
                image_path=str(image_path),
                user_text=""
            )
            
            # 保存结果
            results_list.append({
                'filename': image_path.name,
                'diagnosis': result['final_report']['diagnosis'],
                'confidence': result['final_report']['confidence'],
                'vision_label': result['vision_data']['label'],
                'vision_conf': result['vision_data']['conf'],
                'text_label': result['text_data']['label'],
                'text_conf': result['text_data']['conf'],
                'treatment': result['final_report']['treatment']
            })
            
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            results_list.append({
                'filename': image_path.name,
                'diagnosis': 'ERROR',
                'error': str(e)
            })
    
    # 保存到 CSV
    import pandas as pd
    df = pd.DataFrame(results_list)
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\n✅ 结果已保存到: {output_csv}")
    
    # 关闭系统
    doctor.close()

if __name__ == "__main__":
    batch_diagnosis("datasets/wheat_data/images/train", "diagnosis_results.csv")
```

---

## 🔧 故障排查

### 问题 1: 训练时显存不足 (OOM)

**症状**：
```
RuntimeError: CUDA out of memory
```

**解决方案**：

1. **减小批次大小**
```bash
python src/vision/train_improved.py --epochs 50 --batch 8
```

2. **减小图像尺寸**
```bash
python src/vision/train_improved.py --epochs 50 --imgsz 416
```

3. **使用 CPU 训练**
```bash
python src/vision/train_improved.py --epochs 50 --device cpu
```

### 问题 2: 诊断结果总是"未知"

**症状**：
```
诊断结论：【未知】
置信度: 0.00
```

**解决方案**：

1. **训练模型**
```bash
# 训练 50 轮
python src/vision/train_improved.py --epochs 50
```

2. **检查图像质量**
- 确保图像清晰
- 病灶区域明显
- 光照条件良好

3. **检查数据集**
```bash
# 验证数据集完整性
python check_dataset.py
```

### 问题 3: Neo4j 连接失败

**症状**：
```
neo4j.exceptions.ServiceUnavailable: Unable to connect to neo4j at bolt://localhost:7687
```

**解决方案**：

1. **启动 Neo4j 服务**
```bash
# 使用 Docker 启动
docker run -d \
  --name wheat-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/123456789s \
  neo4j:5.15
```

2. **验证连接**
```bash
# 测试连接
python test_neo4j.py
```

3. **访问 Neo4j 浏览器界面**
- 地址：http://localhost:7474
- 用户名：neo4j
- 密码：123456789s

### 问题 4: Web 界面无法访问

**症状**：
```
OSError: [Errno 48] Address already in use
```

**解决方案**：

1. **检查端口占用**
```bash
# Windows
netstat -ano | findstr :7860

# 或使用其他端口
python app.py --port 8080
```

2. **重启 Web 服务**
```bash
# 停止当前服务（Ctrl+C）
# 重新启动
python app.py
```

---

## 📊 性能指标

### 目标指标

| 指标 | 目标值 | 当前状态 |
|------|---------|---------|
| mAP@0.5 | > 95% | 待训练 |
| CIoU | > 0.85 | 待训练 |
| 诊断准确率 | > 90% | 待训练 |
| 平均置信度 | > 0.7 | 待训练 |
| 推理效率 | > 30 FPS | 待测试 |

### 性能优化建议

1. **使用 GPU 训练**
- NVIDIA GPU（推荐）
- CUDA 11.0+
- 显存 ≥ 8GB

2. **数据增强**
- 使用 Mosaic 和 Mixup
- 调整 HSV 参数
- 旋转和翻转

3. **模型选择**
- yolov8n：最快，适合边缘部署
- yolov8s：平衡速度和精度
- yolov8m：高精度，适合服务器部署

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [README.md](file:///d:/Project/WheatAgent/README.md) | 项目主文档 |
| [INSTALLATION.md](file:///d:/Project/WheatAgent/INSTALLATION.md) | 安装部署指南 |
| [ARCHITECTURE.md](file:///d:/Project/WheatAgent/ARCHITECTURE.md) | 系统架构详解 |
| [DATA_PREPARATION.md](file:///d:/Project/WheatAgent/DATA_PREPARATION.md) | 数据准备指南 |
| [TRAINING.md](file:///d:/Project/WheatAgent/TRAINING.md) | 模型训练指南 |
| [API_USAGE.md](file:///d:/Project/WheatAgent/API_USAGE.md) | API 使用说明 |
| [DEPLOYMENT_REPORT.md](file:///d:/Project/WheatAgent/DEPLOYMENT_REPORT.md) | 部署报告 |
| [SYSTEM_IMPROVEMENT_REPORT.md](file:///d:/Project/WheatAgent/SYSTEM_IMPROVEMENT_REPORT.md) | 系统改进报告 |

---

## 🎯 快速参考

### 常用命令

```bash
# 启动 Web 界面
python app.py

# 训练模型（50 轮）
python src/vision/train_improved.py --epochs 50

# 训练模型（100 轮）
python src/vision/train_improved.py --epochs 100

# LoRA 微调（10 轮）
python src/vision/train_improved.py --lora --epochs 10

# 测试 Neo4j 连接
python test_neo4j.py

# 检查数据集
python check_dataset.py

# 系统功能测试
python test_system.py
```

### 文件路径

| 组件 | 路径 |
|------|------|
| 主程序 | [main.py](file:///d:/Project/WheatAgent/main.py) |
| Web 界面 | [app.py](file:///d:/Project/WheatAgent/app.py) |
| 训练脚本 | [train_improved.py](file:///d:/Project/WheatAgent/src/vision/train_improved.py) |
| 配置文件 | [wheat_disease.yaml](file:///d:/Project/WheatAgent/configs/wheat_disease.yaml) |
| 数据集 | [datasets/wheat_data/](file:///d:/Project/WheatAgent/datasets/wheat_data/) |

---

## 📞 技术支持

### 系统要求

- Python 3.8+
- PyTorch 2.0+
- CUDA 11.0+（如使用 GPU）
- Neo4j 5.15+
- 8GB+ RAM（推荐 16GB）

### 推荐硬件

| 用途 | 硬件配置 |
|------|----------|
| 训练 | NVIDIA GPU（8GB+ 显存），16GB+ RAM |
| 推理 | NVIDIA GPU（4GB+ 显存），8GB RAM |
| 边缘部署 | NVIDIA Jetson Orin NX |
| 开发 | CPU，8GB RAM |

---

<div align="center">

**🌾 IWDDA 系统已完全部署并准备就绪！**

**Web 访问**：http://localhost:7860

**开始使用**：训练模型 → 提升诊断准确率

**文档版本**：v1.0

**最后更新**：2026-02-10

</div>

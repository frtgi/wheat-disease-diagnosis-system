# WheatAgent 开发指南

## 项目概述

WheatAgent（基于多模态特征融合的小麦病害诊断智能体）是一个融合计算机视觉、自然语言处理和知识图谱技术的智能农业诊断系统。

## 系统架构

```
WheatAgent/
├── src/
│   ├── api/              # FastAPI RESTful接口
│   │   ├── __init__.py
│   │   └── main.py       # API主应用
│   ├── web/              # Gradio Web界面
│   │   ├── __init__.py
│   │   └── app.py        # Web应用
│   ├── vision/           # 视觉感知模块
│   │   └── vision_engine.py
│   ├── cognition/        # 认知模块
│   │   └── cognition_engine.py
│   ├── fusion/           # 多模态融合模块
│   │   └── fusion_engine.py
│   ├── graph/            # 知识图谱模块
│   │   └── graph_engine.py
│   └── evolution/        # 自进化模块
│       └── active_learner.py
├── tests/                # 测试模块
│   ├── test_api.py
│   ├── test_vision.py
│   └── conftest.py
├── models/               # 模型权重
├── datasets/             # 数据集
└── docs/                 # 文档
```

## 快速开始

### 1. 环境配置

```bash
# 激活Python 3.10环境
conda activate wheatagent-py310

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

#### 启动API服务
```bash
python run_api.py
```
API文档访问: http://localhost:8000/docs

#### 启动Web界面
```bash
python run_web.py
```
Web界面访问: http://localhost:7860

### 3. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_api.py -v

# 运行非慢速测试
pytest tests/ -v -m "not slow"
```

## API接口说明

### 健康检查
- **GET** `/health` - 服务健康状态

### 诊断接口
- **POST** `/diagnose/image` - 图像病害诊断
  - 参数: `file` (图像文件), `use_knowledge` (bool), `top_k` (int)
  
- **POST** `/diagnose/text` - 文本症状诊断
  - 参数: `description` (str), `use_knowledge` (bool), `top_k` (int)

### 知识图谱接口
- **GET** `/knowledge/diseases` - 获取病害列表
- **GET** `/knowledge/disease/{name}` - 获取病害详情

### 模型管理
- **GET** `/models` - 获取已加载模型列表

## Web界面功能

### 1. 图像诊断
- 上传小麦病害图像
- 自动检测和识别病害
- 可视化检测结果
- 显示防治建议

### 2. 文本诊断
- 输入症状描述
- 基于语义匹配诊断
- 提供相关病害建议

### 3. 知识库查询
- 查看所有已知病害
- 查询特定病害详情
- 获取防治方法

## 开发规范

### 代码风格
- 遵循PEP 8规范
- 使用类型注解
- 编写docstring文档

### 测试要求
- 新功能必须包含单元测试
- 核心模块必须包含集成测试
- 测试覆盖率 > 80%

### 提交规范
- 使用语义化提交信息
- 提交前运行测试
- 更新相关文档

## 性能指标

| 指标 | 目标值 | 当前值 |
|------|--------|--------|
| 检测准确率 (mAP@0.5) | > 95% | - |
| 推理速度 (FPS) | > 30 | - |
| API响应时间 | < 500ms | - |
| Web界面加载 | < 3s | - |

## 部署指南

### 本地部署
```bash
# 1. 克隆项目
git clone <repository>
cd WheatAgent

# 2. 创建环境
conda create -n wheatagent python=3.10
conda activate wheatagent

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python run_api.py  # 终端1
python run_web.py  # 终端2
```

### 生产部署
- 使用Gunicorn部署API: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.main:app`
- 使用Nginx反向代理
- 配置HTTPS
- 设置监控和日志

## 常见问题

### Q1: 如何添加新的病害类型？
1. 更新 `data/wheat_disease.yaml`
2. 收集训练数据
3. 重新训练YOLOv8模型
4. 更新知识图谱

### Q2: 如何优化检测速度？
1. 使用TensorRT导出模型
2. 调整输入图像尺寸
3. 使用半精度推理 (FP16)
4. 批量处理图像

### Q3: 如何扩展知识图谱？
1. 准备结构化数据
2. 使用 `src/graph/knowledge_graph_builder.py`
3. 导入到Neo4j
4. 重新训练TransE嵌入

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

MIT License

## 联系方式

- 项目主页: [GitHub](https://github.com/your-repo/WheatAgent)
- 问题反馈: [Issues](https://github.com/your-repo/WheatAgent/issues)
- 邮件联系: your-email@example.com

---

**最后更新**: 2026-02-10

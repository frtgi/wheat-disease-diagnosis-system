# 🔌 IWDDA API 使用说明

本文档详细说明如何使用 IWDDA 的各种接口，包括 Web 界面、命令行接口和编程接口。

## 📋 目录

- [快速开始](#快速开始)
- [Web 界面使用](#web-界面使用)
- [命令行接口](#命令行接口)
- [Python API](#python-api)
- [批量诊断](#批量诊断)
- [知识问答](#知识问答)
- [反馈系统](#反馈系统)
- [高级用法](#高级用法)

---

## 🚀 快速开始

### 最简单的使用方式

```python
from main import WheatDoctor

# 初始化诊断系统
doctor = WheatDoctor()

# 执行诊断
result = doctor.run_diagnosis(
    image_path="data/images/test_wheat.jpg",
    user_text="叶片上有黄色条纹状锈斑"
)

# 查看结果
print(f"诊断结果: {result['final_report']['diagnosis']}")
print(f"置信度: {result['final_report']['confidence']:.2f}")
```

### 启动 Web 界面

```bash
# 启动 Gradio Web 服务
python app.py
```

访问 `http://localhost:7860` 使用交互式界面。

---

## 🌐 Web 界面使用

### 启动 Web 服务

```bash
# 基本启动
python app.py

# 自定义端口
python app.py --port 8080

# 公网访问
python app.py --server_name 0.0.0.0 --server_port 7860
```

### 功能模块

#### 1. 智能诊断 (Diagnosis)

**功能**：上传图像进行病害诊断

**步骤**：
1. 点击"智能诊断"标签页
2. 上传小麦叶片/麦穗图像
3. 输入症状描述（可选）
4. 点击"开始会诊"按钮
5. 查看诊断结果和防治建议

**输入**：
- **图像**：支持的格式包括 JPG、PNG、JPEG
- **症状描述**：例如"叶片上有黄色条纹"

**输出**：
- **病灶定位图**：标注检测框的可视化图像
- **诊断报告**：包含诊断结果、置信度、推理过程
- **扩展建议**：预防措施、环境诱因

#### 2. 专家咨询 (Chatbot)

**功能**：基于知识图谱的问答系统

**示例问题**：
- "赤霉病怎么预防？"
- "条锈病的成因是什么？"
- "白粉病用什么药？"
- "蚜虫如何防治？"

**步骤**：
1. 点击"专家咨询"标签页
2. 在输入框中输入问题
3. 查看系统回答

#### 3. 系统管理

**功能**：查看系统状态和反馈信息

**内容包括**：
- 模型版本信息
- 数据集统计
- 反馈数据统计

---

## 💻 命令行接口

### 基本诊断

```bash
# 使用测试脚本
python main.py
```

### 自定义诊断

创建自定义脚本 `custom_diagnosis.py`:

```python
from main import WheatDoctor

def main():
    # 初始化系统
    doctor = WheatDoctor()
    
    # 执行诊断
    result = doctor.run_diagnosis(
        image_path="path/to/your/image.jpg",
        user_text="描述症状"
    )
    
    # 打印详细结果
    print("=" * 60)
    print("诊断报告")
    print("=" * 60)
    print(f"诊断结果: {result['final_report']['diagnosis']}")
    print(f"置信度: {result['final_report']['confidence']:.2%}")
    print("\n推理过程:")
    for step in result['final_report']['reasoning']:
        print(f"  - {step}")
    print(f"\n治疗建议: {result['final_report']['treatment']}")
    
    # 保存结果图像
    from PIL import Image
    Image.fromarray(result['plotted_image']).save('result.jpg')
    print("\n结果图像已保存: result.jpg")
    
    # 关闭系统
    doctor.close()

if __name__ == "__main__":
    main()
```

运行：
```bash
python custom_diagnosis.py
```

---

## 🐍 Python API

### 初始化系统

```python
from main import WheatDoctor

# 使用默认配置
doctor = WheatDoctor()

# 自定义 Neo4j 密码
from src.graph.graph_engine import KnowledgeAgent
kg = KnowledgeAgent(password="your_password")
doctor = WheatDoctor()
doctor.brain = kg
```

### 执行诊断

```python
result = doctor.run_diagnosis(
    image_path="path/to/image.jpg",
    user_text="叶片上有黄色条纹"
)
```

**返回值结构**：

```python
{
    'plotted_image': numpy.ndarray,  # 标注后的图像 (RGB)
    'vision_data': {
        'label': '条锈病',
        'conf': 0.92
    },
    'text_data': {
        'label': '条锈病',
        'conf': 0.85
    },
    'final_report': {
        'diagnosis': '条锈病',
        'confidence': 0.887,
        'reasoning': [
            '✅ 视觉与文本证据一致，均指向【条锈病】。'
        ],
        'treatment': '三唑酮/戊唑醇(喷雾)'
    }
}
```

### 访问各模块

#### 1. 视觉模块

```python
# 直接使用视觉引擎
from src.vision.vision_engine import VisionAgent

eye = VisionAgent()
results = eye.detect(
    image_path="path/to/image.jpg",
    conf_threshold=0.5,
    save_result=True
)

# 遍历检测结果
for result in results:
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        print(f"类别: {class_id}, 置信度: {confidence:.2f}")
```

#### 2. 文本模块

```python
# 直接使用文本引擎
from src.text.text_engine import LanguageAgent

ear = LanguageAgent()

# 计算相似度
similarity = ear.compute_similarity(
    "叶片上有黄色条纹",
    "条锈病的典型症状是黄色条纹"
)
print(f"相似度: {similarity:.4f}")

# 获取文本嵌入
embedding = ear.get_embedding("叶片上有黄色条纹")
print(f"嵌入维度: {embedding.shape}")
```

#### 3. 知识图谱模块

```python
# 直接使用知识图谱引擎
from src.graph.graph_engine import KnowledgeAgent

brain = KnowledgeAgent(password="123456789s")

# 获取病害详情
details = brain.get_disease_details("条锈病")
print(f"成因: {details['causes']}")
print(f"预防: {details['preventions']}")
print(f"治疗: {details['treatments']}")

# 获取治疗建议
treatment = brain.get_treatment_info("条锈病")
print(f"治疗建议: {treatment}")

# 关闭连接
brain.close()
```

#### 4. 融合模块

```python
# 直接使用融合引擎
from src.fusion.fusion_engine import FusionAgent
from src.graph.graph_engine import KnowledgeAgent

# 初始化
kg = KnowledgeAgent()
fusion = FusionAgent(knowledge_agent=kg)

# 执行融合
vision_result = {'label': '条锈病', 'conf': 0.92}
text_result = {'label': '条锈病', 'conf': 0.85}

report = fusion.fuse_and_decide(
    vision_result=vision_result,
    text_result=text_result,
    user_text="叶片上有黄色条纹"
)

print(f"最终诊断: {report['diagnosis']}")
print(f"置信度: {report['confidence']:.2f}")
```

#### 5. 反馈模块

```python
# 直接使用反馈引擎
from src.action.learner_engine import ActiveLearner

learner = ActiveLearner()

# 收集反馈
learner.collect_feedback(
    image_path="path/to/image.jpg",
    system_diagnosis="白粉病",
    user_correction="条锈病",
    comments="实际是条锈病，白粉病误判"
)
```

---

## 📦 批量诊断

### 批量处理脚本

```python
import os
from pathlib import Path
from main import WheatDoctor
import pandas as pd

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
                'confidence': 0.0,
                'error': str(e)
            })
    
    # 保存到 CSV
    df = pd.DataFrame(results_list)
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\n✅ 结果已保存到: {output_csv}")
    
    # 关闭系统
    doctor.close()

if __name__ == "__main__":
    batch_diagnosis("data/images/test")
```

运行：
```bash
python batch_diagnosis.py
```

### 多进程加速

```python
import multiprocessing as mp
from functools import partial

def diagnose_single(image_path, user_text=""):
    """诊断单张图像"""
    from main import WheatDoctor
    doctor = WheatDoctor()
    result = doctor.run_diagnosis(image_path, user_text)
    doctor.close()
    return result

def batch_diagnosis_parallel(image_dir, num_processes=4):
    """多进程批量诊断"""
    image_files = list(Path(image_dir).glob('*.jpg'))
    
    # 创建进程池
    with mp.Pool(num_processes) as pool:
        results = pool.map(diagnose_single, image_files)
    
    return results

if __name__ == "__main__":
    results = batch_diagnosis_parallel("data/images/test", num_processes=4)
```

---

## 📚 知识问答

### 知识图谱查询

```python
from src.graph.graph_engine import KnowledgeAgent

# 初始化
kg = KnowledgeAgent()

# 查询病害详情
def query_disease(disease_name):
    """查询病害的完整信息"""
    details = kg.get_disease_details(disease_name)
    
    print(f"=== {details['name']} ===")
    print(f"\n🌧️ 成因:")
    for cause in details['causes']:
        print(f"  - {cause}")
    
    print(f"\n🛡️ 预防措施:")
    for prevention in details['preventions']:
        print(f"  - {prevention}")
    
    print(f"\n💊 治疗药剂:")
    for treatment in details['treatments']:
        print(f"  - {treatment}")

# 查询示例
query_disease("条锈病")
query_disease("赤霉病")
query_disease("白粉病")

kg.close()
```

### 复杂查询

```python
def complex_query():
    """执行复杂的图查询"""
    kg = KnowledgeAgent()
    
    with kg.driver.session() as session:
        # 查询所有由高湿环境引起的病害
        query1 = """
        MATCH (d:Disease)-[:CAUSED_BY]->(c:Cause {name: '高湿环境'})
        RETURN d.name as disease_name
        """
        result1 = session.run(query1)
        print("\n由高湿环境引起的病害:")
        for record in result1:
            print(f"  - {record['disease_name']}")
        
        # 查询所有可用三唑酮治疗的病害
        query2 = """
        MATCH (d:Disease)-[:TREATED_BY]->(t:Treatment)
        WHERE t.name CONTAINS '三唑酮'
        RETURN d.name as disease_name
        """
        result2 = session.run(query2)
        print("\n可用三唑酮治疗的病害:")
        for record in result2:
            print(f"  - {record['disease_name']}")
    
    kg.close()

complex_query()
```

---

## 🔄 反馈系统

### 提交反馈

```python
from main import WheatDoctor
from src.action.learner_engine import ActiveLearner

def submit_feedback(image_path, system_diagnosis, 
                  user_correction, comments=""):
    """提交用户反馈"""
    # 初始化学习器
    learner = ActiveLearner()
    
    # 收集反馈
    learner.collect_feedback(
        image_path=image_path,
        system_diagnosis=system_diagnosis,
        user_correction=user_correction,
        comments=comments
    )
    
    print("✅ 反馈已提交！")

# 示例：系统诊断为白粉病，实际是条锈病
submit_feedback(
    image_path="data/images/test_wheat.jpg",
    system_diagnosis="白粉病",
    user_correction="条锈病",
    comments="实际是条锈病，白粉病误判"
)
```

### 查看反馈日志

```python
def view_feedback_logs():
    """查看反馈日志"""
    import os
    from pathlib import Path
    
    feedback_root = Path("datasets/feedback_data")
    
    # 遍历所有类别文件夹
    for class_dir in feedback_root.iterdir():
        if class_dir.is_dir():
            log_file = class_dir / "feedback_log.txt"
            
            if log_file.exists():
                print(f"\n=== {class_dir.name} ===")
                with open(log_file, 'r', encoding='utf-8') as f:
                    print(f.read())

view_feedback_logs()
```

### 处理反馈数据

```python
from src.action.evolve import EvolutionEngine

def process_feedback():
    """处理反馈数据并准备增量训练"""
    engine = EvolutionEngine()
    
    # 消化反馈数据
    processed_count = engine.digest_feedback()
    
    print(f"✅ 处理了 {processed_count} 个反馈样本")
    print("反馈数据已移动到训练集，可以开始增量训练")

process_feedback()
```

---

## 🎯 高级用法

### 自定义融合策略

```python
from src.fusion.fusion_engine import FusionAgent

class CustomFusionAgent(FusionAgent):
    """自定义融合策略"""
    
    def fuse_and_decide(self, vision_result, text_result, user_text):
        """自定义融合逻辑"""
        v_label = vision_result.get('label', '未知')
        v_conf = vision_result.get('conf', 0.0)
        t_label = text_result.get('label', '未知')
        t_conf = text_result.get('conf', 0.0)
        
        # 自定义策略：只采信视觉结果
        if v_conf > 0.7:
            final_diagnosis = v_label
            final_conf = v_conf
            reasoning = ["仅采信视觉结果"]
        else:
            final_diagnosis = "未知"
            final_conf = 0.0
            reasoning = ["置信度不足，无法确定"]
        
        return {
            "diagnosis": final_diagnosis,
            "confidence": final_conf,
            "reasoning": reasoning,
            "treatment": self.kg.get_treatment_info(final_diagnosis)
        }

# 使用自定义融合
from src.graph.graph_engine import KnowledgeAgent

kg = KnowledgeAgent()
custom_fusion = CustomFusionAgent(knowledge_agent=kg)
```

### 集成到 FastAPI

```python
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from main import WheatDoctor
import io
from PIL import Image

app = FastAPI(title="IWDDA API")
doctor = WheatDoctor()

@app.post("/diagnose")
async def diagnose(
    file: UploadFile = File(...),
    description: str = ""
):
    """
    诊断接口
    """
    # 保存上传的图像
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # 临时保存
    temp_path = f"temp_{file.filename}"
    image.save(temp_path)
    
    # 执行诊断
    result = doctor.run_diagnosis(temp_path, description)
    
    # 返回结果
    return JSONResponse({
        "diagnosis": result['final_report']['diagnosis'],
        "confidence": float(result['final_report']['confidence']),
        "reasoning": result['final_report']['reasoning'],
        "treatment": result['final_report']['treatment']
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

运行：
```bash
python api_server.py
```

访问：`http://localhost:8000/docs`

### 实时视频流诊断

```python
import cv2
from main import WheatDoctor

def real_time_diagnosis(video_source=0):
    """
    实时视频流诊断
    """
    # 初始化
    doctor = WheatDoctor()
    cap = cv2.VideoCapture(video_source)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 保存当前帧
        cv2.imwrite("temp_frame.jpg", frame)
        
        # 执行诊断
        result = doctor.run_diagnosis("temp_frame.jpg", "")
        
        # 在帧上绘制结果
        diagnosis = result['final_report']['diagnosis']
        conf = result['final_report']['confidence']
        
        cv2.putText(frame, f"{diagnosis} ({conf:.2f})", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   1, (0, 255, 0), 2)
        
        # 显示
        cv2.imshow('Real-time Diagnosis', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    doctor.close()

if __name__ == "__main__":
    real_time_diagnosis(0)  # 0 表示默认摄像头
```

---

## 📊 性能监控

### 记录诊断历史

```python
import json
from datetime import datetime

class DiagnosisLogger:
    """诊断日志记录器"""
    
    def __init__(self, log_file="diagnosis_history.json"):
        self.log_file = log_file
        self.history = self._load_history()
    
    def _load_history(self):
        """加载历史记录"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def log(self, image_path, result):
        """记录诊断结果"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'image_path': image_path,
            'diagnosis': result['final_report']['diagnosis'],
            'confidence': float(result['final_report']['confidence']),
            'vision_label': result['vision_data']['label'],
            'vision_conf': float(result['vision_data']['conf']),
            'text_label': result['text_data']['label'],
            'text_conf': float(result['text_data']['conf'])
        }
        
        self.history.append(record)
        self._save_history()
    
    def _save_history(self):
        """保存历史记录"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def get_statistics(self):
        """获取统计信息"""
        if not self.history:
            return {}
        
        total = len(self.history)
        diagnoses = [r['diagnosis'] for r in self.history]
        
        from collections import Counter
        diagnosis_counts = Counter(diagnoses)
        
        avg_confidence = sum(r['confidence'] for r in self.history) / total
        
        return {
            'total_diagnoses': total,
            'diagnosis_distribution': dict(diagnosis_counts),
            'average_confidence': avg_confidence
        }

# 使用示例
logger = DiagnosisLogger()

result = doctor.run_diagnosis("image.jpg", "症状描述")
logger.log("image.jpg", result)

stats = logger.get_statistics()
print(f"总诊断次数: {stats['total_diagnoses']}")
print(f"平均置信度: {stats['average_confidence']:.2f}")
```

---

## 🐛 常见问题

### Q1: 如何处理非小麦图像？

**A**: 系统会返回"未知"诊断，置信度较低。建议：
1. 添加"其他作物"类别
2. 使用置信度阈值过滤
3. 提示用户上传正确的图像

### Q2: 如何提高诊断速度？

**A**: 优化方法：
1. 使用更小的模型（yolov8n）
2. 降低输入图像尺寸
3. 使用 GPU 加速
4. 批量处理时使用多进程

### Q3: 如何处理多语言输入？

**A**: 当前系统主要支持中文。如需支持其他语言：
1. 更换文本模型为多语言模型
2. 更新标准症状库
3. 添加翻译层

### Q4: 如何集成到移动应用？

**A**: 推荐方案：
1. 使用 FastAPI 提供 REST API
2. 移动应用调用 API
3. 或使用 ONNX/TensorRT 导出模型，在移动端本地推理

### Q5: 如何保护用户隐私？

**A**: 隐私保护措施：
1. 不存储用户上传的图像
2. 使用临时文件，诊断后立即删除
3. 匿名化日志记录
4. 提供本地部署选项

---

## 📞 获取帮助

- **项目文档**: [README.md](README.md)
- **安装指南**: [INSTALLATION.md](INSTALLATION.md)
- **系统架构**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **数据准备**: [DATA_PREPARATION.md](DATA_PREPARATION.md)
- **训练指南**: [TRAINING.md](TRAINING.md)
- **问题反馈**: [GitHub Issues](https://github.com/your-repo/WheatAgent/issues)

---

<div align="center">

**祝您使用愉快！如有问题，请随时反馈。**

</div>

import torch
import ultralytics
import transformers
import neo4j
import gradio

print("="*30)
print("✅ 环境检查报告 (Environment Check)")
print("="*30)
print(f"1. PyTorch 版本: {torch.__version__}")
print(f"   - GPU 是否可用: {torch.cuda.is_available()}")
print(f"2. YOLO (Ultralytics) 版本: {ultralytics.__version__}")
print(f"3. Transformers 版本: {transformers.__version__}")
print(f"4. Neo4j Driver 版本: {neo4j.__version__}")
print(f"5. Gradio 版本: {gradio.__version__}")
print("="*30)
print("🚀 所有依赖库导入成功！可以开始开发了！")
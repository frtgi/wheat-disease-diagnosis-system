"""
检查 PyTorch 和 CUDA 环境
"""
import torch

print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    major, minor = torch.cuda.get_device_capability()
    print(f"GPU Compute Capability: {major}.{minor}")

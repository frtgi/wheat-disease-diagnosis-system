#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
恢复训练脚本
从上次崩溃的检查点继续训练
"""

import os
import sys

os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

from ultralytics import YOLO

def main():
    """
    主函数 - 从检查点恢复训练
    """
    os.chdir("D:/Project/WheatAgent")
    
    checkpoint_path = "models/wheat_disease_v10_yolov8s/phase1_warmup/weights/last.pt"
    
    print("=" * 60)
    print("从检查点恢复训练")
    print(f"检查点: {checkpoint_path}")
    print("=" * 60)
    
    model = YOLO(checkpoint_path)
    
    results = model.train(
        resume=True,
        workers=2,
    )
    
    print("\n训练完成!")
    return results

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
# 文件路径: WheatAgent/src/action/learner_engine.py
import os
import shutil
import datetime

class ActiveLearner:
    def __init__(self, data_root="datasets/feedback_data"):
        """
        初始化自进化学习引擎
        :param data_root: 反馈数据存储根目录
        """
        self.data_root = data_root
        if not os.path.exists(self.data_root):
            os.makedirs(self.data_root)
        print(f"🎓 [Learner Engine] 自进化模块已就绪 (存储路径: {self.data_root})")

    def collect_feedback(self, image_path, system_diagnosis, user_correction=None, comments=""):
        """
        收集用户反馈，构建困难样本库 (Hard Sample Mining)
        """
        # 如果用户没有修正，说明系统诊断正确，或者用户确认了系统诊断
        final_label = user_correction if user_correction else system_diagnosis
        
        # 1. 创建对应类别的文件夹
        save_dir = os.path.join(self.data_root, final_label)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        # 2. 生成带时间戳的文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        
        # 标记：如果是修正过的，加个前缀方便区分
        prefix = f"err_{system_diagnosis}_corr_" if user_correction else "confirmed_"
        new_filename = f"{timestamp}_{prefix}{final_label}{ext}"
        save_path = os.path.join(save_dir, new_filename)
        
        # 3. 复制图片
        try:
            shutil.copy2(image_path, save_path)
            
            # 4. 记录日志 (Expert Rationale)
            log_path = os.path.join(save_dir, "feedback_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                record = f"[{timestamp}] Image: {new_filename} | System: {system_diagnosis} | Final: {final_label} | Comment: {comments}\n"
                f.write(record)
                
            print(f"💾 [自进化] 样本已由专家(用户)确认并入库: {final_label}")
            print(f"   -> 已保存至: {save_path}")
            print(f"   -> 该数据将用于下一轮增量训练 (Incremental Learning)。")
            
        except Exception as e:
            print(f"❌ 保存反馈数据失败: {e}")
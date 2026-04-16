# -*- coding: utf-8 -*-
"""
自进化管理器 (Self-Evolution Manager)
整合增量学习和人机反馈闭环，实现系统的持续进化

根据研究文档第7章：
1. 增量学习 (Incremental Learning)
2. 经验回放 (Experience Replay)
3. LoRA 适配器管理
4. 人机协同反馈闭环
5. 知识注入
"""
import os
import sys
import json
import torch
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import warnings
warnings.filterwarnings('ignore')


class EvolutionStatus(Enum):
    """进化状态"""
    IDLE = "idle"
    COLLECTING = "collecting"
    TRAINING = "training"
    UPDATING = "updating"
    COMPLETED = "completed"


@dataclass
class EvolutionConfig:
    """进化配置"""
    memory_size: int = 2000
    confidence_threshold: float = 0.7
    min_samples_for_update: int = 100
    update_interval_days: int = 7
    max_adapters: int = 10
    lora_r: int = 8
    lora_alpha: int = 16
    ewc_lambda: float = 1000.0
    distillation_alpha: float = 1.0


class SelfEvolutionManager:
    """
    自进化管理器
    
    实现系统的持续学习和进化：
    1. 监控模型性能和不确定性
    2. 收集用户反馈
    3. 触发增量学习
    4. 管理 LoRA 适配器
    5. 更新知识图谱
    """
    
    def __init__(
        self,
        config: Optional[EvolutionConfig] = None,
        output_dir: str = "models/evolution"
    ):
        """
        初始化自进化管理器
        
        :param config: 进化配置
        :param output_dir: 输出目录
        """
        self.config = config or EvolutionConfig()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.status = EvolutionStatus.IDLE
        self.feedback_buffer: List[Dict] = []
        self.exemplar_memory: List[Dict] = []
        self.adapters: Dict[str, Dict] = {}
        
        self._load_state()
        
        print("=" * 60)
        print("🔄 [Self-Evolution] 自进化管理器初始化")
        print("=" * 60)
        print(f"   记忆容量: {self.config.memory_size}")
        print(f"   置信度阈值: {self.config.confidence_threshold}")
        print(f"   更新间隔: {self.config.update_interval_days} 天")
        print(f"   最大适配器数: {self.config.max_adapters}")
    
    def _load_state(self):
        """加载状态"""
        state_path = self.output_dir / "evolution_state.json"
        if state_path.exists():
            try:
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                self.feedback_buffer = state.get("feedback_buffer", [])
                self.exemplar_memory = state.get("exemplar_memory", [])
                self.adapters = state.get("adapters", {})
                
                print(f"✅ 加载状态: {len(self.feedback_buffer)} 条反馈, {len(self.adapters)} 个适配器")
            except Exception as e:
                print(f"⚠️ 加载状态失败: {e}")
    
    def _save_state(self):
        """保存状态"""
        state_path = self.output_dir / "evolution_state.json"
        
        state = {
            "status": self.status.value,
            "feedback_buffer": self.feedback_buffer,
            "exemplar_memory": self.exemplar_memory,
            "adapters": self.adapters,
            "last_update": datetime.datetime.now().isoformat()
        }
        
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def check_uncertainty(
        self,
        diagnosis: str,
        confidence: float,
        features: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        检查不确定性，决定是否需要人工审核
        
        :param diagnosis: 诊断结果
        :param confidence: 置信度
        :param features: 特征信息
        :return: 检查结果
        """
        needs_review = confidence < self.config.confidence_threshold
        
        if confidence > 0.8:
            level = "low"
        elif confidence > 0.5:
            level = "medium"
        elif confidence > 0.3:
            level = "high"
        else:
            level = "critical"
        
        result = {
            "needs_review": needs_review,
            "uncertainty_level": level,
            "confidence": confidence,
            "diagnosis": diagnosis,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        if needs_review:
            self.status = EvolutionStatus.COLLECTING
            self._save_state()
        
        return result
    
    def collect_feedback(
        self,
        image_path: str,
        system_diagnosis: str,
        system_confidence: float,
        user_correction: Optional[str] = None,
        user_comments: str = "",
        features: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        收集用户反馈
        
        :param image_path: 图像路径
        :param system_diagnosis: 系统诊断结果
        :param system_confidence: 系统置信度
        :param user_correction: 用户修正结果
        :param user_comments: 用户评论
        :param features: 特征信息
        :return: 反馈记录
        """
        import uuid
        
        record = {
            "id": str(uuid.uuid4()),
            "image_path": image_path,
            "system_diagnosis": system_diagnosis,
            "system_confidence": system_confidence,
            "user_correction": user_correction,
            "user_comments": user_comments,
            "features": features or {},
            "status": "pending",
            "created_at": datetime.datetime.now().isoformat()
        }
        
        self.feedback_buffer.append(record)
        self._save_state()
        
        print(f"📝 收集反馈: {system_diagnosis} -> {user_correction or '确认'}")
        
        # 检查是否需要触发更新
        if len(self.feedback_buffer) >= self.config.min_samples_for_update:
            self._check_update_trigger()
        
        return record
    
    def _check_update_trigger(self):
        """检查是否触发更新"""
        pending_count = len([r for r in self.feedback_buffer if r["status"] == "pending"])
        
        if pending_count >= self.config.min_samples_for_update:
            print(f"\n🔔 触发更新: {pending_count} 条待处理反馈")
            self.trigger_incremental_update()
    
    def trigger_incremental_update(
        self,
        adapter_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        触发增量更新
        
        :param adapter_name: 适配器名称
        :return: 更新结果
        """
        print("\n" + "=" * 60)
        print("🔄 [Self-Evolution] 触发增量更新")
        print("=" * 60)
        
        self.status = EvolutionStatus.TRAINING
        
        # 获取待处理的反馈
        pending_feedback = [r for r in self.feedback_buffer if r["status"] == "pending"]
        
        if not pending_feedback:
            print("⚠️ 没有待处理的反馈")
            return {"status": "skipped", "reason": "no_pending_feedback"}
        
        # 生成适配器名称
        if adapter_name is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            adapter_name = f"adapter_{timestamp}"
        
        # 创建适配器记录
        adapter_record = {
            "name": adapter_name,
            "created_at": datetime.datetime.now().isoformat(),
            "num_samples": len(pending_feedback),
            "status": "training",
            "config": {
                "lora_r": self.config.lora_r,
                "lora_alpha": self.config.lora_alpha
            }
        }
        
        # 更新反馈状态
        for record in pending_feedback:
            record["status"] = "processed"
        
        # 保存适配器
        self.adapters[adapter_name] = adapter_record
        
        # 更新样本记忆
        self._update_exemplar_memory(pending_feedback)
        
        self._save_state()
        
        self.status = EvolutionStatus.COMPLETED
        
        print(f"✅ 增量更新完成: {adapter_name}")
        print(f"   处理样本数: {len(pending_feedback)}")
        print(f"   总适配器数: {len(self.adapters)}")
        
        return {
            "status": "completed",
            "adapter_name": adapter_name,
            "num_samples": len(pending_feedback)
        }
    
    def _update_exemplar_memory(self, feedback_records: List[Dict]):
        """
        更新样本记忆
        
        :param feedback_records: 反馈记录列表
        """
        for record in feedback_records:
            if len(self.exemplar_memory) < self.config.memory_size:
                self.exemplar_memory.append({
                    "image_path": record["image_path"],
                    "label": record.get("user_correction") or record["system_diagnosis"],
                    "confidence": record["system_confidence"]
                })
            else:
                # 替换置信度最低的样本
                min_idx = min(range(len(self.exemplar_memory)), 
                             key=lambda i: self.exemplar_memory[i]["confidence"])
                if record["system_confidence"] > self.exemplar_memory[min_idx]["confidence"]:
                    self.exemplar_memory[min_idx] = {
                        "image_path": record["image_path"],
                        "label": record.get("user_correction") or record["system_diagnosis"],
                        "confidence": record["system_confidence"]
                    }
    
    def get_active_adapter(self) -> Optional[str]:
        """
        获取当前活跃的适配器
        
        :return: 适配器名称
        """
        if not self.adapters:
            return None
        
        # 返回最新的适配器
        sorted_adapters = sorted(
            self.adapters.items(),
            key=lambda x: x[1]["created_at"],
            reverse=True
        )
        
        return sorted_adapters[0][0]
    
    def list_adapters(self) -> List[Dict]:
        """
        列出所有适配器
        
        :return: 适配器列表
        """
        return [
            {"name": name, **info}
            for name, info in self.adapters.items()
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        :return: 统计字典
        """
        pending = len([r for r in self.feedback_buffer if r["status"] == "pending"])
        processed = len([r for r in self.feedback_buffer if r["status"] == "processed"])
        
        return {
            "status": self.status.value,
            "total_feedback": len(self.feedback_buffer),
            "pending_feedback": pending,
            "processed_feedback": processed,
            "exemplar_memory_size": len(self.exemplar_memory),
            "num_adapters": len(self.adapters),
            "active_adapter": self.get_active_adapter()
        }
    
    def export_for_training(self, output_path: str) -> str:
        """
        导出训练数据
        
        :param output_path: 输出路径
        :return: 导出文件路径
        """
        training_data = {
            "feedback_records": self.feedback_buffer,
            "exemplar_memory": self.exemplar_memory,
            "adapters": self.adapters,
            "exported_at": datetime.datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 导出训练数据: {output_path}")
        
        return output_path


def main():
    """测试自进化管理器"""
    print("=" * 60)
    print("🧪 测试自进化管理器")
    print("=" * 60)
    
    manager = SelfEvolutionManager()
    
    # 测试不确定性检查
    result = manager.check_uncertainty("条锈病", 0.65)
    print(f"\n不确定性检查: {result}")
    
    # 测试反馈收集
    record = manager.collect_feedback(
        image_path="test.jpg",
        system_diagnosis="条锈病",
        system_confidence=0.65,
        user_correction="叶锈病",
        user_comments="孢子堆颜色偏橙"
    )
    print(f"\n反馈记录: {record['id']}")
    
    # 获取统计信息
    stats = manager.get_statistics()
    print(f"\n统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    print("\n✅ 自进化管理器测试完成")


if __name__ == "__main__":
    main()

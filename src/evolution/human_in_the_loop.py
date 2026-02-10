# -*- coding: utf-8 -*-
"""
人机协同反馈闭环 (Human-in-the-Loop Feedback)
根据研究文档，该模块实现：
1. 不确定性预警：当模型置信度低于阈值时自动标记待审核样本
2. 专家标注与修正：农学专家通过界面查看疑难样本并进行修正
3. 知识注入：修正后的样本进入训练集，专家解释转化为知识图谱三元组
4. 模型更新：定期触发增量训练，将新知识内化
"""
import os
import json
import shutil
import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class FeedbackStatus(Enum):
    """反馈状态枚举"""
    PENDING = "pending"           # 待审核
    REVIEWED = "reviewed"         # 已审核
    CONFIRMED = "confirmed"       # 已确认
    CORRECTED = "corrected"       # 已修正
    DISCARDED = "discarded"       # 已丢弃
    PROCESSED = "processed"       # 已处理（进入训练）


class UncertaintyLevel(Enum):
    """不确定性级别"""
    LOW = "low"                   # 低不确定性 (置信度 > 0.8)
    MEDIUM = "medium"             # 中等不确定性 (0.5 < 置信度 <= 0.8)
    HIGH = "high"                 # 高不确定性 (0.3 < 置信度 <= 0.5)
    CRITICAL = "critical"         # 严重不确定性 (置信度 <= 0.3)


@dataclass
class FeedbackRecord:
    """
    反馈记录数据类
    """
    id: str                       # 唯一标识符
    image_path: str               # 图像路径
    system_diagnosis: str         # 系统诊断结果
    system_confidence: float      # 系统置信度
    user_correction: Optional[str]  # 用户修正结果
    user_comments: str            # 用户评论/解释
    uncertainty_level: str        # 不确定性级别
    status: str                   # 状态
    created_at: str               # 创建时间
    reviewed_at: Optional[str]    # 审核时间
    reviewer_id: Optional[str]    # 审核人ID
    features: Optional[Dict]      # 特征信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def create(
        cls,
        image_path: str,
        system_diagnosis: str,
        system_confidence: float,
        user_correction: Optional[str] = None,
        user_comments: str = "",
        features: Optional[Dict] = None
    ) -> 'FeedbackRecord':
        """
        创建新的反馈记录
        
        :param image_path: 图像路径
        :param system_diagnosis: 系统诊断结果
        :param system_confidence: 系统置信度
        :param user_correction: 用户修正结果
        :param user_comments: 用户评论
        :param features: 特征信息
        :return: FeedbackRecord实例
        """
        # 确定不确定性级别
        if system_confidence > 0.8:
            uncertainty = UncertaintyLevel.LOW.value
        elif system_confidence > 0.5:
            uncertainty = UncertaintyLevel.MEDIUM.value
        elif system_confidence > 0.3:
            uncertainty = UncertaintyLevel.HIGH.value
        else:
            uncertainty = UncertaintyLevel.CRITICAL.value
        
        # 确定初始状态
        if user_correction:
            status = FeedbackStatus.CORRECTED.value
        else:
            status = FeedbackStatus.PENDING.value
        
        return cls(
            id=str(uuid.uuid4()),
            image_path=image_path,
            system_diagnosis=system_diagnosis,
            system_confidence=system_confidence,
            user_correction=user_correction,
            user_comments=user_comments,
            uncertainty_level=uncertainty,
            status=status,
            created_at=datetime.datetime.now().isoformat(),
            reviewed_at=None,
            reviewer_id=None,
            features=features
        )


class UncertaintyMonitor:
    """
    不确定性监控器
    监控模型预测的不确定性，自动标记需要专家审核的样本
    """
    
    def __init__(
        self,
        high_uncertainty_threshold: float = 0.5,
        critical_uncertainty_threshold: float = 0.3,
        entropy_threshold: float = 1.0
    ):
        """
        初始化不确定性监控器
        
        :param high_uncertainty_threshold: 高不确定性阈值
        :param critical_uncertainty_threshold: 严重不确定性阈值
        :param entropy_threshold: 熵阈值
        """
        self.high_uncertainty_threshold = high_uncertainty_threshold
        self.critical_uncertainty_threshold = critical_uncertainty_threshold
        self.entropy_threshold = entropy_threshold
        
        # 统计信息
        self.stats = {
            "total_predictions": 0,
            "high_uncertainty_count": 0,
            "critical_uncertainty_count": 0,
            "flagged_count": 0
        }
        
        print(f"🔍 [Uncertainty Monitor] 不确定性监控器初始化")
        print(f"   高不确定性阈值: {high_uncertainty_threshold}")
        print(f"   严重不确定性阈值: {critical_uncertainty_threshold}")
    
    def check_uncertainty(
        self,
        confidence: float,
        prediction_entropy: Optional[float] = None
    ) -> tuple:
        """
        检查预测的不确定性
        
        :param confidence: 置信度
        :param prediction_entropy: 预测熵
        :return: (是否需要标记, 不确定性级别)
        """
        self.stats["total_predictions"] += 1
        
        # 基于置信度判断
        if confidence <= self.critical_uncertainty_threshold:
            self.stats["critical_uncertainty_count"] += 1
            return True, UncertaintyLevel.CRITICAL
        
        if confidence <= self.high_uncertainty_threshold:
            self.stats["high_uncertainty_count"] += 1
            return True, UncertaintyLevel.HIGH
        
        # 基于熵判断
        if prediction_entropy and prediction_entropy > self.entropy_threshold:
            return True, UncertaintyLevel.MEDIUM
        
        return False, UncertaintyLevel.LOW
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        if stats["total_predictions"] > 0:
            stats["flagged_rate"] = stats["flagged_count"] / stats["total_predictions"]
        else:
            stats["flagged_rate"] = 0.0
        return stats


class HumanInTheLoop:
    """
    人机协同反馈闭环
    实现专家与AI系统的协同工作
    """
    
    def __init__(
        self,
        feedback_dir: str = "data/human_feedback",
        auto_flag_threshold: float = 0.5
    ):
        """
        初始化人机协同模块
        
        :param feedback_dir: 反馈数据存储目录
        :param auto_flag_threshold: 自动标记阈值
        """
        self.feedback_dir = feedback_dir
        self.auto_flag_threshold = auto_flag_threshold
        
        # 创建目录结构
        self.pending_dir = os.path.join(feedback_dir, "pending")
        self.reviewed_dir = os.path.join(feedback_dir, "reviewed")
        self.confirmed_dir = os.path.join(feedback_dir, "confirmed")
        self.corrected_dir = os.path.join(feedback_dir, "corrected")
        self.knowledge_dir = os.path.join(feedback_dir, "knowledge_extracted")
        
        for dir_path in [self.pending_dir, self.reviewed_dir, self.confirmed_dir, 
                        self.corrected_dir, self.knowledge_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # 不确定性监控器
        self.uncertainty_monitor = UncertaintyMonitor()
        
        # 反馈记录缓存
        self.feedback_records: Dict[str, FeedbackRecord] = {}
        
        # 回调函数
        self.on_feedback_submitted: Optional[Callable] = None
        self.on_knowledge_extracted: Optional[Callable] = None
        
        # 加载已有记录
        self._load_existing_records()
        
        print(f"👤 [Human-in-the-Loop] 人机协同模块初始化完成")
        print(f"   反馈目录: {feedback_dir}")
        print(f"   自动标记阈值: {auto_flag_threshold}")
    
    def submit_prediction(
        self,
        image_path: str,
        system_diagnosis: str,
        system_confidence: float,
        features: Optional[Dict] = None
    ) -> Optional[FeedbackRecord]:
        """
        提交预测结果，检查是否需要专家审核
        
        :param image_path: 图像路径
        :param system_diagnosis: 系统诊断结果
        :param system_confidence: 系统置信度
        :param features: 特征信息
        :return: 如果需要审核则返回FeedbackRecord，否则返回None
        """
        # 检查不确定性
        needs_review, uncertainty_level = self.uncertainty_monitor.check_uncertainty(
            system_confidence
        )
        
        # 如果需要审核或置信度低于阈值
        if needs_review or system_confidence < self.auto_flag_threshold:
            # 创建反馈记录
            record = FeedbackRecord.create(
                image_path=image_path,
                system_diagnosis=system_diagnosis,
                system_confidence=system_confidence,
                features=features
            )
            
            # 保存到待审核队列
            self._save_record(record, self.pending_dir)
            self.feedback_records[record.id] = record
            
            print(f"⚠️ 样本已标记待审核: {record.id}")
            print(f"   诊断: {system_diagnosis} (置信度: {system_confidence:.2f})")
            print(f"   不确定性级别: {uncertainty_level.value}")
            
            return record
        
        return None
    
    def submit_feedback(
        self,
        record_id: str,
        user_correction: Optional[str] = None,
        user_comments: str = "",
        reviewer_id: Optional[str] = None
    ) -> bool:
        """
        提交专家反馈
        
        :param record_id: 记录ID
        :param user_correction: 用户修正结果
        :param user_comments: 用户评论
        :param reviewer_id: 审核人ID
        :return: 是否成功
        """
        if record_id not in self.feedback_records:
            print(f"❌ 记录不存在: {record_id}")
            return False
        
        record = self.feedback_records[record_id]
        
        # 更新记录
        record.user_correction = user_correction
        record.user_comments = user_comments
        record.reviewer_id = reviewer_id
        record.reviewed_at = datetime.datetime.now().isoformat()
        
        # 确定新状态
        if user_correction:
            if user_correction == record.system_diagnosis:
                record.status = FeedbackStatus.CONFIRMED.value
                target_dir = self.confirmed_dir
            else:
                record.status = FeedbackStatus.CORRECTED.value
                target_dir = self.corrected_dir
                
                # 提取知识
                self._extract_knowledge(record)
        else:
            record.status = FeedbackStatus.REVIEWED.value
            target_dir = self.reviewed_dir
        
        # 移动记录
        self._move_record(record, target_dir)
        
        # 触发回调
        if self.on_feedback_submitted:
            self.on_feedback_submitted(record)
        
        print(f"✅ 反馈已提交: {record_id}")
        print(f"   系统诊断: {record.system_diagnosis}")
        print(f"   用户修正: {user_correction or '无'}")
        print(f"   状态: {record.status}")
        
        return True
    
    def get_pending_reviews(
        self,
        uncertainty_filter: Optional[str] = None,
        limit: int = 10
    ) -> List[FeedbackRecord]:
        """
        获取待审核的样本列表
        
        :param uncertainty_filter: 不确定性级别过滤
        :param limit: 返回数量限制
        :return: 反馈记录列表
        """
        pending_records = [
            record for record in self.feedback_records.values()
            if record.status == FeedbackStatus.PENDING.value
        ]
        
        # 按不确定性级别排序（严重的优先）
        uncertainty_priority = {
            UncertaintyLevel.CRITICAL.value: 0,
            UncertaintyLevel.HIGH.value: 1,
            UncertaintyLevel.MEDIUM.value: 2,
            UncertaintyLevel.LOW.value: 3
        }
        
        pending_records.sort(
            key=lambda x: uncertainty_priority.get(x.uncertainty_level, 4)
        )
        
        # 过滤
        if uncertainty_filter:
            pending_records = [
                r for r in pending_records
                if r.uncertainty_level == uncertainty_filter
            ]
        
        return pending_records[:limit]
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        获取反馈统计信息
        
        :return: 统计信息字典
        """
        stats = {
            "total_records": len(self.feedback_records),
            "pending_count": 0,
            "reviewed_count": 0,
            "confirmed_count": 0,
            "corrected_count": 0,
            "uncertainty_distribution": {
                UncertaintyLevel.LOW.value: 0,
                UncertaintyLevel.MEDIUM.value: 0,
                UncertaintyLevel.HIGH.value: 0,
                UncertaintyLevel.CRITICAL.value: 0
            },
            "accuracy": 0.0
        }
        
        confirmed_and_corrected = []
        
        for record in self.feedback_records.values():
            # 状态统计
            if record.status == FeedbackStatus.PENDING.value:
                stats["pending_count"] += 1
            elif record.status == FeedbackStatus.REVIEWED.value:
                stats["reviewed_count"] += 1
            elif record.status == FeedbackStatus.CONFIRMED.value:
                stats["confirmed_count"] += 1
                confirmed_and_corrected.append(record)
            elif record.status == FeedbackStatus.CORRECTED.value:
                stats["corrected_count"] += 1
                confirmed_and_corrected.append(record)
            
            # 不确定性分布
            if record.uncertainty_level in stats["uncertainty_distribution"]:
                stats["uncertainty_distribution"][record.uncertainty_level] += 1
        
        # 计算准确率
        if confirmed_and_corrected:
            correct_count = sum(
                1 for r in confirmed_and_corrected
                if r.system_diagnosis == r.user_correction
            )
            stats["accuracy"] = correct_count / len(confirmed_and_corrected)
        
        # 合并不确定性监控统计
        stats["uncertainty_stats"] = self.uncertainty_monitor.get_statistics()
        
        return stats
    
    def _extract_knowledge(self, record: FeedbackRecord):
        """
        从专家反馈中提取知识
        
        :param record: 反馈记录
        """
        if not record.user_correction or not record.user_comments:
            return
        
        # 构建知识三元组
        knowledge_triples = []
        
        # 如果系统诊断错误，建立错误关联
        if record.user_correction != record.system_diagnosis:
            knowledge_triples.append({
                "subject": record.system_diagnosis,
                "predicate": "易混淆为",
                "object": record.user_correction,
                "context": record.user_comments,
                "source": f"expert_feedback_{record.id}"
            })
        
        # 保存提取的知识
        knowledge_file = os.path.join(
            self.knowledge_dir,
            f"{record.id}.json"
        )
        
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump({
                "record_id": record.id,
                "extracted_at": datetime.datetime.now().isoformat(),
                "triples": knowledge_triples,
                "expert_comments": record.user_comments
            }, f, ensure_ascii=False, indent=2)
        
        # 触发回调
        if self.on_knowledge_extracted:
            self.on_knowledge_extracted(knowledge_triples)
        
        print(f"📚 知识已提取: {len(knowledge_triples)} 个三元组")
    
    def _save_record(self, record: FeedbackRecord, directory: str):
        """保存记录到指定目录"""
        # 复制图像
        image_filename = os.path.basename(record.image_path)
        target_image_path = os.path.join(directory, image_filename)
        
        if os.path.exists(record.image_path):
            shutil.copy2(record.image_path, target_image_path)
        
        # 保存元数据
        metadata_path = os.path.join(directory, f"{record.id}.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
    
    def _move_record(self, record: FeedbackRecord, target_dir: str):
        """移动记录到目标目录"""
        # 从原目录删除
        for dir_path in [self.pending_dir, self.reviewed_dir, self.confirmed_dir, self.corrected_dir]:
            metadata_path = os.path.join(dir_path, f"{record.id}.json")
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            image_filename = os.path.basename(record.image_path)
            image_path = os.path.join(dir_path, image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # 保存到新目录
        self._save_record(record, target_dir)
    
    def _load_existing_records(self):
        """加载已有的反馈记录"""
        for dir_path in [self.pending_dir, self.reviewed_dir, self.confirmed_dir, self.corrected_dir]:
            if not os.path.exists(dir_path):
                continue
            
            for filename in os.listdir(dir_path):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(dir_path, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    record = FeedbackRecord(**data)
                    self.feedback_records[record.id] = record
                
                except Exception as e:
                    print(f"⚠️ 加载反馈记录失败 {filepath}: {e}")
    
    def export_training_data(self, output_dir: str) -> Dict[str, Any]:
        """
        导出训练数据
        
        :param output_dir: 输出目录
        :return: 导出统计
        """
        os.makedirs(output_dir, exist_ok=True)
        
        export_stats = {
            "confirmed": 0,
            "corrected": 0,
            "total": 0
        }
        
        # 导出已确认和已修正的样本
        for record in self.feedback_records.values():
            if record.status not in [FeedbackStatus.CONFIRMED.value, 
                                     FeedbackStatus.CORRECTED.value]:
                continue
            
            # 确定标签
            label = record.user_correction or record.system_diagnosis
            
            # 创建类别目录
            class_dir = os.path.join(output_dir, label)
            os.makedirs(class_dir, exist_ok=True)
            
            # 复制图像
            image_filename = os.path.basename(record.image_path)
            target_path = os.path.join(class_dir, f"{record.id}_{image_filename}")
            
            if os.path.exists(record.image_path):
                shutil.copy2(record.image_path, target_path)
            
            # 更新统计
            if record.status == FeedbackStatus.CONFIRMED.value:
                export_stats["confirmed"] += 1
            else:
                export_stats["corrected"] += 1
            
            export_stats["total"] += 1
            
            # 更新记录状态
            record.status = FeedbackStatus.PROCESSED.value
        
        print(f"✅ 训练数据已导出: {export_stats['total']} 个样本")
        print(f"   已确认: {export_stats['confirmed']}")
        print(f"   已修正: {export_stats['corrected']}")
        
        return export_stats


def test_human_in_the_loop():
    """测试人机协同反馈闭环"""
    print("=" * 60)
    print("🧪 测试人机协同反馈闭环")
    print("=" * 60)
    
    # 创建人机协同模块
    hitl = HumanInTheLoop(
        feedback_dir="data/test_human_feedback",
        auto_flag_threshold=0.6
    )
    
    # 测试提交预测（高置信度，不需要审核）
    print("\n" + "=" * 60)
    print("🧪 测试高置信度预测")
    print("=" * 60)
    
    record1 = hitl.submit_prediction(
        image_path="test_image_1.jpg",
        system_diagnosis="条锈病",
        system_confidence=0.92
    )
    print(f"✅ 高置信度预测: {'需要审核' if record1 else '无需审核'}")
    
    # 测试提交预测（低置信度，需要审核）
    print("\n" + "=" * 60)
    print("🧪 测试低置信度预测")
    print("=" * 60)
    
    record2 = hitl.submit_prediction(
        image_path="test_image_2.jpg",
        system_diagnosis="白粉病",
        system_confidence=0.45
    )
    print(f"✅ 低置信度预测: {'需要审核' if record2 else '无需审核'}")
    
    # 测试提交反馈（确认正确）
    print("\n" + "=" * 60)
    print("🧪 测试提交确认反馈")
    print("=" * 60)
    
    if record2:
        hitl.submit_feedback(
            record_id=record2.id,
            user_correction="白粉病",  # 确认系统诊断正确
            user_comments="诊断正确，确实是白粉病",
            reviewer_id="expert_001"
        )
    
    # 测试提交另一个预测和修正反馈
    print("\n" + "=" * 60)
    print("🧪 测试提交修正反馈")
    print("=" * 60)
    
    record3 = hitl.submit_prediction(
        image_path="test_image_3.jpg",
        system_diagnosis="条锈病",
        system_confidence=0.38
    )
    
    if record3:
        hitl.submit_feedback(
            record_id=record3.id,
            user_correction="叶锈病",  # 修正系统诊断
            user_comments="这是叶锈病，不是条锈病。叶锈病的孢子堆较小且不规则。",
            reviewer_id="expert_001"
        )
    
    # 测试获取统计信息
    print("\n" + "=" * 60)
    print("🧪 测试获取统计信息")
    print("=" * 60)
    
    stats = hitl.get_feedback_statistics()
    print(f"✅ 总记录数: {stats['total_records']}")
    print(f"✅ 待审核: {stats['pending_count']}")
    print(f"✅ 已确认: {stats['confirmed_count']}")
    print(f"✅ 已修正: {stats['corrected_count']}")
    print(f"✅ 系统准确率: {stats['accuracy']:.2%}")
    
    # 测试获取待审核列表
    print("\n" + "=" * 60)
    print("🧪 测试获取待审核列表")
    print("=" * 60)
    
    pending = hitl.get_pending_reviews(limit=5)
    print(f"✅ 待审核样本数: {len(pending)}")
    
    # 清理测试数据
    if os.path.exists("data/test_human_feedback"):
        shutil.rmtree("data/test_human_feedback")
    
    print("\n" + "=" * 60)
    print("✅ 人机协同反馈闭环测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_human_in_the_loop()

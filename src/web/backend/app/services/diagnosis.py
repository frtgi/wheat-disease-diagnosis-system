"""
诊断服务
处理诊断相关的业务逻辑，集成 AI 引擎进行智能诊断
"""
import logging
import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from dataclasses import dataclass
from datetime import datetime
from PIL import Image

from ..models.diagnosis import Diagnosis
from ..schemas.diagnosis import DiagnosisCreate, DiagnosisUpdate
from .yolo_service import get_yolo_service
from .qwen_service import get_qwen_service

logger = logging.getLogger(__name__)

INFERENCE_SEMAPHORE = asyncio.Semaphore(3)


@dataclass
class DiagnosisResult:
    """
    诊断结果数据类

    存储 AI 诊断的完整结果，支持多候选病害置信度列表
    """
    disease_name: str
    confidence: float
    severity: str
    description: str
    recommendations: List[str]
    knowledge_links: List[str]
    confidences: Optional[List[Dict[str, Any]]] = None
    vision_features: Optional[Dict[str, Any]] = None
    cognition_features: Optional[Dict[str, Any]] = None
    fusion_features: Optional[Dict[str, Any]] = None


# 创建服务单例
_yolo_service = None
_qwen_service = None


def get_vision_engine():
    """
    获取视觉引擎单例（使用 YOLOv8Service）
    
    返回:
        YOLOv8Service: YOLO 服务实例
    """
    global _yolo_service
    if _yolo_service is None:
        try:
            print("👁️ 初始化视觉引擎 (YOLOv8Service)...")
            _yolo_service = get_yolo_service()
            print("✅ 视觉引擎初始化完成")
        except Exception as e:
            logger.error(f"视觉引擎初始化失败：{e}")
            raise
    return _yolo_service


def get_qwen_engine():
    """
    获取 Qwen 认知引擎单例
    
    返回:
        QwenService: Qwen 服务实例
    """
    global _qwen_service
    if _qwen_service is None:
        try:
            print("🧠 初始化认知引擎 (QwenService)...")
            _qwen_service = get_qwen_service()
            print("✅ 认知引擎初始化完成")
        except Exception as e:
            logger.error(f"认知引擎初始化失败：{e}")
            raise
    return _qwen_service


def get_knowledge_agent():
    """
    获取知识图谱代理单例（简化版）
    
    返回:
        None: 暂不支持
    """
    return None


def get_fusion_engine():
    """
    获取融合引擎单例（简化版）
    
    返回:
        None: 暂不支持
    """
    return None


class DiagnosisService:
    """
    诊断服务类
    
    提供基于 AI 的小麦病害诊断功能，包括：
    - 图像诊断 (diagnose_image)
    - 文本诊断 (diagnose_text)
    - 诊断记录管理
    """
    
    def __init__(self, db: Session):
        """
        初始化诊断服务
        
        参数:
            db: 数据库会话
        """
        self.db = db
    
    def _calculate_image_md5(self, image_path: str) -> str:
        """
        计算图像的 MD5 哈希值
        
        参数:
            image_path: 图像文件路径
            
        返回:
            图像的 MD5 哈希字符串
        """
        import hashlib
        
        hash_md5 = hashlib.md5()
        try:
            with open(image_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"计算图像 MD5 失败：{e}")
            # 如果无法读取文件，使用时间戳作为备用方案
            return hashlib.md5(f"{image_path}_{datetime.now().isoformat()}".encode()).hexdigest()
    
    def _parse_qwen_output(self, output: str) -> DiagnosisResult:
        """
        解析 Qwen 输出
        
        参数:
            output: Qwen 生成的文本
        
        返回:
            DiagnosisResult: 诊断结果
        """
        import json
        
        try:
            # 尝试解析 JSON 格式输出
            data = json.loads(output)
            return DiagnosisResult(
                disease_name=data.get("disease_name", "未知"),
                confidence=data.get("confidence", 0.5),
                severity=data.get("severity", "medium"),
                description=data.get("description", ""),
                recommendations=data.get("recommendations", []),
                knowledge_links=data.get("knowledge_links", [])
            )
        except json.JSONDecodeError:
            # 非 JSON 格式，尝试从文本中提取信息
            return self._parse_text_output(output)
        except Exception as e:
            logger.warning(f"JSON 解析失败，使用默认解析：{e}")
            return self._parse_text_output(output)
    
    def _parse_text_output(self, output: str) -> DiagnosisResult:
        """
        解析文本格式输出
        
        参数:
            output: Qwen 生成的文本
        
        返回:
            DiagnosisResult: 诊断结果
        """
        import re
        
        disease_name = "未知病害"
        confidence = 0.5
        severity = "medium"
        description = output
        recommendations = ["请咨询专业农技人员"]
        
        # 尝试提取病害名称
        disease_patterns = [
            r"诊断为 [:：]?\s*(.+?)(?:[。.!]|$)",
            r"病害 [:：]?\s*(.+?)(?:[。.!]|$)",
            r"识别为 [:：]?\s*(.+?)(?:[。.!]|$)"
        ]
        
        for pattern in disease_patterns:
            match = re.search(pattern, output)
            if match:
                disease_name = match.group(1).strip()
                break
        
        # 尝试提取置信度
        conf_patterns = [
            r"置信度 [:：]?\s*(\d+\.?\d*)%?",
            r"概率 [:：]?\s*(\d+\.?\d*)%?",
            r"confidence [:：]?\s*(\d+\.?\d*)"
        ]
        
        for pattern in conf_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    conf_value = float(match.group(1))
                    if conf_value > 1:
                        conf_value = conf_value / 100
                    confidence = min(max(conf_value, 0.0), 1.0)
                except ValueError:
                    pass
                break
        
        # 尝试提取严重程度
        if any(word in output for word in ["严重", "重度", "高危"]):
            severity = "high"
        elif any(word in output for word in ["轻微", "轻度", "初期"]):
            severity = "low"
        
        # 尝试提取防治建议
        rec_patterns = [
            r"防治建议 [:：]?\s*(.+?)(?:[。.!]|$)",
            r"建议 [:：]?\s*(.+?)(?:[。.!]|$)",
            r"治疗方案 [:：]?\s*(.+?)(?:[。.!]|$)"
        ]
        
        extracted_recs = []
        for pattern in rec_patterns:
            matches = re.findall(pattern, output)
            extracted_recs.extend(matches)
        
        if extracted_recs:
            recommendations = [rec.strip() for rec in extracted_recs[:5]]
        
        return DiagnosisResult(
            disease_name=disease_name,
            confidence=confidence,
            severity=severity,
            description=description,
            recommendations=recommendations,
            knowledge_links=[]
        )
    
    async def diagnose_image(
        self,
        image_path: str,
        symptoms: Optional[str] = None
    ) -> DiagnosisResult:
        """
        图像诊断方法
        
        使用信号量限制并发推理数量，防止 GPU 内存溢出
        
        参数:
            image_path: 图像文件路径
            symptoms: 可选的文本症状描述
        
        返回:
            DiagnosisResult: 诊断结果
        """
        async with INFERENCE_SEMAPHORE:
            try:
                logger.info(f"开始图像诊断（当前并发：{3 - INFERENCE_SEMAPHORE._value}）")
                
                print(f"\n🔍 开始图像诊断：{image_path}")
                
                # 1. 视觉检测
                print("\n👁️ 步骤 1: 视觉检测...")
                yolo_service = get_vision_engine()
                
                image = Image.open(image_path).convert('RGB')
                vision_result = yolo_service.detect(image)
                
                if not vision_result.get('success') or vision_result.get('count', 0) == 0:
                    print("⚠️ 视觉检测未发现目标，使用纯文本诊断")
                    if symptoms:
                        return await self.diagnose_text(symptoms)
                    else:
                        return DiagnosisResult(
                        disease_name="未检测到病害",
                        confidence=0.0,
                        severity="low",
                        description="图像中未检测到明显的病害症状",
                        recommendations=["请拍摄更清晰的叶片图像", "确保光线充足"],
                        knowledge_links=[],
                        confidences=[{"disease_name": "健康", "confidence": 1.0, "disease_class": None}]
                    )
                
                detections = vision_result.get('detections', [])
                primary_detection = max(detections, key=lambda x: x.get('confidence', 0))

                disease_name = primary_detection.get('class_name', '未知病害')
                confidence = primary_detection.get('confidence', 0.0)

                confidences_list = [
                    {
                        "disease_name": det.get('chinese_name', det.get('class_name', '未知')),
                        "confidence": det.get('confidence', 0.0),
                        "disease_class": det.get('class_id')
                    }
                    for det in sorted(detections, key=lambda x: x.get('confidence', 0), reverse=True)
                ]

                print(f"✅ 视觉检测完成：{disease_name} (置信度：{confidence:.2%})，共 {len(confidences_list)} 个候选")
                
                # 2. 确定严重程度
                severity = "medium"
                if confidence > 0.8:
                    severity = "high"
                elif confidence < 0.5:
                    severity = "low"
                
                # 3. 获取病害信息
                description = f"检测到病害：{disease_name}"
                recommendations = [
                    "及时清除病残体",
                    "合理密植，改善通风",
                    "喷施杀菌剂防治",
                    "请咨询专业农技人员获取详细防治方案"
                ]
                
                # 4. 尝试使用 Qwen 进行增强分析
                knowledge_links = []
                try:
                    qwen_service = get_qwen_engine()
                    if qwen_service and qwen_service.is_loaded:
                        print("\n🧠 步骤 2: AI 增强分析...")
                        ai_result = qwen_service.diagnose(
                            image=image,
                            symptoms=symptoms or f"检测到{disease_name}",
                            enable_thinking=False,
                            use_graph_rag=True,
                            disease_context=disease_name
                        )
                        if ai_result.get('success'):
                            ai_diagnosis = ai_result.get('diagnosis', {})
                            if ai_diagnosis.get('disease_name'):
                                disease_name = ai_diagnosis['disease_name']
                            if ai_diagnosis.get('confidence'):
                                confidence = max(confidence, ai_diagnosis['confidence'])
                            if ai_diagnosis.get('description'):
                                description = ai_diagnosis['description']
                            if ai_diagnosis.get('recommendations'):
                                recommendations = ai_diagnosis['recommendations']
                            if ai_result.get('knowledge_links'):
                                knowledge_links = ai_result['knowledge_links']
                            print("✅ AI 增强分析完成")
                except Exception as e:
                    logger.warning(f"AI 增强分析失败：{e}")
                
                print(f"\n✅ 图像诊断完成：{disease_name} (置信度：{confidence:.2%}, 严重程度：{severity})")
                
                return DiagnosisResult(
                    disease_name=disease_name,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    recommendations=recommendations,
                    knowledge_links=knowledge_links,
                    confidences=confidences_list,
                    vision_features={
                        'detections': detections,
                        'primary_class': disease_name,
                        'confidence': confidence
                    }
                )
                
            except Exception as e:
                logger.error(f"图像诊断失败：{e}")
                import traceback
                traceback.print_exc()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"诊断失败：{str(e)}"
                )

    async def diagnose_text(
        self,
        symptoms: str
    ) -> DiagnosisResult:
        """
        文本诊断方法
        
        参数:
            symptoms: 文本症状描述
        
        返回:
            DiagnosisResult: 诊断结果
        """
        try:
            print("\n📝 开始文本诊断...")
            
            # 使用 Qwen 引擎进行文本分析
            qwen_engine = get_qwen_engine()
            
            # 先进行规则匹配获取初步诊断
            preliminary_result = self._rule_based_diagnosis(symptoms)
            disease_name = preliminary_result.disease_name if preliminary_result.disease_name != "未知病害" else None
            
            knowledge_links = []
            
            try:
                # 尝试使用 Qwen 的 diagnose 方法（支持 GraphRAG）
                print("🔍 调用 Qwen diagnose 方法...")
                print(f"   - disease_context: {disease_name}")
                print(f"   - qwen_engine.enable_graph_rag: {getattr(qwen_engine, 'enable_graph_rag', 'N/A')}")
                print(f"   - qwen_engine.graphrag_engine: {getattr(qwen_engine, 'graphrag_engine', 'N/A')}")
                
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        qwen_engine.diagnose,
                        image=None,
                        symptoms=symptoms,
                        enable_thinking=False,
                        use_graph_rag=True,
                        disease_context=disease_name
                    ),
                    timeout=30.0
                )
                
                print(f"✅ Qwen diagnose 返回成功: {result.get('success')}")
                print(f"   - knowledge_links: {result.get('knowledge_links', [])}")
                
                if result.get('success'):
                    diagnosis_data = result.get('diagnosis', {})
                    knowledge_links = result.get('knowledge_links', [])
                    
                    diagnosis_result = DiagnosisResult(
                        disease_name=diagnosis_data.get('disease_name', preliminary_result.disease_name),
                        confidence=diagnosis_data.get('confidence', preliminary_result.confidence),
                        severity=diagnosis_data.get('severity', preliminary_result.severity),
                        description=diagnosis_data.get('description', preliminary_result.description),
                        recommendations=diagnosis_data.get('recommendations', preliminary_result.recommendations),
                        knowledge_links=knowledge_links,
                        confidences=[{
                            "disease_name": diagnosis_data.get('disease_name', preliminary_result.disease_name),
                            "confidence": diagnosis_data.get('confidence', preliminary_result.confidence),
                            "disease_class": None
                        }]
                    )
                else:
                    diagnosis_result = preliminary_result
                    
            except Exception as e:
                logger.warning(f"Qwen 文本生成失败：{e}，使用规则匹配")
                # 即使 Qwen 生成失败，也尝试从 GraphRAG 获取知识链接
                try:
                    if qwen_engine and qwen_engine.graphrag_engine and disease_name:
                        disease_details = qwen_engine.graphrag_engine.get_disease_details(disease_name)
                        if disease_details:
                            knowledge_links = disease_details.get('causes', []) + disease_details.get('preventions', []) + disease_details.get('treatments', [])
                            print(f"📚 从 GraphRAG 获取知识链接：{len(knowledge_links)} 条")
                except Exception as kg_error:
                    logger.warning(f"GraphRAG 知识检索失败：{kg_error}")
                # 创建包含知识链接的诊断结果
                diagnosis_result = DiagnosisResult(
                    disease_name=preliminary_result.disease_name,
                    confidence=preliminary_result.confidence,
                    severity=preliminary_result.severity,
                    description=preliminary_result.description,
                    recommendations=preliminary_result.recommendations,
                    knowledge_links=knowledge_links,
                    confidences=[{
                        "disease_name": preliminary_result.disease_name,
                        "confidence": preliminary_result.confidence,
                        "disease_class": None
                    }]
                )
            
            print(f"\n✅ 文本诊断完成：{diagnosis_result.disease_name} (置信度：{diagnosis_result.confidence:.2%})")
            if knowledge_links:
                print(f"📚 知识图谱引用：{len(knowledge_links)} 条")
            return diagnosis_result
            
        except asyncio.TimeoutError:
            logger.error("文本诊断超时")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="诊断超时，请稍后重试"
            )
        except Exception as e:
            logger.error(f"文本诊断失败：{e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"诊断失败：{str(e)}"
            )
    
    def _rule_based_diagnosis(self, symptoms: str) -> DiagnosisResult:
        """
        基于规则的诊断（备用方案）
        
        参数:
            symptoms: 症状描述
        
        返回:
            DiagnosisResult: 诊断结果
        """
        symptoms_lower = symptoms.lower()
        
        # 症状 - 病害映射规则
        disease_rules = {
            '条锈病': {
                'keywords': ['黄色条状', '沿叶脉', '孢子堆', '褪绿'],
                'description': '小麦条锈病，病斑呈条状黄色，沿叶脉平行分布',
                'severity': 'high'
            },
            '叶锈病': {
                'keywords': ['橙黄色', '圆形', '散生', '锈斑'],
                'description': '小麦叶锈病，病斑呈圆形或椭圆形，橙黄色，散生分布',
                'severity': 'medium'
            },
            '白粉病': {
                'keywords': ['白色粉状', '霉层', '白粉'],
                'description': '小麦白粉病，叶片表面覆盖白色粉状霉层',
                'severity': 'medium'
            },
            '赤霉病': {
                'keywords': ['穗部', '粉红', '漂白', '霉层'],
                'description': '小麦赤霉病，穗部发病，呈粉红色霉层',
                'severity': 'high'
            },
            '纹枯病': {
                'keywords': ['云纹状', '茎基部', '病斑'],
                'description': '小麦纹枯病，茎基部病斑呈云纹状',
                'severity': 'medium'
            }
        }
        
        # 匹配病害
        best_match = None
        best_score = 0
        
        for disease, rules in disease_rules.items():
            score = sum(1 for keyword in rules['keywords'] if keyword in symptoms_lower)
            if score > best_score:
                best_score = score
                best_match = (disease, rules)
        
        if best_match and best_score >= 2:
            disease_name, rules = best_match
            confidence = min(0.5 + best_score * 0.15, 0.95)
            
            return DiagnosisResult(
                disease_name=disease_name,
                confidence=confidence,
                severity=rules['severity'],
                description=rules['description'],
                recommendations=[
                    "及时清除病残体",
                    "合理密植，改善通风",
                    "喷施杀菌剂防治"
                ],
                knowledge_links=[],
                confidences=[{"disease_name": disease_name, "confidence": confidence, "disease_class": None}]
            )
        else:
            return DiagnosisResult(
                disease_name="未知病害",
                confidence=0.3,
                severity="low",
                description=f"根据症状描述 '{symptoms}' 无法确定具体病害",
                recommendations=[
                    "请提供更详细的症状描述",
                    "建议上传叶片图像进行 AI 诊断",
                    "咨询当地农技专家"
                ],
                knowledge_links=[],
                confidences=[{"disease_name": "未知病害", "confidence": 0.3, "disease_class": None}]
            )


# 保持原有的数据库操作函数
def create_diagnosis(db: Session, diagnosis_data: DiagnosisCreate, user_id: int) -> Diagnosis:
    """
    创建诊断记录
    
    参数:
        db: 数据库会话
        diagnosis_data: 诊断数据
        user_id: 用户 ID
    
    返回:
        创建的诊断对象
    """
    diagnosis = Diagnosis(
        user_id=user_id,
        disease_id=diagnosis_data.disease_id,
        symptoms=diagnosis_data.symptoms
    )
    
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)
    
    return diagnosis


def get_diagnosis_by_id(db: Session, diagnosis_id: int) -> Optional[Diagnosis]:
    """
    根据 ID 获取诊断记录
    
    参数:
        db: 数据库会话
        diagnosis_id: 诊断 ID
    
    返回:
        诊断对象，不存在返回 None
    """
    return db.query(Diagnosis).filter(Diagnosis.id == diagnosis_id).first()


def get_user_diagnoses(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> List[Diagnosis]:
    """
    获取用户的诊断记录列表
    
    参数:
        db: 数据库会话
        user_id: 用户 ID
        skip: 跳过数量
        limit: 返回数量
    
    返回:
        诊断记录列表
    """
    return db.query(Diagnosis).filter(
        Diagnosis.user_id == user_id
    ).order_by(
        Diagnosis.created_at.desc()
    ).offset(skip).limit(limit).all()


def update_diagnosis(db: Session, diagnosis_id: int, update_data: DiagnosisUpdate) -> Diagnosis:
    """
    更新诊断记录
    
    参数:
        db: 数据库会话
        diagnosis_id: 诊断 ID
        update_data: 更新数据
    
    返回:
        更新后的诊断对象
    
    异常:
        HTTPException: 诊断记录不存在
    """
    diagnosis = get_diagnosis_by_id(db, diagnosis_id)
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断记录不存在"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(diagnosis, field, value)
    
    db.commit()
    db.refresh(diagnosis)
    
    return diagnosis


def delete_diagnosis(db: Session, diagnosis_id: int) -> bool:
    """
    删除诊断记录
    
    参数:
        db: 数据库会话
        diagnosis_id: 诊断 ID
    
    返回:
        是否删除成功
    
    异常:
        HTTPException: 诊断记录不存在
    """
    diagnosis = get_diagnosis_by_id(db, diagnosis_id)
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断记录不存在"
        )
    
    db.delete(diagnosis)
    db.commit()
    
    return True

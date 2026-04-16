"""
数据库迁移脚本 - 初始版本
创建所有数据表并插入初始数据

迁移版本：001
创建时间：2026-03-09
描述：创建 users、diseases、diagnoses、knowledge_graph 表结构
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 导入所有模型
from src.web.backend.app.models import User, Disease, Diagnosis, KnowledgeGraph
from src.web.backend.app.core.database import Base, engine


def create_tables():
    """
    创建所有数据库表
    
    使用 SQLAlchemy ORM 的 metadata.create_all 方法
    根据模型类自动创建对应的数据库表
    """
    print("=" * 60)
    print("开始创建数据库表...")
    print("=" * 60)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("✓ 成功创建以下数据表:")
    print("  - users (用户表)")
    print("  - diseases (病害表)")
    print("  - diagnoses (诊断记录表)")
    print("  - knowledge_graph (知识图谱表)")
    print()


def insert_initial_data(session):
    """
    插入初始测试数据
    
    Args:
        session: SQLAlchemy 数据库会话对象
    """
    print("=" * 60)
    print("开始插入初始数据...")
    print("=" * 60)
    
    # 检查是否已有数据
    if session.query(User).count() > 0:
        print("⚠ 检测到已有用户数据，跳过插入")
        return
    
    # 插入测试用户（密码为 bcrypt 加密的 '123456'）
    print("\n插入测试用户...")
    users = [
        User(
            username='farmer_zhang',
            email='zhang@example.com',
            password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu',
            role='farmer',
            phone='13800138001',
            is_active=True
        ),
        User(
            username='farmer_li',
            email='li@example.com',
            password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu',
            role='farmer',
            phone='13800138002',
            is_active=True
        ),
        User(
            username='tech_wang',
            email='wang@example.com',
            password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu',
            role='technician',
            phone='13800138003',
            is_active=True
        ),
        User(
            username='tech_zhao',
            email='zhao@example.com',
            password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu',
            role='technician',
            phone='13800138004',
            is_active=True
        ),
        User(
            username='admin',
            email='admin@example.com',
            password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu',
            role='admin',
            phone='13800138000',
            is_active=True
        )
    ]
    session.add_all(users)
    print(f"  ✓ 插入 {len(users)} 个测试用户")
    
    # 插入测试病害数据
    print("\n插入测试病害数据...")
    diseases = [
        Disease(
            name='小麦条锈病',
            scientific_name='Puccinia striiformis f. sp. tritici',
            code='WD001',
            category='fungal',
            symptoms='叶片上出现鲜黄色条状孢子堆，排列成行，后期变为褐色。严重时叶片卷曲、干枯，影响光合作用。',
            description='小麦条锈病是小麦上最重要的气传病害之一，流行年份可造成小麦减产 20%-30%，严重时可达 50% 以上。',
            causes='由条形柄锈菌引起，病菌通过气流传播。适宜发病温度为 9-15℃，相对湿度 80% 以上。',
            prevention_methods='["选用抗病品种", "适期播种，避免早播", "合理施肥，增施磷钾肥", "及时清除田间杂草", "药剂拌种"]',
            treatment_methods='["发病初期喷洒 15% 三唑酮可湿性粉剂 1000-1500 倍液", "25% 丙环唑乳油 2000-3000 倍液", "12.5% 烯唑醇可湿性粉剂 4000-5000 倍液", "间隔 7-10 天，连续防治 2-3 次"]',
            suitable_growth_stage='苗期、拔节期、抽穗期',
            severity=0.9
        ),
        Disease(
            name='小麦叶锈病',
            scientific_name='Puccinia triticina',
            code='WD002',
            category='fungal',
            symptoms='叶片上出现橙红色圆形或近圆形孢子堆，散生分布，不突破叶脉。后期病斑处叶片枯黄。',
            description='小麦叶锈病是小麦重要病害，分布广泛，主要危害叶片，也可危害叶鞘和茎秆。',
            causes='由小麦隐匿柄锈菌引起，病菌通过气流和雨水传播。适宜温度为 15-25℃，多雨高湿易发病。',
            prevention_methods='["选用抗病品种", "合理密植，改善通风透光", "平衡施肥，避免氮肥过量", "及时排水，降低田间湿度"]',
            treatment_methods='["发病初期喷洒 20% 三唑酮硫磺悬浮剂 200 倍液", "15% 三唑酮可湿性粉剂 1500 倍液", "25% 敌力脱乳油 2000 倍液", "间隔 10 天左右，连喷 2-3 次"]',
            suitable_growth_stage='拔节期、孕穗期、抽穗期',
            severity=0.7
        ),
        Disease(
            name='小麦白粉病',
            scientific_name='Blumeria graminis f. sp. tritici',
            code='WD003',
            category='fungal',
            symptoms='叶片、叶鞘、茎秆上出现白色絮状霉层，后期霉层变为灰白色或浅褐色，其上散生黑色小粒点。',
            description='小麦白粉病是小麦常见病害，主要危害叶片，严重时也可危害叶鞘、茎秆和穗部。',
            causes='由禾本科布氏白粉菌引起，病菌通过气流传播。适宜温度为 15-20℃，相对湿度 80% 以上，氮肥过多易发病。',
            prevention_methods='["选用抗病品种", "合理密植，改善通风条件", "控制氮肥用量，增施磷钾肥", "及时清除田间病残体"]',
            treatment_methods='["发病初期喷洒 15% 三唑酮可湿性粉剂 1500 倍液", "25% 丙环唑乳油 3000 倍液", "40% 氟硅唑乳油 8000 倍液", "间隔 7-10 天，连续防治 2 次"]',
            suitable_growth_stage='拔节期、孕穗期',
            severity=0.6
        ),
        Disease(
            name='小麦赤霉病',
            scientific_name='Fusarium graminearum',
            code='WD004',
            category='fungal',
            symptoms='主要危害穗部，初期在小穗和颖壳上出现水渍状淡褐色病斑，后扩展至整个穗部。潮湿时病部产生粉红色霉层。',
            description='小麦赤霉病是世界性病害，不仅造成减产，还产生呕吐毒素等真菌毒素，严重影响小麦品质和人畜安全。',
            causes='由禾谷镰刀菌引起，病菌通过雨水飞溅传播。抽穗扬花期遇连续阴雨天气易暴发流行。',
            prevention_methods='["选用抗病品种", "适期播种，避开扬花期阴雨", "开沟排水，降低田间湿度", "及时清除玉米秸秆等病残体"]',
            treatment_methods='["扬花初期喷洒 50% 多菌灵可湿性粉剂 1000 倍液", "70% 甲基硫菌灵可湿性粉剂 1500 倍液", "25% 氰烯菌酯悬浮剂 2000 倍液", "间隔 5-7 天，连喷 2 次"]',
            suitable_growth_stage='抽穗期、扬花期、灌浆期',
            severity=0.95
        ),
        Disease(
            name='小麦纹枯病',
            scientific_name='Rhizoctonia cerealis',
            code='WD005',
            category='fungal',
            symptoms='主要危害叶鞘和茎秆。叶鞘上出现椭圆形云纹状病斑，边缘褐色，中央淡褐色。茎秆病斑可环绕茎部，导致植株倒伏。',
            description='小麦纹枯病是小麦重要土传病害，主要危害叶鞘和茎基部，严重时造成植株倒伏、枯死。',
            causes='由禾谷丝核菌引起，病菌在土壤中病残体上越冬。适宜温度为 20-25℃，高湿、氮肥过多易发病。',
            prevention_methods='["选用抗病品种", "轮作倒茬，减少菌源", "适期播种，避免早播", "合理施肥，增施磷钾肥", "开沟排水，降低田间湿度"]',
            treatment_methods='["发病初期喷洒 5% 井冈霉素水剂 1000 倍液", "15% 三唑酮可湿性粉剂 1500 倍液", "25% 丙环唑乳油 2000 倍液", "间隔 7-10 天，连喷 2-3 次"]',
            suitable_growth_stage='苗期、拔节期、孕穗期',
            severity=0.65
        )
    ]
    session.add_all(diseases)
    print(f"  ✓ 插入 {len(diseases)} 种病害数据")
    
    # 插入知识图谱数据
    print("\n插入知识图谱数据...")
    knowledge_data = [
        # 病害实体
        KnowledgeGraph(entity='小麦条锈病', entity_type='disease', relation='causes', target_entity='条形柄锈菌', attributes='{"scientific_name": "Puccinia striiformis f. sp. tritici", "severity": 0.9}'),
        KnowledgeGraph(entity='小麦叶锈病', entity_type='disease', relation='causes', target_entity='小麦隐匿柄锈菌', attributes='{"scientific_name": "Puccinia triticina", "severity": 0.7}'),
        KnowledgeGraph(entity='小麦白粉病', entity_type='disease', relation='causes', target_entity='禾本科布氏白粉菌', attributes='{"scientific_name": "Blumeria graminis f. sp. tritici", "severity": 0.6}'),
        KnowledgeGraph(entity='小麦赤霉病', entity_type='disease', relation='causes', target_entity='禾谷镰刀菌', attributes='{"scientific_name": "Fusarium graminearum", "severity": 0.95}'),
        KnowledgeGraph(entity='小麦纹枯病', entity_type='disease', relation='causes', target_entity='禾谷丝核菌', attributes='{"scientific_name": "Rhizoctonia cerealis", "severity": 0.65}'),
        
        # 症状实体
        KnowledgeGraph(entity='鲜黄色条状孢子堆', entity_type='symptom', relation='indicates', target_entity='小麦条锈病', attributes='{"location": "叶片", "color": "鲜黄色"}'),
        KnowledgeGraph(entity='橙红色圆形孢子堆', entity_type='symptom', relation='indicates', target_entity='小麦叶锈病', attributes='{"location": "叶片", "color": "橙红色"}'),
        KnowledgeGraph(entity='白色絮状霉层', entity_type='symptom', relation='indicates', target_entity='小麦白粉病', attributes='{"location": "叶片、叶鞘", "color": "白色"}'),
        KnowledgeGraph(entity='穗部水渍状病斑', entity_type='symptom', relation='indicates', target_entity='小麦赤霉病', attributes='{"location": "穗部", "color": "淡褐色"}'),
        KnowledgeGraph(entity='云纹状病斑', entity_type='symptom', relation='indicates', target_entity='小麦纹枯病', attributes='{"location": "叶鞘、茎秆", "pattern": "云纹状"}'),
        
        # 治疗方法实体
        KnowledgeGraph(entity='三唑酮', entity_type='treatment', relation='treats', target_entity='小麦条锈病', attributes='{"type": "fungicide", "dosage": "1000-1500 倍液"}'),
        KnowledgeGraph(entity='丙环唑', entity_type='treatment', relation='treats', target_entity='小麦叶锈病', attributes='{"type": "fungicide", "dosage": "2000-3000 倍液"}'),
        KnowledgeGraph(entity='烯唑醇', entity_type='treatment', relation='treats', target_entity='小麦白粉病', attributes='{"type": "fungicide", "dosage": "4000-5000 倍液"}'),
        KnowledgeGraph(entity='多菌灵', entity_type='treatment', relation='treats', target_entity='小麦赤霉病', attributes='{"type": "fungicide", "dosage": "1000 倍液"}'),
        KnowledgeGraph(entity='井冈霉素', entity_type='treatment', relation='treats', target_entity='小麦纹枯病', attributes='{"type": "fungicide", "dosage": "1000 倍液"}'),
        
        # 生长阶段实体
        KnowledgeGraph(entity='苗期', entity_type='growth_stage', relation='susceptible_to', target_entity='小麦条锈病', attributes='{"duration": "播种 - 越冬"}'),
        KnowledgeGraph(entity='拔节期', entity_type='growth_stage', relation='susceptible_to', target_entity='小麦叶锈病', attributes='{"duration": "春季返青后"}'),
        KnowledgeGraph(entity='孕穗期', entity_type='growth_stage', relation='susceptible_to', target_entity='小麦白粉病', attributes='{"duration": "抽穗前"}'),
        KnowledgeGraph(entity='抽穗期', entity_type='growth_stage', relation='susceptible_to', target_entity='小麦赤霉病', attributes='{"duration": "穗部抽出"}'),
        KnowledgeGraph(entity='扬花期', entity_type='growth_stage', relation='susceptible_to', target_entity='小麦赤霉病', attributes='{"duration": "开花授粉"}')
    ]
    session.add_all(knowledge_data)
    print(f"  ✓ 插入 {len(knowledge_data)} 条知识图谱数据")
    
    # 插入示例诊断记录
    print("\n插入示例诊断记录...")
    diagnoses = [
        Diagnosis(
            user_id=1,
            disease_id=1,
            image_url='/uploads/diagnosis/20260309_001.jpg',
            symptoms='叶片上出现鲜黄色条状病斑，排列成行',
            disease_name='小麦条锈病',
            confidence=0.9500,
            severity='重度',
            description='典型条锈病症状，病斑呈鲜黄色条状排列',
            recommendations='["立即喷洒 15% 三唑酮可湿性粉剂 1000-1500 倍液", "7 天后复查，必要时再次喷药", "清除田间杂草，减少菌源"]',
            growth_stage='拔节期',
            location='河南省郑州市',
            status='completed'
        ),
        Diagnosis(
            user_id=1,
            disease_id=3,
            image_url='/uploads/diagnosis/20260309_002.jpg',
            symptoms='叶片上有白色絮状霉层',
            disease_name='小麦白粉病',
            confidence=0.8800,
            severity='中度',
            description='叶片表面覆盖白色粉状物，典型白粉病症状',
            recommendations='["喷洒 25% 丙环唑乳油 3000 倍液", "改善田间通风条件", "控制氮肥用量"]',
            growth_stage='孕穗期',
            location='河南省郑州市',
            status='completed'
        ),
        Diagnosis(
            user_id=2,
            disease_id=4,
            image_url='/uploads/diagnosis/20260309_003.jpg',
            symptoms='穗部出现淡褐色病斑，有粉红色霉层',
            disease_name='小麦赤霉病',
            confidence=0.9200,
            severity='重度',
            description='穗部受害，产生典型粉红色霉层，赤霉病症状明显',
            recommendations='["立即喷洒 50% 多菌灵可湿性粉剂 1000 倍液", "5 天后再次喷药", "开沟排水，降低田间湿度"]',
            growth_stage='扬花期',
            location='山东省济南市',
            status='completed'
        ),
        Diagnosis(
            user_id=3,
            disease_id=2,
            image_url='/uploads/diagnosis/20260309_004.jpg',
            symptoms='叶片上有橙红色圆形小斑点',
            disease_name='小麦叶锈病',
            confidence=0.8500,
            severity='轻度',
            description='叶片散生橙红色圆形孢子堆，叶锈病初期症状',
            recommendations='["喷洒 20% 三唑酮硫磺悬浮剂 200 倍液", "加强田间管理，改善通风", "10 天后复查"]',
            growth_stage='拔节期',
            location='河北省石家庄市',
            status='completed'
        ),
        Diagnosis(
            user_id=4,
            disease_id=5,
            image_url='/uploads/diagnosis/20260309_005.jpg',
            symptoms='茎基部叶鞘有云纹状病斑',
            disease_name='小麦纹枯病',
            confidence=0.7800,
            severity='中度',
            description='叶鞘出现典型云纹状病斑，纹枯病症状明显',
            recommendations='["喷洒 5% 井冈霉素水剂 1000 倍液", "开沟排水，降低湿度", "增施磷钾肥，增强抗病力"]',
            growth_stage='拔节期',
            location='安徽省合肥市',
            status='completed'
        )
    ]
    session.add_all(diagnoses)
    print(f"  ✓ 插入 {len(diagnoses)} 条诊断记录")
    
    # 提交事务
    session.commit()
    print("\n✓ 初始数据插入完成！")


def run_migration():
    """
    执行数据库迁移
    
    步骤：
    1. 创建数据库表
    2. 插入初始数据
    3. 验证迁移结果
    """
    print("\n" + "=" * 60)
    print("小麦病害 AI 诊断系统 - 数据库迁移工具")
    print("迁移版本：001_initial")
    print("=" * 60 + "\n")
    
    try:
        # 创建 Session
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # 步骤 1: 创建表
        create_tables()
        
        # 步骤 2: 插入初始数据
        insert_initial_data(session)
        
        # 步骤 3: 验证迁移结果
        print("\n" + "=" * 60)
        print("验证迁移结果...")
        print("=" * 60)
        
        user_count = session.query(User).count()
        disease_count = session.query(Disease).count()
        diagnosis_count = session.query(Diagnosis).count()
        knowledge_count = session.query(KnowledgeGraph).count()
        
        print(f"\n数据统计:")
        print(f"  - users: {user_count} 条")
        print(f"  - diseases: {disease_count} 条")
        print(f"  - diagnoses: {diagnosis_count} 条")
        print(f"  - knowledge_graph: {knowledge_count} 条")
        
        print("\n" + "=" * 60)
        print("✓ 数据库迁移完成！")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ 迁移失败：{str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


def downgrade(session):
    """
    回滚迁移（删除所有数据）
    
    Args:
        session: SQLAlchemy 数据库会话对象
    """
    print("\n⚠ 警告：即将回滚迁移，删除所有数据...")
    confirm = input("确认要删除所有数据吗？(yes/no): ")
    
    if confirm.lower() != 'yes':
        print("已取消回滚操作")
        return
    
    # 删除所有数据（按外键依赖顺序）
    print("删除诊断记录...")
    session.query(Diagnosis).delete()
    print("删除知识图谱数据...")
    session.query(KnowledgeGraph).delete()
    print("删除病害数据...")
    session.query(Disease).delete()
    print("删除用户数据...")
    session.query(User).delete()
    
    session.commit()
    print("✓ 回滚完成")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库迁移工具')
    parser.add_argument('--downgrade', action='store_true', help='回滚迁移（删除所有数据）')
    args = parser.parse_args()
    
    if args.downgrade:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            downgrade(session)
        finally:
            session.close()
    else:
        run_migration()

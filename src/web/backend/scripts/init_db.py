"""
数据库初始化和修复脚本
用于创建/修复数据库表结构
"""
import sys
from pathlib import Path
from sqlalchemy import text

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import Base, engine, SessionLocal, SyncSessionLocal, sync_engine
from app.core.config import settings
from app.models.user import User
from app.models.diagnosis import Diagnosis
from app.models.knowledge import KnowledgeGraph
from app.models.user import User as UserModel

def check_database_connection():
    """检查数据库连接"""
    print("=" * 50)
    print("检查数据库连接...")
    print("=" * 50)
    
    try:
        db = SyncSessionLocal()
        db.execute(text("SELECT 1"))
        print("✅ 数据库连接成功")
        db.close()
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败：{e}")
        return False


def check_tables_exist():
    """检查表是否存在"""
    print("\n" + "=" * 50)
    print("检查数据表...")
    print("=" * 50)
    
    try:
        db = SyncSessionLocal()
        
        # 检查所有表
        tables = ['users', 'diagnoses', 'knowledge_graph']
        for table in tables:
            result = db.execute(text(f"SHOW TABLES LIKE '{table}'"))
            if result.fetchone():
                print(f"✅ 表 {table} 存在")
            else:
                print(f"❌ 表 {table} 不存在")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ 检查表失败：{e}")
        return False


def create_or_repair_tables():
    """创建或修复数据表"""
    print("\n" + "=" * 50)
    print("创建/修复数据表...")
    print("=" * 50)
    
    try:
        # 使用 SQLAlchemy 创建所有表
        Base.metadata.create_all(bind=sync_engine)
        print("✅ 数据表创建/修复成功")
        return True
    except Exception as e:
        print(f"❌ 创建数据表失败：{e}")
        return False


def check_user_model_fields():
    """检查 User 模型字段"""
    print("\n" + "=" * 50)
    print("检查 User 模型字段...")
    print("=" * 50)
    
    try:
        columns = User.__table__.columns
        print("User 模型字段:")
        for col in columns:
            print(f"  - {col.name}: {col.type} (nullable={col.nullable})")
        return True
    except Exception as e:
        print(f"❌ 检查 User 模型失败：{e}")
        return False


def test_user_creation():
    """测试用户创建"""
    print("\n" + "=" * 50)
    print("测试用户创建...")
    print("=" * 50)
    
    try:
        db = SyncSessionLocal()
        
        # 检查是否已存在测试用户
        test_user = db.query(User).filter(User.username == "test_admin").first()
        if test_user:
            print("ℹ️  测试用户已存在，跳过创建")
        else:
            # 创建测试用户
            from app.core.security import get_password_hash
            user = User(
                username="test_admin",
                email="test@example.com",
                password_hash=get_password_hash("test123"),
                role="admin",
                is_active=True
            )
            db.add(user)
            db.commit()
            print("✅ 测试用户创建成功")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ 测试用户创建失败：{e}")
        db.rollback()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("数据库初始化和修复工具")
    print("=" * 50)
    print(f"数据库地址：{settings.DATABASE_URL}")
    print("=" * 50)
    
    # 1. 检查数据库连接
    if not check_database_connection():
        print("\n❌ 数据库连接失败，请检查数据库配置")
        return False
    
    # 2. 检查表是否存在
    check_tables_exist()
    
    # 3. 创建/修复表
    if not create_or_repair_tables():
        print("\n❌ 创建/修复表失败")
        return False
    
    # 4. 重新检查表
    check_tables_exist()
    
    # 5. 检查 User 模型字段
    check_user_model_fields()
    
    # 6. 测试用户创建
    test_user_creation()
    
    print("\n" + "=" * 50)
    print("✅ 数据库初始化和修复完成")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

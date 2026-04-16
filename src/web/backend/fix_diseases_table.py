"""
数据库表结构修复脚本
添加缺失的字段到 diseases 表
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database import sync_engine
from sqlalchemy import text

def fix_diseases_table():
    """修复 diseases 表结构"""
    print("\n=== 修复 diseases 表结构 ===\n")
    
    conn = sync_engine.connect()
    
    try:
        # 1. 添加 code 字段
        print("添加 code 字段...")
        try:
            conn.execute(text("""
                ALTER TABLE diseases 
                ADD COLUMN code VARCHAR(50) UNIQUE NULL COMMENT '疾病编码'
                AFTER scientific_name
            """))
            print("✅ code 字段添加成功")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("ℹ️  code 字段已存在")
            else:
                print(f"❌ 添加 code 字段失败：{e}")
        
        # 2. 添加 causes 字段
        print("添加 causes 字段...")
        try:
            conn.execute(text("""
                ALTER TABLE diseases 
                ADD COLUMN causes TEXT NULL COMMENT '病因'
                AFTER symptoms
            """))
            print("✅ causes 字段添加成功")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("ℹ️  causes 字段已存在")
            else:
                print(f"❌ 添加 causes 字段失败：{e}")
        
        # 3. 添加 severity 字段
        print("添加 severity 字段...")
        try:
            conn.execute(text("""
                ALTER TABLE diseases 
                ADD COLUMN severity FLOAT DEFAULT 0.0 COMMENT '严重程度 (0-1)'
                AFTER image_urls
            """))
            print("✅ severity 字段添加成功")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("ℹ️  severity 字段已存在")
            else:
                print(f"❌ 添加 severity 字段失败：{e}")
        
        conn.commit()
        
        print("\n=== 验证表结构 ===")
        result = conn.execute(text("DESCRIBE diseases"))
        columns = [row[0] for row in result]
        print(f"当前字段列表：{columns}")
        
        required_columns = ['id', 'name', 'scientific_name', 'code', 'category', 
                          'symptoms', 'causes', 'prevention_methods', 
                          'treatment_methods', 'suitable_growth_stage', 
                          'image_urls', 'severity', 'created_at', 'updated_at']
        
        missing = [col for col in required_columns if col not in columns]
        if missing:
            print(f"❌ 缺失字段：{missing}")
        else:
            print("✅ 所有必需字段都存在")
        
    except Exception as e:
        print(f"❌ 修复失败：{e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_diseases_table()

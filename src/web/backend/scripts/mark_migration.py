"""
标记 Alembic 迁移版本为已完成

当表已存在但迁移版本未标记时使用此脚本
"""
from sqlalchemy import create_engine, text

# 数据库连接配置
DATABASE_URL = "mysql+pymysql://root:123456@127.0.0.1:3306/wheat_agent_db"

def main():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 检查 alembic_version 表是否存在
        result = conn.execute(text("SHOW TABLES LIKE 'alembic_version'"))
        if result.fetchone() is None:
            # 创建 alembic_version 表
            conn.execute(text("""
                CREATE TABLE alembic_version (
                    version_num VARCHAR(32) NOT NULL PRIMARY KEY
                )
            """))
            print("创建 alembic_version 表")
        
        # 检查是否已有版本记录
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        row = result.fetchone()
        
        if row is None:
            # 插入版本号
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('001')"))
            print("迁移版本已标记为 001")
        elif row[0] != '001':
            # 更新版本号
            conn.execute(text("UPDATE alembic_version SET version_num = '001'"))
            print(f"迁移版本已从 {row[0]} 更新为 001")
        else:
            print("迁移版本已是 001，无需更新")
        
        conn.commit()
    
    # 验证表是否存在
    print("\n验证认证相关表:")
    tables = ['password_reset_tokens', 'refresh_tokens', 'login_attempts', 'user_sessions']
    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(text(f"SHOW TABLES LIKE '{table}'"))
            if result.fetchone():
                print(f"  ✅ {table} - 存在")
            else:
                print(f"  ❌ {table} - 不存在")

if __name__ == "__main__":
    main()

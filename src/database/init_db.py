"""
数据库初始化脚本
执行 init.sql 文件中的 SQL 语句来初始化数据库
"""
import pymysql
import os

# 数据库连接配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4'
}

def read_sql_file(file_path):
    """读取 SQL 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql_file(cursor, sql_file_path):
    """执行 SQL 文件"""
    # 读取 SQL 文件
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割 SQL 语句（按分号分割）
    statements = sql_content.split(';')
    
    success_count = 0
    error_count = 0
    
    for statement in statements:
        statement = statement.strip()
        if not statement or statement.startswith('--'):
            continue
        
        try:
            cursor.execute(statement)
            success_count += 1
        except Exception as e:
            # 忽略一些非关键错误
            if 'ERROR 1064' in str(e):
                print(f"❌ SQL 语法错误：{e}")
                error_count += 1
            elif 'ERROR 1007' in str(e) or 'ERROR 1008' in str(e):
                # 数据库已存在，可以忽略
                pass
            else:
                print(f"⚠️  执行 SQL 时出错：{e}")
    
    return success_count, error_count

def main():
    """主函数"""
    print("=" * 60)
    print("IWDDA 数据库初始化")
    print("=" * 60)
    
    # 获取 SQL 文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'init.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL 文件不存在：{sql_file}")
        return
    
    print(f"✓ SQL 文件：{sql_file}")
    
    try:
        # 连接数据库
        print("\n[1] 连接 MySQL 数据库...")
        connection = pymysql.connect(**DB_CONFIG)
        
        if connection:
            print("✓ 数据库连接成功")
            
            # 创建游标
            cursor = connection.cursor()
            
            # 执行 SQL 文件
            print("\n[2] 执行 SQL 初始化脚本...")
            success, errors = execute_sql_file(cursor, sql_file)
            
            # 提交事务
            connection.commit()
            
            print(f"\n✓ 执行完成：成功 {success} 条，错误 {errors} 条")
            
            # 查询统计信息
            print("\n[3] 查询统计信息...")
            
            # 查询用户数
            cursor.execute("SELECT COUNT(*) FROM wheat_agent_db.users")
            user_count = cursor.fetchone()[0]
            print(f"✓ 用户数：{user_count}")
            
            # 查询病害数
            cursor.execute("SELECT COUNT(*) FROM wheat_agent_db.diseases")
            disease_count = cursor.fetchone()[0]
            print(f"✓ 病害数：{disease_count}")
            
            # 查询知识图谱条目数
            cursor.execute("SELECT COUNT(*) FROM wheat_agent_db.knowledge_graph")
            kg_count = cursor.fetchone()[0]
            print(f"✓ 知识图谱条目数：{kg_count}")
            
            print("\n" + "=" * 60)
            print("数据库初始化完成！")
            print("=" * 60)
            
    except pymysql.Error as e:
        print(f"\n❌ 数据库错误：{e}")
    except Exception as e:
        print(f"\n❌ 未知错误：{e}")
    finally:
        if 'connection' in locals() and connection:
            cursor.close()
            connection.close()
            print("\n✓ 数据库连接已关闭")

if __name__ == "__main__":
    main()

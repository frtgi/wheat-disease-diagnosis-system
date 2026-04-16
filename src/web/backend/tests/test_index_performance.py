"""
数据库索引性能测试脚本
测试索引优化前后的查询性能对比
"""
import asyncio
import time
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 数据库连接配置
DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/wheat_agent_db"

async def test_query_performance():
    """测试查询性能"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    print("=" * 60)
    print("数据库索引性能测试")
    print("=" * 60)
    
    async with async_session() as session:
        # 测试 1: 用户查询性能
        print("\n[测试 1] 按用户名查询用户")
        start = time.time()
        for _ in range(100):
            result = await session.execute(
                text("SELECT * FROM users WHERE username = :username"),
                {"username": "farmer_zhang"}
            )
            _ = result.fetchall()
        elapsed = time.time() - start
        print(f"  100 次查询耗时：{elapsed*1000:.2f}ms")
        print(f"  平均每次查询：{elapsed*10:.4f}ms")
        
        # 测试 2: 诊断记录查询（按用户）
        print("\n[测试 2] 按用户 ID 查询诊断记录")
        start = time.time()
        for _ in range(100):
            result = await session.execute(
                text("SELECT * FROM diagnosis_records WHERE user_id = :user_id ORDER BY created_at DESC LIMIT 10"),
                {"user_id": 1}
            )
            _ = result.fetchall()
        elapsed = time.time() - start
        print(f"  100 次查询耗时：{elapsed*1000:.2f}ms")
        print(f"  平均每次查询：{elapsed*10:.4f}ms")
        
        # 测试 3: 诊断记录查询（按时间）
        print("\n[测试 3] 按时间范围查询诊断记录")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        start = time.time()
        for _ in range(100):
            result = await session.execute(
                text("""
                    SELECT * FROM diagnosis_records 
                    WHERE created_at BETWEEN :start_date AND :end_date
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            _ = result.fetchall()
        elapsed = time.time() - start
        print(f"  100 次查询耗时：{elapsed*1000:.2f}ms")
        print(f"  平均每次查询：{elapsed*10:.4f}ms")
        
        # 测试 4: 知识图谱查询
        print("\n[测试 4] 知识图谱实体查询")
        start = time.time()
        for _ in range(100):
            result = await session.execute(
                text("""
                    SELECT * FROM knowledge_graph 
                    WHERE entity_type = :entity_type AND entity = :entity
                """),
                {"entity_type": "disease", "entity": "白粉病"}
            )
            _ = result.fetchall()
        elapsed = time.time() - start
        print(f"  100 次查询耗时：{elapsed*1000:.2f}ms")
        print(f"  平均每次查询：{elapsed*10:.4f}ms")
        
        # 测试 5: 病害统计查询
        print("\n[测试 5] 病害统计查询")
        start = time.time()
        for _ in range(50):
            result = await session.execute(
                text("""
                    SELECT disease_name, COUNT(*) as total_count, AVG(confidence) as avg_confidence
                    FROM diagnosis_records
                    GROUP BY disease_name
                """)
            )
            _ = result.fetchall()
        elapsed = time.time() - start
        print(f"  50 次查询耗时：{elapsed*1000:.2f}ms")
        print(f"  平均每次查询：{elapsed*20:.4f}ms")
        
        # 测试 6: 复合查询（用户 + 时间）
        print("\n[测试 6] 复合查询（用户 ID + 时间范围）")
        start = time.time()
        for _ in range(100):
            result = await session.execute(
                text("""
                    SELECT * FROM diagnosis_records 
                    WHERE user_id = :user_id 
                    AND created_at BETWEEN :start_date AND :end_date
                    ORDER BY created_at DESC
                """),
                {"user_id": 1, "start_date": start_date, "end_date": end_date}
            )
            _ = result.fetchall()
        elapsed = time.time() - start
        print(f"  100 次查询耗时：{elapsed*1000:.2f}ms")
        print(f"  平均每次查询：{elapsed*10:.4f}ms")
    
    print("\n" + "=" * 60)
    print("性能测试完成！")
    print("=" * 60)

async def show_index_info():
    """显示索引信息"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    print("\n" + "=" * 60)
    print("数据库索引信息")
    print("=" * 60)
    
    async with async_session() as session:
        # 获取所有表的索引信息
        tables = ['users', 'diagnosis_records', 'diseases', 'knowledge_graph']
        
        for table in tables:
            print(f"\n表：{table}")
            print("-" * 60)
            result = await session.execute(text(f"SHOW INDEX FROM {table}"))
            indexes = result.fetchall()
            
            current_index = None
            for idx in indexes:
                index_name = idx[2]
                if index_name != current_index:
                    current_index = index_name
                    column_name = idx[4]
                    print(f"  索引：{index_name:30s} 列：{column_name}")
                else:
                    column_name = idx[4]
                    print(f"{' ' * 35} 列：{column_name}")

async def main():
    """主函数"""
    try:
        # 显示索引信息
        await show_index_info()
        
        # 运行性能测试
        await test_query_performance()
        
    except Exception as e:
        print(f"\n错误：{e}")
        print("请确保数据库已启动并且索引已创建")

if __name__ == "__main__":
    asyncio.run(main())

"""
数据库索引初始化脚本
创建优化索引以提升查询性能
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from app.core.database import SyncSessionLocal
from app.core.index_optimizer import IndexOptimizer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_indexes():
    """创建数据库索引"""
    db = SyncSessionLocal()
    
    try:
        logger.info("="*60)
        logger.info("🚀 开始创建数据库索引")
        logger.info("="*60)
        
        optimizer = IndexOptimizer(db)
        
        logger.info("\n📊 1. 分析现有索引...")
        
        for table_name in optimizer.RECOMMENDED_INDEXES.keys():
            analysis = optimizer.analyze_table_indexes(table_name)
            logger.info(f"\n表 {table_name}:")
            logger.info(f"  - 现有索引数：{analysis['total_existing']}")
            logger.info(f"  - 缺失索引数：{analysis['total_missing']}")
            
            if analysis['missing_indexes']:
                logger.info("  - 缺失的索引：")
                for idx in analysis['missing_indexes']:
                    logger.info(f"    * {idx['name']} on ({', '.join(idx['columns'])})")
        
        logger.info("\n📊 2. 创建缺失索引...")
        results = optimizer.optimize_all_tables()
        
        total_created = 0
        total_failed = 0
        
        for table_name, result in results.items():
            created = len(result['created'])
            failed = len(result['failed'])
            total_created += created
            total_failed += failed
            
            if created > 0:
                logger.info(f"\n✅ 表 {table_name} 创建了 {created} 个索引：")
                for idx_name in result['created']:
                    logger.info(f"  - {idx_name}")
            
            if failed > 0:
                logger.warning(f"\n⚠️  表 {table_name} 有 {failed} 个索引创建失败：")
                for idx_name in result['failed']:
                    logger.warning(f"  - {idx_name}")
        
        logger.info("\n" + "="*60)
        logger.info("📋 索引创建总结")
        logger.info("="*60)
        logger.info(f"✅ 成功创建索引：{total_created} 个")
        
        if total_failed > 0:
            logger.warning(f"⚠️  创建失败索引：{total_failed} 个")
        else:
            logger.info("✅ 所有索引创建成功！")
        
        logger.info("\n📊 3. 验证索引创建...")
        
        for table_name in optimizer.RECOMMENDED_INDEXES.keys():
            indexes = optimizer.get_existing_indexes(table_name)
            logger.info(f"\n表 {table_name} 现有索引：")
            for idx in indexes:
                columns = ", ".join(idx.get("column_names", []))
                logger.info(f"  - {idx['name']} on ({columns})")
        
    except Exception as e:
        logger.error(f"❌ 创建索引失败：{e}")
        db.rollback()
        raise
    finally:
        db.close()


def analyze_query_performance():
    """分析查询性能"""
    db = SyncSessionLocal()
    
    try:
        logger.info("\n" + "="*60)
        logger.info("🔍 分析查询性能")
        logger.info("="*60)
        
        optimizer = IndexOptimizer(db)
        
        test_queries = [
            "SELECT * FROM diagnoses WHERE user_id = 1",
            "SELECT * FROM diagnoses WHERE user_id = 1 AND created_at > '2026-01-01'",
            "SELECT * FROM diseases WHERE category = 'fungal'",
            "SELECT * FROM diseases WHERE name LIKE '%锈病%'",
        ]
        
        for query in test_queries:
            logger.info(f"\n分析查询：{query}")
            analysis = optimizer.analyze_query_performance(query)
            
            if "error" in analysis:
                logger.error(f"  ❌ 分析失败：{analysis['error']}")
            else:
                logger.info(f"  ✅ 使用索引：{analysis['using_index']}")
                if analysis['analysis']:
                    first_row = analysis['analysis'][0]
                    logger.info(f"  - 查询类型：{first_row.get('type', 'N/A')}")
                    logger.info(f"  - 可能的索引：{first_row.get('possible_keys', 'N/A')}")
                    logger.info(f"  - 实际使用的索引：{first_row.get('key', 'N/A')}")
                    logger.info(f"  - 扫描行数：{first_row.get('rows', 'N/A')}")
    
    except Exception as e:
        logger.error(f"❌ 分析失败：{e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_indexes()
    analyze_query_performance()

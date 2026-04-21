"""
数据库索引优化模块
提供索引分析、创建和管理功能
"""
import logging
import re
from typing import List, Dict, Any
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class IndexOptimizer:
    """
    数据库索引优化器
    
    功能：
    1. 分析现有索引
    2. 推荐缺失索引
    3. 创建优化索引
    4. 检测冗余索引
    """
    
    # 推荐的索引配置
    RECOMMENDED_INDEXES = {
        "users": [
            {"columns": ["username"], "name": "idx_users_username", "unique": True},
            {"columns": ["email"], "name": "idx_users_email", "unique": True},
            {"columns": ["is_active"], "name": "idx_users_is_active"},
            {"columns": ["created_at"], "name": "idx_users_created_at"},
        ],
        "diagnoses": [
            {"columns": ["user_id"], "name": "idx_diagnoses_user_id"},
            {"columns": ["disease_id"], "name": "idx_diagnoses_disease_id"},
            {"columns": ["disease_name"], "name": "idx_diagnoses_disease_name"},
            {"columns": ["status"], "name": "idx_diagnoses_status"},
            {"columns": ["created_at"], "name": "idx_diagnoses_created_at"},
            {"columns": ["user_id", "created_at"], "name": "idx_diagnoses_user_created"},
            {"columns": ["user_id", "status"], "name": "idx_diagnoses_user_status"},
            {"columns": ["disease_name", "created_at"], "name": "idx_diagnoses_disease_created"},
        ],
        "diseases": [
            {"columns": ["name"], "name": "idx_diseases_name"},
            {"columns": ["category"], "name": "idx_diseases_category"},
            {"columns": ["code"], "name": "idx_diseases_code", "unique": True},
        ],
        "knowledge_graph": [
            {"columns": ["entity"], "name": "idx_knowledge_entity"},
            {"columns": ["entity_type"], "name": "idx_knowledge_entity_type"},
            {"columns": ["relation"], "name": "idx_knowledge_relation"},
            {"columns": ["entity_type", "entity"], "name": "idx_knowledge_type_entity"},
        ],
    }
    
    def __init__(self, db: Session):
        """
        初始化索引优化器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.inspector = inspect(db.bind)
    
    def get_existing_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表的现有索引
        
        Args:
            table_name: 表名
        
        Returns:
            索引列表
        """
        try:
            indexes = self.inspector.get_indexes(table_name)
            return indexes
        except Exception as e:
            logger.error(f"获取表 {table_name} 的索引失败：{e}")
            return []
    
    def analyze_table_indexes(self, table_name: str) -> Dict[str, Any]:
        """
        分析表的索引情况
        
        Args:
            table_name: 表名
        
        Returns:
            分析结果
        """
        existing = self.get_existing_indexes(table_name)
        existing_names = {idx["name"] for idx in existing}
        
        recommended = self.RECOMMENDED_INDEXES.get(table_name, [])
        missing = []
        
        for idx in recommended:
            if idx["name"] not in existing_names:
                missing.append(idx)
        
        return {
            "table": table_name,
            "existing_indexes": existing,
            "missing_indexes": missing,
            "total_existing": len(existing),
            "total_missing": len(missing)
        }
    
    @staticmethod
    def _validate_identifier(name: str) -> str:
        """
        验证 SQL 标识符是否合法

        仅允许字母、数字和下划线，防止 SQL 注入

        参数:
            name: 待验证的标识符

        返回:
            验证后的标识符

        异常:
            ValueError: 标识符不合法
        """
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            raise ValueError(f"非法的 SQL 标识符: {name}")
        return name

    def create_index(self, table_name: str, columns: List[str], index_name: str, unique: bool = False) -> bool:
        """
        创建索引

        参数:
            table_name: 表名
            columns: 列名列表
            index_name: 索引名称
            unique: 是否唯一索引

        返回:
            是否创建成功
        """
        try:
            table_name = self._validate_identifier(table_name)
            index_name = self._validate_identifier(index_name)
            columns = [self._validate_identifier(col) for col in columns]

            unique_str = "UNIQUE" if unique else ""
            columns_str = ", ".join(columns)

            sql = f"""
            CREATE {unique_str} INDEX {index_name} 
            ON {table_name} ({columns_str})
            """

            self.db.execute(text(sql))
            self.db.commit()

            logger.info(f"成功创建索引：{index_name} on {table_name}({columns_str})")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建索引失败 {index_name}：{e}")
            return False
    
    def create_missing_indexes(self, table_name: str) -> Dict[str, Any]:
        """
        创建表的缺失索引
        
        Args:
            table_name: 表名
        
        Returns:
            创建结果
        """
        analysis = self.analyze_table_indexes(table_name)
        results = {
            "created": [],
            "failed": []
        }
        
        for idx in analysis["missing_indexes"]:
            success = self.create_index(
                table_name=table_name,
                columns=idx["columns"],
                index_name=idx["name"],
                unique=idx.get("unique", False)
            )
            
            if success:
                results["created"].append(idx["name"])
            else:
                results["failed"].append(idx["name"])
        
        return results
    
    def optimize_all_tables(self) -> Dict[str, Any]:
        """
        优化所有表的索引
        
        Returns:
            优化结果
        """
        results = {}
        
        for table_name in self.RECOMMENDED_INDEXES.keys():
            logger.info(f"正在优化表：{table_name}")
            results[table_name] = self.create_missing_indexes(table_name)
        
        return results
    
    def get_index_usage_stats(self, table_name: str) -> Dict[str, Any]:
        """
        获取索引使用统计（MySQL 特定）
        
        Args:
            table_name: 表名
        
        Returns:
            使用统计
        """
        try:
            sql = text("""
                SELECT 
                    INDEX_NAME,
                    CARDINALITY,
                    SEQ_IN_INDEX,
                    COLUMN_NAME
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = :table_name
                ORDER BY INDEX_NAME, SEQ_IN_INDEX
            """)
            
            result = self.db.execute(sql, {"table_name": table_name})
            rows = result.fetchall()
            
            stats = {}
            for row in rows:
                index_name = row[0]
                if index_name not in stats:
                    stats[index_name] = {
                        "cardinality": row[1],
                        "columns": []
                    }
                stats[index_name]["columns"].append(row[3])
            
            return stats
            
        except Exception as e:
            logger.error(f"获取索引使用统计失败：{e}")
            return {}
    
    def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """
        分析查询性能（使用 EXPLAIN）

        仅允许 SELECT 查询进行性能分析，防止 SQL 注入和未授权修改。

        参数:
            query: SQL 查询语句（仅允许 SELECT）

        返回:
            性能分析结果
        """
        upper_query = query.strip().upper()
        forbidden_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']
        for keyword in forbidden_keywords:
            if keyword in upper_query:
                logger.error(f"查询性能分析拒绝执行包含 {keyword} 的语句")
                return {"error": f"仅允许 SELECT 查询进行性能分析，拒绝包含 {keyword} 的语句"}

        if not upper_query.startswith('SELECT'):
            logger.error("查询性能分析仅允许 SELECT 语句")
            return {"error": "仅允许 SELECT 查询进行性能分析"}

        try:
            explain_sql = text(f"EXPLAIN {query}")
            result = self.db.execute(explain_sql)
            rows = result.fetchall()
            
            analysis = []
            for row in rows:
                analysis.append({
                    "id": row[0],
                    "select_type": row[1],
                    "table": row[2],
                    "type": row[3],
                    "possible_keys": row[4],
                    "key": row[5],
                    "key_len": row[6],
                    "ref": row[7],
                    "rows": row[8],
                    "Extra": row[9]
                })
            
            return {
                "query": query,
                "analysis": analysis,
                "using_index": any(row["key"] for row in analysis)
            }
            
        except Exception as e:
            logger.error(f"分析查询性能失败：{e}")
            return {"error": str(e)}


def optimize_database_indexes(db: Session) -> Dict[str, Any]:
    """
    优化数据库索引的便捷函数
    
    Args:
        db: 数据库会话
    
    Returns:
        优化结果
    """
    optimizer = IndexOptimizer(db)
    return optimizer.optimize_all_tables()

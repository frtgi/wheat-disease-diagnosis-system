"""
Alembic 环境配置模块
配置数据库连接和迁移运行环境
"""
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.database import Base
from app.models import User, Disease, Diagnosis, KnowledgeGraph
from app.models.auth import PasswordResetToken, RefreshToken, LoginAttempt, UserSession

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    """
    获取数据库连接 URL
    
    返回:
        str: 同步数据库连接 URL
    """
    return (
        f"mysql+pymysql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}"
        f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
        f"?charset=utf8mb4"
    )


def run_migrations_offline() -> None:
    """
    在 'offline' 模式下运行迁移
    
    此模式生成 SQL 脚本而不连接数据库，适用于：
    - 生成 SQL 脚本供 DBA 审核
    - 在无法直接连接数据库的环境中执行迁移
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在 'online' 模式下运行迁移
    
    此模式直接连接数据库执行迁移，适用于：
    - 开发环境
    - 有直接数据库访问权限的生产环境
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

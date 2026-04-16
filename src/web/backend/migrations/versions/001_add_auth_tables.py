"""add auth tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

创建认证相关数据表：
- password_reset_tokens: 密码重置令牌表
- refresh_tokens: 刷新令牌表
- login_attempts: 登录尝试记录表
- user_sessions: 用户会话表
- 为 users 表添加缺失的索引
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库架构
    
    创建以下表：
    - password_reset_tokens: 存储密码重置令牌
    - refresh_tokens: 存储刷新令牌
    - login_attempts: 记录登录尝试
    - user_sessions: 管理用户会话
    
    添加以下索引：
    - users 表的 email 索引（如不存在）
    """
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='令牌 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='关联用户 ID'),
        sa.Column('token', sa.String(255), nullable=False, comment='重置令牌'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='过期时间'),
        sa.Column('used', sa.Boolean(), nullable=True, default=False, comment='是否已使用'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_comment='密码重置令牌表'
    )
    op.create_index(op.f('ix_password_reset_tokens_id'), 'password_reset_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_password_reset_tokens_user_id'), 'password_reset_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_password_reset_tokens_token'), 'password_reset_tokens', ['token'], unique=True)
    op.create_index('ix_password_reset_tokens_user_expires', 'password_reset_tokens', ['user_id', 'expires_at'])

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='令牌 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='关联用户 ID'),
        sa.Column('token', sa.String(255), nullable=False, comment='刷新令牌'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='过期时间'),
        sa.Column('revoked', sa.Boolean(), nullable=True, default=False, comment='是否已撤销'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_comment='刷新令牌表'
    )
    op.create_index(op.f('ix_refresh_tokens_id'), 'refresh_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token'), 'refresh_tokens', ['token'], unique=True)
    op.create_index('ix_refresh_tokens_user_expires', 'refresh_tokens', ['user_id', 'expires_at'])

    op.create_table(
        'login_attempts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='记录 ID'),
        sa.Column('username', sa.String(50), nullable=False, comment='尝试登录的用户名'),
        sa.Column('ip_address', sa.String(45), nullable=False, comment='登录 IP 地址'),
        sa.Column('success', sa.Boolean(), nullable=True, default=False, comment='是否登录成功'),
        sa.Column('timestamp', sa.DateTime(), nullable=True, comment='尝试时间'),
        sa.PrimaryKeyConstraint('id'),
        mysql_comment='登录尝试记录表'
    )
    op.create_index(op.f('ix_login_attempts_id'), 'login_attempts', ['id'], unique=False)
    op.create_index(op.f('ix_login_attempts_username'), 'login_attempts', ['username'], unique=False)
    op.create_index(op.f('ix_login_attempts_ip_address'), 'login_attempts', ['ip_address'], unique=False)
    op.create_index(op.f('ix_login_attempts_timestamp'), 'login_attempts', ['timestamp'], unique=False)
    op.create_index('ix_login_attempts_ip_timestamp', 'login_attempts', ['ip_address', 'timestamp'])
    op.create_index('ix_login_attempts_username_timestamp', 'login_attempts', ['username', 'timestamp'])

    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='会话 ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='关联用户 ID'),
        sa.Column('session_token', sa.String(255), nullable=False, comment='会话令牌'),
        sa.Column('device_info', sa.Text(), nullable=True, comment='设备信息（User-Agent 等）'),
        sa.Column('ip_address', sa.String(45), nullable=True, comment='登录 IP 地址'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='会话过期时间'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True, comment='会话是否活跃'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_comment='用户会话表'
    )
    op.create_index(op.f('ix_user_sessions_id'), 'user_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_sessions_session_token'), 'user_sessions', ['session_token'], unique=True)
    op.create_index('ix_user_sessions_user_expires', 'user_sessions', ['user_id', 'expires_at'])
    op.create_index('ix_user_sessions_user_active', 'user_sessions', ['user_id', 'is_active'])

    conn = op.get_bind()
    result = conn.execute(sa.text("SHOW INDEX FROM users WHERE Key_name = 'ix_users_email'"))
    if not result.fetchone():
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    """
    回滚数据库架构
    
    删除以下表：
    - user_sessions
    - login_attempts
    - refresh_tokens
    - password_reset_tokens
    """
    op.drop_index('ix_user_sessions_user_active', table_name='user_sessions')
    op.drop_index('ix_user_sessions_user_expires', table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_session_token'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_user_id'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_id'), table_name='user_sessions')
    op.drop_table('user_sessions')

    op.drop_index('ix_login_attempts_username_timestamp', table_name='login_attempts')
    op.drop_index('ix_login_attempts_ip_timestamp', table_name='login_attempts')
    op.drop_index(op.f('ix_login_attempts_timestamp'), table_name='login_attempts')
    op.drop_index(op.f('ix_login_attempts_ip_address'), table_name='login_attempts')
    op.drop_index(op.f('ix_login_attempts_username'), table_name='login_attempts')
    op.drop_index(op.f('ix_login_attempts_id'), table_name='login_attempts')
    op.drop_table('login_attempts')

    op.drop_index('ix_refresh_tokens_user_expires', table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_id'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')

    op.drop_index('ix_password_reset_tokens_user_expires', table_name='password_reset_tokens')
    op.drop_index(op.f('ix_password_reset_tokens_token'), table_name='password_reset_tokens')
    op.drop_index(op.f('ix_password_reset_tokens_user_id'), table_name='password_reset_tokens')
    op.drop_index(op.f('ix_password_reset_tokens_id'), table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')

"""
认证增强数据模型
定义密码重置、刷新令牌、登录尝试、用户会话等表结构
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from ..core.database import Base


class PasswordResetToken(Base):
    """
    密码重置令牌模型类

    对应数据库表：password_reset_tokens
    存储用户密码重置请求的令牌信息
    """

    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="令牌 ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="关联用户 ID")
    token = Column(String(255), unique=True, nullable=False, index=True, comment="重置令牌")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    used = Column(Boolean, default=False, comment="是否已使用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系 - 令牌属于某个用户
    user = relationship("User", backref="password_reset_tokens")

    # 复合索引 - 防止同一用户重复有效令牌
    __table_args__ = (
        Index("ix_password_reset_tokens_user_expires", "user_id", "expires_at"),
        Index('ix_pwdreset_user_token_unique', 'user_id', 'token', unique=True),
    )


class RefreshToken(Base):
    """
    刷新令牌模型类

    对应数据库表：refresh_tokens
    存储用户刷新令牌，用于无感刷新访问令牌
    """

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="令牌 ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="关联用户 ID")
    token = Column(String(128), unique=True, nullable=False, index=True, comment="刷新令牌（SHA256 哈希存储）")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    revoked = Column(Boolean, default=False, comment="是否已撤销")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系 - 令牌属于某个用户
    user = relationship("User", backref="refresh_tokens")

    # 复合索引 - 防止同一用户重复有效令牌
    __table_args__ = (
        Index("ix_refresh_tokens_user_expires", "user_id", "expires_at"),
        Index('ix_reftoken_user_token_unique', 'user_id', 'token', unique=True),
    )


class LoginAttempt(Base):
    """
    登录尝试记录模型类

    对应数据库表：login_attempts
    记录用户登录尝试，用于安全审计和防暴力破解
    保留期限：90 天，建议通过 MySQL EVENT 或应用层定时任务清理
    """

    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="记录 ID")
    username = Column(String(50), nullable=False, index=True, comment="尝试登录的用户名")
    ip_address = Column(String(45), nullable=False, index=True, comment="登录 IP 地址")
    success = Column(Boolean, default=False, comment="是否登录成功")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, comment="尝试时间")

    # 复合索引 - 用于快速查询某 IP 的登录尝试次数
    __table_args__ = (
        Index("ix_login_attempts_ip_timestamp", "ip_address", "timestamp"),
        Index("ix_login_attempts_username_timestamp", "username", "timestamp"),
    )


class UserSession(Base):
    """
    用户会话模型类

    对应数据库表：user_sessions
    管理用户登录会话，支持多设备登录管理
    """

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="会话 ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="关联用户 ID")
    session_token = Column(String(255), unique=True, nullable=False, index=True, comment="会话令牌")
    device_info = Column(Text, nullable=True, comment="设备信息（User-Agent 等）")
    ip_address = Column(String(45), nullable=True, comment="登录 IP 地址")
    expires_at = Column(DateTime, nullable=False, comment="会话过期时间")
    is_active = Column(Boolean, default=True, comment="会话是否活跃")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系 - 会话属于某个用户
    user = relationship("User", backref="user_sessions")

    # 复合索引
    __table_args__ = (
        Index("ix_user_sessions_user_expires", "user_id", "expires_at"),
        Index("ix_user_sessions_user_active", "user_id", "is_active"),
    )

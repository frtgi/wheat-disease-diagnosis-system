"""
认证服务
处理用户注册、登录、认证等业务逻辑
"""
import secrets
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status

from ..models.user import User
from ..models.auth import PasswordResetToken, RefreshToken, LoginAttempt, UserSession
from ..core.security import verify_password, get_password_hash
from .cache import cache_service


MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
PASSWORD_RESET_EXPIRE_HOURS = 1
REFRESH_TOKEN_EXPIRE_DAYS = 7
SESSION_EXPIRE_DAYS = 7


def _hash_token(token: str) -> str:
    """
    对令牌进行 SHA-256 哈希

    参数:
        token: 原始令牌字符串

    返回:
        哈希后的十六进制字符串
    """
    return hashlib.sha256(token.encode()).hexdigest()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    认证用户
    
    参数:
        db: 数据库会话
        username: 用户名或邮箱
        password: 密码
    
    返回:
        用户对象，认证失败返回 None
    """
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def create_user(db: Session, username: str, email: str, password: str) -> User:
    """
    创建新用户
    
    执行用户创建操作，包括密码哈希处理和数据库持久化。
    此函数假设调用方已进行唯一性预检查，仅作为防御性编程的二次验证。
    
    参数:
        db: 数据库会话
        username: 用户名（3-50个字符）
        email: 邮箱地址
        password: 明文密码（将被哈希存储）
    
    返回:
        User: 创建成功的用户对象
    
    异常:
        HTTPException: 用户名或邮箱已存在时返回 409 CONFLICT
        ValueError: 密码哈希生成失败
    """
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该用户名已被使用，请选择其他用户名"
        )
    
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已被注册，请使用其他邮箱"
        )
    
    try:
        hashed_password = get_password_hash(password)
    except ValueError as e:
        raise ValueError(f"密码哈希生成失败: {e}")
    
    user = User(
        username=username,
        email=email,
        password_hash=hashed_password
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    根据 ID 获取用户
    
    参数:
        db: 数据库会话
        user_id: 用户 ID
    
    返回:
        用户对象，不存在返回 None
    """
    return db.query(User).filter(User.id == user_id).first()


async def get_user_by_id_cached(db: Session, user_id: int) -> Optional[User]:
    """
    根据 ID 获取用户（带缓存）
    
    优先从 Redis 缓存获取用户信息，缓存未命中时查询数据库并更新缓存。
    
    参数:
        db: 数据库会话
        user_id: 用户 ID
    
    返回:
        用户对象，不存在返回 None
    """
    try:
        cached_user = await cache_service.get_user_info(user_id)
        if cached_user:
            user = User(
                id=cached_user.get("id"),
                username=cached_user.get("username"),
                email=cached_user.get("email"),
                role=cached_user.get("role"),
                is_active=cached_user.get("is_active", True)
            )
            return user
    except Exception:
        pass
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if user:
        try:
            await cache_service.set_user_info(user_id, {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            })
        except Exception:
            pass
    
    return user


async def invalidate_user_cache(user_id: int) -> bool:
    """
    使用户缓存失效
    
    参数:
        user_id: 用户 ID
    
    返回:
        是否成功
    """
    try:
        return await cache_service.invalidate_user_cache(user_id)
    except Exception:
        return False



def create_password_reset_token(db: Session, email: str) -> Optional[str]:
    """
    创建密码重置令牌

    生成随机令牌并在数据库中存储其 SHA-256 哈希值，
    原始令牌仅通过邮件发送给用户，不持久化存储。

    参数:
        db: 数据库会话
        email: 用户邮箱

    返回:
        重置令牌（原始值），用户不存在返回 None
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)
    
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=_hash_token(token),
        expires_at=expires_at,
        used=False
    )
    db.add(reset_token)
    db.commit()
    
    return token


def verify_password_reset_token(db: Session, token: str) -> Optional[User]:
    """
    验证密码重置令牌

    对用户提供的令牌进行 SHA-256 哈希后与数据库中存储的哈希值比较。

    参数:
        db: 数据库会话
        token: 重置令牌（原始值）

    返回:
        用户对象，验证失败返回 None
    """
    reset_token = db.query(PasswordResetToken).filter(
        and_(
            PasswordResetToken.token == _hash_token(token),
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > datetime.utcnow()
        )
    ).first()
    
    if not reset_token:
        return None
    
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    return user


def mark_password_reset_token_used(db: Session, token: str) -> bool:
    """
    标记密码重置令牌为已使用

    通过令牌的 SHA-256 哈希值查找并标记为已使用。

    参数:
        db: 数据库会话
        token: 重置令牌（原始值）

    返回:
        是否成功标记
    """
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == _hash_token(token)
    ).first()
    
    if not reset_token:
        return False
    
    reset_token.used = True
    db.commit()
    return True


def create_refresh_token(db: Session, user_id: int) -> str:
    """
    创建刷新令牌
    
    参数:
        db: 数据库会话
        user_id: 用户 ID
    
    返回:
        刷新令牌
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    refresh_token = RefreshToken(
        user_id=user_id,
        token=_hash_token(token),
        expires_at=expires_at,
        revoked=False
    )
    db.add(refresh_token)
    db.commit()
    
    return token


def verify_refresh_token(db: Session, token: str) -> Optional[User]:
    """
    验证刷新令牌
    
    参数:
        db: 数据库会话
        token: 刷新令牌
    
    返回:
        用户对象，验证失败返回 None
    """
    token_hash = _hash_token(token)
    refresh_token = db.query(RefreshToken).filter(
        and_(
            RefreshToken.token == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > datetime.utcnow()
        )
    ).first()
    
    if not refresh_token:
        refresh_token = db.query(RefreshToken).filter(
            and_(
                RefreshToken.token == token,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > datetime.utcnow()
            )
        ).first()
    
    if not refresh_token:
        return None
    
    user = db.query(User).filter(User.id == refresh_token.user_id).first()
    return user


def revoke_refresh_token(db: Session, token: str) -> bool:
    """
    撤销刷新令牌
    
    参数:
        db: 数据库会话
        token: 刷新令牌
    
    返回:
        是否成功撤销
    """
    token_hash = _hash_token(token)
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token_hash
    ).first()
    
    if not refresh_token:
        refresh_token = db.query(RefreshToken).filter(
            RefreshToken.token == token
        ).first()
    
    if not refresh_token:
        return False
    
    refresh_token.revoked = True
    db.commit()
    return True


def revoke_all_user_refresh_tokens(db: Session, user_id: int) -> int:
    """
    撤销用户所有刷新令牌
    
    参数:
        db: 数据库会话
        user_id: 用户 ID
    
    返回:
        撤销的令牌数量
    """
    count = db.query(RefreshToken).filter(
        and_(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False)
        )
    ).update({"revoked": True})
    db.commit()
    return count


def create_user_session(
    db: Session, 
    user_id: int, 
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> str:
    """
    创建用户会话
    
    参数:
        db: 数据库会话
        user_id: 用户 ID
        ip_address: IP 地址
        user_agent: 用户代理
    
    返回:
        会话令牌
    """
    session_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=SESSION_EXPIRE_DAYS)
    
    session = UserSession(
        user_id=user_id,
        session_token=session_token,
        ip_address=ip_address,
        device_info=user_agent,
        expires_at=expires_at,
        is_active=True
    )
    db.add(session)
    db.commit()
    
    return session_token


def get_user_sessions(db: Session, user_id: int) -> List[UserSession]:
    """
    获取用户会话列表
    
    参数:
        db: 数据库会话
        user_id: 用户 ID
    
    返回:
        会话列表
    """
    return db.query(UserSession).filter(
        and_(
            UserSession.user_id == user_id,
            UserSession.is_active.is_(True),
            UserSession.expires_at > datetime.utcnow()
        )
    ).all()


def revoke_session(db: Session, session_id: int, user_id: int) -> bool:
    """
    撤销指定会话
    
    参数:
        db: 数据库会话
        session_id: 会话 ID
        user_id: 用户 ID
    
    返回:
        是否成功撤销
    """
    session = db.query(UserSession).filter(
        and_(
            UserSession.id == session_id,
            UserSession.user_id == user_id
        )
    ).first()
    
    if not session:
        return False
    
    session.is_active = False
    db.commit()
    return True


def revoke_all_user_sessions(db: Session, user_id: int) -> int:
    """
    撤销用户所有会话
    
    参数:
        db: 数据库会话
        user_id: 用户 ID
    
    返回:
        撤销的会话数量
    """
    count = db.query(UserSession).filter(
        and_(
            UserSession.user_id == user_id,
            UserSession.is_active.is_(True)
        )
    ).update({"is_active": False})
    db.commit()
    return count


def record_login_attempt(db: Session, email: str, success: bool, ip_address: Optional[str] = None) -> None:
    """
    记录登录尝试
    
    参数:
        db: 数据库会话
        email: 邮箱
        success: 是否成功
        ip_address: IP 地址
    """
    attempt = LoginAttempt(
        username=email,
        success=success,
        ip_address=ip_address or "unknown",
        timestamp=datetime.utcnow()
    )
    db.add(attempt)
    db.commit()


def check_login_attempts(db: Session, email: str) -> int:
    """
    检查登录失败次数
    
    参数:
        db: 数据库会话
        email: 邮箱
    
    返回:
        最近锁定时间窗口内的失败次数
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    
    failed_count = db.query(LoginAttempt).filter(
        and_(
            LoginAttempt.username == email,
            LoginAttempt.success.is_(False),
            LoginAttempt.timestamp > cutoff_time
        )
    ).count()
    
    return failed_count


def is_account_locked(db: Session, email: str) -> bool:
    """
    检查账户是否被锁定
    
    参数:
        db: 数据库会话
        email: 邮箱
    
    返回:
        是否被锁定
    """
    failed_attempts = check_login_attempts(db, email)
    return failed_attempts >= MAX_LOGIN_ATTEMPTS

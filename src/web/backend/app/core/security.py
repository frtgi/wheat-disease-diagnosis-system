"""
安全认证模块
提供 JWT 令牌生成、验证以及密码加密功�?
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Header, Cookie, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import bcrypt
import logging

from .config import settings
from .database import get_db
from ..models.user import User
from ..services.cache import cache_service

logger = logging.getLogger(__name__)

# bcrypt 密码最大长度限制（字节�?
BCRYPT_MAX_PASSWORD_LENGTH = 72

# Token 配置常量
TOKEN_BLACKLIST_PREFIX = "token:blacklist:"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"

# OAuth2 方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


async def get_token_from_request(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
    token_query: Optional[str] = Query(None, alias="token"),
) -> Optional[str]:
    """
    从请求中提取 Token

    优先�?Authorization header 获取，其次从 httpOnly cookie 获取，最后从查询参数获取�?
    支持 httpOnly Cookie 迁移方案�?SSE 连接场景（EventSource 不支持自定义 Header）�?

    参数:
        authorization: Authorization 请求�?
        access_token_cookie: httpOnly cookie 中的 access_token
        token_query: URL 查询参数中的 token（用�?SSE 连接�?

    返回:
        Optional[str]: Token 字符串，未找到返�?None
    """
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    if access_token_cookie:
        return access_token_cookie
    if token_query:
        return token_query
    return None


def _truncate_password(password: str) -> bytes:
    """
    截断密码以符�?bcrypt �?72 字节限制

    bcrypt 限制密码长度�?72 字节，超过此长度会抛出异常�?
    此函数将密码截断�?72 字节（UTF-8 编码）�?

    参数:
        password: 原始密码字符�?

    返回:
        截断后的密码字节
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
        logger.warning(f"密码超过 {BCRYPT_MAX_PASSWORD_LENGTH} 字节，已自动截断")
        password_bytes = password_bytes[:BCRYPT_MAX_PASSWORD_LENGTH]
    return password_bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    使用 bcrypt 库进行密码验证，支持自动处理 72 字节长度限制�?
    此函数直接使�?bcrypt 避免 passlib 版本兼容性问题�?

    参数:
        plain_password: 用户输入的明文密�?
        hashed_password: 数据库存储的密码哈希�?

    返回:
        bool: 验证成功返回 True，失败返�?False

    注意:
        bcrypt 4.1+ 版本移除�?__about__ 属性，导致 passlib 无法正确读取版本信息�?
        因此直接使用 bcrypt 库进行验证�?
    """
    try:
        password_bytes = _truncate_password(plain_password)
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError as e:
        logger.error(f"密码验证失败 - 无效的密码格�? {e}")
        return False
    except TypeError as e:
        logger.error(f"密码验证失败 - 类型错误: {e}")
        return False
    except Exception as e:
        logger.error(f"密码验证失败 - 未知错误: {e}", exc_info=True)
        return False


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    使用 bcrypt 算法生成密码哈希值，自动处理 72 字节长度限制�?
    此函数直接使�?bcrypt 避免 passlib 版本兼容性问题�?

    参数:
        password: 用户输入的明文密�?

    返回:
        str: bcrypt 哈希后的密码字符�?

    异常:
        ValueError: 密码为空或哈希生成失�?

    注意:
        bcrypt 限制密码长度�?72 字节，超过部分将被自动截断�?
        建议在前端进行密码长度验证，提升用户体验�?
    """
    if not password:
        raise ValueError("密码不能为空")

    try:
        password_bytes = _truncate_password(password)
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except ValueError as e:
        logger.error(f"密码哈希生成失败 - 值错�? {e}")
        raise ValueError(f"密码哈希生成失败: {e}")
    except TypeError as e:
        logger.error(f"密码哈希生成失败 - 类型错误: {e}")
        raise ValueError(f"密码哈希生成失败: {e}")
    except Exception as e:
        logger.error(f"密码哈希生成失败 - 未知错误: {e}", exc_info=True)
        raise ValueError(f"密码哈希生成失败: {e}")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌

    参数:
        data: 令牌数据
        expires_delta: 过期时间增量

    返回:
        JWT 令牌
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码访问令牌

    参数:
        token: JWT 令牌

    返回:
        解码后的数据，如果失败则返回 None
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建刷新令牌

    生成用于刷新访问令牌�?JWT，有效期比访问令牌更长（默认7天）�?
    刷新令牌通常存储在更安全的位置（�?HttpOnly Cookie），
    用于在访问令牌过期后获取新的访问令牌，无需用户重新登录�?

    参数:
        data: 令牌载荷数据，通常包含用户标识（如 sub 字段�?
        expires_delta: 自定义过期时间增量，默认�?REFRESH_TOKEN_EXPIRE_DAYS �?

    返回:
        str: 编码后的 JWT 刷新令牌字符�?
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return encoded_jwt


async def verify_token(token: str) -> Optional[dict]:
    """
    验证 Token 并返�?payload

    �?JWT 令牌进行解码和验证，检查签名有效性和过期时间�?
    同时检�?Token 是否已被加入黑名单（用户登出后失效）�?

    参数:
        token: 待验证的 JWT 令牌字符�?

    返回:
        Optional[dict]: 验证成功返回令牌载荷字典，失败返�?None
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        jti = payload.get("jti")
        if jti:
            try:
                if await cache_service.is_token_revoked(token):
                    logger.debug(f"Token 已被撤销: jti={jti}")
                    return None
            except Exception:
                pass

        return payload
    except JWTError as e:
        logger.debug(f"Token 验证失败: {e}")
        return None


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户

    支持�?Authorization header �?httpOnly cookie 两种方式获取 Token�?
    确保向后兼容的同时提升安全性�?

    参数:
        token: JWT 令牌（从 header �?cookie 获取�?
        db: 数据库会�?

    返回:
        当前用户对象

    异常:
        HTTPException: 令牌无效或用户不存在
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌类�?,
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError:
        raise credentials_exception

    if await is_token_blacklisted(token):
        logger.warning(f"检测到黑名�?Token，拒绝访�? username={username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已失效，请重新登�?,
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账号已被禁用"
        )

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    要求管理员权限的认证依赖

    验证当前用户是否具有管理员角色（admin），
    用于保护需要管理员权限的敏�?API 端点�?

    参数:
        current_user: 通过 get_current_user 获取的当前用户对�?

    返回:
        当前用户对象（已验证为管理员�?

    异常:
        HTTPException: 用户非管理员时返�?403 权限不足错误
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可访问此接�?
        )
    return current_user


async def add_token_to_blacklist(token: str, ttl: int = None) -> bool:
    """
    �?Token 加入 Redis 黑名�?

    当用户登出或 Token 被撤销时调用此函数�?
    �?Token 添加�?Redis 黑名单中，防止被继续使用�?

    参数:
        token: JWT Token 字符�?
        ttl: 黑名单过期时间（秒），默认为 None（自动从 Token 解析剩余有效期）

    返回:
        bool: 成功加入黑名单返�?True，失败返�?False

    异常:
        不抛出异常，内部捕获并记录错误日�?
    """
    try:
        if ttl is None:
            payload = decode_access_token(token)
            if payload and "exp" in payload:
                exp_timestamp = payload["exp"]
                remaining_seconds = exp_timestamp - datetime.now(timezone.utc).timestamp()
                ttl = max(int(remaining_seconds), 0)
            else:
                ttl = ACCESS_TOKEN_EXPIRE_MINUTES * 60

        return await cache_service.add_token_to_blacklist(token, expire=ttl)
    except Exception as e:
        logger.error(f"�?Token 加入黑名单失�? {e}", exc_info=True)
        return False


async def is_token_blacklisted(token: str) -> bool:
    """
    检�?Token 是否在黑名单�?

    在验�?Token 有效性时调用此函数，
    如果 Token 已被列入黑名单则拒绝访问�?

    参数:
        token: JWT Token 字符�?

    返回:
        bool: Token 在黑名单中返�?True，否则返�?False

    异常:
        不抛出异常，Redis 连接失败时返�?True（fail-closed 策略，拒绝请求）
    """
    try:
        return await cache_service.is_token_revoked(token)
    except Exception as e:
        logger.warning(f"检�?Token 黑名单状态失败，采用 fail-closed 策略: {e}")
        return True

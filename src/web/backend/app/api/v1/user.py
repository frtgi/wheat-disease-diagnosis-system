"""
用户 API 路由
处理用户注册、登录、信息管理等功能
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ...core.database import get_db
from ...core.config import settings
from ...core.security import create_access_token, decode_access_token, add_token_to_blacklist
from ...schemas.user import (
    UserCreate, UserResponse, UserLogin, Token, UserUpdate,
    PasswordResetRequest, PasswordReset, TokenRefresh,
    SessionResponse, MessageResponse, LoginResponse
)
from ...services.auth import (
    authenticate_user, create_user, get_user_by_id,
    create_password_reset_token, verify_password_reset_token,
    mark_password_reset_token_used, create_refresh_token,
    verify_refresh_token, revoke_refresh_token,
    create_user_session, get_user_sessions, revoke_session,
    revoke_all_user_sessions, revoke_all_user_refresh_tokens,
    record_login_attempt, is_account_locked
)
from ...models.user import User
from ...core.security import get_password_hash
from ...rate_limiter import limiter
from ...utils.xss_protection import validate_username, sanitize_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users")

AUTH_TAG = "认证管理"
USER_TAG = "用户信息"
SESSION_TAG = "会话管理"


@router.post(
    "/register",
    summary="用户注册",
    description="""
## 用户注册接口

创建新的用户账号，用于访问小麦病害诊断系统。

### 注册流程
1. 邮箱唯一性预检查
2. 用户名唯一性预检查  
3. 密码安全哈希处理（使用 bcrypt）
4. 用户数据持久化到数据库

### 请求限制
- 频率限制：每分钟最多 3 次请求

### 字段要求
- **username**: 用户名，3-50 个字符，仅支持字母、数字、下划线
- **email**: 有效的邮箱地址，用于密码重置和通知
- **password**: 密码，至少 6 个字符，建议包含字母和数字

### 错误码说明
| 错误码 | 说明 |
|--------|------|
| AUTH_001 | 邮箱已被注册 |
| AUTH_002 | 用户名已被使用 |
| AUTH_003 | 认证相关错误 |
| SYS_001 | 密码处理失败 |
| SYS_002 | 系统内部错误 |
""",
    tags=[AUTH_TAG],
    responses={
        200: {
            "description": "注册成功",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "summary": "注册成功",
                            "value": {
                                "success": True,
                                "data": {
                                    "id": 1,
                                    "username": "farmer_zhang",
                                    "email": "zhang@example.com",
                                    "role": "farmer",
                                    "is_active": True,
                                    "created_at": "2026-03-27T10:30:00"
                                },
                                "message": "注册成功"
                            }
                        },
                        "email_exists": {
                            "summary": "邮箱已被注册",
                            "value": {
                                "success": False,
                                "error": "该邮箱已被注册，请使用其他邮箱",
                                "error_code": "AUTH_001"
                            }
                        },
                        "username_exists": {
                            "summary": "用户名已被使用",
                            "value": {
                                "success": False,
                                "error": "该用户名已被使用，请选择其他用户名",
                                "error_code": "AUTH_002"
                            }
                        }
                    }
                }
            }
        }
    }
)
@limiter.limit("3/minute")
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"收到注册请求：username={user_data.username}, email={user_data.email}")
        
        is_valid, error_msg = validate_username(user_data.username)
        if not is_valid:
            logger.warning(f"注册失败 - 用户名验证失败：{user_data.username}, 错误：{error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_code": "AUTH_005"
            }
        
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            logger.warning(f"注册失败 - 邮箱已被注册：{user_data.email}")
            return {
                "success": False,
                "error": "该邮箱已被注册，请使用其他邮箱",
                "error_code": "AUTH_001"
            }
        
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            logger.warning(f"注册失败 - 用户名已被使用：{user_data.username}")
            return {
                "success": False,
                "error": "该用户名已被使用，请选择其他用户名",
                "error_code": "AUTH_002"
            }
        
        user = create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        
        logger.info(f"用户注册成功：username={user.username}, user_id={user.id}")
        
        return {
            "success": True,
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "message": "注册成功"
        }
        
    except HTTPException as e:
        logger.error(f"注册失败 - HTTP异常：{e.detail}")
        return {
            "success": False,
            "error": e.detail,
            "error_code": "AUTH_003"
        }
    except ValueError as e:
        logger.error(f"注册失败 - 密码哈希错误：{e}", exc_info=True)
        db.rollback()
        return {
            "success": False,
            "error": "密码处理失败，请稍后重试",
            "error_code": "SYS_001"
        }
    except IntegrityError as e:
        logger.error(f"注册失败 - 数据库完整性错误：{e}", exc_info=True)
        db.rollback()
        return {
            "success": False,
            "error": "用户名或邮箱已被使用",
            "error_code": "AUTH_001"
        }
    except Exception as e:
        logger.error(f"注册失败 - 未知错误：{e}", exc_info=True)
        db.rollback()
        return {
            "success": False,
            "error": "注册失败，请稍后重试",
            "error_code": "SYS_002"
        }


@router.post(
    "/login",
    summary="用户登录",
    description="""
## 用户登录接口

使用用户名/邮箱和密码进行登录认证，获取访问令牌。

### 登录流程
1. 验证用户凭证（用户名/邮箱 + 密码）
2. 检查账号状态（是否被禁用）
3. 生成 JWT 访问令牌（有效期 24 小时）
4. 生成刷新令牌（有效期 7 天）
5. 记录登录日志

### 请求限制
- 频率限制：每分钟最多 5 次请求

### 字段要求
- **username**: 用户名或注册邮箱
- **password**: 用户密码

### 错误码说明
| 错误码 | 说明 |
|--------|------|
| AUTH_002 | 用户名或密码错误 |
| AUTH_004 | 用户账号已被禁用 |
| SYS_002 | 系统内部错误 |
""",
    tags=[AUTH_TAG],
    responses={
        200: {
            "description": "登录成功",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "summary": "登录成功",
                            "value": {
                                "success": True,
                                "data": {
                                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                    "refresh_token": "rt_abc123def456...",
                                    "token_type": "bearer",
                                    "user": {
                                        "id": 1,
                                        "username": "farmer_zhang",
                                        "email": "zhang@example.com",
                                        "role": "farmer",
                                        "is_active": True
                                    }
                                },
                                "message": "登录成功"
                            }
                        },
                        "invalid_credentials": {
                            "summary": "凭证错误",
                            "value": {
                                "success": False,
                                "error": "用户名或密码错误",
                                "error_code": "AUTH_002"
                            }
                        },
                        "account_disabled": {
                            "summary": "账号已禁用",
                            "value": {
                                "success": False,
                                "error": "用户账号已被禁用",
                                "error_code": "AUTH_004"
                            }
                        }
                    }
                }
            }
        }
    }
)
@limiter.limit("5/minute")
def login(request: Request, response: Response, login_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, login_data.username, login_data.password)
        
        if not user:
            logger.warning(f"登录失败 - 用户名或密码错误：{login_data.username}")
            return {
                "success": False,
                "error": "用户名或密码错误",
                "error_code": "AUTH_002"
            }
        
        if not user.is_active:
            logger.warning(f"登录失败 - 账号已禁用：{login_data.username}")
            return {
                "success": False,
                "error": "用户账号已被禁用",
                "error_code": "AUTH_004"
            }
        
        access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
        refresh_token = create_refresh_token(db, user.id)
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            max_age=86400,
            path="/"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            max_age=604800,
            path="/"
        )
        
        logger.info(f"用户登录成功：username={user.username}, user_id={user.id}")
        
        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active
                }
            },
            "message": "登录成功"
        }
        
    except Exception as e:
        logger.error(f"登录失败 - 未知错误：{e}", exc_info=True)
        return {
            "success": False,
            "error": "登录失败，请稍后重试",
            "error_code": "SYS_002"
        }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户信息",
    description="""
## 获取当前登录用户信息

获取当前已认证用户的详细个人信息，包括用户名、邮箱、角色等。

### 认证要求
- 需要在请求头中携带有效的 Bearer Token
- Authorization: Bearer {access_token}

### 返回信息
- 用户 ID
- 用户名
- 邮箱地址
- 手机号（如有）
- 头像 URL
- 用户角色（farmer/expert/admin）
- 账号状态
- 创建时间和更新时间

### 性能优化
- 使用缓存减少数据库查询（缓存 12 小时）
- 用户信息更新时自动失效缓存
""",
    tags=[USER_TAG],
    responses={
        200: {
            "description": "获取成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "farmer_zhang",
                        "email": "zhang@example.com",
                        "phone": "13800138000",
                        "avatar_url": "/uploads/avatars/avatar_1.jpg",
                        "role": "farmer",
                        "is_active": True,
                        "created_at": "2026-03-27T10:30:00",
                        "updated_at": "2026-03-27T10:30:00"
                    }
                }
            }
        },
        401: {
            "description": "未授权",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_token": {"detail": "缺少认证令牌"},
                        "invalid_token": {"detail": "无效的认证令牌"}
                    }
                }
            }
        }
    }
)
@sanitize_response(fields_to_sanitize=["username", "email", "phone", "avatar_url"])
async def get_current_user_info(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    from ...services.cache import cache_service
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌"
        )
    
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    username = payload.get("sub")
    user_id = payload.get("user_id")
    
    if user_id:
        try:
            cached_user = await cache_service.get_user_info(user_id)
            if cached_user:
                logger.debug(f"用户信息缓存命中：user_id={user_id}")
                return User(**cached_user)
        except Exception as e:
            logger.warning(f"读取用户缓存失败：{e}")
    
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    try:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
        await cache_service.set_user_info(user.id, user_dict)
    except Exception as e:
        logger.warning(f"设置用户缓存失败：{e}")
    
    return user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="获取指定用户信息",
    description="""
## 获取指定用户信息

根据用户 ID 获取用户的公开信息。

### 路径参数
- **user_id**: 用户 ID（整数）

### 返回信息
返回指定用户的基本信息，不包含敏感数据如密码。
""",
    tags=[USER_TAG],
    responses={
        200: {
            "description": "获取成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "farmer_zhang",
                        "email": "zhang@example.com",
                        "phone": "13800138000",
                        "avatar_url": None,
                        "role": "farmer",
                        "is_active": True,
                        "created_at": "2026-03-27T10:30:00",
                        "updated_at": "2026-03-27T10:30:00"
                    }
                }
            }
        },
        404: {
            "description": "用户不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "用户不存在"}
                }
            }
        }
    }
)
@sanitize_response(fields_to_sanitize=["username", "email", "phone", "avatar_url"])
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权查看其他用户信息")
    
    user = get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="更新用户信息",
    description="""
## 更新用户信息

更新指定用户的个人信息。

### 路径参数
- **user_id**: 用户 ID（整数）

### 可更新字段
- **username**: 新用户名（3-50 字符）
- **email**: 新邮箱地址
- **phone**: 手机号
- **avatar**: 头像 URL
- **is_active**: 账号激活状态

### 注意事项
- 更新邮箱时需要确保新邮箱未被其他用户使用
- 用户名修改后需使用新用户名登录
""",
    tags=[USER_TAG],
    responses={
        200: {
            "description": "更新成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "farmer_zhang_new",
                        "email": "zhang_new@example.com",
                        "phone": "13900139000",
                        "avatar_url": "/uploads/avatars/avatar_1.jpg",
                        "role": "farmer",
                        "is_active": True,
                        "created_at": "2026-03-27T10:30:00",
                        "updated_at": "2026-03-27T12:00:00"
                    }
                }
            }
        },
        404: {
            "description": "用户不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "用户不存在"}
                }
            }
        }
    }
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权修改其他用户信息")
    
    user = get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user_data.username:
        is_valid, error_msg = validate_username(user_data.username)
        if not is_valid:
            logger.warning(f"用户更新失败 - 用户名验证失败：{user_data.username}, 错误：{error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    
    update_dict = user_data.model_dump(exclude_unset=True, by_alias=True)
    for field, value in update_dict.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.post(
    "/password/reset-request",
    response_model=MessageResponse,
    summary="请求密码重置",
    description="""
## 请求密码重置

发送密码重置验证码到用户注册邮箱。

### 工作流程
1. 验证邮箱是否已注册
2. 生成密码重置令牌（有效期 1 小时）
3. 发送重置邮件到用户邮箱

### 安全措施
- 无论邮箱是否存在，都返回相同响应（防止邮箱枚举攻击）
- 重置令牌一次性使用，使用后自动失效

### 请求参数
- **email**: 注册时使用的邮箱地址
""",
    tags=[AUTH_TAG],
    responses={
        200: {
            "description": "请求已处理",
            "content": {
                "application/json": {
                    "example": {
                        "message": "如果该邮箱已注册，您将收到密码重置邮件",
                        "success": True
                    }
                }
            }
        }
    }
)
def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    logger.info(f"收到密码重置请求：email={request_data.email}")
    
    token = create_password_reset_token(db, request_data.email)
    
    if not token:
        logger.warning(f"密码重置失败，邮箱不存在：{request_data.email}")
        return {"message": "如果该邮箱已注册，您将收到密码重置邮件", "success": True}
    
    logger.info(f"密码重置令牌已创建：email={request_data.email}")
    
    return {"message": "如果该邮箱已注册，您将收到密码重置邮件", "success": True}


@router.post(
    "/password/reset",
    response_model=MessageResponse,
    summary="执行密码重置",
    description="""
## 执行密码重置

使用重置令牌设置新密码。

### 工作流程
1. 验证重置令牌有效性和时效性
2. 更新用户密码（bcrypt 哈希）
3. 标记令牌为已使用
4. 撤销该用户所有会话

### 请求参数
- **token**: 密码重置令牌（从邮件获取）
- **new_password**: 新密码（至少 6 个字符）

### 错误情况
- 令牌无效或已过期
- 令牌已被使用
""",
    tags=[AUTH_TAG],
    responses={
        200: {
            "description": "密码重置成功",
            "content": {
                "application/json": {
                    "example": {
                        "message": "密码重置成功",
                        "success": True
                    }
                }
            }
        },
        400: {
            "description": "令牌无效",
            "content": {
                "application/json": {
                    "example": {"detail": "重置令牌无效或已过期"}
                }
            }
        }
    }
)
def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    logger.info("收到密码重置执行请求")
    
    user = verify_password_reset_token(db, reset_data.token)
    
    if not user:
        logger.warning("密码重置令牌无效或已过期")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="重置令牌无效或已过期"
        )
    
    user.password_hash = get_password_hash(reset_data.new_password)
    mark_password_reset_token_used(db, reset_data.token)
    
    db.commit()
    
    logger.info(f"密码重置成功：user_id={user.id}")
    
    return {"message": "密码重置成功", "success": True}


@router.post(
    "/token/refresh",
    response_model=Token,
    summary="刷新访问令牌",
    description="""
## 刷新访问令牌

使用刷新令牌获取新的访问令牌，无需重新登录。

### 工作流程
1. 验证刷新令牌有效性
2. 检查用户账号状态
3. 生成新的访问令牌（有效期 24 小时）

### 请求参数
- **refresh_token**: 登录时获取的刷新令牌

### 令牌有效期
- 访问令牌：24 小时
- 刷新令牌：7 天
""",
    tags=[AUTH_TAG],
    responses={
        200: {
            "description": "令牌刷新成功",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "刷新令牌无效",
            "content": {
                "application/json": {
                    "example": {"detail": "刷新令牌无效或已过期"}
                }
            }
        },
        403: {
            "description": "账号已禁用",
            "content": {
                "application/json": {
                    "example": {"detail": "用户账号已被禁用"}
                }
            }
        }
    }
)
def refresh_token(
    refresh_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    user = verify_refresh_token(db, refresh_data.refresh_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌无效或已过期"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账号已被禁用"
        )
    
    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
    
    logger.info(f"令牌刷新成功：user_id={user.id}")
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="用户登出",
    description="""
## 用户登出

注销当前用户会话，撤销所有相关令牌。

### 工作流程
1. 验证访问令牌
2. 撤销该用户所有刷新令牌
3. 撤销该用户所有活跃会话
4. 记录登出日志

### 认证要求
- 需要在请求头中携带有效的 Bearer Token
- Authorization: Bearer {access_token}
""",
    tags=[AUTH_TAG],
    responses={
        200: {
            "description": "登出成功",
            "content": {
                "application/json": {
                    "example": {
                        "message": "登出成功",
                        "success": True
                    }
                }
            }
        },
        401: {
            "description": "未授权",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_token": {"detail": "缺少认证令牌"},
                        "invalid_token": {"detail": "无效的认证令牌"}
                    }
                }
            }
        }
    }
)
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    用户登出处理函数

    验证访问令牌，撤销所有相关令牌和会话，并将当前 Token 加入黑名单。
    同时清除 httpOnly cookie。

    参数:
        request: FastAPI 请求对象
        response: FastAPI 响应对象
        db: 数据库会话
        authorization: Authorization 请求头

    返回:
        登出成功响应

    异常:
        HTTPException: 缺少或无效的认证令牌
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        from ...core.security import get_token_from_request
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌"
        )

    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )

    user_id = payload.get("user_id")
    username = payload.get("sub")

    if user_id:
        revoke_all_user_refresh_tokens(db, user_id)
        revoke_all_user_sessions(db, user_id)

    await add_token_to_blacklist(token)

    response.delete_cookie(key="access_token", path="/", secure=not settings.DEBUG)
    response.delete_cookie(key="refresh_token", path="/", secure=not settings.DEBUG)

    logger.info(f"用户登出成功：username={username}")

    return {"message": "登出成功", "success": True}


@router.get(
    "/sessions/list",
    response_model=List[SessionResponse],
    summary="获取活跃会话列表",
    description="""
## 获取活跃会话列表

获取当前用户的所有活跃会话信息，用于设备管理。

### 认证要求
- 需要在请求头中携带有效的 Bearer Token
- Authorization: Bearer {access_token}

### 返回信息
- 会话 ID
- 会话令牌（部分隐藏）
- IP 地址
- 用户代理（浏览器/设备信息）
- 会话状态
- 创建时间
- 过期时间
""",
    tags=[SESSION_TAG],
    responses={
        200: {
            "description": "获取成功",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "user_id": 1,
                            "session_token": "sess_abc...xyz",
                            "ip_address": "192.168.1.100",
                            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                            "is_active": True,
                            "created_at": "2026-03-27T10:30:00",
                            "expires_at": "2026-04-03T10:30:00"
                        }
                    ]
                }
            }
        },
        401: {
            "description": "未授权",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_token": {"detail": "缺少认证令牌"},
                        "invalid_token": {"detail": "无效的认证令牌"}
                    }
                }
            }
        }
    }
)
def get_sessions(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌"
        )
    
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    sessions = get_user_sessions(db, user_id)
    
    return sessions


@router.delete(
    "/sessions/{session_id}",
    response_model=MessageResponse,
    summary="终止指定会话",
    description="""
## 终止指定会话

强制终止指定的登录会话，用于设备管理或安全操作。

### 路径参数
- **session_id**: 要终止的会话 ID

### 认证要求
- 需要在请求头中携带有效的 Bearer Token
- 只能终止自己的会话

### 使用场景
- 在其他设备上强制登出
- 发现异常登录时终止会话
- 清理不活跃的设备登录
""",
    tags=[SESSION_TAG],
    responses={
        200: {
            "description": "会话已终止",
            "content": {
                "application/json": {
                    "example": {
                        "message": "会话已终止",
                        "success": True
                    }
                }
            }
        },
        401: {
            "description": "未授权",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_token": {"detail": "缺少认证令牌"},
                        "invalid_token": {"detail": "无效的认证令牌"}
                    }
                }
            }
        },
        404: {
            "description": "会话不存在",
            "content": {
                "application/json": {
                    "example": {"detail": "会话不存在或无权终止"}
                }
            }
        }
    }
)
def terminate_session(
    session_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌"
        )
    
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    success = revoke_session(db, session_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在或无权终止"
        )
    
    logger.info(f"会话终止成功：session_id={session_id}, user_id={user_id}")
    
    return {"message": "会话已终止", "success": True}

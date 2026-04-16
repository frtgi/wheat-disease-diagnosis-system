"""
用户 Pydantic 模式
定义用户数据的请求和响应格式
"""
from datetime import datetime
from typing import Optional, Dict, Any, Type
from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")


class UserCreate(UserBase):
    """用户创建请求模式"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserUpdate(BaseModel):
    """用户更新请求模式"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar: Optional[str] = Field(None, alias="avatar_url", description="头像 URL")
    is_active: Optional[bool] = Field(None, description="是否激活")

    class Config:
        populate_by_name = True


class UserResponse(UserBase):
    """用户响应模式（不包含敏感信息如密码哈希）"""
    id: int
    avatar_url: Optional[str] = None
    avatar: Optional[str] = Field(None, alias="avatar_url", description="头像别名，与 avatar_url 相同")
    role: str = "farmer"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

        @staticmethod
        def json_schema_extra(schema: Dict[str, Any], model: Type['UserResponse']) -> None:
            """确保响应模式中不包含密码相关字段"""
            forbidden_fields = ['password', 'password_hash']
            for field in forbidden_fields:
                if field in schema.get('properties', {}):
                    del schema['properties'][field]


class UserLogin(BaseModel):
    """用户登录请求模式"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """令牌响应模式"""
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """登录响应模式"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """令牌数据模式"""
    username: Optional[str] = None
    user_id: Optional[int] = None


class PasswordResetRequest(BaseModel):
    """密码重置请求模式"""
    email: str = Field(..., description="注册时使用的邮箱地址")


class PasswordReset(BaseModel):
    """密码重置执行模式"""
    token: str = Field(..., description="密码重置令牌")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class TokenRefresh(BaseModel):
    """令牌刷新模式"""
    refresh_token: str = Field(..., description="刷新令牌")


class SessionResponse(BaseModel):
    """会话响应模式"""
    id: int
    user_id: int
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    expires_at: datetime
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """通用消息响应模式"""
    message: str
    success: bool = True

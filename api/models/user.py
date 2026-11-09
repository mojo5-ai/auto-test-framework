"""
API 数据模型模块

使用 pydantic 定义请求/响应的数据结构，确保：
1. 接口返回数据自动校验类型
2. 错误时给出清晰的错误信息
3. IDE 自动补全，减少手写字典

用法：
    from api.models.user import UserResponse
    user = UserResponse(**response.json())
    print(user.id, user.username)
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRequest(BaseModel):
    """用户创建/更新请求模型"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    role: Optional[str] = Field("user", description="用户角色")


class UserResponse(BaseModel):
    """用户接口响应模型"""
    id: Optional[int] = Field(None, description="用户 ID")
    username: str = Field("", description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    role: str = Field("user", description="用户角色")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


class ApiResponse(BaseModel):
    """通用 API 响应包装"""
    code: int = Field(0, description="业务状态码，0 表示成功")
    message: str = Field("success", description="业务消息")
    data: Optional[dict | list] = Field(None, description="响应数据")
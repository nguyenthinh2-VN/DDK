"""
User Schemas (DTO) - Request/Response models cho quản lý User & Role.

Tương đương: DTO trong Spring.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ── User Request DTOs ────────────────────────────────


class UserCreateRequest(BaseModel):
    """Request body khi admin tạo user mới."""

    username: str = Field(..., min_length=3, max_length=50, description="Tên đăng nhập")
    password: str = Field(..., min_length=6, description="Mật khẩu (tối thiểu 6 ký tự)")
    full_name: str = Field(..., min_length=1, max_length=255, description="Họ tên đầy đủ")
    role_id: str = Field(..., description="ID của role gán cho user")


class UserUpdateRequest(BaseModel):
    """Request body khi cập nhật user (các field đều optional)."""

    full_name: str | None = Field(default=None, max_length=255, description="Họ tên đầy đủ")
    role_id: str | None = Field(default=None, description="Đổi role của user")
    is_active: bool | None = Field(default=None, description="Kích hoạt / vô hiệu hóa tài khoản")


# ── User Response DTOs ───────────────────────────────


class RoleResponse(BaseModel):
    """Thông tin role."""

    id: str
    name: str
    display_name: str
    level: int

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """Thông tin user trả về cho admin."""

    id: str
    username: str
    full_name: str
    is_active: bool
    created_at: datetime
    role: RoleResponse | None = None

    model_config = {"from_attributes": True}


# ── Permission Response DTOs ─────────────────────────


class PermissionResponse(BaseModel):
    """Thông tin permission."""

    id: str
    code: str
    name: str

    model_config = {"from_attributes": True}


class AssignPermissionRequest(BaseModel):
    """Request body khi gán permission vào role."""

    permission_id: str = Field(..., description="ID của permission cần gán")

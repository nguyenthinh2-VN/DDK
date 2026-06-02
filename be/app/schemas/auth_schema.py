"""
Auth Schemas (DTO) - Request/Response models cho Authentication.

Tương đương: DTO trong Spring.

Định nghĩa dữ liệu truyền qua các API auth (login, me, change-password).
"""

from pydantic import BaseModel, Field


# ── Request DTOs ─────────────────────────────────────


class LoginRequest(BaseModel):
    """Request body khi đăng nhập."""

    username: str = Field(..., min_length=1, description="Tên đăng nhập")
    password: str = Field(..., min_length=1, description="Mật khẩu")


class ChangePasswordRequest(BaseModel):
    """Request body khi đổi mật khẩu."""

    old_password: str = Field(..., min_length=1, description="Mật khẩu cũ")
    new_password: str = Field(..., min_length=6, description="Mật khẩu mới (tối thiểu 6 ký tự)")


# ── Response DTOs ────────────────────────────────────


class TokenResponse(BaseModel):
    """Response trả về sau khi đăng nhập thành công."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Loại token")
    message: str = Field(..., description="Thông báo (đa ngôn ngữ)")


class CurrentUserResponse(BaseModel):
    """Thông tin user hiện tại (GET /api/auth/me)."""

    id: str
    username: str
    full_name: str
    role: str = Field(..., description="Tên role, VD: CEO")
    role_level: int = Field(..., description="Cấp bậc của role")
    permissions: list[str] = Field(default_factory=list, description="Danh sách permission code")

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Response chỉ chứa message (đa ngôn ngữ)."""

    message: str

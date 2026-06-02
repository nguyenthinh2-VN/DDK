"""
Auth API Router (Controller) - Endpoints xác thực.

Tương đương: @RestController trong Spring.

Tầng Controller: nhận request, validate input (qua Schema), gọi Service,
trả response. KHÔNG chứa business logic.

Endpoints:
- POST /api/auth/login           (public)
- POST /api/auth/logout          (required)
- GET  /api/auth/me              (required)
- PUT  /api/auth/change-password (required)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth_schema import (
    LoginRequest,
    ChangePasswordRequest,
    TokenResponse,
    CurrentUserResponse,
    MessageResponse,
)
from app.services.auth_service import AuthService
from app.utils.auth_guard import get_current_user
from app.utils.i18n import get_message
from app.utils.response_helper import get_language, LocalizedHTTPException

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, summary="Đăng nhập")
async def login(
    body: LoginRequest,
    lang: str = Depends(get_language),
    db: AsyncSession = Depends(get_db),
):
    """Đăng nhập bằng username/password, trả về JWT access token."""
    service = AuthService(db)
    user = await service.authenticate(body.username, body.password)

    if user is None:
        raise LocalizedHTTPException(
            status.HTTP_401_UNAUTHORIZED, "auth.invalid_credentials", lang
        )
    if not user.is_active:
        raise LocalizedHTTPException(
            status.HTTP_403_FORBIDDEN, "auth.account_inactive", lang
        )

    token = service.create_token_for_user(user)
    return TokenResponse(
        access_token=token,
        message=get_message("auth.login_success", lang),
    )


@router.post("/logout", response_model=MessageResponse, summary="Đăng xuất")
async def logout(
    lang: str = Depends(get_language),
    current_user: User = Depends(get_current_user),
):
    """
    Đăng xuất.

    Vì dùng JWT stateless (không Refresh Token), logout chủ yếu để FE
    xóa token phía client. Endpoint xác nhận user hợp lệ và trả message.
    """
    return MessageResponse(message=get_message("auth.logout_success", lang))


@router.get("/me", response_model=CurrentUserResponse, summary="Thông tin user hiện tại")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lấy thông tin user đang đăng nhập (kèm role + permissions)."""
    service = AuthService(db)
    return service.build_current_user(current_user)


@router.put("/change-password", response_model=MessageResponse, summary="Đổi mật khẩu")
async def change_password(
    body: ChangePasswordRequest,
    lang: str = Depends(get_language),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Đổi mật khẩu của user hiện tại."""
    service = AuthService(db)
    success = await service.change_password(
        current_user, body.old_password, body.new_password
    )
    if not success:
        raise LocalizedHTTPException(
            status.HTTP_400_BAD_REQUEST, "auth.old_password_incorrect", lang
        )
    return MessageResponse(message=get_message("auth.password_changed", lang))

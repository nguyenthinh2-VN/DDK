"""
Admin Users API Router (Controller) - Quản lý User.

Tương đương: @RestController trong Spring.

Phân quyền theo cấp bậc role tối thiểu (require_min_role):
- POST   /api/admin/users        -> Director
- GET    /api/admin/users        -> Director
- GET    /api/admin/users/{id}   -> Manager
- PUT    /api/admin/users/{id}   -> Manager
- DELETE /api/admin/users/{id}   -> CEO
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import ROLE_CEO, ROLE_DIRECTOR, ROLE_MANAGER
from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth_schema import MessageResponse
from app.schemas.user_schema import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
)
from app.services.user_service import UserService
from app.utils.auth_guard import require_min_role
from app.utils.i18n import get_message
from app.utils.response_helper import get_language, LocalizedHTTPException

router = APIRouter(prefix="/api/admin/users", tags=["Admin - Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo user mới (Director+)",
)
async def create_user(
    body: UserCreateRequest,
    lang: str = Depends(get_language),
    _: User = Depends(require_min_role(ROLE_DIRECTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Tạo user mới. Yêu cầu role tối thiểu: Director."""
    service = UserService(db)
    user, error_key = await service.create_user(body)
    if error_key is not None:
        raise LocalizedHTTPException(status.HTTP_400_BAD_REQUEST, error_key, lang)
    return user


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Danh sách user (Director+)",
)
async def list_users(
    _: User = Depends(require_min_role(ROLE_DIRECTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách tất cả user. Yêu cầu role tối thiểu: Director."""
    service = UserService(db)
    return await service.get_all_users()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Chi tiết user (Manager+)",
)
async def get_user(
    user_id: str,
    lang: str = Depends(get_language),
    _: User = Depends(require_min_role(ROLE_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """Lấy chi tiết user theo ID. Yêu cầu role tối thiểu: Manager."""
    service = UserService(db)
    user = await service.get_user(user_id)
    if user is None:
        raise LocalizedHTTPException(status.HTTP_404_NOT_FOUND, "user.not_found", lang)
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Cập nhật user (Manager+)",
)
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    lang: str = Depends(get_language),
    _: User = Depends(require_min_role(ROLE_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """Cập nhật user (đổi role_id, full_name, is_active). Yêu cầu: Manager."""
    service = UserService(db)
    user, error_key = await service.update_user(user_id, body)
    if error_key is not None:
        code = (
            status.HTTP_404_NOT_FOUND
            if error_key == "user.not_found"
            else status.HTTP_400_BAD_REQUEST
        )
        raise LocalizedHTTPException(code, error_key, lang)
    return user


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Xóa user (CEO)",
)
async def delete_user(
    user_id: str,
    lang: str = Depends(get_language),
    _: User = Depends(require_min_role(ROLE_CEO)),
    db: AsyncSession = Depends(get_db),
):
    """Xóa user theo ID. Yêu cầu role: CEO."""
    service = UserService(db)
    success, error_key = await service.delete_user(user_id)
    if not success:
        raise LocalizedHTTPException(status.HTTP_404_NOT_FOUND, error_key, lang)
    return MessageResponse(message=get_message("user.deleted", lang))

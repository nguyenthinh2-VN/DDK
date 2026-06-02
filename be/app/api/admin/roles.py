"""
Admin Roles API Router (Controller) - Quản lý Role & Permission.

Tương đương: @RestController trong Spring.

Phân quyền theo cấp bậc role tối thiểu (require_min_role):
- GET    /api/admin/roles                              -> Manager
- GET    /api/admin/roles/{id}/permissions             -> Manager
- POST   /api/admin/roles/{id}/permissions             -> CEO
- DELETE /api/admin/roles/{id}/permissions/{perm_id}   -> CEO
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import ROLE_CEO, ROLE_MANAGER
from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth_schema import MessageResponse
from app.schemas.user_schema import (
    RoleResponse,
    PermissionResponse,
    AssignPermissionRequest,
)
from app.services.user_service import UserService
from app.utils.auth_guard import require_min_role
from app.utils.i18n import get_message
from app.utils.response_helper import get_language, LocalizedHTTPException

router = APIRouter(prefix="/api/admin/roles", tags=["Admin - Roles & Permissions"])


@router.get(
    "",
    response_model=list[RoleResponse],
    summary="Danh sách roles (Manager+)",
)
async def list_roles(
    _: User = Depends(require_min_role(ROLE_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách tất cả role. Yêu cầu role tối thiểu: Manager."""
    service = UserService(db)
    return await service.get_all_roles()


@router.get(
    "/{role_id}/permissions",
    response_model=list[PermissionResponse],
    summary="Quyền của role (Manager+)",
)
async def get_role_permissions(
    role_id: str,
    lang: str = Depends(get_language),
    _: User = Depends(require_min_role(ROLE_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách permission của 1 role. Yêu cầu: Manager."""
    service = UserService(db)
    permissions, error_key = await service.get_role_permissions(role_id)
    if error_key is not None:
        raise LocalizedHTTPException(status.HTTP_404_NOT_FOUND, error_key, lang)
    return permissions


@router.post(
    "/{role_id}/permissions",
    response_model=MessageResponse,
    summary="Gán quyền vào role (CEO)",
)
async def assign_permission(
    role_id: str,
    body: AssignPermissionRequest,
    lang: str = Depends(get_language),
    _: User = Depends(require_min_role(ROLE_CEO)),
    db: AsyncSession = Depends(get_db),
):
    """Gán 1 permission vào role (phân quyền động). Yêu cầu role: CEO."""
    service = UserService(db)
    success, error_key = await service.assign_permission(role_id, body.permission_id)
    if not success:
        raise LocalizedHTTPException(status.HTTP_404_NOT_FOUND, error_key, lang)
    return MessageResponse(message=get_message("role.permission_assigned", lang))


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    response_model=MessageResponse,
    summary="Bỏ quyền khỏi role (CEO)",
)
async def remove_permission(
    role_id: str,
    permission_id: str,
    lang: str = Depends(get_language),
    _: User = Depends(require_min_role(ROLE_CEO)),
    db: AsyncSession = Depends(get_db),
):
    """Bỏ 1 permission khỏi role (phân quyền động). Yêu cầu role: CEO."""
    service = UserService(db)
    success, error_key = await service.remove_permission(role_id, permission_id)
    if not success:
        raise LocalizedHTTPException(status.HTTP_404_NOT_FOUND, error_key, lang)
    return MessageResponse(message=get_message("role.permission_removed", lang))

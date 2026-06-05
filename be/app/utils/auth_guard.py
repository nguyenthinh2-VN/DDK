"""
Auth Guard - FastAPI dependencies cho xác thực & phân quyền.

Tương đương: Spring Security filter chain + @PreAuthorize.

Cung cấp:
- get_current_user:   Verify JWT, load User từ DB -> trả về User entity.
- require_min_role:    Factory tạo dependency yêu cầu cấp bậc role tối thiểu.
- require_permission:  Factory tạo dependency yêu cầu 1 permission cụ thể.

Lưu ý về level: số nhỏ hơn = quyền cao hơn (CEO=1 ... EMPLOYEE=4).
Vì vậy "đủ quyền" nghĩa là role_level của user <= level yêu cầu.
"""

from fastapi import Depends, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.i18n import resolve_language
from app.utils.jwt_helper import decode_access_token
from app.utils.response_helper import LocalizedHTTPException

# Scheme để Swagger UI hiển thị ô nhập Bearer token
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    accept_language: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency: verify Bearer token và trả về User entity hiện tại.

    Raise 401 nếu thiếu token / token sai / user không tồn tại / bị vô hiệu hóa.
    """
    lang = resolve_language(accept_language)

    if credentials is None or not credentials.credentials:
        raise LocalizedHTTPException(
            status.HTTP_401_UNAUTHORIZED, "common.unauthorized", lang,
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise LocalizedHTTPException(
            status.HTTP_401_UNAUTHORIZED, "auth.token_invalid", lang,
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise LocalizedHTTPException(
            status.HTTP_401_UNAUTHORIZED, "auth.token_invalid", lang,
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepository(db)
    user = await repo.find_by_id(user_id)
    if user is None:
        raise LocalizedHTTPException(
            status.HTTP_401_UNAUTHORIZED, "auth.token_invalid", lang,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise LocalizedHTTPException(
            status.HTTP_403_FORBIDDEN, "auth.account_inactive", lang,
        )

    return user


def require_min_role(min_role_or_level):
    """
    Factory tạo dependency yêu cầu cấp bậc role tối thiểu.

    min_role_or_level có thể là level cao nhất được phép (int) hoặc tên role (str).
    VD: require_min_role(2) hoặc require_min_role("TREASURY").
    """
    if isinstance(min_role_or_level, str):
        from app.config.constants import ROLE_LEVEL_MAP
        min_level = next((lvl for lvl, name in ROLE_LEVEL_MAP.items() if name == min_role_or_level), 999)
    else:
        min_level = int(min_role_or_level)

    async def _checker(
        current_user: User = Depends(get_current_user),
        accept_language: str | None = Header(default=None),
    ) -> User:
        lang = resolve_language(accept_language)
        role_level = current_user.role.level if current_user.role else 999
        if role_level > min_level:
            raise LocalizedHTTPException(
                status.HTTP_403_FORBIDDEN, "common.forbidden", lang,
            )
        return current_user

    return _checker


def require_permission(permission_code: str):
    """
    Factory tạo dependency yêu cầu 1 permission cụ thể.

    Kiểm tra user có permission_code trong role của họ hay không.

    Dùng: Depends(require_permission("user:create"))
    """

    async def _checker(
        current_user: User = Depends(get_current_user),
        accept_language: str | None = Header(default=None),
    ) -> User:
        lang = resolve_language(accept_language)
        codes = (
            {p.code for p in current_user.role.permissions}
            if current_user.role
            else set()
        )
        if permission_code not in codes:
            raise LocalizedHTTPException(
                status.HTTP_403_FORBIDDEN, "common.forbidden", lang,
            )
        return current_user

    return _checker

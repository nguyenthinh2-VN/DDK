"""
Auth Service - Business Logic Layer cho Authentication.

Tương đương: @Service class trong Spring.

Xử lý: login (verify password + tạo JWT), đổi mật khẩu, build thông tin
user hiện tại. KHÔNG xử lý HTTP request/response (đó là việc của API layer).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import CurrentUserResponse
from app.utils.jwt_helper import create_access_token
from app.utils.password_helper import verify_password, hash_password


class AuthService:
    """Service xử lý nghiệp vụ xác thực."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def authenticate(self, username: str, password: str) -> User | None:
        """
        Xác thực username + password.

        Returns:
            User nếu hợp lệ; None nếu sai thông tin đăng nhập.
        """
        user = await self.user_repo.find_by_username(username)
        if user is None:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_token_for_user(self, user: User) -> str:
        """Tạo JWT access token từ thông tin user + role."""
        role_name = user.role.name if user.role else "UNKNOWN"
        role_level = user.role.level if user.role else 999
        return create_access_token(
            user_id=user.id,
            username=user.username,
            role=role_name,
            role_level=role_level,
        )

    def build_current_user(self, user: User) -> CurrentUserResponse:
        """Build DTO thông tin user hiện tại (kèm role + permissions)."""
        permissions = (
            [p.code for p in user.role.permissions] if user.role else []
        )
        return CurrentUserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role.name if user.role else "UNKNOWN",
            role_level=user.role.level if user.role else 999,
            permissions=permissions,
        )

    async def change_password(
        self, user: User, old_password: str, new_password: str
    ) -> bool:
        """
        Đổi mật khẩu cho user.

        Returns:
            True nếu đổi thành công; False nếu mật khẩu cũ không đúng.
        """
        if not verify_password(old_password, user.hashed_password):
            return False
        user.hashed_password = hash_password(new_password)
        await self.user_repo.update(user)
        return True

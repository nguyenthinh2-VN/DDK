"""
User Service - Business Logic Layer cho quản lý User, Role & Permission.

Tương đương: @Service class trong Spring.

Xử lý nghiệp vụ CRUD user, đọc role, và phân quyền động (gán/bỏ permission).
Trả về kết quả dạng (success, data, error_key) để Controller dịch message.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.schemas.user_schema import UserCreateRequest, UserUpdateRequest
from app.utils.password_helper import hash_password


class UserService:
    """Service xử lý nghiệp vụ quản lý người dùng và phân quyền."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    # ── User CRUD ────────────────────────────────────

    async def create_user(self, data: UserCreateRequest) -> tuple[User | None, str | None]:
        """
        Tạo user mới.

        Returns:
            (user, None) nếu thành công;
            (None, error_key) nếu lỗi (username tồn tại / role không tồn tại).
        """
        existing = await self.user_repo.find_by_username(data.username)
        if existing is not None:
            return None, "user.already_exists"

        role = await self.role_repo.find_role_by_id(data.role_id)
        if role is None:
            return None, "role.not_found"

        user = User(
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role_id=data.role_id,
        )
        created = await self.user_repo.create(user)
        # Load lại để có quan hệ role đầy đủ
        return await self.user_repo.find_by_id(created.id), None

    async def get_user(self, user_id: str) -> User | None:
        """Lấy chi tiết user theo ID."""
        return await self.user_repo.find_by_id(user_id)

    async def get_all_users(self) -> list[User]:
        """Lấy danh sách tất cả user."""
        return await self.user_repo.find_all()

    async def update_user(
        self, user_id: str, data: UserUpdateRequest
    ) -> tuple[User | None, str | None]:
        """
        Cập nhật user (full_name, role_id, is_active).

        Returns:
            (user, None) nếu thành công;
            (None, error_key) nếu user/role không tồn tại.
        """
        user = await self.user_repo.find_by_id(user_id)
        if user is None:
            return None, "user.not_found"

        if data.role_id is not None:
            role = await self.role_repo.find_role_by_id(data.role_id)
            if role is None:
                return None, "role.not_found"
            user.role_id = data.role_id

        if data.full_name is not None:
            user.full_name = data.full_name
        if data.password is not None:
            user.hashed_password = hash_password(data.password)
        if data.is_active is not None:
            user.is_active = data.is_active

        await self.user_repo.update(user)
        return await self.user_repo.find_by_id(user_id), None

    async def delete_user(self, user_id: str) -> tuple[bool, str | None]:
        """
        Xóa user theo ID.

        Returns:
            (True, None) nếu thành công; (False, error_key) nếu không tìm thấy.
        """
        user = await self.user_repo.find_by_id(user_id)
        if user is None:
            return False, "user.not_found"
        await self.user_repo.delete(user)
        return True, None

    # ── Role & Permission ────────────────────────────

    async def get_all_roles(self):
        """Lấy danh sách tất cả role."""
        return await self.role_repo.find_all_roles()

    async def get_role_permissions(self, role_id: str) -> tuple[list | None, str | None]:
        """Lấy danh sách permission của 1 role."""
        role = await self.role_repo.find_role_by_id(role_id)
        if role is None:
            return None, "role.not_found"
        return role.permissions, None

    async def assign_permission(
        self, role_id: str, permission_id: str
    ) -> tuple[bool, str | None]:
        """Gán 1 permission vào role (phân quyền động)."""
        role = await self.role_repo.find_role_by_id(role_id)
        if role is None:
            return False, "role.not_found"
        permission = await self.role_repo.find_permission_by_id(permission_id)
        if permission is None:
            return False, "role.permission_not_found"
        await self.role_repo.assign_permission(role, permission)
        return True, None

    async def remove_permission(
        self, role_id: str, permission_id: str
    ) -> tuple[bool, str | None]:
        """Bỏ 1 permission khỏi role (phân quyền động)."""
        role = await self.role_repo.find_role_by_id(role_id)
        if role is None:
            return False, "role.not_found"
        permission = await self.role_repo.find_permission_by_id(permission_id)
        if permission is None:
            return False, "role.permission_not_found"
        await self.role_repo.remove_permission(role, permission)
        return True, None

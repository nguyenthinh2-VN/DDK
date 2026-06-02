"""
Role Repository - Data Access Layer cho Role & Permission.

Tương đương: @Repository interface trong Spring / JPA Repository.

Chỉ chịu trách nhiệm CRUD với database, KHÔNG chứa business logic.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.models.permission import Permission


class RoleRepository:
    """Repository pattern cho Role & Permission entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Role ─────────────────────────────────────────

    async def create_role(self, role: Role) -> Role:
        """Lưu mới một Role vào database."""
        self.db.add(role)
        await self.db.flush()
        return role

    async def find_role_by_id(self, role_id: str) -> Role | None:
        """Tìm Role theo ID (kèm permissions nhờ lazy selectin)."""
        stmt = select(Role).where(Role.id == role_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_role_by_name(self, name: str) -> Role | None:
        """Tìm Role theo name (VD: 'CEO')."""
        stmt = select(Role).where(Role.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all_roles(self) -> list[Role]:
        """Lấy tất cả Role, sắp theo level (cao nhất trước)."""
        stmt = select(Role).order_by(Role.level.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ── Permission ───────────────────────────────────

    async def create_permission(self, permission: Permission) -> Permission:
        """Lưu mới một Permission vào database."""
        self.db.add(permission)
        await self.db.flush()
        return permission

    async def find_permission_by_id(self, permission_id: str) -> Permission | None:
        """Tìm Permission theo ID."""
        stmt = select(Permission).where(Permission.id == permission_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_permission_by_code(self, code: str) -> Permission | None:
        """Tìm Permission theo code (VD: 'scan:upload')."""
        stmt = select(Permission).where(Permission.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all_permissions(self) -> list[Permission]:
        """Lấy tất cả Permission."""
        stmt = select(Permission).order_by(Permission.code.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ── Role-Permission (phân quyền động) ────────────

    async def assign_permission(self, role: Role, permission: Permission) -> Role:
        """Gán 1 permission vào role (nếu chưa có)."""
        if permission not in role.permissions:
            role.permissions.append(permission)
            await self.db.flush()
        return role

    async def remove_permission(self, role: Role, permission: Permission) -> Role:
        """Bỏ 1 permission khỏi role (nếu đang có)."""
        if permission in role.permissions:
            role.permissions.remove(permission)
            await self.db.flush()
        return role

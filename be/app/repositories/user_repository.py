"""
User Repository - Data Access Layer cho User.

Tương đương: @Repository interface trong Spring / JPA Repository.

Chỉ chịu trách nhiệm CRUD với database, KHÔNG chứa business logic.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository pattern cho User entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        """Lưu mới một User vào database."""
        self.db.add(user)
        await self.db.flush()
        return user

    async def find_by_id(self, user_id: str) -> User | None:
        """Tìm User theo ID (kèm role + permissions nhờ lazy selectin)."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_username(self, username: str) -> User | None:
        """Tìm User theo username. Trả về None nếu không tìm thấy."""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(self) -> list[User]:
        """Lấy tất cả User."""
        stmt = select(User).order_by(User.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, user: User) -> User:
        """Cập nhật User (đã được modify trước khi gọi hàm này)."""
        await self.db.flush()
        return user

    async def delete(self, user: User) -> None:
        """Xóa User khỏi database."""
        await self.db.delete(user)
        await self.db.flush()

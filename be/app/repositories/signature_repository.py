"""
Repository cho Signature.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signature import Signature


class SignatureRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, signature: Signature) -> Signature:
        self.db.add(signature)
        await self.db.flush()
        return signature

    async def find_all_active_by_user_id(self, user_id: str) -> list[Signature]:
        stmt = (
            select(Signature)
            .where(Signature.user_id == user_id, Signature.is_active.is_(True))
            .order_by(Signature.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_by_id(self, signature_id: str) -> Signature | None:
        stmt = select(Signature).where(Signature.id == signature_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, signature: Signature) -> Signature:
        await self.db.flush()
        return signature

"""
Scan Batch Repository - Data Access Layer cho ScanBatch.

Tương đương: @Repository interface trong Spring / JPA Repository.

Chỉ chịu trách nhiệm CRUD với database, KHÔNG chứa business logic.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan_batch import ScanBatch


class ScanBatchRepository:
    """Repository pattern cho ScanBatch entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, batch: ScanBatch) -> ScanBatch:
        """Lưu mới một ScanBatch vào database."""
        self.db.add(batch)
        await self.db.flush()
        return batch

    async def find_by_id(self, batch_id: str) -> ScanBatch | None:
        """Tìm ScanBatch theo ID (kèm danh sách scans nhờ lazy selectin)."""
        stmt = select(ScanBatch).where(ScanBatch.id == batch_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(self) -> list[ScanBatch]:
        """Lấy tất cả ScanBatch, mới nhất trước."""
        stmt = select(ScanBatch).order_by(ScanBatch.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, batch: ScanBatch) -> ScanBatch:
        """Cập nhật ScanBatch (đã được modify trước khi gọi)."""
        await self.db.flush()
        return batch

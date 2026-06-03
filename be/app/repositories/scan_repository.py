"""
Scan Repository - Data Access Layer cho ScanResult.

Tương đương: @Repository interface trong Spring / JPA Repository.

Tầng Repository: chỉ chịu trách nhiệm CRUD với database.
- KHÔNG chứa business logic
- Chỉ query / insert / update / delete
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan_result import ScanResult


class ScanRepository:
    """
    Repository pattern cho ScanResult entity.

    Tương đương: public interface ScanResultRepository extends JpaRepository<ScanResult, String>
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, scan_result: ScanResult) -> ScanResult:
        """Lưu mới một ScanResult vào database."""
        self.db.add(scan_result)
        await self.db.flush()
        return scan_result

    async def find_by_id(self, scan_id: str) -> ScanResult | None:
        """Tìm ScanResult theo ID. Trả về None nếu không tìm thấy."""
        stmt = select(ScanResult).where(ScanResult.id == scan_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(self) -> list[ScanResult]:
        """Lấy tất cả ScanResult."""
        stmt = select(ScanResult).order_by(ScanResult.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_by_batch_id(self, batch_id: str) -> list[ScanResult]:
        """Lấy tất cả ScanResult thuộc 1 batch, theo thứ tự tạo."""
        stmt = (
            select(ScanResult)
            .where(ScanResult.batch_id == batch_id)
            .order_by(ScanResult.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, scan_result: ScanResult) -> ScanResult:
        """Cập nhật ScanResult (đã được modify trước khi gọi hàm này)."""
        await self.db.flush()
        return scan_result

    async def delete(self, scan_id: str) -> bool:
        """Xóa ScanResult theo ID. Trả về True nếu xóa thành công."""
        scan_result = await self.find_by_id(scan_id)
        if scan_result:
            await self.db.delete(scan_result)
            await self.db.flush()
            return True
        return False

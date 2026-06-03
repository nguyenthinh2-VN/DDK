"""
Stats API Router - Endpoints cho thống kê Dashboard.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.scan_result import ScanResult
from app.models.user import User
from app.utils.auth_guard import require_permission

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get(
    "/dashboard",
    summary="Lấy dữ liệu thống kê cho Dashboard",
)
async def get_dashboard_stats(
    current_user: User = Depends(require_permission("scan:read")),
    db: AsyncSession = Depends(get_db),
):
    """
    Trả về số liệu thống kê: tổng file, số file thành công, số file lỗi.
    """
    # Total uploaded files
    stmt_total = select(func.count(ScanResult.id))
    total = await db.scalar(stmt_total) or 0

    # Total scanned (completed) slips
    stmt_scanned = select(func.count(ScanResult.id)).where(ScanResult.status == "completed")
    scanned = await db.scalar(stmt_scanned) or 0

    # Total failed slips
    stmt_failed = select(func.count(ScanResult.id)).where(ScanResult.status == "failed")
    failed = await db.scalar(stmt_failed) or 0

    return {
        "total_uploaded_files": total,
        "total_scanned_slips": scanned,
        "total_failed_slips": failed
    }

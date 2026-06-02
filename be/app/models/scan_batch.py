"""
ScanBatch Model (Entity) - ORM model cho bảng scan_batches.

Tương đương: @Entity class trong Spring / JPA.

Gom 1 lần upload nhiều file (3–5) thành 1 batch để FE theo dõi tiến độ
xử lý OCR bất đồng bộ. Mỗi batch có nhiều ScanResult (quan hệ 1-N).
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class ScanBatch(Base):
    """Entity gom nhiều file scan trong 1 lần upload."""

    __tablename__ = "scan_batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    total_files = Column(Integer, nullable=False, comment="Tổng số file trong batch")
    completed_files = Column(Integer, default=0, nullable=False, comment="Số file đã xử lý xong")
    failed_files = Column(Integer, default=0, nullable=False, comment="Số file lỗi")
    status = Column(
        String(20),
        default="pending",
        comment="pending | processing | completed | partial_failed",
    )
    uploaded_by = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
        comment="User upload (lấy từ JWT)",
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Quan hệ 1-N với ScanResult
    scans = relationship(
        "ScanResult",
        back_populates="batch",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ScanBatch(id={self.id}, total={self.total_files}, status={self.status})>"

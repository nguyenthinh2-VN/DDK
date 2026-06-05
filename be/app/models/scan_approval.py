"""
ScanApproval Model (Entity) - Log lịch sử duyệt/từ chối phiếu.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class ScanApproval(Base):
    """
    Entity lưu lịch sử phê duyệt phiếu của các Role.
    """

    __tablename__ = "scan_approvals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_result_id = Column(
        String(36),
        ForeignKey("scan_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(50), nullable=False, comment="Role lúc duyệt (e.g. KE_TOAN, THU_QUY)")
    action = Column(String(20), nullable=False, comment="APPROVED | REJECTED")
    note = Column(String(500), nullable=True, comment="Lý do reject (nếu có)")
    signature_id = Column(
        String(36),
        ForeignKey("signatures.id", ondelete="SET NULL"),
        nullable=True,
        comment="Chữ ký đã dùng để duyệt",
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan_result = relationship("ScanResult", back_populates="approvals", lazy="selectin")
    user = relationship("User", lazy="selectin")
    signature = relationship("Signature", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ScanApproval(id={self.id}, action={self.action}, role={self.role})>"

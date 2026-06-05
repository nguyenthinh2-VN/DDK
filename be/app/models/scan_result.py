"""
ScanResult Model (Entity) - ORM model cho bảng scan_results.

Tương đương: @Entity class trong Spring / JPA.

Đây là tầng Entity: định nghĩa cấu trúc bảng trong database.
Cập nhật v2: thêm batch_id, document_type, ocr_json, ocr_raw_json,
confidence_avg, error_message; đổi text fields sang LONGTEXT.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base


class ScanResult(Base):
    """
    Entity lưu kết quả scan OCR cho 1 phiếu (1 ảnh = 1 phiếu).

    Tương đương @Entity @Table(name = "scan_results") trong JPA.
    """

    __tablename__ = "scan_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(
        String(36),
        ForeignKey("scan_batches.id", ondelete="CASCADE"),
        nullable=True,
        comment="Thuộc batch nào (1 lần upload nhiều file)",
    )
    original_filename = Column(String(255), nullable=False, comment="Tên file gốc upload")
    image_path = Column(String(500), nullable=False, comment="Đường dẫn ảnh gốc đã lưu")
    processed_image_path = Column(String(500), nullable=True, comment="Đường dẫn ảnh đã tiền xử lý OpenCV")
    document_type = Column(
        String(50),
        default="advance_payment_slip",
        comment="Loại phiếu (mở rộng sau)",
    )
    ocr_text = Column(LONGTEXT, nullable=True, comment="Text OCR gộp (plain)")
    ocr_json = Column(JSON, nullable=True, comment="Kết quả structured theo template")
    ocr_raw_json = Column(JSON, nullable=True, comment="Output thô PaddleOCR (text+bbox+confidence)")
    html_content = Column(LONGTEXT, nullable=True, comment="HTML tái dựng bố cục")
    confidence_avg = Column(Float, nullable=True, comment="Độ tin cậy trung bình")
    status = Column(String(20), default="pending", comment="pending | processing | completed | failed")
    error_message = Column(LONGTEXT, nullable=True, comment="Lý do nếu failed")
    workflow_status = Column(String(50), default="DRAFT", comment="DRAFT | PENDING_KE_TOAN | PENDING_THU_QUY | PENDING_CEO | COMPLETED | REJECTED")
    current_assignee_role = Column(String(50), nullable=True, comment="Role đang chờ duyệt")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Quan hệ N-1 với ScanBatch
    batch = relationship("ScanBatch", back_populates="scans", lazy="selectin")
    
    # Quan hệ 1-N với ScanApproval
    approvals = relationship("ScanApproval", back_populates="scan_result", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ScanResult(id={self.id}, filename={self.original_filename}, status={self.status})>"

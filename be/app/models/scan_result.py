"""
ScanResult Model (Entity) - ORM model cho bảng scan_results.

Tương đương: @Entity class trong Spring / JPA.

Đây là tầng Entity: định nghĩa cấu trúc bảng trong database.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime
from app.database.base import Base


class ScanResult(Base):
    """
    Entity lưu kết quả scan OCR.

    Tương đương @Entity @Table(name = "scan_results") trong JPA.
    """

    __tablename__ = "scan_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String(255), nullable=False, comment="Tên file gốc upload")
    image_path = Column(String(500), nullable=False, comment="Đường dẫn file ảnh đã lưu")
    ocr_text = Column(Text, nullable=True, comment="Nội dung text OCR trích xuất được")
    html_content = Column(Text, nullable=True, comment="Nội dung HTML đã generate")
    status = Column(String(20), default="pending", comment="Trạng thái: pending | processing | completed | failed")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ScanResult(id={self.id}, filename={self.original_filename}, status={self.status})>"

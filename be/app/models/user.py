"""
User Model (Entity) - ORM model cho bảng users.

Tương đương: @Entity class User trong Spring / JPA.

Mỗi User có đúng 1 Role (quan hệ Many-to-One: nhiều user -> 1 role).
Mật khẩu luôn được lưu dưới dạng hash (bcrypt), không lưu plaintext.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class User(Base):
    """Entity người dùng nội bộ."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, comment="Tên đăng nhập")
    hashed_password = Column(String(255), nullable=False, comment="Mật khẩu đã hash (bcrypt)")
    full_name = Column(String(255), nullable=False, comment="Họ tên đầy đủ")
    role_id = Column(
        String(36),
        ForeignKey("roles.id"),
        nullable=False,
        comment="FK tới roles (1 user có 1 role)",
    )
    is_active = Column(Boolean, default=True, nullable=False, comment="Tài khoản có hoạt động không")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Quan hệ N-1 với Role (eager load để lấy role + permissions khi auth)
    role = relationship("Role", back_populates="users", lazy="selectin")
    signatures = relationship("Signature", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role_id={self.role_id})>"

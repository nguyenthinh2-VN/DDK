"""
Permission Model (Entity) - ORM model cho bảng permissions.

Tương đương: @Entity class Permission trong Spring / JPA.

Mỗi Permission là 1 quyền cụ thể (VD: scan:upload, user:create).
Một Permission có thể thuộc nhiều Role (quan hệ Many-to-Many).
"""

import uuid

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.role_permission import role_permissions


class Permission(Base):
    """Entity quyền hạn (VD: scan:upload, user:create)."""

    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(100), unique=True, nullable=False, comment="VD: scan:upload, user:create")
    name = Column(String(255), nullable=False, comment="Tên hiển thị của quyền")

    # Quan hệ N-N với Role qua bảng role_permissions
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, code={self.code})>"

"""
Role Model (Entity) - ORM model cho bảng roles.

Tương đương: @Entity class Role trong Spring / JPA.

Mỗi Role có 1 cấp bậc (level) và nhiều Permission (quan hệ Many-to-Many
qua bảng role_permissions). Một User chỉ có 1 Role.
"""

import uuid

from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.role_permission import role_permissions


class Role(Base):
    """Entity vai trò (CEO, DIRECTOR, MANAGER, EMPLOYEE)."""

    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False, comment="CEO | DIRECTOR | MANAGER | EMPLOYEE")
    display_name = Column(String(100), nullable=False, comment="Tên hiển thị")
    level = Column(Integer, nullable=False, comment="Cấp bậc: CEO=1 cao nhất, EMPLOYEE=4 thấp nhất")

    # Quan hệ N-N với Permission qua bảng role_permissions
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )

    # Quan hệ 1-N với User (1 role có nhiều user)
    users = relationship("User", back_populates="role", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name}, level={self.level})>"

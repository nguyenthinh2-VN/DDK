"""
Role-Permission Association - Bảng trung gian Many-to-Many.

Tương đương: @JoinTable trong JPA (quan hệ @ManyToMany giữa Role và Permission).

Đây là bảng nối phân quyền động: admin có thể thêm/bớt permission cho role
bất kỳ lúc nào bằng cách insert/delete dòng trong bảng này.
"""

from sqlalchemy import Table, Column, String, ForeignKey

from app.database.base import Base

# Bảng trung gian role_permissions (không cần Model class riêng)
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

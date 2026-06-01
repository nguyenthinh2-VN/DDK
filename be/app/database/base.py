"""
Database Base - Base class cho tất cả ORM models.

Tương đương: BaseEntity trong Spring / JPA.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class cho tất cả SQLAlchemy models.

    Mọi model (entity) đều kế thừa từ class này.
    Tương đương @MappedSuperclass trong JPA/Hibernate.
    """
    pass

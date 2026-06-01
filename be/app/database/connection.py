"""
Database Connection - Kết nối và quản lý session database.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config.settings import settings

# Tạo async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

# Session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """
    Dependency injection cho FastAPI - cung cấp database session.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

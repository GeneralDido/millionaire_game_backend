from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from .db import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async DB sessions"""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

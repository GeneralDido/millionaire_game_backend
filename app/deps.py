from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from .db import AsyncSessionLocal
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from .config import settings


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


api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


async def get_admin_key(key: str | None = Security(api_key_header)):
    if key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Not authorized")
    return key

# app/db.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    echo=True
)

# Use async_sessionmaker for async sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

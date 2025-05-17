import os
import asyncio
import uuid
import pytest

from unittest.mock import patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.deps import get_db
from tests.test_models import TestBase, Game, Player, Score

# ── Shared in-memory DB engine and sessionmaker ───────────────────────────
TEST_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    future=True,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# ── Override dependency to use test DB sessions ──────────────────────────
async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


# ── Drop and (re)create tables between tests ───────────────────────────
@pytest.fixture(autouse=True)
async def reset_db_for_tests():
    """Reset the database tables before each test.

    This provides stricter isolation than transaction rollback alone,
    ensuring each test starts with completely clean tables.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)
        await conn.run_sync(TestBase.metadata.create_all)
    yield


# ── Per-test DB session with rollback ───────────────────────────────────
@pytest.fixture
async def db_session():
    """Provides an async session for testing with a transaction rollback.

    Each test function that uses this fixture will get a fresh database session
    that is rolled back at the end, ensuring test isolation.
    """
    async with TestSessionLocal() as session:
        # Start a nested transaction
        async with session.begin():
            # Provide the session to the test
            yield session
            # Roll back the transaction to ensure test isolation
            await session.rollback()


# ── Async HTTP client mounted in-process via ASGI ────────────────────────
@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ── Optional sync TestClient ───────────────────────────────────────────
@pytest.fixture
def test_client():
    with TestClient(app) as tc:
        yield tc


# ── Mock settings for tests ────────────────────────────────────────────
@pytest.fixture(autouse=True)
def mock_settings():
    with patch("app.config.settings") as ms:
        ms.DATABASE_URL = TEST_DATABASE_URL
        ms.OPENAI_API_KEY = "sk-test-key"
        yield ms


# ── Patch models to use test-specific models ────────────────────────────
@pytest.fixture(autouse=True)
def patch_models():
    with patch("app.routers.games.Game", Game), \
            patch("app.routers.scores.Game", Game), \
            patch("app.routers.scores.Player", Player), \
            patch("app.routers.scores.Score", Score), \
            patch("app.routers.leaderboard.Player", Player), \
            patch("app.routers.leaderboard.Score", Score):
        yield


# ── Helper function to generate unique hash values ────────────────────────
@pytest.fixture
def unique_hash():
    """Generate a unique hash for each test to avoid unique constraint violations."""
    return f"test_hash_{uuid.uuid4().hex[:8]}"

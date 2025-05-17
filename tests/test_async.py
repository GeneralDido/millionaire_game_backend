# tests/test_async.py
import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_models import Game


@pytest.mark.asyncio
async def test_db_setup(db_session: AsyncSession):
    """Test that the database is set up correctly."""
    # Check if the games table exists
    result = await db_session.execute(select(func.count()).select_from(Game))
    count = result.scalar()

    # No games should exist at the start
    assert count == 0

    # Insert a test game
    test_game = Game(
        questions_json={"test": "data"},
        questions_hash="test_hash"
    )
    db_session.add(test_game)
    await db_session.flush()

    # Verify the game was inserted
    result = await db_session.execute(select(Game).filter(Game.questions_hash == "test_hash"))
    game = result.scalars().first()
    assert game is not None
    assert game.questions_hash == "test_hash"

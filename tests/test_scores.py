# tests/test_scores.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from tests.test_models import Player, Score

from tests.mocks import mock_openai


@pytest.mark.asyncio
async def test_submit_score(client: AsyncClient, db_session: AsyncSession, mock_openai):
    """Test submitting a score for a game."""
    # First create a game
    game_response = await client.post("/games/")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]

    # Submit a score
    score_data = {
        "player_name": "TestPlayer",
        "score": 1000
    }
    response = await client.post(f"/games/{game_id}/score", json=score_data)
    assert response.status_code == 201
    assert response.json()["message"] == "Score submitted successfully"

    # Verify score was saved to database
    result = await db_session.execute(
        select(Score).where(Score.game_id == game_id)  # type: ignore[arg-type]
    )
    score = result.scalars().first()
    assert score is not None
    assert score.score == 1000

    # Verify player was created
    result = await db_session.execute(
        select(Player).where(Player.name == "TestPlayer")
    )
    player = result.scalars().first()
    assert player is not None


@pytest.mark.asyncio
async def test_submit_score_existing_player(client: AsyncClient, db_session: AsyncSession, mock_openai):
    """Test submitting a score for an existing player."""
    # Create a game
    game_response = await client.post("/games/")
    game_id = game_response.json()["game_id"]

    # Submit first score to create the player
    score_data1 = {
        "player_name": "ExistingPlayer",
        "score": 500
    }
    await client.post(f"/games/{game_id}/score", json=score_data1)

    # Submit second score with same player
    score_data2 = {
        "player_name": "ExistingPlayer",
        "score": 1500
    }
    response = await client.post(f"/games/{game_id}/score", json=score_data2)
    assert response.status_code == 201

    # Verify we have two scores but only one player
    result = await db_session.execute(
        select(func.count()).select_from(Score).filter(Score.game_id == game_id)  # type: ignore[arg-type]
    )
    score_count = result.scalar()
    assert score_count == 2

    result = await db_session.execute(
        select(func.count()).select_from(Player).filter(Player.name == "ExistingPlayer")
    )
    player_count = result.scalar()
    assert player_count == 1


@pytest.mark.asyncio
async def test_submit_score_nonexistent_game(client: AsyncClient):
    """Test submitting a score for a game that doesn't exist."""
    score_data = {
        "player_name": "TestPlayer",
        "score": 1000
    }
    response = await client.post("/games/999/score", json=score_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"

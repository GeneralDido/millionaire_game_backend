# tests/test_leaderboard.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_models import Game, Player, Score


async def setup_leaderboard_data(db_session: AsyncSession, hash_suffix=None, name_suffix=None):
    """Helper to set up test data for leaderboard."""
    import uuid

    unique_hash = f"test_hash_{hash_suffix or uuid.uuid4().hex[:8]}"
    name_suffix = name_suffix or uuid.uuid4().hex[:6]

    # Create a game
    game = Game(questions_json={"questions": []}, questions_hash=unique_hash)
    db_session.add(game)
    await db_session.flush()

    # Create players
    players = [
        Player(name=f"Player1_{name_suffix}"),
        Player(name=f"Player2_{name_suffix}"),
        Player(name=f"Player3_{name_suffix}")
    ]
    db_session.add_all(players)
    await db_session.flush()

    # Create scores
    scores = [
        # Player1 has two scores, one higher
        Score(player_id=players[0].id, game_id=game.id, score=1000),
        Score(player_id=players[0].id, game_id=game.id, score=1500),
        # Player2 has one score
        Score(player_id=players[1].id, game_id=game.id, score=2000),
        # Player3 has one score
        Score(player_id=players[2].id, game_id=game.id, score=500)
    ]
    db_session.add_all(scores)
    await db_session.commit()
    return game, players, scores


@pytest.mark.asyncio
async def test_get_leaderboard(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving the leaderboard."""
    # Setup test data
    _, players, scores = await setup_leaderboard_data(
        db_session,
        hash_suffix="leaderboard_test",
        name_suffix="leaderboard_test"
    )

    response = await client.get("/leaderboard/")
    assert response.status_code == 200
    data = response.json()

    # Must contain at least 3 entries
    assert len(data) >= 3

    # Verify fields and types
    for entry in data:
        assert isinstance(entry["player"], str)
        assert isinstance(entry["best"], int)
        assert isinstance(entry["game_id"], int)
        # played_at comes back as ISO string
        assert isinstance(entry["played_at"], str)

    # Sorted by best score descending
    for i in range(len(data) - 1):
        assert data[i]["best"] >= data[i + 1]["best"]

    # Top score at least 2000
    assert data[0]["best"] >= 2000


@pytest.mark.asyncio
async def test_get_leaderboard_limit(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving the leaderboard with a limit."""
    # Setup test data
    _, players, scores = await setup_leaderboard_data(
        db_session,
        hash_suffix="leaderboard_limit_test",
        name_suffix="limit_test"
    )

    response = await client.get("/leaderboard/?limit=2")
    assert response.status_code == 200
    data = response.json()

    # Respect limit
    assert len(data) == 2
    assert data[0]["best"] >= data[1]["best"]

    # Verify new fields in each entry
    for entry in data:
        assert isinstance(entry["game_id"], int)
        assert isinstance(entry["played_at"], str)

    # Ensure correct players present
    names = [e["player"] for e in data]
    assert any(n.startswith("Player1_") for n in names)
    assert any(n.startswith("Player2_") for n in names)

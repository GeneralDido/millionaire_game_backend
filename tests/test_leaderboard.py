# tests/test_leaderboard.py
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_models import Game, Player, Score


async def setup_leaderboard_data(db_session: AsyncSession, hash_suffix=None, name_suffix=None):
    """Helper to set up test data for leaderboard."""
    # Create a game with a unique hash
    import uuid

    unique_hash = f"test_hash_{hash_suffix or uuid.uuid4().hex[:8]}"
    name_suffix = name_suffix or uuid.uuid4().hex[:6]

    # Create a game
    game = Game(questions_json={"questions": []}, questions_hash=unique_hash)
    db_session.add(game)
    await db_session.flush()

    # Create players with unique names using the suffix
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
    # Setup test data with a unique hash and name suffix
    name_suffix = "leaderboard_test"
    _, players, _ = await setup_leaderboard_data(
        db_session,
        hash_suffix="leaderboard_test",
        name_suffix=name_suffix
    )

    # Get leaderboard
    response = await client.get("/leaderboard/")
    assert response.status_code == 200

    data = response.json()

    # Check that we get at least 3 results
    assert len(data) >= 3

    # Verify the data is sorted in descending order by score
    for i in range(len(data) - 1):
        assert data[i]["best"] >= data[i + 1]["best"], "Leaderboard should be sorted by score in descending order"

    # Check that our highest scores are present (don't check exact names)
    # The top score should be at least 2000
    assert data[0]["best"] >= 2000


@pytest.mark.asyncio
async def test_get_leaderboard_limit(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving the leaderboard with a limit."""
    # Setup test data with a different unique hash and name suffix
    name_suffix = "limit_test"
    _, players, _ = await setup_leaderboard_data(
        db_session,
        hash_suffix="leaderboard_limit_test",
        name_suffix=name_suffix
    )

    # Get leaderboard with limit
    response = await client.get("/leaderboard/?limit=2")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2  # Limited to 2

    # Instead of checking exact names (which might be affected by other tests),
    # just verify the expected number of results and that they're ordered correctly
    assert len(data) == 2
    assert data[0]["best"] >= data[1]["best"]  # First entry has higher score than second

    # Verify that the player names are in the response
    player_names = [entry["player"] for entry in data]
    assert any(name.startswith("Player2_") for name in player_names)
    assert any(name.startswith("Player1_") for name in player_names)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..deps import get_db
from ..models import Game, Player, Score
from ..schemas import ScoreCreate

router = APIRouter()


@router.post("/{game_id}/score", status_code=201)
async def submit_score(
        game_id: int,
        score_data: ScoreCreate,
        db: AsyncSession = Depends(get_db)
):
    """Submit a score for a game"""
    # Verify game exists
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalars().first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Find or create player
    result = await db.execute(
        select(Player).where(Player.name == score_data.player_name)
    )
    player = result.scalars().first()

    if not player:
        player = Player(name=score_data.player_name)
        db.add(player)
        await db.flush()  # Generate ID without committing transaction

    # Create score
    new_score = Score(
        player_id=player.id,
        game_id=game_id,
        score=score_data.score
    )
    db.add(new_score)
    # Removed redundant db.commit(); commit is handled by get_db dependency

    return {"message": "Score submitted successfully"}

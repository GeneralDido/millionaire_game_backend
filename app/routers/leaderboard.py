# app/routers/leaderboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from ..deps import get_db
from ..models import Player, Score
from ..schemas import LeaderboardEntry

router = APIRouter()


@router.get("/", response_model=List[LeaderboardEntry])
async def get_leaderboard(
        limit: int = 10,
        db: AsyncSession = Depends(get_db)
):
    """Get global leaderboard with the highest scores"""
    # Subquery to find best score per player
    subq = select(
        Score.player_id,
        func.max(Score.score).label("best_score")
    ).group_by(Score.player_id).subquery()

    # Use select_from with join expression
    query = (
        select(
            Player.name.label("player"),
            subq.c.best_score.label("best")
        )
        .select_from(Player)
        .join(subq, Player.id == subq.c.player_id)  # type: ignore[arg-type]
        .order_by(subq.c.best_score.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    leaderboard_entries = [
        {"player": row.player, "best": row.best}
        for row in result.all()
    ]
    return leaderboard_entries

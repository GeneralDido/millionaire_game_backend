# app/routers/leaderboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
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
    # 1. subquery: best score per player
    subq = (
        select(
            Score.player_id,
            func.max(Score.score).label("best_score")
        )
        .group_by(Score.player_id)
        .subquery()
    )

    # 2. join Player → subq → Score to fetch the game_id and played_at for that best_score
    query = (
        select(
            Player.name.label("player"),
            subq.c.best_score.label("best"),
            Score.game_id.label("game_id"),
            Score.played_at.label("played_at"),
        )
        .select_from(Player)
        .join(subq, Player.id == subq.c.player_id)  # type: ignore[arg-type]
        .join(
            Score,
            and_(
                Score.player_id == subq.c.player_id,
                Score.score == subq.c.best_score,
            )
        )
        .order_by(subq.c.best_score.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    # 3. map to dicts for Pydantic
    return [
        {
            "player": r.player,
            "best": r.best,
            "game_id": r.game_id,
            "played_at": r.played_at,
        }
        for r in rows
    ]

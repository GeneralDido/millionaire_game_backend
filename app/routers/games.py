from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any

from ..deps import get_db, get_admin_key
from ..models import Game
from ..schemas import GameCreate, GameRead, Question
from ..services.questions import generate_questions

router = APIRouter()


def _build_game_response(game_id: int, game_data: Dict[str, Any]) -> GameRead:
    """Helper to build consistent GameRead responses"""
    return GameRead(
        game_id=game_id,
        questions=[Question.model_validate(q) for q in game_data["questions"]],
        bonus_question=(Question.model_validate(game_data["bonus_question"])
                        if game_data.get("bonus_question") else None)
    )


@router.post("/", response_model=GameRead)
async def create_game(
        _: GameCreate = None,
        _admin_key: str = Depends(get_admin_key),
        db: AsyncSession = Depends(get_db)
):
    """Create a new game with 15 questions and a bonus question, or fetch existing game with same questions"""

    # Generate questions with OpenAI
    questions, bonus_question, questions_hash = await generate_questions()

    # Prepare the query once
    stmt = select(Game).where(Game.questions_hash == questions_hash)

    # Check if a game with this hash already exists
    result = await db.execute(stmt)
    existing_game = result.scalars().first()

    if existing_game:
        # Return existing game if found
        return _build_game_response(existing_game.id, existing_game.questions_json)

    # Create new game record
    game_data = {
        "questions": [q.model_dump() for q in questions],
        "bonus_question": bonus_question.model_dump() if bonus_question else None
    }
    new_game = Game(
        questions_json=game_data,
        questions_hash=questions_hash
    )
    db.add(new_game)

    # flush so new_game.id is populated
    await db.flush()
    # reloads all columns from the DB
    await db.refresh(new_game)

    try:
        return GameRead(
            game_id=new_game.id,
            questions=questions,
            bonus_question=bonus_question
        )
    except IntegrityError:
        # Race condition: another inserted same hash
        await db.rollback()
        # Re-use the same query from above
        result = await db.execute(stmt)
        existing = result.scalars().first()
        if not existing:
            # Very unlikely, but handle it gracefully
            raise HTTPException(status_code=500, detail="Failed to retrieve game after conflict")
        return _build_game_response(existing.id, existing.questions_json)


@router.get("/list")
async def list_games(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game.id, Game.created_at).order_by(Game.created_at))
    return [{"game_id": gid, "created_at": at} for gid, at in result.all()]


@router.get("/random", response_model=GameRead)
async def random_game(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).order_by(func.random()).limit(1))
    game = result.scalars().first()
    if not game:
        raise HTTPException(404, "No games available")
    return _build_game_response(game.id, game.questions_json)


@router.get("/{game_id}", response_model=GameRead)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific game by ID"""
    stmt = select(Game).where(Game.id == game_id)
    result = await db.execute(stmt)
    game = result.scalars().first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return _build_game_response(game.id, game.questions_json)

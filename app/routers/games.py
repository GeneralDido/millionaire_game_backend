from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any

from ..deps import get_db
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
    try:
        # Using commit directly which implicitly flushes
        await db.commit()
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


@router.get("/{game_id}", response_model=GameRead)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific game by ID"""
    stmt = select(Game).where(Game.id == game_id)
    result = await db.execute(stmt)
    game = result.scalars().first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return _build_game_response(game.id, game.questions_json)

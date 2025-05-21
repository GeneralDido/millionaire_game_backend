from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Question(BaseModel):
    q: str
    correct: str
    wrong: List[str]
    difficulty: int
    category: str
    hint: Optional[str]


class GameCreate(BaseModel):
    """(reserved) additional options for game creation (e.g. category, difficulty)"""
    # no fields yet
    pass


class GameRead(BaseModel):
    game_id: int
    questions: List[Question]
    bonus_question: Optional[Question] = None


class GameUpdate(BaseModel):
    """
    Admin payload for updating an existing game.
    """
    prompt: str


class ScoreCreate(BaseModel):
    player_name: str
    score: int


class LeaderboardEntry(BaseModel):
    player: str
    best: int
    game_id: int
    played_at: Optional[datetime]


class ExistsResponse(BaseModel):
    exists: bool

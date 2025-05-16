from pydantic import BaseModel
from typing import List, Optional


class Question(BaseModel):
    q: str
    correct: str
    wrong: List[str]
    hint: Optional[str]


class GameCreate(BaseModel):
    # body is not needed for basic game-create; extend later for category or mode
    pass


class GameRead(BaseModel):
    game_id: int
    questions: List[Question]
    bonus_question: Optional[Question] = None


class ScoreCreate(BaseModel):
    player_name: str
    score: int


class LeaderboardEntry(BaseModel):
    player: str
    best: int

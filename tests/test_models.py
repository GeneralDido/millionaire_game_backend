# tests/test_models.py
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, JSON
from sqlalchemy.orm import declarative_base

# Create test-specific Base
TestBase = declarative_base()


class Game(TestBase):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    # Use JSON instead of JSONB for SQLite compatibility
    questions_json = Column(JSON, nullable=False)
    questions_hash = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime, server_default=func.now())


class Player(TestBase):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Score(TestBase):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    score = Column(Integer, nullable=False)
    played_at = Column(DateTime, server_default=func.now())

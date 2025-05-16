from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    questions_json = Column(JSONB, nullable=False)
    questions_hash = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime, server_default=func.now())


class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    score = Column(Integer, nullable=False)
    played_at = Column(DateTime, server_default=func.now())

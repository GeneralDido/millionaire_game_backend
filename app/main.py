# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routers import games, leaderboard, scores
from app.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # No auto-create in production; Alembic migrations manage schema
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Millionaire API",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router, prefix="/games", tags=["games"])
app.include_router(scores.router, prefix="/games", tags=["scores"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "1.0.0"}

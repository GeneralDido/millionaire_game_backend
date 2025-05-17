# Millionaire Quiz API

A lightweight FastAPI backend for a quiz-style game inspired by "Who Wants to Be a Millionaire". It generates
multiple-choice questions (and a bonus question) using the OpenAI API, stores games and scores in PostgreSQL, and
exposes leaderboard data.

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Getting Started](#getting-started)

    * [Prerequisites](#prerequisites)
    * [Clone & Install](#clone--install)
    * [Environment Variables](#environment-variables)
    * [Database Migrations](#database-migrations)
    * [Run Locally](#run-locally)
4. [Docker Compose](#docker-compose)
5. [Deployment to Render](#deployment-to-render)
6. [API Reference](#api-reference)

    * [Health Check](#health-check)
    * [Create Game](#create-game)
    * [Get Game](#get-game)
    * [Submit Score](#submit-score)
    * [Leaderboard](#leaderboard)
7. [Data Models & Schemas](#data-models--schemas)
8. [Testing](#testing)
9. [Configuration](#configuration)
10. [License](#license)

---

## Features

* Generate a new quiz with 15 questions + a bonus question via the OpenAI API
* Idempotent game creation: repeated calls return the same game for identical question sets
* Submit scores by player name without full user authentication
* Global leaderboard showing highest score per player
* SQLite for local testing, PostgreSQL for production
* Alembic migrations for schema management
* Docker Compose for easy local development

## Tech Stack

* **FastAPI** for building the HTTP API
* **SQLAlchemy 2.0** (async) for ORM
* **Alembic** for database migrations
* **Pydantic v2** for request/response schemas
* **OpenAI** for question generation
* **PostgreSQL** (asyncpg) in production
* **SQLite** (aiosqlite) for tests
* **pytest** + **pytest-asyncio** for testing
* **Docker Compose** for local containers

## Getting Started

### Prerequisites

* Python 3.11+
* Git
* [Poetry](https://python-poetry.org/) or `pip` for dependency management
* Docker & Docker Compose (optional)

### Clone & Install

```bash
git clone https://github.com/yourname/millionaire-backend.git
cd millionaire-backend
```

**With Poetry**:

```bash
poetry install
poetry shell
```

**Or with pip**:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root with:

```ini
# .env
DATABASE_URL = postgresql+asyncpg://user:password@localhost:5432/millionaire
OPENAI_API_KEY = sk-...
# Optional:
ALLOWED_ORIGINS = ["http://localhost:3000"]
DB_ECHO = false
```

### Database Migrations

Initialize or upgrade your database schema using Alembic:

```bash
alembic upgrade head
```

### Run Locally

```bash
uvicorn app.main:app --reload
```

Open your browser at `http://localhost:8000/docs` for the interactive OpenAPI docs.

## Docker Compose

Bring up PostgreSQL + API together with one command:

```bash
docker-compose up --build -d
```

* **API** listens on `http://localhost:8000`
* **Postgres** on port `5432`

Apply migrations inside the API container:

```bash
docker-compose exec api alembic upgrade head
```

## Deployment to Render

1. **Create** a new Web Service on Render, connect your repo.
2. **Build Command**: `pip install -r requirements.txt`
3. **Pre-Deploy Command**: `alembic upgrade head`
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Environment**:

    * `DATABASE_URL` → copy the **Internal Database URL** from Render Postgres
    * `OPENAI_API_KEY` → your key
    * (optional) `ALLOWED_ORIGINS` → e.g. `["http://localhost:3000","https://quiz-ui.vercel.app"]`
6. **Health Check Path**: `/health`

---

## API Reference

Base URL: `http://localhost:8000/` (or your Render URL)

### Health Check

```http
GET /health
```

**Response**

```json
{
  "status": "ok"
}
```

### Create Game

```http
POST /games/
```

**Description**: Generates (or retrieves) a game.
Returns 15 questions + a bonus.

**Response** `200 OK`

```text
{
  "game_id": 1,
  "questions": [
    /* array of Question */
  ],
  "bonus_question": {
    /* Question */
  }
}
```

### Get Game

```http
GET /games/{game_id}
```

**Response** `200 OK` or `404 Not Found`

```text
/* same JSON schema as Create Game */
```

### Submit Score

```http
POST /games/{game_id}/score
Content-Type: application/json
```

**Body** (ScoreCreate)

```json
{
  "player_name": "YourName",
  "score": 1200
}
```

**Response** `201 Created`

```json
{
  "message": "Score submitted successfully"
}
```

### Leaderboard

```http
GET /leaderboard/?limit=10
```

**Response** `200 OK`

```json
[
  {
    "player": "Alice",
    "best": 2000
  },
  {
    "player": "Bob",
    "best": 1500
  },
  "..."
]
```

## Data Models & Schemas

* **Game** (SQLAlchemy)

    * `id: int`
    * `questions_json: JSON`
    * `questions_hash: str`
    * `created_at: datetime`

* **Player** (SQLAlchemy)

    * `id: int`
    * `name: str`

* **Score** (SQLAlchemy)

    * `id: int`
    * `player_id: int`
    * `game_id: int`
    * `score: int`
    * `played_at: datetime`

* **Question** (Pydantic)

    * `q: str`
    * `correct: str`
    * `wrong: List[str]`
    * `hint: Optional[str]`

* **GameRead** (Pydantic)

    * `game_id: int`
    * `questions: List[Question]`
    * `bonus_question: Optional[Question]`

* **ScoreCreate**

    * `player_name: str`
    * `score: int`

* **LeaderboardEntry**

    * `player: str`
    * `best: int`

## Testing

Run tests locally:

```bash
# Load test environment
cp .env.test .env
pytest -xvs
```

Or use the provided script:

```bash
./run_tests.sh
```

All tests pass against an in-memory SQLite database.

## Configuration

| Env Var           | Description                                        | Default                     |
|-------------------|----------------------------------------------------|-----------------------------|
| `DATABASE_URL`    | SQLAlchemy database URL (`postgresql+asyncpg://…`) | required                    |
| `OPENAI_API_KEY`  | OpenAI API key                                     | required                    |
| `ALLOWED_ORIGINS` | CORS origins array                                 | `["http://localhost:3000"]` |
| `DB_ECHO`         | Log all SQL statements (`true`/`false`)            | `false`                     |

## License

MIT © Your Name

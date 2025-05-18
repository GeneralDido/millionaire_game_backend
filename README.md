# Millionaire Quiz API

A lightweight FastAPI backend for a quiz-style game inspired by “Who Wants to Be a Millionaire”. It generates
multiple‐choice questions (and a bonus question) using the OpenAI API, stores games and scores in PostgreSQL, and
exposes leaderboard data.

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Getting Started](#getting-started)
4. [Database Migrations](#database-migrations)
5. [Deployment to Render](#deployment-to-render)
6. [API Reference](#api-reference)
7. [Data Models & Schemas](#data-models--schemas)
8. [Testing](#testing)
9. [Configuration](#configuration)
10. [License](#license)

---

## Features

- Generate a new quiz with 15 questions + a bonus question via the OpenAI API
- Idempotent game creation: repeated calls return the same game for identical question sets
- **Admin-only** question generation (protected by API key)
- Submit scores by player name without full user authentication
- Global leaderboard showing the highest score per player
- Alembic migrations for schema management

---

## Tech Stack

- **FastAPI** (async)
- **SQLAlchemy 2.0** (async ORM)
- **Alembic** for schema migrations
- **Pydantic v2** for request/response validation
- **OpenAI** for question generation
- **PostgreSQL** (asyncpg) in production
- **SQLite** (aiosqlite) for local testing
- **pytest** + **pytest-asyncio** for tests

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- Poetry or pip

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
OPENAI_API_KEY = sk-…
ADMIN_API_KEY = your-admin-secret-key
ALLOWED_ORIGINS = ["http://localhost:3000"]
DB_ECHO = false
```

For tests, override in `.env.test`:

```ini
DATABASE_URL = sqlite+aiosqlite:///:memory:
OPENAI_API_KEY = sk-test-key
ADMIN_API_KEY = sk-test-admin-key
```

### Database Migrations

Alembic’s `alembic.ini` leaves `sqlalchemy.url=` blank; we override it in `alembic/env.py` (
switching `+asyncpg` → `+psycopg2`) so
both offline and online modes work.

```bash
alembic upgrade head
```

### Run Locally

```bash
uvicorn app.main:app --reload
```

Open your browser at `http://localhost:8000/docs` for the interactive OpenAPI docs.

## Deployment to Render

1. **Create** a new Web Service on Render, connect your repo.

2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**:
   ```bash
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. **Environment**:

    * `DATABASE_URL` → copy the **Internal Database URL** from Render Postgres
    * `OPENAI_API_KEY` → your key
    * (optional) `ALLOWED_ORIGINS` → e.g. `["http://localhost:3000","https://quiz-ui.vercel.app"]`
5. **Health Check Path**: `/health`

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
  "status": "ok",
  "version": "1.0.0"
}
```

### Generate Game (Admin only)

```http
POST /games/
X-Admin-Key: <ADMIN_API_KEY>
```

**Description**: Generates (or retrieves) a game.
Returns 15 questions + a bonus.

**Response** `200 OK`

```text
{
  "game_id": 1,
  "questions": [ /* Question[] */ ],
  "bonus_question": { /* Question */ }
}
```

### List Games

```http
GET /games/list
```

**Response** `200 OK`

```text
[
  { "game_id": 1, "created_at": "2025-05-18T12:34:56" },
  …
]
```

### Get Game

```http
GET /games/{game_id}
```

**Response** `200 OK` or `404 Not Found`

```text
/* same JSON schema as Generate Game */
```

### Random Game

```http
GET /games/random
```

**Response** `200 OK`

```text
/* one random GameRead */
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

### OpenAPI Spec

```bash
curl http://127.0.0.1:8000/openapi.json -o openapi.json
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

* **ScoreCreate** (Pydantic)

    * `player_name: str`
    * `score: int`

* **LeaderboardEntry** (Pydantic)

    * `player: str`
    * `best: int`

## Testing

Use the bundled `run_tests.sh`:

```bash
# loads .env.test automatically
./run_tests.sh
```

All tests pass against an in-memory SQLite database.

## Configuration

| Env Var           | Description                                        | Default                     |
|-------------------|----------------------------------------------------|-----------------------------|
| `DATABASE_URL`    | SQLAlchemy database URL (`postgresql+asyncpg://…`) | required                    |
| `OPENAI_API_KEY`  | OpenAI API key                                     | required                    |
| `ADMIN_API_KEY`   | Admin-only key for POST /games	                    | required                    |
| `ALLOWED_ORIGINS` | CORS origins array                                 | `["http://localhost:3000"]` |
| `DB_ECHO`         | Log all SQL statements (`true`/`false`)            | `false`                     |

## License

MIT © Dimitrios Panouris

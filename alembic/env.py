import sys
import os
from logging.config import fileConfig
from dotenv import load_dotenv

from sqlalchemy import pool, engine_from_config
from alembic import context

# Calculate paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

# Add project root to Python's path BEFORE any imports
sys.path.insert(0, project_root)

# Now we can safely import from app
from app.config import settings
from app.models import Base

# Load environment variables
load_dotenv(os.path.join(project_root, ".env"))

# Alembic Config and Logging
config = context.config
fileConfig(config.config_file_name)

# Override URL for migrations: switch asyncpg → psycopg2
sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
config.set_main_option("sqlalchemy.url", sync_url)

# Metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode (no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode using a sync psycopg2 engine."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # detect column type changes
            render_as_batch=True,  # for SQLite or other dialects if needed
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

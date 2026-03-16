import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, engine_from_config, pool

# Add the backend directory to the path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env from backend/ or project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from app.database import Base  # noqa: E402
from app.models import *  # noqa: E402, F401, F403

config = context.config

# Override sqlalchemy.url from environment variable
database_url = os.getenv("SYNC_DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = config.get_main_option("sqlalchemy.url")

    # Add SSL for Neon/cloud databases (engine_from_config doesn't support connect_args)
    connect_args = {}
    if url and ("neon.tech" in url or "sslmode=require" in url):
        connect_args["sslmode"] = "require"

    connectable = create_engine(url, poolclass=pool.NullPool, connect_args=connect_args)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

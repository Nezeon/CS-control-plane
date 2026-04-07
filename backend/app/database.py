import re
import ssl

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings


def _needs_ssl(url: str) -> bool:
    """Detect if the database URL requires SSL (Neon, other cloud providers)."""
    return "neon.tech" in url or "sslmode=require" in url


def _strip_sslmode(url: str) -> str:
    """Strip sslmode param from URL — asyncpg doesn't accept it as a query param."""
    url = re.sub(r"[?&]sslmode=[^&]*", "", url)
    # Fix leftover '&' becoming first param
    url = url.replace("?&", "?")
    return url


def _async_connect_args() -> dict:
    """Build connect_args for asyncpg. SSL must be passed as context, not URL param."""
    if _needs_ssl(settings.DATABASE_URL):
        return {"ssl": ssl.create_default_context()}
    return {}


def _sync_connect_args() -> dict:
    """Build connect_args for psycopg2."""
    if _needs_ssl(settings.SYNC_DATABASE_URL):
        return {"sslmode": "require"}
    return {}


# Async engine (for FastAPI endpoints)
# Strip sslmode from URL — asyncpg rejects it; SSL is passed via connect_args instead
_async_url = _strip_sslmode(settings.DATABASE_URL) if settings.DATABASE_URL else settings.DATABASE_URL
engine = create_async_engine(
    _async_url,
    echo=False,
    connect_args={**_async_connect_args(), "command_timeout": 30, "server_settings": {"statement_timeout": "30000"}},
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=120,  # Recycle every 2 min (Neon drops idle connections at ~5 min)
    pool_timeout=30,   # Wait up to 30s for a connection from pool
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine (for Celery tasks, agents, chat pipeline)
# NullPool = fresh connection every time, no reuse. Required for local dev from India
# because Neon's pooler silently drops idle connections from distant regions, causing
# psycopg2 to hang forever on stale TCP sockets. Each query pays ~1-2s SSL handshake
# but never hangs on a dead connection.
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    connect_args={
        **_sync_connect_args(),
        "connect_timeout": 15,
        "keepalives": 1,
        "keepalives_idle": 5,
        "keepalives_interval": 3,
        "keepalives_count": 3,
    },
    poolclass=NullPool,
)
SyncSessionLocal = sessionmaker(bind=sync_engine)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    return SyncSessionLocal()


def warm_sync_pool():
    """Pre-warm check — verify DB is reachable."""
    from sqlalchemy import text
    with sync_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        conn.commit()

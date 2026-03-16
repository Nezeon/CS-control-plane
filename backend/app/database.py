import re
import ssl

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

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
    connect_args=_async_connect_args(),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=180,  # Recycle before Neon idles (~5 min)
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine (for Celery tasks, agents, seed script)
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    connect_args=_sync_connect_args(),
    pool_size=3,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=180,  # Recycle connections every 3 min (Neon idles at 5 min)
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
    """Pre-warm the sync connection pool so the first real query doesn't pay SSL cold-start."""
    from sqlalchemy import text
    with sync_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        conn.commit()

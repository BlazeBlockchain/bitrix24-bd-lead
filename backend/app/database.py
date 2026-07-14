from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings

# Create async SQLAlchemy engine (asyncpg driver)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory for dependency injection
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async DB session (standard FastAPI + SQLAlchemy async pattern)."""
    async with AsyncSessionLocal() as session:
        yield session
    # Note: explicit commit/rollback should be done by callers/services for control.


async def init_db():
    """Initialize database tables (for dev; use Alembic in prod via entrypoint).

    T009: imports all models (User, CrmConnection, Lead, UserMemoryProfile,
    OutreachHistory, UsageLedger) so metadata includes full data-model schema.
    """
    # Import models so metadata is populated (T009 full)
    from app.models import (  # noqa: F401
        user,
        crm_connection,
        lead,
        user_memory_profile,
        outreach_history,
        usage_ledger,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection pool."""
    await engine.dispose()


# Re-export Base for alembic and models (mirrors vanguard pattern)
# Actual Base defined in models/base.py for model imports
from app.models.base import Base  # type: ignore

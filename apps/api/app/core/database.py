"""
Database connection and session management.
Uses SQLAlchemy async engine with proper session lifecycle.
PATCH 14: True async-scoped sessions for concurrency safety.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import AsyncGenerator
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine with proper configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to False in production
    future=True,
    pool_pre_ping=True,
    # PATCH 14: Optimized for SQLite concurrency
    pool_size=5 if "sqlite" in settings.DATABASE_URL else 10,
    max_overflow=10 if "sqlite" in settings.DATABASE_URL else 20,
    pool_timeout=30,
    pool_recycle=3600,
)

# PATCH 14: Session factory with proper async configuration
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,  # Critical: prevent automatic flushes
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    PATCH 14: Proper async session dependency with context management.
    Ensures one session per request with automatic cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # Only rollback if session is still active
            if session.in_transaction():
                await session.rollback()
            raise
        finally:
            # Session is automatically closed by context manager
            pass


async def init_db():
    """Initialize database tables. Creates all tables from models."""
    try:
        logger.info("Initializing database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

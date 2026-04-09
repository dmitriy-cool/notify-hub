import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/notifyhub_db"
)

# Асинхронный engine для FastAPI
async_engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Синхронный engine для Celery (преобразуем asyncpg -> psycopg2)
sync_database_url = DATABASE_URL.replace("asyncpg", "psycopg2")
sync_engine = create_engine(
    sync_database_url,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)


async def get_db():
    """Dependency для получения асинхронной сессии БД в FastAPI"""
    async with AsyncSessionLocal() as db:
        yield db


def get_sync_db():
    """Получить синхронную сессию для Celery"""
    db = SyncSessionLocal()
    try:
        return db
    finally:
        db.close()

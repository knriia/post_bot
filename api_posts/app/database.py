from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    pass


async_engine = create_async_engine(
    settings.postgres_url,
    pool_size=20,
    max_overflow=10,
)

async_session_local = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_postgres_session():
    async with async_session_local() as session:
        yield session


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_redis_session():
    async with Redis.from_url(settings.redis_url, decode_responses=True) as radis:
        yield radis

from __future__ import annotations

import os
from pathlib import Path

import dotenv
from models import Base
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")
DEFAULT_DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRE_URL")
)


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Configure basic-rag/.env or export DATABASE_URL.")
    return database_url


def get_engine(database_url: str | None = None, echo: bool = False) -> AsyncEngine:
    return create_async_engine(database_url or get_database_url(), echo=echo)


async def create_extensions(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        available = await conn.execute(
            text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
        )
        if available.scalar_one_or_none() is None:
            raise RuntimeError(
                "PostgreSQL server does not have pgvector installed. "
                "This schema requires extension 'vector' for the embedding column. "
                "Install pgvector on the PostgreSQL server, then run CREATE EXTENSION vector."
            )

        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except DBAPIError as exc:
            raise RuntimeError(
                "Failed to enable PostgreSQL extension 'vector'. "
                "Ensure pgvector is installed on the server and the current user can run CREATE EXTENSION."
            ) from exc


async def create_schema(engine: AsyncEngine) -> None:
    await create_extensions(engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

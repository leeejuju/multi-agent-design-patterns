from __future__ import annotations

import argparse
import asyncio

from db import create_schema, drop_schema, get_database_url, get_engine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize PostgreSQL tables for RAG benchmarking.")
    parser.add_argument("--database-url", default=get_database_url(), help="SQLAlchemy database URL.")
    parser.add_argument("--drop-first", action="store_true", help="Drop existing tables before creating them.")
    parser.add_argument("--echo", action="store_true", help="Enable SQLAlchemy SQL echo.")
    return parser.parse_args()


async def amain() -> None:
    args = parse_args()
    engine = get_engine(args.database_url, echo=args.echo)

    if args.drop_first:
        await drop_schema(engine)

    await create_schema(engine)
    await engine.dispose()
    print("Schema ready:", args.database_url)


if __name__ == "__main__":
    asyncio.run(amain())

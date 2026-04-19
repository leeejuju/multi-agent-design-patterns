from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, func
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.asyncio import create_async_engine

basic_rag_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(basic_rag_dir))
sys.path.insert(0, str(basic_rag_dir / "embeding"))
from embeding import create_client  # noqa: E402

load_dotenv()

metadata = MetaData(schema="public")

rag_chunk = Table(
    "rag_chunk",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("doc_id", String(64), nullable=False),
    Column("chunk_no", Integer, nullable=False),
    Column("content", String(65535), nullable=False),
    Column("embedding", Vector(1024), nullable=False),
    Column("token_count", Integer, nullable=False),
    Column("char_count", Integer, nullable=False),
    Column("source", String(128), nullable=False),
    Column("label", String(64), nullable=False),
    Column("metadata", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


@dataclass
class RagChunk:
    doc_id: str
    chunk_no: int
    content: str
    embedding: list[float]
    source: str
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)
    token_count: int | None = None
    char_count: int | None = None

    def to_row(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "chunk_no": self.chunk_no,
            "content": self.content,
            "embedding": self.embedding,
            "token_count": self.token_count,
            "char_count": self.char_count,
            "source": self.source,
            "label": self.label,
            "metadata": self.metadata,
        }


async def load_chunks(
    json_path: str,
    *,
    embedding_provider: str = "dashscope",
    embedding_model: str | None = None,
    dimensions: int = 1024,
    batch_size: int = 16,
    max_concurrency: int = 4,
) -> list[RagChunk]:
    with open(json_path, encoding="utf-8") as file:
        items = json.load(file)

    client = create_client(embedding_provider, model=embedding_model, dimensions=dimensions)
    embeddings = await client.batch_encode(
        [item["content"] for item in items],
        batch_size=batch_size,
        max_concurrency=max_concurrency,
        is_query=False,
    )
    chunks: list[RagChunk] = []
    for chunk_no, (item, embedding) in enumerate(zip(items, embeddings, strict=True)):
        item["metadata"]["page"] = item["page"]
        chunks.append(
            RagChunk(
                doc_id=item["doc_id"],
                chunk_no=chunk_no,
                content=item["content"],
                embedding=embedding,
                token_count=item["token_count"],
                char_count=item["char_count"],
                source=item["source"],
                label=item["label"],
                metadata=item["metadata"],
            )
        )
    return chunks


async def write_chunks(database_url: str, chunks: list[RagChunk]) -> None:
    rows = [chunk.to_row() for chunk in chunks]
    statement = insert(rag_chunk).values(rows)
    statement = statement.on_conflict_do_update(
        index_elements=["doc_id", "chunk_no", "label"],
        set_={
            "content": statement.excluded.content,
            "embedding": statement.excluded.embedding,
            "token_count": statement.excluded.token_count,
            "char_count": statement.excluded.char_count,
            "source": statement.excluded.source,
            "metadata": statement.excluded.metadata,
        },
    )

    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.execute(statement)
    await engine.dispose()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--database-url", default=os.getenv("POSTGRE_URL"))
    parser.add_argument("--embedding-provider", default="dashscope")
    parser.add_argument("--embedding-model", default="text-embedding-v3")
    parser.add_argument("--dimensions", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-concurrency", type=int, default=2)
    args = parser.parse_args()

    for i in os.listdir(args.json):
        json_path = os.path.join(args.json, i)
        chunks = await load_chunks(
            json_path,
            embedding_provider=args.embedding_provider,
            embedding_model=args.embedding_model,
            dimensions=args.dimensions,
            batch_size=args.batch_size,
            max_concurrency=args.max_concurrency,
        )
    await write_chunks(args.database_url, chunks)
    print(f"wrote {len(chunks)} chunks")


if __name__ == "__main__":
    asyncio.run(main())

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
from pymilvus import DataType, MilvusClient

basic_rag_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(basic_rag_dir))
sys.path.insert(0, str(basic_rag_dir / "embeding"))
from embeding import create_client  # noqa: E402

load_dotenv()

REQUIRED_CHUNK_FIELDS = {
    "doc_id",
    "content",
    "page",
    "token_count",
    "char_count",
    "source",
    "label",
}


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
            "id": f"{self.doc_id}:{self.chunk_no}:{self.label}",
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
    json_path: str | Path,
    *,
    embedding_provider: str = "dashscope",
    embedding_model: str | None = None,
    dimensions: int = 1024,
    batch_size: int = 16,
    max_concurrency: int = 4,
) -> list[RagChunk]:
    json_path = Path(json_path)
    with json_path.open(encoding="utf-8") as file:
        items = json.load(file)
    if not isinstance(items, list):
        raise ValueError(f"{json_path} 必须包含一个 JSON 列表。")
    if not items:
        return []
    for index, item in enumerate(items):
        validate_chunk_item(item, json_path, index)

    client = create_client(embedding_provider, model=embedding_model, dimensions=dimensions)
    embeddings = await client.batch_encode(
        [item["content"] for item in items],
        batch_size=batch_size,
        max_concurrency=max_concurrency,
        is_query=False,
    )
    chunks: list[RagChunk] = []
    for chunk_no, (item, embedding) in enumerate(zip(items, embeddings, strict=True)):
        metadata = dict(item.get("metadata") or {})
        metadata["page"] = item["page"]
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
                metadata=metadata,
            )
        )
    return chunks


def validate_chunk_item(item: Any, json_path: Path, index: int) -> None:
    if not isinstance(item, dict):
        raise ValueError(f"{json_path} 中的第 {index} 个条目必须是一个对象。")

    missing_fields = REQUIRED_CHUNK_FIELDS - item.keys()
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"{json_path} 中的第 {index} 个条目缺少字段: {missing}。")

    if not isinstance(item["content"], str) or not item["content"].strip():
        raise ValueError(f"{json_path} 中的第 {index} 个条目的内容（content）为空。")


def collect_json_paths(input_path: str | Path) -> list[Path]:
    path = Path(input_path).expanduser()

    if not path.is_dir():
        raise FileNotFoundError(f"JSON 输入路径不存在: {path}")

    json_paths = sorted(
        child for child in path.iterdir() if child.is_file() and child.suffix.lower() == ".json"
    )
    if not json_paths:
        raise FileNotFoundError(f"路径 {path} 没文件")
    return json_paths


def ensure_collection(client: MilvusClient, collection_name: str, dimensions: int) -> None:
    if client.has_collection(collection_name):
        return

    schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=256)
    schema.add_field("doc_id", DataType.VARCHAR, max_length=64)
    schema.add_field("chunk_no", DataType.INT64)
    schema.add_field("content", DataType.VARCHAR, max_length=65535)
    schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=dimensions)
    schema.add_field("token_count", DataType.INT64)
    schema.add_field("char_count", DataType.INT64)
    schema.add_field("source", DataType.VARCHAR, max_length=512)
    schema.add_field("label", DataType.VARCHAR, max_length=128)
    schema.add_field("metadata", DataType.JSON)

    index_params = MilvusClient.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="AUTOINDEX",
        metric_type="COSINE",
    )

    client.create_collection(
        collection_name=collection_name,
        schema=schema,
        index_params=index_params,
    )


def write_chunks(
    milvus_uri: str,
    collection_name: str,
    chunks: list[RagChunk],
    *,
    token: str = "",
    dimensions: int = 1024,
) -> None:
    client = MilvusClient(uri=milvus_uri, token=token)
    ensure_collection(client, collection_name, dimensions)
    client.upsert(collection_name=collection_name, data=[chunk.to_row() for chunk in chunks])
    client.close()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="包含分块数据的 JSON 文件或目录路径")
    parser.add_argument(
        "--milvus-uri",
        default=os.getenv("MILVUS_URI", "http://localhost:19530"),
        help="Milvus 服务地址",
    )
    parser.add_argument(
        "--milvus-token", default=os.getenv("MILVUS_TOKEN", ""), help="Milvus 认证 Token（可选）"
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("MILVUS_COLLECTION", "rag_chunk"),
        help="Milvus 集合（Collection）名称",
    )
    parser.add_argument(
        "--embedding-provider", default="dashscope", help="Embedding 提供商 (如 dashscope)"
    )
    parser.add_argument("--embedding-model", default="text-embedding-v3", help="Embedding 模型名称")
    parser.add_argument("--dimensions", type=int, default=1024, help="Embedding 维度")
    parser.add_argument("--batch-size", type=int, default=4, help="Embedding 批处理大小")
    parser.add_argument("--max-concurrency", type=int, default=2, help="Embedding 最大并发请求数")
    args = parser.parse_args()

    all_chunks: list[RagChunk] = []
    for json_path in collect_json_paths(args.json):
        all_chunks.extend(
            await load_chunks(
                json_path,
                embedding_provider=args.embedding_provider,
                embedding_model=args.embedding_model,
                dimensions=args.dimensions,
                batch_size=args.batch_size,
                max_concurrency=args.max_concurrency,
            )
        )
    if not all_chunks:
        raise ValueError(f"未从 {args.json} 加载到任何分块数据。")

    write_chunks(
        args.milvus_uri,
        args.collection,
        all_chunks,
        token=args.milvus_token,
        dimensions=args.dimensions,
    )
    print(f"成功将 {len(all_chunks)} 条分块写入到集合 {args.collection}")


if __name__ == "__main__":
    asyncio.run(main())

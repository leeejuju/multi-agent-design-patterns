import argparse
from pathlib import Path

try:
    from .chunker import DATA_DIR, JSONChunker
    from .ingestion import (
        BM25_INDEX_DIR,
        EMBEDDING_DIM,
        EMBEDDING_MODEL,
        EMBEDDING_PROVIDER,
        MILVUS_COLLECTION,
        MILVUS_URI,
        BM25Ingestor,
        MilvusIngestor,
    )
except ImportError:
    from chunker import DATA_DIR, JSONChunker
    from ingestion import (
        BM25_INDEX_DIR,
        EMBEDDING_DIM,
        EMBEDDING_MODEL,
        EMBEDDING_PROVIDER,
        MILVUS_COLLECTION,
        MILVUS_URI,
        BM25Ingestor,
        MilvusIngestor,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="对提取的 JSON 页面进行分块并入库。")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--bm25-index-dir", type=Path, default=BM25_INDEX_DIR)
    parser.add_argument("--queries", nargs="*", default=["risk factor"])
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--milvus-uri", default=MILVUS_URI)
    parser.add_argument("--milvus-collection", default=MILVUS_COLLECTION)
    parser.add_argument(
        "--embedding-provider",
        choices=["dashscope", "ollama"],
        default=EMBEDDING_PROVIDER,
    )
    parser.add_argument("--embedding-model", default=EMBEDDING_MODEL)
    parser.add_argument("--embedding-dim", type=int, default=EMBEDDING_DIM)
    parser.add_argument("--drop-collection", action="store_true", default=True)
    parser.add_argument("--no-drop", dest="drop_collection", action="store_false")
    parser.add_argument("--no-bm25", action="store_true")
    parser.add_argument("--no-milvus", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    chunks = JSONChunker(json_paths=args.data_dir).chunk_all()
    doc_count = len({chunk.metadata["doc_id"] for chunk in chunks})
    print(f"已加载 {doc_count} 个文档，共 {len(chunks)} 个 chunk。")

    if not args.no_bm25:
        bm25 = BM25Ingestor(args.bm25_index_dir)
        count = bm25.ingest(chunks)
        print(f"BM25 已索引 {count} 个 chunk，路径: {args.bm25_index_dir}。")
        
    if not args.no_milvus:
        milvus = MilvusIngestor(
            uri=args.milvus_uri,
            collection_name=args.milvus_collection,
            embedding_provider=args.embedding_provider,
            embedding_model=args.embedding_model,
            embedding_dim=args.embedding_dim,
        )
        count = milvus.ingest(chunks, drop_existing=args.drop_collection)
        print(f"\nMilvus 已写入 {count} 个 chunk 到集合 '{milvus.collection_name}'。")
        print(f"Milvus 集合内记录数: {milvus.count()}")


if __name__ == "__main__":
    main()

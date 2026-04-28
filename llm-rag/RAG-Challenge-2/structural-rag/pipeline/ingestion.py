import json
import math
import os
import re
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from pymilvus import (
    Collection,
    DataType,
    MilvusClient,
    connections,
    utility,
)

from chunker import JSONChunker
from model import Chunk

load_dotenv()

# ==========================================================================
# Configuration
# ==========================================================================

MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "rag_chunk")
EMBEDDING_MODEL = "text-embedding-v3"
EMBEDDING_DIM = 1024
BATCH_SIZE = 32
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
BM25_INDEX_DIR = Path(__file__).resolve().parent / "bm25_index"

# BM25
TOKEN_PATTERN = re.compile(r"\w+")
K1 = 1.5
B = 0.75

# Milvus
_SCHEMA_FIELDS = [
    {
        "name": "chunk_id",
        "dtype": DataType.VARCHAR,
        "is_primary": True,
        "max_length": 64,
    },
    {"name": "text", "dtype": DataType.VARCHAR, "max_length": 65535},
    {"name": "doc_id", "dtype": DataType.VARCHAR, "max_length": 256},
    {"name": "page_index", "dtype": DataType.INT64},
    {"name": "chunk_type", "dtype": DataType.VARCHAR, "max_length": 32},
    {"name": "title", "dtype": DataType.VARCHAR, "max_length": 512},
]
INDEX_PARAMS = {"metric_type": "COSINE", "index_type": "AUTOINDEX", "params": {}}


# ==========================================================================
# BM25 Ingestor
# ==========================================================================


class BM25Ingestor:
    def __init__(self, index_dir: str | Path):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self._corpus: dict[str, dict] = {}
        self._doc_lengths: dict[str, int] = {}
        self._inverted: dict[str, dict[str, int]] = {}
        self._avgdl: float = 0.0

    # -- ingest ------------------------------------------------------------

    def ingest(self, chunks: list[Chunk]) -> int:
        self._reset()
        for chunk in chunks:
            self._index_one(chunk)
        self._finalise()
        self._save()
        return len(self._corpus)

    # -- search ------------------------------------------------------------

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        self._load()
        query_terms = self._tokenize(query)
        if not query_terms or not self._corpus:
            return []

        scored = defaultdict(float)
        for term in query_terms:
            postings = self._inverted.get(term, {})
            idf = self._idf(term)
            for chunk_id, tf in postings.items():
                dl = self._doc_lengths.get(chunk_id, 1)
                numerator = tf * (K1 + 1)
                denominator = tf + K1 * (1 - B + B * dl / self._avgdl)
                scored[chunk_id] += idf * numerator / denominator

        ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            {
                "chunk_id": cid,
                "text": self._corpus[cid]["text"],
                "metadata": self._corpus[cid]["metadata"],
                "score": round(score, 4),
            }
            for cid, score in ranked
        ]

    # -- internals ---------------------------------------------------------

    def _reset(self) -> None:
        self._corpus.clear()
        self._doc_lengths.clear()
        self._inverted.clear()
        self._avgdl = 0.0

    def _index_one(self, chunk: Chunk) -> None:
        cid = chunk.metadata["chunk_id"]
        tokens = self._tokenize(chunk.text)
        self._corpus[cid] = {"text": chunk.text, "metadata": chunk.metadata}
        self._doc_lengths[cid] = len(tokens)
        term_freqs: dict[str, int] = {}
        for token in tokens:
            term_freqs[token] = term_freqs.get(token, 0) + 1
        for term, tf in term_freqs.items():
            self._inverted.setdefault(term, {})[cid] = tf

    def _finalise(self) -> None:
        if not self._doc_lengths:
            self._avgdl = 1.0
        else:
            self._avgdl = sum(self._doc_lengths.values()) / len(self._doc_lengths)

    def _idf(self, term: str) -> float:
        n = len(self._inverted.get(term, {}))
        N = len(self._corpus)
        return math.log((N - n + 0.5) / (n + 0.5) + 1)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [t.lower() for t in TOKEN_PATTERN.findall(text)]

    # -- persistence -------------------------------------------------------

    def _save(self) -> None:
        self._write_json("corpus.json", self._corpus)
        self._write_json("terms.json", self._inverted)
        self._write_json(
            "stats.json",
            {
                "N": len(self._corpus),
                "avgdl": self._avgdl,
                "doc_lengths": self._doc_lengths,
            },
        )

    def _load(self) -> None:
        if self._corpus:
            return
        self._corpus = self._read_json("corpus.json")
        self._inverted = self._read_json("terms.json")
        stats = self._read_json("stats.json")
        self._doc_lengths = stats.get("doc_lengths", {})
        self._avgdl = stats.get("avgdl", 1.0)

    def _write_json(self, filename: str, data: object) -> None:
        (self.index_dir / filename).write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

    def _read_json(self, filename: str) -> dict:
        path = self.index_dir / filename
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


# ==========================================================================
# Milvus Ingestor
# ==========================================================================


class MilvusIngestor:
    def __init__(
        self,
        uri: str = MILVUS_URI,
        collection_name: str = MILVUS_COLLECTION,
        embedding_model: str = EMBEDDING_MODEL,
        embedding_dim: int = EMBEDDING_DIM,
        batch_size: int = BATCH_SIZE,
    ):
        self.uri = uri
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.batch_size = batch_size
        self._embeddings = OpenAIEmbeddings(
            model=embedding_model,
            dimensions=embedding_dim,
            base_url=DASHSCOPE_BASE_URL,
            api_key=DASHSCOPE_API_KEY,
        )

    # -- ingest ------------------------------------------------------------

    def ingest(self, chunks: list[Chunk], drop_existing: bool = True) -> int:
        self._connect()
        self._ensure_collection(drop_existing)
        collection = Collection(self.collection_name)
        total = 0
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i : i + self.batch_size]
            texts = [c.text for c in batch]
            vectors = self._embed(texts)
            collection.insert(self._build_rows(batch, vectors))
            total += len(batch)
        collection.flush()
        collection.load()
        return total

    def count(self) -> int:
        self._connect()
        if not utility.has_collection(self.collection_name):
            return 0
        self._ensure_loaded()
        return Collection(self.collection_name).num_entities

    # -- connection --------------------------------------------------------

    def _connect(self) -> None:
        alias = "default"
        if connections.has_connection(alias):
            existing = connections.get_connection_addr(alias)
            if existing.get("uri") == self.uri:
                return
            connections.disconnect(alias)
        connections.connect(alias=alias, uri=self.uri)

    # -- collection -------------------------------------------------------

    def _ensure_collection(self, drop: bool) -> None:
        if drop and utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
        if utility.has_collection(self.collection_name):
            return
        schema = MilvusClient.create_schema(auto_id=False)
        for field in _SCHEMA_FIELDS:
            kwargs = {**field}
            dtype = kwargs.pop("dtype")
            schema.add_field(dtype=dtype, **kwargs)
        schema.add_field(
            dtype=DataType.FLOAT_VECTOR, name="embedding", dim=self.embedding_dim
        )
        schema.verify()
        Collection(self.collection_name, schema=schema)
        Collection(self.collection_name).create_index("embedding", INDEX_PARAMS)

    def _ensure_loaded(self) -> None:
        try:
            Collection(self.collection_name).load()
        except Exception:
            pass

    # -- embedding ---------------------------------------------------------

    def _embed(self, texts: list[str]) -> list[list[float]]:
        for attempt in range(3):
            try:
                return self._embeddings.embed_documents(texts)
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2**attempt)
        return []

    # -- rows --------------------------------------------------------------

    @staticmethod
    def _build_rows(chunks: list[Chunk], vectors: list[list[float]]) -> list[dict]:
        rows: list[dict] = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            meta = chunk.metadata
            rows.append(
                {
                    "chunk_id": meta.get("chunk_id", ""),
                    "text": chunk.text,
                    "doc_id": meta.get("doc_id", ""),
                    "page_index": meta.get("page_index") or 0,
                    "chunk_type": meta.get("chunk_type", "text"),
                    "title": meta.get("title") or "",
                    "embedding": vector,
                }
            )
        return rows


# ==========================================================================
# Orchestrator
# ==========================================================================


def main():
    print("=== Chunking JSON pages ===")
    chunker = JSONChunker(data_dir=DATA_DIR)
    chunks = chunker.chunk_all()
    doc_count = len({c.metadata["doc_id"] for c in chunks})
    print(f"  Produced {len(chunks)} chunks from {doc_count} documents")

    print("\n=== BM25 Ingestion ===")
    bm25 = BM25Ingestor(BM25_INDEX_DIR)
    n = bm25.ingest(chunks)
    print(f"  Indexed {n} chunks to {BM25_INDEX_DIR}")

    print("\n=== BM25 Smoke Test ===")
    for result in bm25.search("risk factor")[:3]:
        meta = result["metadata"]
        doc_id = meta.get("doc_id", "?")
        page = meta.get("page_index", "?")
        print(f"  [{doc_id}:p{page}] score={result['score']}  {result['text'][:120]}")

    print("\n=== Milvus Ingestion ===")
    milvus = MilvusIngestor()
    n = milvus.ingest(chunks, drop_existing=True)
    print(f"  Inserted {n} rows into '{milvus.collection_name}'")
    print(f"  Collection count: {milvus.count()}")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()

import math
import os
import pickle
import re
import time
from collections import defaultdict
from pathlib import Path

import httpx
from dotenv import load_dotenv
from pymilvus import Collection, DataType, MilvusClient, connections, utility
from pymilvus.exceptions import MilvusException

try:
    from .model import Chunk
except ImportError:
    from model import Chunk

load_dotenv(Path(__file__).with_name(".env"))


MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "rag_chunk_struct_rag")
MILVUS_TIMEOUT = float(os.getenv("MILVUS_TIMEOUT", "10"))
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "dashscope").lower()
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "bge-m3" if EMBEDDING_PROVIDER == "ollama" else "text-embedding-v3",
)
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))
BATCH_SIZE = 4
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_EMBEDDINGS_URL = f"{DASHSCOPE_BASE_URL}/embeddings"
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBEDDINGS_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/api/embed"

BM25_INDEX_DIR = Path(__file__).resolve().parent / "bm25_index"

STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "at",
    "for",
    "by",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "what",
    "which",
    "who",
    "when",
    "where",
    "how",
    "according",
    "annual",
    "report",
    "period",
    "last",
    "end",
    "data",
    "available",
    "return",
}

# BM25 分词规则：匹配小写字母数字词，支持连字符和撇号连接的复合词
TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)*")
K1 = 1.5  # BM25 词频饱和系数
B = 0.75  # BM25 长度归一化系数

SCHEMA_FIELDS = [
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
    {"name": "company_name", "dtype": DataType.VARCHAR, "max_length": 512},
]
INDEX_PARAMS = {"metric_type": "COSINE", "index_type": "AUTOINDEX", "params": {}}


class BM25Ingestor:
    def __init__(self, index_dir: str | Path):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self._corpus: dict[str, dict] = {}
        self._doc_lengths: dict[str, int] = {}
        self._inverted: dict[str, dict[str, int]] = {}
        self._avgdl = 1.0

    def ingest(self, chunks: list[Chunk]) -> int:
        self._reset()
        for chunk in chunks:
            self._index_one(chunk)
        self._finalize()
        self._save()
        return len(self._corpus)

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        self._load()
        terms = {term for term in self._tokenize(query) if term not in STOPWORDS}
        if not terms or not self._corpus:
            return []

        scores: defaultdict[str, float] = defaultdict(float)
        for term in terms:
            postings = self._inverted.get(term, {})
            idf = self._idf(term)
            for chunk_id, tf in postings.items():
                scores[chunk_id] += idf * self._term_score(tf, self._doc_lengths[chunk_id])

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
        return [
            {
                "chunk_id": chunk_id,
                "text": self._corpus[chunk_id]["text"],
                "metadata": self._corpus[chunk_id]["metadata"],
                "score": round(score, 4),
            }
            for chunk_id, score in ranked
        ]

    def _reset(self) -> None:
        self._corpus.clear()
        self._doc_lengths.clear()
        self._inverted.clear()
        self._avgdl = 1.0

    @staticmethod
    def _build_search_text(chunk: Chunk) -> str:
        metadata = chunk.metadata
        return "\n".join(
            [
                metadata.get("company_name") or "",
                metadata.get("title") or "",
                metadata.get("doc_id") or "",
                chunk.text,
            ]
        )

    def _index_one(self, chunk: Chunk) -> None:
        chunk_id = chunk.metadata["chunk_id"]
        search_text = self._build_search_text(chunk)
        tokens = self._tokenize(search_text)
        self._corpus[chunk_id] = {"text": chunk.text, "metadata": chunk.metadata}
        self._doc_lengths[chunk_id] = len(tokens)

        # 统计当前 chunk 的词频，构建倒排索引：term -> {chunk_id -> term_frequency}
        term_freqs: dict[str, int] = {}
        for token in tokens:
            term_freqs[token] = term_freqs.get(token, 0) + 1

        for term, tf in term_freqs.items():
            self._inverted.setdefault(term, {})[chunk_id] = tf

    def _finalize(self) -> None:
        # 计算语料库平均文档长度，BM25 长度归一化需要
        if not self._doc_lengths:
            self._avgdl = 1.0
            return

        avgdl = sum(self._doc_lengths.values()) / len(self._doc_lengths)
        self._avgdl = max(avgdl, 1.0)

    def _idf(self, term: str) -> float:
        # BM25 逆文档频率：包含该词的文档越少，IDF 越高
        doc_count = len(self._corpus)
        hit_count = len(self._inverted.get(term, {}))
        return math.log((doc_count - hit_count + 0.5) / (hit_count + 0.5) + 1)

    def _term_score(self, tf: int, doc_length: int) -> float:
        # BM25 词频得分：对高频词做饱和处理，防止长文档天然高分
        numerator = tf * (K1 + 1)
        denominator = tf + K1 * (1 - B + B * doc_length / self._avgdl)
        return numerator / denominator

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return TOKEN_PATTERN.findall(text.lower())

    def _save(self) -> None:
        path = self.index_dir / "bm25_index.pkl"
        with open(path, "wb") as fh:
            pickle.dump(
                {
                    "corpus": self._corpus,
                    "inverted": self._inverted,
                    "avgdl": self._avgdl,
                    "doc_lengths": self._doc_lengths,
                },
                fh,
            )

    def _load(self) -> None:
        if self._corpus:
            return

        path = self.index_dir / "bm25_index.pkl"
        if not path.exists():
            return

        with open(path, "rb") as fh:
            data = pickle.load(fh)
        self._corpus = data["corpus"]
        self._inverted = data["inverted"]
        self._avgdl = data["avgdl"]
        self._doc_lengths = data["doc_lengths"]


class MilvusIngestor:
    def __init__(
        self,
        uri: str = MILVUS_URI,
        collection_name: str = MILVUS_COLLECTION,
        embedding_provider: str = EMBEDDING_PROVIDER,
        embedding_model: str = EMBEDDING_MODEL,
        embedding_dim: int = EMBEDDING_DIM,
        batch_size: int = BATCH_SIZE,
        timeout: float = MILVUS_TIMEOUT,
    ):
        self.uri = uri
        self.collection_name = collection_name
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        self.batch_size = batch_size
        self.timeout = timeout

    def ingest(self, chunks: list[Chunk], drop_existing: bool = True) -> int:
        self._connect()
        self._ensure_collection(drop_existing)

        collection = Collection(self.collection_name)
        total = 0
        for index in range(0, len(chunks), self.batch_size):
            batch = chunks[index : index + self.batch_size]
            vectors = self._embed([chunk.text for chunk in batch])
            collection.insert(self._build_rows(batch, vectors))
            total += len(batch)

        collection.flush()
        return total

    def count(self) -> int:
        self._connect()
        if not utility.has_collection(self.collection_name, timeout=self.timeout):
            return 0
        return Collection(self.collection_name).num_entities

    def _connect(self) -> None:
        # 复用已有连接，避免重复创建；uri 变更时断开重建
        alias = "default"
        if connections.has_connection(alias):
            existing = connections.get_connection_addr(alias)
            if existing.get("uri") == self.uri:
                return
            connections.disconnect(alias)
        try:
            connections.connect(alias=alias, uri=self.uri, timeout=self.timeout)
            utility.get_server_version(timeout=self.timeout)
        except MilvusException as exc:
            # 连接失败时给出明确提示，而不是抛出底层 MilvusException
            raise ConnectionError(
                f"无法连接到 Milvus {self.uri}，请检查 MILVUS_URI、网络及端口 19530 是否开放"
            ) from exc

    def _ensure_collection(self, drop_existing: bool) -> None:
        if drop_existing and utility.has_collection(self.collection_name, timeout=self.timeout):
            utility.drop_collection(self.collection_name)
        if utility.has_collection(self.collection_name, timeout=self.timeout):
            return

        schema = MilvusClient.create_schema(auto_id=False)
        for field in SCHEMA_FIELDS:
            options = field.copy()
            field_name = options.pop("name")
            dtype = options.pop("dtype")
            schema.add_field(field_name=field_name, datatype=dtype, **options)
        schema.add_field(
            field_name="embedding",
            datatype=DataType.FLOAT_VECTOR,
            dim=self.embedding_dim,
        )
        schema.verify()

        collection = Collection(self.collection_name, schema=schema)
        collection.create_index("embedding", INDEX_PARAMS)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if self.embedding_provider == "ollama":
            return self._embed_with_ollama(texts)
        if self.embedding_provider == "dashscope":
            return self._embed_with_dashscope(texts)
        raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")

    def _embed_with_dashscope(self, texts: list[str]) -> list[list[float]]:
        # 指数退避重试（最多 3 次），应对临时网络波动和限流
        for attempt in range(3):
            try:
                response = httpx.post(
                    DASHSCOPE_EMBEDDINGS_URL,
                    json={
                        "model": self.embedding_model,
                        "input": texts,
                        "dimensions": self.embedding_dim,
                        "encoding_format": "float",
                    },
                    headers={
                        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    timeout=120,
                )
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    raise RuntimeError(f"错了: {response.status_code} {response.text}") from exc
                body = response.json()
                vectors = [item["embedding"] for item in body["data"]]
                self._validate_vectors(vectors)
                return vectors
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2**attempt)
        return []

    def _embed_with_ollama(self, texts: list[str]) -> list[list[float]]:
        for attempt in range(3):
            try:
                response = httpx.post(
                    OLLAMA_EMBEDDINGS_URL,
                    json={
                        "model": self.embedding_model,
                        "input": texts,
                    },
                    timeout=120,
                )
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    raise RuntimeError(
                        f"Ollama embedding request failed: {response.status_code} {response.text}"
                    ) from exc
                vectors = response.json()["embeddings"]
                self._validate_vectors(vectors)
                return vectors
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2**attempt)
        return []

    def _validate_vectors(self, vectors: list[list[float]]) -> None:
        # 校验向量维度与集合定义一致，否则插入 Milvus 会静默失败
        bad_dims = {len(vector) for vector in vectors if len(vector) != self.embedding_dim}
        if bad_dims:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.embedding_dim}, got "
                f"{sorted(bad_dims)} from {self.embedding_provider}/{self.embedding_model}. "
                "Set EMBEDDING_DIM to match the model before creating the Milvus collection."
            )

    @staticmethod
    def _build_rows(chunks: list[Chunk], vectors: list[list[float]]) -> list[dict]:
        rows = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            metadata = chunk.metadata
            rows.append(
                {
                    "chunk_id": metadata.get("chunk_id", ""),
                    "text": chunk.text,
                    "doc_id": metadata.get("doc_id", ""),
                    "page_index": metadata.get("page_index") or 0,
                    "chunk_type": metadata.get("chunk_type", "text"),
                    "title": metadata.get("title") or "",
                    "company_name": metadata.get("company_name") or "",
                    "embedding": vector,
                }
            )
        return rows

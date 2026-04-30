"""混合检索 + LLM 问答的 QuestionProcessor 模块。"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pymilvus import MilvusClient

load_dotenv(Path(__file__).with_name(".env"))

try:
    from .ingestion import BM25_INDEX_DIR, MILVUS_COLLECTION, MILVUS_URI, BM25Ingestor
    from .llm.providers import PROVIDERS as LLM_PROVIDERS
    from .prompt import build_prompt
except ImportError:
    from ingestion import BM25_INDEX_DIR, MILVUS_COLLECTION, MILVUS_URI, BM25Ingestor
    from llm.providers import PROVIDERS as LLM_PROVIDERS
    from prompt import build_prompt

basic_rag_dir = Path(__file__).resolve().parents[2] / "basic-rag"
sys.path.insert(0, str(basic_rag_dir))
sys.path.insert(0, str(basic_rag_dir / "embedding"))
from embedding import create_client  # noqa: E402

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "dashscope")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "dashscope")
TOP_K = int(os.getenv("TOP_K", "10"))
RRF_K = 60


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    rank_bm25: int = -1
    rank_milvus: int = -1
    bm25_score: float = 0.0
    milvus_score: float = 0.0
    final_score: float = 0.0


class QuestionProcessor:
    """混合 RAG 处理器：BM25 + 向量检索（COSINE） +  完整 Chunk 扩展。"""

    def __init__(
        self,
        *,
        milvus_uri: str = MILVUS_URI,
        milvus_collection: str = MILVUS_COLLECTION,
        bm25_index_dir: str | Path = BM25_INDEX_DIR,
        embedding_provider: str = EMBEDDING_PROVIDER,
        embedding_model: str | None = EMBEDDING_MODEL,
        embedding_dim: int = EMBEDDING_DIM,
        llm_provider: str = LLM_PROVIDER,
        llm_model: str | None = None,
        top_k: int = TOP_K,
        expand_siblings: bool = True,
        max_siblings: int = 5,
        merge_mode: str = "rrf",
        rrf_k: int = RRF_K,
        bm25_weight: float = 0.5,
        milvus_weight: float = 0.5,
    ):
        self.milvus_uri = milvus_uri
        self.milvus_collection = milvus_collection
        self.bm25_index_dir = Path(bm25_index_dir)
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        self.llm_provider_name = llm_provider
        self.llm_model = llm_model
        self.top_k = top_k
        self.expand_siblings = expand_siblings
        self.max_siblings = max_siblings
        self.merge_mode = merge_mode
        self.rrf_k = rrf_k
        self.bm25_weight = bm25_weight
        self.milvus_weight = milvus_weight

        self._bm25: BM25Ingestor | None = None
        self._milvus_client: MilvusClient | None = None
        self._embedding_client: Any = None
        self._llm: ChatOpenAI | None = None

    @property
    def bm25(self) -> BM25Ingestor:
        if self._bm25 is None:
            self._bm25 = BM25Ingestor(self.bm25_index_dir)
        return self._bm25

    @property
    def milvus_client(self) -> MilvusClient:
        if self._milvus_client is None:
            self._milvus_client = MilvusClient(uri=self.milvus_uri)
            self._milvus_client.load_collection(self.milvus_collection)
        return self._milvus_client

    @property
    def embedding_client(self) -> Any:
        if self._embedding_client is None:
            self._embedding_client = create_client(
                self.embedding_provider,
                model=self.embedding_model,
                dimensions=self.embedding_dim,
            )
            self._embedding_client.timeout = 300
        return self._embedding_client

    @property
    def llm(self) -> ChatOpenAI:
        if self._llm is None:
            provider = LLM_PROVIDERS[self.llm_provider_name]
            model = self.llm_model or provider.default_model
            kwargs: dict[str, Any] = {"model": model, "api_key": os.getenv(provider.api_key_env)}
            if provider.base_url:
                kwargs["base_url"] = provider.base_url
            self._llm = ChatOpenAI(**kwargs)
        return self._llm

    def search(self, query: str) -> list[SearchResult]:
        """执行混合检索（BM25 + 向量），返回融合后的结果。"""
        bm25_hits = self._keyword_search(query)
        milvus_hits = self._vector_search(query)

        merged = self._merge_results(bm25_hits, milvus_hits)
        merged.sort(key=lambda r: r.final_score, reverse=True)
        merged = merged[: self.top_k]

        if self.expand_siblings:
            merged = self._expand_siblings(merged)

        return merged

    async def ask(self, query: str, kind: str) -> str:
        """完整问答：检索 → Prompt → LLM 生成。"""
        results = self.search(query)

        chunks: list[dict] = []
        for r in results:
            chunk = {
                "chunk_id": r.chunk_id,
                "text": r.text,
                "metadata": r.metadata,
                "score": r.final_score,
                "source": r.source,
            }
            if r.rank_milvus >= 0:
                chunk["cosine_similarity"] = r.milvus_score
            if r.rank_bm25 >= 0:
                chunk["bm25_score"] = r.bm25_score
            chunks.append(chunk)

        prompt = build_prompt(query=query, kind=kind, top_k=len(chunks), chunks=chunks)
        response = await self.llm.ainvoke(prompt)
        return response.content

    def close(self) -> None:
        if self._milvus_client is not None:
            self._milvus_client.close()
            self._milvus_client = None

    def __enter__(self) -> QuestionProcessor:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _keyword_search(self, query: str) -> list[SearchResult]:
        raw = self.bm25.search(query, top_k=self.top_k)
        results: list[SearchResult] = []
        for rank, item in enumerate(raw):
            metadata = item.get("metadata", {})
            results.append(
                SearchResult(
                    chunk_id=item["chunk_id"],
                    text=item["text"],
                    metadata=metadata,
                    source="bm25",
                    rank_bm25=rank,
                    bm25_score=item.get("score", 0.0),
                )
            )
        return results

    def _vector_search(self, query: str) -> list[SearchResult]:
        try:
            query_vector = self.embedding_client.embed_query(query)
            hits = self.milvus_client.search(
                collection_name=self.milvus_collection,
                data=[query_vector],
                anns_field="embedding",
                limit=self.top_k,
                output_fields=[
                    "chunk_id",
                    "text",
                    "doc_id",
                    "page_index",
                    "chunk_type",
                    "title",
                    "company_name",
                ],
                search_params={"metric_type": "COSINE"},
            )
        except Exception:
            return []

        results: list[SearchResult] = []
        for rank, hit in enumerate(hits[0]):
            entity = hit["entity"]
            results.append(
                SearchResult(
                    chunk_id=entity["chunk_id"],
                    text=entity["text"],
                    metadata={
                        "doc_id": entity.get("doc_id", ""),
                        "page_index": entity.get("page_index"),
                        "chunk_type": entity.get("chunk_type", "text"),
                        "title": entity.get("title") or "",
                        "company_name": entity.get("company_name") or "",
                    },
                    source="milvus",
                    rank_milvus=rank,
                    milvus_score=hit["distance"],
                )
            )
        return results

    def _merge_results(
        self,
        bm25_hits: list[SearchResult],
        milvus_hits: list[SearchResult],
    ) -> list[SearchResult]:
        by_id: dict[str, SearchResult] = {}

        for r in bm25_hits:
            by_id[r.chunk_id] = r

        for r in milvus_hits:
            if r.chunk_id in by_id:
                existing = by_id[r.chunk_id]
                existing.rank_milvus = r.rank_milvus
                existing.milvus_score = r.milvus_score
                existing.source = "merged"
            else:
                by_id[r.chunk_id] = r

        # 保留 BM25 和 Milvus 两路召回，避免低向量分数误杀表格和关键词证据。
        merged = list(by_id.values())

        if self.merge_mode == "rrf":
            for r in merged:
                r.final_score = self._compute_rrf(r)
        else:
            for r in merged:
                r.final_score = self._compute_weighted(r, bm25_hits, milvus_hits)

        return merged

    def _compute_rrf(self, result: SearchResult) -> float:
        score = 0.0
        if result.rank_bm25 >= 0:
            score += 1.0 / (self.rrf_k + result.rank_bm25 + 1)
        if result.rank_milvus >= 0:
            score += 1.0 / (self.rrf_k + result.rank_milvus + 1)
        return score

    def _compute_weighted(
        self,
        result: SearchResult,
        bm25_hits: list[SearchResult],
        milvus_hits: list[SearchResult],
    ) -> float:
        def _min_max(scores: list[float]) -> tuple[float, float]:
            if not scores:
                return 0.0, 1.0
            return min(scores), max(scores)

        bm25_scores = [r.bm25_score for r in bm25_hits]
        milvus_scores = [r.milvus_score for r in milvus_hits]
        bm25_min, bm25_max = _min_max(bm25_scores)
        milvus_min, milvus_max = _min_max(milvus_scores)

        norm_bm25 = 0.0
        norm_milvus = 0.0

        if result.rank_bm25 >= 0 and bm25_max > bm25_min:
            norm_bm25 = (result.bm25_score - bm25_min) / (bm25_max - bm25_min + 1e-9)
        if result.rank_milvus >= 0 and milvus_max > milvus_min:
            norm_milvus = (result.milvus_score - milvus_min) / (milvus_max - milvus_min + 1e-9)

        return self.bm25_weight * norm_bm25 + self.milvus_weight * norm_milvus

    def _expand_siblings(self, results: list[SearchResult]) -> list[SearchResult]:
        expanded: list[SearchResult] = []
        seen_ids: set[str] = {r.chunk_id for r in results}

        for anchor in results:
            expanded.append(anchor)
            siblings = self._query_page_siblings(
                doc_id=anchor.metadata.get("doc_id", ""),
                page_index=anchor.metadata.get("page_index"),
                exclude_ids=seen_ids,
            )
            for sibling in siblings[: self.max_siblings]:
                expanded.append(sibling)
                seen_ids.add(sibling.chunk_id)

        return expanded

    def _query_page_siblings(
        self,
        doc_id: str,
        page_index: int | None,
        exclude_ids: set[str],
    ) -> list[SearchResult]:
        if not doc_id or page_index is None:
            return []

        escaped_doc_id = doc_id.replace('"', '\\"')
        filter_expr = f'doc_id == "{escaped_doc_id}" and page_index == {page_index}'

        try:
            entities = self.milvus_client.query(
                collection_name=self.milvus_collection,
                filter=filter_expr,
                output_fields=[
                    "chunk_id",
                    "text",
                    "doc_id",
                    "page_index",
                    "chunk_type",
                    "title",
                    "company_name",
                ],
            )
        except Exception:
            return []

        siblings: list[SearchResult] = []
        for entity in entities:
            cid = entity["chunk_id"]
            if cid in exclude_ids:
                continue
            siblings.append(
                SearchResult(
                    chunk_id=cid,
                    text=entity["text"],
                    metadata={
                        "doc_id": entity.get("doc_id", ""),
                        "page_index": entity.get("page_index"),
                        "chunk_type": entity.get("chunk_type", "text"),
                        "title": entity.get("title") or "",
                        "company_name": entity.get("company_name") or "",
                    },
                    source="sibling",
                    final_score=0.0,
                )
            )
        return siblings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="答案检索")
    parser.add_argument(
        "--query",
        default="What was the largest single spending of CrossFirst Bank on executive compensation in USD?",
        help="用户问题",
    )
    parser.add_argument(
        "--kind", default="name", choices=["number", "name", "names", "boolean"], help="问题类型"
    )
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument("--milvus-uri", default=MILVUS_URI)
    parser.add_argument("--milvus-collection", default=MILVUS_COLLECTION)
    parser.add_argument("--bm25-index-dir", type=Path, default=BM25_INDEX_DIR)
    parser.add_argument("--embedding-provider", default=EMBEDDING_PROVIDER)
    parser.add_argument("--embedding-model", default=EMBEDDING_MODEL)
    parser.add_argument("--embedding-dim", type=int, default=EMBEDDING_DIM)
    parser.add_argument("--llm-provider", default=LLM_PROVIDER)
    parser.add_argument("--llm-model", default=None)
    parser.add_argument("--merge-mode", choices=["rrf", "weighted"], default="rrf")
    parser.add_argument("--rrf-k", type=int, default=RRF_K)
    parser.add_argument("--bm25-weight", type=float, default=0.5)
    parser.add_argument("--milvus-weight", type=float, default=0.5)
    parser.add_argument("--no-expand", dest="expand_siblings", action="store_false")
    parser.add_argument("--max-siblings", type=int, default=5)
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    with QuestionProcessor(
        milvus_uri=args.milvus_uri,
        milvus_collection=args.milvus_collection,
        bm25_index_dir=args.bm25_index_dir,
        embedding_provider=args.embedding_provider,
        embedding_model=args.embedding_model,
        embedding_dim=args.embedding_dim,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        top_k=args.top_k,
        expand_siblings=args.expand_siblings,
        max_siblings=args.max_siblings,
        merge_mode=args.merge_mode,
        rrf_k=args.rrf_k,
        bm25_weight=args.bm25_weight,
        milvus_weight=args.milvus_weight,
    ) as question_processor:
        result = await question_processor.ask(args.query, args.kind)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())

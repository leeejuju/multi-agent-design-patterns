from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pymilvus import MilvusClient

basic_rag_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(basic_rag_dir))
sys.path.insert(0, str(basic_rag_dir / "embeding"))
from embeding import create_client  # noqa: E402
from llm.providers import PROVIDERS  # noqa: E402

load_dotenv()


async def search(
    milvus_uri: str,
    collection_name: str,
    query: str,
    *,
    top_k: int,
    embedding_provider: str,
    embedding_model: str | None,
    dimensions: int,
) -> list[dict]:
    embedding_client = create_client(
        embedding_provider, model=embedding_model, dimensions=dimensions
    )
    embedding_client.timeout = 300
    query_vector = embedding_client.embed_query(query)

    client = MilvusClient(uri=milvus_uri, token=os.getenv("MILVUS_TOKEN", ""))
    hits = client.search(
        collection_name=collection_name,
        data=[query_vector],
        anns_field="embedding",
        limit=top_k,
        output_fields=["doc_id", "chunk_no", "content", "source", "label", "metadata"],
        search_params={"metric_type": "COSINE"},
    )
    client.close()

    chunks = []
    for hit in hits[0]:
        entity = hit["entity"]
        chunks.append(
            {
                "doc_id": entity["doc_id"],
                "chunk_no": entity["chunk_no"],
                "content": entity["content"],
                "source": entity["source"],
                "label": entity["label"],
                "metadata": entity["metadata"],
                "cosine_similarity": hit["distance"],
            }
        )
    return chunks


def build_prompt(query: str, kind: str, top_k: int, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"Retrieved chunk {index}\n"
        f"pdf_sha1: {chunk['doc_id']}\n"
        f"document: {chunk['source']}\n"
        f"label: {chunk['label']}\n"
        f"page_index: {chunk['metadata'].get('page')}\n"
        f"chunk_no: {chunk['chunk_no']}\n"
        f"cosine_similarity: {chunk['cosine_similarity']:.6f}\n"
        f"content:\n{chunk['content']}"
        for index, chunk in enumerate(chunks, start=1)
    )
    return f"""Answer the question using only the context.

        Retrieved top_k: {top_k}

        Answer rules:
        - Return JSON only.
        - JSON fields: question_text, kind, value, references, retrieval_results, reasoning_process.
        - kind must be exactly "{kind}".
        - If the context is not enough, value must be "N/A" and references must be [].
        - For kind "number", value must be only a number string.
        - Do not include currency symbols, commas, spaces, or notes for kind "number".
        - For kind "name", value must be only the name.
        - For kind "names", value must be a list of names.
        - For kind "boolean", value must be true or false.
        - references must contain source pages used for the answer.
        - Each reference format: {{"pdf_sha1": "...", "page_index": 0}}.
        - retrieval_results must list the retrieved chunks.
        - retrieval_results must include all top_k retrieved chunks from the context.
        - Each retrieval result must include pdf_sha1, page_index, document, cosine_similarity.
        - reasoning_process must briefly explain the evidence used.
        - reasoning_process must explain how the answer was derived.

        Context:
        {context}

        Question:
        {query}
    """


async def answer(
    milvus_uri: str,
    collection_name: str,
    query: str,
    *,
    kind: str,
    top_k: int,
    embedding_provider: str,
    embedding_model: str | None,
    dimensions: int,
    llm_provider: str,
) -> str:
    chunks = await search(
        milvus_uri,
        collection_name,
        query,
        top_k=top_k,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        dimensions=dimensions,
    )
    provider = PROVIDERS[llm_provider]
    llm = ChatOpenAI(
        model=provider.default_model,
        base_url=provider.base_url,
        api_key=os.getenv(provider.api_key_env),
    )
    response = await llm.ainvoke(build_prompt(query, kind, top_k, chunks))
    return response.content


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--kind", required=True, choices=["number", "name", "names", "boolean"])
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--milvus-uri", default=os.getenv("MILVUS_URI", "http://localhost:19530"))
    parser.add_argument("--collection", default=os.getenv("MILVUS_COLLECTION", "rag_chunk"))
    parser.add_argument("--embedding-provider", default="dashscope")
    parser.add_argument("--embedding-model", default=None)
    parser.add_argument("--llm-provider", default="dashscope")
    parser.add_argument("--dimensions", type=int, default=1024)
    args = parser.parse_args()

    result = await answer(
        args.milvus_uri,
        args.collection,
        args.query,
        kind=args.kind,
        top_k=args.top_k,
        embedding_provider=args.embedding_provider,
        embedding_model=args.embedding_model,
        dimensions=args.dimensions,
        llm_provider=args.llm_provider,
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())

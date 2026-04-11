# PostgreSQL RAG Benchmark Schema

This benchmark now uses the SQLAlchemy schema under `llm-rag/RAG-Challenge-2/basic-rag/dataset`.

## Files
- `../RAG-Challenge-2/basic-rag/dataset/models.py`: table definition
- `../RAG-Challenge-2/basic-rag/dataset/init_db.py`: schema initialization entrypoint

## Design Goals
- Keep the hot path in one table to avoid `JOIN` overhead during retrieval benchmarks.
- Support vector search, full-text search, and hybrid retrieval on the same dataset.
- Preserve a small set of experiment fields so chunking and retrieval strategies can be compared reproducibly.

## Table Shape
The schema creates one table: `rag_chunk`.

Important columns:
- `doc_id`: groups chunks from the same source document
- `chunk_no`: preserves chunk order inside one document
- `content`: raw chunk text
- `content_tsv`: generated full-text search vector
- `embedding`: `pgvector` column, fixed to `vector(1024)`
- `source`: dataset identifier, for example `finance`, `wiki`, `manual`
- `label`: experiment identifier, for example `chunk512_overlap64`
- `metadata`: low-frequency experiment metadata in `jsonb`

## Assumptions
- PostgreSQL has the `pgvector` extension installed.
- Embedding dimension is `1024`. If the embedding model changes, update `vector(1024)` before running the schema.
- Full-text search uses `to_tsvector('simple', content)` to avoid language-specific preprocessing in the benchmark baseline.

## Initialize The Schema
```bash
uv run python llm-rag/RAG-Challenge-2/basic-rag/dataset/init_db.py
```

## Recommended Load Contract
- Use one `label` per chunking strategy.
- Reuse the same source corpus across labels when comparing retrieval performance.
- Keep `doc_id` stable across experiments so recall comparisons stay aligned.

## Query Templates
Vector search:
```sql
SELECT id, doc_id, chunk_no, content, embedding <=> $1 AS score
FROM rag_chunk
WHERE label = $2
ORDER BY embedding <=> $1
LIMIT $3;
```

Full-text search:
```sql
SELECT id, doc_id, chunk_no, content, ts_rank_cd(content_tsv, websearch_to_tsquery('simple', $1)) AS score
FROM rag_chunk
WHERE label = $2
  AND content_tsv @@ websearch_to_tsquery('simple', $1)
ORDER BY score DESC
LIMIT $3;
```

Hybrid retrieval:
```sql
WITH vector_hits AS (
    SELECT id, 1.0 - (embedding <=> $1) AS vector_score
    FROM rag_chunk
    WHERE label = $2
    ORDER BY embedding <=> $1
    LIMIT $3
),
text_hits AS (
    SELECT id, ts_rank_cd(content_tsv, websearch_to_tsquery('simple', $4)) AS text_score
    FROM rag_chunk
    WHERE label = $2
      AND content_tsv @@ websearch_to_tsquery('simple', $4)
    ORDER BY text_score DESC
    LIMIT $3
)
SELECT c.id, c.doc_id, c.chunk_no, c.content,
       COALESCE(v.vector_score, 0) AS vector_score,
       COALESCE(t.text_score, 0) AS text_score,
       COALESCE(v.vector_score, 0) + COALESCE(t.text_score, 0) AS hybrid_score
FROM rag_chunk AS c
LEFT JOIN vector_hits AS v ON c.id = v.id
LEFT JOIN text_hits AS t ON c.id = t.id
WHERE v.id IS NOT NULL OR t.id IS NOT NULL
ORDER BY hybrid_score DESC
LIMIT $3;
```

## Benchmark Notes
- `label` is the main slice for comparing chunking strategies.
- `source` is the main slice for comparing datasets.
- Keep benchmark queries identical except for the retrieval strategy being tested.

# Basic RAG PostgreSQL Setup

Files:
- `models.py`: SQLAlchemy model for the `rag_chunk` table
- `db.py`: engine and schema helpers
- `init_db.py`: initialize the PostgreSQL schema with SQLAlchemy
- `file_parser.py`: extract files, optionally call OCR, then export chunked JSONL

Default table:
- `rag_chunk`

Run:
```bash
uv run python llm-rag/RAG-Challenge-2/basic-rag/dataset/init_db.py
```

Drop and recreate:
```bash
uv run python llm-rag/RAG-Challenge-2/basic-rag/dataset/init_db.py --drop-first
```

Override database:
```bash
$env:DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:54321/rag_benchmark"
uv run python llm-rag/RAG-Challenge-2/basic-rag/dataset/init_db.py
```

Build JSONL with one chunk config:
```bash
uv run python llm-rag/RAG-Challenge-2/basic-rag/dataset/file_parser.py `
  --input llm-rag/RAG-Challenge-2/basic-rag/examples `
  --output llm-rag/RAG-Challenge-2/basic-rag/output/chunks.jsonl `
  --chunk-size 1000 `
  --chunk-overlap 200
```

Build JSONL with multiple chunk configs:
```bash
uv run python llm-rag/RAG-Challenge-2/basic-rag/dataset/file_parser.py `
  --input llm-rag/RAG-Challenge-2/basic-rag/examples `
  --output llm-rag/RAG-Challenge-2/basic-rag/output/chunks.jsonl `
  --chunk-config 500:50 `
  --chunk-config 1000:200 `
  --chunk-config 1500:300
```

Use PaddleOCR-compatible HTTP API for images or scanned PDFs:
```bash
uv run python llm-rag/RAG-Challenge-2/basic-rag/dataset/file_parser.py `
  --input llm-rag/RAG-Challenge-2/basic-rag/examples `
  --output llm-rag/RAG-Challenge-2/basic-rag/output/chunks.jsonl `
  --chunk-config 1000:200 `
  --ocr-provider paddle_api `
  --ocr-api-url http://127.0.0.1:8000/ocr `
  --ocr-api-header "Authorization:Bearer <token>"
```

Expected JSONL fields:
- `doc_id`
- `chunk_no`
- `content`
- `token_count`
- `char_count`
- `source`
- `label`
- `metadata.chunk_size`
- `metadata.chunk_overlap`

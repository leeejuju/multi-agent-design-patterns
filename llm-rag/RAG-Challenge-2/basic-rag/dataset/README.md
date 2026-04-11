# Basic RAG PostgreSQL Setup

Files:
- `models.py`: SQLAlchemy model for the `rag_chunk` table
- `db.py`: engine and schema helpers
- `init_db.py`: initialize the PostgreSQL schema with SQLAlchemy

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

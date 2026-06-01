# multi-agent-design-patterns

![Banner](assets/LLM.jpg)

A learning-driven collection of **multi-agent design pattern** implementations, framework deep-dives,
and LLM experimentation modules — covering agent architectures, RAG strategies, memory systems,
and model fine-tuning.

基于《Agentic Design Patterns》的**多智能体设计模式**学习合集，涵盖智能体架构、框架源码解析、
RAG 检索策略、记忆系统与模型训练实验。

---

## 🗂 Project Structure

```
.
├── multi-agent-design-patterns/   # Core agent design patterns
│   └── lesson1_ordinary_agent/    # Base agent (BaseAgent / BaseContext) + FastAPI server + Web UI
├── multi-agent-framework/         # Framework implementations & source reading
│   ├── langchain/                 # LangChain V1.0+ — core, runnable patterns, LangGraph
│   ├── deepagent/                 # DeepAgent harness architecture notes
│   ├── AgentScope/                # AgentScope multi-agent framework
│   ├── deer-flow/                 # Deer-flow agent workflow
│   ├── OpenManus/                 # OpenManus general-purpose agent
│   └── youtu-agent/               # Youtu-agent (Tencent)
├── agent-system-design/           # Agent system architecture & engineering
│   ├── building-effective-agents/ # Anthropic's "Building Effective Agents" guide
│   ├── harness-engeneering/       # Agent harness patterns
│   └── multi-agent-research-system/ # Multi-agent research system architecture
├── agent-system-paper/            # Paper reading & analysis
│   └── Is-Grep-All-You-Need/      # Graph-based IR vs. Grep for agent search
├── multi-agent-memory/            # Agent memory systems
│   ├── evermemos/                 # Evermemos memory backend
│   ├── mem0/                      # Mem0 memory layer
│   └── Zep/                       # Zep memory platform
├── llm-memory/                    # Memory practice
│   └── evermind-practice/         # Evermind hands-on experiments
├── llm-rag/                       # RAG strategy validation
│   ├── ECOM1/                     # E-commerce RAG sample (product search)
│   ├── RAG-Challenge-2/           # Multi-strategy RAG comparison
│   │   ├── basic-rag/             # Baseline hard-chunk approach
│   │   ├── graph-rag/             # Graph-based retrieval
│   │   ├── grep-rag/              # Grep-based retrieval
│   │   ├── ragflow/               # RAGFlow deep layout parsing
│   │   └── structural-rag/        # Markdown hierarchical chunking + parent-child retrieval
│   └── RAG-Data/                  # Benchmark datasets (annual reports, financial docs)
├── llm-lab/                       # Model experimentation
│   ├── llm-base/                  # Transformer & BERT from scratch (PyTorch)
│   ├── llm-sft/                   # Supervised fine-tuning resources
│   └── llm-dpo/                   # DPO (Direct Preference Optimization) resources
└── agent-sys-asyncio/             # Async I/O patterns for agent systems
```

---

## 🔑 Key Modules

### Agent Design Patterns (`multi-agent-design-patterns/`)

Implements the fundamental building blocks from *Agentic Design Patterns*:
- **BaseAgent** — abstract agent class with `name`, `description`, `context`, and `stream_messages()`
- **BaseContext** — dataclass for agent state management with `update()`, `get_context()`, serialization
- **ModelProvider** — Pydantic-based LLM configuration (provider, api_key, base_url)
- Full-stack demo: FastAPI backend + React (Vite) frontend

### Framework Deep-Dives (`multi-agent-framework/`)

Source-level reading notes and architecture analysis of major agent frameworks:
- **LangChain 1.0** (2025 Edition) — core primitives, Runnable patterns, LangGraph state machines
- **DeepAgent** — backend / middleware / profile harness architecture
- **OpenManus**, **AgentScope**, **Deer-flow**, **Youtu-agent**

### RAG Strategy Lab (`llm-rag/`)

Systematic RAG strategy comparison targeting **~80% accuracy** on professional documents:
- Baseline hard-chunk vs. RAGFlow deep parsing vs. Markdown hierarchical chunking
- Parent-child retrieval pattern for long-document context
- Real-world datasets: annual reports, financial statements, cross-industry documents

### Memory Systems (`multi-agent-memory/`)

Exploration of agent memory backends: **Evermemos**, **Mem0**, **Zep** — covering vector search,
session persistence, and long-term memory patterns.

### Model Lab (`llm-lab/`)

- **llm-base**: Transformer (Attention Is All You Need) and BERT implementations from scratch
- **llm-sft**: SFT dataset and training recipe collection
- **llm-dpo**: DPO alignment resources

---

## 🛠 Tech Stack

| Category       | Technologies                                                                 |
| -------------- | ---------------------------------------------------------------------------- |
| **Agent**      | LangChain ≥1.2, LangGraph ≥1.0.5, DeepAgents ≥0.4.3                          |
| **LLM SDKs**   | langchain-openai, langchain-deepseek, langchain-google-genai                  |
| **Vector DB**  | Milvus (pymilvus), pgvector                                                  |
| **RAG**        | ragas ≥0.4.3, docling ≥2.85, langchain-text-splitters                        |
| **Doc Parsing**| PyMuPDF, pymupdf4llm                                                         |
| **Config**     | Pydantic-settings ≥2.11                                                      |
| **Tooling**    | Python ≥3.13, uv, Ruff (line-length=100, double-quotes)                      |

---

## 🚀 Getting Started

### Prerequisites

- Python ≥3.13
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd multi-agent-design-patterns

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys (SILICONFLOW_API_KEY, DASHSCOPE_API_KEY, GEMINI_API_KEY, etc.)
```

### Run Examples

```bash
# Run the base agent demo
uv run python main.py

# Run a specific module
uv run python multi-agent-design-patterns/lesson1_ordinary_agent/src/agents/manger.py

# Run tests for a specific module
uv run pytest -q multi-agent-framework/langchain/1-langchain-core/runnable_part
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint check
uv run ruff check .
```

---

## 📋 Conventions

- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `docs:`, `chore:`, etc.
  - See [CONTRIBUTING.md](CONTRIBUTING.md) for details (Chinese descriptions)
- **Code style**: Ruff with line-length 100, double-quotes, `snake_case` for functions, `PascalCase` for classes
- **Python**: ≥3.13

---

## 📄 License

This project is licensed under the terms in [LICENSE](LICENSE).

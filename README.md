# multi-agent-design-patterns

[中文版本](README_CN.md)

A personal knowledge base for LLM learning — agent architectures, framework reading notes, RAG strategies, memory systems, and model experiments.

---

## Directory Structure

```
.
├── multi-agent-design-patterns/   # Agent design pattern practice
│   └── lesson1_ordinary_agent/    #   BaseAgent/BaseContext + FastAPI + React frontend
├── multi-agent-framework/         # Framework reading notes
│   ├── langchain/                 #   Reflections on reading LangChain V1.0 source (runnables, messages, tools, etc.)
│   ├── deepagent/                 #   DeepAgent harness architecture (backend / middleware / profile)
│   ├── AgentScope/                #   AgentScope multi-agent framework
│   ├── deer-flow/                 #   Deer-flow
│   ├── OpenManus/                 #   OpenManus
│   └── youtu-agent/               #   Youtu-agent (Tencent)
├── agent-system-design/           # Agent system design
│   ├── building-effective-agents/ #   Notes on Anthropic's "Building Effective Agents" & engineering reflections
│   ├── harness-engeneering/       #   Agent harness engineering
│   └── multi-agent-research-system/ # Multi-agent research system architecture
├── agent-system-paper/            # Paper reading
│   └── Is-Grep-All-You-Need/      #   Graph-based IR vs. Grep retrieval comparison
├── multi-agent-memory/            # Memory system survey
│   ├── evermemos/                 #   Evermemos
│   ├── mem0/                      #   Mem0
│   └── Zep/                       #   Zep
├── llm-memory/                    # Memory system practice
│   └── evermind-practice/         #   EverMemOS deployment & experiments
├── llm-rag/                       # RAG strategy validation
│   ├── ECOM1/                     #   BitGN E-commerce agent benchmark (ECOM)
│   ├── RAG-Challenge-2/           #   Multi-strategy RAG comparison
│   │   ├── basic-rag/             #     Hard-chunk baseline
│   │   ├── graph-rag/             #     Graph-based retrieval
│   │   ├── grep-rag/              #     Grep-based retrieval (coding agent style)
│   │   ├── ragflow/               #     RAGFlow deep layout parsing
│   │   └── structural-rag/        #     Markdown hierarchical chunking + parent-child retrieval
│   └── RAG-Data/                  #   Benchmark datasets (annual reports, financial docs)
├── llm-lab/                       # Model experiments
│   ├── llm-base/                  #   Transformer & BERT from scratch (PyTorch)
│   ├── llm-sft/                   #   SFT fine-tuning resources (datasets, training recipes)
│   └── llm-dpo/                   #   DPO alignment resources
└── agent-sys-asyncio/             # Async I/O for agent systems
```

---

## Key Modules

### Framework Reading Notes (`multi-agent-framework/`)

Personal reflections and notes from reading major agent framework source code, with LangChain as the primary focus:
- **langchain-core**: Runnable protocol, message types, tool interfaces, language model base classes, serialization
- **langgraph**: State graphs, checkpointing, Pregel engine
- **deepagent**: Three-layer harness architecture (Backend / Middleware / Profiles)

### "Building Effective Agents" Notes (`agent-system-design/`)

A detailed breakdown of Anthropic's multi-agent research system design principles, including personal engineering reflections:
- Orchestrator pattern: Leader → Sub-agent task decomposition
- Search strategy: Start wide, then narrow down
- Parallel tool calling & MapReduce patterns
- Real-world implementation experience with LangGraph Workflow

### RAG Strategy Validation (`llm-rag/`)

Comparative experiments on retrieval quality for professional long documents, targeting ~80% accuracy:
- **Baseline**: Physical hard-chunking
- **RAGFlow**: DeepDoc model for complex PDF layout restoration
- **Structural RAG**: PDF → Markdown → hierarchical chunking + parent-child retrieval
- **Grep RAG**: Keyword matching without embeddings or vector databases (coding agent approach)
- **ECOM1**: BitGN e-commerce operations agent benchmark

### Model Experiments (`llm-lab/`)

- **Transformer**: Full PyTorch implementation based on "Attention Is All You Need"
- **BERT**: PyTorch reproduction of Google AI's 2018 BERT
- **SFT/DPO**: Fine-tuning and alignment resource collection

### Memory Systems (`llm-memory/`, `multi-agent-memory/`)

- **EverMemOS**: Four-layer brain-inspired memory OS (93% on LoCoMo benchmark)
- **Mem0 / Zep / Evermemos**: Memory backend survey

---

*This is a personal learning repository. Most content is in Chinese, and some modules are still being populated.*

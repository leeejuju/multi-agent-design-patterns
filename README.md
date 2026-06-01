# multi-agent-design-patterns

[中文版本](README_CN.md)

A personal knowledge base for LLM learning — agent architectures, framework reading notes, RAG strategies, memory systems, and model experiments.

---

## Directory Structure

```
.
├── multi-agent-design-patterns/          # Agent design pattern practice
│   └── lesson1_ordinary_agent/           #   BaseAgent / BaseContext + FastAPI + React frontend
├── multi-agent-framework/                # Framework reading notes
│   ├── langchain/                        #   LangChain V1.0
│   │   ├── 1-langchain-core/             #     langchain-core: runnables, messages, tools, prompts...
│   │   ├── 2-langchain/                  #     langchain: agent
│   │   └── 3-langgraph/                  #     langgraph: state graph, checkpoint, pregel
│   ├── deepagent/                        #   DeepAgent harness architecture
│   ├── AgentScope/                       #   AgentScope multi-agent framework
│   ├── deer-flow/                        #   Deer-flow
│   ├── OpenManus/                        #   OpenManus
│   └── youtu-agent/                      #   Youtu-agent (Tencent)
├── agent-system-design/                  # Agent system design
│   ├── building-effective-agents/        #   Anthropic "Building Effective Agents" notes
│   ├── harness-engeneering/              #   Agent harness engineering
│   ├── multi-agent-research-system/      #   Multi-agent research system architecture
│   └── writing-effective-tools-for-agents/ # Effective tool design for agents
├── agent-system-paper/                   # Paper reading
│   └── Is-Grep-All-You-Need/             #   Graph-based IR vs. Grep for agent search
├── agent-sys-asyncio/                    # Async I/O for agent systems
├── multi-agent-memory/                   # Memory system survey
│   ├── evermemos/                        #   Evermemos
│   ├── mem0/                             #   Mem0
│   └── Zep/                              #   Zep
├── llm-memory/                           # Memory system practice
│   └── evermind-practice/                #   EverMemOS deployment & experiments
├── llm-rag/                              # RAG strategy validation
│   ├── ECOM1/                            #   BitGN E-commerce agent benchmark
│   │   └── ecom-sample/                  #     Runnable Python sample
│   ├── RAG-Challenge-2/                  #   Multi-strategy RAG comparison
│   │   ├── basic-rag/                    #     Hard-chunk baseline
│   │   ├── graph-rag/                    #     Graph-based retrieval
│   │   ├── grep-rag/                     #     Grep-based retrieval (coding agent style)
│   │   ├── ragflow/                      #     RAGFlow deep layout parsing
│   │   └── structural-rag/               #     Markdown hierarchical chunking + parent-child retrieval
│   ├── RAG-Challenge-3/                  #   Next-phase RAG experiments
│   └── RAG-Data/                         #   Benchmark datasets
│       ├── IIya-rice/                    #     IIya-rice documents
│       └── RAG-Challlenge-dataset/       #     RAG Challenge standard test set
├── llm-lab/                              # Model experiments
│   ├── llm-base/                         #   Foundation model implementations
│   │   ├── transformer/                  #     Transformer (Attention Is All You Need)
│   │   ├── BERT-pytorch/                 #     BERT PyTorch reproduction
│   │   └── NLP_textClassifier-master/    #     Text classification baselines
│   ├── llm-sft/                          #   SFT resources (datasets, training recipes)
│   └── llm-dpo/                          #   DPO alignment resources
└── vibecoding-workshop/                  # Workshop materials
```

---

## Key Modules

### Framework Reading Notes (`multi-agent-framework/`)

Personal reflections from reading major agent framework source code, centered on LangChain:

- **1-langchain-core**: Runnable protocol, message types, tool interfaces, language model base classes, serialization — the foundational abstractions that all LangChain packages depend on
- **2-langchain**: Higher-level agent construction (`create_agent`, etc.)
- **3-langgraph**: State graphs, checkpointing, Pregel engine — the orchestration layer
- **deepagent**: Three-layer harness architecture (Backend / Middleware / Profiles)

### "Building Effective Agents" Notes (`agent-system-design/`)

A detailed breakdown of Anthropic's multi-agent research system design principles, with personal engineering reflections:

- Orchestrator pattern: Leader → Sub-agent task decomposition
- Search strategy: Start wide, then narrow down
- Parallel tool calling & MapReduce patterns
- Real-world implementation experience with LangGraph Workflow

### RAG Strategy Validation (`llm-rag/`)

Comparative experiments across `RAG-Challenge-2/` and `RAG-Challenge-3/`, targeting ~80% retrieval accuracy on professional long documents (annual reports, financial statements):

| Strategy | Directory | Approach |
|----------|-----------|----------|
| Baseline | `basic-rag/` | Physical hard-chunking, no semantic analysis |
| Graph RAG | `graph-rag/` | Graph-based information retrieval |
| Grep RAG | `grep-rag/` | Keyword matching, no embeddings, no vector DB |
| RAGFlow | `ragflow/` | DeepDoc model for complex PDF layout restoration |
| Structural RAG | `structural-rag/` | PDF → Markdown → hierarchical chunking + parent-child retrieval |

Also includes `ECOM1/` — the BitGN E-commerce operations agent benchmark with runnable Python sample.

### Model Experiments (`llm-lab/`)

- **llm-base/transformer**: Full PyTorch implementation based on "Attention Is All You Need"
- **llm-base/BERT-pytorch**: PyTorch reproduction of Google AI's 2018 BERT
- **llm-base/NLP_textClassifier-master**: Classic text classification baselines (textCNN, BiLSTM, Transformer, etc.)
- **llm-sft**: SFT dataset and training recipe collection
- **llm-dpo**: DPO alignment resource collection

### Memory Systems (`llm-memory/`, `multi-agent-memory/`)

- **evermind-practice/**: EverMemOS — four-layer brain-inspired memory OS (93% on LoCoMo benchmark)
- **evermemos/**, **mem0/**, **Zep/**: Memory backend survey

---

*This is a personal learning repository. Most content is in Chinese, and some modules are still being populated.*

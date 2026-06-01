# multi-agent-design-patterns

个人 LLM 学习与知识库，涵盖智能体架构、框架源码阅读、RAG 检索策略、记忆系统与模型训练实验。

A personal knowledge base for LLM learning — agent architectures, framework source reading, RAG strategies, memory systems, and model experiments.

---

## 目录结构

```
.
├── multi-agent-design-patterns/   # 智能体设计模式实践
│   └── lesson1_ordinary_agent/    #   BaseAgent/BaseContext 基础实现 + FastAPI + React 前端
├── multi-agent-framework/         # 框架源码阅读与架构笔记
│   ├── langchain/                 #   LangChain V1.0 核心源码解析（runnables、messages、tools 等）
│   ├── deepagent/                 #   DeepAgent harness 架构（backend / middleware / profile）
│   ├── AgentScope/                #   AgentScope 多智能体框架
│   ├── deer-flow/                 #   Deer-flow
│   ├── OpenManus/                 #   OpenManus
│   └── youtu-agent/               #   Youtu-agent（腾讯）
├── agent-system-design/           # 智能体系统设计
│   ├── building-effective-agents/ #   Anthropic「Building Effective Agents」阅读笔记与实践反思
│   ├── harness-engeneering/       #   Agent harness 工程化
│   └── multi-agent-research-system/ # 多智能体研究系统架构
├── agent-system-paper/            # 论文阅读
│   └── Is-Grep-All-You-Need/      #   Graph-based IR vs Grep 检索对比
├── multi-agent-memory/            # 记忆系统调研
│   ├── evermemos/                 #   Evermemos
│   ├── mem0/                      #   Mem0
│   └── Zep/                       #   Zep
├── llm-memory/                    # 记忆系统实践
│   └── evermind-practice/         #   EverMemOS 部署与实验
├── llm-rag/                       # RAG 方案验证
│   ├── ECOM1/                     #   BitGN 电商智能体基准赛（ECOM）
│   ├── RAG-Challenge-2/           #   多策略 RAG 对比实验
│   │   ├── basic-rag/             #     物理分块（baseline）
│   │   ├── graph-rag/             #     图检索
│   │   ├── grep-rag/              #     Grep 检索（Coding Agent 风格）
│   │   ├── ragflow/               #     RAGFlow 深度布局解析
│   │   └── structural-rag/        #     Markdown 层级化拆分 + 父子检索
│   └── RAG-Data/                  #   测试数据集（年报、财务文档等）
├── llm-lab/                       # 模型实验
│   ├── llm-base/                  #   Transformer 与 BERT 从零实现（PyTorch）
│   ├── llm-sft/                   #   SFT 微调资源（数据集、训练配方）
│   └── llm-dpo/                   #   DPO 对齐资源
└── agent-sys-asyncio/             # Agent 系统异步 I/O
```

---

## 主要模块说明

### 智能体框架源码阅读（multi-agent-framework/）

对主流智能体框架的核心源码进行逐模块拆解与架构分析。以 LangChain 为重点：
- **langchain-core**：Runnable 协议、消息类型、工具接口、语言模型基类、序列化等底层抽象
- **langgraph**：状态图、checkpoint、pregel 引擎等编排层
- **deepagent**：harness 架构的三个核心分层（Backend / Middleware / Profiles）

### Anthropic「Building Effective Agents」阅读笔记（agent-system-design/）

详细拆解 Anthropic 多智能体研究系统的设计原则，包含作者本人的工程实践反思：
- Orchestrator 模式：Leader → Sub-agent 的任务分解与调度
- 搜索策略：Start wide, then narrow down
- 并行工具调用与 MapReduce 模式
- LangGraph Workflow 实现中的实际踩坑经验

### RAG 方案验证（llm-rag/）

围绕专业领域长文档（年报、财务报告）的检索质量对比实验，目标是达到 ~80% 的检索准确度：
- **Baseline**：物理硬分块
- **RAGFlow**：利用 DeepDoc 模型还原复杂 PDF 布局
- **Structural RAG**：PDF → Markdown → 层级化切片 + 父子检索
- **Grep RAG**：无向量库、无语义检索，直接关键字命中（Coding Agent 常用方案）
- **ECOM1**：BitGN 电商运营智能体基准赛

### 模型实验（llm-lab/）

- **Transformer**：基于「Attention Is All You Need」的 PyTorch 完整实现
- **BERT**：Google AI 2018 BERT 的 PyTorch 复现
- **SFT/DPO**：微调与对齐资料收集

### 记忆系统（llm-memory/、multi-agent-memory/）

- **EverMemOS**：四层类脑架构的记忆操作系统（LoCoMo 基准 93% 准确率）
- **Mem0 / Zep / Evermemos**：记忆后端调研

---

## 技术栈

Python ≥3.13 · LangChain · LangGraph · DeepAgents · Milvus · pgvector · PyMuPDF · RAGAS · Pydantic · uv · Ruff

---

*本仓库为个人学习用途，内容以中文为主，部分模块仍在持续补充中。*

# multi-agent-design-patterns

[English](README.md)

个人 LLM 学习知识库，涵盖智能体架构、框架源码阅读笔记、RAG 检索策略、记忆系统与模型训练实验。

---

## 目录结构

```
.
├── multi-agent-design-patterns/          # 智能体设计模式实践
│   └── lesson1_ordinary_agent/           #   BaseAgent / BaseContext 基础实现 + FastAPI + React 前端
├── multi-agent-framework/                # 框架源码阅读笔记
│   ├── langchain/                        #   LangChain V1.0
│   │   ├── 1-langchain-core/             #     langchain-core：runnables、messages、tools、prompts...
│   │   ├── 2-langchain/                  #     langchain：agent
│   │   └── 3-langgraph/                  #     langgraph：状态图、checkpoint、pregel
│   ├── deepagent/                        #   DeepAgent harness 架构
│   ├── AgentScope/                       #   AgentScope 多智能体框架
│   ├── deer-flow/                        #   Deer-flow
│   ├── OpenManus/                        #   OpenManus
│   └── youtu-agent/                      #   Youtu-agent（腾讯）
├── agent-system-design/                  # 智能体系统设计
│   ├── building-effective-agents/        #   Anthropic「Building Effective Agents」阅读笔记
│   ├── harness-engeneering/              #   Agent harness 工程化
│   ├── multi-agent-research-system/      #   多智能体研究系统架构
│   └── writing-effective-tools-for-agents/ # 为 Agent 设计高效工具
├── agent-system-paper/                   # 论文阅读
│   └── Is-Grep-All-You-Need/             #   Graph-based IR vs Grep 检索对比
├── agent-sys-asyncio/                    # Agent 系统异步 I/O
├── multi-agent-memory/                   # 记忆系统调研
│   ├── evermemos/                        #   Evermemos
│   ├── mem0/                             #   Mem0
│   └── Zep/                              #   Zep
├── llm-memory/                           # 记忆系统实践
│   └── evermind-practice/                #   EverMemOS 部署与实验
├── llm-rag/                              # RAG 方案验证
│   ├── ECOM1/                            #   BitGN 电商智能体基准赛
│   │   └── ecom-sample/                  #     可运行的 Python 示例
│   ├── RAG-Challenge-2/                  #   多策略 RAG 对比实验
│   │   ├── basic-rag/                    #     物理分块（baseline）
│   │   ├── graph-rag/                    #     图检索
│   │   ├── grep-rag/                     #     Grep 检索（Coding Agent 风格）
│   │   ├── ragflow/                      #     RAGFlow 深度布局解析
│   │   └── structural-rag/               #     Markdown 层级化拆分 + 父子检索
│   ├── RAG-Challenge-3/                  #   下一阶段 RAG 实验
│   └── RAG-Data/                         #   测试数据集
│       ├── IIya-rice/                    #     IIya-rice 文档集
│       └── RAG-Challlenge-dataset/       #     RAG Challenge 标准测试集
├── llm-lab/                              # 模型实验
│   ├── llm-base/                         #   基础模型实现
│   │   ├── transformer/                  #     Transformer（Attention Is All You Need）
│   │   ├── BERT-pytorch/                 #     BERT PyTorch 复现
│   │   └── NLP_textClassifier-master/    #     文本分类经典 baseline
│   ├── llm-sft/                          #   SFT 微调资源（数据集、训练配方）
│   └── llm-dpo/                          #   DPO 对齐资源
└── vibecoding-workshop/                  # Workshop 材料
```

---

## 主要模块说明

### 框架源码阅读笔记（multi-agent-framework/）

阅读主流智能体框架源码过程中的个人思考与记录，以 LangChain 为主：

- **1-langchain-core**：Runnable 协议、消息类型、工具接口、语言模型基类、序列化 —— 所有 LangChain 包的底层抽象
- **2-langchain**：上层 agent 封装（`create_agent` 等）
- **3-langgraph**：状态图、checkpoint、pregel 引擎 —— 编排层
- **deepagent**：harness 架构的三个核心分层（Backend / Middleware / Profiles）

### Anthropic「Building Effective Agents」阅读笔记（agent-system-design/）

详细拆解 Anthropic 多智能体研究系统的设计原则，包含作者本人的工程实践反思：

- Orchestrator 模式：Leader → Sub-agent 的任务分解与调度
- 搜索策略：Start wide, then narrow down
- 并行工具调用与 MapReduce 模式
- LangGraph Workflow 实现中的实际踩坑经验

### RAG 方案验证（llm-rag/）

在 `RAG-Challenge-2/` 和 `RAG-Challenge-3/` 中对比多种策略，围绕专业长文档（年报、财务报告）目标 ~80% 检索准确度：

| 策略 | 目录 | 方式 |
|------|------|------|
| Baseline | `basic-rag/` | 物理硬分块，不做语义分析 |
| Graph RAG | `graph-rag/` | 图检索 |
| Grep RAG | `grep-rag/` | 关键字命中，无向量库、无语义检索 |
| RAGFlow | `ragflow/` | DeepDoc 模型还原复杂 PDF 布局 |
| Structural RAG | `structural-rag/` | PDF → Markdown → 层级化切片 + 父子检索 |

同时包含 `ECOM1/` —— BitGN 电商运营智能体基准赛，含可运行 Python 示例。

### 模型实验（llm-lab/）

- **llm-base/transformer**：基于「Attention Is All You Need」的 PyTorch 完整实现
- **llm-base/BERT-pytorch**：Google AI 2018 BERT 的 PyTorch 复现
- **llm-base/NLP_textClassifier-master**：经典文本分类 baseline（textCNN、BiLSTM、Transformer 等）
- **llm-sft**：SFT 微调资源（数据集、训练配方）
- **llm-dpo**：DPO 对齐资源收集

### 记忆系统（llm-memory/、multi-agent-memory/）

- **evermind-practice/**：EverMemOS —— 四层类脑架构记忆操作系统（LoCoMo 基准 93% 准确率）
- **evermemos/**、**mem0/**、**Zep/**：记忆后端调研

---

*本仓库为个人学习用途，部分模块仍在持续补充中。*

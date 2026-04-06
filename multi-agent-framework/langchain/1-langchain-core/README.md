# LangChain-Core

> `langchain-core` 是整个 LangChain 所有的基本行为的抽象集合，定义了所有agent组件的调用标准协议，但是你让我用这玩意上工程，或许之前我会，但是现在就算了。
> 所有其他包（`langchain`、`langgraph`、`langchain-openai` 等）都依赖它，但它不依赖任何人。

---

## 📦 模块总览

```
langchain-core          ← 最底层，定义所有基础抽象
    │
    ├── callbacks           # 回调系统（追踪、日志、事件钩子）
    ├── documents           # Document 数据结构（RAG 的基础单元）
    ├── embeddings          # 嵌入模型接口（文本 → 向量）
    ├── example_selectors   # Few-shot 示例选择器
    ├── indexing            # 索引 API（文档去重、增量更新）
    ├── language_models     # 语言模型基类（BaseChatModel、BaseLLM）
    ├── load                # 序列化/反序列化（Serializable）
    ├── messages            # 消息类型（HumanMessage、AIMessage 等）
    ├── output_parsers      # 输出解析器（JSON、Pydantic 等）
    ├── outputs             # 模型输出结构（ChatResult、LLMResult）
    ├── prompts             # Prompt 模板（ChatPromptTemplate 等）
    ├── runnables      🌟   # Runnable 接口（核心中的核心）
    ├── tools               # 工具定义接口（BaseTool）
    ├── tracers             # 追踪器（LangSmith、Console）
    ├── utils               # 通用工具函数
    └── vectorstores        # 向量数据库接口
```

---
 
## 🌟 核心模块说明

### 1. `runnables` — langchain的基础组件

`Runnable` 是 LangChain 的核心接口。所有组件（Model、Tool、Prompt、Parser）都实现了这个协议，应是为了设计层面（尤其是langchain作为一个架构的开发方面）提供统一的调用方式：

| 方法 | 说明 |
| :--- | :--- |
| `invoke` / `ainvoke` | 单次调用 |
| `stream` / `astream` | 流式输出 |
| `batch` / `abatch` | 批量并发 |
| `|` 管道符 | 组合成 `RunnableSequence` |

> 📖 详细解析见 [runnable_part/README.md](./runnable_part/README.md)

### 2. `language_models` — 模型抽象

定义了 `BaseLanguageModel` → `BaseChatModel` 的继承链，所有 LLM 厂商的实现（OpenAI、Anthropic、Qwen 等）都必须继承此基类。

> 📖 详细解析见 [language_models_part/README.md](./language_models_part/README.md)

### 3. `load` — 序列化能力

`Serializable` 类让 LangChain 对象可以"存盘/读盘"，同时通过 `lc_secrets` 自动隐藏 API Key 等敏感信息。

### 4. `messages` — 消息协议

定义了 LLM 对话中的标准消息类型：

- `HumanMessage` — 用户输入
- `AIMessage` — 模型输出
- `SystemMessage` — 系统提示
- `ToolMessage` — 工具调用结果

### 5. `tools` — 工具接口

定义了 `BaseTool`，Agent 通过 `bind_tools()` 将工具绑定到模型上。

---

## 🏗️ 在 LangChain 生态中的位置

```
langchain-core              ← 基础协议
    │
    ├── langchain            ← 上层封装（create_agent 等）
    ├── langgraph            ← Agent 编排引擎（状态图）
    └── langchain-xxx        ← 各厂商集成（openai、anthropic...）
```
# DeepAgents 源码阅读文档框架

本目录只保留源码阅读框架，不填充完整解释。

## 本地源码

- 包名：`deepagents`
- 版本：`0.4.3`
- 源码位置：`.venv/Lib/site-packages/deepagents`

## 核心阅读主题

| 文档目录 | 源码范围 | 重点联动点 |
| --- | --- | --- |
| `agent-entry/` | `graph.py` | `create_deep_agent()` 如何装配 LangChain `create_agent()` |
| `backends/` | `backends/protocol.py`, `state.py`, `store.py`, `composite.py` | `ToolRuntime`, LangGraph state/store, backend factory |
| `middleware-stack/` | `middleware/*.py` | `AgentMiddleware`, `ToolRuntime`, `StructuredTool`, `Command`, `request.override(...)` |
| `subagents/` | `middleware/subagents.py` | 子 Agent 如何再次调用 LangChain `create_agent()` 或接入 `Runnable` |
| `summarization/` | `middleware/summarization.py` | LangChain summarization middleware 的复用与 DeepAgents 后端落盘 |

## 暂不单独建目录

- `backends/filesystem.py`, `local_shell.py`, `sandbox.py`：先归入 `backends/`。
- `middleware/memory.py`, `skills.py`, `patch_tool_calls.py`：先归入 `middleware-stack/`。
- `base_prompt.md`, `_utils.py`, `_version.py`：先不拆独立章节。

## 建议阅读顺序

1. `agent-entry/README.md`
2. `backends/README.md`
3. `middleware-stack/README.md`
4. `subagents/README.md`
5. `summarization/README.md`


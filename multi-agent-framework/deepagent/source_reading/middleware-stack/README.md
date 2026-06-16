# Middleware Stack

## 源码范围

- `.venv/Lib/site-packages/deepagents/middleware/__init__.py`
- `.venv/Lib/site-packages/deepagents/middleware/filesystem.py`
- `.venv/Lib/site-packages/deepagents/middleware/memory.py`
- `.venv/Lib/site-packages/deepagents/middleware/skills.py`
- `.venv/Lib/site-packages/deepagents/middleware/subagents.py`
- `.venv/Lib/site-packages/deepagents/middleware/summarization.py`
- `.venv/Lib/site-packages/deepagents/middleware/patch_tool_calls.py`

## 待读源码点

- [ ] 哪些类继承 `AgentMiddleware`
- [ ] 每个 middleware 是否定义 `state_schema`
- [ ] `before_agent` / `abefore_agent`
- [ ] `wrap_model_call` / `awrap_model_call`
- [ ] `wrap_tool_call` / `awrap_tool_call`
- [ ] 通过 `request.override(...)` 修改 system prompt 或 tools 的位置
- [ ] 通过 `StructuredTool.from_function(...)` 暴露工具的位置
- [ ] 通过 `Command(update=...)` 写回 LangGraph state 的位置

## Middleware 清单

| Middleware | 源码文件 | 重点 Hook | 待填充 |
| --- | --- | --- | --- |
| `FilesystemMiddleware` | `filesystem.py` | TODO | TODO |
| `MemoryMiddleware` | `memory.py` | TODO | TODO |
| `SkillsMiddleware` | `skills.py` | TODO | TODO |
| `SubAgentMiddleware` | `subagents.py` | TODO | TODO |
| `SummarizationMiddleware` | `summarization.py` | TODO | TODO |
| `PatchToolCallsMiddleware` | `patch_tool_calls.py` | TODO | TODO |

## LangChain / LangGraph 联动点

- [ ] `langchain.agents.middleware.types.AgentMiddleware`
- [ ] `langchain.agents.middleware.types.AgentState`
- [ ] `langchain.agents.middleware.types.ModelRequest`
- [ ] `langchain.agents.middleware.types.ModelResponse`
- [ ] `langchain.tools.ToolRuntime`
- [ ] `langchain_core.tools.StructuredTool`
- [ ] `langchain_core.messages.ToolMessage`
- [ ] `langgraph.types.Command`
- [ ] `langgraph.runtime.Runtime`

## 待填充笔记

### Middleware 执行顺序

TODO

### Prompt 注入

TODO

### Tool 注入与过滤

TODO

### State 写回

TODO


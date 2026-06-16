# Subagents

## 源码范围

- `.venv/Lib/site-packages/deepagents/middleware/subagents.py`
- `.venv/Lib/site-packages/deepagents/graph.py`

## 待读源码点

- [ ] `SubAgent` 与 `CompiledSubAgent` 的字段差异
- [ ] `GENERAL_PURPOSE_SUBAGENT` 的默认 spec
- [ ] `create_deep_agent()` 如何为 subagent 补齐默认 model/tools/middleware
- [ ] `SubAgentMiddleware` 如何创建 `task` 工具
- [ ] 子 Agent 何时调用 LangChain `create_agent(...)`
- [ ] 自定义 `Runnable` 子 Agent 的接入条件
- [ ] 子 Agent 返回结果如何变成 `ToolMessage` 或 `Command`
- [ ] 父子 Agent state 的传入、过滤和回写规则

## LangChain / LangGraph 联动点

- [ ] `langchain.agents.create_agent`
- [ ] `langchain.chat_models.init_chat_model`
- [ ] `langchain.tools.ToolRuntime`
- [ ] `langchain_core.runnables.Runnable`
- [ ] `langchain_core.tools.StructuredTool`
- [ ] `langchain_core.messages.HumanMessage`
- [ ] `langchain_core.messages.ToolMessage`
- [ ] `langgraph.types.Command`

## 待填充笔记

### Task 工具

TODO

### 子 Agent 编译路径

TODO

### 父子状态边界

TODO


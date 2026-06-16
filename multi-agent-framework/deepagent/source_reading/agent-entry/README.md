# Agent Entry

## 源码范围

- `.venv/Lib/site-packages/deepagents/graph.py`
- `.venv/Lib/site-packages/deepagents/__init__.py`

## 待读源码点

- [ ] `create_deep_agent()` 的参数面：`model`, `tools`, `middleware`, `subagents`, `skills`, `memory`, `backend`, `checkpointer`, `store`
- [ ] 默认模型：`get_default_model()` 与 `ChatAnthropic`
- [ ] 字符串模型初始化：`init_chat_model(...)`
- [ ] 默认 middleware stack 的组装顺序
- [ ] `system_prompt` 与 `BASE_AGENT_PROMPT` 的拼接方式
- [ ] 最终调用 `langchain.agents.create_agent(...)` 的参数传递
- [ ] `.with_config({"recursion_limit": 1000})` 的运行时意义

## LangChain / LangGraph 联动点

- [ ] `langchain.agents.create_agent`
- [ ] `langchain.agents.middleware.TodoListMiddleware`
- [ ] `langchain.agents.middleware.HumanInTheLoopMiddleware`
- [ ] `langchain.chat_models.init_chat_model`
- [ ] `langchain_core.language_models.BaseChatModel`
- [ ] `langchain_core.tools.BaseTool`
- [ ] `langgraph.types.Checkpointer`
- [ ] `langgraph.store.base.BaseStore`
- [ ] `langgraph.graph.state.CompiledStateGraph`

## 待填充笔记

### 入口职责

TODO

### 默认装配链路

TODO

### 和 LangChain `create_agent()` 的边界

TODO


# Backends

## 源码范围

首读：

- `.venv/Lib/site-packages/deepagents/backends/protocol.py`
- `.venv/Lib/site-packages/deepagents/backends/state.py`
- `.venv/Lib/site-packages/deepagents/backends/store.py`
- `.venv/Lib/site-packages/deepagents/backends/composite.py`

后读：

- `.venv/Lib/site-packages/deepagents/backends/filesystem.py`
- `.venv/Lib/site-packages/deepagents/backends/local_shell.py`
- `.venv/Lib/site-packages/deepagents/backends/sandbox.py`
- `.venv/Lib/site-packages/deepagents/backends/utils.py`

## 待读源码点

- [ ] `BackendProtocol` 的统一文件操作接口
- [ ] `BackendFactory = Callable[[ToolRuntime], BackendProtocol]`
- [ ] `StateBackend` 如何读取 `runtime.state`
- [ ] `StoreBackend` 如何读取 `runtime.store`
- [ ] `CompositeBackend` 如何路由不同 backend
- [ ] `SandboxBackendProtocol` 与 `execute` 工具的关系
- [ ] `WriteResult` / `EditResult` 中 `files_update` 如何交给 middleware 写回 LangGraph state

## LangChain / LangGraph 联动点

- [ ] `langchain.tools.ToolRuntime`
- [ ] LangGraph state
- [ ] LangGraph checkpointer
- [ ] `langgraph.store.base.BaseStore`
- [ ] `langgraph.config.get_config`

## 待填充笔记

### Backend 抽象边界

TODO

### StateBackend

TODO

### StoreBackend

TODO

### CompositeBackend

TODO


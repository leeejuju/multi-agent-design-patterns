# Summarization

## 源码范围

- `.venv/Lib/site-packages/deepagents/middleware/summarization.py`
- `.venv/Lib/site-packages/deepagents/graph.py`

## 待读源码点

- [ ] `SummarizationMiddleware` 和内部 `_DeepAgentsSummarizationMiddleware` 的关系
- [ ] 复用 LangChain `SummarizationMiddleware` 的位置
- [ ] `_compute_summarization_defaults(model)` 如何读取 model profile
- [ ] `wrap_model_call` / `awrap_model_call` 中触发 summarization 的条件
- [ ] conversation history 如何写入 backend
- [ ] `Command(update={"_summarization_event": ...})` 如何写回 state
- [ ] `ContextOverflowError` 的处理路径
- [ ] `thread_id` 如何从 LangGraph config 取出

## LangChain / LangGraph 联动点

- [ ] `langchain.agents.middleware.summarization.SummarizationMiddleware`
- [ ] `langchain.agents.middleware.summarization.ContextSize`
- [ ] `langchain.agents.middleware.types.ExtendedModelResponse`
- [ ] `langchain_core.messages.*`
- [ ] `langchain_core.messages.utils.count_tokens_approximately`
- [ ] `langchain_core.exceptions.ContextOverflowError`
- [ ] `langgraph.config.get_config`
- [ ] `langgraph.types.Command`

## 待填充笔记

### 默认策略

TODO

### 消息裁剪与摘要

TODO

### 历史落盘

TODO


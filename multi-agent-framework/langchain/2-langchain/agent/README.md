# agent

> [!NOTE]
> 从去年 10 月开始，LangChain 大改后，Agent 创建入口主要挪到了这里。这个方法特重要

| 参数名 | 类型 | 描述 |
| --- | --- | --- |
| model | `str \| BaseChatModel` | 模型本身 |
| tools | `Sequence[BaseTool \| Callable[..., Any] \| dict[str, Any]] \| None` | 初始化时传入的工具 |
| system_prompt | `str \| SystemMessage \| None` | sys的prompt |
| middleware | `Sequence[AgentMiddleware[StateT_co, ContextT]]` | 中间件，控制模型的toolcall，agent，modelcall 前后的行为，覆盖agent运行的整个周期，后续会详细说下，这个是特别重要的改动 |
| response_format | `ResponseFormat[ResponseT] \| type[ResponseT] \| dict[str, Any] \| None` |  |
| state_schema | `type[AgentState[ResponseT]] \| None` |  |
| context_schema | `type[ContextT] \| None` |  |
| checkpointer | `Checkpointer \| None` |  |
| store | `BaseStore \| None` |  |
| interrupt_before | `list[str] \| None` |  |
| interrupt_after | `list[str] \| None` |  |
| debug | `bool` |  |
| name | `str \| None` |  |
| cache | `BaseCache[Any] \| None` |  |

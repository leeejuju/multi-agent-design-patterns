# langchain.agent
> [!NOTE]
> 从去年 10 月开始，LangChain 大改后，Agent 创建入口主要挪到了这里。这个方法特重要

## factory

agent 创建的工程方法，有以下参数，特别重要的一点，从25年大改后，agent 底层走的是 graph 的那一套了
超级重大的革新（但是以前走哪我也不知道哈哈哈哈哈哈哈哈，不想看以前的老代码了）



| 参数名 | 类型 | 描述 |
| --- | --- | --- |
| model | `str \| BaseChatModel` | 模型本身 |
| tools | `Sequence[BaseTool \| Callable[..., Any] \| dict[str, Any]] \| None` | 初始化时传入的工具 |
| system_prompt | `str \| SystemMessage \| None` | sys的prompt |
| middleware | `Sequence[AgentMiddleware[StateT_co, ContextT]]` | 中间件，控制模型的toolcall，agent，modelcall 前后的行为，覆盖agent运行的整个周期，后续会详细说下，这个是特别重要的改动 |
| response_format | `ResponseFormat[ResponseT] \| type[ResponseT] \| dict[str, Any] \| None` | 模型的返回类型 |
| state_schema | `type[AgentState[ResponseT]] \| None` | Agent runtime 的state 参数|
| context_schema | `type[ContextT] \| None` | 一些额外的上席文参数 |
| checkpointer | `Checkpointer \| None` | memory langchain 管理记忆的核心内容，非常种重要  |
| store | `BaseStore \| None` | langchain 管理记忆的核心内容，非常种重要|
| interrupt_before | `list[str] \| None` | HIL的打断参数或者一些前后操作可用的，类似 AOP |
| interrupt_after | `list[str] \| None` | 同上 |
| debug | `bool` |  |
| name | `str \| None` | 给graph起别名 |
| cache | `BaseCache[Any] \| None` | 顾名思义，不过是给图的执行结果存的cache，类似 lru |


初始化模型的时候其实，就 init_chat_model 方法就不往下层说了，主要有两个是比较，emm..., 工程上比较重要的

即    
configurable_fields: Literal["any"] | list[str] | tuple[str, ...] | None = None,
config_prefix: str | None = None,

字面意思，可配置/可变的模型变量的以及可配置的模型的前缀，
原文是
configurable_fields：Which model parameters are configurable at runtime:
config_prefix：Useful when you have multiple configurable models in the same application.

这就有意思了，模型运行时参数的可变以及给模型上别名，会有非常大的可玩空间

举例来说，你在用 A 模型的时候，欠费/宕机/不想用了，不同任务的场景需要不同价格/类型的模型

又或者 search tool 的并发场景，需要 flash 模型思考快速总结，

简单的总结需要用到小模型

那么就可以用这种方式切换了，但是有一点，agent 更新之后有了 Middleware 其实可以在这里通过request override 重写当前用的模型，我觉得这个更方便一点。

config_prefix就更不用说了，有了前缀，不同角色的 Agent 以及 任务，可通过前缀的不同，使用指定模型去处理任务就是了。


## structured_output

规定了结构化输出的一堆格式 AutoStrategy 、 ProviderStrategy、 ToolStrategy
主要是用于 responseFormat = True 时的输出策略，


AutoStrategy 选择最优的 respone strategy 具体会在后续的代码中判断

ToolStrategy 

ProviderStrategy 各大厂商自己的模型纯支持输出结构化的结果









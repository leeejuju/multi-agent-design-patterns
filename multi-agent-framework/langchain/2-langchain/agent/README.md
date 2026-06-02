# LangChain Agent Factory 与 Middleware

> [!NOTE]
> 从 2025 年 10 月开始，LangChain 大改后，Agent 创建入口主要挪到了这里。这个方法很重要。

## factory

agent 创建的工厂方法，有以下参数。特别重要的一点是，从 2025 年大改后，agent 底层走的是 graph 那一套。

要记住底层走 Graph 这一点。它后续的执行，以及整个 Agent 行为的构成，都是依照 LangGraph 的原则去设计的。

| 参数名 | 类型 | 描述 |
| --- | --- | --- |
| model | `str \| BaseChatModel` | 模型本身 |
| tools | `Sequence[BaseTool \| Callable[..., Any] \| dict[str, Any]] \| None` | 初始化时传入的工具 |
| system_prompt | `str \| SystemMessage \| None` | sys 的 prompt |
| middleware | `Sequence[AgentMiddleware[StateT_co, ContextT]]` | 中间件，控制模型的 tool call、agent、model call 前后的行为，是很重要的改动 |
| response_format | `ResponseFormat[ResponseT] \| type[ResponseT] \| dict[str, Any] \| None` | 模型的返回类型 |
| state_schema | `type[AgentState[ResponseT]] \| None` | Agent runtime 的 state 参数 |
| context_schema | `type[ContextT] \| None` | 一些额外的上下文参数 |
| checkpointer | `Checkpointer \| None` | memory，LangChain 管理记忆的核心内容 |
| store | `BaseStore \| None` | LangChain 管理记忆的核心内容 |
| interrupt_before | `list[str] \| None` | HIL 的打断参数，或者一些前后操作可用的，类似 AOP |
| interrupt_after | `list[str] \| None` | 同上 |
| debug | `bool` |  |
| name | `str \| None` | 给 graph 起别名 |
| cache | `BaseCache[Any] \| None` | 给图的执行结果存 cache，类似 lru |

## create_agent 初始化流程

create_agent 初始化的时候经历了这样的流程：

1. 初始化模型。初始化模型的时候用到了 init_chat_model。一般用 LangChain 时，更多情况下是直接把模型塞进去，这也是最简单的初始化方式。
2. 合并消息 input。
3. 合并 System Prompt。初始化带入的时候，它会直接使用 LangChain 专属的 BaseMessage 继承的 SystemMessage 进行转换。
4. 处理 Structured Output。

LangChain 本身规定了三种方式：

1. tool strategy
2. auto strategy
3. provider strategy

这三种 strategy 都是针对 response_format 这个参数进行构建的，目的就是迫使模型输出 Structured 的格式。

然后就是 Middleware 的定义。

Middleware 是 LangChain 在 2025 年 10 月大改版以后一个特别重要的特性。它把模型的前后处理、Agent 的执行前后、Tool 的执行前后，以及 Model 周期内可能发生的一些行为进行了封装。它的行为有点像 Java 里的 AOP。

它囊括的几个方法包括：

1. before agent
2. after agent
3. before model
4. after model
5. wrap model call
6. wrap tool call

这几个方法都比较顾名思义，但是具体怎么串联需要看 factory 里的编排逻辑。

之前看文档时，我以为 Middleware 里面的行为是按一个 middleware 一个 middleware 执行的。后来发现它其实更像 Hook：

1. 所有 before 行为：把 Middleware 里面所有的 before 行为通过for循环串到一起，然后顺序执行。
2. 所有 after 行为：同样串到一起，然后执行。
3. wrap 行为：会组合成 wrapper stack，包住对应的 model call 或 tool call。



def _chain_async_tool_call_wrappers(
    wrappers: Sequence[
        Callable[
            [ToolCallRequest, Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]]],
            Awaitable[ToolMessage | Command[Any]],
        ]
    ],
) -> (
    Callable[
        [ToolCallRequest, Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]]],
        Awaitable[ToolMessage | Command[Any]],
    ]
    | None
):
    """Compose async wrappers into middleware stack (first = outermost).

    Args:
        wrappers: Async wrappers in middleware order.

    Returns:
        Composed async wrapper, or `None` if empty.
    """
    if not wrappers:
        return None

    if len(wrappers) == 1:
        return wrappers[0]

    def compose_two(
        outer: Callable[
            [ToolCallRequest, Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]]],
            Awaitable[ToolMessage | Command[Any]],
        ],
        inner: Callable[
            [ToolCallRequest, Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]]],
            Awaitable[ToolMessage | Command[Any]],
        ],
    ) -> Callable[
        [ToolCallRequest, Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]]],
        Awaitable[ToolMessage | Command[Any]],
    ]:
        """Compose two async wrappers where outer wraps inner."""

        async def composed(
            request: ToolCallRequest,
            execute: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
        ) -> ToolMessage | Command[Any]:
            # Create an async callable that invokes inner with the original execute
            async def call_inner(req: ToolCallRequest) -> ToolMessage | Command[Any]:
                return await inner(req, execute)

            # Outer can call call_inner multiple times
            return await outer(request, call_inner)

        return composed


  # Chain all wrappers: first -> second -> ... -> last
    result = wrappers[-1]
    for wrapper in reversed(wrappers[:-1]):
        result = compose_two(wrapper, result)

    return result
这里介绍一个比较有特点的方法，就是我之前提过的“倒序执行”。

因为在 Python 中异步方法更常用，所以我这里全程只看异步（Async）的方法。你可以观察一下它 compose 后 Agent 的 wrap_to_call 执行顺序。当你拥有多个中间件（Middleware）时，比如书写顺序是 A Middleware、B Middleware 和 C Middleware，在 for 循环加载时，它们是按顺序读取进去的。

但实际执行时，你需要从最内层进行反向执行。为了实现这一点，它采取了一个比较讨巧的方法，在代码中称之为 `chain_all_wrappers`：

1. 倒序提取：它通过逆序的方式，首先将最后一个 Middleware 拿出来。因为最内层的 wrap_to_call 方法应该是最先被执行的。
2. 链式入参：执行时，B Middleware 的 wrap_to_call 会将 C Middleware 执行的结果作为入参。
3. 迭代融合：它利用 `result = wrappers[-1]` 这种逻辑，将整个序列倒过来进行迭代，并使用 `compose_two` 方法将它们融合在一起。

最终，这个过程会返回一个包含了完整执行顺序的套娃函数体
具体看这里：  # Chain all wrappers: first -> second -> ... -> last
    result = wrappers[-1]
    for wrapper in reversed(wrappers[:-1]):
        result = compose_two(wrapper, result)








其它的 init_chat_model 方法下又提供了几个参数，主要有两个工程上比较重要：

```python
configurable_fields: Literal["any"] | list[str] | tuple[str, ...] | None = None
config_prefix: str | None = None
```

字面意思就是：可配置/可变的模型变量，以及可配置模型的前缀。

原文是：

```text
configurable_fields: Which model parameters are configurable at runtime.
config_prefix: Useful when you have multiple configurable models in the same application.
```

模型运行时参数的可变，以及给模型上别名，会有很大的可玩空间。比如 A 模型欠费、宕机、不想用了，或者不同任务需要不同价格/类型的模型，就可以通过这种方式切换。

不过 agent 更新之后有了 Middleware，也可以通过 request override 重写当前用的模型，我觉得这个更方便一点。

config_prefix 就更不用说了。有了前缀，不同角色的 Agent 以及不同任务，可以通过前缀使用指定模型去处理。

## structured_output

规定了结构化输出的一堆格式：AutoStrategy、ProviderStrategy、ToolStrategy。

主要是用于 response_format 的输出策略。

AutoStrategy 选择最优的 response strategy，具体会在后续的代码中判断。

ToolStrategy 官方是这样说的：

> For models that don’t support native structured output, LangChain uses tool calling to achieve the same result. This works with all models that support tool calling.

对于原生不支持结构化输出的模型，LangChain 会把这部分内容封装成 Tool Calling 的形式，去实现稳定的结构化 Response 效果。

ProviderStrategy 是各大厂商自己的模型原生支持输出结构化结果。

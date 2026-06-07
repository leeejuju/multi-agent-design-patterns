# LangChain Agent Factory 与 Middleware

> [!NOTE]
> 从 2025 年 10 月开始，LangChain 大改后，Agent 创建入口主要挪到了这里。这个方法很重要。

## Factory

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

## init_chat_model

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

LangChain 本身规定了三种方式：

1. tool strategy
2. auto strategy
3. provider strategy

这三种 strategy 都是针对 response_format 这个参数进行构建的，目的就是迫使模型输出 Structured 的格式。

## Middleware 定义

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

## wrap tool call 的组合

```python
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
```

这里介绍一个比较有特点的方法，就是我之前提过的“倒序执行”。

因为在 Python 中异步方法更常用，所以我这里全程只看异步（Async）的方法。你可以观察一下它 compose 后 Agent 的 wrap_to_call 执行顺序。当你拥有多个中间件（Middleware）时，比如书写顺序是 A Middleware、B Middleware 和 C Middleware，在 for 循环加载时，它们是按顺序读取进去的。

但实际执行时，你需要从最内层进行反向执行。为了实现这一点，它采取了一个比较讨巧的方法，在代码中称之为 `chain_all_wrappers`：

1. 倒序提取：它通过逆序的方式，首先将最后一个 Middleware 拿出来。因为最内层的 wrap_to_call 方法应该是最先被执行的。
2. 链式入参：执行时，B Middleware 的 wrap_to_call 会将 C Middleware 执行的结果作为入参。
3. 迭代融合：它利用 `result = wrappers[-1]` 这种逻辑，将整个序列倒过来进行迭代，并使用 `compose_two` 方法将它们融合在一起。

最终，这个过程会返回一个包含了完整执行顺序的套娃函数体 类似 A(B(C(kwargs)))

具体看这里：

```python
# Chain all wrappers: first -> second -> ... -> last
result = wrappers[-1]
for wrapper in reversed(wrappers[:-1]):
    result = compose_two(wrapper, result)
```

compose two的两个参数都是具体的 awarp_tool_call的

## before/after agent/model 的抽取

```python
# before/after agent/model
middleware_w_before_agent = [
    m
    for m in middleware
    if m.__class__.before_agent is not AgentMiddleware.before_agent
    or m.__class__.abefore_agent is not AgentMiddleware.abefore_agent
]
middleware_w_before_model = [
    m
    for m in middleware
    if m.__class__.before_model is not AgentMiddleware.before_model
    or m.__class__.abefore_model is not AgentMiddleware.abefore_model
]
middleware_w_after_model = [
    m
    for m in middleware
    if m.__class__.after_model is not AgentMiddleware.after_model
    or m.__class__.aafter_model is not AgentMiddleware.aafter_model
]
middleware_w_after_agent = [
    m
    for m in middleware
    if m.__class__.after_agent is not AgentMiddleware.after_agent
    or m.__class__.aafter_agent is not AgentMiddleware.aafter_agent
]
```

ps: 这下子我就想起来了，之前看到的所谓 middleware 执行的顺序问题，是先顺序后倒序出处是那里了，不过有偏差罢了

## wrap model call 的抽取

```python
if middleware_w_awrap_model_call:
    async_handlers = [
        traceable(name=f"{m.name}.awrap_model_call", process_inputs=_scrub_inputs)(
            m.awrap_model_call
        )
        for m in middleware_w_awrap_model_call
    ]
    awrap_model_call_handler = _chain_async_model_call_handlers(async_handlers)
```

model call 和 toolcall由于贯穿他们各自的执行周期，所以也是单独抽取出来的

## state 抽取

和tool一致，从当前的agent 抽取工具后遍历中间件抽取所有的内容

```python
state_schemas: set[type] = {m.state_schema for m in middleware}
# Use provided state_schema if available, otherwise use base AgentState
base_state = state_schema if state_schema is not None else AgentState
state_schemas.add(base_state)
```

## Graph 初始化

完事以上准备好了以后

```python
graph: StateGraph[
    AgentState[ResponseT], ContextT, _InputAgentState, _OutputAgentState[ResponseT]
] = StateGraph(
    state_schema=resolved_state_schema,
    input_schema=input_schema,
    output_schema=output_schema,
    context_schema=context_schema,
)
```

直接就将所有的状态打包好开始构造初始的图

## Graph 边构造

从 factory.py 的 line 1365~1646 开始，都属于 langgraph 的 edge 构造

把 middleware 的行为（before,after 那一套行为）都挂载成了边

但是每个边是怎么安排的呢？并不是那么随意的，在很久之前，我刚刚接触 langgraph 这一套内容的时候

会存在好几个点，condition_edage, tool_edage 等等，但是复杂 agent loop/harness 的场景，编排会如何？？

整个图如何编排的

其实一般你看官方编排

```text
# TODO 此处填图
```

比较符合惯性的思维

他的 middleware 中，执行顺序是：before_agent -> before_model -> model

行为是这样编排的，遍历出所有的 before/after, agent/model 后，挂上各自的 middleware 下的节点

值得注意的一点是，他设置的 entry/exit node，以及 loop 的 entry/exit

他 entry 的顺序是这样的, 按照一般的 agent 执行逻辑触发

agent 作为 model 的前置行为，会率先作为入口。

## Loop and Tool (循环机制)

对于 langchain 来说，其设计的是基于 loop 的循环

其次是 tool 环节，无论是 harness 或者 agent 的 tool 实现多次循环调用是基操

但是话又说回来，有的工具本身就是结果，不用反复迭代

于是 langchain 在 BaseTool 类规定了 return_direct 参数

True 时直接返回结果后，直接进入 END or after_agent 环节（ after agent 也是 model 执行后的一个环节）

langchain 在设计时提供几套条件路径，

tool 的 edage 走向给出了条件分支 after_agent, model， END， 条件就是以上的内容

loop-exit 则的走向三个节点，分别是：

1. tools
3. exit_node ( after_agent，END )

其中 exit_node 本身也是指向 after_agent，END 这两个环节

LoopX 那个给了一个判断条件，就是 _make_model_to_model_edge 。他这里面搞了好几个逻辑：

1. Jump 逻辑

   如果有指定的 jump_to 目的地，它会直接跳往该目的地，并附带上之前的参数。

2. 消息处理判断

   如果没有 jump 任务，它会再找是否有 AI 消息（AIMessage）和 ToolMessage，判断这两个消息是否已经处理完。

3. 结束节点跳转

   如果没有 AI 消息，则直接跳往结束（END）节点。END 地方包括两个：一个是 END，一个是 after_agent。

4. Pending to Call 状态

   系统会继续判断是否存在 pending_to_call。所谓 pending_to_call，就是工具存在但没有被调用，也没有生成结果。这种情况下，需要再次将工具发送到 tools 节点去执行。

如果已经有了 structured_response（即有明确的结束内容），系统就会直接 END 状态。

我首先会说一下，为什么在 loop 的时候会再次往 tools 上面走。

1. tools 的执行过程可能会报错，你不能保证它百分之百成功。
2. tools 本身可能没有收集到足够的信息。
3. 上层的（比如 Agent As Tool 的 Agent 下属 Tool 在收集到信息后，经由 Agent 判定该信息尚未收集完整，没有完全满足条件。因为信息不够，所以它会再次跳回到 Tool 节点。

这是因为 tools 本身并不只是指某一个具体的工具，同时因为 Agent 也可以作为 tool 存在，所以这是一个比较复杂的情况。

## structured output tool 的分支

以上说的是有 Tool 节点的情况。它后边又分了几个不同的状态：

```python
elif len(structured_output_tools) > 0:
    graph.add_conditional_edges(
        loop_exit_node,
        RunnableCallable(
            _make_model_to_model_edge(
                model_destination=loop_entry_node,
                end_destination=exit_node,
            ),
            trace=False,
        ),
        [loop_entry_node, exit_node],
    )
```

主要这个问题在于，他可能没有给 agent 提供工具，但我又规定了需要一些结构化的输出格式，所以他就这样规定了一下

当 Agent 没有赋给 Agent tool 的时候，他就直接去走 Middleware 的底层流程

## before agent / before model 的边

```python
else:
    _add_middleware_edge(
        graph,
        name=f"{middleware_w_after_model[0].name}.after_model",
        default_destination=exit_node,
        model_destination=loop_entry_node,
        end_destination=exit_node,
        can_jump_to=_get_can_jump_to(middleware_w_after_model[0], "after_model"),
    )

# Add before_agent middleware edges
if middleware_w_before_agent:
    for m1, m2 in itertools.pairwise(middleware_w_before_agent):
        _add_middleware_edge(
            graph,
            name=f"{m1.name}.before_agent",
            default_destination=f"{m2.name}.before_agent",
            model_destination=loop_entry_node,
            end_destination=exit_node,
            can_jump_to=_get_can_jump_to(m1, "before_agent"),
        )
    # Connect last before_agent to loop_entry_node (before_model or model)
    _add_middleware_edge(
        graph,
        name=f"{middleware_w_before_agent[-1].name}.before_agent",
        default_destination=loop_entry_node,
        model_destination=loop_entry_node,
        end_destination=exit_node,
        can_jump_to=_get_can_jump_to(middleware_w_before_agent[-1], "before_agent"),
    )

# Add before_model middleware edges
if middleware_w_before_model:
    for m1, m2 in itertools.pairwise(middleware_w_before_model):
        _add_middleware_edge(
            graph,
            name=f"{m1.name}.before_model",
            default_destination=f"{m2.name}.before_model",
            model_destination=loop_entry_node,
            end_destination=exit_node,
            can_jump_to=_get_can_jump_to(m1, "before_model"),
        )
    # Go directly to model after the last before_model
    _add_middleware_edge(
        graph,
        name=f"{middleware_w_before_model[-1].name}.before_model",
        default_destination="model",
        model_destination=loop_entry_node,
        end_destination=exit_node,
        can_jump_to=_get_can_jump_to(middleware_w_before_model[-1], "before_model"),
    )
```

以上则是，串联 before-agent , before-model的各边

通过 pairwise 的由 A 的组件执行完毕后 导向 B ， 后续依次类推, 构成了 graph 的中间件执行链路

由于操作一致，不在详述

## after model / after agent 的边

```python
# Add after_model middleware edges
if middleware_w_after_model:
    graph.add_edge("model", f"{middleware_w_after_model[-1].name}.after_model")
    for idx in range(len(middleware_w_after_model) - 1, 0, -1):
        m1 = middleware_w_after_model[idx]
        m2 = middleware_w_after_model[idx - 1]
        _add_middleware_edge(
            graph,
            name=f"{m1.name}.after_model",
            default_destination=f"{m2.name}.after_model",
            model_destination=loop_entry_node,
            end_destination=exit_node,
            can_jump_to=_get_can_jump_to(m1, "after_model"),
        )
    # Note: Connection from after_model to after_agent/END is handled above
    # in the conditional edges section

# Add after_agent middleware edges
if middleware_w_after_agent:
    # Chain after_agent middleware (runs once at the very end, before END)
    for idx in range(len(middleware_w_after_agent) - 1, 0, -1):
        m1 = middleware_w_after_agent[idx]
        m2 = middleware_w_after_agent[idx - 1]
        _add_middleware_edge(
            graph,
            name=f"{m1.name}.after_agent",
            default_destination=f"{m2.name}.after_agent",
            model_destination=loop_entry_node,
            end_destination=exit_node,
            can_jump_to=_get_can_jump_to(m1, "after_agent"),
        )

    # Connect the last after_agent to END
    _add_middleware_edge(
        graph,
        name=f"{middleware_w_after_agent[0].name}.after_agent",
        default_destination=END,
        model_destination=loop_entry_node,
        end_destination=exit_node,
        can_jump_to=_get_can_jump_to(middleware_w_after_agent[0], "after_agent"),
    )
```

这里就是之前提过的倒排序执行

前置的执行顺序是 before-agent -> before-model -> model -> after-model -> after-agent -> END (如果没有循环的话)

因为他设计 after系的执行的时候

```python
for idx in range(len(middleware_w_after_model) - 1, 0, -1):
```

逆向进行

## 总结

至此以上，关于 LangChain Create Agent 的 Factory 这个函数重要的地方基本就这些，

以上全部内容都是手打的代码，我会配合 Typeless  口述，并使用 Codex 来整理内容的排版。

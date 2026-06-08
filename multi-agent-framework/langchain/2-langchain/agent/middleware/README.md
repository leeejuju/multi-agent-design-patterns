# Agent Middleware

已经说了 create agent 的构建以后，下面是他 builtin 的 middleware,

| 文件名 | 功能 | 目的 |
| :--- | :--- | :--- |
| **human_in_the_loop.py** | 提供人工审批介入流程，拦截并挂起敏感工具调用，支持人工批准、修改或拒绝。 | 保证敏感/高危操作（如转账、写操作）的安全控制。 |
| **model_call_limit.py** | 监控并限制大模型在单次运行或单个会话中的调用次数。 | 防止 Agent 因规划错误陷入自我纠错的死循环，控制 Token 成本。 |
| **model_retry.py** | 自动重试因限流、超时等网络波动而失败的大模型请求。 | 提高大模型 API 调用的鲁棒性与网络健壮性。 |
| **model_fallback.py** | 当主模型调用持续报错时，按顺序自动降级切换至备用大模型。 | 保证模型层的高可用性和容错能力。 |
| **summarization.py** | 自动在 Token 数量超限时对较早的历史消息进行摘要式压缩并替换。 | 优化上下文窗口占用，控制长会话下的计算与输入 Token 成本。 |
| **pii.py** | 检测并遮蔽（Mask）或哈希（Hash）输入输出中的敏感个人隐私数据。 | 满足安全审计与合规要求，防止用户隐私数据泄漏给外部大模型。 |
| **shell_tool.py** | 绑定持续终端会话工具，并提供 Host、Docker 等执行环境策略。 | 隔离并安全运行大模型生成的代码，避免破坏宿主机。 |
| **tool_call_limit.py** | 监控并限制特定工具或全部工具的累计调用次数。 | 拦截频繁多余的工具调用，避免资源浪费和陷入死循环。 |
| **tool_retry.py** | 对发生瞬时异常的工具调用进行指数退避式自动重试。 | 提高外部 API 工具和三方依赖接口调用的可靠性。 |
| **context_editing.py** | 对超出 token 界限的历史会话进行过滤并将其替换为 placeholder。 | 快速裁切过往冗余的详细工具结果，精简上下文。 |
| **tool_selection.py** | 利用轻量路由模型干预、改写或过滤大模型选择的工具。 | 在模型与工具之间增加一层动态决策路由，控制工具调用流。 |
| **tool_emulator.py** | 使用大模型模拟（仿真）工具的返回结果。 | 供自动化测试和 Dry-run 运行时脱离外部 API 执行评估。 |
| **todo.py** | 提供任务进度待办清单工具，将目标任务分解为 pending、in_progress 和 completed 状态。 | 使模型能保持长序列复杂任务的执行规划和状态可见度。 |
| **file_search.py** | 提供文件系统的 Glob 和 Grep 检索工具。 | 帮助 Agent 能够更加快速精准地定位和读取文件内容。 |


先按下不表，主要是看他的功能设计是怎么做的，在什么节点开始/结束，为什么要放在这个节点开始/结束，能不能放到其他节点开始/结束

针对不同业务该怎么设计自己的？

# 1. type.py (这里规定了 Middlewara 的一堆 meta 设计, 并且提供了已经内置其中的 agent/model 行为注解，方便)

这里提供注解是为了方便那些只需要用到单个be/af agent/model周期的行为但是不需要全套的情况

这里直接看一个就行了，逻辑是一样的

```
def before_agent(
    func: _CallableWithStateAndRuntime[StateT, ContextT] | None = None,
    *,
    state_schema: type[StateT] | None = None,
    tools: list[BaseTool] | None = None,
    can_jump_to: list[JumpTo] | None = None,
    name: str | None = None,
) -> (
    Callable[[_CallableWithStateAndRuntime[StateT, ContextT]], AgentMiddleware[StateT, ContextT]]
    | AgentMiddleware[StateT, ContextT]
):
    """Decorator used to dynamically create a middleware with the `before_agent` hook.

    Args:
        func: The function to be decorated.

            Must accept: `state: StateT, runtime: Runtime[ContextT]` - State and runtime
            context
        state_schema: Optional custom state schema type.

            If not provided, uses the default `AgentState` schema.
        tools: Optional list of additional tools to register with this middleware.
        can_jump_to: Optional list of valid jump destinations for conditional edges.

            Valid values are: `'tools'`, `'model'`, `'end'`
        name: Optional name for the generated middleware class.

            If not provided, uses the decorated function's name.

    Returns:
        Either an `AgentMiddleware` instance (if func is provided directly) or a
            decorator function that can be applied to a function it is wrapping.

    The decorated function should return:

    - `dict[str, Any]` - State updates to merge into the agent state
    - `Command` - A command to control flow (e.g., jump to different node)
    - `None` - No state updates or flow control

    Examples:
        !!! example "Basic usage"

            ```python
            @before_agent
            def log_before_agent(state: AgentState, runtime: Runtime) -> None:
                print(f"Starting agent with {len(state['messages'])} messages")
            ```

        !!! example "With conditional jumping"

            ```python
            @before_agent(can_jump_to=["end"])
            def conditional_before_agent(
                state: AgentState, runtime: Runtime
            ) -> dict[str, Any] | None:
                if some_condition(state):
                    return {"jump_to": "end"}
                return None
            ```

        !!! example "With custom state schema"

            ```python
            @before_agent(state_schema=MyCustomState)
            def custom_before_agent(state: MyCustomState, runtime: Runtime) -> dict[str, Any]:
                return {"custom_field": "initialized_value"}
            ```

        !!! example "Streaming custom events"

            Use `runtime.stream_writer` to emit custom events during agent execution.
            Events are received when streaming with `stream_mode="custom"`.

            ```python
            from langchain.agents import create_agent
            from langchain.agents.middleware import before_agent, AgentState
            from langchain.messages import HumanMessage
            from langgraph.runtime import Runtime


            @before_agent
            async def notify_start(state: AgentState, runtime: Runtime) -> None:
                '''Notify user that agent is starting.'''
                runtime.stream_writer(
                    {
                        "type": "status",
                        "message": "Initializing agent session...",
                    }
                )
                # Perform prerequisite tasks here
                runtime.stream_writer({"type": "status", "message": "Agent ready!"})


            agent = create_agent(
                model="openai:gpt-5.2",
                tools=[...],
                middleware=[notify_start],
            )

            # Consume with stream_mode="custom" to receive events
            async for mode, event in agent.astream(
                {"messages": [HumanMessage("Hello")]},
                stream_mode=["updates", "custom"],
            ):
                if mode == "custom":
                    print(f"Status: {event}")
            ```
    """

    def decorator(
        func: _CallableWithStateAndRuntime[StateT, ContextT],
    ) -> AgentMiddleware[StateT, ContextT]:
        is_async = iscoroutinefunction(func)

        func_can_jump_to = (
            can_jump_to if can_jump_to is not None else getattr(func, "__can_jump_to__", [])
        )

        if is_async:

            async def async_wrapped(
                _self: AgentMiddleware[StateT, ContextT],
                state: StateT,
                runtime: Runtime[ContextT],
            ) -> dict[str, Any] | Command[Any] | None:
                return await func(state, runtime)  # type: ignore[misc]

            # Preserve can_jump_to metadata on the wrapped function
            if func_can_jump_to:
                async_wrapped.__can_jump_to__ = func_can_jump_to  # type: ignore[attr-defined]

            middleware_name = name or cast(
                "str", getattr(func, "__name__", "BeforeAgentMiddleware")
            )

            return type(
                middleware_name,
                (AgentMiddleware,),
                {
                    "state_schema": state_schema or AgentState,
                    "tools": tools or [],
                    "abefore_agent": async_wrapped,
                },
            )()

        def wrapped(
            _self: AgentMiddleware[StateT, ContextT],
            state: StateT,
            runtime: Runtime[ContextT],
        ) -> dict[str, Any] | Command[Any] | None:
            return func(state, runtime)  # type: ignore[return-value]

        # Preserve can_jump_to metadata on the wrapped function
        if func_can_jump_to:
            wrapped.__can_jump_to__ = func_can_jump_to  # type: ignore[attr-defined]

        # Use function name as default if no name provided
        middleware_name = name or cast("str", getattr(func, "__name__", "BeforeAgentMiddleware"))

        return type(
            middleware_name,
            (AgentMiddleware,),
            {
                "state_schema": state_schema or AgentState,
                "tools": tools or [],
                "before_agent": wrapped,
            },
        )()

    if func is not None:
        return decorator(func)
    return decorator

```

他会在你使用单注解的时候，用 func name 创建一个， 方便调试估计

## ModelRequest （model call 期间的重要参数， 具体就 warp_model_call ）
Model request information for the agent.

该函数实例化位于 graph invoke 的时候， 需要注意的只有 override 的时候， sys_msg 和 sys_prompt 不可以同时存在
也是为了放置语义的不清吧


## ModelResponse 同理， 依旧只是存在于 wrap_model_call 的返回期间

## type 核心就是这些了


# 2. HIL.py 人在回路，说这个主要是涉及到任务的 interupt 和 resume.

![HIL example](../image/HIL_eg.png)


人在回路中间件，规定了一系列断点。



cc 和 codex 让你 yes 的就是 HIL 

我在想一个问题，比如 claude , chatgpt 的 web 端 和 cc的逻辑估计是一样的

cc 里是这么搞的


···
···

HumanInTheLoopMiddleware 提供了一个 interrupt_on 参数， 类型是 dict[str, bool] 以及 dict[str, InterruptOnConfig]

对于需要被拦截的工具，提供了三个选项 approve, edit, reject， InterruptOnConfig 稍微不一样，组成也是 allowed_decisions，和 descprtion

组合完后完成后，就形成了 HIL 中间件

同时 HIL 规定的了两个封装，ActionRequest， ReviewConfig，本别代表执行的函数参数以及需要review，审批的类型

那到解析的后就形成了HIL的执行链路

那么要问了，最核心的打断是怎么实现的

## interrupt
···
def interrupt(value: Any) -> Any:
    """Interrupt the graph with a resumable exception from within a node.

    The `interrupt` function enables human-in-the-loop workflows by pausing graph
    execution and surfacing a value to the client. This value can communicate context
    or request input required to resume execution.

    In a given node, the first invocation of this function raises a `GraphInterrupt`
    exception, halting execution. The provided `value` is included with the exception
    and sent to the client executing the graph.

    A client resuming the graph must use the [`Command`][langgraph.types.Command]
    primitive to specify a value for the interrupt and continue execution.
    The graph resumes from the start of the node, **re-executing** all logic.

    If a node contains multiple `interrupt` calls, LangGraph matches resume values
    to interrupts based on their order in the node. This list of resume values
    is scoped to the specific task executing the node and is not shared across tasks.

    To use an `interrupt`, you must enable a checkpointer, as the feature relies
    on persisting the graph state.

    !!! example

        ```python
        import uuid
        from typing import Optional
        from typing_extensions import TypedDict

        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.constants import START
        from langgraph.graph import StateGraph
        from langgraph.types import interrupt, Command


        class State(TypedDict):
            \"\"\"The graph state.\"\"\"

            foo: str
            human_value: Optional[str]
            \"\"\"Human value will be updated using an interrupt.\"\"\"


        def node(state: State):
            answer = interrupt(
                # This value will be sent to the client
                # as part of the interrupt information.
                \"what is your age?\"
            )
            print(f\"> Received an input from the interrupt: {answer}\")
            return {\"human_value\": answer}


        builder = StateGraph(State)
        builder.add_node(\"node\", node)
        builder.add_edge(START, \"node\")

        # A checkpointer must be enabled for interrupts to work!
        checkpointer = InMemorySaver()
        graph = builder.compile(checkpointer=checkpointer)

        config = {
            \"configurable\": {
                \"thread_id\": uuid.uuid4(),
            }
        }

        for chunk in graph.stream({\"foo\": \"abc\"}, config):
            print(chunk)

        # > {'__interrupt__': (Interrupt(value='what is your age?', id='45fda8478b2ef754419799e10992af06'),)}

        command = Command(resume=\"some input from a human!!!\")

        for chunk in graph.stream(Command(resume=\"some input from a human!!!\"), config):
            print(chunk)

        # > Received an input from the interrupt: some input from a human!!!
        # > {'node': {'human_value': 'some input from a human!!!'}}
        ```

    Args:
        value: The value to surface to the client when the graph is interrupted.

    Returns:
        Any: On subsequent invocations within the same node (same task to be precise), returns the value provided during the first invocation

    Raises:
        GraphInterrupt: On the first invocation within the node, halts execution and surfaces the provided value to the client.
    """
    from langgraph._internal._constants import (
        CONFIG_KEY_CHECKPOINT_NS,
        CONFIG_KEY_SCRATCHPAD,
        CONFIG_KEY_SEND,
        RESUME,
    )
    from langgraph.config import get_config
    from langgraph.errors import GraphInterrupt

    conf = get_config()["configurable"]
    # track interrupt index
    scratchpad = conf[CONFIG_KEY_SCRATCHPAD]
    idx = scratchpad.interrupt_counter()
    # find previous resume values
    if scratchpad.resume:
        if idx < len(scratchpad.resume):
            conf[CONFIG_KEY_SEND]([(RESUME, scratchpad.resume)])
            return scratchpad.resume[idx]
    # find current resume value
    v = scratchpad.get_null_resume(True)
    if v is not None:
        assert len(scratchpad.resume) == idx, (scratchpad.resume, idx)
        scratchpad.resume.append(v)
        conf[CONFIG_KEY_SEND]([(RESUME, scratchpad.resume)])
        return v
    # no resume value found
    raise GraphInterrupt(
        (
            Interrupt.from_ns(
                value=value,
                ns=conf[CONFIG_KEY_CHECKPOINT_NS],
            ),
        )
    )
···

interrupt 可以接受任意的类型，说明会有很多种的打断方式

# 3. model call limit, model fall back, model retry

这其实就不用说了，很明显的是为了模型执行服务的

## 3.1 ModelCallLimitMiddleware

源码是这么说的

This middleware monitors the number of model calls made during agent execution
and can terminate the agent when specified limits are reached. It supports
both thread-level and run-level call counting with configurable exit behaviors.

监测中间件，检测 agent 执行周期内模型调用次数，并且次数到达上线后就断掉，同时支持 对话级别和运行级别的退出/终止机制


···
class ModelCallLimitState(AgentState[ResponseT]):
    """State schema for `ModelCallLimitMiddleware`.

    Extends `AgentState` with model call tracking fields.

    Type Parameters:
        ResponseT: The type of the structured response. Defaults to `Any`.
    """

    thread_model_call_count: NotRequired[Annotated[int, PrivateStateAttr]] 
    run_model_call_count: NotRequired[Annotated[int, UntrackedValue, PrivateStateAttr]]
···
以上是刚才提到的俩参数， 单 thread（chat） 的调用模型次数, 第二个是单次 run 启用的模型次数


def __init__(
        self,
        *,
        thread_limit: int | None = None,
        run_limit: int | None = None,
        exit_behavior: Literal["end", "error"] = "end",
    )

除了chat级别以及 单次运行的生命周期的 model call 限制， 还有还提供了 end 和 error 两种机制，估计也是为了方便

···
    @hook_config(can_jump_to=["end"])
    @override
    def before_model(
        self, state: ModelCallLimitState[ResponseT], runtime: Runtime[ContextT]
    ) -> dict[str, Any] | None:
        """Check model call limits before making a model call.

        Args:
            state: The current agent state containing call counts.
            runtime: The langgraph runtime.

        Returns:
            If limits are exceeded and exit_behavior is `'end'`, returns
                a `Command` to jump to the end with a limit exceeded message. Otherwise
                returns `None`.

        Raises:
            ModelCallLimitExceededError: If limits are exceeded and `exit_behavior`
                is `'error'`.
        """
        thread_count = state.get("thread_model_call_count", 0)
        run_count = state.get("run_model_call_count", 0)

        # Check if any limits will be exceeded after the next call
        thread_limit_exceeded = self.thread_limit is not None and thread_count >= self.thread_limit
        run_limit_exceeded = self.run_limit is not None and run_count >= self.run_limit

        if thread_limit_exceeded or run_limit_exceeded:
            if self.exit_behavior == "error":
                raise ModelCallLimitExceededError(
                    thread_count=thread_count,
                    run_count=run_count,
                    thread_limit=self.thread_limit,
                    run_limit=self.run_limit,
                )
            if self.exit_behavior == "end":
                # Create a message indicating the limit was exceeded
                limit_message = _build_limit_exceeded_message(
                    thread_count, run_count, self.thread_limit, self.run_limit
                )
                limit_ai_message = AIMessage(content=limit_message)

                return {"jump_to": "end", "messages": [limit_ai_message]}

        return None
···

同时加了钩子函数 hook config 这个单纯给函数添加了个属性 即 can jump to
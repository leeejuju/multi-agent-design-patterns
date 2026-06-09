# type.py (这里规定了 Middlewara 的一堆 meta 设计, 并且提供了已经内置其中的 agent/model 行为注解，方便)

这里提供注解是为了方便那些只需要用到单个be/af agent/model周期的行为但是不需要全套的情况

这里直接看一个就行了，逻辑是一样的

```python
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

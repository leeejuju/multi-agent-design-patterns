# model call limit

这其实就不用说了，很明显的是为了模型执行服务的

## ModelCallLimitMiddleware

源码是这么说的

This middleware monitors the number of model calls made during agent execution
and can terminate the agent when specified limits are reached. It supports
both thread-level and run-level call counting with configurable exit behaviors.

这是个监测中间件，检测 agent 执行周期内模型调用次数，并且次数到达上线后就断掉，同时支持 对话级别和运行级别的退出/终止机制

同时规定了当前中间件的隔离状态
```python
class ModelCallLimitState(AgentState[ResponseT]):
    """State schema for `ModelCallLimitMiddleware`.

    Extends `AgentState` with model call tracking fields.

    Type Parameters:
        ResponseT: The type of the structured response. Defaults to `Any`.
    """

    thread_model_call_count: NotRequired[Annotated[int, PrivateStateAttr]] 
    run_model_call_count: NotRequired[Annotated[int, UntrackedValue, PrivateStateAttr]]
```
以上是刚才提到的俩参数， 单 thread（chat） 的调用模型次数, 第二个是单次 run 启用的模型次数


```python
def __init__(
        self,
        *,
        thread_limit: int | None = None,
        run_limit: int | None = None,
        exit_behavior: Literal["end", "error"] = "end",
    )
```

除了chat级别以及 单次运行的生命周期的 model call 限制， 还有还提供了 end 和 error 两种机制，估计也是为了方便

```python
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
```

同时加了钩子函数 hook config 这个单纯给所有函数添加了个属性 即 can jump to
这一点就遵循 graph 构建时的 exit 路径，有 end 就走 end, 没有 end 就走 aftermodel
本身 model call limit，这个 Middleware只是限制call 其实没什么好说的

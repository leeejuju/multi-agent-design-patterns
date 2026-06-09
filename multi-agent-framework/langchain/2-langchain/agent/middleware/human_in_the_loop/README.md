# HIL.py 人在回路，说这个主要是涉及到任务的 interupt 和 resume.

![HIL example](../../image/HIL_eg.png)


人在回路中间件，规定了一系列断点。



cc 和 codex 让你 yes 的就是 HIL 

我在想一个问题，比如 claude , chatgpt 的 web 端 和 cc的逻辑估计是一样的

cc 里是这么搞的


```text
```

HumanInTheLoopMiddleware 提供了一个 interrupt_on 参数， 类型是 dict[str, bool] 以及 dict[str, InterruptOnConfig]

对于需要被拦截的工具，提供了三个选项 approve, edit, reject， InterruptOnConfig 稍微不一样，组成也是 allowed_decisions，和 descprtion

组合完后完成后，就形成了 HIL 中间件

同时 HIL 规定的了两个封装，ActionRequest， ReviewConfig，本别代表执行的函数参数以及需要review，审批的类型

那到解析的后就形成了HIL的执行链路

那么要问了，最核心的打断是怎么实现的

## interrupt
```python
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
```

interrupt 可以接受任意的类型，说明会有很多种的打断方式

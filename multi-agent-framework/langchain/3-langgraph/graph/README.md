# langgraph.graph

源码位置：`.venv/Lib/site-packages/langgraph/graph/`

## state.py (图创建的核心包)

```python
class StateGraph(Generic[StateT, ContextT, InputT, OutputT]):
    """A graph whose nodes communicate by reading and writing to a shared state.

    The signature of each node is `State -> Partial<State>`.
```

graph 创建类，当前 create_agent 的底层方法之一，也是图的入口。

其定义了一堆类属性， edages、nodes、branches、channels、managed、schemas、watting_edages、compiled。

以及 state_schema: type[StateT] context_schema: type[ContextT] | None input_schema: type[InputT]
output_schema: type[OutputT] 等四个层面的状态管理类。

这里有一点很有意思，主要是关于 Graph 参数的处理

他对参数做了三个分类，Managed、Channel、Schemas

这里我们要回到 [channels](../channels/README.md) 看下




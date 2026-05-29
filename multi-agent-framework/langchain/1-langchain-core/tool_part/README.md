# langchain_core tool part


## BaseTool

```python
name: str
description: str
args_schema: Annotated[ArgsSchema | None, SkipValidation()] = Field(
    default=None, description="The tool schema."
) 以上几个都不提了，一眼就知道干啥的


return_direct: bool = False
这个参数单独拎出来，按着源码的描述是这样子
处理 AgentExecutor 中的工具调用问题，True 的时候调用后会直接结束 AgentExecutor 的循环, 此外 AgentExecutor 是个巨老的包，弃用了已经

verbose: bool = False 日志

callbacks: Callbacks = Field(default=None, exclude=True)
我猜测是所有可 Runnable 的东西都要加上这样一个Call back函数,


tags: list[str] | None = None 

metadata: dict[str, Any] | None = None
handle_tool_error: bool | str | Callable[[ToolException], str] | None = False
handle_validation_error: (
    bool | str | Callable[[ValidationError | ValidationErrorV1], str] | None
) = False
response_format: Literal["content", "content_and_artifact"] = "content"
extras: dict[str, Any] | None = None
```

## InjectedToolArg && InjectedToolCallId && ## BaseToolkit

    """Annotation for tool arguments that are injected at runtime.

    Tool arguments annotated with this class are not included in the tool
    schema sent to language models and are instead injected during execution.

    运行时注入的工具参数，这个后续我会说，先mark下





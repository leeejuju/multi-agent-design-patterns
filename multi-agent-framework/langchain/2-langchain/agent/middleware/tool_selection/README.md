# tool_selection
```text
Uses an LLM to select relevant tools before calling the main model.

    When an agent has many tools available, this middleware filters them down
    to only the most relevant ones for the user's query. This reduces token usage
    and helps the main model focus on the right tools.
```
    
顾名思义，ToolSelect 中间件的描述是：Use an LLM to select a relevant tool before calling the main model。

也就是说，在执行主模型之前，先通过它来选择最适合的模型或最适合的工具。


获取最近一轮的 user 消息，以及开发者自己固定的一些消息（比如一些 tool）。

就比如说，在我处理某一项任务的时候，开发者会固定把这几个工具（比如 HIL，即 Human-in-the-loop）放在这里。因为这些部分其实会一直存在，所以他会将这些工具固定在这里边

而且它主要是为了不去占位。因为你是固定的，固定的工具会始终存在，所以它就不会去占那个 Available tools.的站位，所以会在后边拼

然后基本上这些

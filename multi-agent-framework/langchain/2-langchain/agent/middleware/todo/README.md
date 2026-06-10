# TODO middleware

## preamble

TODO 顾名思义，就是规划个 list 出来
sc 是这么说的：
This middleware adds a `write_todos` tool that allows agents to create and manage
structured task lists for complex multi-step operations. It's designed to help
agents track progress, organize complex tasks, and provide users with visibility
into task completion status.

总结下来就是：这玩意是为了复杂任务设计，目的就是给 Agent 提供任务任务上的分解，协助追踪进度（提供可观测性）
ps: AgentMiddleware 的专属状态要留在 Middleware 内部，他原生的几乎所有都是这么设计

## design pattern

现在要进行思考，从直觉出发，计划的生成要靠谁？

模型理所应当是第一选择，所以 TODO 就围绕了 wrap_model_call 去控制模型的生成(看下来是)，after_model 控制结果？



## TODO prompt
```
WRITE_TODOS_TOOL_DESCRIPTION = """Use this tool to create and manage a structured task list for your current work session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.

Only use this tool if you think it will be helpful in staying organized. If the user's request is trivial and takes less than 3 steps, it is better to NOT use this tool and just do the task directly.

## When to Use This Tool
Use this tool in these scenarios:

1. Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
2. Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
3. User explicitly requests todo list - When the user directly asks you to use the todo list
4. User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)
5. The plan may need future revisions or updates based on results from the first few steps

## How to Use This Tool
1. When you start working on a task - Mark it as in_progress BEFORE beginning work.
2. After completing a task - Mark it as completed and add any new follow-up tasks discovered during implementation.
3. You can also update future tasks, such as deleting them if they are no longer necessary, or adding new tasks that are necessary. Don't change previously completed tasks.
4. You can make several updates to the todo list at once. For example, when you complete a task, you can mark the next task you need to start as in_progress.

## When NOT to Use This Tool
It is important to skip using this tool when:
1. There is only a single, straightforward task
2. The task is trivial and tracking it provides no benefit
3. The task can be completed in less than 3 trivial steps
4. The task is purely conversational or informational

## Task States and Management

1. **Task States**: Use these states to track progress:
   - pending: Task not yet started
   - in_progress: Currently working on (you can have multiple tasks in_progress at a time if they are not related to each other and can be run in parallel)
   - completed: Task finished successfully

2. **Task Management**:
   - Update task status in real-time as you work
   - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
   - Complete current tasks before starting new ones
   - Remove tasks that are no longer relevant from the list entirely
   - IMPORTANT: When you write this todo list, you should mark your first task (or tasks) as in_progress immediately!.
   - IMPORTANT: Unless all tasks are completed, you should always have at least one task in_progress to show the user that you are working on something.

3. **Task Completion Requirements**:
   - ONLY mark a task as completed when you have FULLY accomplished it
   - If you encounter errors, blockers, or cannot finish, keep the task as in_progress
   - When blocked, create a new task describing what needs to be resolved
   - Never mark a task as completed if:
     - There are unresolved issues or errors
     - Work is partial or incomplete
     - You encountered blockers that prevent completion
     - You couldn't find necessary resources or dependencies
     - Quality standards haven't been met

4. **Task Breakdown**:
   - Create specific, actionable items
   - Break complex tasks into smaller, manageable steps
   - Use clear, descriptive task names

Being proactive with task management demonstrates attentiveness and ensures you complete all requirements successfully
Remember: If you only need to make a few tool calls to complete a task, and it is clear what you need to do, it is better to just do the task directly and NOT call this tool at all."""  # noqa: E501

WRITE_TODOS_SYSTEM_PROMPT = """## `write_todos`

You have access to the `write_todos` tool to help you manage and plan complex objectives.
Use this tool for complex objectives to ensure that you are tracking each necessary step and giving the user visibility into your progress.
This tool is very helpful for planning complex objectives, and for breaking down these larger complex objectives into smaller steps.

It is critical that you mark todos as completed as soon as you are done with a step. Do not batch up multiple steps before marking them as completed.
For simple objectives that only require a few steps, it is better to just complete the objective directly and NOT use this tool.
Writing todos takes time and tokens, use it when it is helpful for managing complex many-step problems! But not for simple few-step requests.

## Important To-Do List Usage Notes to Remember
- The `write_todos` tool should never be called multiple times in parallel.
- Don't be afraid to revise the To-Do list as you go. New information may reveal new tasks that need to be done, or old tasks that are irrelevant."""  # noqa: E501

```

TODO 的 prompt 分为俩
一个是 WRITE_TODOS_TOOL_DESCRIPTION, 一个 是 WRITE_TODOS_SYSTEM_PROMPT

这就不说了，一个是定位，一个是详细的描述，拆解下先

WRITE_TODOS_SYSTEM_PROMPT： 

翻译下来是：

使用 write_todo 工具，管理和规划复杂目标，用这工具可以确保能追踪到每一步，且给用户提供每一步的可观测性
该工具可以提供负责复杂任务的规划，将其拆分为多个子步骤

尤其重要的是，当todo 完成后，要显式的标记为 done, 不可以在任务结束之前，batch执行多步骤
对于那些只需几步就完成的任务，就不要用这工具，
todo是个烧token的工具，所有只用在复杂任务上
**important TODO List Useage Note ti Remember**

1. Todo 不一次并发call很多个。
2. 要动态修改 Todo 不要害怕改动，因为可能有新消息进来，也有新任务，也有无关的老任务，所以不要直接改

WRITE_TODOS_TOOL_DESCRIPTION（略长）：

使用该工具，对当前会话的结构性任务进行拆分和管理，
再次强调工具是长任务用的，3步以上用，否则不用

### When to Use This Tool

1. 复杂多步任务，当需要3步以上的任务/需要清晰任务的时候/
2. 有一定复杂性的任务，任务需要详细的规划和分多步执行
3. 用户请求规划todo list 的任务：
4. 用户请求多个任务（比如用，分割）
5. 需要根据前几个任务进行迭代的plan任务

### How to Use This Tool

1. 当任务执行前，将其标记为 in_progress
2. 完成任务后：将任务标记为 completed 如有新任务，则加进来
3. 可更新future（估计是未执行）任务：比如删除无用的任务，或者添加新任务
4. 你可以一次性执行数个更新操作到 todo list 中，比如，当你完成一个任务时，可以同时把下一个需要开始的任务标记为 in_progress

### Task States and Management

他详细的描述了任务的几个管理方式和状态**Task States**，**Task Management**，**Task Completion Requirements** **Task Breakdown**
好几个类的状态去处理，

这个才是核心
Task States 规定了 pending, in_progress, complelted 这是任务三状态

Task Management 则是如何管理任务
包含了更新任务状态，确定任务的执行状态，任务必须一个接一个，任务开始后的第一个需要理解标记为 in_progress 

### Task Completion Requirements 则规定了任务完成的标准

1. 全部完成才能标记 completed 的状态.
2. 执行中遇到错误，阻塞，或者无法完成，则将该任务始终标记为in_progress
3. 以下情况禁止将任务标记为 complelted
   1. 有无法解决的问题或者错误
   2. 任务只处理了一半或者没完成
   3. 遇到阻塞无法完成
   4. 无法找到完成任务所需的资源或者依赖
   5. 任务结果的质量不达标

### Task Breakdown 任务分解策略

1. 生成详细可执行的条目
2. 将复杂任务拆解为多个可处理的小任务
3. 使用清晰的描述性 task name

## Conclusion

总结下来就是，你要是说很复杂吗，其实不至于

langchain 在设计 todo的时候会反复详细的设计和强调任务的推进逻辑和状态标记原则，我隐约能感觉到一些东西，但是又说不清

但是可以看出提示词的趋势在于，强调状态的稳定管理，如何稳定的推进任务？

所以他反复的强调状态，通篇提示词没有写很多 case 而是维护状态的稳定，不是很久之前的 prompt 时代那种硬性的约束书写

工程手段上就没啥可说的了，预设了 write_tool方法，通过 StructuredTool 构建形成
调用就完事了

而且，这种任务还可以切模型思考，具体就在 wrap_model_call 就行，
   





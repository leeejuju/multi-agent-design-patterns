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

## 拆分笔记

| 模块 | 笔记 |
| :--- | :--- |
| `types.py` | [types](types/README.md) |
| `human_in_the_loop.py` | [human_in_the_loop](human_in_the_loop/README.md) |
| `model_call_limit.py` | [model_call_limit](model_call_limit/README.md) |
| `model_fallback.py` | [model_fallback](model_fallback/README.md) |
| `model_retry.py` | [model_retry](model_retry/README.md) |
| `tool_call_limit.py` | [tool_call_limit](tool_call_limit/README.md) |
| `tool_emulator.py` | [tool_emulator](tool_emulator/README.md) |
| `tool_retry.py` | [tool_retry](tool_retry/README.md) |
| `tool_selection.py` | [tool_selection](tool_selection/README.md) |
| `summarization.py` | [summarization](summarization/README.md) |

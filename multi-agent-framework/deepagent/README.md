# DeepAgent 架构阅读笔记

这份笔记只关注 DeepAgent 系统中最核心的运行时设计，不展开太多细枝末节。

重点是理解它作为 Agent Harness 的工程组织方式：Agent 在运行前如何准备上下文，运行中如何管理状态，以及不同模型如何被约束到相对稳定的行为模式。

## 核心分层

DeepAgent 主要可以拆成三个部分：

1. `Backend`
   - 定义运行时后端能力，例如 Shell 调用、Protocol 协议、Sandbox 和 State。
   - 负责存储 Agent 运行时状态，并承载运行过程中产生的附属产物。

2. `Middleware`
   - 主要承载模型调用前后的预处理和后处理。
   - 在 LangChain 后续版本的 Agent 结构中，Middleware 是非常关键的扩展点。

3. `Profiles`
   - 面向不同模型定义 Harness 约束。
   - 不同模型的行为模式并不一致，因此需要通过 Profile 做纠偏，让 Agent 运行规则更稳定。

回到 Harness 本身，这才是 DeepAgent 的核心意义：它不是只包装一次模型调用，而是组织一套可控的 Agent 运行环境。

## 运行入口

整体入口在 `create_agent`。

这个入口会把运行时需要的模块组织起来，例如 `backend_factory`，并接入以下工具和协议：

1. 协议部分：`protocol`、`backend_protocol`
2. 文件系统：`file_system` middleware
3. 内存管理：`memory` middleware
4. 调用处理：`patch_to_calling` middleware
5. 扩展能力：`skills` middleware

这些组件共同处理 Agent 运行前需要准备的行为和上下文信息。

## Backend：状态与工作区

Backend 是这套系统里很值得关注的一层。

在 Coding Agent 中，运行时上下文会持续产生很多状态。比如使用 `ls`、`read`、`grep` 等工具时，本质上都需要围绕当前工作区维护状态、文件信息和执行结果。

DeepAgent 在架构上把状态管理做了拆分：

- Agent 本身的运行流转状态是一类信息。
- Agent 运行过程中产生的文件、命令结果、临时内容是另一类信息。
- Backend 提供统一的工作区抽象，用来承载这些可读写、可查询、可路由的运行时资源。

所以 Backend 的价值不只是“保存东西”，而是给上层 Agent 和 Middleware 提供一套通用工具，例如 `ls`、`read` 等，让不同状态机都能复用同一套运行时能力。

其中 `Composite Backend` 可以理解为一个路由型 Backend：它把不同类型的行为请求分发到不同 Backend，再完成二次路由。

## File System Middleware

File System 是 Coding Agent 中最常见的能力。

运行 Codex、 Claude Code 这类工具，比较常见以下工具：

- `grep`
- `ls`
- `read`

这里有一个容易忽略的细节：列举文件时要处理 `symlink`。

`symlink` 是 symbolic link，也就是指向其他文件或目录的链接。它在文件系统里比较特殊，如果不加限制，可能导致遍历范围变得不可控。因此 DeepAgent 在文件列举阶段做了过滤，避免 Coding Agent 在文件系统访问上引入复杂风险。

另一个值得注意的方法是 `perform string replacement`。

它主要用于控制写入或替换行为中的偏差。比如字符串替换时经常会遇到：

1. 待替换目标不存在。
2. 目标字符串有细微偏差，例如末尾位置不同，或者夹杂换行、空格等控制字符。

这个方法的意义在于：让文件修改行为尽量保持确定，而不是直接交给模型自由生成整段文件内容。

## 暂不展开的部分

代码里还涉及 LangSmith。

由于 LangSmith 是 LangChain 自己的观测体系，并且商用场景会涉及收费，这里暂时不展开。当前笔记更关注 DeepAgent 自身的 Harness、Backend、Middleware 和文件系统设计。






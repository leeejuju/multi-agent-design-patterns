# summarization.

summarization，是一个需要思考的东西。不同的业务场景下，亚索的对象也应该是不同的

coding 下对于任务的连续性就很重要，但是你换到其他行业就不一定了，而且压缩的重点也各不相同

此外在面试过程中，经常会问到压缩机制的问题：压缩的是什么，压缩了那些东西，以及具体的压缩策略。

针对这方面，我建议去看一下 CC 和 Codex 的源码。因为 CC 源码是泄露了的，Codex 是开源的，通过对比研究这两个项目的源码，基本上就能看出其中的端倪了。


## langchain' compact strategy

以下是 langchain 压缩的时候的 promopt, langchain 作为一个 agent SDK 是为了搭建 agent, 所以提供单个的 prompt ，同时 SumarMiddleware 也只是个样板，所以策略上不像  cc or codex ,没那么多东西，主要分为了几个部分，role, primary obj, obj_info, instruction 

### role, primary obj, obj_info

role就不说了，
primary obj 说的就是，Prompt 的唯一任务就是根据历史对话，提取高质量/最相关的上下文

obj_info：大意是当接近可接受的输入的 token 上限的时候，根据历史对话，提取高价值的历史/和历史对话最相近的上下文

提取出的上下文将会重写提供的上下文的历史记录，因此需要确保压缩信息是对任务目标有用的

### instruction

SESSION INTENT（会话意图）: 确定用户的主要意图和请求，任务目标是什么？意图的总结需要足够简洁和充分能理解对话的整个意图.

SUMMARY (总结) : 从历史会话提取并记录所有的重要内容，包括重要的选择，结论以及对话中的策略选择，以及重要决策背后的推理逻辑

记录下所有拒绝的选项，并且说明为何没有采用

ARTIFACTS（产物） ：产出了什么文件？或者整个对话（agent 执行）期间有无资源被访问，修改，创建？如果改了，说清楚改了那里，以及改的路径
主要是为了防止丢失以及 rewind估计

NEXT STEPS：离着完成任务还有几步？下一步要干啥

看下来就是，从对话、回溯、记忆、以及任务等方面对上下文进行拆分提取，对于一般的对话来说，也是够的，但是像设计到

harness 的 cc, codex这种任务来说也是不太够的，下面我会说下 cc 是如何去 compat 上下文的

```python
DEFAULT_SUMMARY_PROMPT = \
"""
<role>
Context Extraction Assistant
</role>

<primary_objective>
Your sole objective in this task is to extract the highest quality/most relevant context from the conversation history below.
</primary_objective>

<objective_information>
You're nearing the total number of input tokens you can accept, so you must extract the highest quality/most relevant pieces of information from your conversation history.
This context will then overwrite the conversation history presented below. Because of this, ensure the context you extract is only the most important information to continue working toward your overall goal.
</objective_information>

<instructions>
The conversation history below will be replaced with the context you extract in this step.
You want to ensure that you don't repeat any actions you've already completed, so the context you extract from the conversation history should be focused on the most important information to your overall goal.

You should structure your summary using the following sections. Each section acts as a checklist - you must populate it with relevant information or explicitly state "None" if there is nothing to report for that section:

## SESSION INTENT
What is the user's primary goal or request? What overall task are you trying to accomplish? This should be concise but complete enough to understand the purpose of the entire session.

## SUMMARY
Extract and record all of the most important context from the conversation history. Include important choices, conclusions, or strategies determined during this conversation. Include the reasoning behind key decisions. Document any rejected options and why they were not pursued.

## ARTIFACTS
What artifacts, files, or resources were created, modified, or accessed during this conversation? For file modifications, list specific file paths and briefly describe the changes made to each. This section prevents silent loss of artifact information.

## NEXT STEPS
What specific tasks remain to be completed to achieve the session intent? What should you do next?

</instructions>

The user will message you with the full message history from which you'll extract context to create a replacement. Carefully read through it all and think deeply about what information is most important to your overall goal and should be saved:

With all of this in mind, please carefully read over the entire conversation history, and extract the most important and relevant context to replace it so that you can free up space in the conversation history.
Respond ONLY with the extracted context. Do not include any additional information, or text before or after the extracted context.

<messages>
Messages to summarize:
{messages}
</messages>

"""
```

## claude code's compact Strategy

像 cc 和 codex 这样的 coding agent, 可以细想下执行中有哪些场景？

像你用这些的时候，会根据使用的 terminal 不同使用不同的原生工具。我用 win 就会有一堆 rg, gerp 这一堆 shell 的原生命令
在家用 wsl 就会有其他的 linux 原生命令，同时 AGENT.md以及Claude.md写了啥命令，也会用，比如我就会用 uv 和 ruff （但是没用过 Mac 呜呜呜呜呜
）

同时提问需求的前后会有 你的需求，代码的变动，调用了社么工具，结果如何？是否中断，执行结果等等等

对于 cc 来说 （这里只看 /compat 路径）

触发压缩的时候他把 NO_TOOLS_PREMBLE 放在前面

```
const NO_TOOLS_PREAMBLE = `CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.

- Do NOT use Read, Bash, Grep, Glob, Edit, Write, or ANY other tool.
- You already have all the context you need in the conversation above.
- Tool calls will be REJECTED and will waste your only turn — you will fail the task.
- Your entire response must be plain text: an <analysis> block followed by a <summary> block.
```
翻译过来是：

```
注意：仅仅回答，不要调用工具（而且是什么都不能用）
你已经有当前对话所需的全部上下文
tool call 不允许执行，而且这会直接导致失败（因为会waste 掉这一轮）
这么说好奇怪

规定了回答模式为<analysis> 和  <summary> 的block
```

看下来 Anthropic 在设计时反复提到了不允许调用工具，并且枚举了工具，而且陈述了调用的结果（即使调用了也会是失败，我估计时写的有检测代码兜底，而且必须是plain text）。

我猜测是有以下原因：1，模型本身习惯性的调用工具。2，针对这样的场景难以解决这种情况。3，强调：禁止调用工具->调用也会失败，且浪费一轮机会->必须输出 plain-text 这种禁止+陈述利弊+再次要求的方式，维度就是把输出的倾向引导为直接输出内容


BASE_COMPACT_PROMPT
```text
"""
const BASE_COMPACT_PROMPT = `Your task is to create a detailed summary of the conversation so far, paying close attention to the user's explicit requests and your previous actions.
This summary should be thorough in capturing technical details, code patterns, and architectural decisions that would be essential for continuing development work without losing context.

${DETAILED_ANALYSIS_INSTRUCTION_BASE}

Your summary should include the following sections:

1. Primary Request and Intent: Capture all of the user's explicit requests and intents in detail
2. Key Technical Concepts: List all important technical concepts, technologies, and frameworks discussed.
3. Files and Code Sections: Enumerate specific files and code sections examined, modified, or created. Pay special attention to the most recent messages and include full code snippets where applicable and include a summary of why this file read or edit is important.
4. Errors and fixes: List all errors that you ran into, and how you fixed them. Pay special attention to specific user feedback that you received, especially if the user told you to do something differently.
5. Problem Solving: Document problems solved and any ongoing troubleshooting efforts.
6. All user messages: List ALL user messages that are not tool results. These are critical for understanding the users' feedback and changing intent.
7. Pending Tasks: Outline any pending tasks that you have explicitly been asked to work on.
8. Current Work: Describe in detail precisely what was being worked on immediately before this summary request, paying special attention to the most recent messages from both user and assistant. Include file names and code snippets where applicable.
9. Optional Next Step: List the next step that you will take that is related to the most recent work you were doing. IMPORTANT: ensure that this step is DIRECTLY in line with the user's most recent explicit requests, and the task you were working on immediately before this summary request. If your last task was concluded, then only list next steps if they are explicitly in line with the users request. Do not start on tangential requests or really old requests that were already completed without confirming with the user first.
                       If there is a next step, include direct quotes from the most recent conversation showing exactly what task you were working on and where you left off. This should be verbatim to ensure there's no drift in task interpretation.

Here's an example of how your output should be structured:

<example>
<analysis>
[Your thought process, ensuring all points are covered thoroughly and accurately]
</analysis>

<summary>
1. Primary Request and Intent:
   [Detailed description]

2. Key Technical Concepts:
   - [Concept 1]
   - [Concept 2]
   - [...]

3. Files and Code Sections:
   - [File Name 1]
      - [Summary of why this file is important]
      - [Summary of the changes made to this file, if any]
      - [Important Code Snippet]
   - [File Name 2]
      - [Important Code Snippet]
   - [...]

4. Errors and fixes:
    - [Detailed description of error 1]:
      - [How you fixed the error]
      - [User feedback on the error if any]
    - [...]

5. Problem Solving:
   [Description of solved problems and ongoing troubleshooting]

6. All user messages: 
    - [Detailed non tool use user message]
    - [...]

7. Pending Tasks:
   - [Task 1]
   - [Task 2]
   - [...]

8. Current Work:
   [Precise description of current work]

9. Optional Next Step:
   [Optional Next step to take]

</summary>
</example>

Please provide your summary based on the conversation so far, following this structure and ensuring precision and thoroughness in your response. 

There may be additional summarization instructions provided in the included context. If so, remember to follow these instructions when creating the above summary. Examples of instructions include:
<example>
## Compact Instructions
When summarizing the conversation focus on typescript code changes and also remember the mistakes you made and how you fixed them.
</example>

<example>
# Summary instructions
When you are using compact - please focus on test output and code changes. Include file reads verbatim.
</example>
`
"""
```

其抽取内容有好几个部分

得 detail

而且他用了一个词 **paying close attention**  to the user's explicit requests and your previous action.This summary should be thorough in capturing technical details, code patterns, and architectural decisions that would be essential for continuing development work without losing context

翻过来就是
**需要重点关注用户的请求和之前的行为，总结需要捕捉技术细节，代码模式/样式/结构（大概这意思），以及不可或缺的，结构性的对于继续开发任务至关重要的决定**

重点关注的是历史行为和用户的**清晰请求**

且总结需要涵盖

**技术细节**， **代码样式**，**不可或缺的，结构性的对于继续开发任务至关重要的决**

但是说实话，他这个提示词有点抽象，我们继续往下看

"""
DETAILED_ANALYSIS_INSTRUCTION_BASE = \

"""
Before providing your final summary, wrap your analysis in <analysis> tags to organize your thoughts and ensure you've covered all necessary points. In your analysis process:

1. Chronologically analyze each message and section of the conversation. For each section thoroughly identify:
   - The user's explicit requests and intents
   - Your approach to addressing the user's requests
   - Key decisions, technical concepts and code patterns
   - Specific details like:
     - file names
     - full code snippets
     - function signatures
     - file edits
   - Errors that you ran into and how you fixed them
   - Pay special attention to specific user feedback that you received, especially if the user told you to do something differently.
2. Double-check for technical accuracy and completeness, addressing each required element thoroughly.
"""
DETAILED_ANALYSIS_INSTRUCTION_BASE

是对于填充内容的分析要求

要求在给出结果前，在 analysis 里组织语言，并且要确保生成的内容要涵盖到之前提过的几个方面

1，渐进式的分析所选对话的每个消息，并且每个对话需要囊括
    1，用户的意图和需求
    2，处理用户需求的方案方法
    3，关键决策，技术性的概念和代码样式（可能是结构，架构都可能）
    4，特定的细节： 文件明，全部的代码，函数的名称参数，文件的改动情况
    5，遇到的错误以及解决方案
    6，尤其注意 **pay special attention** 用户的反馈，尤其是做一些不一样的事

2， 反复检查技术的准确性，总结分析的完整性，确保完备处理每个所需的元素的

这部分其实就是分析精确性的要求，详细总结了所需要分析总结的元素，强调了那些是重点，是一段强化性质的prompt

下面是元素具体内容的要求

Your summary should include the following sections:

1. Primary Request and Intent: Capture all of the user's explicit requests and intents in detail
2. Key Technical Concepts: List all important technical concepts, technologies, and frameworks discussed.
3. Files and Code Sections: Enumerate specific files and code sections examined, modified, or created. Pay special attention to the most recent messages and include full code snippets where applicable and include a summary of why this file read or edit is important.
4. Errors and fixes: List all errors that you ran into, and how you fixed them. Pay special attention to specific user feedback that you received, especially if the user told you to do something differently.
5. Problem Solving: Document problems solved and any ongoing troubleshooting efforts.
6. All user messages: List ALL user messages that are not tool results. These are critical for understanding the users' feedback and changing intent.
7. Pending Tasks: Outline any pending tasks that you have explicitly been asked to work on.
8. Current Work: Describe in detail precisely what was being worked on immediately before this summary request, paying special attention to the most recent messages from both user and assistant. Include file names and code snippets where applicable.
9. Optional Next Step: List the next step that you will take that is related to the most recent work you were doing. IMPORTANT: ensure that this step is DIRECTLY in line with the user's most recent explicit requests, and the task you were working on immediately before this summary request. If your last task was concluded, then only list next steps if they are explicitly in line with the users request. Do not start on tangential requests or really old requests that were already completed without confirming with the user first.

If there is a next step, include direct quotes from the most recent conversation showing exactly what task you were working on and where you left off. This should be verbatim to ensure there's no drift in task interpretation.


这种详细性质的定义包含

1. 主要需求/意图：捕捉到用户所有的清晰的需求的意图细节
2. 关键技术概念：列出所有的重要技术概念，技术以及框架/架构上的讨论
3. 文件和代码：枚举所有修改，检查, 创建的指定文件和代码，尤其关注最新的消息，也要包含全部的可用代码片段，同时也要附上为何读取修改该文件重要性的总结。
4. 错误与修复： 列举遇到的所有错误，以及对应错误的修改方案，尤其主要用户的反馈以及用户所要求的（修改？修复方式）？
5. 问题处理（注意问题不一定就是错误）：记录所有已经解决的问题以及正在定位中的问题
6. 用户的msg：列举出所有的非toolcall的用户消息，这些有助于理解用户的反馈和用户意图是否变化
7. 待处理任务：描述已经发出并且正在进行中的任务
8. 当前任务：在总结历史前，以精确的文字描述需要理解触发的任务，并且重点关注AI的回答和用户的消息，包含那些可用的文件名称和代码实例
9. 可选（Next Step）：根据当前的任务列举出下一步最相关的任务
注意：确保当前的步骤和用户最近的需求保持一致，并且要在总结前任务是理解触发的。如果上一步任务已经结束且下一步清晰的符合用户需求，则列举出下一部任务。要确保向用户进行询问，不要从老任务或者无关任务开始。

如果有下一步的任务，则需要包含从最近的对话中引用正在处理或者遗留的任务，而且要原封不动的进行执行 or 总结，确保任务的理解不会漂移。

随后就是一些 fewshot 的examaple 规定了输出的样式

看下来，Antropic 从多个维度对要总结的内容进行了详细的规定

可以看出没有 specific 轮数，即没有以轮数作为压缩单位，

而是着重在于文件修改，历史对话，技术细节，错误修改以及原因，和任务的状态，特别是改动的细节，最为主要的总结对象，以及下一步的规定
这个压缩策略，就有点以 diff 为主的工程性变动，而非类似的对话性质的压缩

他在结尾有拼接了 NO_TOOLS_TRAILER 再次强调不允许调用工具以及输出的格式，估计是为了防止长文本的稀释，在尾端又强调了一次
const NO_TOOLS_TRAILER =
  '\n\nREMINDER: Do NOT call any tools. Respond with plain text only — ' +
  'an <analysis> block followed by a <summary> block. ' +
  'Tool calls will be rejected and you will fail the task.'



### claude code compact prompt 总结

从分析 langchain 和 cc 的summraize/compact 其实都是为了压缩上下文，
而且侧重的对象异曲同工，都是包含了用户的意图，执行过程中的错误以及修改方式，文件的生成，创建等等。
只不过 cc 的设计更加的细致且科学

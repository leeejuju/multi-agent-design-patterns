# DeepAgent 工程范式

这里记录几种适合在当前项目中沉淀的 agent 工程范式。每种范式都优先描述最小可运行结构，避免提前引入复杂编排。

## 1. Harness

Harness 是 agent 的执行外壳，用来把模型、工具、状态、日志和评测入口固定下来。

适用场景：

- 需要反复运行同一个 agent 任务。
- 需要稳定记录输入、输出、工具调用和错误。
- 需要把 demo 代码整理成可测试、可复现的工程入口。

最小结构：

```text
harness/
  agent.py        # agent 定义
  tools.py        # 可调用工具
  state.py        # 任务状态
  runner.py       # 命令行或脚本入口
  evals.py        # 样例任务与验证逻辑
```

核心流程：

```text
input -> build_context -> agent_step -> tool_call -> observe -> final_output
```

工程要点：

- `runner.py` 只负责装配和运行，不写业务逻辑。
- 工具函数保持小而明确，返回结构化结果。
- 状态对象记录任务进度、关键中间产物和错误信息。
- eval 样例先覆盖关键路径，再补边界情况。

## 2. Research

Research 是面向资料检索、阅读、归纳和引用整理的 agent 范式。

适用场景：

- 技术调研、论文阅读、竞品分析、资料汇总。
- 需要把多个来源合并成结构化结论。
- 需要明确区分事实、推断和待验证问题。

最小角色：

- `Planner`：拆分研究问题，生成查询计划。
- `Searcher`：检索候选资料。
- `Reader`：提取关键事实、观点和证据。
- `Synthesizer`：合并结论，输出报告。

核心流程：

```text
question -> research_plan -> search -> read -> notes -> synthesis -> report
```

输出建议：

```text
summary
key_findings
evidence
open_questions
next_steps
```

工程要点：

- 每条结论尽量保留来源。
- 把原始摘录和最终总结分开存储。
- 对不确定内容显式标注为推断或待验证。
- 避免让同一个 agent 同时负责搜索、判断和写最终报告。

## 3. Text to Circle

Text to Circle 是把自然语言输入转换为循环结构、闭环流程或圆形关系图的 agent 范式。

适用场景：

- 把文本需求整理成反馈闭环。
- 把业务过程抽象为环状流程。
- 把复杂说明转换成可视化节点和边。

最小结构：

```text
text -> entities -> relations -> circle_model -> render_payload
```

推荐数据结构：

```python
{
    "title": "循环名称",
    "nodes": [
        {"id": "plan", "label": "计划"},
        {"id": "act", "label": "执行"},
        {"id": "observe", "label": "观察"},
        {"id": "adjust", "label": "调整"},
    ],
    "edges": [
        {"source": "plan", "target": "act"},
        {"source": "act", "target": "observe"},
        {"source": "observe", "target": "adjust"},
        {"source": "adjust", "target": "plan"},
    ],
}
```

工程要点：

- 先抽取节点，再判断边，最后补全闭环。
- 节点数量保持克制，优先 4 到 8 个。
- 如果文本不是闭环结构，先输出线性流程，再由 agent 判断是否能闭合。
- 渲染层只消费结构化数据，不直接解析自然语言。

## 4. Rough Loop

Rough Loop 是快速草稿、评审、修订的迭代式 agent 范式。

适用场景：

- 写作、方案设计、代码草案、提示词优化。
- 目标不完全明确，需要通过多轮粗糙产物收敛。
- 希望先得到可用版本，再逐步提高质量。

最小角色：

- `Drafter`：生成第一版粗稿。
- `Reviewer`：指出问题、缺口和风险。
- `Reviser`：根据评审意见修订。
- `Judge`：判断是否达到停止条件。

核心流程：

```text
goal -> draft -> review -> revise -> judge -> final
                    ^                  |
                    |------------------|
```

停止条件：

- 达到最大迭代次数。
- `Judge` 判断输出已经满足目标。
- 剩余问题不值得继续迭代。

工程要点：

- 第一版草稿可以粗糙，但必须完整。
- Reviewer 只指出可执行问题，不写泛泛评价。
- Reviser 只处理本轮评审意见，避免扩大范围。
- 每轮保存 `draft`、`review`、`revision`，便于回放和调试。

## 选型建议

| 范式 | 主要目标 | 典型产物 |
| --- | --- | --- |
| Harness | 稳定运行与评测 | runner、日志、eval |
| Research | 调研与综合 | notes、evidence、report |
| Text to Circle | 文本到闭环结构 | nodes、edges、diagram payload |
| Rough Loop | 迭代打磨 | draft、review、revision |

优先从 Harness 开始，把运行入口和状态记录固定下来；其他范式可以作为 Harness 内部的具体任务形态逐步加入。

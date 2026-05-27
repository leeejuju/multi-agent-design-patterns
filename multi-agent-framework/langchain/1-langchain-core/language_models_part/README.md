# Language Models — 模型抽象层

> 本模块定义了 LangChain 中所有语言模型的标准接口。
> 无论是 OpenAI、Anthropic、Qwen 还是本地模型，都必须遵循这套协议。

---

## 🏗️ 继承链

```
Runnable[Input, Output]                  ← 万物基类（统一调用协议）
    │
RunnableSerializable[Input, Output]      ← 加入序列化能力
    │   └── 继承了 Serializable（存盘/读盘）
    │   └── 继承了 Runnable（invoke/stream/batch）
    │
BaseLanguageModel[LanguageModelOutputVar] ← 基础定义输入输出泛型
    │
    └── BaseChatModel                     ← 聊天模型（输入消息列表，输出 AIMessage）
        │
        └── BaseChatOpenAI                ← OpenAI 聊天模型
            │
            ├── ChatOpenAI                ← GPT-4 等
            └── AzureChatOpenAI           ← Azure 部署
```

---

## 🔑 核心概念

### 1. `BaseLanguageModel` — Model的基基类，定义了模型所需的固定行为以及部分参数

比如generate——prompt的行为以及一些cache以及token相关 (cache行为后面再说，相当重要的知识点)

```python
class BaseLanguageModel(RunnableSerializable[LanguageModelInput, LanguageModelOutputVar], ABC):
```

- `LanguageModelInput` — 输入类型，支持 `str`、`list[BaseMessage]`、`PromptValue`
- `LanguageModelOutputVar` — 输出类型，被约束为 `AIMessage` 或 `str`

### 2. `BaseChatModel` — 模型基类，所有langchain的适配都是走这个

```python
class BaseChatModel(BaseLanguageModel[AIMessage], ABC):

这里由于 Python 本身的问题，只说异步的，反正异步也是同步改过来的

他异步生成的这一套经过的特别复杂的过程

我只想吐槽，傻逼才用 py 的 AI SDK 去做 Agent 侧， 我真他妈被折磨的不行。

我只说ainvoke 和 astream这部分。


基本上是套了 N 多层的路径，导致了这么慢的执行速度，草泥马










```

- 输出类型固定为 `AIMessage`
- 和其他方法一样提供了异步和同步的方法


### 3. `RunnableSerializable` 

```python
class RunnableSerializable(Serializable, Runnable[Input, Output]):
```


---


# LangChain Message 源码分析

## 1. BaseMessage — 消息基类

### 1.1 核心字段

message里和其他组件一样，继承了 BaseMessage

并且规定了基础的Message参数，以及序列化等一些玩意

```
content: str | list[str | dict]
    """The contents of the message."""

    additional_kwargs: dict = Field(default_factory=dict)
    """Reserved for additional payload data associated with the message.

    For example, for a message from an AI, this could include tool calls as
    encoded by the model provider.

    """

    response_metadata: dict = Field(default_factory=dict)
    """Examples: response headers, logprobs, token counts, model name."""

    type: str
    """The type of the message. Must be a string that is unique to the message type.

    The purpose of this field is to allow for easy identification of the message type
    when deserializing messages.

    """

    name: str | None = None
    """An optional name for the message.

    This can be used to provide a human-readable name for the message.

    Usage of this field is optional, and whether it's used or not is up to the
    model implementation.

    """

    id: str | None = Field(default=None, coerce_numbers_to_str=True)
```

比如这些等，这里就一一不表了

### 1.2 类层次：BaseMessage 与 BaseMessageChunk

base在大类上设计了二类

BaseMessage 与 BaseMessageChunk，对应单条消息和多组BaseMessag子集消息集合

除此之外没有别的了，基本就是消息的合并转化，

### 1.3 设计思考

除此之外，比较好奇的就是，我感觉写法是有点遗留设计的意思，但是又感觉像故意这么设计的
并非是目的性的质疑，而是for循环略慢，但是他这个又是没法避免的，为了适配多家模型，for循环一步一步整理

但是后续他又推出了一堆 langchain-xxx，估计也是性质的设计，毕竟，还有那种普适方法

### 1.4 消息格式转换流水线

```python
from langchain_core.messages.block_translators.anthropic import (  # noqa: PLC0415
    _convert_to_v1_from_anthropic_input,
)
from langchain_core.messages.block_translators.bedrock_converse import (  # noqa: PLC0415
    _convert_to_v1_from_converse_input,
)
from langchain_core.messages.block_translators.google_genai import (  # noqa: PLC0415
    _convert_to_v1_from_genai_input,
)
from langchain_core.messages.block_translators.langchain_v0 import (  # noqa: PLC0415
    _convert_v0_multimodal_input_to_v1,
)
from langchain_core.messages.block_translators.openai import (  # noqa: PLC0415
    _convert_to_v1_from_chat_completions_input,
)
```

以上消息类型的转化，基本上

```python
for parsing_step in [
    _convert_v0_multimodal_input_to_v1,
    _convert_to_v1_from_chat_completions_input,
    _convert_to_v1_from_anthropic_input,
    _convert_to_v1_from_genai_input,
    _convert_to_v1_from_converse_input,
]:
```

消息的转化经过了以上五个工序

#### 第一步：_convert_v0_multimodal_input_to_v1（旧格式兼容）

这部分是初步的过滤，分为俩方法，

_convert_legacy_v0_content_block_to_v1
以及
_convert_v0_multimodal_input_to_v1

基础的逻辑上是将

符合他的名字，是将初始的所有类型消息，无论是 text or image or something else,
将其分开包裹，其中包括消息类型，格式，extra等

而且有几个点很有意思

1. 就是_convert_v0_multimodal_input_to_v1 判断了双层的

   ```
   if block_type not in {"image", "audio", "file"} or "source_type" not in block:
       # Not a v0 format block, return unchanged
       return block
   ```

   ，我估计是一种防御性质的写法？毕竟是legacy了？

2. 当存在img内容时， source会有一个 id 的情况， 这个我调试的时候没太遇见，我估计是传图是一种，text的方式的时候，会有这情况

总体，也说明了V1 的 Messages 格式，包含的都是 xxxxContentBlock 的实例

基本处理对象也只有 img，file, audio 三种类型

#### 第二步：_convert_to_v1_from_chat_completions_input（OpenAI 格式兼容）

这是对于模型产生结果的兼容，比如之前国内特别多的厂商走的都是 OpemAI的格式，现在走 A\ 的也多

对于已经清理好的信息 langchain v1 的 message
先走一段 is_openai_data_block 方法

方法具体我就不提供了

总之要满足符合 OpenAI 的格式，image 文件，需要
block 的顶级字段符合 {"type", "image_url", "detail"}
同时 iamge_url 需要是 dict, 且 url 必须是 str .

file 和 audio 倒是简单一点，

完事走了 _convert_openai_format_to_data_block
将 OpenAI 的格式，转为 v1

然后将非 v1 的消息关键字下沉到 nostandard

#### 第三步～第五步：Anthropic / Google / AWS 格式适配

后续三个都是为了适配 A\, Google, AWS的格式了，不再一一详述

## 2. SystemMessage 与 HumanMessage

这俩基本上单纯继承了 BaseMessage 然后没做其他的特别修改而已，

这里就跳过了先，所有的操作基本是从父类拿

## 3. AIMessage 与 ToolMessage

AI msg 是最最最核心的部分，Agent运行的上下文，基本都是这里的产出

其主要分为了五类

### 3.1 InputTokenDetails / OutputTokenDetails / UsageMetadata

1. InputTokenDetails

2. OutputTokenDetails

3. UsageMetadata

### 3.2 AIMessage

4. AIMessage

   这里定义了三个主要参数

   tool call、invalid_toolcall, usage_metadata

   顾名思义，有效/无效的toolcall 以及 token消耗的元数据

   其返回了俩 attr , 都是 tool 相关的， 剩下的就是

   content_blocks 这里编排了 AI 相关的内容， 如果消息的返回内容，符合 v1 格式

   直接返回 v1 定义的各种 xxContentBlock

   不符合就会走，get_translator，

   get_translator 注册了基本各个大厂商的模型，并且提供了，从各个厂商转接回 v1 格式的中间件

   然后通过中间件把 AIMessage 转出去，前提是Response了模型厂商，而且是得集成了Translator

   而对于 toolcall AI message 两手措施，一个是 tool call 一个是content，所以在content block 加上了 tool call的失败或者错漏的问题

   还有一个很奇怪的问题，就是如果你开启了 enable reasoning，它会把 reasoning 放到最前面。

   ```
   has_reasoning = any(block.get("type") == "reasoning" for block in blocks)
   if not has_reasoning and (
       reasoning_block := _extract_reasoning_from_additional_kwargs(self)
   ):
       blocks.insert(0, reasoning_block)

   return blocks
   ```

   我 debug 了一下，发现确实在前面。我猜这可能是一种语义上的约定。通常我们人类做事都会先 reasoning，先想好应该怎么做，然后再决定下一步。

   这就跟炒菜似的：做菜之前先想好怎么做，然后再去准备油、盐、醋。这种行为逻辑应该是这样的。

### 3.3 AIMessageChunk（流式输出）

5. AIMessageChunk

   AI Message Chunk 其实是一个比较特殊的东西。

   你可以这样理解：在输出时本质上只有 AI Message 这一种对象，所以当它进行流式输出（Streaming）时，系统会将 AI Message 打碎，以 AI Chunk 的方式进行输出。

   基本上，这个机制的作用主要体现在两个方面：
   1. 前端 UI 界面：用户可以看到内容逐字跳出的流式变化。后端基本上都可以看到，比如说 message、tool name 的 message，还有 tool arguments，这些东西全都可以看到。
   2. 本地工具执行：
      工具的执行（Tool Call）必须等 AI Chunk 全部输出完毕。后端在拼接好完整的 Tool Call 参数后，才会正式触发工具的执行。 chunk_position 的参数其实也是代表这个意思
      然后，它也会在纯粹的 Tool Call 场景下，对其进行标准化的 format

   但是你可以看到 AIMessageChunk 有一个特定的处理方法，因为它是涉及到流式输出的，所以需要连续add到初始的 message list 里面，不然也没法拼成一个整体的有效片段


嗯，因为所有的东西都是从第一性原理去看的，所以说这些不是特别重要的东西我都不看了，本身也是结合开发过程中所看到的一些东西去分析

以上所有内容由 Typeless 口述整理
# LangChainMessage Part

## base.py
message里和其他组件一样，继承了 BaseMessage

并且规定了基础的Message参数，以及序列化等一些玩意

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


比如这些等，这里就一一不表了

base在大类上设计了二类

BaseMessage 与 BaseMessageChunk，对应单条消息和多组BaseMessag子集消息集合

除此之外没有别的了，基本就是消息的合并转化，

除此之外，比较好奇的就是，我感觉写法是有点遗留设计的意思，但是又感觉像故意这么设计的
并非是目的性的质疑，而是for循环略慢，但是他这个又是没法避免的，为了适配多家模型，for循环一步一步整理

但是后续他又推出了一堆 langchain-xxx，估计也是性质的设计，毕竟，还有那种普适方法


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
以上消息类型的转化，基本上

for parsing_step in [
            _convert_v0_multimodal_input_to_v1,
            _convert_to_v1_from_chat_completions_input,
            _convert_to_v1_from_anthropic_input,
            _convert_to_v1_from_genai_input,
            _convert_to_v1_from_converse_input,
        ]:消息的转化经过了以上五个工序

一，_convert_v0_multimodal_input_to_v1：


这部分是初步的过滤，分为俩方法，

_convert_legacy_v0_content_block_to_v1
以及
_convert_v0_multimodal_input_to_v1


基础的逻辑上是件将


符合他的名字，是将初始的所有类型消息，无论是 text or image or something else, 
将其分开包裹，其中包括消息类型，格式，extra等

而且有几个点很有意思

1，就是_convert_v0_multimodal_input_to_v1 判断了双层的

if block_type not in {"image", "audio", "file"} or "source_type" not in block:
        # Not a v0 format block, return unchanged
        return block


，我估计是一种防御性质的写法？毕竟是legacy了？

2.当存在img内容时， source会有一个 id 的情况， 这个我调试的时候没太遇见，我估计是穿图是一种，text的方式的时候，会有这情况


总体，也说明了V1 的 Messages 格式，包含的都是 xxxxContentBlock 的实例

基本处理对象也只有 img，file, audio 三种类型


二，_convert_to_v1_from_chat_completions_input：

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


后续三个都是为了适配 A\, Google, AWS的格式了，不再一一详述

## System and Human msg
这俩基本上单纯继承了 BaseMessage 然后没做其他的特别修改而已，

这里就跳过了先，所有的操作基本是从父类拿

## AI msg && Tool msg

AI msg 是最最最核心的部分，Agent运行的上下文，基本都是这里的产出

其主要分为了五类


1，InputTokenDetails

2，OutputTokenDetails

3，UsageMetadata

4，AIMessage
这里定义了三个主要参数

tool call、invalid_toolcall, usage_metadata

顾名思义，有效/无效的toolcall 以及 token消耗的元数据

其返回了俩 attr , 都是 tool 相关的， 剩下的就是

content_blocks 这里编排了 AI 相关的内容， 如果消息的返回内容，符合 v1 格式

直接返回 v1 定义的各种 xxContentBlock

不符合就会走，get_translator，

get_translator 注册了基本各个大厂商的模型，并且提供了，从各个厂商转接回 v1 格式的中间件

然后通过中间件把 AIMessage 转出去，前提是Response了模型厂商，而且是得集成了Translator


而对于 toolcall AI messageLiam两手措施，一个是 tool call 一个是content，所以在content block 加上了 tool call的失败或者错漏的问题





5，AIMessageChunk（只是个对上面的集成）
































    

    




# langchain_core outparser
模型输出结果规定的究极基类

## Base's BaseLLMOutputParser
定义了模型结果解析的抽象类，没啥好说的，只是所有基类都要实现自己的 parse_result 方法
根据返回的 Geration 块，生成结构化的 output .

## Base's BaseGenerationOutputParser


# langchain_core output

## generation's Generation

定义了生成消息的基本属性，依旧是属于可Serilizable的对象

## generation's GenerationChunk
模型生成内容的最小单位，其定义了 add 方法，可以把所有 Chunk 拼接起来后重新返回 GenerationChunk

## chatgeneartion's ChatGeneration
单次对话生成的内容，兼容了 deprcated 的消息格式，初始化后填充信息

## chatgeneartion's ChatGenerationChunk
合并多轮的 GenerateChunk


## chat_result's ChatResult
原文是 Use to represent the result of a chat model call with a single prompt. 即代表单次的 prompt 触发后的模型输出结果，


## LLMResult
"A container for results of an LLM call. 也很简单，存储模型触发回答的一系列的 List .基本也是模模型输出的下游任务处理




以上作为消息生成的基建类pack，承载了模型输出后的格式规定以及内容上的编排，output负责结果的生成，等任务逐渐走向下游的具体类中时，这些才会这真正的发挥作用，

但是其定义总觉得有些过头的地方，

langchain 在设计的时候，Generation 集成了基础属性，内容，names以及Serializeable那一套的属性, GenerateChunk 作为基础性质的容器,负责将多个 Generation 进行集成为一整个的chunk 。 



同时又定义了 ChatGeneration 以及 ChatGenerationChunk 这个 more Spesific 一点，用于集成 LLM 输出的，经由 langchain 的 msg 格式化的 BaseMessages 及其子类的（HumanMessage, AIMessage, SystemMessages）等消息。、


LLMResult以及generation， generationchunk 我反倒是觉得有些遗留设计的问道

因为Genertion本身的内容除了承载输出单元的属性定义以外，是有点不符合的，ChatGeration 才是更符合当前对话消息输出的设计方案





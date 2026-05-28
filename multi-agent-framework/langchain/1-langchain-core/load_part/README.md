# langchain_core load part

这里定义了 langchain 的核心行为之一，即 Serializable 它实现了langchain对象的在模型输入输出的序列化和反序列化，尤其重要的一点

并且给出了大量的解释，为何要这么设计，序列化和反序列化时的所要注意的问题

## mapping
这里规定了所有的可序列化/反序列化相关规定的  langchain 命名空间
兼容了一堆老包,

## validators




## Reviver
和 Serializable 是一对，负责 lc 对象的恢复，涉及到 langchain 运行周期的各个方面

## Serializable
这个详细的定义了lc的序列化和反序列化的核心


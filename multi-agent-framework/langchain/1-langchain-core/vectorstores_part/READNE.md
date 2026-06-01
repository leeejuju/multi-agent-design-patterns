# langchain_core vectores part

## class VectorStore(ABC):
  为了将所有的向量库纳入 langchain 体系下的基类，定义了VecDB的所有基础方法具体就不展开说了

  我一直觉得，langchain want do everything 的想法，有点弱智了，向量库作为外部数据源的读取以及内部数据的转换桥接部分，我不明白为何也要集成，数据交换的部分直接交给程序员自己做不好吗？

  除非是这样子，是在我看来。以后所有的基础设计，无论是已经纳入体系的 GREP 等 OS 的基础方法还是 text2sql（本质上是 SQL as tool） 这一类。以后的所有内容都可能会变成 AGENTIC Tool 的基础设施/工具节点， 而不是以前的单纯的信息的传递和交换（简单RAG的时代是作为检索或者embeding），可能是出于这个考虑，而将向量库纳入 Agent 体系，不仅是检索，而是作为体系的一员，附带上检索的能力，我能想到的设计目的只有这一个。

  但是感觉还是很臃肿，langchain 真的是叠了很多层。
  
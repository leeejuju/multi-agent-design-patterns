# langchain_core.document part

## BaseMedia
官方是这么说的，RAG检索和处理（str）数据的基本定义单位
但是不适用多模态的情况 

由于 Retrieval 在发展初期的的碎片性，导致其必定是一块一块的

## Blob

一般是py有个基类，这是文件加载中的初最小原始单位


## Document

class Document(BaseMedia):
    """Class for storing a piece of text and associated metadata.

    !!! note

        `Document` is for **retrieval workflows**, not chat I/O. For sending text
        to an LLM in a conversation, use message types from `langchain.messages`.

    Example:
        ```python
        from langchain_core.documents import Document

        document = Document(
            page_content="Hello, world!", metadata={"source": "https://example.com"}
        )
        ```
    """

    这个我熟，以前刚做RAG处理，拆分后的字段+原始数据直接拆分后进行处理就完事了


## BaseDocumentCompressor
文档的后处理方式抽象类，后面用到再说



## BaseDocumentTransformer(ABC):

文件转换的抽象类，后面看到会给穿起来


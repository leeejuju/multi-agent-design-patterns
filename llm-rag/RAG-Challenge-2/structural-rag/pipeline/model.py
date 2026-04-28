from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Document:
    """输入文档的元数据。"""
    source: str
    file_name: str
    metadata: dict = field(default_factory=dict)


@dataclass
class Chunk:
    """最小检索单元。"""

    text: str
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if "chunk_id" not in self.metadata:
            self.metadata["chunk_id"] = uuid4().hex


@dataclass
class PageChunks:
    """单页全部 chunk。检索的时候用"""

    page_index: int
    chunks: list[Chunk] = field(default_factory=list)

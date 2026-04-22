from dataclasses import dataclass


@dataclass
class Document:
    source: str
    blocks: list["Block"]
    metadata: dict


@dataclass
class Block:
    text: str
    block_type: str
    page: int | None
    level: int | None
    metadata: dict


@dataclass
class Chunk:
    text: str
    metadata: dict

# from dataclasses import dataclass


# @dataclass
# class Document:
#     source: str  # 来源（文件路径、URL 等）
#     blocks: list["Block"]  # 语义块列表
#     metadata: dict  # 原始文档元数据（如文件名、日期等）


# @dataclass
# class Block:
#     text: str  # 文本块
#     block_type: str  # 文本块类型（text、table、figure 等）
#     page: int | None  # 页码
#     level: int | None  # 文本块等级
#     metadata: dict  # 文本块元数据


# @dataclass
# class Chunk:
#     text: str
#     metadata: dict

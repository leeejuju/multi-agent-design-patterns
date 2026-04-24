import re
from dataclasses import dataclass
from pathlib import Path

try:
    from ..model import Chunk
except ImportError:
    from model import Chunk


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PAGE_MARKER_PATTERN = re.compile(r"^<!--\s*page:\s*(\d+|None)\s*-->\s*$")
TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
FENCE_PATTERN = re.compile(r"^\s*(```|~~~)")


@dataclass
class MarkdownBlock:
    text: str
    block_type: str
    page: int | None


@dataclass
class MarkdownSection:
    heading_path: list[str]
    level: int | None
    blocks: list[MarkdownBlock]

    @property
    def text(self) -> str:
        return "\n\n".join(block.text for block in self.blocks).strip()


class MarkdownChunker:
    def __init__(
        self,
        max_chars: int = 1800,
        min_chars: int = 300,
        overlap_chars: int = 150,
    ):
        self.max_chars = max_chars
        self.min_chars = min_chars
        self.overlap_chars = overlap_chars

    def chunk_file(self, markdown_path: str | Path, metadata: dict | None = None) -> list[Chunk]:
        markdown_path = Path(markdown_path).expanduser().resolve()
        content = markdown_path.read_text(encoding="utf-8")
        file_metadata = {"source": str(markdown_path)}
        if metadata:
            file_metadata.update(metadata)
        return self.chunk_text(content, file_metadata)

    def chunk_text(self, content: str, metadata: dict | None = None) -> list[Chunk]:
        metadata = metadata or {}
        sections = split_markdown_sections(content)
        chunks: list[Chunk] = []

        for section_index, section in enumerate(sections):
            parent_id = f"{metadata.get('source', 'document')}::section-{section_index}"
            parent_text = section.text
            if not parent_text:
                continue

            parent_metadata = {
                **metadata,
                "chunk_type": "parent",
                "parent_id": parent_id,
                "section_index": section_index,
                "heading_path": section.heading_path,
                "heading": section.heading_path[-1] if section.heading_path else None,
                "level": section.level,
                "page_start": first_page(section.blocks),
                "page_end": last_page(section.blocks),
            }
            chunks.append(Chunk(text=parent_text, metadata=parent_metadata))

            for child_index, child_blocks in enumerate(self.split_blocks(section.blocks)):
                child_text = "\n\n".join(block.text for block in child_blocks).strip()
                if not child_text:
                    continue

                chunks.append(
                    Chunk(
                        text=inject_heading_context(section.heading_path, child_text),
                        metadata={
                            **parent_metadata,
                            "chunk_type": "child",
                            "child_index": child_index,
                            "parent_id": parent_id,
                            "page_start": first_page(child_blocks),
                            "page_end": last_page(child_blocks),
                        },
                    )
                )

        return chunks

    def split_blocks(self, blocks: list[MarkdownBlock]) -> list[list[MarkdownBlock]]:
        chunks: list[list[MarkdownBlock]] = []
        current: list[MarkdownBlock] = []
        current_size = 0

        for block in blocks:
            block_size = len(block.text)
            next_size = current_size + block_size + (2 if current else 0)

            if current and next_size > self.max_chars and current_size >= self.min_chars:
                chunks.append(current)
                current = self.tail_overlap(current)
                current_size = block_text_size(current)

            current.append(block)
            current_size += block_size + (2 if len(current) > 1 else 0)

        if current:
            chunks.append(current)

        return chunks

    def tail_overlap(self, blocks: list[MarkdownBlock]) -> list[MarkdownBlock]:
        if self.overlap_chars <= 0:
            return []

        tail: list[MarkdownBlock] = []
        size = 0
        for block in reversed(blocks):
            if block.block_type in {"table", "code"}:
                continue
            tail.insert(0, block)
            size += len(block.text) + 2
            if size >= self.overlap_chars:
                break
        return tail


def split_markdown_sections(content: str) -> list[MarkdownSection]:
    blocks = parse_markdown_blocks(content)
    sections: list[MarkdownSection] = []
    heading_stack: list[tuple[int, str]] = []
    current_blocks: list[MarkdownBlock] = []
    current_level: int | None = None

    for block in blocks:
        match = HEADING_PATTERN.match(block.text)
        if match:
            if current_blocks:
                sections.append(
                    MarkdownSection(
                        heading_path=[heading for _, heading in heading_stack],
                        level=current_level,
                        blocks=current_blocks,
                    )
                )
                current_blocks = []

            level = len(match.group(1))
            title = strip_markdown_emphasis(match.group(2))
            heading_stack = [
                (item_level, item_title)
                for item_level, item_title in heading_stack
                if item_level < level
            ]
            heading_stack.append((level, title))
            current_level = level
            current_blocks.append(block)
            continue

        current_blocks.append(block)

    if current_blocks:
        sections.append(
            MarkdownSection(
                heading_path=[heading for _, heading in heading_stack],
                level=current_level,
                blocks=current_blocks,
            )
        )

    return sections


def parse_markdown_blocks(content: str) -> list[MarkdownBlock]:
    lines = content.splitlines()
    blocks: list[MarkdownBlock] = []
    buffer: list[str] = []
    current_page: int | None = None
    block_page: int | None = None
    index = 0

    def flush(block_type: str = "text") -> None:
        nonlocal buffer, block_page
        text = "\n".join(buffer).strip()
        if text:
            blocks.append(MarkdownBlock(text=text, block_type=block_type, page=block_page))
        buffer = []
        block_page = None

    while index < len(lines):
        line = lines[index]
        page_match = PAGE_MARKER_PATTERN.match(line.strip())
        if page_match:
            flush()
            current_page = None if page_match.group(1) == "None" else int(page_match.group(1))
            index += 1
            continue

        if not line.strip():
            flush()
            index += 1
            continue

        if FENCE_PATTERN.match(line):
            flush()
            fence = FENCE_PATTERN.match(line).group(1)
            block_page = current_page
            buffer.append(line)
            index += 1
            while index < len(lines):
                buffer.append(lines[index])
                if lines[index].strip().startswith(fence):
                    index += 1
                    break
                index += 1
            flush("code")
            continue

        if is_table_start(lines, index):
            flush()
            block_page = current_page
            while index < len(lines) and is_table_line(lines[index]):
                buffer.append(lines[index])
                index += 1
            flush("table")
            continue

        if HEADING_PATTERN.match(line):
            flush()
            blocks.append(MarkdownBlock(text=line.strip(), block_type="heading", page=current_page))
            index += 1
            continue

        if block_page is None:
            block_page = current_page
        buffer.append(line)
        index += 1

    flush()
    return blocks


def is_table_start(lines: list[str], index: int) -> bool:
    return (
        index + 1 < len(lines)
        and is_table_line(lines[index])
        and TABLE_SEPARATOR_PATTERN.match(lines[index + 1]) is not None
    )


def is_table_line(line: str) -> bool:
    return line.strip().startswith("|") and "|" in line.strip()[1:]


def strip_markdown_emphasis(text: str) -> str:
    return text.strip().strip("#").strip().strip("*_`").strip()


def inject_heading_context(heading_path: list[str], text: str) -> str:
    if not heading_path:
        return text
    return f"Section: {' > '.join(heading_path)}\n\n{text}"


def block_text_size(blocks: list[MarkdownBlock]) -> int:
    return sum(len(block.text) for block in blocks) + max(0, len(blocks) - 1) * 2


def first_page(blocks: list[MarkdownBlock]) -> int | None:
    pages = [block.page for block in blocks if block.page is not None]
    return min(pages) if pages else None


def last_page(blocks: list[MarkdownBlock]) -> int | None:
    pages = [block.page for block in blocks if block.page is not None]
    return max(pages) if pages else None

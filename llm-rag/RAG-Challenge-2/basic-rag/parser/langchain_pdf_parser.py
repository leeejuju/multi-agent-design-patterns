from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

import fitz

CONTENT_PATTERN = re.compile(r"[^A-Za-z0-9\u4e00-\u9fff\s.,;:!?()%$+\-*/=<>@#&'\"]")
SEPARATOR_PATTERN = re.compile(r"[-_.=]{4,}")
SPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class ChunkConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 200


@dataclass(frozen=True)
class ChunkSlice:
    content: str
    start: int
    end: int


@dataclass(frozen=True)
class PdfDocument:
    source: Path
    page_texts: list[str]
    full_text: str
    page_spans: list[tuple[int, int]]


def clean_content(content: str) -> str:
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    content = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", content)
    content = re.sub(r"[ \t]+\n", "\n", content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = SEPARATOR_PATTERN.sub(" ", content)
    content = CONTENT_PATTERN.sub(" ", content)
    return SPACE_PATTERN.sub(" ", content).strip()


def compose_document(page_texts: list[str]) -> tuple[str, list[tuple[int, int]]]:
    spans: list[tuple[int, int]] = []
    parts: list[str] = []
    cursor = 0

    for text in page_texts:
        if parts:
            parts.append("\n\n")
            cursor += 2
        start = cursor
        parts.append(text)
        cursor += len(text)
        spans.append((start, cursor))

    return "".join(parts), spans


def page_for_offset(page_spans: list[tuple[int, int]], offset: int) -> int:
    for page_index, (start, end) in enumerate(page_spans):
        if start <= offset < end:
            return page_index
    return max(len(page_spans) - 1, 0)


class LangChainPdfParser:
    parser_name = "pymupdf_recursive"
    label_prefix = "pymupdf_recursive"
    separators = ("\n\n", "\n", ". ", " ", "")

    def __init__(self, chunk_config: ChunkConfig | None = None) -> None:
        self.chunk_config = chunk_config or ChunkConfig()
        if self.chunk_config.chunk_overlap >= self.chunk_config.chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size。")

    def extract_document(self, pdf_path: str | Path) -> PdfDocument:
        source = Path(pdf_path).expanduser().resolve()
        page_texts: list[str] = []

        with fitz.open(source) as document:
            for page in document:
                page_texts.append(clean_content(page.get_text()))

        full_text, page_spans = compose_document(page_texts)
        return PdfDocument(
            source=source,
            page_texts=page_texts,
            full_text=full_text,
            page_spans=page_spans,
        )

    def split_document(self, document: PdfDocument) -> list[ChunkSlice]:
        if not document.full_text:
            return []

        chunks: list[ChunkSlice] = []
        step = self.chunk_config.chunk_size - self.chunk_config.chunk_overlap
        start = 0

        while start < len(document.full_text):
            end = min(start + self.chunk_config.chunk_size, len(document.full_text))
            end = self._best_split_end(document.full_text, start, end)
            content = document.full_text[start:end].strip()
            if content:
                content_start = (
                    start
                    + len(document.full_text[start:end])
                    - len(document.full_text[start:end].lstrip())
                )
                chunks.append(ChunkSlice(content=content, start=content_start, end=end))
            if end >= len(document.full_text):
                break
            start = max(end - self.chunk_config.chunk_overlap, start + step)

        return chunks

    def build_chunks(self, pdf_path: str | Path, *, label: str | None = None) -> list[dict]:
        document = self.extract_document(pdf_path)
        chunk_label = label or self._default_label()
        doc_id = document.source.stem

        return [
            {
                "doc_id": doc_id,
                "chunk_no": index,
                "content": chunk.content,
                "page": page_for_offset(document.page_spans, chunk.start),
                "token_count": len(chunk.content),
                "char_count": len(chunk.content),
                "source": document.source.stem,
                "label": chunk_label,
                "metadata": {
                    "parser": self.parser_name,
                    "chunk_size": self.chunk_config.chunk_size,
                    "chunk_overlap": self.chunk_config.chunk_overlap,
                },
            }
            for index, chunk in enumerate(self.split_document(document))
        ]

    def save_chunks(
        self,
        pdf_path: str | Path,
        output_path: str | Path,
        *,
        label: str | None = None,
    ) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        chunks = self.build_chunks(pdf_path=pdf_path, label=label)
        output.write_text(json.dumps(chunks, ensure_ascii=False, indent=4), encoding="utf-8")
        return output

    def _best_split_end(self, text: str, start: int, end: int) -> int:
        if end >= len(text):
            return end

        window = text[start:end]
        min_size = int(self.chunk_config.chunk_size * 0.6)
        for separator in self.separators:
            if not separator:
                return end
            offset = window.rfind(separator)
            if offset >= min_size:
                return start + offset + len(separator)
        return end

    def _default_label(self) -> str:
        return (
            f"{self.label_prefix}_{self.chunk_config.chunk_size}_{self.chunk_config.chunk_overlap}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="使用 PyMuPDF 解析 PDF 文件并写入 JSON 分块数据。")
    parser.add_argument("--input", required=True, help="PDF 文件或目录。")
    parser.add_argument("--output", required=True, help="JSON 文件或输出目录。")
    parser.add_argument("--chunk-size", type=int, default=1000, help="分块大小。默认：1000。")
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="分块重叠大小。默认：200。",
    )
    parser.add_argument("--label", default=None, help="可选的分块标签。")
    return parser.parse_args()


def iter_pdf_paths(input_path: Path) -> list[Path]:
    if input_path.is_dir():
        return sorted(input_path.glob("*.pdf"))
    return [input_path]


def output_path_for(pdf_path: Path, output_path: Path, multiple: bool) -> Path:
    if multiple or output_path.suffix.lower() != ".json":
        return output_path / f"{pdf_path.stem}.json"
    return output_path


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    pdf_paths = iter_pdf_paths(input_path)
    parser = LangChainPdfParser(
        chunk_config=ChunkConfig(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    )

    for pdf_path in pdf_paths:
        output = parser.save_chunks(
            pdf_path=pdf_path,
            output_path=output_path_for(pdf_path, output_path, multiple=len(pdf_paths) > 1),
            label=args.label,
        )
        print(f"分块已写入: {output}")


if __name__ == "__main__":
    main()

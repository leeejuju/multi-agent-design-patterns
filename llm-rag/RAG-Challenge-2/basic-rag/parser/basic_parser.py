from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import fitz

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+")


@dataclass(frozen=True, slots=True)
class ChunkConfig:
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size 必须大于 0。")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap 必须大于或等于 0。")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size。")


class BasicParser:
    def __init__(self, chunk_config: ChunkConfig | None = None) -> None:
        self.chunk_config = chunk_config or ChunkConfig()

    def extract_text(self, pdf_path: str | Path) -> tuple[Path, list[str], str]:
        source = Path(pdf_path).expanduser().resolve()
        if source.suffix.lower() != ".pdf":
            raise ValueError(f"仅支持 PDF 文件，收到: {source}")
        if not source.exists():
            raise FileNotFoundError(f"未找到 PDF 文件: {source}")

        with fitz.open(source) as document:
            page_texts = [page.get_text("text") or "" for page in document]

        full_text = self._normalize_text("\n\n".join(page_texts))
        return source, page_texts, full_text

    def build_chunks(
        self, pdf_path: str | Path, *, label: str | None = None
    ) -> list[dict]:
        source, page_texts, full_text = self.extract_text(pdf_path)
        chunks = self._fixed_chunks(full_text)
        doc_id = hashlib.sha256(str(source).encode("utf-8")).hexdigest()[:64]
        chunk_label = label or self._default_label()

        return [
            {
                "doc_id": doc_id,
                "chunk_no": index,
                "content": chunk,
                "token_count": self._estimate_token_count(chunk),
                "char_count": len(chunk),
                "source": str(source),
                "label": chunk_label,
                "metadata": {
                    "chunk_size": self.chunk_config.chunk_size,
                    "chunk_overlap": self.chunk_config.chunk_overlap,
                    "page_count": len(page_texts),
                    "parser": "pymupdf_raw_text",
                    "source_file": source.name,
                },
            }
            for index, chunk in enumerate(chunks)
        ]

    def save_chunks(
        self,
        pdf_path: str | Path,
        output_path: str | Path,
        *,
        label: str | None = None,
    ) -> Path:
        records = self.build_chunks(pdf_path=pdf_path, label=label)
        output = Path(output_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as file_obj:
            for record in records:
                file_obj.write(json.dumps(record, ensure_ascii=False) + "\n")
        return output

    def _fixed_chunks(self, text: str) -> list[str]:
        if not text:
            return []

        chunk_size = self.chunk_config.chunk_size
        step = chunk_size - self.chunk_config.chunk_overlap
        chunks: list[str] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_length:
                break
            start += step

        return chunks

    def _default_label(self) -> str:
        return f"raw_fixed_{self.chunk_config.chunk_size}_{self.chunk_config.chunk_overlap}"

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(r"[ \t]+\n", "\n", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        return len(TOKEN_PATTERN.findall(text))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="提取 PDF 原始文本并按固定大小输出 JSONL 分块。"
    )
    parser.add_argument("--input", required=True, help="PDF 文件路径。")
    parser.add_argument("--output", required=True, help="JSONL 输出文件路径。")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"固定分块大小。默认值: {DEFAULT_CHUNK_SIZE}。",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"固定分块重叠量。默认值: {DEFAULT_CHUNK_OVERLAP}。",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="可选的分块标签。默认值为 raw_fixed_<chunk_size>_<chunk_overlap>。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chunker = BasicParser(
        chunk_config=ChunkConfig(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    )
    output = chunker.save_chunks(
        pdf_path=args.input,
        output_path=args.output,
        label=args.label,
    )
    print(f"分块已写入: {output}")


if __name__ == "__main__":
    main()

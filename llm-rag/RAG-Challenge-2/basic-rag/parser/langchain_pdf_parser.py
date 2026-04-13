from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

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


class LangChainPdfParser:
    def __init__(self, chunk_config: ChunkConfig | None = None) -> None:
        self.chunk_config = chunk_config or ChunkConfig()

    def load_documents(self, pdf_path: str | Path) -> tuple[Path, list]:
        source = Path(pdf_path).expanduser().resolve()
        if source.suffix.lower() != ".pdf":
            raise ValueError(f"仅支持 PDF 文件，收到: {source}")
        if not source.exists():
            raise FileNotFoundError(f"未找到 PDF 文件: {source}")

        try:
            from langchain_community.document_loaders import PyMuPDFLoader
        except ImportError as exc:
            raise ImportError(
                "LangChain PDF 解析需要 langchain-community，"
                "请使用 `uv add langchain-community` 安装。"
            ) from exc

        loader = PyMuPDFLoader(str(source))
        return source, loader.load()

    def extract_text(self, pdf_path: str | Path) -> tuple[Path, list, str]:
        source, documents = self.load_documents(pdf_path)
        page_texts = [doc.page_content or "" for doc in documents]
        full_text = self._normalize_text("\n\n".join(page_texts))
        return source, documents, full_text

    def split_text(self, text: str) -> list[str]:
        if not text:
            return []

        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError as exc:
            raise ImportError(
                "RecursiveCharacterTextSplitter 需要 langchain-text-splitters，"
                "请使用 `uv add langchain-text-splitters` 安装。"
            ) from exc

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_config.chunk_size,
            chunk_overlap=self.chunk_config.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        return [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]

    def build_chunks(
        self,
        pdf_path: str | Path,
        *,
        label: str | None = None,
    ) -> list[dict]:
        source, documents, full_text = self.extract_text(pdf_path)
        chunks = self.split_text(full_text)
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
                    "page_count": len(documents),
                    "parser": "langchain_pymupdf_loader",
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

    def _default_label(self) -> str:
        return (
            f"langchain_fixed_{self.chunk_config.chunk_size}"
            f"_{self.chunk_config.chunk_overlap}"
        )

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
        description="使用 LangChain PyMuPDFLoader 解析 PDF 并按固定大小输出 JSONL 分块。"
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
        help="可选的分块标签。默认值为 langchain_fixed_<chunk_size>_<chunk_overlap>。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    parser = LangChainPdfParser(
        chunk_config=ChunkConfig(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    )
    output = parser.save_chunks(
        pdf_path=args.input,
        output_path=args.output,
        label=args.label,
    )
    print(f"分块已写入: {output}")


if __name__ == "__main__":
    main()

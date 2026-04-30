import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from .model import Chunk
except ImportError:
    from model import Chunk


HEADER_PATTERN = re.compile(r"^(#{1,6})\s", re.MULTILINE)
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MIN_CHUNK_CHARS = 200
TARGET_CHUNK_CHARS = 800
NOISE_THRESHOLD = 50


class JSONChunker:
    """将提取的 JSON 页面切分为 Markdown 语块。"""

    def __init__(
        self,
        json_paths: str | Path,
        min_chunk_chars: int = MIN_CHUNK_CHARS,
        target_chunk_chars: int = TARGET_CHUNK_CHARS,
    ):
        self.json_paths = Path(json_paths)
        self.min_chunk_chars = min_chunk_chars
        self.target_chunk_chars = target_chunk_chars

    def chunk_all(self) -> list[Chunk]:
        chunks: list[Chunk] = []
        for json_path in self._iter_json_files():
            chunks.extend(self._chunk_json(json_path))
        return chunks

    def _iter_json_files(self) -> list[Path]:
        json_files: list[Path] = []
        for json_dir in sorted(self.json_paths.iterdir()):
            json_files.extend(sorted(json_dir.glob("*.json")))
        return json_files

    def _chunk_json(self, json_path: Path) -> list[Chunk]:
        with open(json_path, encoding="utf-8") as file:
            data = json.load(file)

        doc_meta = data.get("document", {})
        doc_id = doc_meta.get("file_name", json_path.stem)

        chunks: list[Chunk] = []
        for page in data.get("pages", []):
            chunks.extend(self._chunk_page(page, doc_id, doc_meta))
        return chunks

    def _chunk_page(self, page: dict, doc_id: str, doc_meta: dict) -> list[Chunk]:
        segments = self._split_by_headers(page.get("text", ""))
        if not segments:
            return []

        chunks = self._build_chunks(
            segments=segments,
            doc_id=doc_id,
            doc_meta=doc_meta,
            page_index=page.get("page_index"),
            tables=page.get("tables", []),
        )
        merged = self._merge_short(chunks)
        return [chunk for chunk in merged if self._is_substantive(chunk)]

    def _split_by_headers(self, text: str) -> list[str]:
        matches = list(HEADER_PATTERN.finditer(text))
        if not matches:
            stripped = text.strip()
            return [stripped] if stripped else []

        segments: list[str] = []
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            segment = text[start:end].strip()
            if segment:
                segments.append(segment)
        return self._drop_noise_segments(segments)

    def _drop_noise_segments(self, segments: list[str]) -> list[str]:
        cleaned: list[str] = []
        prefix = ""

        for segment in segments:
            body = self._extract_body(segment)
            if len(body) < NOISE_THRESHOLD:
                prefix = f"{prefix}\n\n{segment}".strip() if prefix else segment
                continue

            if prefix:
                cleaned.append(f"{prefix}\n\n{segment}".strip())
                prefix = ""
            else:
                cleaned.append(segment)

        if prefix and cleaned:
            cleaned[-1] = f"{cleaned[-1]}\n\n{prefix}".strip()
        elif prefix:
            cleaned.append(prefix)
        return cleaned

    @staticmethod
    def _extract_body(text: str) -> str:
        lines = []
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("!["):
                continue
            lines.append(stripped)
        return " ".join(lines)

    def _build_chunks(
        self,
        segments: list[str],
        doc_id: str,
        doc_meta: dict,
        page_index: int | None,
        tables: list[dict],
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        table_texts = {table.get("table", "") for table in tables}
        preamble_texts = {table.get("preamble", "") for table in tables}

        for index, segment in enumerate(segments):
            chunk_id = hashlib.sha1(f"{doc_id}-{page_index}-{index}-{segment}".encode()).hexdigest()
            chunks.append(
                Chunk(
                    text=segment,
                    metadata={
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "page_index": page_index,
                        "chunk_type": self._detect_chunk_type(segment, table_texts, preamble_texts),
                        "title": doc_meta.get("title"),
                        "author": doc_meta.get("author"),
                        "company_name": doc_meta.get("company_name"),
                        "source": doc_meta.get("source"),
                    },
                )
            )
        return chunks

    def _detect_chunk_type(self, text: str, table_texts: set[str], preamble_texts: set[str]) -> str:
        for table_text in table_texts:
            if table_text and table_text in text:
                return "table"
        for preamble_text in preamble_texts:
            if preamble_text and preamble_text in text:
                return "table"
        return "text"

    def _merge_short(self, chunks: list[Chunk]) -> list[Chunk]:
        if not chunks:
            return chunks

        merged: list[Chunk] = []
        pending: list[Chunk] = []

        for chunk in chunks:
            pending.append(chunk)
            if sum(len(item.text) for item in pending) >= self.min_chunk_chars:
                merged.append(self._join(pending))
                pending.clear()

        if pending:
            if merged and len(pending[0].text) < self.min_chunk_chars:
                merged[-1] = self._join([merged[-1], *pending])
            else:
                merged.append(self._join(pending))

        return merged

    @staticmethod
    def _is_substantive(chunk: Chunk) -> bool:
        body = JSONChunker._extract_body(chunk.text)
        if chunk.metadata.get("chunk_type") == "table":
            return len(body) >= 10
        return len(body) >= NOISE_THRESHOLD

    @staticmethod
    def _join(chunks: list[Chunk]) -> Chunk:
        if len(chunks) == 1:
            return chunks[0]

        metadata = chunks[0].metadata.copy()
        chunk_types = {chunk.metadata.get("chunk_type", "text") for chunk in chunks}
        metadata["chunk_type"] = "table" if "table" in chunk_types else "text"
        return Chunk(text="\n\n".join(chunk.text for chunk in chunks), metadata=metadata)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将提取的 JSON 页面切分为语块。")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    chunks = JSONChunker(json_paths=args.data_dir).chunk_all()
    if not chunks:
        print("No chunks found.")
        return

    lengths = [len(chunk.text) for chunk in chunks]
    types: dict[str, int] = {}
    for chunk in chunks:
        chunk_type = chunk.metadata.get("chunk_type", "text")
        types[chunk_type] = types.get(chunk_type, 0) + 1

    print(f"Documents: {len({chunk.metadata['doc_id'] for chunk in chunks})}")
    print(f"Chunks: {len(chunks)}")
    print(f"Chunk types: {types}")
    print(f"Length: min={min(lengths)} max={max(lengths)} avg={sum(lengths) // len(lengths)}")


if __name__ == "__main__":
    main()

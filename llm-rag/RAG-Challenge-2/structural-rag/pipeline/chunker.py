import json
import re
from pathlib import Path

from model import Chunk

HEADER_PATTERN = re.compile(r"^(#{1,6})\s", re.MULTILINE)
IMAGE_REF_PATTERN = re.compile(r"^!\[.*\]\(.+\)$", re.MULTILINE)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MIN_CHUNK_CHARS = 200
TARGET_CHUNK_CHARS = 800
NOISE_THRESHOLD = 50


class JSONChunker:
    """读取SON 文件，基于 Markdown 标题边界（``#`` 到 ``######``）进行拆分。相邻且短于
    过短的块会被合并，以避免产生。包含表格标记或，表格前导文本的块会被标记为 ``chunk_type: "table"``
    """

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
        """处理所有 JSON 文件，并返回chunk lis"""
        all_chunks: list[Chunk] = []
        for json_path in self._iter_json_files():
            all_chunks.extend(self._chunk_json(json_path))
        return all_chunks

    def _iter_json_files(self) -> list[Path]:
        """返回排序后的 JSON 文件列表"""
        json_files = []
        for json_path in sorted(self.json_paths.iterdir()):
            for file in json_path.glob("*.json"):
                json_files.append(file)
        return json_files

    def _chunk_json(self, json_path: Path) -> list[Chunk]:
        with open(json_path, encoding="utf-8") as fh:
            data = json.load(fh)

        doc_meta = data.get("document", {})
        doc_id = doc_meta.get("file_name", json_path.stem)
        pages = data.get("pages", [])

        chunks: list[Chunk] = []
        for page in pages:
            page_chunks = self._chunk_page(page, doc_id, doc_meta)
            chunks.extend(page_chunks)
        return chunks

    def _chunk_page(self, page: dict, doc_id: str, doc_meta: dict) -> list[Chunk]:
        page_index = page.get("page_index")
        text = page.get("text", "")
        tables = page.get("tables", [])

        segments = self._split_by_headers(text)
        if not segments:
            return []

        chunks = self._build_chunks(segments, doc_id, doc_meta, page_index, tables)
        merged = self._merge_short(chunks)
        return [c for c in merged if self._is_substantive(c)]

    def _split_by_headers(self, text: str) -> list[str]:
        """正则表达式标题层级拆分文本，即#、##、###等。返回拆分后的文本片段列表。"""
        matches = list(HEADER_PATTERN.finditer(text))
        if not matches:
            stripped = text.strip()
            return [stripped] if stripped else []

        segments: list[str] = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            segment = text[start:end].strip()
            if segment:
                segments.append(segment)
        return self._drop_noise_segments(segments)

    def _drop_noise_segments(self, segments: list[str]) -> list[str]:
        """合并孤儿文本。"""
        cleaned: list[str] = []
        carry: str = ""
        for seg in segments:
            body = self._extract_body(seg)
            if len(body) < NOISE_THRESHOLD:
                carry = (carry + "\n\n" + seg).strip() if carry else seg
            else:
                if carry:
                    cleaned.append((carry + "\n\n" + seg).strip())
                    carry = ""
                else:
                    cleaned.append(seg)
        if carry and cleaned:
            cleaned[-1] = (cleaned[-1] + "\n\n" + carry).strip()
        elif carry:
            cleaned.append(carry)
        return cleaned

    @staticmethod
    def _extract_body(text: str) -> str:
        """返回去除标题行和图片引用后的 *text*。"""
        lines = text.split("\n")
        meaningful: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if stripped.startswith("!["):
                continue
            if stripped:
                meaningful.append(stripped)
        return " ".join(meaningful)

    def _build_chunks(
        self,
        segments: list[str],
        doc_id: str,
        doc_meta: dict,
        page_index: int | None,
        tables: list[dict],
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        table_texts = {t.get("table", "") for t in tables}
        preamble_texts = {t.get("preamble", "") for t in tables}

        for segment in segments:
            chunk_type = self._classify(segment, table_texts, preamble_texts)
            chunks.append(
                Chunk(
                    text=segment,
                    metadata={
                        "doc_id": doc_id,
                        "page_index": page_index,
                        "chunk_type": chunk_type,
                        "title": doc_meta.get("title"),
                        "author": doc_meta.get("author"),
                        "source": doc_meta.get("source"),
                    },
                )
            )
        return chunks

    def _classify(self, text: str, table_texts: set[str], preamble_texts: set[str]) -> str:
        """如果 *text* 与任意表格或前导文本相交，则返回 ``"table"``。"""
        for tt in table_texts:
            if tt and tt in text:
                return "table"
        for pt in preamble_texts:
            if pt and pt in text:
                return "table"
        return "text"

    def _merge_short(self, chunks: list[Chunk]) -> list[Chunk]:
        if not chunks:
            return chunks

        merged: list[Chunk] = []
        buffer: list[Chunk] = []

        for chunk in chunks:
            buffer.append(chunk)
            if sum(len(c.text) for c in buffer) >= self.min_chunk_chars:
                merged.append(self._join(buffer))
                buffer.clear()

        if buffer:
            if merged and len(buffer[0].text) < self.min_chunk_chars:
                merged[-1] = self._join([merged[-1]] + buffer)
            else:
                merged.append(self._join(buffer))

        return merged

    @staticmethod
    def _is_substantive(chunk: Chunk) -> bool:
        """丢弃正文文本（不含标题和图片）过短的块。"""
        body = JSONChunker._extract_body(chunk.text)
        # 如果包含表格，或文本足够长，则保留
        if chunk.metadata.get("chunk_type") == "table":
            return len(body) >= 10
        return len(body) >= NOISE_THRESHOLD

    @staticmethod
    def _join(buffer: list[Chunk]) -> Chunk:
        if len(buffer) == 1:
            return buffer[0]
        text = "\n\n".join(c.text for c in buffer)
        meta = buffer[0].metadata.copy()
        types = {c.metadata.get("chunk_type", "text") for c in buffer}
        meta["chunk_type"] = "table" if "table" in types else "text"
        return Chunk(text=text, metadata=meta)


def main():
    """独立运行：读取 data2/ 所有 JSON，给出统计信息。"""
    from ingestion import BM25Ingestor

    chunker = JSONChunker(json_paths=DATA_DIR)
    chunks = chunker.chunk_all()

    lengths = [len(c.text) for c in chunks]
    types: dict[str, int] = {}
    for c in chunks:
        ct = c.metadata.get("chunk_type", "text")
        types[ct] = types.get(ct, 0) + 1

    print(f"文档数: {len({c.metadata['doc_id'] for c in chunks})}")
    print(f"chunk 总数: {len(chunks)}")
    print(f"按类型: {types}")
    print(f"大小范围: min={min(lengths)}  max={max(lengths)}  avg={sum(lengths) // len(lengths)}")

    print("\n=== BM25 快速验证 ===")
    bm25 = BM25Ingestor(DATA_DIR.parent / "pipeline" / "bm25_index")
    bm25.ingest(chunks)
    for q in ("risk factor", "supply chain", "executive compensation"):
        print(f'\n查询: "{q}"')
        for r in bm25.search(q, top_k=2):
            meta = r["metadata"]
            did = meta.get("doc_id", "?")
            pg = meta.get("page_index", "?")
            print(f"  [{did:>12s}:p{pg}] score={r['score']:.2f}  {r['text'][:80]}")


if __name__ == "__main__":
    main()

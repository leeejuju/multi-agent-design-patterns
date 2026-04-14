from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import fitz

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
PAGE_SEPARATOR = "\n\n"
TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+")
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
PAGE_NUMBER_PATTERN = re.compile(
    r"^(page\s+)?\d{1,3}(\s+of\s+\d{1,4})?$",
    re.IGNORECASE,
)
COMPANY_PATTERN = re.compile(
    r"\b(?:limited|ltd\.?|inc\.?|corp\.?|corporation|group|holdings?|plc|llc|pty\.?\s+ltd\.?|co\.?)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ChunkConfig:
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0.")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")


@dataclass(frozen=True, slots=True)
class PageSpan:
    page_no: int
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class ChunkSlice:
    content: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class PdfDocumentData:
    source: Path
    page_texts: list[str]
    full_text: str
    page_spans: list[PageSpan]
    page_count: int
    title: str
    company_name: str


def resolve_pdf_path(pdf_path: str | Path) -> Path:
    source = Path(pdf_path).expanduser().resolve()
    if source.suffix.lower() != ".pdf":
        raise ValueError(f"Only PDF files are supported, got: {source}")
    if not source.exists():
        raise FileNotFoundError(f"PDF file not found: {source}")
    return source


def normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", normalized)
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def estimate_token_count(text: str) -> int:
    return len(TOKEN_PATTERN.findall(text))


def save_jsonl(records: list[dict], output_path: str | Path) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file_obj:
        for record in records:
            file_obj.write(json.dumps(record, ensure_ascii=False) + "\n")
    return output


def load_pdf_metadata(source: Path) -> dict[str, str]:
    with fitz.open(source) as document:
        metadata = document.metadata or {}
    return {key: str(value).strip() for key, value in metadata.items() if value}


def compose_document(page_texts: list[str]) -> tuple[str, list[PageSpan]]:
    full_parts: list[str] = []
    page_spans: list[PageSpan] = []
    cursor = 0

    for index, text in enumerate(page_texts, start=1):
        normalized_page = normalize_text(text)
        if full_parts:
            full_parts.append(PAGE_SEPARATOR)
            cursor += len(PAGE_SEPARATOR)
        start = cursor
        full_parts.append(normalized_page)
        cursor += len(normalized_page)
        page_spans.append(PageSpan(page_no=index, start=start, end=cursor))

    return "".join(full_parts), page_spans


def map_pages_for_span(page_spans: list[PageSpan], start: int, end: int) -> list[int]:
    pages: list[int] = []
    for span in page_spans:
        if end <= span.start:
            continue
        if start >= span.end:
            continue
        pages.append(span.page_no)
    return pages


def trim_span(text: str, start: int, end: int) -> ChunkSlice | None:
    raw = text[start:end]
    if not raw:
        return None
    leading = len(raw) - len(raw.lstrip())
    trailing = len(raw) - len(raw.rstrip())
    trimmed_start = start + leading
    trimmed_end = end - trailing
    if trimmed_end <= trimmed_start:
        return None
    return ChunkSlice(
        content=text[trimmed_start:trimmed_end],
        start=trimmed_start,
        end=trimmed_end,
    )


def make_fixed_chunks(text: str, chunk_config: ChunkConfig) -> list[ChunkSlice]:
    if not text:
        return []

    chunk_slices: list[ChunkSlice] = []
    start = 0
    step = chunk_config.chunk_size - chunk_config.chunk_overlap
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_config.chunk_size, text_length)
        chunk_slice = trim_span(text, start, end)
        if chunk_slice is not None:
            chunk_slices.append(chunk_slice)
        if end >= text_length:
            break
        start += step

    return chunk_slices


def build_chunk_record(
    *,
    doc_id: str,
    chunk_no: int,
    chunk: ChunkSlice,
    document: PdfDocumentData,
    chunk_config: ChunkConfig,
    label: str,
    parser_name: str,
) -> dict:
    return {
        "doc_id": doc_id,
        "chunk_no": chunk_no,
        "content": chunk.content,
        "token_count": estimate_token_count(chunk.content),
        "char_count": len(chunk.content),
        "source": str(document.source),
        "label": label,
        "metadata": {
            "chunk_size": chunk_config.chunk_size,
            "chunk_overlap": chunk_config.chunk_overlap,
            "page_count": document.page_count,
            "pages": map_pages_for_span(document.page_spans, chunk.start, chunk.end),
            "title": document.title,
            "company_name": document.company_name,
            "parser": parser_name,
            "source_file": document.source.name,
        },
    }


def make_doc_id(source: Path) -> str:
    return hashlib.sha256(str(source).encode("utf-8")).hexdigest()[:64]


def extract_document_metadata(source: Path, page_texts: list[str]) -> tuple[str, str]:
    metadata = load_pdf_metadata(source)
    title = extract_title(page_texts, metadata)
    company_name = extract_company_name(page_texts, metadata)
    return title, company_name


def extract_title(page_texts: list[str], metadata: dict[str, str]) -> str:
    first_page_lines = collect_candidate_lines(page_texts[:1], per_page_limit=12)
    non_company_lines = [
        line
        for line in first_page_lines
        if not looks_like_company_name(line)
        and line.lower() not in {"contents", "table of contents"}
    ]

    if non_company_lines:
        if len(non_company_lines) >= 2 and (
            YEAR_PATTERN.search(non_company_lines[1]) or len(non_company_lines[0]) <= 40
        ):
            parts = [non_company_lines[0]]
            for candidate in non_company_lines[1:3]:
                if looks_like_company_name(candidate):
                    break
                if len(" ".join(parts + [candidate])) > 120:
                    break
                parts.append(candidate)
                if YEAR_PATTERN.search(candidate):
                    break
            return " ".join(parts).strip()
        return non_company_lines[0]

    metadata_title = clean_candidate_line(metadata.get("title", ""))
    if is_useful_title(metadata_title):
        return metadata_title
    return ""


def extract_company_name(page_texts: list[str], metadata: dict[str, str]) -> str:
    page_lines = collect_candidate_lines(page_texts[:3], per_page_limit=20)
    for line in page_lines:
        if looks_like_company_name(line):
            return line

    for key in ("author", "subject", "creator", "producer", "title"):
        candidate = clean_candidate_line(metadata.get(key, ""))
        if looks_like_company_name(candidate):
            return candidate

    return ""


def collect_candidate_lines(page_texts: Iterable[str], per_page_limit: int) -> list[str]:
    lines: list[str] = []
    for text in page_texts:
        count = 0
        for raw_line in text.splitlines():
            candidate = clean_candidate_line(raw_line)
            if not candidate or is_noise_line(candidate):
                continue
            lines.append(candidate)
            count += 1
            if count >= per_page_limit:
                break
    return lines


def clean_candidate_line(line: str) -> str:
    candidate = re.sub(r"\s+", " ", line).strip()
    return candidate.strip("|•- ")


def is_noise_line(line: str) -> bool:
    if not line:
        return True
    if len(line) < 2 or len(line) > 140:
        return True
    if PAGE_NUMBER_PATTERN.fullmatch(line):
        return True
    if re.fullmatch(r"[\W_]+", line):
        return True
    if re.fullmatch(r"\d+", line):
        return len(line) <= 2 or YEAR_PATTERN.search(line) is None
    return False


def looks_like_company_name(line: str) -> bool:
    return bool(line and COMPANY_PATTERN.search(line))


def is_useful_title(line: str) -> bool:
    if not line or is_noise_line(line):
        return False
    if looks_like_company_name(line):
        return False
    return True

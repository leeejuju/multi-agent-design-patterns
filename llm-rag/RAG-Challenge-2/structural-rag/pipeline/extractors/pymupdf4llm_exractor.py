import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pymupdf as fitz
import pymupdf4llm as pdf2md
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


# def extract_metadata_with_llm(pdf_path: Path) -> dict:
#     message = [
#         (
#             "system",
#             "请提取以下PDF文档的元信息，包括标题、作者、页数、创建日期等，并以JSON格式返回。",
#         ),
#         ("human", "..."),
#     ]
#     provider = PROVIDERS["dashscope"]
#     llm = ChatOpenAI(
#         model=provider.default_model,
#         base_url=provider.base_url,
#         api_key=os.getenv(provider.api_key_env),
#     )
#     llm.ainvoke(
#         message,
#     )

#     message = []


PIPELINE_DIR = Path(__file__).resolve().parents[1]
if str(PIPELINE_DIR) not in sys.path:
    sys.path.append(str(PIPELINE_DIR))


def extract_pdf_metadata(pdf_path: Path) -> dict:
    doc = fitz.open(str(pdf_path))
    try:
        return {
            **doc.metadata,
            "page_count": doc.page_count,
            "source": str(pdf_path),
            "file_name": pdf_path.name,
        }
    finally:
        doc.close()


def extract_pdf_to_markdown(
    pdf_path: Path,
    output_dir: Path,
    page_batch_size: int = 10,
) -> tuple[Path, str, dict]:
    pdf_output_dir = output_dir / pdf_path.stem
    image_dir = pdf_output_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    document_metadata = extract_pdf_metadata(pdf_path)
    page_count = document_metadata["page_count"]
    pages = []

    for page_range in batched_page_ranges(page_count, page_batch_size):
        raw_chunks = pdf2md.to_markdown(
            str(pdf_path),
            pages=page_range,
            write_images=True,
            image_path=str(image_dir),
            page_chunks=True,
        )
        chunks = normalize_page_chunks(raw_chunks)
        pages.extend(build_page_record(pdf_path, chunk) for chunk in chunks)

    pages.sort(key=lambda page: page["page"] or 0)
    content = "\n\n".join(format_page_markdown(page) for page in pages)
    extraction_metadata = {
        "document": document_metadata,
        "pages": pages,
    }
    return pdf_path, content, extraction_metadata


def batched_page_ranges(page_count: int, page_batch_size: int) -> list[list[int]]:
    if page_batch_size <= 0:
        raise ValueError("page_batch_size must be greater than 0")
    return [
        list(range(start, min(start + page_batch_size, page_count)))
        for start in range(0, page_count, page_batch_size)
    ]


def normalize_page_chunks(raw_chunks: str | dict | list) -> list[dict]:
    if isinstance(raw_chunks, str):
        raw_chunks = json.loads(raw_chunks)

    if isinstance(raw_chunks, dict):
        if isinstance(raw_chunks.get("pages"), list):
            return raw_chunks["pages"]
        if isinstance(raw_chunks.get("chunks"), list):
            return raw_chunks["chunks"]
        if isinstance(raw_chunks.get("page_chunks"), list):
            return raw_chunks["page_chunks"]
        return [raw_chunks]

    return raw_chunks


def build_page_record(pdf_path: Path, chunk: dict) -> dict:
    metadata = chunk.get("metadata", {})
    page = metadata.get("page") or metadata.get("page_number")
    text = chunk.get("text", "")
    page_record = {key: value for key, value in chunk.items() if key not in {"metadata", "text"}}
    if "page_boxes" in page_record:
        page_record["page_boxes"] = attach_box_text(page_record["page_boxes"], text)

    return {
        **page_record,
        "page": page,
        "source": str(pdf_path),
        "text": text,
        "metadata": {
            **metadata,
            "page": page,
            "source": str(pdf_path),
            "file_name": pdf_path.name,
        },
    }


def attach_box_text(page_boxes: list[dict], text: str) -> list[dict]:
    boxes = []
    for box in page_boxes:
        box_text = extract_text_by_pos(text, box.get("pos"))
        boxes.append(
            {
                **box,
                "text": box_text,
            }
        )
    return boxes


def extract_text_by_pos(text: str, pos: list[int] | None) -> str:
    if not pos or len(pos) != 2:
        return ""
    start, end = pos
    return text[start:end].strip()


def format_page_markdown(page: dict) -> str:
    page_number = page["page"]
    metadata = json.dumps(page["metadata"], ensure_ascii=False, sort_keys=True, default=str)
    return f"<!-- page: {page_number} -->\n<!-- page_metadata: {metadata} -->\n\n{page['text']}"


def write_markdown(output_dir: Path, pdf_path: Path, content: str) -> Path:
    pdf_output_dir = output_dir / pdf_path.stem
    pdf_output_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = pdf_output_dir / f"{pdf_path.stem}.md"
    markdown_path.write_text(content, encoding="utf-8")
    return markdown_path


def write_extraction_metadata(output_dir: Path, pdf_path: Path, metadata: dict) -> Path:
    pdf_output_dir = output_dir / pdf_path.stem
    pdf_output_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = pdf_output_dir / f"{pdf_path.stem}.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return metadata_path


class PyMuPDF4LLMExtractor:
    def __init__(
        self,
        input_dir: list[str] | str | None = None,
        output_dir: str | None = None,
        page_batch_size: int = 10,
    ):
        self.input_dir = input_dir
        self.output_dir = Path(output_dir).expanduser().resolve()
        self.page_batch_size = page_batch_size

    def extract_pdf_parallel(self, max_workers: int = 4) -> None:
        pdf_paths = self.resolve_pdf_paths()
        output_dirs = [self.output_dir] * len(pdf_paths)
        page_batch_sizes = [self.page_batch_size] * len(pdf_paths)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(
                extract_pdf_to_markdown, pdf_paths, output_dirs, page_batch_sizes
            )

            for pdf_path, content, metadata in tqdm(results, total=len(pdf_paths)):
                write_markdown(self.output_dir, pdf_path, content)
                write_extraction_metadata(self.output_dir, pdf_path, metadata)

    def resolve_pdf_paths(self) -> list[Path]:
        if self.input_dir is None:
            return []

        if isinstance(self.input_dir, str):
            path = Path(self.input_dir).expanduser().resolve()

            if path.exists() and path.is_dir():
                return sorted(path.glob("*.pdf"))
            return [self.resolve_pdf_path(path)]

        return [self.resolve_pdf_path(path) for path in self.input_dir]

    def resolve_pdf_path(self, pdf_path: str | Path) -> Path:
        pdf_path = Path(pdf_path).expanduser().resolve()

        if not pdf_path.exists():
            raise FileNotFoundError("文件不存在")

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError("无效文件，请传入 PDF")

        return pdf_path


if __name__ == "__main__":
    extractor = PyMuPDF4LLMExtractor(
        input_dir=r"E:\1_LLM_PROJECT\multi-agent-design-patterns\llm-rag\RAG-Data\IIya-rice",
        output_dir=(
            r"E:\1_LLM_PROJECT\multi-agent-design-patterns"
            r"\llm-rag\RAG-Challenge-2\structural-rag\data2"
        ),
    )
    extractor.extract_pdf_parallel()

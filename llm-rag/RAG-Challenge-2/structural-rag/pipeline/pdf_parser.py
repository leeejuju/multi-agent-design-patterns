import json
import re
import csv
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pymupdf as fitz
import pymupdf4llm as pdf2md
from dotenv import load_dotenv

load_dotenv()


PIPELINE_DIR = Path(__file__).resolve().parents[1]
if str(PIPELINE_DIR) not in sys.path:
    sys.path.append(str(PIPELINE_DIR))


TABLE_ROW_PATTERN = re.compile(r"^\|.+\|")


class JsonExtractor:
    def __init__(
        self,
        metadata: dict | None = None,
        backup_dir: str | None = None,
        table_context_lines: int = 5,
    ):
        self.metadata = metadata
        self.backup_dir = backup_dir
        self.table_context_lines = table_context_lines

    def extract_pages(self, pdf_path: Path, raw_chunks: str | dict | list) -> list[dict]:
        chunks = raw_chunks
        return [self.build_page_record(pdf_path, chunk) for chunk in chunks]

    def build_extraction_metadata(self, document_metadata: dict, pages: list[dict]) -> dict:
        return {
            "document": document_metadata,
            "pages": pages,
        }
    

    def detect_tables(self, text: str) -> list[dict]:
        lines = text.split("\n")
        table_blocks = []
        i = 0

        while i < len(lines):
            if not TABLE_ROW_PATTERN.match(lines[i]):
                i += 1
                continue

            table_start = i
            while i < len(lines) and (
                TABLE_ROW_PATTERN.match(lines[i]) or lines[i].strip() == ""
            ):
                if lines[i].strip() == "" and i + 1 < len(lines) and not TABLE_ROW_PATTERN.match(lines[i + 1]):
                    break
                i += 1
            table_end = i
            table_lines = lines[table_start:table_end]

            preamble_start = max(0, table_start - self.table_context_lines)
            preamble_lines = lines[preamble_start:table_start]

            table_blocks.append({
                "preamble": "\n".join(preamble_lines).strip(),
                "table": "\n".join(table_lines).strip(),
                "line_start": table_start,
                "line_end": table_end,
            })

        return table_blocks

    def build_page_record(self, pdf_path: Path, chunk: dict) -> dict:
        metadata = chunk.get("metadata", {})
        document_metadata = self.metadata.get(pdf_path.stem, {})
        
        page = metadata.get("page") or metadata.get("page_number")
        text = chunk.get("text", "")
        page_record = {
            key: value
            for key, value in chunk.items()
            if key not in {"metadata", "text", "page_boxes"}
        }

        tables = self.detect_tables(text)

        return {
            **page_record,
            "page": page,
            "source": str(pdf_path),
            "text": text,
            "tables": tables,
        }

    def write_extraction_metadata(self, output_dir: Path, pdf_path: Path, metadata: dict) -> Path:
        pdf_output_dir = output_dir / pdf_path.stem
        pdf_output_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = pdf_output_dir / f"{pdf_path.stem}.json"
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        return metadata_path

    def extract_report(self, extract_result: dict | None = None):
        pass


class PyMuPDF4LLMExtractor:
    def __init__(
        self,
        input_dir: list[str] | str | None = None,
        output_dir: str | None = None,
        page_batch_size: int = 10,
        csv_path: str | Path | None = None,
        json_extractor: JsonExtractor | None = None,
    ):
        self.input_dir = input_dir
        self.output_dir = Path(output_dir).expanduser().resolve()
        self.page_batch_size = page_batch_size
        self.metadata_dict = {}

        if csv_path:
            self.metadata_dict = self._parse_csv_metadata(csv_path)
        self.json_extractor = json_extractor or JsonExtractor(metadata=self.metadata_dict)
    
    @staticmethod
    def _parse_csv_metadata(csv_path: Path) -> dict:
        company_dict = {}
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                company_dict[row["sha1"]] = {
                    "company_name": row.get('company_name')
                }
        return company_dict
            
   

    def extract_pdf_metadata(self, pdf_path: Path) -> dict:
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
        self,
        pdf_path: Path,
        output_dir: Path,
        page_batch_size: int = 10,
    ) -> tuple[Path, str, dict]:
        pdf_output_dir = output_dir / pdf_path.stem
        image_dir = pdf_output_dir
        image_dir.mkdir(parents=True, exist_ok=True)

        document_metadata = self.extract_pdf_metadata(pdf_path)
        page_count = document_metadata["page_count"]
        pages = []

        for page_range in self.batched_page_ranges(page_count, page_batch_size):
            raw_chunks = pdf2md.to_markdown(
                str(pdf_path),
                pages=page_range,
                write_images=True,
                page_chunks=True,
                image_path=str(image_dir),
            )
            pages.extend(self.json_extractor.extract_pages(pdf_path, raw_chunks))

        pages.sort(key=lambda page: page["page"] or 0)
        content = "\n\n".join(self.format_page_markdown(page) for page in pages)
        extraction_metadata = self.json_extractor.build_extraction_metadata(
            document_metadata, pages
        )
        return pdf_path, content, extraction_metadata

    def format_page_markdown(self, page: dict) -> str:
        return page["text"]

    def write_markdown(self, output_dir: Path, pdf_path: Path, content: str) -> Path:
        pdf_output_dir = output_dir / pdf_path.stem
        pdf_output_dir.mkdir(parents=True, exist_ok=True)

        markdown_path = pdf_output_dir / f"{pdf_path.stem}.md"
        markdown_path.write_text(content, encoding="utf-8")
        return markdown_path

    def batched_page_ranges(self, page_count: int, page_batch_size: int) -> list[list[int]]:
        return [
            list(range(start, min(start + page_batch_size, page_count)))
            for start in range(0, page_count, page_batch_size)
        ]

    def extract_pdf_parallel(self, max_workers: int = 4) -> None:
        pdf_paths = self.resolve_pdf_paths()
        output_dirs = [self.output_dir] * len(pdf_paths)
        page_batch_sizes = [self.page_batch_size] * len(pdf_paths)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(
                self.extract_pdf_to_markdown,
                pdf_paths,
                output_dirs,
                page_batch_sizes,
            )

            for pdf_path, content, metadata in results:
                self.write_markdown(self.output_dir, pdf_path, content)
                self.json_extractor.write_extraction_metadata(self.output_dir, pdf_path, metadata)

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
            raise ValueError("无效文件，请提供PDF文件")

        return pdf_path


if __name__ == "__main__":
    extractor = PyMuPDF4LLMExtractor(
        input_dir=r"E:\1_LLM_PROJECT\multi-agent-design-patterns\llm-rag\RAG-Data\IIya-rice",
        output_dir=(
            r"E:\1_LLM_PROJECT\multi-agent-design-patterns"
            r"\llm-rag\RAG-Challenge-2\structural-rag\data2"
        ),
        csv_path=r"E:\1_LLM_PROJECT\multi-agent-design-patterns\llm-rag\RAG-Challenge-2\structural-rag\data.csv",
    )
    extractor.extract_pdf_parallel()

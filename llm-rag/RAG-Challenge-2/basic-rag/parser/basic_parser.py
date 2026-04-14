from __future__ import annotations

import argparse

import fitz

from parser_common import (
    ChunkConfig,
    PdfDocumentData,
    build_chunk_record,
    compose_document,
    extract_document_metadata,
    make_doc_id,
    make_fixed_chunks,
    resolve_pdf_path,
    save_jsonl,
)


class BasicParser:
    parser_name = "pymupdf_raw_text"
    label_prefix = "raw_fixed"

    def __init__(self, chunk_config: ChunkConfig | None = None) -> None:
        self.chunk_config = chunk_config or ChunkConfig()

    def extract_page_texts(self, pdf_path: str) -> tuple:
        source = resolve_pdf_path(pdf_path)
        with fitz.open(source) as document:
            page_texts = [page.get_text("text") or "" for page in document]
        return source, page_texts

    def extract_document(self, pdf_path: str) -> PdfDocumentData:
        source, page_texts = self.extract_page_texts(pdf_path)
        full_text, page_spans = compose_document(page_texts)
        title, company_name = extract_document_metadata(source, page_texts)
        return PdfDocumentData(
            source=source,
            page_texts=page_texts,
            full_text=full_text,
            page_spans=page_spans,
            page_count=len(page_texts),
            title=title,
            company_name=company_name,
        )

    def build_chunks(self, pdf_path: str, *, label: str | None = None) -> list[dict]:
        document = self.extract_document(pdf_path)
        chunk_slices = make_fixed_chunks(document.full_text, self.chunk_config)
        chunk_label = label or self._default_label()
        doc_id = make_doc_id(document.source)
        return [
            build_chunk_record(
                doc_id=doc_id,
                chunk_no=index,
                chunk=chunk,
                document=document,
                chunk_config=self.chunk_config,
                label=chunk_label,
                parser_name=self.parser_name,
            )
            for index, chunk in enumerate(chunk_slices)
        ]

    def save_chunks(
        self,
        pdf_path: str,
        output_path: str,
        *,
        label: str | None = None,
    ):
        return save_jsonl(self.build_chunks(pdf_path=pdf_path, label=label), output_path)

    def _default_label(self) -> str:
        return f"{self.label_prefix}_{self.chunk_config.chunk_size}_{self.chunk_config.chunk_overlap}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract raw PDF text and write fixed-size JSONL chunks."
    )
    parser.add_argument("--input", required=True, help="Path to the PDF file.")
    parser.add_argument("--output", required=True, help="Path to the JSONL output file.")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Fixed chunk size. Default: 1000.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Fixed chunk overlap. Default: 200.",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Optional chunk label. Defaults to raw_fixed_<chunk_size>_<chunk_overlap>.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    parser = BasicParser(
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
    print(f"Chunks written to: {output}")


if __name__ == "__main__":
    main()

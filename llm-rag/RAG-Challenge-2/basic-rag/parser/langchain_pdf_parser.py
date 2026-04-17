from __future__ import annotations

import argparse

from parser_common import (
    ChunkConfig,
    ChunkSlice,
    PdfDocumentData,
    build_chunk_record,
    compose_document,
    extract_document_metadata,
    make_doc_id,
    resolve_pdf_path,
    save_json,
)


class LangChainPdfParser:
    parser_name = "langchain_pymupdf_recursive"
    label_prefix = "langchain_recursive"

    def __init__(self, chunk_config: ChunkConfig | None = None) -> None:
        self.chunk_config = chunk_config or ChunkConfig()

    def extract_page_texts(self, pdf_path: str) -> tuple:
        source = resolve_pdf_path(pdf_path)

        try:
            from langchain_community.document_loaders import PyMuPDFLoader
        except ImportError as exc:
            raise ImportError(
                "langchain-community is required for LangChain PDF parsing. "
                "Install it with `uv add langchain-community`."
            ) from exc

        loader = PyMuPDFLoader(str(source))
        documents = loader.load()
        page_texts = [doc.page_content or "" for doc in documents]
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

    def split_document(self, document: PdfDocumentData) -> list[ChunkSlice]:
        if not document.full_text:
            return []

        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError as exc:
            raise ImportError(
                "langchain-text-splitters is required for RecursiveCharacterTextSplitter. "
                "Install it with `uv add langchain-text-splitters`."
            ) from exc

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_config.chunk_size,
            chunk_overlap=self.chunk_config.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            add_start_index=True,
        )
        split_documents = splitter.create_documents([document.full_text], metadatas=[{}])

        chunk_slices: list[ChunkSlice] = []
        for doc in split_documents:
            content = doc.page_content
            if not content:
                continue
            start = int(doc.metadata.get("start_index", -1))
            if start < 0:
                continue
            chunk_slices.append(
                ChunkSlice(
                    content=content,
                    start=start,
                    end=start + len(content),
                )
            )
        return chunk_slices

    def build_chunks(self, pdf_path: str, *, label: str | None = None) -> list[dict]:
        document = self.extract_document(pdf_path)
        chunk_slices = self.split_document(document)
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
        return save_json(self.build_chunks(pdf_path=pdf_path, label=label), output_path)

    def _default_label(self) -> str:
        return (
            f"{self.label_prefix}_{self.chunk_config.chunk_size}_{self.chunk_config.chunk_overlap}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse PDF files with LangChain and write recursive JSON chunks."
    )
    parser.add_argument("--input", required=True, help="Path to the PDF file.")
    parser.add_argument("--output", required=True, help="Path to the JSON output file.")
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
        help="Optional chunk label. Defaults to langchain_recursive_<chunk_size>_<chunk_overlap>.",
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
    print(f"Chunks written to: {output}")


if __name__ == "__main__":
    main()

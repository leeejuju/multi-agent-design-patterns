from __future__ import annotations

import argparse
from collections.abc import Iterable

import fitz
import httpx

from parser_common import (
    ChunkConfig,
    PdfDocumentData,
    build_chunk_record,
    compose_document,
    extract_document_metadata,
    make_doc_id,
    make_fixed_chunks,
    resolve_pdf_path,
    save_json,
)


class PaddleOCRParser:
    parser_name = "paddleocr_api_raw_text"
    label_prefix = "paddleocr_fixed"

    def __init__(
        self,
        *,
        ocr_api_url: str,
        ocr_api_headers: dict[str, str] | None = None,
        timeout: float = 60.0,
        dpi: int = 144,
        chunk_config: ChunkConfig | None = None,
    ) -> None:
        self.ocr_api_url = ocr_api_url
        self.ocr_api_headers = ocr_api_headers or {}
        self.timeout = timeout
        self.dpi = dpi
        self.chunk_config = chunk_config or ChunkConfig()

    def extract_page_texts(self, pdf_path: str) -> tuple:
        source = resolve_pdf_path(pdf_path)
        page_texts: list[str] = []

        with fitz.open(source) as document, httpx.Client(timeout=self.timeout) as client:
            for page_index, page in enumerate(document, start=1):
                pixmap = page.get_pixmap(dpi=self.dpi, alpha=False)
                image_bytes = pixmap.tobytes("png")
                page_texts.append(self._ocr_page(client, image_bytes, page_index))

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
        return save_json(self.build_chunks(pdf_path=pdf_path, label=label), output_path)

    def _ocr_page(
        self,
        client: httpx.Client,
        image_bytes: bytes,
        page_no: int,
    ) -> str:
        response = client.post(
            self.ocr_api_url,
            headers=self.ocr_api_headers,
            files={"file": (f"page-{page_no}.png", image_bytes, "image/png")},
        )
        response.raise_for_status()

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"OCR API returned non-JSON response for page {page_no}."
            ) from exc

        text = self._extract_text_from_payload(payload)
        if not text:
            raise RuntimeError(f"OCR API returned no text for page {page_no}.")
        return text

    def _extract_text_from_payload(self, payload) -> str:
        fragments = [fragment.strip() for fragment in self._collect_text_fragments(payload)]
        fragments = [fragment for fragment in fragments if fragment]
        return "\n".join(fragments).strip()

    def _collect_text_fragments(self, value) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, dict):
            for key in (
                "text",
                "ocr_text",
                "page_text",
                "content",
                "rec_text",
                "transcription",
            ):
                if key in value and isinstance(value[key], str):
                    return [value[key]]

            fragments: list[str] = []
            for nested_key in (
                "data",
                "result",
                "results",
                "ocr_result",
                "ocr_results",
                "pages",
                "items",
                "texts",
                "words",
            ):
                if nested_key in value:
                    fragments.extend(self._collect_text_fragments(value[nested_key]))
            return fragments

        if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
            fragments: list[str] = []
            for item in value:
                fragments.extend(self._collect_text_fragments(item))
            return fragments

        return []

    def _default_label(self) -> str:
        return f"{self.label_prefix}_{self.chunk_config.chunk_size}_{self.chunk_config.chunk_overlap}"


def parse_headers(values: list[str] | None) -> dict[str, str]:
    if not values:
        return {}

    headers: dict[str, str] = {}
    for value in values:
        if ":" not in value:
            raise ValueError(f"Invalid header format: {value}")
        name, header_value = value.split(":", 1)
        headers[name.strip()] = header_value.strip()
    return headers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render PDF pages, call a PaddleOCR-compatible HTTP API, and write JSON chunks."
    )
    parser.add_argument("--input", required=True, help="Path to the PDF file.")
    parser.add_argument("--output", required=True, help="Path to the JSON output file.")
    parser.add_argument("--ocr-api-url", required=True, help="PaddleOCR-compatible API URL.")
    parser.add_argument(
        "--ocr-api-header",
        action="append",
        default=[],
        help='Optional HTTP header, e.g. "Authorization: Bearer <token>". Repeat as needed.',
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="HTTP timeout in seconds. Default: 60.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=144,
        help="PDF render DPI before OCR. Default: 144.",
    )
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
        help="Optional chunk label. Defaults to paddleocr_fixed_<chunk_size>_<chunk_overlap>.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    parser = PaddleOCRParser(
        ocr_api_url=args.ocr_api_url,
        ocr_api_headers=parse_headers(args.ocr_api_header),
        timeout=args.timeout,
        dpi=args.dpi,
        chunk_config=ChunkConfig(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        ),
    )
    output = parser.save_chunks(
        pdf_path=args.input,
        output_path=args.output,
        label=args.label,
    )
    print(f"Chunks written to: {output}")


if __name__ == "__main__":
    main()

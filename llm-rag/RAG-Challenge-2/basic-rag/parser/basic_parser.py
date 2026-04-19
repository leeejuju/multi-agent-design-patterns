import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

import fitz

CONTENT_PATTERN = re.compile(
    r"[^A-Za-z0-9\u4e00-\u9fff\s.,;:!?()%$+\-*/=<>@#&'\"，。；：！？（）￥]"
)
SEPARATOR_PATTERN = re.compile(r"[-_.=]{4,}")
SPACE_PATTERN = re.compile(r"\s+")


def clean_content(content: str) -> str:
    content = SEPARATOR_PATTERN.sub(" ", content)
    content = CONTENT_PATTERN.sub(" ", content)
    return SPACE_PATTERN.sub(" ", content).strip()


@dataclass(frozen=True)
class ChunkConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 200


class BasicParser:
    parser_name = "basic_parser"
    label_prefix = "raw_fixed"

    def __init__(self) -> None:
        self.chunk_config = ChunkConfig()

    def build_chunk(self, source: str):
        page_dict = []
        doc = fitz.open(source)
        texts = [doc[page].get_text() for page in range(len(doc))]

        doc_id = Path(source).stem
        source = Path(source).stem
        label = Path(source).stem
        for page, text in enumerate(texts):
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
            text = re.sub(r"[ \t]+\n", "\n", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = clean_content(text)

            for i in range(
                0, len(text), self.chunk_config.chunk_size - self.chunk_config.chunk_overlap
            ):
                chunk = text[i : i + self.chunk_config.chunk_size]
                chunk = chunk.strip()
                page_dict.append(
                    {
                        "doc_id": doc_id,
                        "chunk_no": i,
                        "content": chunk,
                        "page": page,
                        "token_count": len(chunk),
                        "char_count": len(chunk),
                        "source": source,
                        "label": label,
                        "metadata": {},
                    }
                )
        return page_dict

    def save_json(self, pdf_path: str, output_path: str):
        page_dict = self.build_chunk(pdf_path)

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(page_dict, f, ensure_ascii=False, indent=4)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="解析 PDF 文本并写入固定大小的 JSON chunk。")
    parser.add_argument("--input", required=True, help="PDF 文件目录")
    parser.add_argument("--output", required=True, help="JSON 输出目录")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="固定 chunk 大小，默认 1000。",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="固定 chunk overlap，默认 200。",
    )
    return parser.parse_args()


def main() -> None:
    import os

    args = parse_args()
    parser = BasicParser()

    for i in os.listdir(args.input):
        pdf_path = os.path.join(args.input, i)
        output_path = os.path.join(args.output, Path(pdf_path).stem + ".json")
        parser.save_json(
            pdf_path=pdf_path,
            output_path=output_path,
        )


if __name__ == "__main__":
    main()

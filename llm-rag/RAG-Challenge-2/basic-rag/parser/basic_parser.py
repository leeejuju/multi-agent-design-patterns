import re
import json
import fitz
import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 200


class BasicParser:
    parser_name = "基础解析器"
    label_prefix = "raw_fixed"

    def __init__(self) -> None:
        self.chunk_config = ChunkConfig()

    def metadata_parser(self, source: str):
        metadata_dict = {}
        doc = fitz.open(source)
        # 定义正则：匹配常见的公司名后缀
        COMPANY_PATTERN = re.compile(
            r"\b(?:limited|ltd\.?|inc\.?|corp\.?|corporation|group|holdings?|plc|llc|pty\.?\s+ltd\.?|co\.?)\b",
            re.IGNORECASE,
        )

        lines = []
        for page in range(2):
            text = doc[page].get_text()
            lines.extend([line.strip() for line in text.splitlines() if line.strip()])

        company_name = ""
        for line in lines:
            if COMPANY_PATTERN.search(line):
                company_name = line
                break

        title = ""
        first_page_lines = [line.strip() for line in doc[0].get_text().splitlines() if line.strip()]
        for line in first_page_lines:
            if COMPANY_PATTERN.search(line):
                continue
            if line.lower() in {"contents", "table of contents"}:
                continue
            if 0 < len(line) < 20 and not re.fullmatch(r"[\W_]+|\d+", line):
                title = line
                break

        metadata_dict["company_name"] = company_name
        metadata_dict["title"] = title
        metadata_dict["page_count"] = len(doc)
        return metadata_dict

    def build_chunk(self, source: str):
        page_dict = []
        doc = fitz.open(source)
        texts = [doc[page].get_text() for page in range(len(doc))]
        for page, text in enumerate(texts):
            # 清理文本，将回车、换行、控制字符等统一或删除
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
            text = re.sub(r"[ \t]+\n", "\n", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = text.strip()

            for i in range(
                0, len(text), self.chunk_config.chunk_size - self.chunk_config.chunk_overlap
            ):
                chunk = text[i : i + self.chunk_config.chunk_size]
                chunk = chunk.strip()
                page_dict.append(
                    {
                        "text": chunk,
                        "page": page,
                    }
                )
        return page_dict

    def save_json(self, pdf_path: str, output_path: str):
        from pathlib import Path

        metadata_dict = self.metadata_parser(pdf_path)
        page_dict = self.build_chunk(pdf_path)
        metadata_dict["pages"] = page_dict

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(metadata_dict, f, ensure_ascii=False, indent=4)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="提取pdf文本并写入固定大小的json文件.")
    parser.add_argument("--input", required=True, help="pdf文件路径")
    parser.add_argument("--output", required=True, help="json文件路径")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="固定chunk为1000.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="固定overlap为200.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    parser = BasicParser()
    parser.save_json(
        pdf_path=args.input,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()

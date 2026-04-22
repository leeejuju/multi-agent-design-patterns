from pathlib import Path
import sys

import pymupdf4llm as pdf2md

PIPELINE_DIR = Path(__file__).resolve().parents[1]
if str(PIPELINE_DIR) not in sys.path:
    sys.path.append(str(PIPELINE_DIR))

from model import Block, Document


class PyMuPDF4LLMExtractor:
    def __init__(
        self,
        input_dir: list[str] | str | None = None,
        output_dir: str | None = None,
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir

    def extract_pdf(self) -> None:
        pdf_paths = self.reslove_pdf_paths()
        for pdf_path in pdf_paths:
            content = pdf2md.to_markdown(str(pdf_path))
            print(content)

    def reslove_pdf_paths(self):
        """
        批量解析PDF路径，后面想改为生成器
        """
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

        if pdf_path.suffix != ".pdf":
            raise ValueError("无效文件，转pdf去")

        return pdf_path


if __name__ == "__main__":
    extractor = PyMuPDF4LLMExtractor(
        input_dir=r"E:\1_LLM_PROJECT\multi-agent-design-patterns\llm-rag\RAG-Data\IIya-rice",
        output_dir="../example/",
    )
    extractor.extract_pdf()

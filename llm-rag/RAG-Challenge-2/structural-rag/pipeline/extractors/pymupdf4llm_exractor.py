import os
import sys
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import pymupdf as fitz
import pymupdf4llm as pdf2md
from tqdm import tqdm
from llm import PROVIDERS
from langchain_openai import ChatOpenAI
load_dotenv()


    
def extract_metadata_with_llm(pdf_path: Path) -> dict:
    pdf = fitz.open(str(pdf_path))
    pdf_name = pdf_path.stem
    pdf_lens = len(pdf)
    message = [
    ("system", "请提取以下PDF文档的元信息，包括但不限于标题、作者、页数、创建日期等，并以JSON格式返回。"),
    ("human", "...")
]
    provider = PROVIDERS["dashscope"]
    llm = ChatOpenAI(
        model=provider.default_model,
        base_url=provider.base_url,
        api_key=os.getenv(provider.api_key_env),
    )
    llm.ainvoke(message, )

    message = []

    
    
PIPELINE_DIR = Path(__file__).resolve().parents[1]
if str(PIPELINE_DIR) not in sys.path:
    sys.path.append(str(PIPELINE_DIR))


def extract_pdf_metadata(pdf_path: Path) -> dict:
    doc = pdf2md.open(str(pdf_path))
    metadata = doc.metadata
    doc.close()
    return metadata


def extract_pdf_to_markdown(pdf_path: Path, output_dir: Path) -> tuple[Path, str]:
    pdf_output_dir = output_dir / pdf_path.stem
    image_dir = pdf_output_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    chunks = pdf2md.to_markdown(
        str(pdf_path),
        write_images=True,
        image_path=str(image_dir),
        page_chunks=True,
    )
    content = "\n\n".join(
        f"<!-- page: {chunk.get('metadata', {}).get('page')} -->\n\n{chunk['text']}"
        for chunk in chunks
    )
    return pdf_path, content


def extract_pdf_to_markdown(pdf_path: Path, output_dir: Path) -> tuple[Path, str]:
    pdf_output_dir = output_dir / pdf_path.stem
    image_dir = pdf_output_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    chunks = pdf2md.to_json(
        str(pdf_path),
        write_images=True,
        image_path=str(image_dir),
        page_chunks=True,
    )
    content = "\n\n".join(
        f"<!-- page: {chunk.get('metadata', {}).get('page')} -->\n\n{chunk['text']}"
        for chunk in chunks
    )
    return pdf_path, content


def write_markdown(output_dir: Path, pdf_path: Path, content: str) -> Path:
    pdf_output_dir = output_dir / pdf_path.stem
    pdf_output_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = pdf_output_dir / f"{pdf_path.stem}.md"
    markdown_path.write_text(content, encoding="utf-8")
    return markdown_path


class PyMuPDF4LLMExtractor:
    def __init__(
        self,
        input_dir: list[str] | str | None = None,
        output_dir: str | None = None,
    ):
        self.input_dir = input_dir
        self.output_dir = Path(output_dir).expanduser().resolve()

    def extract_pdf_parallel(self, max_workers: int = 4) -> None:
        pdf_paths = self.resolve_pdf_paths()
        output_dirs = [self.output_dir] * len(pdf_paths)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(extract_pdf_to_markdown, pdf_paths, output_dirs)

            for pdf_path, content in tqdm(results, total=len(pdf_paths)):
                write_markdown(self.output_dir, pdf_path, content)

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


# if __name__ == "__main__":
#     extractor = PyMuPDF4LLMExtractor(
#         input_dir=r"E:\1_LLM_PROJECT\multi-agent-design-patterns\llm-rag\RAG-Data\IIya-rice",
#         output_dir=r"E:\1_LLM_PROJECT\multi-agent-design-patterns\llm-rag\RAG-Challenge-2\structural-rag\data",
#     )
#     extractor.extract_pdf_parallel()

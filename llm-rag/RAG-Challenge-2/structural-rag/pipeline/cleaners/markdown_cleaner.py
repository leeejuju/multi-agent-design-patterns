import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from tqdm import tqdm

PICTURE_OMITTED_PATTERN = re.compile(
    r"\*\*==> picture \[\d+ x \d+\] intentionally omitted <==\*\*"
)
PAGE_MARKER_PATTERN = re.compile(r"<!-- page:\s*(\d+|None)\s*-->")


def extract_title(content: str) -> str | None:
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def extract_first_page(content: str) -> int | None:
    match = PAGE_MARKER_PATTERN.search(content)
    if match is None or match.group(1) == "None":
        return None
    return int(match.group(1))


def clean_markdown(content: str) -> str:
    content = PICTURE_OMITTED_PATTERN.sub("", content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip() + "\n"


def parse_markdown_file(args: tuple[Path, Path]) -> dict:
    markdown_path, output_dir = args
    content = markdown_path.read_text(encoding="utf-8")
    cleaned_content = clean_markdown(content)

    metadata = {
        "source": str(markdown_path),
        "title": extract_title(cleaned_content),
        "first_page": extract_first_page(cleaned_content),
    }

    output_path = output_dir / markdown_path.parent.name / markdown_path.name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(cleaned_content, encoding="utf-8")

    return {
        "markdown_path": str(output_path),
        "metadata": metadata,
    }


class MarkdownCleaner:
    def __init__(self, markdown_dirs: str, output_dir: str):
        self.markdown_dirs = Path(markdown_dirs).expanduser().resolve()
        self.output_dir = Path(output_dir).expanduser().resolve()

    def run(self, max_workers: int = 4) -> list[dict]:
        markdown_paths = list(self.markdown_dirs.rglob("*.md"))
        tasks = [(markdown_path, self.output_dir) for markdown_path in markdown_paths]

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = list(
                tqdm(
                    executor.map(parse_markdown_file, tasks),
                    total=len(tasks),
                )
            )

        return results


if __name__ == "__main__":
    cleaner = MarkdownCleaner(
        markdown_dirs=r"E:\1_LLM_PROJECT\multi-agent-design-patterns\llm-rag\RAG-Challenge-2\structural-rag\data",
        output_dir=r"E:\1_LLM_PROJECT\multi-agent-design-patterns\llm-rag\RAG-Challenge-2\structural-rag\cleaned_data",
    )
    result = cleaner.run()
    print(f"Cleaned {result} markdown files.")

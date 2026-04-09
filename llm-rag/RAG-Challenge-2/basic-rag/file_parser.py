import fitz
import argparse
import docling_parse


def parse_pdf(file_path: str) -> list[dict]:
    doc = fitz.open(file_path)
    pages_data = []
    for page_num, page in enumerate(doc):
        text = page.get_text("json")
        print("xxxxxxxxxxxxxxxxxxxxxxxxx")
        print(page_num, text)
        print("xxxxxxxxxxxxxxxxxxxxxxxxx")

        pages_data.append(
            {
                "page": page_num + 1,
                "text": text,
            }
        )
    return pages_data


path = r"e:\1_LLM_PROJECT\rag\enterprise-rag-challenge-main\round2\pdfs\1ab89c81bdb49d4bfba2202eeb8e1c93bed414c7.pdf"
parse_pdf(path)

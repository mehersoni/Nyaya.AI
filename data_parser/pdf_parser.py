from pathlib import Path
from typing import List, Dict
import pdfplumber

def extract_pdf_text(pdf_path: Path) -> List[Dict]:
    """
    Extract text from PDF with page number tracking.
    Returns list of page data with page numbers.
    """
    pages_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text()
            if not page_text:
                continue

            cleaned_lines = []
            for line in page_text.splitlines():
                line = " ".join(line.split())
                if line:
                    cleaned_lines.append(line)

            pages_data.append({
                "page_number": page_num,
                "text": "\n".join(cleaned_lines)
            })

    return pages_data

def extract_pdf_text_raw(pdf_path: Path) -> str:
    """
    Legacy function for backward compatibility.
    Returns raw text without page structure.
    """
    pages_data = extract_pdf_text(pdf_path)
    return "\n".join(page["text"] for page in pages_data)

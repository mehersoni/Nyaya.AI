from pathlib import Path
import pdfplumber

def extract_pdf_text(pdf_path: Path) -> str:
    text_blocks = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if not page_text:
                continue

            cleaned_lines = []
            for line in page_text.splitlines():
                line = " ".join(line.split())
                if line:
                    cleaned_lines.append(line)

            text_blocks.append("\n".join(cleaned_lines))

    return "\n".join(text_blocks)

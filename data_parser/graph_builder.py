import re
from pathlib import Path
from typing import List, Dict
from data_parser.pdf_parser import extract_pdf_text


SECTION_START_PATTERN = re.compile(r"^(\d+)\.\s+(.*)")
IGNORE_EXACT_PATTERN = re.compile(
    r"^(ARRANGEMENT OF SECTIONS|SECTIONS|CHAPTER\s+[IVXLC]+)$",
    re.IGNORECASE
)


def is_all_caps_title(line: str) -> bool:
    """
    Detect chapter titles like:
    'CONSUMER PROTECTION COUNCILS.'
    robustly, even with PDF noise.
    """
    cleaned = re.sub(r"[^A-Za-z]", "", line)
    return cleaned.isupper() and len(cleaned) > 5


def extract_sections(pages: List[Dict]) -> List[Dict]:
    sections = []
    current = None

    for page in pages:
        page_number = page["page_number"]
        lines = page["text"].splitlines()

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Ignore structural headers
            if IGNORE_EXACT_PATTERN.match(line):
                continue

            # Ignore chapter titles (robust)
            if is_all_caps_title(line) and not SECTION_START_PATTERN.match(line):
                continue

            match = SECTION_START_PATTERN.match(line)

            if match:
                if current:
                    sections.append(current)

                section_number = match.group(1)
                heading = match.group(2)

                current = {
                    "section_number": section_number,
                    "heading": heading,
                    "text": line,
                    "pages": {page_number}
                }
            else:
                if current:
                    current["text"] += "\n" + line
                    current["pages"].add(page_number)

    if current:
        sections.append(current)

    for s in sections:
        s["pages"] = sorted(s["pages"])

    return sections


if __name__ == "__main__":
    pdf_path = Path("data_parser/source_pdfs/consumer_protection_act_2019.pdf")
    pages = extract_pdf_text(pdf_path)

    sections = extract_sections(pages)

    for s in sections[:3]:
        print("\n" + "=" * 60)
        print(f"Section {s['section_number']}: {s['heading']}")
        print(f"Pages: {s['pages']}")
        print(s["text"][:1200])

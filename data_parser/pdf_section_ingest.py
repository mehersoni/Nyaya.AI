import re
from pathlib import Path
from data_parser.pdf_parser import extract_pdf_text

# Matches: "3. Central Consumer Protection Council."
SECTION_RE = re.compile(
    r"^(\d{1,3})\.\s+(?!The\b)[A-Z][A-Za-z ,'-]+\.?$"
)

CHAPTER_RE = re.compile(r"^CHAPTER\s+([IVXLC]+)", re.IGNORECASE)

def extract_sections_from_pdf(pdf_path: Path):
    raw_text = extract_pdf_text(pdf_path)

    # IMPORTANT: restore line structure
    lines = raw_text.split("\n")

    sections = []
    current_section = None
    current_chapter = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect chapter
        chap_match = CHAPTER_RE.match(line)
        if chap_match:
            roman = chap_match.group(1)
            current_chapter = f"CPA_2019_CH{roman}"
            continue

        # Detect section start ONLY at line start
        sec_match = SECTION_RE.match(line)
        if sec_match:
            if current_section:
                sections.append(current_section)

            number = sec_match.group(1)
            current_section = {
                "section_id": f"CPA_2019_S{number}",
                "act": "Consumer Protection Act, 2019",
                "section_number": number,
                "text": line,
                "chapter": current_chapter
            }
            continue

        # Accumulate section body
        if current_section:
            current_section["text"] += " " + line

    if current_section:
        sections.append(current_section)

    return sections

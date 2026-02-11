import re
from pathlib import Path


DEFINITION_START = re.compile(r'^\(\d+\)\s+"([^"]+)"\s+means\s+(.*)', re.IGNORECASE)
SUBCLAUSE = re.compile(r'^\([ivx]+\)|^\([a-z]+\)', re.IGNORECASE)


def extract_definitions(section_text: str):
    """
    Extract definition candidates from Section 2 text.
    Returns a list of {term, definition}.
    """
    definitions = []
    current = None

    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = DEFINITION_START.match(line)

        if match:
            if current:
                definitions.append(current)

            term = match.group(1).strip()
            definition = match.group(2).strip()

            current = {
                "term": term,
                "definition": definition
            }
        else:
            if current:
                # continuation lines (sub-clauses etc.)
                if SUBCLAUSE.match(line) or not line.startswith("("):
                    current["definition"] += " " + line

    if current:
        definitions.append(current)

    return definitions


if __name__ == "__main__":
    # TEMP: paste Section 2 text here for now
    SECTION_2_TEXT = Path("data_parser/section2_raw.txt").read_text(encoding="utf-8")

    defs = extract_definitions(SECTION_2_TEXT)

    for d in defs:
        print("\n---")
        print(f"TERM: {d['term']}")
        print(f"DEF: {d['definition'][:400]}...")

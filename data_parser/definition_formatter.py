import re
from pathlib import Path
import json


DEFINITION_START = re.compile(r'^\(\d+\)\s+"([^"]+)"\s+means\s+(.*)', re.IGNORECASE)
SUBCLAUSE = re.compile(r'^\([ivx]+\)|^\([a-z]+\)', re.IGNORECASE)


def clean_text(text: str) -> str:
    text = text.replace("---", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_and_format(section_text: str):
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

            current = {
                "term": match.group(1).strip(),
                "definition": clean_text(match.group(2)),
                "defined_in": "CPA_2019_S2"
            }
        else:
            if current:
                if SUBCLAUSE.match(line) or not line.startswith("("):
                    current["definition"] += " " + clean_text(line)

    if current:
        definitions.append(current)

    return definitions


if __name__ == "__main__":
    raw_text = Path("data_parser/section2_raw.txt").read_text(encoding="utf-8")

    defs = extract_and_format(raw_text)

    print("\n### DEFINITIONS (paste into definitions.data.json)\n")
    print(json.dumps(defs, indent=2, ensure_ascii=False))

    print("\n### DEFINES EDGES (paste into defines.data.json)\n")
    edges = [{"section": "CPA_2019_S2", "term": d["term"]} for d in defs]
    print(json.dumps(edges, indent=2, ensure_ascii=False))

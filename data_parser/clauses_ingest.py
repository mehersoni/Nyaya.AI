from pathlib import Path
import json
from data_parser.clause_parser import parse_clauses


def _write(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ingest_clauses(root: Path):
    clauses, edges = parse_clauses(root)

    _write(root / "knowledge_graph/nodes/clauses.data.json", clauses)
    _write(root / "knowledge_graph/edges/contains_clause.data.json", edges)

    return len(clauses), len(edges)


if __name__ == "__main__":
    root = Path(".")
    c, e = ingest_clauses(root)
    print(f"Clauses written: {c}")
    print(f"Edges written: {e}")

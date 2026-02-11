import json
from pathlib import Path
from jsonschema import validate, ValidationError


class SchemaValidationError(Exception):
    pass


class ReferentialIntegrityError(Exception):
    pass


def _load(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_file(data_path: Path, schema_path: Path):
    data = _load(data_path)
    schema = _load(schema_path)

    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise SchemaValidationError(
            f"{data_path.name} failed schema validation: {e.message}"
        )


def _collect_section_ids(root: Path):
    sections = _load(root / "knowledge_graph/nodes/sections.data.json")
    return {s["section_id"] for s in sections}


def validate_referential_integrity(root: Path):
    section_ids = _collect_section_ids(root)

    # ---- definitions ----
    definitions = _load(root / "knowledge_graph/nodes/definitions.data.json")
    for d in definitions:
        if d["defined_in"] not in section_ids:
            raise ReferentialIntegrityError(
                f"Definition '{d['term']}' refers to unknown section '{d['defined_in']}'"
            )

    # ---- rights ----
    rights = _load(root / "knowledge_graph/nodes/rights.data.json")
    for r in rights:
        if r["granted_by"] not in section_ids:
            raise ReferentialIntegrityError(
                f"Right '{r['right_id']}' refers to unknown section '{r['granted_by']}'"
            )

    # ---- references edges ----
    references = _load(root / "knowledge_graph/edges/references.data.json")
    for ref in references:
        if ref["from"] not in section_ids or ref["to"] not in section_ids:
            raise ReferentialIntegrityError(f"Invalid reference edge: {ref}")

    # ---- defines edges ----
    defines = _load(root / "knowledge_graph/edges/defines.data.json")
    for d in defines:
        if d["source"] not in section_ids:
            raise ReferentialIntegrityError(
                f"Defines edge refers to unknown section '{d['source']}'"
            )

    # ---- contains edges ----
    contains = _load(root / "knowledge_graph/edges/contains.data.json")
    for c in contains:
        if c["child"] not in section_ids:
            raise ReferentialIntegrityError(
                f"Contains edge refers to unknown child '{c['child']}'"
            )
        
    # ---- contains_clause edges ----
    contains = _load(root / "knowledge_graph/edges/contains.data.json")

    for c in contains:
        if c["parent"] not in section_ids:
            raise ReferentialIntegrityError(
                f"Contains edge refers to unknown parent section '{c['parent']}'"
            )





def validate_knowledge_graph(root: Path):
    # Step 2: schema validation
    pairs = [
    ("knowledge_graph/nodes/sections.data.json", "knowledge_graph/nodes/sections.schema.json"),
    ("knowledge_graph/nodes/definitions.data.json", "knowledge_graph/nodes/definitions.schema.json"),
    ("knowledge_graph/nodes/rights.data.json", "knowledge_graph/nodes/rights.schema.json"),
    ("knowledge_graph/nodes/clauses.data.json", "knowledge_graph/nodes/clauses.schema.json"),
    ("knowledge_graph/edges/references.data.json", "knowledge_graph/edges/references.schema.json"),
    ("knowledge_graph/edges/defines.data.json", "knowledge_graph/edges/defines.schema.json"),
    ("knowledge_graph/edges/contains.data.json", "knowledge_graph/edges/contains.schema.json"),
    ("knowledge_graph/edges/contains_clause.data.json", "knowledge_graph/edges/contains_clause.schema.json")
]


    for data_rel, schema_rel in pairs:
        validate_file(root / data_rel, root / schema_rel)

    # Step 3: referential integrity
    validate_referential_integrity(root)

    

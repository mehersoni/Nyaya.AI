import json
from pathlib import Path
from jsonschema import validate, ValidationError


class SchemaValidationError(Exception):
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
            f"{data_path.name} failed validation: {e.message}"
        )


def validate_knowledge_graph(root: Path):
    pairs = [
        ("knowledge_graph/nodes/sections.data.json", "knowledge_graph/nodes/sections.schema.json"),
        ("knowledge_graph/nodes/definitions.data.json", "knowledge_graph/nodes/definitions.schema.json"),
        ("knowledge_graph/nodes/rights.data.json", "knowledge_graph/nodes/rights.schema.json"),
        ("knowledge_graph/edges/references.data.json", "knowledge_graph/edges/references.schema.json"),
        ("knowledge_graph/edges/defines.data.json", "knowledge_graph/edges/defines.schema.json"),
        ("knowledge_graph/edges/contains.data.json", "knowledge_graph/edges/contains.schema.json"),
    ]

    for data_rel, schema_rel in pairs:
        validate_file(root / data_rel, root / schema_rel)

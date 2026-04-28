import json
from pathlib import Path
from typing import Any, Dict, List

from .paths import SCHEMAS_DIR


def load_unified_listing_schema(schema_path: Path = None) -> Dict[str, Any]:
    path = schema_path or SCHEMAS_DIR / "unified_listing.schema.json"
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_query_schema(schema_path: Path = None) -> Dict[str, Any]:
    path = schema_path or SCHEMAS_DIR / "query.schema.json"
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_schema(name: str) -> Dict[str, Any]:
    if name in {"unified-listing", "unified_listing", "result"}:
        return load_unified_listing_schema()
    if name == "query":
        return load_query_schema()
    raise ValueError("schema name must be one of: unified-listing, query")


def validate_json_document(document: Any, schema: Dict[str, Any]) -> List[Dict[str, str]]:
    errors: List[Dict[str, str]] = []
    _validate_node(document, schema, schema, "$", errors)
    return errors


def _validate_node(
    value: Any,
    schema: Dict[str, Any],
    root_schema: Dict[str, Any],
    path: str,
    errors: List[Dict[str, str]],
) -> None:
    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], root_schema)

    if "const" in schema and value != schema["const"]:
        errors.append({"path": path, "message": f"expected constant {schema['const']!r}"})
        return

    if "enum" in schema and value not in schema["enum"]:
        errors.append({"path": path, "message": f"expected one of {schema['enum']!r}"})
        return

    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(value, expected_type):
        errors.append({"path": path, "message": f"expected type {expected_type!r}"})
        return

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append({"path": path, "message": f"missing required property {key!r}"})

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append({"path": f"{path}.{key}", "message": "additional property is not allowed"})

        for key, child_schema in properties.items():
            if key in value:
                _validate_node(value[key], child_schema, root_schema, f"{path}.{key}", errors)

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            _validate_node(item, schema["items"], root_schema, f"{path}[{index}]", errors)


def _resolve_ref(ref: str, root_schema: Dict[str, Any]) -> Dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Unsupported schema reference: {ref}")
    node: Any = root_schema
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _matches_type(value: Any, expected_type: Any) -> bool:
    if isinstance(expected_type, list):
        return any(_matches_type(value, item) for item in expected_type)
    if expected_type == "null":
        return value is None
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    return True

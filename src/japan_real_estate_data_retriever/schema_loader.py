import json
from pathlib import Path
from typing import Any, Dict

from .paths import SCHEMAS_DIR


def load_unified_listing_schema(schema_path: Path = None) -> Dict[str, Any]:
    path = schema_path or SCHEMAS_DIR / "unified_listing.schema.json"
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


import json
from pathlib import Path
from typing import Any, Dict

from .paths import REFERENCES_DIR
from .schema_loader import load_unified_listing_schema
from .sites import get_site


def load_site_workflow(source: str) -> str:
    site = get_site(source)
    path = REFERENCES_DIR / site.workflow_reference
    with path.open("r", encoding="utf-8") as file:
        return file.read()


def load_filter_capabilities() -> str:
    path = REFERENCES_DIR / "search-filter-capabilities.md"
    with path.open("r", encoding="utf-8") as file:
        return file.read()


def build_browser_use_task(source: str, query: Dict[str, Any]) -> str:
    site = get_site(source)
    workflow = load_site_workflow(source)
    filter_capabilities = load_filter_capabilities()
    query_json = json.dumps(query, ensure_ascii=False, indent=2)

    return f"""You are a Japanese real estate listing extraction agent. Visit only {site.display_name}, starting from {site.base_url}, and retrieve real listing and detail-page information according to the user query.

Requirements:
- Follow the site workflow strictly and do not scrape across sources.
- Prefer detail pages for extraction; use list-page data only when a detail field is missing.
- Return structured JSON only. Do not return Markdown or process explanations.
- When source_listing_id exists, each listing id must be "{site.source}:<source_listing_id>". When source_listing_id is unavailable, keep source_url and let downstream code generate the URL-hash id.
- Use null for unknown scalar fields and [] for unavailable arrays.
- Preserve original labels and ambiguous values seen on the page in raw, so mappings can be refined later.
- Translate the user request into available site filters before browsing details. Put unavailable or approximate filters into raw.unapplied_filters and raw.filter_translation_notes.

User query:
{query_json}

General search-filter capabilities and conversion rules:
{filter_capabilities}

Site workflow and field mapping:
{workflow}
"""


def build_session_payload(
    source: str,
    query: Dict[str, Any],
    model: str = "bu-mini",
    max_cost_usd: float = 2.0,
) -> Dict[str, Any]:
    return {
        "task": build_browser_use_task(source, query),
        "model": model,
        "keepAlive": False,
        "maxCostUsd": max_cost_usd,
        "proxyCountryCode": "jp",
        "outputSchema": load_unified_listing_schema(),
        "enableRecording": False,
        "skills": True,
        "agentmail": False,
        "cacheScript": False,
    }


def write_payload(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

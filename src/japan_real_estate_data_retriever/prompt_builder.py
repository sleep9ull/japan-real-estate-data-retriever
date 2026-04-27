import json
from pathlib import Path
from typing import Any, Dict, Optional

from .paths import REFERENCES_DIR
from .schema_loader import load_unified_listing_schema
from .sites import get_site


DEFAULT_BROWSER_TIMEOUT_MINUTES = 60
DEFAULT_BROWSER_SCREEN_WIDTH = 1440
DEFAULT_BROWSER_SCREEN_HEIGHT = 1000
DEFAULT_AGENT_MODEL = "bu-mini"
DEFAULT_BROWSER_RECONNECT_ATTEMPTS = 2


def load_site_workflow(source: str) -> str:
    site = get_site(source)
    path = REFERENCES_DIR / site.workflow_reference
    with path.open("r", encoding="utf-8") as file:
        return file.read()


def load_filter_capabilities() -> str:
    path = REFERENCES_DIR / "search-filter-capabilities.md"
    with path.open("r", encoding="utf-8") as file:
        return file.read()


def build_local_agent_instructions(source: str, query: Dict[str, Any]) -> str:
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


def build_browser_session_payload(
    timeout_minutes: int = DEFAULT_BROWSER_TIMEOUT_MINUTES,
    profile_id: Optional[str] = None,
    enable_recording: bool = False,
    browser_screen_width: int = DEFAULT_BROWSER_SCREEN_WIDTH,
    browser_screen_height: int = DEFAULT_BROWSER_SCREEN_HEIGHT,
    allow_resizing: bool = False,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "proxyCountryCode": "jp",
        "timeout": timeout_minutes,
        "browserScreenWidth": browser_screen_width,
        "browserScreenHeight": browser_screen_height,
        "allowResizing": allow_resizing,
        "enableRecording": enable_recording,
    }
    if profile_id:
        payload["profileId"] = profile_id
    return payload


def build_agent_session_payload(
    source: str,
    query: Dict[str, Any],
    model: str = DEFAULT_AGENT_MODEL,
    max_cost_usd: float = 2.0,
    keep_alive: bool = False,
    profile_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    enable_recording: bool = False,
    skills: bool = True,
    agentmail: bool = False,
    cache_script: bool = False,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "task": build_local_agent_instructions(source, query),
        "model": model,
        "keepAlive": keep_alive,
        "maxCostUsd": max_cost_usd,
        "proxyCountryCode": "jp",
        "outputSchema": load_unified_listing_schema(),
        "enableRecording": enable_recording,
        "skills": skills,
        "agentmail": agentmail,
        "cacheScript": cache_script,
    }
    if profile_id:
        payload["profileId"] = profile_id
    if workspace_id:
        payload["workspaceId"] = workspace_id
    return payload


def build_local_agent_context(source: str, query: Dict[str, Any]) -> Dict[str, Any]:
    site = get_site(source)
    return {
        "source": site.source,
        "site": {
            "displayName": site.display_name,
            "baseUrl": site.base_url,
            "workflowReference": site.workflow_reference,
        },
        "query": query,
        "instructions": build_local_agent_instructions(source, query),
        "browserOnlyExecutionPolicy": build_browser_only_execution_policy(site.source),
        "outputSchema": load_unified_listing_schema(),
    }


def build_browser_only_execution_policy(source: Optional[str] = None) -> Dict[str, Any]:
    """Return operational rules for local agents driving Cloud Browser directly."""
    policy: Dict[str, Any] = {
        "mode": "browser_only_primary",
        "sessionIsolation": "one_cloud_browser_per_source",
        "maxReconnectAttemptsPerSource": DEFAULT_BROWSER_RECONNECT_ATTEMPTS,
        "phases": [
            "connect_to_cdp",
            "navigate_or_reuse_loaded_page",
            "extract_raw_source_rows",
            "normalize_and_rank_locally",
            "stop_cloud_browser",
        ],
        "retryRules": [
            "Run each source as a short independent worker instead of one long multi-site browser flow.",
            "If navigation times out after the target page starts loading, reconnect to the same cdpUrl before creating a replacement browser.",
            "If Page.evaluate or Page.goto raises TargetClosedError, call get-browser or reconnect to the same cdpUrl and inspect existing pages; reuse a loaded DOM when document.title and source-specific list selectors are present.",
            "Write per-source raw HTML/JSON before ranking so a failed normalization step can be retried without reloading the website.",
            "Only create a new Cloud Browser for that source after reconnecting to the current browser fails or the loaded DOM is not usable.",
        ],
        "completionRules": [
            "Merge sources only after each source has produced normalized rows.",
            "Stop every Cloud Browser session after extraction or after an unrecoverable source failure.",
            "Use Cloud Agent fallback only for incomplete sources after browser-only retry and DOM reuse fail.",
        ],
    }
    if source:
        policy["source"] = get_site(source).source
    return policy


def build_browser_workflow_payload(
    source: str,
    query: Dict[str, Any],
    timeout_minutes: int = DEFAULT_BROWSER_TIMEOUT_MINUTES,
    profile_id: Optional[str] = None,
    enable_recording: bool = False,
    browser_screen_width: int = DEFAULT_BROWSER_SCREEN_WIDTH,
    browser_screen_height: int = DEFAULT_BROWSER_SCREEN_HEIGHT,
    allow_resizing: bool = False,
) -> Dict[str, Any]:
    return {
        "executionMode": "browser_only_primary",
        "sessionIsolation": {
            "strategy": "one_cloud_browser_per_source",
            "source": get_site(source).source,
            "reason": "Avoid cross-site browser state, page closures, proxy tunnel issues, and WAF/challenge side effects.",
        },
        "executionPolicy": build_browser_only_execution_policy(source),
        "browserPayload": build_browser_session_payload(
            timeout_minutes=timeout_minutes,
            profile_id=profile_id,
            enable_recording=enable_recording,
            browser_screen_width=browser_screen_width,
            browser_screen_height=browser_screen_height,
            allow_resizing=allow_resizing,
        ),
        "workflow": build_local_agent_context(source, query),
    }


def build_multi_source_browser_workflow_payload(
    sources: list,
    query: Dict[str, Any],
    timeout_minutes: int = DEFAULT_BROWSER_TIMEOUT_MINUTES,
    profile_id: Optional[str] = None,
    enable_recording: bool = False,
    browser_screen_width: int = DEFAULT_BROWSER_SCREEN_WIDTH,
    browser_screen_height: int = DEFAULT_BROWSER_SCREEN_HEIGHT,
    allow_resizing: bool = False,
) -> Dict[str, Any]:
    normalized_sources = [get_site(source).source for source in sources]
    return {
        "executionMode": "browser_only_primary",
        "sessionIsolation": {
            "strategy": "one_cloud_browser_per_source",
            "sources": normalized_sources,
            "reason": "Each source receives its own Cloud Browser session so a site's cookies, challenges, page crashes, or navigation failures cannot affect another source.",
        },
        "executionPolicy": build_browser_only_execution_policy(),
        "sources": {
            source: build_browser_workflow_payload(
                source=source,
                query=query,
                timeout_minutes=timeout_minutes,
                profile_id=profile_id,
                enable_recording=enable_recording,
                browser_screen_width=browser_screen_width,
                browser_screen_height=browser_screen_height,
                allow_resizing=allow_resizing,
            )
            for source in normalized_sources
        },
    }


def write_payload(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

# Overall Workflow

## Purpose

This workflow converts a personalized Japanese property search into structured JSON listing data.

## Steps

1. Normalize the user request into a query object:
   - `transaction_type`: `sale`, `rent`, or another explicit category
   - `property_type`: site-language property type such as `中古マンション`, `新築一戸建て`, `土地`
   - `area`: prefecture, city/ward, station, line, or commute requirement
   - `filters`: price, area, layout, walk minutes, age, floor, yield, or other constraints
   - `max_results`: default 10 unless user specifies otherwise
2. Select sources. If multiple sources are requested, run independent browser-only Cloud Browser sessions per source, then merge only after each source result is normalized. Never reuse one browser session across multiple source sites.
3. Load `search-filter-capabilities.md` and translate user intent into concrete site controls.
4. Load the site workflow reference and use it as the navigation plan.
5. Search the site, applying filters before opening details. If a filter is unavailable, keep it in `raw.unapplied_filters` and post-filter after extraction.
6. Open detail pages for each candidate result.
7. Extract all fields supported by the detail page, preserving original labels in `raw`.
8. Return JSON matching `schemas/unified_listing.schema.json`.

## Browser-Only Runtime Policy

Use this policy when a local agent drives Browser Use Cloud Browser through CDP:

1. Create one Cloud Browser per source site.
2. Execute each source as a short worker: connect to CDP, navigate or reuse a loaded page, extract raw rows, write raw artifacts, normalize/rank locally, and then stop the browser.
3. If navigation times out after the page starts loading, reconnect to the same `cdpUrl` and inspect the current page before creating a replacement session.
4. If `Page.goto` or `Page.evaluate` raises `TargetClosedError`, reconnect to the same `cdpUrl`. If the browser still has a page whose `document.title` and list selectors match the source, reuse the loaded DOM and continue extraction.
5. Create a replacement Cloud Browser only for the affected source, only after reconnecting to the current session fails or the DOM is unusable.
6. Merge results only after each source has produced normalized rows.
7. Stop every Cloud Browser session, including partially failed sessions, to avoid unnecessary browser/proxy cost.

## Browser Use Cloud Defaults

- API key: read only from `BROWSER_USE_API_KEY`.
- API version: v3 standalone browsers for the primary path.
- Primary endpoint: `POST /browsers`.
- Stop endpoint: `PATCH /browsers/{id}` with `{"action": "stop"}`.
- Multi-source isolation: one Cloud Browser session per source site.
- Runtime recovery: reconnect to the same `cdpUrl` and reuse already loaded DOM before replacing a failed source browser.
- Fallback Agent endpoint: `POST /sessions`.
- Fallback Agent stop endpoint: `POST /sessions/{id}/stop`.
- Proxy: `jp`.
- `enableRecording`: false unless debugging.
- The local agent must drive the returned `cdpUrl` according to the site workflow references.
- Validate local-agent output against `schemas/unified_listing.schema.json`.
- Use fallback Agent sessions only for repair, exploration, or incomplete browser-only runs.

## Quality Rules

- Do not invent fields or values.
- Do not scrape hidden or private data.
- Do not bypass authentication, paywalls, robots controls, or access restrictions.
- Stop early and report an error item if the site blocks access or requires unavailable user action.
- Keep partial results if some detail pages fail.

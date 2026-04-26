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
2. Select sources. If multiple sources are requested, run independent Browser Use tasks per source.
3. Load `search-filter-capabilities.md` and translate user intent into concrete site controls.
4. Load the site workflow reference and use it as the navigation plan.
5. Search the site, applying filters before opening details. If a filter is unavailable, keep it in `raw.unapplied_filters` and post-filter after extraction.
6. Open detail pages for each candidate result.
7. Extract all fields supported by the detail page, preserving original labels in `raw`.
8. Return JSON matching `schemas/unified_listing.schema.json`.

## Browser Use Cloud Defaults

- API key: read only from `BROWSER_USE_API_KEY`.
- API version: v3 sessions.
- Proxy: `jp`.
- `skills`: true.
- `agentmail`: false.
- `enableRecording`: false unless debugging.
- Use `outputSchema` to force structured output.

## Quality Rules

- Do not invent fields or values.
- Do not scrape hidden or private data.
- Do not bypass authentication, paywalls, robots controls, or access restrictions.
- Stop early and report an error item if the site blocks access or requires unavailable user action.
- Keep partial results if some detail pages fail.

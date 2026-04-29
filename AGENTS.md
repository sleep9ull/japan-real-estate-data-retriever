# Project Instructions

This project retrieves Japanese real estate transaction/listing data and normalizes different sources into a stable JSON structure for future agents.

## Operating Principles

- Prefer small, reviewable diffs.
- Search the repository before editing and follow existing conventions.
- Never write API keys, tokens, `.env` values, or credentials into code or logs.
- Add or update tests for behavior changes.
- Use English for project documentation and implementation notes.

## Project Conventions

- Use Browser Use Cloud standalone browser REST API (`POST /browsers`) as the primary production browser infrastructure; local agents and project skills should drive the returned `cdpUrl`.
- Use Browser Use Cloud Agent REST API (`POST /sessions`) only as a fallback, repair, or exploration path when browser-only execution fails or a workflow needs refinement.
- For browser-only production runs, create one independent Cloud Browser session per source site. Do not reuse one browser session across multiple source sites.
- For browser-only recovery, reconnect to the same `cdpUrl` and reuse an already loaded DOM before creating a replacement browser or switching to Cloud Agent fallback.
- Write per-source raw artifacts before local normalization/ranking, then stop every Cloud Browser session when extraction or failure handling is complete.
- Use the local `browser-use` CLI only for pure local browser debugging (`open`, `state`, `click`, screenshots, etc.); do not use CLI Cloud passthrough as a production or default path.
- Load the Browser Use Cloud API key from `BROWSER_USE_API_KEY` first. Local checkout tests may fall back to the project `.env.local`, but real values must never be printed or committed.
- All cloud browser and fallback agent sessions should use the Japan proxy: `proxyCountryCode: "jp"`.
- The fixed source identifiers are `suumo`, `athome`, `homes`, and `yahoo_japan`.
- The storage primary key is source-aware: use `source:source_listing_id`; when no source listing ID exists, use `source:url:<sha256-prefix>`.
- All normalized output must conform to the canonical JSON Schema at `schemas/unified_listing.schema.json`.
- Site workflows and field mappings live in `skills/japan-real-estate-data-retriever/references/site-*.md`.

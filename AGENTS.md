# Project Instructions

This project retrieves Japanese real estate transaction/listing data and normalizes different sources into a stable JSON structure for future agents.

## Operating Principles

- Prefer small, reviewable diffs.
- Search the repository before editing and follow existing conventions.
- Never write API keys, tokens, `.env` values, or credentials into code or logs.
- Add or update tests for behavior changes.
- Use English for project documentation and implementation notes.

## Project Conventions

- Use Browser Use Cloud REST API as the production execution path.
- Use the local `browser-use` CLI only for pure local browser debugging (`open`, `state`, `click`, screenshots, etc.); do not use CLI Cloud passthrough as a production or default path.
- Load the Browser Use Cloud API key from `BROWSER_USE_API_KEY` first. Local runs may fall back to the project `.env`, but real values must never be printed or committed.
- All cloud tasks should use the Japan proxy: `proxyCountryCode: "jp"`.
- The fixed source identifiers are `suumo`, `athome`, `homes`, and `yahoo_japan`.
- The storage primary key is source-aware: use `source:source_listing_id`; when no source listing ID exists, use `source:url:<sha256-prefix>`.
- All normalized output must conform to the canonical JSON Schema at `schemas/unified_listing.schema.json`.
- Site workflows and field mappings live in `skills/japan-real-estate-data-retriever/references/site-*.md`.

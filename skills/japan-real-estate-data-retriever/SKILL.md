---
name: japan-real-estate-data-retriever
description: Retrieve and normalize Japanese real estate listings with Browser Use Cloud workflows. Use when Codex needs to run or design listing retrieval for SUUMO, at home, LIFULL HOME'S, or Yahoo! JAPAN Real Estate; translate property search requirements into site filters; map source fields into the unified listing schema; or validate source-aware listing output.
---

# Japan Real Estate Data Retriever

Use this skill to turn a Japanese real estate search request into a browser-only Cloud Browser workflow driven by the local agent and project references. Use Browser Use Cloud Agent only as fallback, repair, or exploration.

## Core Workflow

1. Identify the target site or sites: `suumo`, `athome`, `homes`, `yahoo_japan`. If the user says "all sites", create one independent Cloud Browser session per site and merge only after each source result is normalized.
2. Read only the references needed for the task:
   - `references/overall-workflow.md` for the end-to-end retrieval flow.
   - `references/search-filter-capabilities.md` for translating user filters to site controls.
   - `references/unified-fields.md` for field mapping questions.
   - `references/source-id-strategy.md` for listing ID decisions.
3. Read the relevant site reference:
   - `references/site-suumo.md`
   - `references/site-athome.md`
   - `references/site-homes.md`
   - `references/site-yahoo-japan.md`
4. For Browser Use Cloud behavior or known site interaction limits, read:
   - `references/cloud-probe-findings-2026-04-26.md`
   - `references/cloud-search-detail-probe-findings-2026-04-26.md`
5. Build a query JSON with area, transaction type, property type, filters, max results, and any user preferences.
6. Translate user preferences into site filter controls before browsing detail pages. Apply exact filters first; keep soft preferences and grouped filters for ranking/post-filtering.
7. Build or run through the project CLI in `src/`; it is the single implementation of Cloud Browser creation, fallback Agent sessions, and normalization helpers. Use `run` for the primary browser-only path. Use `run-all` for multi-source browser-only runs. Use `run-agent` only as fallback or workflow discovery. Use `debug-local` only for pure local browser debugging with Browser Use CLI.
8. Validate output against `schemas/unified_listing.schema.json`.

## Browser-Only Execution Policy

For production-style browser-only runs:

- Treat each source as a short independent worker: connect to its `cdpUrl`, navigate or reuse its current page, extract raw source rows, normalize/rank locally, then stop that browser.
- If `Page.goto` times out after a source page starts loading, reconnect to the same `cdpUrl` and inspect the existing page before creating a replacement browser.
- If `Page.evaluate` or `Page.goto` raises `TargetClosedError`, do not assume the source failed permanently. Reconnect to the same `cdpUrl`; if `document.title` and source-specific list selectors are present, reuse the loaded DOM and extract from it.
- Write per-source raw HTML/JSON before ranking, so normalization and CSV export can be retried without another website load.
- Create a new Cloud Browser only for the affected source, and only after reconnecting to the current browser fails or the loaded DOM is unusable.
- Stop every Cloud Browser session at the end of extraction or after unrecoverable failure.

## Commands

From the repository root, generate a browser-only Cloud Browser plan without calling Browser Use:

```bash
python -m japan_real_estate_data_retriever.cli build-task \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --out data/raw/suumo-task.json
```

Create a Cloud Browser session for the primary browser-only path:

```bash
python -m japan_real_estate_data_retriever.cli run \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --out data/raw/suumo-browser-session.json
```

For multiple sources, create isolated sessions with `run-all`:

```bash
python -m japan_real_estate_data_retriever.cli run-all \
  --query-file examples/query.tokyo-condo.json \
  --sources suumo athome homes yahoo_japan \
  --out data/raw/all-browser-sessions.json
```

Stop the Cloud Browser after the local agent finishes:

```bash
python -m japan_real_estate_data_retriever.cli stop-browser \
  --browser-id <browser-session-id>
```

Use Browser Use Cloud Agent only as fallback:

```bash
python -m japan_real_estate_data_retriever.cli run-agent \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --out data/raw/suumo-agent-fallback.json
```

Dry-run before dispatching:

```bash
python -m japan_real_estate_data_retriever.cli run \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --dry-run
```

Use the local Browser Use CLI only when debugging local browser behavior:

```bash
browser-use doctor
python -m japan_real_estate_data_retriever.cli debug-local \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --state \
  --screenshot data/raw/suumo-local-debug.png \
  --out data/raw/suumo-local-debug.json
```

If `browser-use` is not on `PATH` after installing the CLI, run `source ~/.zshrc`, open a new terminal, or use `~/.browser-use-env/bin/browser-use`. Ignore missing `cloudflared` unless the task needs `browser-use tunnel`.

When debugging an environment where `PATH` is not reliable, set `BROWSER_USE_CLI` or pass `--browser-use-cli "$HOME/.browser-use-env/bin/browser-use"`.

Local CLI debugging uses local `browser-use open/state/screenshot` style commands. It does not call Browser Use Cloud and does not produce canonical schema output.

Never print or commit `BROWSER_USE_API_KEY`. Ask the user to provide secrets through environment variables only.

## Output Contract

Every task must return:

- `schema_version`: currently `2026-04-26`
- `source`: one of the four source identifiers
- `query`: the original normalized query object
- `items`: array of unified listing objects
- `errors`: array of `{url, message}` objects

Each item must use `id = source:source_listing_id` when a site listing ID exists. If no listing ID exists, set `source_listing_id` to `null`, keep `source_url`, and let downstream normalization create `source:url:<sha256-prefix>`.

## Schema Contract

Use the generic JSON Schema as the canonical data contract:

- `schemas/unified_listing.schema.json`
- bundled reference copy: `references/unified_listing.schema.json`

Treat the root schema as authoritative. Keep the bundled copy in sync when packaging or changing the schema.

## Implementation Boundary

- Keep executable retrieval, payload generation, REST calls, and normalization in `src/japan_real_estate_data_retriever/`.
- Keep this skill focused on agent instructions and domain references.
- Do not add skill scripts that duplicate project Python package behavior.
- Use `skills/references/` for detailed site workflow, mapping, and probe notes so SKILL.md stays small.

## Site Notes

- Prefer details pages over list pages.
- Apply available search filters before opening result details; record un-applied filters in `raw.unapplied_filters`.
- Capture source-specific raw labels in `raw` whenever mapping is uncertain.
- Fill unknown scalar fields with `null`; fill unknown arrays with `[]`.
- Keep source identity on every item. Never merge listings from different sites by raw ID alone.
- Use Japan proxy (`proxyCountryCode: "jp"`) for Cloud Browser and fallback Agent sessions.

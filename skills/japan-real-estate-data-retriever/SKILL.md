---
name: japan-real-estate-data-retriever
description: Retrieve and normalize Japanese real estate listings with Browser Use Cloud workflows. Use when Codex needs to run or design listing retrieval for SUUMO, at home, LIFULL HOME'S, or Yahoo! JAPAN Real Estate; translate property search requirements into site filters; map source fields into the unified listing schema; or validate source-aware listing output.
---

# Japan Real Estate Data Retriever

Use this skill to turn a Japanese real estate search request into a Browser Use Cloud run that returns stable structured data.

## Core Workflow

1. Identify the target site or sites: `suumo`, `athome`, `homes`, `yahoo_japan`. If the user says "all sites", run one task per site and merge only after each source result is normalized.
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
7. Build or run through the project CLI in `src/`; it is the single implementation of production payload generation and execution. Use `run` for Browser Use Cloud production runs. Use `debug-local` only for pure local browser debugging with Browser Use CLI.
8. Validate output against `schemas/unified_listing.schema.json`.

## Commands

From the repository root, generate a payload without calling Browser Use:

```bash
python -m japan_real_estate_data_retriever.cli build-task \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --out data/raw/suumo-task.json
```

Run through the project CLI. This defaults to Browser Use Cloud REST API:

```bash
python -m japan_real_estate_data_retriever.cli run \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --out data/raw/suumo-session-result.json
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
- Use Japan proxy (`proxyCountryCode: "jp"`) for Browser Use Cloud sessions.

# Japan Real Estate Data Retriever

[English](README.md) | [中文](README.zh-CN.md)

This repository is a workflow-first project for retrieving Japanese real estate listing data. It focuses on stable Browser Use Cloud workflows, a generic JSON Schema, source-aware IDs, and structured outputs that future agents can call.

## Goals

- Use Browser Use Cloud agent browsers to access SUUMO, at home, LIFULL HOME'S, and Yahoo! JAPAN Real Estate.
- Maintain separate workflow and field-mapping references for each source site.
- Normalize detail-page data from different sources into one generic JSON format.
- Keep a stable JSON contract for future agent workflows.
- Support future calls from Hermes agent or other agents that receive personalized property search requests.

## Directory Layout

```text
.
├── skills/japan-real-estate-data-retriever/    # versioned Codex skill
│   ├── SKILL.md                         # agent workflow entrypoint
│   └── references/                      # site workflows, field mappings, design notes
├── schemas/unified_listing.schema.json  # canonical generic JSON Schema
├── src/japan_real_estate_data_retriever/  # single execution implementation
├── examples/                            # sample query requests
├── tests/                               # fast tests that do not require external APIs
├── data/raw/                            # raw probe/session outputs
└── data/normalized/                     # normalized output files
```

## Prerequisites

The project defaults to **Browser Use Cloud** through the REST API. Production runs should use this default path. Provide the API key through an environment variable or a local `.env` file:

```bash
export BROWSER_USE_API_KEY=bu_your_key_here
```

Optional: install Browser Use CLI only when explicitly requested or when debugging locally. The CLI is not the production default.

```bash
curl -fsSL https://browser-use.com/cli/install.sh | bash
source ~/.zshrc
browser-use doctor
```

If `browser-use` is still not found after installation, try a new terminal session or run it directly from the installer environment:

```bash
~/.browser-use-env/bin/browser-use doctor
```

You can also point this project at a specific CLI binary:

```bash
export BROWSER_USE_CLI="$HOME/.browser-use-env/bin/browser-use"
```

`cloudflared not installed` in `browser-use doctor` only affects `browser-use tunnel`; it is not required for normal local CLI debugging. Network warnings may appear when running behind a proxy.

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests
```

Build a Browser Use task payload without calling any external API:

```bash
python -m japan_real_estate_data_retriever.cli build-task \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --out data/raw/suumo-task.json
```

Dry-run a cloud task before dispatching it:

```bash
python -m japan_real_estate_data_retriever.cli run \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --dry-run
```

Run a real task. This defaults to Browser Use Cloud REST API and uses `proxyCountryCode: "jp"`:

```bash
python -m japan_real_estate_data_retriever.cli run \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --out data/raw/suumo-session-result.json
```

Use the local Browser Use CLI for pure local browser debugging:

```bash
python -m japan_real_estate_data_retriever.cli debug-local \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --state \
  --screenshot data/raw/suumo-local-debug.png \
  --out data/raw/suumo-local-debug.json
```

If the CLI is not on `PATH`, pass it explicitly:

```bash
python -m japan_real_estate_data_retriever.cli debug-local \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --browser-use-cli "$HOME/.browser-use-env/bin/browser-use" \
  --state
```

The local debug command uses local `browser-use open`, `state`, and `screenshot` style commands. It does not call Browser Use Cloud and does not produce canonical schema output. Use it to inspect site navigation, filters, labels, and screenshots before updating workflows.

Keep `BROWSER_USE_API_KEY` in the environment or a local `.env` for production Cloud runs; never print or commit real values.

## Reference Documents

- `skills/japan-real-estate-data-retriever/SKILL.md`
- `skills/japan-real-estate-data-retriever/references/overall-workflow.md`
- `skills/japan-real-estate-data-retriever/references/search-filter-capabilities.md`
- `skills/japan-real-estate-data-retriever/references/unified-fields.md`
- `skills/japan-real-estate-data-retriever/references/source-id-strategy.md`
- `skills/japan-real-estate-data-retriever/references/cloud-probe-findings-2026-04-26.md`
- `skills/japan-real-estate-data-retriever/references/cloud-search-detail-probe-findings-2026-04-26.md`
- `skills/japan-real-estate-data-retriever/references/site-suumo.md`
- `skills/japan-real-estate-data-retriever/references/site-athome.md`
- `skills/japan-real-estate-data-retriever/references/site-homes.md`
- `skills/japan-real-estate-data-retriever/references/site-yahoo-japan.md`

Browser Use Cloud v3 uses `https://api.browser-use.com/api/v3` and the `X-Browser-Use-API-Key` header. This project uses Browser Use Cloud REST API as the production/default path. Local Browser Use CLI debugging is separate and only drives a local browser.

## Data Schema

The canonical schema is generic JSON Schema:

```bash
schemas/unified_listing.schema.json
```

The bundled skill copy at `skills/japan-real-estate-data-retriever/references/unified_listing.schema.json` is kept in sync as an agent reference.

The project Python package is the single execution layer for Browser Use payload generation, cloud runs, and normalization. The skill contains the agent workflow and references only.

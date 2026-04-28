# Japan Real Estate Data Retriever

[English](README.md) | [中文](README.zh-CN.md)

This is a workflow-first project for retrieving Japanese real estate listings. Browser Use Cloud is treated primarily as cloud browser infrastructure with a Japan proxy. Your own agent should drive the browser through the project skills/workflows. Browser Use Cloud Agent v3 is kept as a fallback, repair, and exploration path.

## Architecture

- Primary path: Browser Use Cloud standalone browser, `POST /browsers`, with `proxyCountryCode: "jp"`.
- Multi-source jobs must create one independent Cloud Browser session per source. Do not reuse one browser/context across different source sites.
- Local agents connect to the returned `cdpUrl` and follow the site workflow references.
- Fallback path: Browser Use Cloud Agent v3, `POST /sessions`, when browser-only execution fails, a workflow needs repair, or a site requires exploration.
- Local `browser-use` CLI is only for local browser debugging, never the production path.
- All final output should normalize to `schemas/unified_listing.schema.json`.

## Goals

- Maintain site-specific workflows and field mappings for SUUMO, at home, LIFULL HOME'S, and Yahoo! JAPAN Real Estate.
- Normalize detail-page data from different sources into stable JSON/CSV output.
- Support future Hermes or other agents that receive personalized property search requests.
- Keep long-running retrieval deterministic and cost-aware by using project-owned workflows.
- Use Cloud Agent fallback only for difficult pages, blocked flows, or workflow discovery.

## Directory Layout

```text
.
├── .agents/skills/japan-real-estate-data-retriever/
│   ├── SKILL.md
│   └── references/
├── schemas/unified_listing.schema.json
├── src/japan_real_estate_data_retriever/
├── examples/
├── tests/
├── data/raw/
└── data/exports/
```

## Prerequisites

Provide the Browser Use Cloud API key through the environment or a local `.env`. Never print or commit real values:

```bash
export BROWSER_USE_API_KEY=bu_your_key_here
```

Local development:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
PYTHONPATH=src python3 -m unittest discover -s tests
```

Install the agent-native CLI on PATH:

```bash
make install-local
jreretrieve --help
jreretrieve --json doctor
```

`make install-local` uses `uv tool install --editable . --force`, which works with this `pyproject.toml` package even when the system `pip` is too old for editable PEP 517 installs.

## Agent-Friendly CLI

Use `jreretrieve` as the stable command layer from any repository. Prefer `--json` for Codex or other agents.

Discovery and setup:

```bash
jreretrieve --json doctor
jreretrieve --json sources list
jreretrieve --json sources resolve lifull
```

Read local contracts without starting a browser:

```bash
jreretrieve --json schema show --name unified-listing
jreretrieve --json schema validate --name query --file examples/query.shibuya-google-rent-2ldk.json
jreretrieve --json workflow show --site suumo --query-file examples/query.shibuya-google-rent-2ldk.json
```

Raw read-only Browser Use API escape hatch:

```bash
jreretrieve --json request get /browsers/<browser-id>
```

JSON policy:

- `--json` writes machine-readable JSON to stdout only.
- Errors under `--json` use `{"ok": false, "error": {"message": "..."}}` and never include credentials.
- `doctor` reports the auth source category (`env`, `project_env`, or `missing`) without printing token values.
- `request get` returns the Browser Use API response object; live writes are intentionally not exposed through the raw escape hatch.

## Primary Browser-Only Path

Build a browser-only execution plan without calling external APIs:

```bash
PYTHONPATH=src python3 -m japan_real_estate_data_retriever.cli build-task \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/suumo-browser-plan.json
```

Create a Cloud Browser session and write both `browser.cdpUrl` and workflow context:

```bash
PYTHONPATH=src python3 -m japan_real_estate_data_retriever.cli run \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/suumo-browser-session.json
```

For multi-source jobs, use `run-all`; it creates one isolated Cloud Browser session per source:

```bash
PYTHONPATH=src python3 -m japan_real_estate_data_retriever.cli run-all \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/shibuya-google-browser-sessions.json
```

You can also pass sources explicitly:

```bash
PYTHONPATH=src python3 -m japan_real_estate_data_retriever.cli run-all \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --sources suumo athome homes yahoo_japan \
  --out data/raw/shibuya-google-browser-sessions.json
```

Your agent should then use:

- `browser.cdpUrl`: connect with Playwright, Puppeteer, or any CDP client.
- `workflow.instructions`: site-specific execution instructions.
- `workflow.browserOnlyExecutionPolicy` / `executionPolicy`: browser-only runbook for reconnects, DOM reuse, failure isolation, and browser cleanup.
- `workflow.outputSchema`: the canonical output contract.

For browser-only execution, run each source as a short worker:

1. Connect to that source's `cdpUrl`.
2. Navigate to the target page, or reuse the current loaded page.
3. Write per-source raw HTML/JSON before local normalization and ranking.
4. If `Page.goto` times out after the page starts loading, reconnect to the same `cdpUrl` and inspect the current DOM.
5. If `Page.goto` or `Page.evaluate` raises `TargetClosedError`, reconnect to the same `cdpUrl`; when `document.title` and source-specific list selectors are present, reuse the loaded DOM.
6. Create a replacement Cloud Browser only when reconnecting fails or the loaded DOM is unusable.

Stop the Cloud Browser when done:

```bash
PYTHONPATH=src python3 -m japan_real_estate_data_retriever.cli stop-browser \
  --browser-id <browser-session-id>
```

Stop multiple Cloud Browsers:

```bash
PYTHONPATH=src python3 -m japan_real_estate_data_retriever.cli stop-browser \
  --browser-id <suumo-browser-id> <athome-browser-id> <homes-browser-id> <yahoo-browser-id>
```

## Cloud Agent Fallback

Use Cloud Agent v3 only when browser-only execution fails, results are incomplete, or a site workflow needs discovery:

```bash
PYTHONPATH=src python3 -m japan_real_estate_data_retriever.cli run-agent \
  --site yahoo_japan \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --model bu-mini \
  --max-cost-usd 5 \
  --out data/raw/yahoo-agent-session-result.json
```

Stop an active Agent session:

```bash
PYTHONPATH=src python3 -m japan_real_estate_data_retriever.cli stop-session \
  --session-id <agent-session-id>
```

BYOK/provider keys are not stored here or passed through undocumented request fields. Configure BYOK in Browser Use if officially supported, then select the supported model with `--model`.

## Local Debugging

The local `browser-use` CLI is for inspecting pages and controls only:

```bash
PYTHONPATH=src python3 -m japan_real_estate_data_retriever.cli debug-local \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --state \
  --screenshot data/raw/suumo-local-debug.png \
  --out data/raw/suumo-local-debug.json
```

## Recommended Flow

1. Normalize the user request into query JSON.
2. Load the relevant `.agents/skills/japan-real-estate-data-retriever/references/site-*.md` workflow.
3. Use `run` for a single source or `run-all` for multi-source jobs; multi-source jobs must use one Cloud Browser session per source.
4. Let your agent drive CDP according to the workflow: filters, pagination, detail pages, extraction; write per-source raw data before normalization.
5. On navigation timeouts or `TargetClosedError`, reconnect to the same `cdpUrl` and reuse any loaded DOM before replacing the browser.
6. Normalize output to `schemas/unified_listing.schema.json`.
7. Retry browser-only per source or refine the workflow when results are incomplete.
8. Use `run-agent` as fallback or exploration, and fold learnings back into the workflow references.

## Data Schema

Canonical schema:

```bash
schemas/unified_listing.schema.json
```

Bundled skill copy:

```bash
.agents/skills/japan-real-estate-data-retriever/references/unified_listing.schema.json
```

The root schema is authoritative.

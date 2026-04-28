# Japan Real Estate Data Retriever

[English](README.md) | [中文](README.zh-CN.md)

This is a workflow-first project for retrieving Japanese real estate listings. Browser Use Cloud is treated primarily as cloud browser infrastructure with a Japan proxy. Your own agent should drive the browser through the project skills/workflows. Browser Use Cloud Agent v3 is kept as a fallback, repair, and exploration path.

## Quickstart

### For Humans

This project uses `uv` to manage the Python environment and run the project CLI. Install `uv` first if it is not already available. See the [official uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for platform-specific instructions.

```bash
uv --version
```

Set up the project with `uv`:

```bash
git clone <repo-url>
cd japan-real-estate-data-retriever
uv sync
```

If you want the CLI available from any working directory, install it as an editable uv tool. The installed command is `jreretrieve`:

```bash
make install-local
```

Provide your Browser Use Cloud API key through the environment. Do not commit real values:

```bash
export BROWSER_USE_API_KEY=bu_your_key_here
```

You can also store local auth in `~/.jreretrieve/config.toml`:

```toml
browser_use_api_key = "bu_your_key_here"
```

Verify the install:

```bash
jreretrieve --help
jreretrieve --json doctor
jreretrieve --json sources list
```

Validate a query and create a browser-only Cloud Browser session:

```bash
jreretrieve --json schema validate \
  --name query \
  --file examples/query.shibuya-google-rent-2ldk.json

jreretrieve run \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/suumo-browser-session.json
```

The output file contains `browser.cdpUrl` plus the site workflow context. Your local agent connects to that CDP URL, drives the page, writes per-source raw artifacts, normalizes results, and then stops the Cloud Browser:

```bash
jreretrieve stop-browser --browser-id <browser-session-id>
```

The examples below assume `jreretrieve` has been installed with `make install-local`.

### For Agents

Use this block when giving the README to an agent such as Hermes. It installs `uv` if needed, installs `jreretrieve` on `PATH`, and smoke-tests the installed command from outside the repository. Replace `<repo-url>` before running, or skip the `git clone` line when already inside a checkout.

```bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ ! -d japan-real-estate-data-retriever ]; then
  git clone <repo-url> japan-real-estate-data-retriever
fi

cd japan-real-estate-data-retriever
uv sync
make install-local

command -v jreretrieve
cd /tmp
jreretrieve --help
jreretrieve --json doctor
jreretrieve --json sources list
```

For live Browser Use Cloud commands, provide auth out of band. Agents must not print or commit real keys. The CLI reads auth in this order: `BROWSER_USE_API_KEY`, `~/.jreretrieve/config.toml`, then project `.env`.

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

Provide the Browser Use Cloud API key through the environment, user config, or a local `.env`. Never print or commit real values:

```bash
export BROWSER_USE_API_KEY=bu_your_key_here
```

Auth precedence is:

1. `BROWSER_USE_API_KEY` environment variable.
2. `~/.jreretrieve/config.toml` with `browser_use_api_key = "..."`.
3. Project-local `.env` for local runs.

Local development uses `uv`:

```bash
uv sync
uv run python -m unittest discover -s tests
```

If you are developing inside the repository and do not want to install the CLI, run it through the uv-managed environment:

```bash
uv run jreretrieve --json doctor
```

Install the agent-native CLI on PATH:

```bash
make install-local
jreretrieve --help
jreretrieve --json doctor
```

`make install-local` uses `uv tool install --editable . --force`, which installs the editable project as a uv-managed command-line tool.

## Usage

Use `jreretrieve` as the stable command layer after installing it with `make install-local`. Prefer `--json` for Codex or other agents.

Command surface:

- Install/name: `make install-local`, then `jreretrieve`.
- Setup: `jreretrieve --json doctor`.
- Discovery/resolve: `sources list`, `sources resolve <name>`, `sources get <source>`.
- Read local contracts: `schema show`, `schema validate`, `workflow show`.
- Primary live actions: `run`, `run-all`, `stop-browser`.
- Fallback live actions: `run-agent`, `stop-session`.
- Dry-run/preview: pass `--dry-run` to `run`, `run-all`, `run-agent`, or `create-browser`.
- Raw escape hatch: `request get /path` is read-only.

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

Create a primary browser-only session for one source:

```bash
jreretrieve run \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/suumo-browser-session.json
```

Create isolated browser sessions for multiple sources:

```bash
jreretrieve run-all \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --sources suumo athome homes yahoo_japan \
  --out data/raw/shibuya-google-browser-sessions.json
```

Stop browser sessions after extraction:

```bash
jreretrieve stop-browser \
  --browser-id <suumo-browser-id> <athome-browser-id> <homes-browser-id> <yahoo-browser-id>
```

JSON policy:

- `--json` writes machine-readable JSON to stdout only.
- Errors under `--json` use `{"ok": false, "error": {"message": "..."}}` and never include credentials.
- `doctor` reports the auth source category (`env`, `config`, `project_env`, or `missing`) without printing token values.
- `request get` returns the Browser Use API response object; live writes are intentionally not exposed through the raw escape hatch.

## Primary Browser-Only Path

Build a browser-only execution plan without calling external APIs:

```bash
jreretrieve build-task \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/suumo-browser-plan.json
```

Create a Cloud Browser session and write both `browser.cdpUrl` and workflow context:

```bash
jreretrieve run \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/suumo-browser-session.json
```

For multi-source jobs, use `run-all`; it creates one isolated Cloud Browser session per source:

```bash
jreretrieve run-all \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/shibuya-google-browser-sessions.json
```

You can also pass sources explicitly:

```bash
jreretrieve run-all \
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
jreretrieve stop-browser \
  --browser-id <browser-session-id>
```

Stop multiple Cloud Browsers:

```bash
jreretrieve stop-browser \
  --browser-id <suumo-browser-id> <athome-browser-id> <homes-browser-id> <yahoo-browser-id>
```

## Cloud Agent Fallback

Use Cloud Agent v3 only when browser-only execution fails, results are incomplete, or a site workflow needs discovery:

```bash
jreretrieve run-agent \
  --site yahoo_japan \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --model bu-mini \
  --max-cost-usd 5 \
  --out data/raw/yahoo-agent-session-result.json
```

Stop an active Agent session:

```bash
jreretrieve stop-session \
  --session-id <agent-session-id>
```

BYOK/provider keys are not stored here or passed through undocumented request fields. Configure BYOK in Browser Use if officially supported, then select the supported model with `--model`.

## Local Debugging

The local `browser-use` CLI is for inspecting pages and controls only:

```bash
jreretrieve debug-local \
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

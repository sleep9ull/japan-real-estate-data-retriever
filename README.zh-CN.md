# Japan Real Estate Data Retriever

[English](README.md) | [中文](README.zh-CN.md)

这是一个 workflow 优先的日本不动产信息检索项目。当前重点不是写死网页爬虫，而是沉淀稳定的 Browser Use Cloud workflow、通用 JSON Schema、来源隔离 ID 规则，以及未来 agent 可以调用的结构化输出。

## 目标

- 使用 Browser Use Cloud 的云端 agent 浏览器访问 SUUMO、at home、LIFULL HOME'S、Yahoo! JAPAN Real Estate。
- 为每个来源站点维护独立的 workflow 和字段映射参考。
- 将不同来源详情页数据统一为一个通用 JSON 格式。
- 保留一个稳定 JSON contract，供未来 agent workflow 使用。
- 支持未来 Hermes agent 或其他 agent 根据用户个性化不动产搜索需求调用。

## 目录结构

```text
.
├── skills/japan-real-estate-data-retriever/    # versioned Codex skill
│   ├── SKILL.md                         # agent workflow entrypoint
│   └── references/                      # site workflows, field mappings, design notes
├── schemas/unified_listing.schema.json  # canonical generic JSON Schema
├── src/japan_real_estate_data_retriever/  # single execution implementation
├── examples/                            # sample query requests
├── tests/                               # fast tests without external APIs
├── data/raw/                            # raw probe/session outputs
└── data/normalized/                     # normalized output files
```

## 前置条件

项目默认使用 **Browser Use Cloud**，通过 REST API 执行。上线/生产路径应使用这个默认 backend。请通过环境变量或本地 `.env` 提供 API key：

```bash
export BROWSER_USE_API_KEY=bu_your_key_here
```

可选：仅在明确指定或本地调试时安装 Browser Use CLI。CLI 不是生产默认执行路径。

```bash
curl -fsSL https://browser-use.com/cli/install.sh | bash
source ~/.zshrc
browser-use doctor
```

如果安装后仍提示 `browser-use: command not found`，新开一个终端，或直接使用安装环境里的完整路径：

```bash
~/.browser-use-env/bin/browser-use doctor
```

也可以给本项目显式指定 CLI 路径：

```bash
export BROWSER_USE_CLI="$HOME/.browser-use-env/bin/browser-use"
```

`browser-use doctor` 里的 `cloudflared not installed` 只影响 `browser-use tunnel`，普通本地 CLI 调试不需要。使用代理时出现 network warning 也不一定代表安装失败。

## 本地开发

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests
```

生成 Browser Use task payload，但不调用外部 API：

```bash
python -m japan_real_estate_data_retriever.cli build-task \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --out data/raw/suumo-task.json
```

发起云端任务前 dry-run：

```bash
python -m japan_real_estate_data_retriever.cli run \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --dry-run
```

执行真实任务。默认走 Browser Use Cloud REST API，并使用 `proxyCountryCode: "jp"`：

```bash
python -m japan_real_estate_data_retriever.cli run \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --out data/raw/suumo-session-result.json
```

使用本地 Browser Use CLI 做纯本地浏览器调试：

```bash
python -m japan_real_estate_data_retriever.cli debug-local \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --state \
  --screenshot data/raw/suumo-local-debug.png \
  --out data/raw/suumo-local-debug.json
```

如果 CLI 不在 `PATH` 里，也可以直接传路径：

```bash
python -m japan_real_estate_data_retriever.cli debug-local \
  --site suumo \
  --query-file examples/query.tokyo-condo.json \
  --browser-use-cli "$HOME/.browser-use-env/bin/browser-use" \
  --state
```

本地 debug 命令使用的是本机 `browser-use open`、`state`、`screenshot` 这类命令。它不会调用 Browser Use Cloud，也不会产出 canonical schema output。它用于检查站点导航、筛选控件、页面标签和截图，然后再更新 workflow。

生产 Cloud run 需要把真实 API key 放在环境变量或本地 `.env`，不要打印或提交。

## 参考文档

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

Browser Use Cloud v3 使用 `https://api.browser-use.com/api/v3` 和 `X-Browser-Use-API-Key` 请求头。本项目以上线默认路径使用 Browser Use Cloud REST API。本地 Browser Use CLI 调试是独立路径，只驱动本机浏览器。

## 数据 Schema

当前 canonical schema 是通用 JSON Schema：

```bash
schemas/unified_listing.schema.json
```

skill 内置副本 `skills/japan-real-estate-data-retriever/references/unified_listing.schema.json` 会与根目录 schema 保持同步，用作 agent reference。

项目 Python package 是 Browser Use payload 生成、云端执行、normalization 的唯一执行层。skill 只保留 agent workflow 和 reference。

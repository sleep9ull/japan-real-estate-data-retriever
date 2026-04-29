# Japan Real Estate Data Retriever

[English](README.md) | [中文](README.zh-CN.md)

这是一个 workflow 优先的日本不动产信息检索项目。核心思路是：**Browser Use Cloud 主要提供云端浏览器和日本代理，你自己的 agent 按项目 skills/workflow 驱动浏览器；Browser Use Cloud Agent v3 只作为兜底、修复和探索路径。**

## 快速开始

### macOS 本地开发安装

如果是在自己的 Mac 上开发，使用这一套安装方式：CLI 用 editable install，skill 用 symlink install，后续改项目源码和 skill 都会同步生效。本项目使用 `uv` 管理 Python 环境并运行项目 CLI。如果机器上还没有 `uv`，请先安装；不同平台的安装方式见 [uv 官方安装文档](https://docs.astral.sh/uv/getting-started/installation/)。

```bash
uv --version
```

用 `uv` 初始化项目环境：

```bash
git clone <repo-url>
cd japan-real-estate-data-retriever
uv sync
```

如果希望在任意工作目录直接调用 CLI，可以把项目作为 editable uv tool 安装。安装后的命令是 `jreretrieve`，它会指回当前 checkout，所以本地开发时修改源码后 CLI 能同步使用新代码：

```bash
make install-local
```

把 companion skill 以 symlink 方式安装到 agent 的 skills 目录。默认目标是 Hermes 风格的 `~/.agents/skills`：

```bash
make install-skill-dev
```

如果要安装到 Codex 默认目录，用：

```bash
make install-codex-skill-dev
```

本地开发时，也可以直接按这一组命令完成 CLI 和 Codex skill 安装并验证：

```bash
make install-local
make install-codex-skill-dev
make smoke
```

### Linux/Ubuntu 云服务器安装

如果是在 Lightsail、EC2 或其他 Ubuntu 云服务器上给 Hermes/agent 使用，使用这一套安装方式：CLI 仍然是 editable uv tool，skill 以 symlink 方式安装到 `~/.agents/skills`。

```bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y git curl make ca-certificates

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

git clone <repo-url> ~/japan-real-estate-data-retriever
cd ~/japan-real-estate-data-retriever

uv sync
make install-hermes-dev
```

用用户级配置提供 Browser Use Cloud API key，不要打印或提交真实值：

```bash
mkdir -p ~/.jreretrieve
chmod 700 ~/.jreretrieve
cat > ~/.jreretrieve/config.toml <<'EOF'
browser_use_api_key = "REPLACE_WITH_REAL_KEY"
EOF
chmod 600 ~/.jreretrieve/config.toml
```

从仓库外部验证安装：

```bash
cd /tmp
command -v jreretrieve
jreretrieve --json doctor
jreretrieve --json sources list
test -f ~/.agents/skills/japan-real-estate-data-retriever/SKILL.md
```

通过环境变量提供 Browser Use Cloud API key。不要提交真实值：

```bash
export BROWSER_USE_API_KEY=bu_your_key_here
```

也可以把本地认证放在 `~/.jreretrieve/config.toml`：

```toml
browser_use_api_key = "bu_your_key_here"
```

如果是 checkout 本地测试，可以把 `.env.example` 复制成 `.env.local` 后在本机填写。`.env.local` 会被 git 忽略：

```bash
cp .env.example .env.local
```

验证安装：

```bash
jreretrieve --help
jreretrieve --json doctor
jreretrieve --json sources list
```

验证查询文件，并创建一个 browser-only Cloud Browser session：

```bash
jreretrieve --json schema validate \
  --name query \
  --file examples/query.shibuya-google-rent-2ldk.json

jreretrieve run \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/suumo-browser-session.json
```

输出文件里会包含 `browser.cdpUrl` 和站点 workflow context。你的本地 agent 连接这个 CDP URL，驱动页面、写入 per-source raw artifacts、归一化结果，完成后停止 Cloud Browser：

```bash
jreretrieve stop-browser --browser-id <browser-session-id>
```

下面的示例默认已经通过 `make install-local` 安装了 `jreretrieve`，并通过 `make install-skill-dev` 或 `make install-codex-skill-dev` 安装了 skill symlink。

### 给 Agent 看的版本

如果要把这份 README 发给 Hermes/Codex 之类的 agent，可以让它按下面的命令安装。这个流程会在缺少 `uv` 时先安装 `uv`，再把 `jreretrieve` 作为 editable 命令安装到 `PATH`，把 repo skill symlink 到 `~/.agents/skills`，最后从仓库外部 smoke test。运行前请替换 `<repo-url>`；如果 agent 已经在仓库 checkout 里，可以跳过 `git clone` 那一行。

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
make install-hermes-dev

command -v jreretrieve
cd /tmp
jreretrieve --help
jreretrieve --json doctor
jreretrieve --json sources list
```

如果 agent 要执行 Browser Use Cloud live 命令，请通过外部方式提供认证。不要让 agent 打印或提交真实 key。CLI 的认证读取顺序是：`BROWSER_USE_API_KEY`、`~/.jreretrieve/config.toml`、项目 `.env.local`。

## 架构原则

- 主路径使用 Browser Use Cloud standalone browser：`POST /browsers`，固定 `proxyCountryCode: "jp"`。
- 多站点任务强制每个 source 单独创建 Cloud Browser session；不要在同一个 browser/context 里连续跑多个来源站点。
- 本地 agent 通过返回的 `cdpUrl` 接管云端浏览器，并按照本项目维护的站点 workflow 执行搜索、筛选、翻页和详情页抽取。
- Browser Use Cloud Agent v3：`POST /sessions`，仅用于 browser-only 失败、某站点流程变更、需要快速探索页面结构，或需要补足缺失结果时。
- 本地 `browser-use` CLI 只用于本机浏览器调试，不作为生产路径。
- 所有输出最终都要归一化到 `schemas/unified_listing.schema.json`。

## 目标

- 为 SUUMO、at home、LIFULL HOME'S、Yahoo! JAPAN Real Estate 维护独立 workflow 和字段映射。
- 将不同来源详情页数据统一为稳定 JSON/CSV 输出。
- 支持未来 Hermes agent 或其他 agent 根据用户个性化不动产搜索需求调用。
- 用确定性的站点 workflow 降低长期运行成本，并减少外部 Agent 自主判断带来的字段漂移。
- 保留 Cloud Agent fallback，提高 Yahoo、认证页、站点变化等复杂场景下的恢复能力。

## 目录结构

```text
.
├── skills/japan-real-estate-data-retriever/         # companion skill 源文件与站点 workflow
│   ├── SKILL.md
│   └── references/                               # site-*.md、字段映射、探测记录
├── schemas/unified_listing.schema.json           # canonical JSON Schema
├── src/japan_real_estate_data_retriever/         # Cloud API、CLI、normalization
├── examples/                                     # 示例查询
├── tests/                                        # 不依赖外部 API 的快速测试
├── data/raw/                                     # 原始 session/probe/browser 输出
└── data/exports/                                 # CSV 导出结果
```

## 前置条件

生产路径需要 Browser Use Cloud API key。可以从环境变量、用户级 config 或本地 `.env.local` 读取；不要打印或提交真实值：

```bash
export BROWSER_USE_API_KEY=bu_your_key_here
```

认证读取优先级：

1. `BROWSER_USE_API_KEY` 环境变量。
2. `~/.jreretrieve/config.toml` 中的 `browser_use_api_key = "..."`。
3. 项目本地 `.env.local`，用于 checkout 本地测试。

本地开发使用 `uv`：

```bash
uv sync
uv run python -m unittest discover -s tests
```

如果只在仓库内开发，不想安装 CLI，也可以通过 uv 管理的环境临时运行：

```bash
uv run jreretrieve --json doctor
```

把 agent-native CLI 安装到 PATH：

```bash
make install-local
jreretrieve --help
jreretrieve --json doctor
```

`make install-local` 使用 `uv tool install --editable . --force`，会把一个 uv 管理的命令 wrapper 安装到 PATH，同时让实现代码继续留在当前 checkout。

以开发 symlink 方式安装 companion skill：

```bash
make install-skill-dev
```

默认会把 `skills/japan-real-estate-data-retriever` 链接到 `~/.agents/skills/japan-real-estate-data-retriever`。如果要安装到 Codex 默认目录，用：

```bash
make install-codex-skill-dev
```

也可以覆盖目标目录：

```bash
make install-skill-dev SKILL_HOME="$HOME/.custom-agent/skills"
```

## 使用方法

执行 `make install-local` 后，使用 `jreretrieve` 作为稳定命令层；给 Codex、Hermes 或其他 agent 使用时优先加 `--json`。

命令面：

- CLI 安装/命令名：`make install-local`，之后使用 `jreretrieve`。
- Skill 安装：`make install-skill-dev` 安装到 `~/.agents/skills`，或 `make install-codex-skill-dev` 安装到 `~/.codex/skills`。
- 环境检查：`jreretrieve --json doctor`。
- 发现/解析：`sources list`、`sources resolve <name>`、`sources get <source>`。
- 读取本地契约：`schema show`、`schema validate`、`workflow show`。
- 主路径 live action：`run`、`run-all`、`stop-browser`。
- 兜底 live action：`run-agent`、`stop-session`。
- 预览/ dry-run：对 `run`、`run-all`、`run-agent` 或 `create-browser` 传 `--dry-run`。
- raw escape hatch：`request get /path`，只支持只读请求。

发现与环境检查：

```bash
jreretrieve --json doctor
jreretrieve --json sources list
jreretrieve --json sources resolve lifull
```

不启动浏览器，读取本地契约：

```bash
jreretrieve --json schema show --name unified-listing
jreretrieve --json schema validate --name query --file examples/query.shibuya-google-rent-2ldk.json
jreretrieve --json workflow show --site suumo --query-file examples/query.shibuya-google-rent-2ldk.json
```

只读 Browser Use API 逃生口：

```bash
jreretrieve --json request get /browsers/<browser-id>
```

为单个来源创建主路径 browser-only session：

```bash
jreretrieve run \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/suumo-browser-session.json
```

为多个来源创建相互隔离的 browser session：

```bash
jreretrieve run-all \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --sources suumo athome homes yahoo_japan \
  --out data/raw/shibuya-google-browser-sessions.json
```

抽取完成后停止 browser session：

```bash
jreretrieve stop-browser \
  --browser-id <suumo-browser-id> <athome-browser-id> <homes-browser-id> <yahoo-browser-id>
```

JSON 约定：

- `--json` 只向 stdout 输出机器可读 JSON。
- `--json` 下的错误形如 `{"ok": false, "error": {"message": "..."}}`，且不会包含凭证。
- `doctor` 只报告 auth 来源类别：`env`、`config`、`project_env_local` 或 `missing`，不打印 token。
- `request get` 返回 Browser Use API 原始响应对象；raw escape hatch 暂不提供 live write。

可选：仅在本地浏览器调试时安装 Browser Use CLI：

```bash
curl -fsSL https://browser-use.com/cli/install.sh | bash
source ~/.zshrc
browser-use doctor
```

## 主路径：Browser-only

生成 browser-only 执行计划，不调用外部 API：

```bash
jreretrieve build-task \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/suumo-browser-plan.json
```

创建 Cloud Browser session，并输出 `browser.cdpUrl` 和本地 agent workflow context：

```bash
jreretrieve run \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/suumo-browser-session.json
```

多站点任务使用 `run-all`，它会按来源站点强制单开 session：

```bash
jreretrieve run-all \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --out data/raw/shibuya-google-browser-sessions.json
```

也可以显式指定来源：

```bash
jreretrieve run-all \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --sources suumo athome homes yahoo_japan \
  --out data/raw/shibuya-google-browser-sessions.json
```

你的 agent 接下来应读取 `data/raw/suumo-browser-session.json`：

- `browser.cdpUrl`：用 Playwright/Puppeteer/CDP 连接云端浏览器。
- `workflow.instructions`：站点执行手册，包含筛选、详情页优先级、字段要求。
- `workflow.browserOnlyExecutionPolicy` / `executionPolicy`：browser-only 运行规程，包含重连、DOM 复用、失败隔离和停止 session 的规则。
- `workflow.outputSchema`：最终结构化输出必须符合的 schema。

browser-only 执行时建议按来源站点拆成短任务：

1. 连接该 source 的 `cdpUrl`。
2. 导航到目标页面，或复用已经加载好的当前页面。
3. 先落 per-source raw HTML/JSON，再做本地归一化和排序。
4. 如果 `Page.goto` 超时，但页面已经开始加载，先重连同一个 `cdpUrl` 检查当前 DOM。
5. 如果遇到 `TargetClosedError`，先重连同一个 `cdpUrl`；只要 `document.title` 和站点列表 selector 存在，就直接复用已加载 DOM 抽取。
6. 只有当前 browser 无法重连或 DOM 不可用时，才为该 source 重建 Cloud Browser。

任务完成后停止 Cloud Browser：

```bash
jreretrieve stop-browser \
  --browser-id <browser-session-id>
```

停止多个 browser session：

```bash
jreretrieve stop-browser \
  --browser-id <suumo-browser-id> <athome-browser-id> <homes-browser-id> <yahoo-browser-id>
```

## 兜底路径：Cloud Agent v3

当 browser-only 失败、某站点页面变化、需要快速探索或补足结果时，使用 Cloud Agent fallback：

```bash
jreretrieve run-agent \
  --site yahoo_japan \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --model bu-mini \
  --max-cost-usd 5 \
  --out data/raw/yahoo-agent-session-result.json
```

停止仍在运行的 Agent session：

```bash
jreretrieve stop-session \
  --session-id <agent-session-id>
```

BYOK/provider key 不写入本仓库，也不通过未公开字段传递。如果 Browser Use 对项目/model 开启 BYOK，请按官方流程在 Browser Use 侧配置，然后在本项目用 `--model` 选择受支持的 model id。

## 本地调试路径

本地 `browser-use` CLI 只用于观察页面、截图和调试站点控件，不产出 canonical schema：

```bash
jreretrieve debug-local \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --state \
  --screenshot data/raw/suumo-local-debug.png \
  --out data/raw/suumo-local-debug.json
```

如果 CLI 不在 `PATH`：

```bash
jreretrieve debug-local \
  --site suumo \
  --query-file examples/query.shibuya-google-rent-2ldk.json \
  --browser-use-cli "$HOME/.browser-use-env/bin/browser-use" \
  --state
```

## 推荐执行流

1. 将用户需求规范化为 query JSON。
2. 按来源站点读取 checkout 内的 `skills/japan-real-estate-data-retriever/references/site-*.md`，或读取 agent skills 目录下的已安装 symlink。
3. 单站点用 `run` 创建 Cloud Browser；多站点用 `run-all`，确保每个来源站点一个独立 Cloud Browser session。
4. 你的 agent 通过 CDP 按站点 workflow 执行筛选、翻页、详情页抽取；每个 source 先写 raw，再做本地归一化。
5. 如果出现导航超时或 `TargetClosedError`，先重连同一个 `cdpUrl` 并复用已加载 DOM。
6. 归一化到 `schemas/unified_listing.schema.json`。
7. 如果数量不足、站点阻断或字段缺失，先 browser-only 单站重试或调整 workflow。
8. 仍失败时用 `run-agent` 作为 fallback，并把结果差异写入 workflow 参考文档。

## 参考文档

- `skills/japan-real-estate-data-retriever/SKILL.md`
- `skills/japan-real-estate-data-retriever/references/overall-workflow.md`
- `skills/japan-real-estate-data-retriever/references/search-filter-capabilities.md`
- `skills/japan-real-estate-data-retriever/references/unified-fields.md`
- `skills/japan-real-estate-data-retriever/references/source-id-strategy.md`
- `skills/japan-real-estate-data-retriever/references/site-suumo.md`
- `skills/japan-real-estate-data-retriever/references/site-athome.md`
- `skills/japan-real-estate-data-retriever/references/site-homes.md`
- `skills/japan-real-estate-data-retriever/references/site-yahoo-japan.md`

## 数据 Schema

canonical schema：

```bash
schemas/unified_listing.schema.json
```

skill 内置副本：

```bash
skills/japan-real-estate-data-retriever/references/unified_listing.schema.json
```

根目录 schema 是权威版本。修改 schema 时要同步 skill 内置副本。

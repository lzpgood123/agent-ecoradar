# Prompt: Goal A — Project Packaging / Reusable Tracker

你现在要在 `/root/workspace/search in coding` 中执行 **Goal A：项目搭建打包与可复用化**。

## 背景

这是一个 AI Coding Agent 生态追踪项目，重点追踪：

- Claude Code
- OpenAI Codex CLI
- Antigravity CLI / former Gemini CLI
- OpenCode
- Goose
- Qoder / QoderWork
- Trae / Trae Work / Trae Agent
- WorkBuddy / CodeBuddy
- Cursor
- Hermes Agent

这些工具的说明文件已存在于 `/root/workspace/ai-coding-agents/`。请读取这些文件并抽取种子数据。

## 目标

把本项目打包成一个可复用的长期追踪模板，后续可复用到其他生态。

## 必须完成

1. 创建完整目录结构。
2. 创建 `README.md`、`pyproject.toml`、`.env.example`、`.gitignore`。
3. 创建 `data/seed-tools.yaml`、`data/queries.yaml`、`data/sources.yaml`、`data/projects.yaml`、`data/concepts.yaml`。
4. 创建 `schemas/project.schema.json`、`schemas/source.schema.json`、`schemas/tool.schema.json`、`schemas/concept.schema.json`。
5. 创建文档：
   - `docs/taxonomy.md`
   - `docs/methodology.md`
   - `docs/source-strategy.md`
   - `docs/scoring.md`
   - `docs/reusable-packaging.md`
6. 创建脚本：
   - `scripts/validate_data.py`
   - `scripts/collect_github.py`
   - `scripts/collect_exa.py`
   - `scripts/collect_web.py`
   - `scripts/normalize.py`
   - `scripts/score.py`
   - `scripts/build_site.py`
   - `scripts/export_pack.py`
7. 创建静态站点骨架：
   - `site/index.html`
   - `site/app.js`
   - `site/styles.css`
8. 创建 GitHub Actions 模板：
   - `.github/workflows/update-data.yml`
   - `.github/workflows/publish-site.yml`
9. 创建 Hermes cron prompt 模板：
   - `.hermes/cron-prompts/daily-discovery.md`
   - `.hermes/cron-prompts/weekly-report.md`
10. 创建提示词库或更新现有 `prompts/`。

## 技术要求

- Python 使用 `python3`。
- GitHub 搜索必须通过 `gh`。
- Exa 是优先语义搜索来源；默认调用方式是 `mcporter call 'exa.web_search_exa(query: "...", count: 3)'`，Agent Reach venv 已激活状态下可用。不要只检查 `exa` CLI。若 mcporter/Exa 不可用，再实现 `EXA_API_KEY` HTTP API 适配器或明确报错。
- 不要把密钥写入仓库。
- 所有脚本必须支持 `--help`。
- `collect_github.py` 至少支持 `--dry-run` 和 `--limit`。
- `collect_exa.py` 至少支持 `--dry-run` 和 `--limit`。
- `validate_data.py` 必须能校验 YAML/JSON 基本字段。
- `build_site.py` 必须把 YAML 数据导出成 `site/data/*.json`。
- `export_pack.py --dry-run` 必须列出将要打包的文件。

## 验证

完成后实际运行：

```bash
python3 scripts/validate_data.py
python3 scripts/collect_github.py --dry-run --limit 5
python3 scripts/collect_exa.py --dry-run --limit 5
python3 scripts/build_site.py
python3 scripts/export_pack.py --dry-run
```

如果缺少依赖，优先使用标准库；如必须安装依赖，创建 venv 或使用已有环境，不要污染系统 Python。

## 输出

最终回复请包含：

- 创建/修改了哪些关键文件。
- 验证命令真实输出摘要。
- 哪些功能是 MVP，哪些需要后续增强。
- Exa/mcporter 调用验证结果；如不可用，说明 fallback 状态。

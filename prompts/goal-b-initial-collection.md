# Prompt: Goal B — Initial Collection Completed

你现在要在 `/root/workspace/search in coding` 中执行 **Goal B：项目收集完成与初始生态分析**。

## 前提

Goal A 应已完成，项目中应存在：

- `data/seed-tools.yaml`
- `data/queries.yaml`
- `scripts/collect_github.py`
- `scripts/collect_exa.py`
- `scripts/normalize.py`
- `scripts/score.py`
- `scripts/build_site.py`
- `scripts/validate_data.py`

如果不存在，请先暂停并说明需要先执行 Goal A。

## 目标

围绕以下 10 个目标工具完成第一批生态资料收集、归类、评分、分析和可视化：

1. Claude Code
2. OpenAI Codex CLI
3. Antigravity CLI / former Gemini CLI
4. OpenCode
5. Goose
6. Qoder / QoderWork
7. Trae / Trae Work / Trae Agent
8. WorkBuddy / CodeBuddy
9. Cursor
10. Hermes Agent

## 收集范围

收集以下类型：

- 官方仓库、文档、博客、changelog
- 扩展应用
- 插件
- MCP / ACP / A2A server
- skills / prompts / slash commands
- rules / instructions / config templates
- context engineering 工具
- codebase indexing / repo map / graph RAG
- PR review / issue fixing / CI 自动化
- 教程、经验文章、case study
- benchmark / comparison / evaluation
- 可视化管理界面
- 多 agent 工作流
- 安全、沙箱、权限控制经验

## 搜索要求

### GitHub

必须使用 `gh`，不要优先使用 unauthenticated curl。

对每个工具和每个核心概念执行 GitHub 搜索，保存 raw 结果到：

```text
data/raw/github/YYYY-MM-DD/
```

示例查询：

```bash
gh search repos "claude code skills" --sort stars --limit 50 --json fullName,description,stargazersCount,url,updatedAt,language
gh search repos "codex cli AGENTS.md" --sort stars --limit 50 --json fullName,description,stargazersCount,url,updatedAt,language
gh search repos "cursor rules" --sort stars --limit 50 --json fullName,description,stargazersCount,url,updatedAt,language
gh search repos "mcp server coding agent" --sort stars --limit 50 --json fullName,description,stargazersCount,url,updatedAt,language
```

对入选 repo 使用：

```bash
gh repo view OWNER/REPO --json nameWithOwner,description,url,homepageUrl,stargazerCount,forkCount,licenseInfo,repositoryTopics,primaryLanguage,pushedAt,createdAt,updatedAt,isArchived,latestRelease
```

### Exa

互联网语义搜索优先使用 Exa。默认调用方式：

```bash
mcporter call 'exa.web_search_exa(query: "Claude Code ecosystem extensions plugins MCP skills rules best practices", count: 3)'
```

`mcporter` 在 Agent Reach venv 已激活状态下可用。不要只检查 `exa` CLI。每个目标工具至少搜索：

```text
{tool} ecosystem extensions plugins MCP skills rules best practices
{tool} tutorial workflow agentic coding case study
{tool} context engineering codebase indexing rules prompts
{tool} GitHub projects open source extensions
```

如果 mcporter/Exa 未配置或调用失败，清楚说明并使用 curl 抓取百度/Bing 等备用来源，但不要伪造 Exa 结果。

## 数量目标

最低完成：

- 总记录数 ≥ 100。
- GitHub repo ≥ 60。
- 非 GitHub 互联网资料 ≥ 30。
- 每个目标工具 ≥ 10 条相关记录。
- 深度分析/人工审核记录 ≥ 30。

如果因为网络或 API 限制无法达到，必须说明真实阻塞，并尽量保存部分结果。

## 数据处理

1. 保存 raw 结果。
2. 归一化到 `data/projects.yaml`。
3. 去重。
4. 分类。
5. 评分。
6. 标记 `review_state`。
7. 生成 site JSON。
8. 生成报告。

## 报告文件

必须生成：

- `docs/reports/initial-collection-report.md`
- `docs/reports/top-projects.md`
- `docs/reports/tool-ecosystem-comparison.md`
- `docs/reports/trends-and-opportunities.md`

## 验证

执行：

```bash
python3 scripts/validate_data.py
python3 scripts/score.py
python3 scripts/build_site.py
```

并统计：

- `data/projects.yaml` 总记录数。
- GitHub 记录数。
- 非 GitHub 记录数。
- 每个 target tool 的记录数。
- 每个 category 的记录数。

## 输出

最终回复请包含：

- 收集总量。
- 主要来源。
- Top 10 项目。
- 关键趋势。
- 生成的报告路径。
- 验证命令真实输出摘要。
- 未解决问题和下一步建议。

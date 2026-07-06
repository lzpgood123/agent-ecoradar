# Prompt: Exa Semantic Search

在 `/root/workspace/search in coding` 中执行 Exa 语义搜索。

## 规则

- Exa 是互联网搜索的首选来源。
- 默认调用方式：`mcporter call 'exa.web_search_exa(query: "...", count: 3)'`。
- `mcporter` 在 Agent Reach venv 已激活状态下可用；不要只检查 `exa` CLI。
- 如果 mcporter/Exa 不可用，再尝试 `EXA_API_KEY` HTTP API。
- 如果 Exa 全部不可用，明确说明并停止 Exa 搜索，不要伪造结果；fallback 可用 curl 抓取百度/Bing，但必须标注来源不是 Exa。
- 保存 raw 结果到 `data/raw/exa/YYYY-MM-DD/`。
- 结果要归一化到 `data/projects.yaml` 或 `data/sources.yaml`。

## 搜索目标

围绕 10 个工具和核心概念，寻找：

- 官方文档
- launch post
- changelog
- 教程
- best practices
- comparison
- case study
- 社区经验
- 插件/扩展介绍
- MCP/skills/rules 使用案例
- 中文资料

## 推荐 query 模板

```text
{tool} ecosystem extensions plugins MCP skills rules best practices
{tool} tutorial workflow agentic coding case study
{tool} context engineering codebase indexing rules prompts
{tool} GitHub projects open source extensions
{tool} changelog release new features agent coding
{tool} comparison Claude Code Codex Cursor OpenCode Goose
```

核心概念 query：

```text
AI coding agent context engineering best practices
AI coding agent skills prompts rules repository
MCP servers for coding agents GitHub
spec driven development AI coding agents
terminal AI coding agents comparison
Claude Code skills best practices
Codex CLI AGENTS.md workflows
Cursor rules MCP agent workflows
OpenCode agents commands MCP
Goose recipes extensions MCP
Hermes Agent cron skills coding workflow
```

中文 query：

```text
Claude Code 使用经验 技巧 MCP skills
Codex CLI 使用教程 AGENTS.md
Cursor Rules 最佳实践 MCP
OpenCode 使用教程 MCP
Goose AI Agent 教程 MCP
AI Coding Agent 上下文工程 实践
AI 编程 Agent 生态 工具 对比
```

## 输出报告

生成：

- `docs/reports/exa-discovery-YYYY-MM-DD.md`

报告包含：

- 搜索 query
- 高质量来源
- 噪声来源
- 值得加入数据集的条目
- 需要人工复核的条目

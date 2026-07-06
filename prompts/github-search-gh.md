# Prompt: GitHub Search via gh

在 `/root/workspace/search in coding` 中执行 GitHub 搜索采集。

## 规则

- 必须使用已登录的 `gh`。
- 保存 raw JSON 到 `data/raw/github/YYYY-MM-DD/`。
- 不要只看 stars，要保留 topics、license、pushedAt、release 信息。
- 对高相关 repo 再执行 `gh repo view` 补充元数据。

## 搜索对象

目标工具：Claude Code、Codex CLI、Antigravity/Gemini CLI、OpenCode、Goose、Qoder、Trae、WorkBuddy/CodeBuddy、Cursor、Hermes Agent。

概念：MCP、ACP、A2A、skills、rules、AGENTS.md、CLAUDE.md、context engineering、codebase indexing、repo map、PR review、SWE agent、spec-driven development、multi-agent coding。

## 推荐查询

```text
claude code skills
claude code mcp
claude code best practices
codex cli AGENTS.md
codex cli skills
openai codex coding agent
antigravity cli plugin
gemini cli extension
opencode agent commands
opencode mcp
goose recipes extensions
goose mcp agent
qoder ai coding
trae agent mcp
codebuddy ai coding
workbuddy agent skills
cursor rules
cursor mcp
hermes agent skills
hermes agent cron coding
AI coding agent context engineering
mcp server coding agent
AI PR review agent
spec driven development AI coding
codebase indexing AI coding agent
```

## 输出

生成或更新：

- `data/raw/github/YYYY-MM-DD/*.json`
- `data/projects.yaml` 候选记录
- `docs/reports/github-discovery-YYYY-MM-DD.md`

报告包含：

- 查询列表
- 结果数量
- 候选 Top 30
- 噪声关键词
- 推荐后续深挖 repo

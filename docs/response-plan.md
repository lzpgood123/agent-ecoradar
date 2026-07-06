# Search in Coding 响应计划

## 项目定位

`search in coding` 是一个围绕终端型 / Agentic AI Coding 工具的长期生态追踪项目。它的核心不是简单收藏链接，而是持续发现、归类、评分、分析和可视化 AI Coding Agent 生态中的高价值工具、插件、经验和方法论。

## 聚焦对象

第一阶段聚焦：

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

## 两个 Goal

### Goal A：项目搭建打包

把项目建设成一个可复用的追踪模板。

交付物：

- 数据结构
- 分类体系
- 脚本
- 可视化站点
- GitHub Actions
- Hermes cron prompts
- 可复用打包说明

### Goal B：项目收集完成

完成第一批真实生态数据采集和分析。

交付物：

- 至少 100 条结构化记录
- GitHub raw 数据
- Exa/web raw 数据
- 评分结果
- Top 项目报告
- 工具生态对比报告
- 趋势分析报告
- 可视化页面数据

## 执行顺序

建议严格按以下顺序执行：

1. 执行 `prompts/goal-a-project-packaging.md`。
2. 验证 Goal A 的脚本和目录结构。
3. 执行 `prompts/goal-b-initial-collection.md`。
4. 对收集结果执行 `prompts/normalize-and-score.md`。
5. 对 Top 项目使用 `prompts/deep-dive-template.md` 做深度分析。
6. 设置 Hermes cron 使用 `prompts/weekly-report.md`。

## 信息来源策略

### GitHub

- 使用 `gh search repos`。
- 使用 `gh repo view` 补充元数据。
- 保存 raw JSON。
- 不只依赖 stars。

### Exa

- 作为互联网语义搜索首选。
- 查找博客、教程、经验、评测、changelog、社区讨论。
- 默认调用方式：`mcporter call 'exa.web_search_exa(query: "...", count: 3)'`。
- `mcporter` 在 Agent Reach venv 已激活状态下可用。
- 若 `mcporter` / Exa 暂不可用，fallback 为 curl 抓取百度/Bing，但必须明确标注不是 Exa 结果。

### 官方资料

- 官方 docs
- 官方 blog
- GitHub org/repo
- release/changelog
- marketplace/extension registry

### 社区资料

- Hacker News
- Reddit
- X/Twitter
- YouTube
- Dev.to / Medium / Substack
- 中文社区：知乎、掘金、CSDN、少数派、B站等

## 核心分类

- official-tool
- terminal-agent
- ai-ide
- agent-harness
- rules-instructions
- skills-prompts
- mcp-acp-a2a
- context-engineering
- testing-review-ci
- multi-agent-workflow
- tutorial-case-study
- benchmark-evaluation
- ui-dashboard
- security-sandbox

## Hermes 长期自动追踪设计

### 每日任务

- 使用 GitHub query 搜索新增/更新项目。
- 使用 Exa 搜索最新文章、教程、changelog。
- 保存 raw 数据。
- 标记候选项目。

### 每周任务

- 归一化和评分。
- 生成周报。
- 更新可视化数据。
- 列出需要人工审核的 Top 候选。

### 每月任务

- 生成深度趋势分析。
- 更新工具生态对比。
- 清理低质量/失效来源。
- 打包发布可复用模板。

## 验收标准

### Goal A 验收

```bash
python3 scripts/validate_data.py
python3 scripts/collect_github.py --dry-run --limit 5
python3 scripts/collect_exa.py --dry-run --limit 5
python3 scripts/build_site.py
python3 scripts/export_pack.py --dry-run
```

全部可运行，不出现未处理异常。

### Goal B 验收

```bash
python3 scripts/validate_data.py
python3 scripts/score.py
python3 scripts/build_site.py
```

并满足：

- 总记录数 ≥ 100。
- GitHub repo ≥ 60。
- 非 GitHub 来源 ≥ 30。
- 每个目标工具 ≥ 10 条相关记录。
- 报告文件齐全。

## 当前已知前提

- `gh` 已安装并登录。
- `/root/workspace/ai-coding-agents` 已有 10 个目标工具说明文件。
- `/root/workspace/search in coding` 是项目工作目录。
- Exa 语义搜索应通过 `mcporter call 'exa.web_search_exa(query: "...", count: 3)'` 调用；不要只检查是否存在 `exa` CLI。

## 下一步

当用户发出执行指令时，优先执行：

```text
prompts/goal-a-project-packaging.md
```

Goal A 完成并验证后，再执行：

```text
prompts/goal-b-initial-collection.md
```

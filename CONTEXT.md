# Search in Coding

一个持续自动更新的 AI Coding Agent 生态追踪索引库，每天自动发现、归一化、评分、发布生态数据。GitHub 是总仓库，正式站点是展示面。

## Language

### 追踪对象

**Resource**:
被系统追踪的一条生态记录。每条 Resource 对应一个外部 URL（GitHub 仓库、博客文章、社区帖子等），经过归一化后存入 `data/projects.yaml`。
_Avoid_: entry, item, record

**Target Tool**:
系统追踪的 10 个 AI Coding Agent 之一（如 Claude Code、Codex CLI、Cursor）。定义在 `data/seed-tools.yaml` 中，每个工具有 `extension_points` 和 `related_concepts`。Target Tool 自身也是一种 Resource（`record_kind=official-tool`）。
_Avoid_: tracked tool, monitored tool

**Official Tool**:
`record_kind=official-tool` 的 Resource，指 10 个目标工具自身的记录。在排名展示中单独列出（`ranking_scope=official`），不参与生态排名。
_Avoid_: seed tool, base tool

**Ecosystem Project**:
`record_kind=ecosystem-project` 的 Resource，指围绕目标工具的第三方项目（MCP 服务器、skills 集合、rules 模板等）。参与生态排名（`ranking_scope=ecosystem`）。
_Avoid_: community project, third-party project

**Learning Resource**:
`ranking_scope=learning-resource` 的 Resource，指教程、文章、案例研究等非项目类内容。展示但排名权重低于 Ecosystem Project。
_Avoid_: tutorial, article, content

### 记录生命周期

**Record Kind**:
Resource 的类型标签，决定展示方式但不决定排名。取值：`official-tool`、`ecosystem-project`、`article`、`tutorial`、`fallback-result`。
_Avoid_: type, category（category 是另一个字段）

**Source Type**:
Resource 的采集来源类型，决定初始 `source_quality`。取值：`github`、`exa`、`fallback-web`、`official-seed`。
_Avoid_: origin, channel

**Source Quality**:
来源可信度分级，影响评分中的 `confidence` 维度。取值：`verified`（GitHub + official-seed）、`fallback`（fallback-web）、`unverified`（其他）。
_Avoid_: trust level, credibility

**Review State**:
Resource 的自动审核状态，由评分系统驱动。取值：`auto-indexed`（默认入索引）、`auto-curated`（推荐集）、`auto-rejected`（噪声集）。
_Avoid_: status, approval state

**Ranking Scope**:
Resource 在站点展示中的排名范围。取值：`official`（官方工具区）、`ecosystem`（生态排名）、`learning-resource`（学习资源）、`excluded`（被拒绝，不展示在排名中）。
_Avoid_: display scope, visibility

**Curated**:
被自动推荐集（`data/curated-projects.yaml`）选中的 Resource，`review_state=auto-curated`。由评分和覆盖规则决定，非人工审核。
_Avoid_: featured, recommended, approved

**Rejected**:
被自动噪声集（`data/rejected-projects.yaml`）标记的 Resource，`review_state=auto-rejected`。分数过低或来源不可信。
_Avoid_: blocked, denied, spam

### 评分与分类

**Score**:
Resource 的综合评分（0-30），由 6 个维度（ecosystem_value, activity, adoption, practicality, novelty, confidence）各 0-5 分组成，加上 source_weight、category_weight 调整，减去 penalty。
_Avoid_: rating, grade, rank

**Score Reason**:
评分分解记录，包含 base（6 维度合计）、source_weight、category_weight、penalty 四个分量，用于详情展示和评分审计。
_Avoid_: score breakdown, score detail

**Category**:
Resource 的生态分类标签（多值），由 `normalize.py` 中的 CATEGORY_RULES 关键词匹配决定。取值如 `mcp-acp-a2a`、`skills-prompts`、`rules-instructions` 等。
_Avoid_: tag, label, topic

**Relevance Score**:
（设计中）0-1 浮点数，衡量 Resource 内容与 AI coding agent 生态的相关性。低于 0.3 自动 reject。
_Avoid_: match score, quality score

### 采集管道

**Pipeline**:
从采集到部署的完整数据处理流程，由 `update_tracker.py` 编排。顺序：collect -> normalize -> enrich_i18n -> validate -> score -> finalize -> enrich_i18n -> report -> build -> quality_gate -> deploy。
_Avoid_: workflow, process, pipeline（小写泛指时不用大写）

**Snapshot**:
（设计中）每次 pipeline 运行时的数据快照，记录当日记录数、分类分布、工具覆盖、平均分等，存入 `data/snapshots/YYYY-MM-DD.json`，用于趋势分析。
_Avoid_: checkpoint, state dump

**Quality Gate**:
Pipeline 末尾的验证检查（`quality_gate.py`），确保数据完整性、覆盖指标、i18n 完整性达标。未通过则阻断部署。
_Avoid_: validation, check, gate（小写泛指时不用大写）

## Concepts (参考)

以下概念定义在 `data/concepts.yaml` 中，与 Target Tool 的 `related_concepts` 关联：

**Agentic Coding**: AI agents that plan, edit files, run commands, test, and iterate.
**Context Engineering**: Preparing instructions, repo maps, memory, docs and retrieval for coding agents.
**MCP (Model Context Protocol)**: Protocol for connecting tools and data sources to AI agents.
**Skills**: Reusable packaged agent workflows, prompts, references and scripts.
**Rules / Instructions**: CLAUDE.md, AGENTS.md, Cursor rules and similar behavioral guidance.
**Multi-agent Coding**: Planner/builder/reviewer/tester agent collaboration.
**Spec-driven Development**: Requirements and specs drive implementation by agents.
**Codebase Indexing**: Code graph, repo map, semantic search and RAG for repositories.

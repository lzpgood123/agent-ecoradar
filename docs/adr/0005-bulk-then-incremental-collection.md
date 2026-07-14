# ADR-0005: 一次性历史回溯 + 增量更新采集模式

## Status: accepted（2026-07-14 修订）

## Context

原采集模式是每日用固定 query 搜索 GitHub + Exa + fallback-web，广撒网式采集。当采集源收缩到仅 GitHub 后，GitHub 是结构化可穷举的数据源，不需要每天大量搜索。

2026-07-14 grilling 决议修订历史回溯策略：时间下界从「仅 2025-01 起」改为 **2024-01-01 起**；搜索改为 **stars 分层**，不再依赖单一月分片穷举；**dependents API 本轮不做**（REST 不可用）。

## Decision

### 三阶段采集模式

1. **一次性历史回溯**（本任务）：独立脚本 `scripts/initial_collection.py`，手动触发，断点续传。
2. **每日增量**：刷新 track 项目数据 + 搜索当天新项目（`created:>{today-1day}`）。
3. **每周 LLM 分析**：分析新增 + 重评全部。

### 历史回溯策略（2026-07-14）

| 层级 | stars | 分片 | 搜索 | 过滤 |
|------|-------|------|------|------|
| L1 | ≥100000 | 全时段 | 无关键词 + `created:>2024-01-01` | 极薄负向 |
| L2 | 50000–99999 | 全时段 | 同上 | 极薄负向 |
| L3 | 10000–49999 | 全时段 | 同上 | 极薄负向 |
| L4 | 1000–9999 | 按月 | 无关键词 + 月范围 | 负向 + 弱正向（详情前再要求 coding signal） |
| L5a | 500–999 | adaptive | topic + keyword | 严格正负向 |
| L5b | 100–499 | adaptive | topic + keyword | 严格正负向 |
| — | <100 | — | 本轮不做 | — |

- **执行顺序**：L1 → L2 → L3 → L4 → L5a → L5b → code search
- **adaptive（L5）**：先全时段探测；单 query 触顶（约 300）再按月拆分
- **code search**：`filename:CLAUDE.md` / `.cursorrules` / `AGENTS.md` 等；入库 `tracking_priority=pending`
- **安全 merge**：更新 GitHub 可量化字段；**保留** LLM/人工字段（`quality_score`/`quality_detail`/`tracking_priority`/`last_analyzed`/`benchmark_ref` 等）；`official-seed` 不降级
- **checkpoint**：搜索键 `tier|query|month_or_all` + 详情 `completed_details`；候选集落盘 `data/raw/github-initial/candidates.json`
- **本轮明确不做**：`/repos/{owner}/{repo}/dependents`、README 内链抽生态、stars&lt;100

### 覆盖率

每工具 / resource_type 最低数量 + 已知重点项目校验（由 weekly analysis / quality_gate 承担，不在 bulk 脚本里放宽过滤凑数）。

## Consequences

- 候选量可达数千；详情阶段耗时与 core API 配额成正比（可用 `--no-readme` 加速 bulk，README 可后续 enrich）
- L5 全量「query×月」不可行 → adaptive 降低 search 次数
- 每日请求量仍从数百降到约 50–100 次（增量路径）
- 断点续传 + candidates 持久化保证中断可恢复

## Execution note（2026-07-14 本机一次 bulk）

- 候选 **6016**（L1–L5b + code）；`completed_details` **6016**
- `data/projects.yaml` **293 → 5165**；`last_analyzed` **33** 未丢失；official-seed **10 track**
- stats 摘要：`added≈4856`，`updated≈48`，`filtered≈1085`（含 code 路径 strict），`detail_errors=1`
- 本地 `python3 scripts/update_tracker.py --skip-collect` **PASS**（未 `--deploy`）

## Related

- handoff: `docs/superpowers/handoff/2026-07-14-initial-collection-prompt.md`
- script: `scripts/initial_collection.py`
- tests: `tests/test_initial_collection.py`

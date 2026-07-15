# 后批量优化设计：性能 + 补全 + 分类 + LLM 策略

> 日期：2026-07-14  
> 状态：待执行（已 grilling 确认）  
> 作者：方案设计 Agent  
> 前置：一次性历史回溯 bulk 采集已完成（293 → 5165 条），本地 commits 未全部 push，**尚未 deploy**

## 背景

2026-07-14 完成历史回溯 bulk 采集，`data/projects.yaml` 从 293 条增长到 5165 条（github 5155 + official-seed 10）。当前存在 5 个关键问题：

| # | 问题 | 当前数据 | 影响 |
|---|------|---------|------|
| 1 | tutorial 兜底占比过高 | 2699/5165 = **52.3%** | 分类失真 |
| 2 | general-ai-coding 占比过高 | 3210/5165 = **62.1%** | 工具覆盖不均衡 |
| 3 | readme_preview 填充率极低 | 291/5165 = **5.6%** | LLM 分析缺关键输入 |
| 4 | LLM 分析大量 pending | 5120/5165 = **99.1%** 未分析 | 无法在合理时间内消化 |
| 5 | 前端性能隐患 | `projects.json` **6.1MB**、`projects-detail.json` **8.8MB** | 首屏/搜索/详情过慢 |

### 问题根因（摘要）

- **tutorial / general-ai-coding 过高**：`normalize.py` 的 `resource_types_for()` / `target_tools_for()` 主要匹配 `name + description`，未用 `topics`。
- **readme_preview 低**：bulk 用 `--no-readme` 加速；`enrich_projects.py` 尚未批量跑。
- **LLM pending**：并发偏低 + 无 stars 优先 + 首次 backlog 超大。
- **前端性能**：单体 JSON 过大；搜索用 `JSON.stringify` 全文匹配。

## 已确认执行决策（grilling）

| # | 决策 |
|---|------|
| 1 | 批次 1 **只 push，不 deploy** |
| 2 | 执行顺序：**1(push) → 2(frontend perf) → 3(data/normalize) → 第一次 deploy → 4(LLM)** |
| 3 | 批次 1：只 push 已有本地 commits，**不提交**未跟踪 handoff/spec/备份文件 |
| 4 | **第一次 deploy** 由批次 3 最后一步负责 |
| 5 | handoff 为**路由型**：引用本 spec，不贴实现代码 |
| 6 | **每批独立评估 Agent，PASS 才允许下一批** |
| 7 | 批次 4 硬门禁：`readme_preview ≥ 60%` **且** `tutorial ≤ 30%` |
| 8 | 批次 4 首次 backlog：执行时**多轮手动/半自动连跑**（如 4–5 次 × 1000 条）尽快清空 |
| 9 | 取消「无匹配 → cli-tool」兜底；无明确类型仍 `tutorial` |
| 10 | tutorial **≤30% 硬门槛**；达不到则批次 3 失败，不放行批次 4 |
| 11 | normalize **不读 README**；README 只服务 LLM |
| 12 | 搜索索引轻量：`name + summary + resource_type + target_tools` |
| 13 | 分片后**彻底删除**单体 `projects-detail.json` |
| 14 | 批次 2（前端）评估 PASS 后 **push 代码，不 deploy** |
| 15 | 批次 4 每轮分析后都 **score + build + deploy** |
| 16 | LLM 每日增量用**新脚本/新 cron**（`search-in-coding-llm-daily.sh`），**不得覆盖**现有 `search-in-coding-daily.sh`（采集） |
| 17 | 批次 4 前将 `cron.script_timeout_seconds` 设为 **3600**，并验证现有 collect + weekly + 新 LLM daily |
| 18 | 允许 `target_tools=[]`；前端/统计/quality_gate 同步适配 |
| 19 | 批次 3 执行窗口**暂停** daily collect cron，完成后恢复 |
| 20 | 每批 handoff 末尾附评估清单；另写 4 份独立 evaluation-prompt |

## 批次设计（新编号）

### 批次 1：push only（立即）

**目标**：把已有本地 commits 推到 GitHub，**不上线**。

**步骤**：
1. 核对 `git status` / `git log`：只 push 已有 commits（当前预期 ahead ≥3，含 bulk + wiki 同步等）
2. `git push origin main`
3. 验证 GitHub 最新 commit；**禁止** `deploy_site.py`

**约束**：
- 不修改代码/数据
- 不 `git add` 未跟踪的 handoff/spec/备份 yaml/临时 skills
- 工作区可不干净；只要不提交无关文件即可
- 若 push 因 branch protection / 签名失败：停下来报告，不 force push

**完成标志**：
- GitHub `main` 含本地已有 commits
- 线上站点**未**因本批变更（可仍为旧数据）
- 独立评估 PASS

---

### 批次 2：前端性能优化

**目标**：5165 条下可承载：首屏 < 2s、搜索 < 50ms、详情按需加载。

**改动范围**：
1. `scripts/build_site.py`
   - 生成 `search-index.json`（轻量：`id` + `text`，text 由 name/summary/resource_type/target_tools 拼接 lower）
   - `projects-detail` 按 100 条分片 → `site/data/detail/{i}.json` + `detail-index.json`
   - **不再生成**单体 `projects-detail.json`
   - 确认 `SLIM_FIELDS` 不含大字段；可选紧凑 JSON
2. `site/js/data.js` / `filters.js`（及 hashed 产物构建链路）
   - 加载 search-index；搜索用 `id→text` Map 做 `includes`，禁止 `JSON.stringify(project)` 搜索
   - `loadDetail` 按 detail-index 拉分片并缓存；**无**单体 fallback
3. Nginx：确认 JSON gzip（`gzip_types` 含 `application/json`）

**验收指标**：

| 指标 | 目标 |
|------|------|
| projects.json 体积 | 明显下降；gzip 后尽量 < 1MB 传输 |
| detail | 仅分片；单片约 50–200KB 量级 |
| 搜索 | 预构建索引；无 JSON.stringify 全文搜索 |
| 首屏 | < 2s（本地或线上预览可测） |
| 搜索响应 | < 50ms（合理机器上） |

**Git / 上线**：
- 评估 PASS 后 **push 代码**
- **不 deploy**

**约束**：
- 零依赖原生 JS
- 不改 `projects.yaml` 字段 schema
- TDD：`build_site` 搜索索引与分片测试先绿
- 不引入新前端框架

---

### 批次 3：补全 readme + 改进 normalize + 重新评分 + **第一次 deploy**

**目标**：
1. readme_preview ≥ 60%
2. tutorial ≤ 30%（硬）
3. general-ai-coding ≤ 45%
4. 允许部分 `target_tools=[]`
5. 管道全绿后 **push + deploy**

#### 3.1 补全 readme_preview

- 工具：`scripts/enrich_projects.py`
- 对约 4874 条无 preview 项目批量拉 README 前 500 字符
- 使用 `gh api repos/{full_name}/readme` + base64（**不要** `gh repo view --json readme`）
- 断点续传；建议 `--batch-size 5`
- 空 README 是合法结果

#### 3.2 改进 normalize.py

**`resource_types_for(text, topics=None)`**：
- Phase 1：现有关键词匹配
- Phase 1.5：`topics` 精确映射到类型（mcp/skills/rules/agent-framework/cli-tool/tutorial 等）
- 扩展关键词列表（见实现细节附录）
- **兜底**：仍为 `['tutorial']`；**禁止**「AI topics → cli-tool」兜底
- **不读** `readme_preview`

**`target_tools_for(text, tools, topics=None)`**：
- 现有 alias 匹配后，再扫 topics 工具别名
- 无匹配且 topics 含 AI/coding 相关 → `['general-ai-coding']`
- 无匹配且无 AI topics 信号 → **`[]`**
- 前端 / metrics / quality_gate 必须兼容空列表

**安全 merge**：
- normalize 不得冲掉 LLM 字段：`quality_score`, `quality_detail`, `tracking_priority`, `last_analyzed`, `benchmark_ref`
- official-seed 保护：`tracking_priority=track`

#### 3.3 管道

```
enrich_projects → normalize → score → finalize_data → generate_reports → build_site → quality_gate → pytest
```

#### 3.4 执行窗口

- **暂停** daily collect cron（`2a0c271a031f`）后再跑长时间 enrich/normalize
- 完成后恢复 cron

#### 3.5 第一次 deploy

批次 3 评估 PASS 后：
1. push 全部数据/代码变更
2. `python3 scripts/deploy_site.py --dest /var/www/coding.lzpgood.online`
3. 验证线上条数、搜索、详情分片、报告

**批次 4 启动硬门禁（由评估 Agent 判定）**：
- `readme_preview ≥ 60%`
- `tutorial ≤ 30%`
- 任一不达标 → 批次 3 FAIL，继续改规则/关键词，不进入批次 4

---

### 批次 4：LLM 分析策略调整 + 清空 backlog

**目标**：提高吞吐，按 stars 优先，配置可持续 cron，并尽快清空约 5120 条 pending。

#### 4.1 代码/配置

- `weekly_analysis.py`：`batch_size` / workers → **10**（优先读 `config/llm-analysis.yaml`）
- `get_projects_to_analyze()`：**stars 降序**
- `config/llm-analysis.yaml`：`api.batch_size: 10`
- 确认 `KeyRotator` 线程安全（必要时加锁）
- **不改** `llm_prompts.py` 与评分公式

#### 4.2 Cron

| Job | 脚本 | 计划 | 说明 |
|-----|------|------|------|
| 现有 daily collect | `search-in-coding-daily.sh` | 03:00 daily | **保持**；勿覆盖 |
| 现有 weekly LLM | `search-in-coding-weekly.sh` | 周一 03:30 | 保持；全量/重评逻辑 |
| **新建** daily LLM 增量 | `search-in-coding-llm-daily.sh` | `30 3 * * 2-6` | `--max-projects 200 --skip-benchmarks` + deploy |

批次 4 前：
1. `hermes config set cron.script_timeout_seconds 3600`
2. 验证 timeout 对 collect / weekly / 新 llm-daily 生效（现网曾出现 **120s** 超时）

#### 4.3 首次 backlog 清空（执行期）

- **多轮**半自动：例如 4–5 轮 × `--max-projects 1000`（或等价）
- **每轮**后：score + build + **deploy**（线上逐步变好）
- 按 stars 降序，高价值先上线
- 增量落盘 / 7 天 cutoff 保证可续跑

#### 4.4 前置硬门禁

仅当批次 3 评估 PASS（readme≥60% 且 tutorial≤30%）才启动。

---

## 不做什么

| 不做 | 原因 |
|------|------|
| 不删 5165 条数据 | 合法采集；用分类改进解决 |
| 不改评分公式 | 100 分制已定 |
| 不改前端框架 | 零依赖 |
| 不引入新数据源 | 仅 GitHub |
| 不改 LLM prompt 模板 | 只调策略 |
| 不把 AI topics 兜底成 cli-tool | grilling 取消 |
| normalize 不读 README | README 只服务 LLM |
| 不覆盖 daily collect 脚本名 | 避免破坏采集 |

## 实现细节附录（给执行 agent 读，不进 handoff 正文）

### A. topics → resource_type 映射（建议）

| topics 含 | 标记 |
|----------|------|
| mcp-server, model-context-protocol, mcp | mcp-server |
| claude-skills, agent-skills, skills | skills |
| cursor-rules, cursorrules, rules | rules |
| agent-framework, multi-agent | agent-framework |
| cli, cli-tool, command-line | cli-tool |
| tutorial, awesome-list, guide | tutorial |

### B. 关键词扩展（建议）

| 标签 | 新增关键词 |
|------|-----------|
| mcp-server | mcp tool, mcp integration, mcp gateway, mcp hub |
| skills | claude code skills, agent skills, skill library, prompt library, command library |
| rules | coding rules, ai rules, behavioral guidance, system prompt |
| agent-framework | agent runtime, agent platform, agent sdk, coding agent, code agent |
| cli-tool | developer tool, devtool, code assistant, ai assistant, code completion |

### C. 搜索索引字段

```
text = lower(join(name, summary, resource_type..., target_tools...))
```

不含 topics/languages/license/url（grilling 选择轻量）。

### D. 详情分片

- chunk_size = 100
- `detail-index.json`: `{ project_id: chunk_index }`
- 清理旧 `detail/*.json` 后重建
- **删除** `projects-detail.json`

### E. 当前仓库事实（2026-07-14 核对）

- total=5165；no_readme=4874；has_topics=3957；tutorial=2699；general=3210；pending≈5120；analyzed≈33
- `site/data/projects.json` ≈ 6.1MB；`projects-detail.json` ≈ 8.8MB
- `main` 本地曾 ahead 多个 commits；工作区可能含未跟踪 design/handoff
- cron：
  - `2a0c271a031f` daily collect → `search-in-coding-daily.sh`（update_tracker）— 曾 120s 超时
  - `2aa9da554787` weekly LLM → `search-in-coding-weekly.sh`
  - `7388b6c788e8` weekly release 09:00 Mon
- branch protection：require signatures + enforce admins；禁止 force push

## 文档产物清单

| 文件 | 用途 |
|------|------|
| `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md` | 本设计（真相源） |
| `docs/superpowers/handoff/2026-07-14-batch1-push-only-prompt.md` | 批次 1 执行 |
| `docs/superpowers/handoff/2026-07-14-batch2-frontend-perf-prompt.md` | 批次 2 执行 |
| `docs/superpowers/handoff/2026-07-14-batch3-data-normalize-deploy-prompt.md` | 批次 3 执行 |
| `docs/superpowers/handoff/2026-07-14-batch4-llm-strategy-prompt.md` | 批次 4 执行 |
| `docs/superpowers/handoff/2026-07-14-batch1-evaluation-prompt.md` | 批次 1 评估 |
| `docs/superpowers/handoff/2026-07-14-batch2-evaluation-prompt.md` | 批次 2 评估 |
| `docs/superpowers/handoff/2026-07-14-batch3-evaluation-prompt.md` | 批次 3 评估 |
| `docs/superpowers/handoff/2026-07-14-batch4-evaluation-prompt.md` | 批次 4 评估 |

> 旧版 `batch1-push-deploy` / `batch2-normalize-fix` / `batch3-frontend-perf` 文件名已废弃；以新编号文件为准。

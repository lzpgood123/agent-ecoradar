# 新对话 Agent 启动提示词：一次性历史回溯采集（v2，grilling 修订版）

> 将以下全部内容复制粘贴到新对话中作为第一条消息。
>
> 本提示词经 2026-07-14 grilling 决议修订，**不要**回退到旧的「纯按月 2025-01」或「整条覆盖 merge」行为。

---

## 你的任务

你是 "Search in Coding" 项目的开发 Agent。你的任务是执行**一次性历史回溯采集**：

1. 改造 `scripts/initial_collection.py`（及必要的辅助函数/测试）
2. 按 **stars 分层 + 2024-01 起** 的策略从 GitHub 补全生态项目
3. 安全 merge 进现有 `data/projects.yaml`（**绝不能冲掉 LLM 字段**）
4. 跑完整本地衍生链路（**不 deploy、不自动 push**）
5. 同步更新 ADR / CONTEXT / wiki / P1

当前基线：约 **293** 条（github + official-seed 10），其中约 33 条已有 LLM 分析字段。

---

## 第一步：加载技能框架

1. 优先调用 `skill_view("using-superpowers")`（或项目内等价 skill）。
2. **若加载失败**：不要停工。回退阅读并遵守：
   - 工作区 `HERMES.md`（superpowers-zh 规则）
   - `.hermes/skills/` 下相关 skill（如 `test-driven-development`、`verification-before-completion`、`wiki-checkpoint`、`systematic-debugging`）
3. 本任务必须 TDD：先改/加测试，pytest 全绿后再真采集。

---

## 第二步：阅读项目上下文

必读：

1. `wiki/README.md` — 总索引与阅读路线
2. `wiki/L1-全景.md` — 当前状态（注意「历史回溯待执行」）
3. `wiki/L3-代码地图.md` — 重点 `scripts/initial_collection.py`、`normalize.py`、`update_tracker.py`
4. `wiki/L4B-后端详解.md` — 数据管道、tracking_priority、评分
5. `wiki/L6-经验录.md` — 相关坑
6. `CONTEXT.md` — 领域术语（Initial Collection / Tracking Priority 等）
7. `docs/adr/0005-bulk-then-incremental-collection.md` — **将被本任务修订**
8. 本 handoff 全文 — 以本文策略为准，覆盖旧脚本默认行为

实现前先核对事实（用工具读代码/数据，不要凭记忆）：

- `scripts/initial_collection.py` 现状（月分片、checkpoint 键、merge 覆盖）
- `scripts/normalize.py` 的 `github_record()` / 只读 `data/raw/github/*`
- `scripts/update_tracker.py` 的完整步骤与 `--deploy` opt-in
- `tests/test_initial_collection.py`
- `data/projects.yaml` 条数与已有 LLM 字段

---

## 第三步：采集策略（grilling 决议，必须遵守）

### 3.1 时间下界

统一：`created:>2024-01-01`（含等于该日之后创建的仓库）。  
**不再**使用 ADR 旧文中的「仅 2025-01 起」。

### 3.2 Stars 分层表

| 层级 | stars 范围 | 分片 | 搜索方式 | 入库过滤 |
|------|------------|------|----------|----------|
| L1 | ≥100000 | 不分月 | 无关键词全量：`stars:>=100000 created:>2024-01-01` | 仅极薄负向黑名单 |
| L2 | 50000–99999 | 不分月 | 无关键词全量：`stars:50000..99999 created:>2024-01-01` | 仅极薄负向黑名单 |
| L3 | 10000–49999 | 不分月 | 无关键词全量：`stars:10000..49999 created:>2024-01-01` | 仅极薄负向黑名单 |
| L4 | 1000–9999 | **按月** | 无关键词全量：`stars:1000..9999 created:{month_start}..{month_end}` | 负向 + **弱**正向 |
| L5a | 500–999 | 按月 | topic + keyword 检索 + 同 stars/created 过滤 | 严格正负向 + stars≥3 |
| L5b | 100–499 | 按月 | 同上 | 严格正负向 + stars≥3 |
| — | &lt;100 | — | **本轮不做** | — |

执行顺序：L1 → L2 → L3 → L4 → L5a → L5b → code search 补漏。

按月范围：从 `2024-01` 到**当前月**（动态取今天，不要写死 2025-07）。

### 3.3 本轮采集手段（范围边界）

**做：**

1. **Stars 分层主搜**（上表）
2. **现有 topic + keyword 列表**（主要用于 L5；可复用/扩展 `generate_topic_queries()` / `generate_keyword_queries()`）
3. **种子 topic 轻量扩展**：从 10 个官方 seed 仓库读取 topics，生成额外 `topic:...` query（失败可跳过单个 seed）
4. **Code search**（`filename:CLAUDE.md` / `.cursorrules` / `AGENTS.md` 等）：过滤后入库，`tracking_priority=pending`

**明确不做（本轮）：**

- `gh api /repos/{owner}/{repo}/dependents`（不可用 REST，禁止按字面调用）
- README 内链抽取生态项目
- stars &lt; 100 的层

### 3.4 过滤规则

**极薄负向（L1–L3 必用，其它层也用）：**  
`crypto`, `airdrop`, `miner`, `puppies`, `dogs`, `游戏`, `宠物`, `赌` 等明显噪声；`game` / `cheat` 慎用（易误杀 cheat sheet），若使用需限定词边界或组合条件，避免裸词误杀。

**弱正向（L4）：** name/description/topics 中命中较宽 AI/coding 相关词即可，例如：  
`ai`, `llm`, `gpt`, `claude`, `cursor`, `codex`, `mcp`, `agent`, `coding agent`, `prompt`, `copilot` 等（实现时做成常量列表，可测）。

**严格正负向（L5 + code search）：**

- 负向一票否决
- 正向至少命中 1 个更贴 AI coding agent 生态的词（比弱正向更具体，如 coding agent / mcp server / cursor rules / claude code / skills / hooks / agentic 等）
- `stars < 3` 丢弃（`source_type=official-seed` 例外，且 seed 本就不该被本脚本重写策略）

过滤文本至少覆盖：`fullName + description + topics`（有则用），不要只看 name。

### 3.5 Code search 处理

1. 跑 code search queries，收集 `repository.nameWithOwner`
2. 对候选做去重 + 过滤（按 L5 严格规则；无 stars 时先 repo view 再判）
3. 入库时 `tracking_priority=pending`，**不要**直接进 curated
4. 不展示策略由现有站点/finalize 逻辑处理；本脚本不发明新 review_state

---

## 第四步：实现要求（改造 initial_collection.py）

### 4.1 必须改掉的旧行为

| 旧行为 | 新行为 |
|--------|--------|
| 默认 2025-01..2025-07 月分片 | 分层表 + 2024-01→今天 |
| merge `by_url[url]=r` 整条覆盖 | **安全 merge**（见 4.3） |
| checkpoint 仅 query×月 | 搜索层 + **详情 fullName 集合** |
| 详情无 README | `gh repo view` + README 前 500 字（失败→空） |
| 无过滤 / 过滤不一致 | 分层过滤 |
| 声称跑 normalize --source github | **不要**依赖 `data/raw/github` 路径；本脚本直接 merge `projects.yaml` 或把 raw 写到脚本自己的目录并自包含 normalize 调用 `github_record()` |

### 4.2 搜索与分页

- 使用 `gh search repos`，`--sort stars`
- 每个 query 最多翻 **3 页**；每页 limit 与现 CLI 能力对齐（实现时以 `gh search repos --help` 为准，常见 100；不要文档写 90 却代码 30）
- 注意 GitHub search 约 **1000 结果上限**：L4/L5 靠**按月**降低单 query 结果量
- 搜索失败：记录错误、跳过该 query/页，不中止整层（除非 rate limit 耗尽需等待/退出并保留 checkpoint）

### 4.3 安全 merge（数据损坏级约束）

**默认行为：**

- 新 repo：追加完整记录（经 `github_record()` 或等价），`tracking_priority=pending`，`quality_score=0` 等
- 已存在同 URL 或同 `repo` / fullName：
  - **更新** GitHub 可量化字段：`stars`, `forks`, `license`, `topics`, `languages`, `last_updated`, `status`, `readme_preview`, `name`（如需要）, `summary` 仅当旧 summary 为空时
  - **保留** LLM/人工字段：`quality_score`, `quality_detail`, `tracking_priority`, `last_analyzed`, `benchmark_ref`, `review_state`（若已非默认且有分析痕迹则保留）, 已有较好的 `i18n` / 非空 `summary`
  - `first_seen`：保留旧值；`last_seen`：更新为今天
- `source_type=official-seed`：**不得**被降级为 github 普通记录；`tracking_priority` 保持 `track`；仅允许刷新无害元数据（若 seed 无 github 字段则跳过）

**CLI 开关：**

- 默认：上述安全 merge
- `--skip-existing`：同 URL/repo **完全跳过**，只追加全新项目

禁止默认整条覆盖。

### 4.4 Checkpoint / 可恢复

- 文件：`data/initial-collection-checkpoint.json`（或保留现路径，但键结构必须升级）
- **搜索层键**：`tier | query | month_or_all` → 完成标记、结果数、时间戳
- **详情层**：`completed_details: [fullName, ...]` 集合
- 每完成 **N=20** 个 repo view：落盘 raw 细节 + merge 进 `projects.yaml` + 写 checkpoint
- 重跑：跳过已完成搜索键与已完成 fullName
- 每层搜索结束后也保存一次进度日志（print + checkpoint stats）

### 4.5 详情拉取完整度

对每个候选 fullName：

```text
gh repo view {fullName} --json nameWithOwner,description,url,homepageUrl,stargazerCount,forkCount,licenseInfo,repositoryTopics,primaryLanguage,pushedAt,createdAt,updatedAt,isArchived,latestRelease
```

再尝试获取 README 文本（与 `collect_github.py` / 批次 A 一致的方式，如 `gh api repos/{fullName}/readme` 解码），写入 `readme`/`readme_preview` 前 500 字；失败则空字符串，**不阻塞**。

然后调用 `normalize.github_record(detail, tools)` 生成记录再 merge。

### 4.6 并发与 cron

**开跑前：**

1. 列出相关 Hermes cron（日更 tracker、周一 LLM 分析等）
2. **暂停**会写 `data/projects.yaml` 的 job
3. 确认当前不在 03:00 窗口或已暂停

**全部完成后：** 恢复 cron。  
禁止与日更/周分析并行写同一 `projects.yaml`。

### 4.7 测试（先于真采集）

在 `tests/test_initial_collection.py`（及必要新文件）中至少覆盖：

1. stars 分层常量 / 查询生成（L1–L5 边界）
2. 月范围：2024-01 → 当前月（可 freeze 日期测）
3. 分层过滤：L1 负向命中丢弃；L4 弱正向；L5 严格规则；stars&lt;3
4. **merge 保留 LLM 字段**（核心）
5. `--skip-existing` 不更新已有
6. checkpoint 搜索键 + 详情 fullName 跳过逻辑
7. 删除或改写依赖旧 `generate_month_ranges('2025-01','2025-07')` 唯一路径的过时断言

```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate
python3 -m pytest tests/ -v
```

**全绿后才允许**执行真采集。

---

## 第五步：执行采集

### 5.1 预检

```bash
cd "/root/workspace/search in coding"
gh api rate_limit --jq '.rate'
# 暂停相关 cron 后再继续
python3 scripts/initial_collection.py --dry-run   # 打印分层 queries / 月范围 / 手段列表
```

### 5.2 运行

```bash
# 默认可恢复；中断后同样命令续跑
python3 scripts/initial_collection.py

# 若只需追加新项目、不刷新已有 GitHub 字段：
# python3 scripts/initial_collection.py --skip-existing
```

预计耗时：数十分钟到数小时（取决于候选量和 rate limit）。  
配额：详情阶段约 1+ 次 API/repo；code search 更严；耗尽时保存 checkpoint 退出并说明如何续跑。

### 5.3 采集后本地衍生链路（不 deploy）

**禁止**错误路径：

- ~~`normalize.py --source github` 指望读到 initial 的 raw~~（默认只扫 `data/raw/github/`）
- ~~只跑 score + build 却声称完成~~
- ~~自动 `deploy_site.py`~~
- ~~自动 `git push`~~

**必须**在 merge 完成后执行完整本地衍生（可用 `update_tracker.py --skip-collect` **且不要**加 `--deploy`，或逐步执行）：

```bash
python3 scripts/validate_data.py
python3 scripts/score.py
python3 scripts/finalize_data.py
python3 scripts/generate_reports.py
python3 scripts/build_site.py
python3 scripts/quality_gate.py
# 可选等价：python3 scripts/update_tracker.py --skip-collect
# 不要加 --deploy
```

### 5.4 Git

- 本地 commit：脚本、测试、`data/projects.yaml`、衍生数据、文档
- **不要** `git push`
- **不要** 生产 deploy
- 在最终汇报中给出：commit hash、项目数量前后对比、待你确认的 push/deploy 命令

---

## 第六步：同步文档（本任务内完成）

| 文档 | 更新内容 |
|------|----------|
| `docs/adr/0005-bulk-then-incremental-collection.md` | 历史回溯改为 2024-01 起 + 本分层策略；注明 dependents 本轮不做 |
| `CONTEXT.md` | Initial Collection 定义与 ADR 对齐 |
| `wiki/L1-全景.md` | 项目数量、历史回溯已执行/策略摘要 |
| `wiki/L3-代码地图.md` | `initial_collection.py` 职责描述 |
| `wiki/L4B-后端详解.md` | 采集策略、merge 规则 |
| `wiki/L6-经验录.md` | 采集坑（rate limit、过滤误杀、checkpoint 等） |
| `wiki/P1-产品决策日志.md` | 追加 2026-07-14 grilling 决策摘要 |

完成后用 `wiki-checkpoint`（或对照 wiki 更新表自检）确认读写合规。

---

## 第七步：验证清单

### 代码与测试

- [ ] `initial_collection.py` 实现分层表（L1–L5b），无 &lt;100 星层
- [ ] `created` 下界 2024-01-01；L4/L5 按月到**当前月**
- [ ] 无 dependents 假 API；无 README 抽链
- [ ] 安全 merge 单测通过；默认不整条覆盖
- [ ] `--skip-existing` 可用
- [ ] checkpoint 含搜索层 + 详情 fullName；中断可续
- [ ] `pytest tests/ -v` 全绿

### 数据

- [ ] `projects.yaml` 条数增加（预期大致 +100～250 量级，**以实际为准**，不要为凑数放宽过滤）
- [ ] 无按 URL/repo 的重复主记录
- [ ] 已有 LLM 字段样本抽查仍在（quality_score / last_analyzed / tracking_priority）
- [ ] official-seed 仍为 track
- [ ] 新项目默认 `tracking_priority=pending`，`quality_score=0`
- [ ] 新项目尽量具备 stars/forks/license/topics/readme_preview（允许个别 API 失败为空）
- [ ] `resource_type` / `target_tools` 由规则启发式填充即可；**完整质量标签依赖每周 LLM**，不要在验收里要求「已全部 LLM 打标」

### 管道与交付

- [ ] validate / score / finalize / reports / build / quality_gate 均 PASS
- [ ] **未** deploy 到生产
- [ ] **未** git push
- [ ] 相关 cron 已恢复
- [ ] ADR / CONTEXT / wiki / P1 已更新
- [ ] 最终报告含：前后数量、各层新增统计、API 配额消耗摘要、commit hash、续跑/push/deploy 说明

---

## 关键约束（摘要）

1. **分层顺序** L1→…→L5b，高价值优先  
2. **2024-01-01** 起，不是 2025-01  
3. **L1–L3** 无关键词 + 极薄负向；**L4** 无关键词按月 + 负向弱正向；**L5** 检索 + 严格过滤  
4. **&lt;100 stars 本轮不做**  
5. **安全 merge**；保护 official-seed 与 LLM 字段  
6. **详情 checkpoint**；每 20 个落盘  
7. **先测后采**；pytest 全绿  
8. **暂停 cron → 采集 → 本地完整衍生 → 恢复 cron**  
9. **不 deploy、不 push**  
10. **同步 ADR/CONTEXT/wiki/P1**  
11. 技能加载失败要回退，不卡死  

---

## 项目环境信息

- 工作目录：`/root/workspace/search in coding`
- Python：3.12.3（`python3`）；测试用 `source .venv/bin/activate && python3 -m pytest tests/ -v`
- GitHub CLI：`gh` 已认证；注意 core + search 配额
- 站点：https://coding.lzpgood.online/（本任务只本地 build，不自动上线）
- 管道：`python3 scripts/update_tracker.py --skip-collect`（不要加 `--deploy`）
- 当前数据：约 293 条；pending 居多；部分已 LLM 分析

---

## 工具覆盖预期（参考，非硬指标）

| 工具 | 当前约 | 预期增量（参考） |
|------|--------|------------------|
| claude-code | 88 | +50～100 |
| cursor | 46 | +20～40 |
| codex-cli | 43 | +10～20 |
| opencode | 34 | +5～15 |
| antigravity-cli | 26 | +10～20 |
| hermes-agent | 22 | +0～5 |
| workbuddy-codebuddy | 20 | +5～10 |
| qoder | 17 | +0～5 |
| trae | 3 | +0～5 |
| goose | 2 | +5～15 |
| **合计** | ~293 | **约 +100～250** |

goose/trae/qoder 生态本身小，不会因策略变更暴涨——这是事实，不要为凑数放宽过滤。

---

## 最终汇报格式

完成后用中文汇报：

1. 改了哪些文件  
2. 测试结果（命令 + 通过数）  
3. 采集统计：各层候选/入库/跳过/过滤  
4. projects 数量：前 → 后  
5. LLM 字段抽查：未损坏证据  
6. 本地 pipeline 各步结果  
7. commit hash  
8. cron 已恢复确认  
9. **待用户执行**：push / deploy 的准确命令  
10. 已知限制（配额、未做 dependents、&lt;100 星未做等）

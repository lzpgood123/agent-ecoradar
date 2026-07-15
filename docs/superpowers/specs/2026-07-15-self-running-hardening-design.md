# 自运行加固设计规格

> 日期：2026-07-15
> 状态：已执行完成（2026-07-15）
> 作者：运维加固 Agent
> 前置：项目功能开发全部完成，LLM 策略收口，进入自运行阶段。grilling 会话发现 10 个运维可靠性问题。

## 背景

"Search in Coding" 项目已完成全部功能开发（采集 → 评分 → LLM 分析 → 前端 → deploy），5165 条项目数据稳定运行，站点 https://coding.lzpgood.online/ 上线。当前进入自运行阶段，Hermes cron 4 个 job + GitHub Actions 3 个 workflow 自动运行。

grilling 会话对自运行流程逐项审查后，发现 10 个影响长期可靠性的运维问题。本 spec 记录决策清单、修复后时间线、预防性措施，以及明确的不做范围。

### 当前自运行架构

```
Hermes Cron (4 jobs):
  03:00 daily  采集 + 评分 + 构建（不 deploy）         search-in-coding-daily.sh
  03:30 daily  LLM 增量 200 条 + deploy (Tue-Sat)      search-in-coding-llm-daily.sh
  03:30 weekly LLM 全量重评 + 报告 + deploy (Mon)      search-in-coding-weekly.sh
  09:00 weekly GitHub Release (Mon)                    (无脚本，直接 hermes agent)

GitHub Actions (3 workflows):
  update-data.yml   02:00 UTC 采集 + commit push       → 触发 publish-site + release
  publish-site.yml  push:main → GitHub Pages deploy
  release.yml       push:VERSION → 创建 GitHub Release
```

### 关键数据

| 指标 | 数值 |
|------|------|
| 项目总数 | 5165 |
| track 项目 | 4571 |
| reject 项目 | 69 |
| pending/其他 | 525 |
| SenseNova API keys | 13 |
| data/raw 磁盘占用 | 24M（9 天） |
| data/snapshots 磁盘占用 | 8.1M |
| .venv 磁盘占用 | 192M |
| site/ 磁盘占用 | 22M |

## 10 个决策清单

### 决策 1（High）：daily cron 脚本加 source venv

**问题**：`~/.hermes/scripts/search-in-coding-daily.sh` 直接 `/usr/bin/python3 scripts/update_tracker.py`，没有 `source .venv/bin/activate`。`update_tracker.py` 依赖链（normalize.py → common.py → PyYAML）需要 venv 中的 PyYAML。7/15 运行成功是因为系统 Python 恰好有 PyYAML，但不可靠。

**决策**：脚本加 `source .venv/bin/activate`。**不加 `--deploy`**，保持原始设计——daily 采集不 deploy，LLM cron 负责 deploy。

### 决策 2（High）：daily LLM cron 从 03:30 改到 05:00

**问题**：daily 采集 cron 03:00 运行，daily LLM cron 03:30 运行。5165 条数据采集 + normalize + score + build 可能耗时超过 30 分钟，两个脚本同时写 `data/projects.yaml` 可能导致数据损坏。

**决策**：daily LLM cron 从 `30 3 * * 2-6` 改为 `0 5 * * 2-6`（05:00 Tue-Sat），给采集留出 2 小时窗口。

### 决策 3（High）：weekly LLM cron 从 03:30 改到 05:00

**问题**：周一 03:00 daily 采集和 03:30 weekly LLM 同样存在时间冲突。weekly LLM 是全量重评（5165 条），运行时间更长。

**决策**：weekly LLM cron 从 `30 3 * * 1` 改为 `0 5 * * 1`（05:00 Monday），给采集留出 2 小时窗口。

### 决策 4（Medium）：禁用 weekly release cron

**问题**：Hermes cron `7388b6c788e8`（weekly auto release，周一 09:00）与 GitHub Actions `release.yml` 功能重叠。`release.yml` 在 VERSION 变更时自动创建 Release，`update-data.yml` 每次 commit 都会 bump VERSION 并 push，所以每周一 `update-data.yml` 运行后自动触发 `release.yml`。Hermes weekly release cron 冗余且可能产生重复 Release。

**决策**：禁用 Hermes weekly release cron（pause 或 remove）。GitHub Actions `release.yml` 已覆盖此功能。

### 决策 5（High）：修复 GitHub Actions update-data.yml

**问题**：7/15 GitHub Actions Update Data 失败（3m37s）。两个原因：
1. **PyYAML 未安装**：workflow 只 `pip install pytest`，但 `update_tracker.py` → `normalize.py` → `common.py` 依赖 PyYAML，GitHub Actions 环境 Python 默认不包含。
2. **`--exa-limit` 参数不存在**：`update_tracker.py` 的 argparse 没有 `--exa-limit`，但 workflow 传了这个参数。

**决策**：
- Install step 改为 `pip install pytest pyyaml`
- 去掉 `--exa-limit` 参数（`update_tracker.py` 不支持）
- `--github-limit` 保留（`update_tracker.py` 支持）

### 决策 6（High）：track 项目分批刷新 GitHub API

**问题**：daily 采集只搜索新项目（`collect_github.py` 按 queries 搜索），不刷新已有 track 项目的 stars/forks/last_updated。5165 条中 4571 条是 track 状态，如果不定期刷新 GitHub 元数据，分数会过时。但一次性刷新 4571 个项目会触发 GitHub API rate limit（5000/h）。

**决策**：修改 daily cron 采集脚本，实现 track 项目分批刷新——每天刷新 1000 个 track 项目的 GitHub 元数据（stars/forks/topics/last_updated），约 5 天轮一遍全部 4571 个。新脚本 `scripts/refresh_track_projects.py` 接受 `--batch-size 1000` 参数，按 last_seen 最久未刷新排序，调用 `gh repo view` 批量获取最新数据并 merge 回 `data/projects.yaml`。

### 决策 7（Medium）：定期归档低分/reject 项目

**问题**：5165 条项目中 69 条 reject + 部分 score < 20 的低分项目长期占用 `projects.yaml`（12MB），影响 build 性能和数据质量。

**决策**：写归档脚本 `scripts/archive_low_score.py`，将 `tracking_priority == 'reject'` 或 `total_score < 20` 且 `source_type != 'official-seed'` 的项目移到 `data/archive-projects.yaml`，从 `projects.yaml` 移除。**不删除数据**，只是移到归档文件。可定期手动或 cron 运行。

### 决策 8（Medium）：SenseNova API key 监控

**问题**：13 个 API key 轮换使用，但没有记录每个 key 的调用次数和失败状态。如果某个 key 过期或被限流，无法及时发现。当前 `KeyRotator` 只在内存中 `mark_failed`，下次运行就重置了。

**决策**：`weekly_analysis.py` 加 API key 监控——记录每个 key 的调用次数、成功次数、失败次数、失败类型到日志文件 `data/llm-key-stats.json`。每次 LLM 分析后更新。便于排查 key 问题和评估 key 池健康度。

### 决策 9（Medium）：SenseNova API 降级策略

**问题**：daily LLM 增量分析固定 200 条，如果多个 key 同时触发 429 rate limit，当前 `call_with_retry` 只重试 3 次后放弃，可能导致大量分析失败但没有降级机制。

**决策**：`weekly_analysis.py` 加降级策略——检测到 429 错误比例超过 30% 时，自动将 `--max-projects` 减半（200 → 100），并在日志中标记 `degraded_mode: true`。下次运行如果 429 比例恢复正常，自动恢复原始量。

### 决策 10（Medium）：磁盘清理脚本

**问题**：`data/raw/` 每天增长约 2-3M，`data/snapshots/` 每周增长约 1M。长期运行会积累大量过期数据。已有 `archive_raw.py` 处理 raw 目录（默认 30 天），但不处理 snapshots。

**决策**：写清理脚本 `scripts/cleanup_disk.py`，统一处理：
- `data/raw/` 超过 30 天的日期目录 → 删除（不归档，`archive_raw.py` 已可归档，cleanup 是兜底）
- `data/snapshots/` 超过 90 天的 JSON 文件 → 删除
- `data/raw-archive/` 超过 90 天的 tar.gz → 删除
- `.venv/` 和 `cache/` 保留（不清理）
- 默认 dry-run，`--apply` 执行

## 修复后的自运行时间线

```
03:00  daily  采集 + 评分 + 构建（不 deploy）（每日）
       ├── collect_github.py（搜索新项目）
       ├── normalize.py → score.py → finalize_data.py
       ├── refresh_track_projects.py --batch-size 1000（刷新 track 项目元数据，轮询）
       ├── build_site.py → quality_gate.py
       └── 不 deploy

05:00  daily  LLM 增量分析 200 条 + deploy（Tue-Sat）
       ├── weekly_analysis.py --max-projects 200 --skip-benchmarks
       ├── build_site.py
       └── deploy_site.py --dest /var/www/coding.lzpgood.online

05:00  weekly LLM 全量重评 + 报告 + deploy（周一）
       ├── weekly_analysis.py（全量，含 benchmarks + reports）
       ├── build_site.py
       └── deploy_site.py --dest /var/www/coding.lzpgood.online

09:00  weekly release 禁用（由 GitHub Actions release.yml 自动处理）

push   GitHub Actions:
       ├── update-data.yml（02:00 UTC = 10:00 CST，采集 + commit push）
       ├── publish-site.yml（push:main → GitHub Pages deploy）
       └── release.yml（push:VERSION → GitHub Release）
```

### 时间线设计原则

1. **采集和 LLM 错开 2 小时**：03:00 采集完成后，05:00 LLM 分析，避免 `projects.yaml` 写冲突
2. **deploy 只在 LLM 分析后执行**：确保上线数据经过 LLM 质量评估
3. **daily 不 deploy**：这是刻意设计，不是 bug。每天采集的新数据等到 LLM cron 分析后才 deploy
4. **weekly release 禁用**：GitHub Actions `release.yml` 在 VERSION 变更时自动创建 Release，Hermes cron 冗余
5. **GitHub Actions 独立运行**：10:00 CST 的 update-data 是 GitHub 端备份采集，不影响本地 cron

## 预防性措施

### 1. GitHub API 分批刷新 track 项目

- 每天刷新 1000 个 track 项目（约 5 天轮一遍 4571 个）
- 按 `last_seen` 最久未刷新排序
- 调用 `gh repo view` 获取最新 stars/forks/topics/last_updated
- merge 回 `projects.yaml` 时保留 LLM 字段（quality_score、tracking_priority 等）
- 集成到 daily cron 采集流程中

### 2. 定期归档低分/reject 项目

- `scripts/archive_low_score.py`：score < 20 或 reject 的项目移到 `data/archive-projects.yaml`
- 保留数据不删除，只是从主数据文件移出
- 不影响 official-seed 项目
- 可手动运行或加入 cron（每周一次）

### 3. SenseNova API key 监控 + 降级策略

- **监控**：每次 LLM 分析后，记录每个 key 的调用/成功/失败次数到 `data/llm-key-stats.json`
- **降级**：429 错误比例 > 30% 时，自动将 `--max-projects` 减半，标记 `degraded_mode: true`
- **恢复**：下次运行 429 比例 < 10% 时，自动恢复原始量
- 便于排查 key 过期、限流等问题

### 4. 磁盘清理

- `scripts/cleanup_disk.py` 统一清理：
  - raw 30 天清理（`archive_raw.py` 已可归档，cleanup 是删除兜底）
  - snapshots 90 天清理
  - raw-archive 90 天清理
  - cache 和 .venv 保留
- 默认 dry-run，`--apply` 执行
- 可手动运行或加入 cron（每周一次）

## 不做什么

以下内容明确不在本次加固范围内：

1. **不改评分公式**：`score.py` 的 100 分制（quantifiable 60 + quality 40）保持不变
2. **不改前端框架**：现有 vanilla JS + 分片 JSON 架构保持不变
3. **不改 LLM prompt**：`llm_prompts.py` 的分析/benchmark/报告 prompt 保持不变
4. **不改数据格式**：`projects.yaml` 的字段结构保持不变
5. **不改 deploy 机制**：`deploy_site.py` 的 rsync 逻辑保持不变
6. **不改 GitHub Actions publish-site/release**：这两个 workflow 已正常工作
7. **不新增功能**：本次只做运维加固，不增加产品功能

## 验收标准

- [x] daily cron 脚本有 `source .venv/bin/activate`
- [x] daily LLM cron schedule 为 `0 5 * * 2-6`
- [x] weekly LLM cron schedule 为 `0 5 * * 1`
- [x] weekly release cron 已 pause 或 remove
- [x] `update-data.yml` 有 `pip install pyyaml`，无 `--exa-limit`
- [x] `refresh_track_projects.py` 存在且有测试
- [x] `archive_low_score.py` 存在且有测试
- [x] `weekly_analysis.py` 有 API key 监控日志
- [x] `weekly_analysis.py` 有 429 降级策略
- [x] `cleanup_disk.py` 存在且有测试
- [x] 所有新脚本通过 `python3 -m pytest tests/`
- [x] 每个任务完成后 git commit

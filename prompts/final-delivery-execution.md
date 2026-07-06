# Prompt: Final Delivery Execution

请在 `/root/workspace/search in coding` 中继续执行 Search in Coding 项目，目标是完成**最终交付版**，不是 MVP。

必须读取并遵守：

```text
.hermes/plans/2026-07-06_102845-final-delivery-plan.md
```

## 最终目标

把 Search in Coding 做到可发布、可复用、可长期自动追踪、数据质量可信、报告完整、站点可用。只有最终质量门禁全部通过后才能停下。

## 当前问题

之前已经完成了初始 MVP：项目骨架、GitHub 采集、fallback web 采集、292 条记录、初始报告和站点数据。

但这还不是最终完成，因为：

- Exa 没有真正配置成功，只保存了失败记录。
- fallback web 结果还没有充分审计。
- official seed 工具占据 Top 排名，不适合作为生态项目榜。
- 缺少 curated dataset。
- 缺少 rejected/noisy dataset。
- 缺少最终质量门禁脚本。
- 缺少 final delivery 报告和完整运营文档。
- 静态站点只是基础表格，还不是最终可用形态。

## 必须完成的最终交付物

### 数据

必须生成或更新：

```text
data/projects.yaml
data/curated-projects.yaml
data/rejected-projects.yaml
data/scores.yaml
site/data/projects.json
site/data/curated-projects.json
site/data/tools.json
site/data/concepts.json
site/data/metrics.json
```

要求：

- normalized records >= 150
- curated records >= 50
- GitHub verified records >= 30
- non-GitHub reviewed/fallback records >= 30
- 每个目标工具 >= 10 条相关记录
- official seed tools 必须从 ecosystem Top ranking 中分离出去
- fallback web 必须标注为 fallback，不得伪装成 Exa

### 脚本

必须创建或完善：

```text
scripts/quality_gate.py
scripts/generate_reports.py
scripts/validate_data.py
scripts/score.py
scripts/build_site.py
scripts/export_pack.py
scripts/collect_github.py
scripts/collect_exa.py
scripts/collect_web.py
```

### 报告

必须生成：

```text
docs/reports/final-delivery-report.md
docs/reports/curated-top-projects.md
docs/reports/tool-ecosystem-comparison.md
docs/reports/trends-and-opportunities.md
docs/reports/source-quality-audit.md
docs/reports/exa-status-and-fallback.md
docs/reports/next-90-days-roadmap.md
```

### 文档

必须生成或完善：

```text
docs/operating-guide.md
docs/data-dictionary.md
docs/qa-checklist.md
docs/final-definition-of-done.md
docs/reusable-packaging.md
README.md
```

### 站点

必须升级：

- 首页展示 overview metrics
- 官方工具单独展示
- ecosystem projects 单独排名
- 默认排名排除 official seed tools
- 支持 tool/category/source/review/curated filter
- 显示 source quality badge
- 链接到最终报告

### 自动化

必须完善：

```text
.github/workflows/update-data.yml
.github/workflows/publish-site.yml
.hermes/cron-prompts/daily-discovery.md
.hermes/cron-prompts/weekly-report.md
.hermes/cron-prompts/monthly-audit.md
```

## Exa 要求

必须真实尝试：

```bash
mcporter list
mcporter call 'exa.web_search_exa(query: "Claude Code ecosystem MCP skills", count: 3)'
```

如果 Exa 可修复，修复后用 Exa 采集并保存 raw。

如果 Exa 仍不可用：

- 保存精确失败输出。
- 生成 `docs/reports/exa-status-and-fallback.md`。
- fallback web 数据必须标注：`source_type: fallback-web`、`source_quality: fallback`、`tags: [fallback-not-exa]`。
- 不得声称完成了 Exa 语义搜索。

## 最终验证命令

必须实际运行：

```bash
python3 scripts/validate_data.py
python3 scripts/quality_gate.py
python3 scripts/score.py
python3 scripts/generate_reports.py
python3 scripts/build_site.py
python3 scripts/export_pack.py --dry-run
python3 scripts/export_pack.py --output dist/search-in-coding-final.zip
```

如果任何命令失败，必须修复并重跑，直到通过。

## 最终回复必须包含

1. 是否达到最终完成标准。
2. 每条最终验证命令的真实输出摘要。
3. 数据规模：normalized、curated、rejected、GitHub、fallback、official。
4. Exa 是否成功；如果失败，失败原因和 fallback 状态。
5. 最终报告路径。
6. 站点文件路径。
7. 打包文件路径。
8. 仍存在的真实 blocker；如果没有 blocker，明确说明无需用户继续补需求。

请持续执行，不要只写计划，不要在 MVP 处停下，不要伪造结果。
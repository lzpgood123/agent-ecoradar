# ADR-0007: 新增 data/snapshots/ 每日快照机制支持趋势分析

## Status: proposed

## Context

当前所有 618 条记录的 `first_seen` 都是 2026-07-06，系统无法展示数据增长趋势、分类变化、工具生态演进等时间维度信息。虽然 `last_seen` 字段会随每日运行更新，但没有历史快照来对比"昨天 vs 今天"的变化。

站点缺少趋势页面，用户无法看到生态随时间的演进。

## Decision

1. 每次 pipeline 运行时，在 `data/snapshots/YYYY-MM-DD.json` 中记录当日状态快照：
   - 总记录数、各 source_type 记录数
   - 分类分布（每个 category 的记录数）
   - 每个工具的覆盖数
   - 平均分、curated/rejected 数量
   - 当日新增记录数、删除记录数
2. `build_site.py` 读取历史快照，生成 `site/data/trends.json` 供站点消费
3. 站点新增趋势页面：每日新增记录数折线图、分类分布变化、工具生态增长曲线

## Consequences

- `data/snapshots/` 会随时间持续增长（每天约 2-5KB JSON），需要长期归档策略
- 快照文件入 Git，提供完整历史可追溯性
- 前 30 天无历史数据，趋势页面需要积累一段时间才有展示价值
- 为未来的月度/季度趋势报告提供数据基础

# ADR-0002: 评分从来源驱动改为内容质量驱动

## Status: proposed

## Context

当前评分系统中 6 个维度的赋值几乎完全由 `source_type` 决定：GitHub 来源一律 activity=2, practicality=3, confidence=4；Exa 一律 confidence=3；其他来源一律低分。导致同来源内项目分数差异极小（github: 14-22, exa: 13-16, fallback: 5-10），评分实际上是在给来源分类，而非评估项目质量。

一个 50000 star 的活跃项目和 1 star 的空仓库都是 GitHub 来源，分数可能只差 2-3 分，无法有效区分。

## Decision

6 个评分维度从来源固定值改为内容质量指标：

- **ecosystem_value**: 基于扩展面数量（每支持 1 种 extension_point +1，上限 5）
- **activity**: 基于 `pushed_at` 时间窗口（90 天内=5 → 更久=1），非 GitHub 按日期可用性降级
- **adoption**: stars + downloads 综合
- **practicality**: README 完整度、示例代码、文档链接
- **novelty**: first_seen 时间 + 内容独特性（TF-IDF 相似度）
- **confidence**: 保留来源分级但细化（official repo=5 > GitHub community=4 > RSS=4 > Exa=3 > Reddit high-score=3 > 其他=1）

## Consequences

- 评分需要更多数据字段（pushed_at, README 内容, downloads），采集器需增强
- 同来源项目间会有更大的分数差异，curated 集合质量提升
- `config/scoring.yaml` 的 `source_weights` 仍保留，但影响权重降低
- 评分逻辑复杂度增加，需要更充分的测试覆盖

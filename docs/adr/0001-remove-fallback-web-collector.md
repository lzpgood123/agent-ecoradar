# ADR-0001: 砍掉 fallback-web 采集器，Exa 不可用时跳过而非降级

## Status: proposed

## Context

fallback-web 采集器作为 Exa 不可用时的降级方案，通过通用 web 搜索采集数据。实际运行中 147 条 fallback-web 记录中包含大量完全无关内容（morkie 狗狗买卖、Google Sheets 函数文档、AI工具箱导航站等），占总数据的 24%。这些噪声被分类为 `tutorial-case-study`，污染了数据集。

替代方案是加强过滤，但 fallback-web 的搜索结果质量本质上不可控——通用 web 搜索没有 API 级别的质量保证，过滤成本远大于补充价值。

## Decision

砍掉 fallback-web 采集器。Exa 不可用时跳过当天 Exa 采集，等下次重试，不再用通用 web 搜索降级。现有 147 条 fallback-web 记录按内容相关性清洗，无关内容移入 rejected。

## Consequences

- 数据采集量在 Exa 不可用的日期会减少，但质量提升
- 需要 Reddit/HN/RSS 等新来源（ADR-0003）来补充非 GitHub 覆盖
- `source_type=fallback-web` 在代码中保留但不再产生新记录

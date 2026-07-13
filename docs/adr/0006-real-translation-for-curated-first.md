# ADR-0006: 双语翻译从假 fallback 升级为 API 翻译，先 curated 后全量

## Status: proposed

## Context

当前 618 条记录的 i18n zh == en（中文和英文内容完全相同），"双语"功能是假的。`enrich_i18n.py` 只是结构化地把同一内容放入 zh 和 en 字段，没有实际翻译。

全量翻译 618 条记录的成本和 API 调用量较高，且大部分记录质量不高（fallback-web 垃圾数据翻译无意义）。

## Decision

分阶段实现真正翻译：

1. **短期**：只翻译 `review_state=auto-curated` 的 60 条记录（最高质量、最有展示价值）
2. **长期**：逐步翻译所有通过质量门禁的有效记录，每日翻译预算限制（50 条/天）
3. 翻译结果缓存到 `data/translations-cache/`（按 URL hash 命名），避免重复调用
4. 翻译 API 不可用时回退到原英文（不阻塞 pipeline）

翻译 API 选择在实现阶段确定（DeepL 或 Google Translate），取决于可用性和成本。

## Consequences

- 站点的中文体验对 curated 记录显著提升，非 curated 记录仍显示英文
- 翻译缓存机制增加了 `data/` 目录的复杂度，但缓存文件不入 Git（加入 .gitignore）
- 翻译质量依赖 API，技术术语可能翻译不准确，需要后续人工校验

# Prompts for Search in Coding

本目录保存可直接交给 Hermes 执行的任务提示词。

推荐执行顺序：

1. `goal-a-project-packaging.md` — 先搭建可复用项目骨架。
2. `goal-b-initial-collection.md` — 再执行第一轮信息收集和分析。
3. `github-search-gh.md` — 可单独用于 GitHub 采集。
4. `exa-semantic-search.md` — 可单独用于 Exa 互联网语义搜索。
5. `normalize-and-score.md` — 对 raw 数据归一化、评分、去重。
6. `deep-dive-template.md` — 对单个工具或项目做深度研究。
7. `weekly-report.md` — 后续 Hermes cron 每周报告。

注意：

- GitHub 搜索优先使用 `gh`。
- 互联网语义搜索优先使用 Exa。
- 所有 raw 结果必须保存。
- 不要把 API key 写入项目文件。

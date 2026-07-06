# Prompt: Normalize and Score

在 `/root/workspace/search in coding` 中对 raw 采集结果执行归一化、去重、分类和评分。

## 输入

- `data/raw/github/`
- `data/raw/exa/`
- `data/raw/web/`
- `data/seed-tools.yaml`
- `data/queries.yaml`
- `data/concepts.yaml`

## 处理步骤

1. 读取所有 raw 结果。
2. 按 URL、repo full name、normalized name 去重。
3. 过滤明显无关项目。
4. 生成/更新 `data/projects.yaml`。
5. 为每条记录填充：
   - id
   - name
   - url
   - repo
   - source_type
   - category
   - target_tools
   - concepts
   - summary
   - why_it_matters
   - status
   - license
   - stars/forks/last_updated
   - maturity
   - integration_surfaces
   - tags
   - score
   - review_state
6. 根据 scoring 文档打分。
7. 生成统计报告。

## 分类优先级

如果条目是官方仓库/官方文档，标记 `official-tool`。

如果条目能直接增强某工具使用体验，优先标记：

- `rules-instructions`
- `skills-prompts`
- `mcp-acp-a2a`
- `context-engineering`
- `testing-review-ci`
- `multi-agent-workflow`

## 输出

- `data/projects.yaml`
- `data/scores.yaml`
- `docs/reports/normalization-report.md`
- 更新 `site/data/projects.json`

## 验证

运行：

```bash
python3 scripts/validate_data.py
python3 scripts/score.py
python3 scripts/build_site.py
```

最终说明：

- 输入 raw 数量
- 去重后数量
- 被过滤数量
- 每个分类数量
- 每个目标工具数量
- Top 20 项目

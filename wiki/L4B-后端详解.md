# L4B-后端详解 — 后端怎么改

> 后端开发者深入文档。读完能独立修改后端代码。

## 数据管道流程

```
update_tracker.py (入口)
  ├─ collect_github.py     → data/raw/github/YYYY-MM-DD/
  ├─ collect_exa.py        → data/raw/exa/YYYY-MM-DD/
  ├─ collect_web.py        → data/raw/web/YYYY-MM-DD/
  ├─ normalize.py          → data/projects.yaml
  ├─ enrich_i18n.py        → 更新 projects.yaml i18n 字段
  ├─ validate_data.py      → 验证数据完整性
  ├─ score.py              → data/scores.yaml + 更新 projects.yaml
  ├─ finalize_data.py      → curated-projects.yaml + rejected-projects.yaml
  ├─ enrich_i18n.py        → 再次增强
  ├─ generate_reports.py   → docs/reports/*.md
  ├─ build_site.py         → site/data/*.json + site/reports/
  ├─ quality_gate.py       → 全量检查
  ├─ py_compile *.py       → 语法检查
  └─ deploy_site.py        → /var/www/ (仅 --deploy 时)
```

## 分组设计

输入文件（不变的数据定义）：
| 文件 | 用途 | 关键字段 |
|------|------|---------|
| data/seed-tools.yaml | 10 个目标工具定义 | id, name, vendor, primary_type, aliases, extension_points, tracking_priority |
| data/queries.yaml | GitHub 和 Exa 搜索 query 模板 | github[], exa[] |
| data/concepts.yaml | 核心概念定义 | id, name, description |
| config/scoring.yaml | 评分权重配置 | source_weights, category_weights, penalties, ranking |

缓存文件（可重新生成）：
| 文件 | 生成来源 | 用途 |
|------|---------|------|
| data/projects.yaml | normalize.py | 全量归一化索引库 |
| data/scores.yaml | score.py | 评分结果 |
| data/curated-projects.yaml | finalize_data.py | 自动推荐集 |
| data/rejected-projects.yaml | finalize_data.py | 噪声集 |
| docs/reports/*.md | generate_reports.py | 自动报告 |
| site/data/*.json | build_site.py | 站点数据 |
| data/raw/* | collectors | 原始快照 |
| data/snapshots/* | snapshot_and_diff.py | 数据快照 |

## 分类系统 (CATEGORY_RULES)

在 normalize.py 中定义的基于关键词的规则引擎：

| 分类 ID | 关键词示例 |
|---------|-----------|
| mcp-acp-a2a | mcp server, model context protocol, a2a, acp |
| skills-prompts | claude skill, agent skill, skills, prompts |
| rules-instructions | agents.md, cursor rules, .cursorrules |
| context-engineering | context engineering, codebase index, repo map |
| agent-harness | multi-agent, agent orchestration, subagent, agent framework |
| testing-review-ci | pr review, code review, test generation, ci automation |
| benchmark-evaluation | benchmark, evaluation, leaderboard |
| terminal-agent | terminal agent, cli agent |
| ai-ide | (仅当提到具体 IDE 名称时) |
| tutorial-case-study | (兜底分类) |

## 评分系统

### 6 维度（每项 0-5，总计 0-30）

| 维度 | 含义 | 自动赋值逻辑 |
|------|------|-------------|
| ecosystem_value | 生态价值 | MCP/skills/rules/context → 4, 生态项目 → 3 |
| activity | 活跃度 | GitHub → 2, 其他 → 1 |
| adoption | 采用度 | 基于 stars：>=50000→5, >=10000→4, >=1000→3, >=100→2, >0→1 |
| practicality | 实用性 | GitHub → 3, 其他 → 2 |
| novelty | 新颖度 | 默认 2 |
| confidence | 可信度 | GitHub → 4, Exa → 3, fallback → 2 |

### 附加调整

- `source_weight`：在 config/scoring.yaml 中配置
- `category_weight`：按分类的最大权重
- `penalty`：fallback (-3), generic general-ai (-1), archived (-2)

### Curated 选择规则

1. 先选 GitHub 高分 + 高价值分类 → 至少 40 条
2. 再选非 GitHub 高分 → 至少 15 条
3. 确保每个工具至少 1 条
4. 补满到 60 条（按分数排序）
5. Rejected：分数 <=9 或 fallback-web 或 generic

## 数据校验

validate_data.py 检查：
- seed-tools.yaml 必须含 id, name, vendor, primary_type, aliases, tracking_priority
- sources.yaml 必须含 id, name, type
- concepts.yaml 必须含 id, name, description
- projects.yaml 必须含 id, name, url, source_type, category, target_tools, summary, review_state

## 质量门禁 (quality_gate.py)

检查项：
- 归一化记录 >= 150
- curated >= 50, rejected >= 20
- 所有项目含 required 字段
- 所有项目含 i18n.zh/en
- review_state 为 auto-indexed / auto-curated / auto-rejected
- fallback-web 的 source_quality=fallback, 含 fallback-not-exa 标签
- curated review_state=auto-curated, rejected review_state=auto-rejected
- 每个工具覆盖 >= 10
- 官方工具不在 ecosystem ranking
- GitHub verified >= 30, non-GitHub >= 30
- config/scoring.yaml 存在
- 所有必需的报告文件和站点数据文件存在

## 错误处理

- 采集器独立运行，失败只记录不阻塞管道（required=False）
- normalize/score/finalize/report/build 失败则直接 exit（required=True）
- Exa 不可用时自动 fallback 到 web 搜索，但标记 fallback-not-exa

## 配置管理

环境变量（可选）：
- SEARCH_IN_CODING_WEBROOT — 部署目标目录
- EXA_API_KEY — 仅在直接 HTTP fallback 时需要

配置文件：
- config/scoring.yaml — 评分权重 + 排名阈值

## 测试覆盖

2 个测试文件（pytest）：
- test_pipeline_features.py — 管道功能测试
- test_data_integrity.py — 数据完整性测试

运行命令：`pytest tests/ -v`

## 下一步读什么

→ [L5-接口契约](L5-接口契约.md)

## 更新指引

**触发条件：** API 端点增删、核心模块变更、错误处理逻辑变更、评分规则变更
**更新内容：** 管道流程、分类系统、评分系统、配置管理
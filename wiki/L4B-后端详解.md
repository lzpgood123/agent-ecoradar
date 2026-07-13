# L4B-后端详解 — 后端怎么改

> 后端开发者深入文档。读完能独立修改后端代码。

## 数据管道流程

```
update_tracker.py (入口)
  ├─ collect_github.py     -> data/raw/github/YYYY-MM-DD/
  ├─ normalize.py          -> data/projects.yaml (仅 GitHub)
  ├─ validate_data.py      -> 验证数据完整性
  ├─ score.py              -> 更新 projects.yaml (100分制可量化分)
  ├─ finalize_data.py      -> curated-projects.yaml + rejected-projects.yaml
  ├─ generate_reports.py   -> docs/reports/*.md
  ├─ build_site.py         -> site/data/*.json + site/reports/
  ├─ quality_gate.py       -> 全量检查
  ├─ py_compile *.py       -> 语法检查
  └─ deploy_site.py        -> /var/www/ (仅 --deploy 时)
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

## 分类系统 (resource_type)

在 normalize.py 中定义的基于关键词的规则引擎（2 维标签）：

### resource_type（多选，LLM 打标）

| 标签 | 关键词示例 |
|---------|-----------|
| mcp-server | mcp server, model context protocol, mcp |
| skills | skill, prompt pack, slash command, agent skill, claude skill |
| rules | agents.md, claude.md, cursor rules, .cursorrules, ruleset |
| agent-framework | agent framework, multi-agent, subagent, agent orchestration |
| cli-tool | cli, terminal, command line, codebase index, repo map |
| tutorial | tutorial, guide, best practice, case study, benchmark |

### target_tools（多选，可为空）

关联到 10 个目标工具之一，通过关键词匹配推断。

## 评分系统

### 100 分制双层评分（ADR-0003）

| 层 | 节奏 | 负责 | 分值 |
|---|------|------|------|
| 可量化分 | 每日自动 | 规则驱动，基于 GitHub API 实时数据 | 60 分 |
| 质量分 | 每周 LLM | 子代理深度调查 | 40 分 |
| 总分 | 每日更新 | 可量化分 + 最近一次质量分 | 0-100 |

### 可量化分细则（60 分，每日自动）

| 维度 | 分值 | 规则 |
|------|------|------|
| Stars | 20 | >=50k=20, >=10k=16, >=5k=12, >=1k=8, >=100=4, >0=2, 0=0 |
| Activity | 15 | pushed_at 90天内=15, 180天内=12, 365天内=8, 2年内=4, 更久=1 |
| Adoption | 10 | forks>=1000=10, >=100=7, >=10=4, >0=2, 0=0 |
| Maturity | 15 | 有release=5, 有文档=3, 有tests=3, 有CI=2, license明确=2 |

### 质量分细则（40 分，每周 LLM，第 3 批实现）

| 维度 | 分值 | 由 LLM 评估 |
|------|------|------------|
| Relevance | 10 | 与 AI coding agent 生态的相关性 |
| Practicality | 10 | README 完整度、示例代码、文档质量 |
| Novelty | 10 | 内容独特性、创新性 |
| Ecosystem_value | 10 | 扩展面数量、生态重要性 |

### 配置文件

- `config/scoring-v2.yaml` - 100 分制评分配置（量化分规则 + 质量分占位 + 参照基准段）
- `config/scoring.yaml` - 旧评分配置（保留但不再使用）

### Curated 选择规则（新）

1. GitHub 高分项目优先入选（至少 30 条）
2. 确保每个工具至少 1 条 curated
3. 补满到 40 条（按分数排序）
4. Rejected：分数 <=10 或 archived 或 tracking_priority=reject

## 数据校验

validate_data.py 检查：
- seed-tools.yaml 必须含 id, name, vendor, primary_type, aliases, tracking_priority
- concepts.yaml 必须含 id, name, description
- projects.yaml 必须含 id, name, url, source_type, resource_type, target_tools, summary, review_state, total_score, tracking_priority

## 质量门禁 (quality_gate.py)

检查项：
- 归一化记录 >= 100
- curated >= 20, rejected >= 5
- 所有项目含 required 字段（resource_type, tracking_priority, total_score, quantifiable_score, quality_score）
- 所有项目含 i18n.zh/en
- review_state 为 auto-indexed / auto-curated / auto-rejected
- tracking_priority 为 pending / track / index / reject
- 每个工具覆盖 >= 1
- 官方工具 source_type=official-seed 且 tracking_priority=track
- GitHub 记录 >= 50
- config/scoring-v2.yaml 存在
- 所有必需的站点数据文件存在

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
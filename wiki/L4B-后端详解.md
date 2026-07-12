# L4B-后端详解 — 管道怎么改

> 后端（管道层）开发者深入文档。读完能独立修改管道代码。

## 管道全景

管道由 `update_tracker.py` 编排，按以下顺序执行：

```
update_tracker.py [--skip-collect] [--deploy] [--github-limit N] [--exa-limit N]
  ├─ [采集阶段]
  │  ├─ collect_github.py (--limit N)  → data/raw/github/<date>/
  │  ├─ collect_exa.py (--limit N)     → data/raw/exa/<date>/
  │  └─ normalize.py --source all      → data/projects.yaml
  ├─ 校验与丰富
  │  ├─ enrich_i18n.py                 → i18n.zh/en 补齐
  │  ├─ validate_data.py               → 数据格式校验
  │  ├─ score.py                       → data/scores.yaml
  │  ├─ finalize_data.py               → curated + rejected
  │  ├─ enrich_translations.py          → 自动双语摘要
  │  └─ enrich_i18n.py (再次)          → 确保 curated/rejected 有 i18n
  ├─ 报告与构建
  │  ├─ generate_reports.py            → docs/reports/*.md
  │  ├─ build_site.py                  → site/data/*.json
  │  ├─ quality_gate.py                → PASS/FAIL
  │  └─ py_compile                     → 语法检查
  └─ [部署阶段] (--deploy 时启用)
       └─ deploy_site.py                → → Nginx webroot
```

## 路由全景

管道无传统 API 路由。脚本间耦合通过 data/ 目录中的文件完成（管道模式：前一个脚本的输出是后一个脚本的输入）。

## 核心模块

### common.py（工具库）

关键函数：

| 函数 | 用途 |
|------|------|
| load_jsonish(rel) | 从项目根加载 JSON/YAML 文件 |
| save_jsonish(rel, data) | 保存文件，自动创建目录 |
| today() | 返回今天 ISO 日期 |
| slug(s) | 生成 URL 安全标识符 |
| run(cmd, timeout) | 执行 shell 命令 |
| score_from_stars(stars) | GitHub stars → 0-5 分 |
| total_score(p) | 6 维评分之和 |
| infer_record_kind(p) | 推断记录类型（official-tool / tutorial / ecosystem-project 等） |
| infer_source_quality(p) | 推断来源质量（verified / fallback / unverified） |
| infer_ranking_scope(p) | 推断排名范围（official / ecosystem / excluded） |
| normalize_project_fields(p) | 规范化所有必填字段 |

### normalize.py（数据归一化）

关键常量：`CATEGORY_RULES` — 9 个类别的关键词匹配字典

| 类别 | 关键词示例 |
|------|-----------|
| official-tool | CLI, terminal, agent, IDE |
| skills-prompts | skill, prompt, instruction, rule |
| mcp-acp-a2a | MCP, ACP, A2A, protocol |
| rules-instructions | .cursorrules, CLAUDE.md, AGENTS.md |
| context-engineering | context, memory, state |
| testing-review-ci | test, review, CI, quality |
| tutorial-case-study | tutorial, guide, walkthrough, example |
| benchmark-evaluation | benchmark, eval, leaderboard |
| security-sandbox | security, sandbox, safety |

### score.py（评分引擎）

从 `config/scoring.yaml` 加载配置，结构：

```yaml
source_weights:
  github: 2
  exa: 1
  official-seed: 0
  fallback-web: -2
category_weights:
  mcp-acp-a2a: 2
  skills-prompts: 2
  rules-instructions: 2
  context-engineering: 2
  # ... 其他类别
penalties:
  fallback: -2
  generic-general-ai: -1
  archived: -2
ranking:
  curated_min: 60
  rejected_min: 25
  # ...
```

### quality_gate.py（质量门禁）

执行 15+ 项检查，包括：记录数（normalized ≥ 150, curated ≥ 50, rejected ≥ 20）、11 个必填字段、i18n 完备性、review_state 合法性、fallback 标注、工具覆盖（每个工具 ≥ 10 条）、来源分布（GitHub verified ≥ 30, non-GitHub ≥ 30）、配置文件存在、报告/站点文件完整性。

### sanitize_public_data.py（数据清洗）

替换规则：
- `/root/`, `/home/`, `/Users/` 路径 → `[local-source]`
- 私有 URL（localhost, 10.x, 192.168.x, 172.16-31.x）→ `[local-url-removed]`
- 生产路径 → `[production-webroot]` / `[nginx-vhost]` / `[tls-certificate]`

删除字段：`source_doc`, `notes`
整体丢弃：含私有 URL 的记录

## 错误处理

- **采集器可独立失败：** GitHub 失败不影响 Exa，反之亦然。pipe 管道中可选 --skip-collect
- **质量门禁强制：** quality_gate.py 未通过时构建结果不可部署（但脚本仍完成，部署阶段跳过）
- **数据验证非阻塞：** validate_data.py 仅输出警告，不阻断管道
- **降级采集：** Bing RSS 作为 Exa 不可用时的兜底

## 配置管理

| 配置文件 | 位置 | 用途 |
|---------|------|------|
| 评分配置 | config/scoring.yaml | 评分权重、排名阈值、惩罚项 |
| 目标工具 | data/seed-tools.yaml | 10 个工具的 id/name/vendor/primary_type 等 |
| 查询定义 | data/queries.yaml | GitHub 和 Exa 的搜索查询 |
| 分类概念 | data/concepts.yaml | 分类体系定义 |
| 来源 | data/sources.yaml | 数据来源定义 |
| 环境变量 | .env.example | 仅 EXA_API_KEY（可选，走 mcporter 时不需要） |

## Prompt 工程

无 LLM 调用。管道中所有处理均为确定性规则和算法，不使用外部 LLM API。

## 测试覆盖

| 测试文件 | 覆盖内容 |
|---------|---------|
| tests/test_data_integrity.py | 数据完整性：检查必填字段、格式合法性 |
| tests/test_pipeline_features.py | 管道功能：采集 → 归一化 → 评分的核心路径 |

**运行命令：** `python3 -m pytest tests/ -v`
**主要靠** quality_gate.py（运行验证）而非单元测试覆盖

## 下一步读什么

→ [L5-接口契约](L5-接口契约.md)

## 更新指引

**触发条件：** 管道步骤增删、核心模块变更、评分/门禁规则变更
**更新内容：** 管道全景、核心模块、测试覆盖
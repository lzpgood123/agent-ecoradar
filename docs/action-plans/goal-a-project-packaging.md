# Goal A 行动文档：项目搭建打包与可复用化

## 目标

把 `search in coding` 打造成一个可复用的 **AI Coding Agent 生态追踪模板项目**。它不仅服务本次 Claude Code / Codex / Antigravity / OpenCode / Goose / Qoder / Trae / WorkBuddy / Cursor / Hermes 追踪，也能复制给其他技术生态使用。

## 交付物

### 必须创建

- `README.md`：项目定位、快速开始、数据说明、如何复用。
- `pyproject.toml`：Python 项目元数据和依赖说明。
- `.env.example`：`EXA_API_KEY`、GitHub/代理相关环境变量说明。
- `data/seed-tools.yaml`：10 个目标工具的结构化种子数据。
- `data/queries.yaml`：GitHub 与 Exa 搜索 query 配置。
- `data/sources.yaml`：信息源清单。
- `data/projects.yaml`：项目/文章/插件/经验记录主数据集，初始可为空或包含种子。
- `data/concepts.yaml`：概念词表。
- `schemas/*.schema.json`：tool/source/project/concept 数据结构。
- `docs/taxonomy.md`：分类体系。
- `docs/methodology.md`：采集、归一化、评分、人工审核方法。
- `docs/source-strategy.md`：GitHub、Exa、官方文档、社区渠道的来源策略。
- `docs/scoring.md`：评分模型。
- `docs/reusable-packaging.md`：如何把项目复制成另一个生态追踪器。
- `scripts/validate_data.py`：校验 YAML/JSON 基本结构。
- `scripts/collect_github.py`：用 `gh` 搜 GitHub 并保存 raw JSON。
- `scripts/collect_exa.py`：Exa 搜索适配器；如果环境缺少 Exa 凭据，给出明确错误和配置指引。
- `scripts/normalize.py`：把 raw 结果转成候选项目记录。
- `scripts/score.py`：初始规则评分。
- `scripts/build_site.py`：生成/复制站点数据。
- `scripts/export_pack.py`：打包可复用模板。
- `site/index.html`、`site/app.js`、`site/styles.css`：第一版静态可视化页面。
- `.github/workflows/update-data.yml`：GitHub Actions 定时更新模板。
- `.github/workflows/publish-site.yml`：发布 GitHub Pages 的模板。
- `.hermes/cron-prompts/*.md`：Hermes 定时追踪提示词。
- `prompts/*.md`：执行提示词库。

## 目录设计原则

1. **数据优先**：`data/*.yaml` 是事实来源，Markdown/HTML 是派生结果。
2. **raw 可追溯**：GitHub、Exa、Web 原始结果必须保存到 `data/raw/<source>/<date>/`。
3. **人工审核可见**：每条记录都有 `review_state`。
4. **可迁移**：目标工具、query、source 都放在配置里，不写死在脚本里。
5. **可离线读**：核心分析和周报保存在 Markdown，网页只是增强展示。

## 推荐执行步骤

### Step 1：初始化基础文件

创建 README、pyproject、.gitignore、.env.example。

README 至少包含：

- 项目是什么
- 为什么聚焦 terminal/agentic AI coding
- 目标工具清单
- 数据目录说明
- 如何运行采集
- 如何构建站点
- 如何复用模板

### Step 2：写种子数据

从 `/root/workspace/ai-coding-agents` 中提取 10 个工具的结构化信息到 `data/seed-tools.yaml`。

每个工具包含：

- id
- name
- vendor
- primary_type
- repo
- website
- docs
- aliases
- config_files
- extension_points
- related_concepts
- source_doc
- tracking_priority

### Step 3：写 taxonomy / methodology / scoring

将分类体系固定下来：

- official-tool
- terminal-agent
- ai-ide
- agent-harness
- rules-instructions
- skills-prompts
- mcp-acp-a2a
- context-engineering
- testing-review-ci
- multi-agent-workflow
- tutorial-case-study
- benchmark-evaluation
- ui-dashboard
- security-sandbox

### Step 4：创建脚本

脚本可以先做 MVP，但必须真实可运行：

- `validate_data.py` 能读取 YAML/JSON 并检查必填字段。
- `collect_github.py` 调用 `gh search repos` 和 `gh repo view --json`。
- `collect_exa.py` 如果 `EXA_API_KEY` 不存在，必须清楚提示；如果存在，调用 Exa API。
- `normalize.py` 做最小字段归一化。
- `score.py` 根据规则生成基础分数。
- `build_site.py` 将数据导出到 `site/data/*.json`。
- `export_pack.py` 生成 zip/tar 包或 dry-run 清单。

### Step 5：创建可视化页面

第一版页面只需要：

- 总览卡片
- 工具筛选
- 分类筛选
- 项目表格
- 分数排序
- 搜索框
- 链接跳转

不需要复杂前端框架，先用静态 HTML/JS 即可。

### Step 6：自动化模板

创建两类自动化：

1. GitHub Actions：适合开源仓库自动更新。
2. Hermes cron prompts：适合服务器长期智能分析和报告。

### Step 7：验证

运行：

```bash
python3 scripts/validate_data.py
python3 scripts/collect_github.py --dry-run
python3 scripts/collect_exa.py --dry-run
python3 scripts/build_site.py
python3 scripts/export_pack.py --dry-run
```

## 完成标准

- 所有目录和文件存在。
- 所有 Python 脚本 `--help` 可运行。
- `validate_data.py` 通过。
- `build_site.py` 生成 `site/data/*.json`。
- `export_pack.py --dry-run` 输出会打包的文件。
- README 能让别人复用这个项目。

## 注意事项

- 不要把 API Key 写入仓库。
- 不要假装 Exa 可用；如果不可用就写清配置方式。
- GitHub 搜索必须使用已配置的 `gh`，不要优先手写 unauthenticated curl。
- 所有采集结果保留 raw，以便以后重新归一化。

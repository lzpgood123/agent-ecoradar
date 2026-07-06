# Goal 文档索引

后续启动 Search in Coding 项目时，不需要复制长提示词，只需要使用：

```text
请读取并执行 /root/workspace/search in coding/prompts/start-goals-short.md
```

## 分部文档

### 总响应计划

```text
docs/response-plan.md
```

说明项目定位、两个 Goal、执行顺序、信息来源策略、长期 Hermes 自动追踪设计和验收标准。

### Goal A：项目搭建打包

```text
prompts/goal-a-project-packaging.md
docs/action-plans/goal-a-project-packaging.md
```

负责搭建可复用项目骨架、数据结构、脚本、站点、GitHub Actions、Hermes cron prompts。

### Goal B：项目收集完成

```text
prompts/goal-b-initial-collection.md
docs/action-plans/goal-b-initial-collection.md
```

负责 GitHub + Exa + 官方/社区来源采集、归一化、评分、报告和可视化。

### GitHub 搜索

```text
prompts/github-search-gh.md
```

要求 GitHub 搜索必须使用 `gh`，并保存 raw JSON。

### Exa 语义搜索

```text
prompts/exa-semantic-search.md
```

正确调用方式：

```bash
mcporter call 'exa.web_search_exa(query: "...", count: 3)'
```

### 归一化和评分

```text
prompts/normalize-and-score.md
```

负责 raw 数据去重、分类、评分，生成 `data/projects.yaml` 和站点数据。

### 周报

```text
prompts/weekly-report.md
```

用于后续 Hermes cron 每周生成 AI Coding 生态报告。

### 深度分析模板

```text
prompts/deep-dive-template.md
```

用于对单个工具、插件、MCP、skills、rules 仓库或教程做深度分析。

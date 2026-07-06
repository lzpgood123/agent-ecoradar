# Goal B 行动文档：项目收集完成与初始生态分析

## 目标

围绕 10 个目标 AI Coding 工具，完成第一批有实用价值的生态资料收集、归类、评分、分析和可视化发布。

目标工具：

1. Claude Code
2. OpenAI Codex CLI
3. Antigravity CLI / former Gemini CLI
4. OpenCode
5. Goose
6. Qoder / QoderWork
7. Trae / Trae Work / Trae Agent
8. WorkBuddy / CodeBuddy
9. Cursor
10. Hermes Agent

## 收集范围

不仅收官方工具本身，还要收：

- 扩展应用
- 插件
- MCP / ACP / A2A server
- skills / prompts / slash commands
- rules / instructions / config templates
- context engineering 工具
- codebase indexing / repo map 工具
- PR review / issue fixing / CI 自动化工具
- 教程、经验文章、case study
- benchmark / comparison / evaluation
- 可视化管理界面
- 多 agent 工作流
- 安全、沙箱、权限控制经验

## 来源优先级

### 1. Exa 语义搜索

优先用于互联网资料发现：

- 官方文档
- 博客文章
- 教程
- 社区经验
- 深度评测
- launch post
- changelog
- 视频/课程页面
- 中文社区文章

每个目标工具至少执行以下语义 query：

```text
{tool} ecosystem extensions plugins MCP skills rules best practices
{tool} tutorial workflow agentic coding case study
{tool} vs Claude Code Codex Cursor OpenCode Goose
{tool} context engineering codebase indexing rules prompts
{tool} GitHub projects open source extensions
```

针对概念执行：

```text
AI coding agent context engineering best practices
AI coding agent skills prompts rules repository
MCP servers for coding agents GitHub
spec driven development AI coding agents
terminal AI coding agents comparison
Claude Code skills best practices
Codex CLI AGENTS.md workflows
Cursor rules MCP agent workflows
OpenCode agents commands MCP
Goose recipes extensions MCP
Hermes Agent cron skills coding workflow
```

### 2. GitHub via `gh`

必须使用 `gh`：

```bash
gh search repos "claude code skills" --sort stars --limit 50 --json fullName,description,stargazersCount,url,updatedAt,language
gh search repos "codex cli agent skills" --sort stars --limit 50 --json fullName,description,stargazersCount,url,updatedAt,language
gh search repos "cursor rules" --sort stars --limit 50 --json fullName,description,stargazersCount,url,updatedAt,language
gh search repos "mcp server coding agent" --sort stars --limit 50 --json fullName,description,stargazersCount,url,updatedAt,language
gh search repos "context engineering ai coding" --sort stars --limit 50 --json fullName,description,stargazersCount,url,updatedAt,language
```

每个候选 repo 需要补充：

```bash
gh repo view OWNER/REPO --json nameWithOwner,description,url,homepageUrl,stargazerCount,forkCount,licenseInfo,repositoryTopics,primaryLanguage,pushedAt,createdAt,updatedAt,isArchived,latestRelease
```

### 3. 官方源

每个目标工具至少检查：

- 官网
- Docs
- Blog / Changelog
- GitHub repo / org
- Marketplace / extension docs
- Discord/forum/community links 如可访问

### 4. 社区源

允许收录但需要标注 `confidence`：

- Hacker News
- Reddit
- X/Twitter thread
- YouTube 视频/教程
- Medium/Substack/dev.to
- 中文：知乎、掘金、CSDN、少数派、B 站、公众号转载索引

## 第一批数量目标

### 最低完成标准

- 每个目标工具至少 10 条相关记录。
- 总记录数至少 100 条。
- 其中 GitHub repo 至少 60 条。
- 非 GitHub 互联网资料至少 30 条。
- 深度人工/LLM 分析条目至少 30 条。
- 每个大分类至少有 3 条记录，若确实没有则说明原因。

### 理想第一版

- 总记录数 150-250 条。
- 每个目标工具 15-30 条。
- 每个工具有一页生态简评。
- 形成 Top 50 推荐项目。
- 形成 10-20 条趋势观察。

## 归类规则

每条记录必须标注：

- `target_tools`：适配或关联哪些工具。
- `category`：属于哪些生态分类。
- `concepts`：关联概念。
- `source_type`：来源类型。
- `summary`：一句话概括。
- `why_it_matters`：为什么值得追踪。
- `review_state`：审核状态。

## 评分规则

每条记录评分：

```yaml
score:
  ecosystem_value: 0-5
  activity: 0-5
  adoption: 0-5
  practicality: 0-5
  novelty: 0-5
  confidence: 0-5
```

### 高价值记录特征

优先保留：

- 能实际增强目标工具使用体验。
- 有清晰安装/使用文档。
- 能跨多个 coding agent 复用。
- 代表新趋势，如 MCP、skills、rules、context engineering、multi-agent。
- 社区活跃或官方维护。
- 有真实案例/教程/benchmark。

### 降权记录

- 只有营销页面，没有技术细节。
- Repo 已长期不维护。
- 与 AI coding 关系弱。
- 只有 prompt 噱头，没有可复用价值。
- 星数高但内容不相关。

## 产出报告

创建：

- `docs/reports/initial-collection-report.md`
- `docs/reports/top-projects.md`
- `docs/reports/tool-ecosystem-comparison.md`
- `docs/reports/trends-and-opportunities.md`

### initial-collection-report.md 应包含

1. 收集时间和来源。
2. 总记录数。
3. 按工具统计。
4. 按分类统计。
5. Top 20 项目。
6. Top 10 非 GitHub 资料。
7. 重要趋势。
8. 噪声和不确定性。
9. 下一步追踪建议。

### tool-ecosystem-comparison.md 应包含

对 10 个工具分别分析：

- 官方生态成熟度
- 社区生态成熟度
- rules/skills 支持
- MCP/ACP/A2A 支持
- context engineering 能力
- 自动化/CI 能力
- 适合人群
- 生态风险

## 可视化要求

初始站点应展示：

- 项目表格
- 工具筛选
- 分类筛选
- 搜索框
- 分数排序
- Top projects
- 来源链接
- 更新时间

## 验证命令

完成后运行：

```bash
python3 scripts/validate_data.py
python3 scripts/score.py
python3 scripts/build_site.py
```

并确认：

- `data/projects.yaml` 记录数达到目标。
- `site/data/projects.json` 已生成。
- 报告文件存在且包含统计结果。
- 每条记录有来源 URL。
- 没有 API Key 或敏感信息进入仓库。

## 完成标准

Goal B 完成时，应能回答：

1. 目前围绕 Claude Code / Codex / OpenCode / Goose / Cursor / Hermes 等工具，有哪些高价值扩展项目？
2. 哪些项目适合立刻尝试？
3. 哪些只是趋势但尚未成熟？
4. 哪些概念正在塑造 AI coding 生态？
5. 这个追踪系统下周如何继续自动更新？

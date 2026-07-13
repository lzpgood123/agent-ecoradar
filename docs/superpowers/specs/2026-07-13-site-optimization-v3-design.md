# 站点优化 v3 设计：数据修正 + 审美重做 + 翻译

> 日期：2026-07-13
> 状态：用户已确认
> 作者：方案设计 Agent
> 前置：第 2 批前端重写 v2 已完成，dogfood 报告发现 42 个问题（4 Critical / 10 High / 16 Medium / 12 Low）

## 背景

dogfood 报告 + 用户反馈揭示三类核心问题：数据层（字段缺失、repo 路径错误、分类误标、项目缺失）、前端层（审美差像数据库后台、交互缺陷、信任信号失真）、翻译层（274 条 zh==en 假双语）。分三批次解决。

## 批次 A：数据层修正

### A1. 修正 seed-tools.yaml repo 路径

| 工具 | 当前 repo | 正确 repo |
|------|----------|----------|
| goose | aaif-goose/goose | block/goose |
| cursor | cursor/cursor | getcursor/cursor |
| opencode | anomalyco/opencode | sst/opencode |
| qoder | qoderAI | 补全完整 org/repo 格式 |

### A2. 手动补充缺失知名项目

通过 `gh repo view` 获取以下项目详细信息并加入 data/projects.yaml：
- continuedev/continue
- paul-gauthier/aider
- cline/cline
- rooveterinaryinc/roo
- block/goose
- getcursor/cursor
- 其他在采集过程中发现缺失的高星项目

### A3. 修正 normalize.py 字段映射

确保以下字段正确提取自 GitHub API：
- forks: forkCount（当前 0/274）
- license: licenseInfo.spdxId（当前 0/274）
- languages: primaryLanguage + languages（当前 67 条 null）
- stars: stargazerCount（当前 63 条缺失）
- topics: repositoryTopics（新增字段）
- readme_preview: 通过 `gh repo view --json readme` 获取，截取前 500 字符

### A4. 修正 resource_type 误标

至少对 curated Top 40 高星项目重新检查 resource_type，确保 skill 项目不标成 tutorial。

## 批次 B：前端审美重做（Linear/Vercel 风格）

### B1. 视觉设计

| 要素 | 设计 |
|------|------|
| Hero 区域 | 首屏大字号标题 + 总数据展示 + 渐变背景 |
| 卡片 | box-shadow + 半透明边框，非纯色边框 |
| 色彩标签 | 不同 resource_type 不同颜色 pill（mcp=绿、skills=蓝、rules=紫、framework=橙、cli=青、tutorial=灰） |
| 留白 | 区块间距加大，padding 加大 |
| 渐变 | header 背景 #0f172a -> #1e293b，score badge 渐变 |
| 字体层级 | h1=40px, h2=28px, h3=20px, 正文=16px |
| 表格 | hover 高亮，分数彩色圆形 badge，stars 带图标 |
| 工具卡片 | mini 柱状图 + 渐变背景 |
| Inter 字体 | 加载 Google Fonts Inter 或自托管 |

### B2. 交互修复（dogfood 报告）

| dogfood # | 修复 |
|-----------|------|
| #1 | 分数展示改为"可量化分 /60"，隐藏质量分进度条或标注"待 LLM 分析" |
| #5 | 新增"只看收藏"筛选 checkbox |
| #6 | writeState 保留 hash |
| #7 | 结果计数"显示 X / Y" + 清空筛选按钮 + 活跃条件 chips |
| #8 | OR/AND 改为真正的 radiogroup，点已选项不翻转 |
| #9 | 详情面板打开时立即显示 loading，数据到达后替换 |
| #10 | 详情面板展示 score_detail（stars/activity/adoption/maturity 分项） |
| #11 | 工具/类型显示人话名称（用 i18n.resourceTypes 和 tools.json 的 name） |
| #12 | 空字段隐藏（forks/license 为空时不展示该行） |
| #14 | 页脚：更新时间 + GitHub 仓库链接 + 数据说明 |
| #15 | 项目深链 `?project=id`，打开时自动展开详情 |
| #20 | 项目名可点击进详情 |
| #27 | 添加 robots.txt + favicon + OG meta 标签 |

### B3. 信息架构调整

- 指标卡从搜索区中部移到 Hero 区域（dogfood #24）
- 分数分布图从搜索区上方移到工具概览区下方（dogfood #40）
- 详情面板空字段隐藏，未上线能力不占位（dogfood #12）

## 批次 C：翻译

### C1. 批量翻译 274 条 summary

- 用 SenseNova API（DeepSeek-V4-Flash）翻译
- 13 个 API key 轮询
- 翻译结果缓存到 data/translations-cache/
- 翻译后的中文写入 i18n.zh.summary
- 每批 3 并发，274 条约 92 批

## 不做什么

- 不改 build_site.py 的精简/详情 JSON 逻辑
- 不改数据结构（projects.yaml 字段不变，只补全值）
- 不引入前端框架
- 不做全站 i18n（报告翻译等后续）
- 不运行 initial_collection.py 全面回溯（放后面）

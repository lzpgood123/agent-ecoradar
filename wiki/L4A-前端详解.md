# L4A-前端详解 — 前端怎么改

> 前端开发者深入文档。读完能独立修改前端代码。

## 页面状态机

无路由库。单页应用（SPA），所有内容在 index.html 中通过 render() 一次性渲染。

**URL 状态持久化（不刷新）：** query string 用于保存筛选状态，通过 readState() / writeState() 读写。

支持的 query 参数：
- `q` — 搜索关键词
- `tool` — 工具筛选
- `cat` — 分类筛选
- `source` — 来源筛选
- `review` — 审核状态
- `sort` — 排序方式
- `curatedOnly` — 只看推荐（1）
- `recentOnly` — 只看最近新增（1）

**导航：** 三个导航链接指向 site/reports/ 下的静态 .md 文件（浏览器直接打开）

## 组件体系

零框架、零依赖的纯原生 JS SPA。无组件/渲染函数隔离，逻辑集中在 render() 函数中。

渲染流程：
```
main()
  → fetch 4 JSON (projects, curated, tools, metrics)
  → readState() 从 URL 恢复筛选
  → 绑定事件监听
  → render()
       → applyLanguage()       — 设置语言
       → renderMetrics()       — 渲染统计卡片
       → renderOfficial()      — 渲染官方工具卡片
       → renderFiltersOnce()   — 初始化筛选下拉框
       → writeState()          — 保存筛选到 URL
       → 按 7 维度过滤数据
       → 按 5 种模式排序
       → 渲染 #rows 表格
```

## 样式体系

全深色主题（dark mode only），无 light mode。无 CSS 自定义属性，所有值硬编码。

**颜色表：**

| 用途 | 值 |
|------|-----|
| 页面背景 | #0f172a |
| header/表格背景 | #111827 |
| 卡片/统计背景 | #1e293b |
| 输入框/按钮背景 | #020617 |
| 正文文本 | #e2e8f0 |
| header 副文本 | #cbd5e1 |
| 次要文本(hint/muted) | #94a3b8 |
| 链接 | #93c5fd |
| 边框 | #334155 / #475569 |
| 按钮 active 背景 | #2563eb |
| 按钮 active 边框 | #60a5fa |

**质量标签三色体系：**
- verified: #14532d 背景
- fallback: #713f12 背景
- unverified: #4c1d95 背景

**字体：** Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif

**响应式断点：** 760px（缩小 padding、缩小字体、topbar 改为 block）

## 交互模式

**搜索：** 全文搜索（JSON.stringify 包含所有字段），input 事件无 debounce

**筛选（AND 逻辑，7 维度）：**
1. 关键词全文搜索
2. 工具筛选（target_tools 包含关系）
3. 分类筛选（category 包含关系）
4. 来源筛选（source_type 相等）
5. 审核状态筛选（review_state 相等）
6. 只看推荐（id 在 curated 集合中）
7. 只看最近新增（日期 >= 最新 50 条截止日期）

**排序（5 种模式）：**
- `name` — textOf(name) localeCompare
- `source` — source_type localeCompare
- `recent` — first_seen/last_seen 倒序
- 默认 — curated 优先 + 总分降序

**双语切换：** 点击 中文/English 按钮 → lang 变量 + localStorage → render()

**详情弹窗：** 点击项目行显示 detailHtml() — 含评分明细和 notes

## 全局变量

| 变量 | 类型 | 来源 | 用途 |
|------|------|------|------|
| projects | Project[] | data/projects.json | 全量项目 |
| curated | Project[] | data/curated-projects.json | 推荐项目集合 |
| tools | Tool[] | data/tools.json | 工具定义 |
| metrics | Metrics | data/metrics.json | 统计摘要 |
| lang | 'zh'\|'en' | localStorage / navigator.language | 当前语言 |

## 关键函数

| 名称 | 签名 | 用途 |
|------|------|------|
| $(id) | (string) => Element | document.getElementById 简写 |
| t(key) | (string) => string | 从 UI 对象获取当前语言的翻译文本 |
| textOf(item, field) | (obj, string) => string | 从项目 i18n 结构取双语字段 |
| score(p) | (Project) => number | 计算项目总分 |
| safeNumber(v) | (any) => string | 安全数字转字符串 |
| escapeHtml(s) | (string) => string | HTML 转义（& < > " '） |
| safeUrl(raw) | (string) => string | 验证 URL 仅允许 http/https |
| safeToken(s) | (string) => string | 清理为安全 CSS 类名 |
| pills(xs) | (string[]) => string | 数组渲染为 `<span class="pill">` |
| render() | () => void | 主渲染函数 |
| main() | () => Promise<void> | 异步入口函数 |

## UI 配置对象

`UI` 对象结构：`UI.zh.{...}` / `UI.en.{...}`
包含：subtitle, navFinal, navCurated, navAudit, officialTitle, rankingTitle, searchPlaceholder, allTools, allCategories, allSources, allStates, curatedOnly, recentOnly, sortScore, sortName, sortSource, sortRecent, details, copy, copied, 表格列头, metrics 嵌套等

## 下一步读什么

→ [L5-接口契约](L5-接口契约.md)

## 更新指引

**触发条件：** 页面增删、state 结构变更、交互流程变更、样式变量变更
**更新内容：** 页面状态机、关键函数、全局变量、UI 配置
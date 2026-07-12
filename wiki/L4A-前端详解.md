# L4A-前端详解 — 站点怎么改

> 前端（站点层）开发者深入文档。读完能独立修改站点代码。

## 页面状态机

Search in Coding 站点是一个单页静态站点（纯前端 SPA），无页面切换。所有交互在单一页面内完成：

- **初始状态：** 加载 index.html → app.js 通过 fetch 加载 site/data/projects.json + curated-projects.json + tools.json → 渲染主表格 + 筛选器
- **筛选状态：** 用户选择分类/工具/排序 → app.js 就地过滤 + 重排表格
- **双语切换：** 点击语言按钮 → 切换 zh/en 显示文本 → 重新渲染
- **无路由/导航：** 纯单页，无 hash 路由或页面切换

## 组件体系

站点是标准单体 HTML + JS + CSS，无框架依赖：

- **index.html** — 容器：标题区、语言切换按钮、筛选面板（分类下拉 + 工具下拉 + 排序）、主表格容器、页脚
- **app.js** — 所有逻辑在一个文件中：数据加载、筛选、渲染、双语切换
- **styles.css** — 所有样式：CSS 变量、布局、响应式

## 样式体系

| CSS 变量 | 值 | 用途 |
|---------|-----|------|
| --primary-color | #0366d6 | 主色调（链接、按钮） |
| --bg-color | #ffffff | 背景色 |
| --text-color | #333333 | 正文颜色 |
| --border-color | #e1e4e8 | 表格边框 |
| --hover-bg | #f6f8fa | 表格行悬停背景 |

**设计风格：** 简约 GitHub 风格，白底灰边框，蓝色链接。响应式布局（移动端表格横向滚动）。

## 交互模式

1. **页面加载：** fetch 并行加载 7 个 JSON 数据文件 → 全部就绪后调用 renderTable()
2. **分类筛选：** 下拉选择分类 → filterByCategory() 更新 selectedCategory → renderTable()
3. **工具筛选：** 下拉选择工具 → filterByTool() 更新 selectedTool → renderTable()
4. **排序切换：** 选择排序方式（score/name/date）→ 重排数据 → renderTable()
5. **双语切换：** 点击中/英按钮 → switchLanguage() 更新 locale → renderTable()

## 关键函数

| 函数 | 用途 | 调用方 |
|------|------|--------|
| loadData() | fetch 所有 JSON 数据文件 | window.onload |
| renderTable() | 根据筛选条件渲染表格 HTML | loadData(), filter 事件, switchLanguage() |
| filterByCategory(cat) | 按分类过滤 | 分类下拉 change 事件 |
| filterByTool(tool) | 按工具过滤 | 工具下拉 change 事件 |
| switchLanguage(locale) | 切换 zh/en | 语言按钮 click 事件 |

## 状态管理

站点无框架状态管理库，所有状态在全局变量中：

- `allProjects` — 完整项目列表（加载时保存）
- `allCurated` — 完整推荐列表
- `allTools` — 完整工具列表
- `selectedCategory` — 当前分类筛选值
- `selectedTool` — 当前工具筛选值
- `sortBy` — 当前排序方式
- `locale` — 当前语言（'zh' 或 'en'）

## 下一步读什么

→ [L5-接口契约](L5-接口契约.md)

## 更新指引

**触发条件：** 页面增删、state 结构变更、交互流程变更、样式变量变更
**更新内容：** 页面状态机、关键函数、state 结构、CSS 变量
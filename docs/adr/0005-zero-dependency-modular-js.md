# ADR-0005: 网站保持零依赖原生 JS，拆分为模块化文件

## Status: proposed

## Context

当前 `app.js` 将全部前端逻辑（数据加载、渲染、筛选、排序、双语、详情弹窗）压缩在 27 行中（单行几千字符），完全不可维护。`styles.css` 仅 1.6KB，所有颜色值硬编码。

引入前端框架（React/Vue/Svelte）可以解决可维护性问题，但与项目"简单优先、零框架前端"的核心偏好冲突，且增加构建工具链复杂度。

## Decision

保持零依赖原则，将 `app.js` 拆分为模块化文件：

- `js/i18n.js` - 双语配置和切换
- `js/data.js` - 数据加载和状态管理
- `js/filters.js` - 筛选和排序逻辑
- `js/render.js` - 渲染函数（表格、卡片、详情）
- `js/charts.js` - 原生 SVG 图表
- `js/app.js` - 入口和事件绑定

加载方式：多 `<script>` 标签（全局变量共享），不使用 ES modules（兼容性最好）。

`styles.css` 引入 CSS 自定义属性（`--color-bg` 等），替代硬编码颜色值。

## Considered Options

- **React/Vue + 构建工具链**：可维护性最好，但违反零依赖偏好，增加构建步骤
- **ES modules（`<script type="module">`）**：模块化更规范，但需要 HTTP 服务器支持（`file://` 协议不支持 module import），GitHub Pages 预览可以但本地调试不便
- **多 `<script>` 标签 + 全局变量**：最简单，兼容性最好，牺牲了模块隔离但适合当前规模

## Consequences

- 全局变量共享意味着命名冲突风险，需要命名约定（如 `SIC_data`, `SIC_filters`）
- 未来如果规模增长到需要框架，迁移成本可接受（逻辑已按职责拆分）
- CSS 自定义属性不支持 IE11，但项目已声明 dark-mode-only，不考虑旧浏览器

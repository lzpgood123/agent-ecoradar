# 批次 B：前端审美重做（Linear/Vercel 风格） 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将前端审美从"数据库后台"升级为 Linear/Vercel 风格现代深色主题产品，同时修复 dogfood 报告中 15 个 High 以上交互问题。

**架构：** 保持零依赖原生 JS 6 模块结构。重写 styles.css 为 Linear/Vercel 风格。修改 render.js/filters.js/app.js/i18n.js/index.html 修复交互和展示问题。

**技术栈：** 纯 HTML + CSS + 原生 JS，Google Fonts Inter

**关联文档：**
- 设计规格：`docs/superpowers/specs/2026-07-13-site-optimization-v3-design.md`
- dogfood 报告：`docs/ux-dogfood-report-2026-07-13.md`（42 个问题的详细诊断）
- ADR-0006：零依赖模块化
- ADR-0008：前端性能优化

**前置条件：** 批次 A 已完成（数据字段补全、repo 路径修正、分类误标修正）

---

## 文件结构

### 修改文件

| 文件 | 修改内容 |
|------|---------|
| `site/styles.css` | 完全重写为 Linear/Vercel 风格 |
| `site/index.html` | 重写：Hero 区域、信息架构调整、页脚、favicon、OG meta |
| `site/js/render.js` | 分数展示改 /60、人话标签、score_detail 展示、空字段隐藏、详情加载态、项目名可点击、结果计数、活跃条件 chips |
| `site/js/filters.js` | OR/AND radiogroup 修复、writeState 保留 hash、favoritesOnly、项目深链 |
| `site/js/app.js` | 新增交互事件委托（收藏筛选、清空筛选、项目名点击、radiogroup） |
| `site/js/i18n.js` | 新增翻译键 |
| `scripts/build_site.py` | 生成 robots.txt 和 favicon |

---

## 任务 1：重写 styles.css（Linear/Vercel 风格）

**文件：** `site/styles.css`

- [ ] **步骤 1：编写新的 styles.css**

关键设计要素：
- Hero 区域：渐变背景、大字号标题(40px)、数据指标卡
- 卡片：box-shadow + 半透明边框
- 色彩标签：6 种 resource_type 各不同颜色
- 大留白：区块间距 32px
- 渐变 score badge
- 字体层级：h1=40px, h2=28px, h3=20px, 正文=16px
- 表格 hover 高亮、分数圆形 badge
- Inter 字体加载
- 页脚样式
- 移动端表格 overflow-x

```css
/* === CSS Custom Properties === */
:root {
  --color-bg: #0f172a;
  --color-bg-gradient: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  --color-surface: #111827;
  --color-card: #1e293b;
  --color-card-hover: #243244;
  --color-input: #020617;
  --color-text: #e2e8f0;
  --color-text-secondary: #cbd5e1;
  --color-text-muted: #94a3b8;
  --color-link: #93c5fd;
  --color-border: #334155;
  --color-border-subtle: rgba(255,255,255,0.08);
  --color-accent: #2563eb;
  --color-accent-gradient: linear-gradient(135deg, #2563eb, #7c3aed);
  --color-accent-light: #60a5fa;
  --color-fav: #fbbf24;
  --color-success: #14532d;
  --color-danger: #4c1d95;
  --radius: 12px;
  --radius-sm: 8px;
  --radius-xs: 6px;
  --spacing: 32px;
  --spacing-sm: 16px;
  --spacing-xs: 8px;
  --shadow-card: 0 2px 8px rgba(0,0,0,0.3), 0 0 1px rgba(255,255,255,0.05);
  --shadow-card-hover: 0 4px 16px rgba(0,0,0,0.4), 0 0 1px rgba(255,255,255,0.1);
}

/* === Reset & Base === */
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  line-height: 1.6;
  font-size: 16px;
}
a { color: var(--color-link); text-decoration: none; }
a:hover { text-decoration: underline; }

/* === Header === */
header {
  padding: 48px var(--spacing);
  background: var(--color-bg-gradient);
  border-bottom: 1px solid var(--color-border-subtle);
}
.topbar {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing);
  align-items: flex-start;
  flex-wrap: wrap;
  max-width: 1400px;
  margin: 0 auto;
}
h1 { font-size: 40px; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.02em; }
header p { color: var(--color-text-secondary); font-size: 18px; }
nav { margin-top: 20px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
nav a { color: var(--color-link); font-size: 14px; }
.lang-switch { display: flex; gap: var(--spacing-xs); }
.lang-switch button {
  cursor: pointer;
  border: 1px solid var(--color-border);
  background: var(--color-input);
  color: var(--color-text-secondary);
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 13px;
  transition: all 0.15s;
}
.lang-switch button:hover { border-color: var(--color-accent-light); }
.lang-switch button.active {
  background: var(--color-accent);
  border-color: var(--color-accent-light);
  color: white;
}

/* === Hero Metrics === */
.hero-stats {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  margin-top: 24px;
  max-width: 1400px;
  margin-left: auto;
  margin-right: auto;
}
.hero-stat {
  background: var(--color-card);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius);
  padding: 20px 24px;
  box-shadow: var(--shadow-card);
  min-width: 140px;
}
.hero-stat b {
  font-size: 32px;
  font-weight: 800;
  display: block;
  background: var(--color-accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-stat .muted { font-size: 13px; color: var(--color-text-muted); }

/* === Main Layout === */
main { padding: var(--spacing); max-width: 1400px; margin: 0 auto; }

/* === Utility === */
.hint { color: var(--color-text-muted); font-size: 14px; }
.muted { color: var(--color-text-muted); font-size: 0.9em; }

/* === Skeleton === */
.skeleton {
  background: linear-gradient(90deg, var(--color-card) 25%, var(--color-surface) 50%, var(--color-card) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* === Section === */
section { margin-bottom: var(--spacing); }
section h2 { font-size: 28px; font-weight: 700; margin-bottom: var(--spacing-sm); letter-spacing: -0.01em; }

/* === Discovery Zone === */
.discovery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-sm);
}
.discovery-card {
  background: var(--color-card);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius);
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: var(--shadow-card);
}
.discovery-card:hover {
  border-color: var(--color-accent-light);
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-1px);
}

/* === Score Badge === */
.score-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent-gradient);
  color: white;
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 13px;
  font-weight: 700;
  min-width: 32px;
}
.score-badge-large {
  font-size: 20px;
  padding: 4px 16px;
  min-width: 48px;
}

/* === Tool Overview === */
.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--spacing-sm);
}
.tool-card {
  background: var(--color-card);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius);
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: var(--shadow-card);
}
.tool-card:hover {
  border-color: var(--color-accent-light);
  box-shadow: var(--shadow-card-hover);
}
.tool-card h3 { font-size: 20px; font-weight: 600; margin-bottom: 8px; }
.tool-stats { font-size: 13px; color: var(--color-text-muted); }

/* === Color-coded Pills === */
.pill {
  display: inline-block;
  border-radius: 999px;
  padding: 2px 10px;
  margin: 2px;
  font-size: 12px;
  font-weight: 500;
}
.pill-type-mcp-server { background: #14532d; color: #86efac; }
.pill-type-skills { background: #1e3a5f; color: #93c5fd; }
.pill-type-rules { background: #3b0764; color: #c4b5fd; }
.pill-type-agent-framework { background: #451a03; color: #fdba74; }
.pill-type-cli-tool { background: #042f2e; color: #5eead4; }
.pill-type-tutorial { background: #374151; color: #d1d5db; }
.pill-curated { background: var(--color-accent); color: white; }

/* === Chart Container === */
.chart-container { margin-bottom: var(--spacing); overflow-x: auto; }
.chart-container svg { max-width: 100%; }

/* === Search Zone === */
.controls {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
  flex-wrap: wrap;
  align-items: center;
}
input, select {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-input);
  color: var(--color-text);
  font-size: 14px;
  transition: border-color 0.15s;
}
input:focus, select:focus { outline: none; border-color: var(--color-accent); box-shadow: 0 0 0 2px rgba(37,99,235,0.2); }

/* Tag buttons */
.tag-group { display: flex; flex-wrap: wrap; gap: 6px; }
.tag-btn {
  cursor: pointer;
  border: 1px solid var(--color-border);
  background: var(--color-input);
  color: var(--color-text-secondary);
  border-radius: 999px;
  padding: 5px 14px;
  font-size: 13px;
  transition: all 0.15s;
}
.tag-btn:hover { border-color: var(--color-accent-light); color: var(--color-text); }
.tag-btn.active {
  background: var(--color-accent);
  border-color: var(--color-accent-light);
  color: white;
}

/* Mode toggle (radiogroup) */
.mode-toggle {
  display: inline-flex;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  overflow: hidden;
}
.mode-toggle button {
  border: none;
  padding: 5px 14px;
  cursor: pointer;
  background: var(--color-input);
  color: var(--color-text-muted);
  font-size: 13px;
  transition: all 0.15s;
}
.mode-toggle button.active { background: var(--color-accent); color: white; }

/* Active filter chips */
.active-filters { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: var(--spacing-sm); }
.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.filter-chip button {
  border: none;
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}

/* Result count */
.result-count { font-size: 14px; color: var(--color-text-muted); margin-bottom: var(--spacing-sm); }
.clear-filters {
  background: none;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  border-radius: var(--radius-sm);
  padding: 4px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.clear-filters:hover { border-color: var(--color-danger); color: var(--color-text); }

/* === Table === */
.table-wrapper { overflow-x: auto; border-radius: var(--radius); border: 1px solid var(--color-border-subtle); }
table { width: 100%; border-collapse: collapse; background: var(--color-surface); }
th, td { padding: 12px 16px; border-bottom: 1px solid var(--color-border-subtle); text-align: left; vertical-align: top; }
th { font-size: 12px; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; background: var(--color-card); position: sticky; top: 0; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: var(--color-card-hover); }
.project-name { cursor: pointer; color: var(--color-link); }
.project-name:hover { text-decoration: underline; }

/* === Detail Panel === */
.detail-overlay {
  display: none;
  position: fixed;
  top: 0; right: 0; bottom: 0;
  width: min(520px, 100%);
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  box-shadow: -8px 0 32px rgba(0,0,0,0.4);
  z-index: 100;
  overflow-y: auto;
  padding: var(--spacing);
}
.detail-overlay.open { display: block; animation: slideIn 0.2s ease-out; }
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
.detail-overlay h2 { margin-top: 0; font-size: 24px; }
.detail-close {
  position: absolute;
  top: 16px; right: 16px;
  cursor: pointer;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 50%;
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  color: var(--color-text-muted);
  font-size: 20px;
}
.detail-close:hover { color: var(--color-text); border-color: var(--color-accent-light); }
.detail-section { margin-bottom: var(--spacing); }
.detail-section h3 { font-size: 14px; color: var(--color-text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.score-bar { height: 8px; background: var(--color-card); border-radius: 4px; overflow: hidden; margin-top: 4px; }
.score-bar-fill { height: 100%; background: var(--color-accent-gradient); border-radius: 4px; transition: width 0.3s; }

/* Score detail grid */
.score-detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.score-detail-item { background: var(--color-card); border-radius: var(--radius-sm); padding: 12px; }
.score-detail-item .label { font-size: 12px; color: var(--color-text-muted); }
.score-detail-item .value { font-size: 20px; font-weight: 700; }

/* Detail loading */
.detail-loading { display: flex; align-items: center; justify-content: center; padding: 48px; color: var(--color-text-muted); }

/* === Favorites === */
.fav-btn {
  cursor: pointer;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  padding: 4px 8px;
  font-size: 13px;
  color: var(--color-text-muted);
  transition: all 0.15s;
}
.fav-btn:hover { border-color: var(--color-fav); }
.fav-btn.active { color: var(--color-fav); border-color: var(--color-fav); }
.fav-export-input {
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-input);
  color: var(--color-text);
  font-size: 12px;
  max-width: 300px;
}

/* === Error & Empty === */
.error-box, .empty-box { text-align: center; padding: 48px; color: var(--color-text-muted); }
.error-box button, .empty-box button {
  margin-top: 12px;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-card);
  color: var(--color-text);
  cursor: pointer;
}
.error-box button:hover { border-color: var(--color-accent); }

/* === Report === */
.report-content { line-height: 1.8; }
.report-content h1 { font-size: 24px; margin: 16px 0 8px; }
.report-content h2 { font-size: 20px; margin: 14px 0 6px; }
.report-content h3 { font-size: 16px; margin: 12px 0 4px; }
.report-content table { margin: 12px 0; }
.report-content td, .report-content th { padding: 6px 10px; }
.report-content code { background: var(--color-card); padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
.report-content ul { margin: 8px 0 8px 20px; }
.report-content pre { background: var(--color-card); padding: 12px; border-radius: var(--radius-sm); overflow-x: auto; }

/* === Footer === */
footer {
  padding: var(--spacing);
  text-align: center;
  border-top: 1px solid var(--color-border-subtle);
  color: var(--color-text-muted);
  font-size: 13px;
}
footer a { color: var(--color-link); }

/* === Responsive === */
@media (max-width: 760px) {
  main { padding: 16px; }
  .topbar { flex-direction: column; }
  .lang-switch { margin-top: 12px; }
  .detail-overlay { width: 100%; }
  .discovery-grid, .tool-grid { grid-template-columns: 1fr; }
  .table-wrapper table { min-width: 600px; }
  h1 { font-size: 28px; }
  section h2 { font-size: 22px; }
  .hero-stats { gap: 8px; }
  .hero-stat { padding: 12px 16px; min-width: 100px; }
  .hero-stat b { font-size: 24px; }
  .score-detail-grid { grid-template-columns: 1fr; }
}
```

- [ ] **步骤 2：Commit**

```bash
cd "/root/workspace/search in coding"
git add site/styles.css
git commit -m "feat: rewrite styles.css to Linear/Vercel dark theme with gradients, shadows, color-coded pills"
```

---

## 任务 2：重写 index.html

**文件：** `site/index.html`

- [ ] **步骤 1：重写 index.html**

关键改动：
1. 添加 Google Fonts Inter
2. Hero 区域：标题 + 副标题 + 数据指标卡（从搜索区移上来）
3. 工具概览区下方放分数分布图
4. 搜索区：添加结果计数、活跃条件 chips、清空筛选、只看收藏
5. 表格用 table-wrapper 包裹
6. 项目深链支持
7. 页脚：更新时间 + GitHub 链接
8. favicon + OG meta 标签

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Search in Coding - AI Coding Agent 生态追踪器</title>
  <meta name="description" content="持续自动更新的 AI Coding Agent 生态追踪索引库">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <meta property="og:title" content="Search in Coding - AI Coding Agent 生态追踪器">
  <meta property="og:description" content="持续自动更新的 AI Coding Agent 生态追踪索引库">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://coding.lzpgood.online/">
  <meta name="theme-color" content="#0f172a">
  <link rel="stylesheet" href="styles.css">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"WebSite","name":"Search in Coding","description":"AI Coding Agent ecosystem tracker","url":"https://coding.lzpgood.online/"}
  </script>
</head>
<body>
  <header>
    <div class="topbar">
      <div>
        <h1>Search in Coding</h1>
        <p data-i18n="subtitle">AI Coding Agent 生态追踪器</p>
      </div>
      <div class="lang-switch" aria-label="Language switcher">
        <button id="langZh" type="button" aria-pressed="true">中文</button>
        <button id="langEn" type="button" aria-pressed="false">English</button>
      </div>
    </div>
    <nav>
      <a href="#" data-report="weekly-report.md" data-i18n="navWeekly">生态周报</a>
      <a href="#" data-report="tool-comparison.md" data-i18n="navCompare">工具对比</a>
      <a href="#" data-report="curated-top.md" data-i18n="navTop">推荐榜</a>
      <button id="exportFav" class="fav-btn" data-i18n="exportFav">导出收藏</button>
      <input id="favExportUrl" type="text" class="fav-export-input" readonly style="display:none;" placeholder="收藏链接">
    </nav>
    <!-- Hero metrics moved here from search zone -->
    <div id="metrics" class="hero-stats" aria-label="Statistics"></div>
  </header>

  <main>
    <!-- Zone 1: Discovery -->
    <section id="discoverySection">
      <h2 data-i18n="discoveryTitle">最新发现</h2>
      <p class="hint" data-i18n="discoveryHint">按发现时间排序的高质量项目</p>
      <div id="discovery" class="discovery-grid"></div>
    </section>

    <!-- Zone 2: Tool Overview -->
    <section id="toolOverviewSection">
      <h2 data-i18n="toolOverviewTitle">工具生态概览</h2>
      <p class="hint" data-i18n="toolOverviewHint">点击工具卡片查看该工具的生态资源</p>
      <div id="toolOverview" class="tool-grid"></div>
      <div id="toolChart" class="chart-container"></div>
    </section>

    <!-- Zone 3: Search -->
    <section id="searchZone">
      <h2 data-i18n="searchTitle">生态项目搜索</h2>
      <p class="hint" data-i18n="searchHint">多选标签筛选</p>

      <!-- Score distribution chart -->
      <div id="scoreChart" class="chart-container"></div>

      <!-- Controls -->
      <div class="controls">
        <input id="q" data-i18n-placeholder="searchPlaceholder" placeholder="搜索..." aria-label="Search">
        <div id="toolTags" class="tag-group" role="group" aria-label="Tool filter"></div>
        <div id="typeTags" class="tag-group" role="group" aria-label="Type filter"></div>
        <div id="modeToggle" class="mode-toggle" role="radiogroup" aria-label="Match mode">
          <button class="active" role="radio" aria-checked="true" data-i18n="modeOR">任一匹配</button>
          <button role="radio" aria-checked="false" data-i18n="modeAND">全部匹配</button>
        </div>
        <select id="sort" aria-label="Sort">
          <option value="score" data-i18n="sortScore">分数</option>
          <option value="stars" data-i18n="sortStars">Stars</option>
          <option value="updated" data-i18n="sortUpdated">最近更新</option>
          <option value="match" data-i18n="sortMatch">标签匹配</option>
          <option value="recent" data-i18n="sortRecent">最近发现</option>
          <option value="name" data-i18n="sortName">名称</option>
        </select>
        <label><input id="curatedOnly" type="checkbox"> <span data-i18n="curatedOnly">只看推荐</span></label>
        <label><input id="recentOnly" type="checkbox"> <span data-i18n="recentOnly">只看最近新增</span></label>
        <label><input id="favoritesOnly" type="checkbox"> <span data-i18n="favoritesOnly">只看收藏</span></label>
      </div>

      <!-- Active filter chips -->
      <div id="activeFilters" class="active-filters"></div>

      <!-- Result count + clear -->
      <div class="result-count">
        <span id="resultCount"></span>
        <button id="clearFilters" class="clear-filters" data-i18n="clearFilters" style="display:none;">清空筛选</button>
      </div>

      <!-- Table -->
      <div class="table-wrapper">
        <table role="table">
          <thead>
            <tr>
              <th data-i18n="thName">名称</th>
              <th data-i18n="thType">类型</th>
              <th data-i18n="thTools">工具</th>
              <th data-i18n="thScore">分数</th>
              <th data-i18n="thStars">Stars</th>
              <th data-i18n="thLink">链接</th>
            </tr>
          </thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
    </section>
  </main>

  <footer>
    <span data-i18n="footerUpdated">数据更新于</span>: <span id="lastUpdated"></span> ·
    <a href="https://github.com/lzpgood123/search-in-coding" target="_blank" rel="noopener">GitHub</a> ·
    <span data-i18n="footerDesc">AI Coding Agent 生态追踪器</span>
  </footer>

  <!-- Detail panel -->
  <aside id="detailOverlay" class="detail-overlay" role="dialog" aria-modal="true" aria-label="Project details"></aside>

  <!-- Scripts -->
  <script src="js/i18n.js"></script>
  <script src="js/data.js"></script>
  <script src="js/filters.js"></script>
  <script src="js/charts.js"></script>
  <script src="js/render.js"></script>
  <script src="js/app.js"></script>
</body>
</html>
```

注意：实际文件中的 JS/CSS 引用应使用 build_site.py 生成的 hash 文件名。上面的 `<script src="js/i18n.js">` 是源文件引用，build_site.py 运行后会替换为 hash 版本。

- [ ] **步骤 2：Commit**

```bash
cd "/root/workspace/search in coding"
git add site/index.html
git commit -m "feat: rewrite index.html with hero area, footer, OG meta, favorites filter, result count"
```

---

## 任务 3：修改 render.js（交互修复核心）

**文件：** `site/js/render.js`

- [ ] **步骤 1：修改 render.js**

修复 dogfood 报告中的多个问题：

1. **#1 分数展示改为 /60**：score badge 旁标注"/60"，隐藏质量分进度条或标注"待分析"
2. **#10 score_detail 展示**：详情面板展示 stars/activity/adoption/maturity 分项
3. **#11 人话标签**：pills() 函数用 i18n.resourceTypes 翻译，工具名用 tools.json 的 name
4. **#12 空字段隐藏**：详情面板中 forks/license/languages 为空时不展示
5. **#9 详情加载态**：openDetail 立即显示 loading，数据到达后替换
6. **#20 项目名可点击**：表格中项目名加 data-action="detail"
7. **#7 结果计数 + 活跃条件 chips**：renderSearchZone 中显示"显示 X / Y"和活跃筛选条件
8. **#5 只看收藏**：renderSearchZone 中支持 favoritesOnly 筛选

需要修改的函数：renderMetrics、renderSearchZone、renderMore、openDetail、pills

在 render.js 中做以下修改：

**pills 函数改为带颜色的翻译版本：**
```javascript
pills: xs => (xs||[]).map(x => {
  const label = SIC_i18n.t('resourceTypes')[x] || x;
  const cls = 'pill-type-' + (x || 'default');
  return `<span class="pill ${cls}">${this.esc(label)}</span>`;
}).join(''),
```

**renderMetrics 移到 Hero 区域（已在 index.html 中移到 header）：**
```javascript
renderMetrics() {
  const m = SIC_data.metrics;
  const keys = ['projects', 'curated', 'official_tools', 'ecosystem_projects'];
  this.$('metrics').innerHTML = keys.map(k =>
    `<div class="hero-stat"><b>${this.safeNum(m[k] ?? 0)}</b><span class="muted">${SIC_i18n.t('metrics')[k]}</span></div>`
  ).join('');
},
```

**renderSearchZone 添加结果计数和活跃条件 chips：**
```javascript
renderSearchZone() {
  const curatedIds = SIC_data.curatedIds();
  let pool = SIC_data.projects;
  // Bug #5: favoritesOnly
  if (SIC_filters.favoritesOnly) {
    pool = pool.filter(p => SIC_data.isFav(p.id));
  }
  this.currentFiltered = SIC_filters.apply(pool, curatedIds);
  this.renderedCount = 0;
  if (this._observer) { this._observer.disconnect(); }
  this.$('rows').innerHTML = '';

  // Bug #7: result count
  const countEl = $('resultCount');
  if (countEl) {
    countEl.textContent = `${SIC_i18n.t('showing')} ${this.currentFiltered.length} / ${SIC_data.projects.filter(p => p.source_type !== 'official-seed' && p.tracking_priority !== 'reject').length}`;
  }

  // Bug #7: active filter chips
  this.renderActiveFilters();

  // Clear button visibility
  const clearBtn = $('clearFilters');
  if (clearBtn) clearBtn.style.display = SIC_filters.hasActiveFilters() ? '' : 'none';

  if (this.currentFiltered.length === 0) {
    this.$('rows').innerHTML = `<tr><td colspan="6" class="empty-box">${SIC_i18n.t('noResults')}<br><span class="muted">${SIC_i18n.t('adjustFilter')}</span></td></tr>`;
    return;
  }
  this.renderMore();
},

renderActiveFilters() {
  const container = $('activeFilters');
  if (!container) return;
  const chips = [];
  if (SIC_filters.searchQuery) chips.push({label: `"${SIC_filters.searchQuery}"`, type: 'q'});
  for (const t of SIC_filters.selectedTools) {
    const tool = SIC_data.tools.find(x => x.id === t);
    chips.push({label: SIC_i18n.textOf(tool, 'name') || t, type: 'tool', value: t});
  }
  for (const t of SIC_filters.selectedTypes) {
    chips.push({label: SIC_i18n.t('resourceTypes')[t] || t, type: 'type', value: t});
  }
  container.innerHTML = chips.map(c =>
    `<span class="filter-chip">${this.esc(c.label)}<button data-action="remove-filter" data-filter-type="${c.type}" data-filter-value="${this.esc(c.value || '')}">&times;</button></span>`
  ).join('');
},
```

**renderMore 中分数改为 /60 + 项目名可点击：**
```javascript
// In the row template, change:
// <b>${this.esc(SIC_i18n.textOf(p, 'name'))}</b>
// to:
// <b class="project-name" data-action="detail" data-id="${this.esc(p.id)}">${this.esc(SIC_i18n.textOf(p, 'name'))}</b>
//
// And change score display:
// <td><b>${this.safeNum(p.total_score)}</b></td>
// to:
// <td><span class="score-badge">${this.safeNum(p.total_score)}</span><span class="muted" style="font-size:11px;">/60</span></td>
```

**openDetail 添加加载态 + score_detail 展示 + 空字段隐藏：**
```javascript
async openDetail(projectId) {
  const overlay = this.$('detailOverlay');
  // Bug #9: show loading immediately
  overlay.innerHTML = `<div class="detail-loading">${SIC_i18n.t('loading')}</div>`;
  overlay.classList.add('open');

  const p = SIC_data.projects.find(x => x.id === projectId);
  if (!p) { overlay.innerHTML = '<p>Not found</p>'; return; }

  const detail = await SIC_data.loadDetail(projectId);
  const curatedIds = SIC_data.curatedIds();
  const isFav = SIC_data.isFav(p.id);
  const qScore = p.quantifiable_score || 0;
  const total = p.total_score || 0;
  const sd = detail?.score_detail || p.score_detail || {};

  // Bug #7: LLM summary fix
  const llmSummary = detail?.llm_summary;
  const summaryText = llmSummary ? (llmSummary[SIC_i18n.lang] || llmSummary.en || llmSummary.zh || '') : '';

  // Bug #12: hide empty fields
  const forksLine = p.forks ? `<p class="muted">Forks: ${this.safeNum(p.forks)}</p>` : '';
  const licenseLine = p.license ? `<p class="muted">License: ${this.esc(p.license)}</p>` : '';
  const langLine = (p.languages && p.languages.filter(Boolean).length > 0) ? `<p class="muted">Languages: ${this.esc(p.languages.filter(Boolean).join(', '))}</p>` : '';

  overlay.innerHTML = `
    <button class="detail-close" data-action="close-detail">&times;</button>
    <h2>${this.esc(SIC_i18n.textOf(p, 'name'))}</h2>
    <p class="muted">${this.esc(SIC_i18n.textOf(p, 'summary') || '')}</p>

    <div class="detail-section">
      <h3>${SIC_i18n.t('scoreDetail')}</h3>
      <div style="display:flex;gap:12px;align-items:center;margin-bottom:12px;">
        <span class="score-badge score-badge-large">${this.safeNum(total)}</span>
        <span class="muted">/ 60 ${SIC_i18n.t('quantifiable')}</span>
      </div>
      <div class="score-bar"><div class="score-bar-fill" style="width:${total/60*100}%"></div></div>
      ${qualityScore > 0 ? `<p class="muted" style="margin-top:8px;">${SIC_i18n.t('quality')}: ${this.safeNum(qualityScore)}/40</p>` : `<p class="muted" style="margin-top:8px;">${SIC_i18n.t('qualityPending')}</p>`}
    </div>

    ${sd && Object.keys(sd).length > 0 ? `
    <div class="detail-section">
      <h3>${SIC_i18n.t('scoreBreakdown')}</h3>
      <div class="score-detail-grid">
        <div class="score-detail-item"><div class="label">Stars</div><div class="value">${this.safeNum(sd.stars)}/20</div></div>
        <div class="score-detail-item"><div class="label">Activity</div><div class="value">${this.safeNum(sd.activity)}/15</div></div>
        <div class="score-detail-item"><div class="label">Adoption</div><div class="value">${this.safeNum(sd.adoption)}/10</div></div>
        <div class="score-detail-item"><div class="label">Maturity</div><div class="value">${this.safeNum(sd.maturity)}/15</div></div>
      </div>
    </div>` : ''}

    <div class="detail-section">
      <h3>${SIC_i18n.t('details')}</h3>
      <p>${this.pills(p.resource_type)}</p>
      <p>${this.pills(p.target_tools?.map(t => SIC_i18n.t('resourceTypes')[t] || t))}</p>
      <p class="muted">Stars: ${this.safeNum(p.stars)}</p>
      ${forksLine}
      ${licenseLine}
      ${langLine}
      <p class="muted">First seen: ${this.esc(p.first_seen)}</p>
      <p class="muted">Tracking: ${this.esc(p.tracking_priority)}</p>
    </div>

    ${summaryText ? `<div class="detail-section"><h3>LLM Summary</h3><p>${this.esc(summaryText)}</p></div>` : ''}

    ${detail?.readme_preview ? `<div class="detail-section"><h3>${SIC_i18n.t('readme')}</h3><pre>${this.esc(detail.readme_preview.slice(0,500))}</pre></div>` : ''}

    <div class="detail-section">
      <h3>${SIC_i18n.t('relatedProjects')}</h3>
      <div id="relatedProjects">...</div>
    </div>

    <div class="detail-section">
      <a href="${this.safeUrl(p.url)}" target="_blank" rel="noopener noreferrer">${SIC_i18n.t('open')} →</a>
      <button class="fav-btn ${isFav ? 'active' : ''}" data-action="fav" data-id="${this.esc(p.id)}">${isFav ? SIC_i18n.t('favorited') : SIC_i18n.t('favorite')}</button>
    </div>
  `;

  // Related projects (same logic as before)
  // ... (keep existing related projects code)
}
```

- [ ] **步骤 2：Commit**

```bash
cd "/root/workspace/search in coding"
git add site/js/render.js
git commit -m "fix: render.js - score /60, human-readable labels, score_detail, hide empty fields, loading state, result count, filter chips"
```

---

## 任务 4：修改 filters.js + app.js + i18n.js

**文件：** `site/js/filters.js`, `site/js/app.js`, `site/js/i18n.js`

- [ ] **步骤 1：修改 filters.js**

添加：
1. `favoritesOnly` 字段
2. `hasActiveFilters()` 方法
3. `clearAll()` 方法
4. `writeState()` 保留 hash（dogfood #6）
5. OR/AND radiogroup 正确行为
6. 项目深链 `?project=id`

```javascript
// 在 SIC_filters 对象中添加：
favoritesOnly: false,

hasActiveFilters() {
  return this.searchQuery || this.selectedTools.size > 0 || this.selectedTypes.size > 0 || this.curatedOnly || this.recentOnly || this.favoritesOnly;
},

clearAll() {
  this.searchQuery = '';
  this.selectedTools.clear();
  this.selectedTypes.clear();
  this.curatedOnly = false;
  this.recentOnly = false;
  this.favoritesOnly = false;
  this.sortBy = 'score';
  this.matchMode = 'or';
},

// writeState 修改：保留 hash
writeState() {
  const qs = new URLSearchParams();
  if (this.searchQuery) qs.set('q', this.searchQuery);
  if (this.selectedTools.size) qs.set('tools', [...this.selectedTools].join(','));
  if (this.selectedTypes.size) qs.set('types', [...this.selectedTypes].join(','));
  if (this.sortBy !== 'score') qs.set('sort', this.sortBy);
  if (this.matchMode === 'and') qs.set('mode', 'and');
  if (this.curatedOnly) qs.set('curated', '1');
  if (this.recentOnly) qs.set('recent', '1');
  if (this.favoritesOnly) qs.set('fav', '1');
  const hash = location.hash; // Bug #6: preserve hash
  history.replaceState(null, '', `${location.pathname}${qs.toString() ? '?' + qs : ''}${hash}`);
},

// readState 添加 project 深链
readState() {
  const qs = new URLSearchParams(location.search);
  // ... existing code ...
  if (qs.get('fav') === '1') this.favoritesOnly = true;
  if (qs.get('project')) this._pendingProject = qs.get('project');
},
```

- [ ] **步骤 2：修改 app.js**

添加新的事件处理：
1. favoritesOnly checkbox
2. clearFilters button
3. remove-filter chip button
4. radiogroup 正确行为（点已选项不翻转）
5. 项目深链打开详情
6. 页脚更新时间

```javascript
// 在 bindEvents() 中添加：

// Bug #5: favoritesOnly
$('favoritesOnly').addEventListener('change', e => {
  SIC_filters.favoritesOnly = e.target.checked;
  SIC_render.renderSearchZone();
  SIC_filters.writeState();
});

// Bug #7: clear filters
$('clearFilters').addEventListener('click', () => {
  SIC_filters.clearAll();
  syncUI();
  SIC_render.renderSearchZone();
  SIC_filters.writeState();
});

// Bug #8: radiogroup - click active button does nothing
$('modeToggle').addEventListener('click', e => {
  if (e.target.tagName !== 'BUTTON') return;
  const isOR = e.target.textContent.includes(SIC_i18n.t('modeOR')) || e.target === $('modeToggle').querySelectorAll('button')[0];
  const newMode = isOR ? 'or' : 'and';
  if (newMode === SIC_filters.matchMode) return; // no change if same
  SIC_filters.matchMode = newMode;
  $('modeToggle').querySelectorAll('button').forEach((b, i) => {
    b.classList.toggle('active', (i === 0) === (newMode === 'or'));
    b.setAttribute('aria-checked', (i === 0) === (newMode === 'or'));
  });
  SIC_render.renderSearchZone();
  SIC_filters.writeState();
});

// Bug #7: remove individual filter chip
// (handled in global click delegation, add case 'remove-filter')

// Bug #15: project deep link
if (SIC_filters._pendingProject) {
  SIC_render.openDetail(SIC_filters._pendingProject);
}

// Footer: last updated time
const lastUpdatedEl = $('lastUpdated');
if (lastUpdatedEl && SIC_data.metrics?.date) {
  lastUpdatedEl.textContent = SIC_data.metrics.date;
} else if (lastUpdatedEl) {
  lastUpdatedEl.textContent = new Date().toISOString().slice(0, 10);
}
```

在 handleGlobalClick 中添加 remove-filter case：
```javascript
case 'remove-filter':
  const ft = btn.dataset.filterType;
  const fv = btn.dataset.filterValue;
  if (ft === 'q') SIC_filters.searchQuery = '';
  else if (ft === 'tool') SIC_filters.toggleTool(fv);
  else if (ft === 'type') SIC_filters.toggleType(fv);
  syncUI();
  SIC_render.renderSearchZone();
  SIC_filters.writeState();
  break;
```

- [ ] **步骤 3：修改 i18n.js**

添加新翻译键：
```javascript
// zh
favoritesOnly: '只看收藏',
showing: '显示',
clearFilters: '清空筛选',
scoreBreakdown: '评分分项',
qualityPending: '质量分待 LLM 分析',
footerUpdated: '数据更新于',
footerDesc: 'AI Coding Agent 生态追踪器',
loading: '加载中...',

// en
favoritesOnly: 'Favorites only',
showing: 'Showing',
clearFilters: 'Clear filters',
scoreBreakdown: 'Score Breakdown',
qualityPending: 'Quality score pending LLM analysis',
footerUpdated: 'Data updated',
footerDesc: 'AI Coding Agent Ecosystem Tracker',
loading: 'Loading...',
```

- [ ] **步骤 4：Commit**

```bash
cd "/root/workspace/search in coding"
git add site/js/filters.js site/js/app.js site/js/i18n.js
git commit -m "fix: filters/app/i18n - favoritesOnly, clearAll, radiogroup fix, hash preservation, deep link, footer"
```

---

## 任务 5：生成 robots.txt 和 favicon

**文件：** `scripts/build_site.py`（修改）, `site/robots.txt`（生成）, `site/favicon.svg`（创建）

- [ ] **步骤 1：在 build_site.py 中添加 robots.txt 生成**

```python
# 在 main() 中添加：
robots_path = ROOT / 'site' / 'robots.txt'
robots_path.write_text(
    'User-agent: *\nAllow: /\nSitemap: https://coding.lzpgood.online/sitemap.xml\n',
    encoding='utf-8'
)
```

- [ ] **步骤 2：创建 favicon.svg**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="8" fill="#0f172a"/>
  <text x="16" y="22" font-family="monospace" font-size="18" font-weight="bold" fill="#60a5fa" text-anchor="middle">S</text>
</svg>
```

- [ ] **步骤 3：Commit**

```bash
cd "/root/workspace/search in coding"
git add scripts/build_site.py site/favicon.svg
git commit -m "feat: add robots.txt generation and favicon.svg"
```

---

## 任务 6：重建站点、部署、验证

- [ ] **步骤 1：运行 pipeline**

运行：`cd "/root/workspace/search in coding" && python3 scripts/update_tracker.py --skip-collect`
预期：PASS

- [ ] **步骤 2：部署**

运行：`cd "/root/workspace/search in coding" && python3 scripts/deploy_site.py`

- [ ] **步骤 3：浏览器验证清单**

- [ ] Hero 区域：大标题 + 渐变背景 + 指标卡显示
- [ ] "最新发现"区有项目卡片
- [ ] 工具概览区有卡片 + 柱状图
- [ ] 色彩标签：不同 resource_type 不同颜色
- [ ] 分数显示为"/60"而非"/100"
- [ ] 工具/类型显示人话名称
- [ ] 点击工具卡片 -> tag button 高亮 + 筛选 + 滚动
- [ ] OR/AND：点已选项不翻转
- [ ] 搜索后显示"显示 X / Y"
- [ ] 活跃条件 chips 显示并可移除
- [ ] 清空筛选按钮工作
- [ ] "只看收藏"功能正常
- [ ] 项目名可点击进详情
- [ ] 详情面板有加载态
- [ ] 详情面板展示 score_detail 分项
- [ ] 空字段隐藏
- [ ] 详情面板 README 预览（如有）
- [ ] 虚拟滚动连续加载
- [ ] 报告链接正常渲染
- [ ] 中英文切换正常
- [ ] 页脚显示更新时间 + GitHub 链接
- [ ] favicon 显示
- [ ] 移动端表格可滚动
- [ ] 无 JS 控制台错误

- [ ] **步骤 4：Commit 并 tag**

```bash
cd "/root/workspace/search in coding"
git add -A
git commit -m "feat: batch B complete - Linear/Vercel redesign + 15 dogfood fixes"
git tag v2025.07.13-batchB
```

---

## 验收标准

- [ ] styles.css 为 Linear/Vercel 风格（渐变、阴影、色彩标签、大留白）
- [ ] index.html 有 Hero 区域 + 页脚 + OG meta + favicon
- [ ] 分数展示为"/60"
- [ ] 工具/类型显示人话名称
- [ ] 结果计数 + 活跃条件 chips + 清空筛选
- [ ] "只看收藏"功能
- [ ] OR/AND radiogroup 正确行为
- [ ] writeState 保留 hash
- [ ] 项目名可点击 + 深链
- [ ] 详情加载态 + score_detail + 空字段隐藏
- [ ] 页脚 + robots.txt + favicon
- [ ] Inter 字体加载
- [ ] 无 JS 控制台错误
- [ ] pipeline PASS

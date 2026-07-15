# Search in Coding — 前端全面视觉重做设计方案

> **状态：** 方案已锁定（风格 B）  
> **日期：** 2026-07-14  
> **范围：** 纯前端视觉 / 交互呈现重做  
> **硬约束：** **不新增任何后端接口 / 数据契约 / API 端点**；不改采集、评分、报告生成链路  
> **原型：**  
> - `docs/design-drafts/2026-07-14-frontend-visual-redesign.html`（单风格 v2）  
> - `docs/design-drafts/2026-07-14-frontend-style-variants.html`（A–E 对照，最终选 B）

---

## 1. 目标与非目标

### 1.1 目标

1. 解决用户明确痛点：
   - 工具覆盖 / 分数分布两张 SVG **过大且难读**
   - Header 中「推荐榜 / 生态周报 / 工具对比」**位置与形态难看**
2. 全面升级视觉气质为 **Warm paper dark（风格 B）**：
   - 暖石色深色底
   - 琥珀强调色
   - 圆润卡片
   - Emil 工程感交互反馈（克制）
3. 保持现有信息架构可用：发现 → 工具概览 → 搜索
4. 保持零依赖原生 HTML/CSS/JS，构建与部署流程不变

### 1.2 非目标（明确不做）

| 不做 | 原因 |
|------|------|
| 新增后端接口 / JSON 字段 / 数据契约 | 用户硬约束：避免弄坏当前网站 |
| 改 `projects.yaml` / 评分 / 采集 / LLM 分析 | 与视觉无关 |
| 引入 React/Vue/Tailwind/图表库 | 违反零依赖与简单优先 |
| 改报告 Markdown 生成内容 | 只改前端呈现容器 |
| 全面改 URL 状态协议 | 现有 query 参数继续有效 |
| 本轮直接改生产并 deploy | 先方案，后执行 Agent 实现 |

---

## 2. 硬约束：不破坏现有站点

### 2.1 数据与接口冻结

继续只消费现有静态资源，**不新增、不改 schema**：

| 现有资源 | 用途 | 本轮 |
|----------|------|------|
| `site/data/metrics.json` | Hero 指标 | 只读 |
| `site/data/tools.json` | 工具概览 / 标签 | 只读 |
| `site/data/projects.json` | 列表 / 发现 / 图表聚合 | 只读（前端本地聚合） |
| `site/data/projects-detail.json` | 详情懒加载 | 只读 |
| `site/data/curated-projects.json` | 推荐集合 | 只读 |
| `site/reports/*.md` | 三份报告 | 只读，仅改打开方式 UI |
| `?q&tools&types&sort&mode&curated&recent&fav&project` | URL 状态 | **保持兼容** |

### 2.2 构建 / 部署冻结

- 继续用 `scripts/build_site.py` 做 CSS/JS content-hash
- 继续 `deploy_site.py` / GitHub Actions 既有流程
- 本轮只改 `site/` 源文件（`index.html` / `styles.css` / `js/*.js` 源文件），hash 由 build 再生
- **不改** Nginx 配置、API、cron、数据管道

### 2.3 功能回归底线

实现后必须仍可用：

1. 中英文切换  
2. 筛选 / 排序 / 清空 / chips  
3. 虚拟滚动表格  
4. 收藏 + 导出 URL  
5. 项目详情（数据仍来自 `projects-detail.json`）  
6. 三份报告可打开阅读  
7. `?project=` 深链  
8. 键盘 Esc 关闭浮层  

---

## 3. 已锁定产品决策（Grilling 结果）

| # | 决策 | 选择 |
|---|------|------|
| 1 | 问题对象 | 工具生态概览下两张 SVG 图 |
| 2 | 图表策略 | 保留并重做：更小、有标题/轴/柱上数值 |
| 3 | 图表排布 | 桌面并排；移动端上下堆叠 |
| 4 | 报告入口 | Header 右侧 pill 按钮组 |
| 5 | 报告呈现 | **居中浮窗 modal**（用户修正：优于侧栏） |
| 6 | 范围 | 全面视觉重做（仍零依赖） |
| 7 | 气质 | Emil 工程感；中等偏紧密度 |
| 8 | 动效 | 克制：active / hover / modal / focus；无花哨入场 |
| 9 | 字体 | 继续 Inter（B 可用 Space Grotesk 作标题可选增强，正文 Inter 兜底） |
| 10 | 配色 | **风格 B：暖石色深色 + 琥珀强调**（用户最终选定） |
| 11 | 类型 pill | 保留多色，降饱和、更克制 |
| 12 | 发现卡 | 紧凑卡 3–4 列：分数 + 名 + 1 行摘要 + 类型 |
| 13 | 工具卡 | 紧凑网格：名 + 项目数/推荐数 |
| 14 | 搜索区 | 工具栏式控制条 + 精致表格 |
| 15 | Metrics | Header 下 4 个小指标卡，再接图表 |
| 16 | 项目详情 | 可与报告共用浮窗体系，或详情继续侧栏；**默认推荐：报告用居中浮窗，项目详情可保留侧栏**（避免长详情阅读被 720px 模态限制）。若实现成本要统一，则详情也进浮窗，但宽度仍 ~720px |

> **实现备注：** 用户确认报告必须浮窗。项目详情未再单独推翻；为降低风险，方案默认：
> - 报告：居中 modal  
> - 项目详情：可继续右侧 panel（现有逻辑），仅做 B 风格皮肤  
> 两者都 **不新增接口**。

---

## 4. 视觉系统（Style B tokens）

### 4.1 颜色

```css
:root {
  /* Warm paper dark */
  --color-bg: #1c1917;              /* stone-900-ish */
  --color-bg-elevated: #292524;     /* modal / elevated */
  --color-surface: #292524;
  --color-surface-2: #35302c;
  --color-card: #2c2825;
  --color-card-hover: #35302c;

  --color-border: rgba(255, 248, 240, 0.10);
  --color-border-strong: rgba(255, 248, 240, 0.16);

  --color-text: #faf7f2;
  --color-text-secondary: #e7e0d6;
  --color-text-muted: #b5aa9c;

  --color-accent: #f59e0b;          /* amber-500 */
  --color-accent-light: #fbbf24;    /* amber-400 */
  --color-accent-soft: rgba(245, 158, 11, 0.14);
  --color-accent-border: rgba(245, 158, 11, 0.35);

  --color-link: #fcd34d;
  --color-fav: #fbbf24;
  --color-danger: #f87171;

  /* type pills: desaturated warm-friendly */
  --pill-skills-bg: rgba(251, 191, 36, 0.12);
  --pill-skills-fg: #fde68a;
  --pill-rules-bg: rgba(252, 165, 165, 0.12);
  --pill-rules-fg: #fecaca;
  --pill-mcp-bg: rgba(52, 211, 153, 0.12);
  --pill-mcp-fg: #6ee7b7;
  --pill-cli-bg: rgba(45, 212, 191, 0.12);
  --pill-cli-fg: #5eead4;
  --pill-framework-bg: rgba(251, 146, 60, 0.12);
  --pill-framework-fg: #fdba74;
  --pill-tutorial-bg: rgba(214, 211, 209, 0.12);
  --pill-tutorial-fg: #e7e5e4;
}
```

**删除 / 停用：**

- `--color-accent-gradient` 蓝紫渐变（分数徽章改为琥珀 soft fill）
- 近黑 `#0f172a / #05070b` 作为主背景（太暗，用户明确反馈）

### 4.2 形状 / 阴影 / 动效

```css
:root {
  --radius: 16px;
  --radius-sm: 12px;
  --radius-xs: 10px;
  --space: 22px;
  --space-sm: 12px;
  --space-xs: 8px;
  --max-width: 1320px;

  --shadow-card: 0 10px 30px rgba(0,0,0,0.28);
  --shadow-modal: 0 30px 90px rgba(0,0,0,0.50);
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
}
```

**交互规格（Emil 克制）：**

| 元素 | 行为 | 时长 |
|------|------|------|
| 按钮 / pill / tag / 卡片 | `:active { transform: scale(0.97) }` | 120ms |
| 卡片 hover | 边框琥珀色 + 轻微上移 1–2px | 160ms ease-out |
| Modal 打开 | `scale(0.97→1)` + fade + 居中 | 200ms ease-out |
| Modal 关闭 | 反向；Esc / 遮罩 / × | 180–200ms |
| Focus | amber ring `0 0 0 3px rgba(245,158,11,.18)` | — |
| 列表键盘切换 / 高频操作 | **不动画** | 0 |

禁止：整页入场错落动画、`transition: all`、`ease-in` 用于打开。

### 4.3 字体层级（中等偏紧）

| 角色 | 规格 |
|------|------|
| 站点标题 | 24–26px / 700 / tracking -0.04em |
| Section h2 | 17–18px / 700 |
| 卡片标题 | 13–14px / 650 |
| 正文 | 14px / 400–500（比现 16px 略紧） |
| 辅助 | 12px muted |
| 数字 metrics | 26–28px / 700 / tabular-nums / accent color |

字体栈建议：

```css
font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
/* 可选：标题增加 "Space Grotesk", Inter, ... —— 若外网字体失败则 Inter 兜底 */
```

---

## 5. 页面信息架构（首屏上→下）

```
[ sticky prototype banner 不存在于生产 ]
Header
  左：标题 + 副标题
  右：报告 pill 组 | 导出收藏 | 语言切换
Metrics 一行 4 卡
Charts 并排
  左：工具覆盖分布（可读 SVG）
  右：分数分布（可读 SVG）
最新发现（紧凑网格）
工具生态概览（紧凑网格）
生态项目搜索（工具栏 + 表格）
Footer
```

**相对现状的关键搬迁：**

| 现状 | 方案 |
|------|------|
| 图表在工具概览区底部，又大又裸 | 上移到 metrics 下，并排紧凑可读 |
| nav 链接像右侧散落文字 | Header 右侧 pill 组 |
| 报告塞进右侧 detail overlay | **居中 modal**，内含 tab 切换三报告 |
| 蓝紫深色 Linear 风 | Warm paper dark + amber |

---

## 6. 组件规格

### 6.1 Header 报告 pill

- 容器：圆角胶囊底 / 或 B 风格独立圆角按钮组（原型 B 为独立圆角按钮）
- 三项：`推荐榜` / `生态周报` / `工具对比`
- 点击：`preventDefault` → `openReportModal(reportFile)`
- active：当前打开的报告高亮
- **不改** `data-report` 文件名：`curated-top.md` / `weekly-report.md` / `tool-comparison.md`

### 6.2 Metrics

- 4 卡：`projects` / `curated` / `official_tools` / `ecosystem_projects`
- 数据源仍 `SIC_data.metrics`（现有）
- 数字用 accent 色，标签 muted

### 6.3 图表（核心痛点修复）

**仍用 `SIC_charts` 本地 SVG，不引库。**

#### 工具覆盖图

- 输入：现有 tools + projects 聚合 count（与 `renderToolOverview` 相同逻辑）
- 输出要求：
  - 卡片标题：`工具覆盖分布`
  - 副标题：`各目标工具关联项目数 · 单位：项目`
  - Y 轴刻度 + 网格线
  - 柱顶数值标签
  - X 轴短标签（截断人类可读名）
  - 高度约 180–210px，不是整屏大图

#### 分数分布图

- 输入：现有 `total_score` 数组分桶（沿用 0–20 … 81–100）
- 同样：标题 / 副标题 / 轴 / 数值
- 注意真实数据极度偏斜（大量 21–40）；数值标签必须可见，避免“只剩一根巨柱看不懂”

#### 布局

```html
<section class="charts-row">
  <article class="chart-card" id="toolChartCard">...</article>
  <article class="chart-card" id="scoreChartCard">...</article>
</section>
```

```css
.charts-row {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 12px;
}
@media (max-width: 1100px) {
  .charts-row { grid-template-columns: 1fr; }
}
```

`#toolChart` / `#scoreChart` 可保留 id，外包 chart-card；或在 `renderToolOverview` / `renderScoreChart` 写入完整 card HTML。**不改数据来源。**

### 6.4 最新发现卡

- 字段仍：score badge + name + summary 截断 + resource_type pills
- 网格：`repeat(auto-fill, minmax(240px, 1fr))` 或固定 3–4 列
- 点击仍 `data-action="detail"`

### 6.5 工具概览卡

- 字段仍：tool name + project count + curated count
- 点击仍 `data-action="tool-filter"`
- 原底部大图移走后，本区只保留网格（更干净）

### 6.6 搜索工具栏

- 视觉：单一 toolbar 容器包住 search / tags / sort / checkboxes
- 逻辑零改：`SIC_filters` / `renderTagButtons` / chips / clear 全保留
- 表格：更紧 padding、sticky thead、暖色 hover

### 6.7 报告居中浮窗（新 UI，旧数据）

**HTML 建议新增（仅前端 DOM）：**

```html
<div id="reportBackdrop" class="modal-backdrop" hidden></div>
<div id="reportModal" class="modal" role="dialog" aria-modal="true" hidden>
  <div class="modal-head">
    <div>
      <h2 id="reportModalTitle">推荐榜</h2>
      <p class="meta">报告</p>
    </div>
    <button type="button" class="modal-close" data-action="close-report">×</button>
  </div>
  <div class="modal-tabs" role="tablist">
    <button type="button" data-report="curated-top.md">推荐榜</button>
    <button type="button" data-report="weekly-report.md">生态周报</button>
    <button type="button" data-report="tool-comparison.md">工具对比</button>
  </div>
  <div id="reportModalBody" class="modal-body report-content"></div>
</div>
```

**行为：**

1. fetch 仍 `reports/<file>`（现有路径）
2. 渲染仍 `SIC_render.renderReport(md)`（现有 markdown 渲染器）
3. 写入 `#reportModalBody`，不再塞进 `#detailOverlay`（或先实现为 modal，detail 独立）
4. 关闭：× / backdrop / Esc
5. 打开时 `document.body.style.overflow='hidden'`，关闭恢复
6. 宽度 `min(720px, 100vw-32px)`，最大高度 `~78vh`，body 滚动

**无障碍：** 现有 `app.js` 报告点击逻辑从 detailOverlay 改为 reportModal 即可。

### 6.8 项目详情侧栏（皮肤升级）

- 保留 `#detailOverlay` 右侧面板逻辑，避免大改 `openDetail`
- 应用 B token：暖底、圆角关闭钮、琥珀 focus
- 宽度可维持 `min(520px, 100%)` 或微调到 `560px`
- **不改** `loadDetail` / score_detail 展示逻辑

---

## 7. 文件改动清单（仅前端）

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `site/styles.css` | 重写 token + 组件样式 | B 风格、charts-row、modal、toolbar、密度 |
| `site/index.html` | 结构调整 | Header pills 布局；metrics/charts DOM；report modal DOM；不改 script 数据路径 |
| `site/js/charts.js` | 增强 SVG 可读性 | 标题外置也可；轴、数值、高度；API 可向后兼容 |
| `site/js/render.js` | 渲染结构调整 | discovery/tool/metrics class；chart 容器；**不改数据字段** |
| `site/js/app.js` | 报告打开改为 modal | 事件绑定；Esc 同时处理 report/detail |
| `site/js/i18n.js` | 少量文案 key | 图表标题/副标题中英 |
| `site/js/*.hash.js` / `styles.hash.css` | build 再生 | 不手改 hash 产物 |

**明确不改：**

- `scripts/*.py`（除若 build 无需改则完全不动）
- `data/**`
- `schemas/**`
- `site/data/**` 生成逻辑
- `site/reports/**` 内容
- Nginx / cron / Actions 业务逻辑

---

## 8. Before → After（Emil 审查表）

| Before | After | Why |
|--------|-------|-----|
| 近黑蓝底 + 蓝紫渐变 | 暖石色底 + 琥珀单色强调 | 用户觉得太暗；B 更柔且有辨识度 |
| 裸 SVG 大图、无轴无标题 | 并排 chart-card + 标题/轴/数值 | 解决“根本看不出展示什么” |
| Header 报告像散落链接 | 右侧 pill 组 | 扫读与点击目标清晰 |
| 报告塞右侧 detail 抽屉 | 居中浮窗 + 内 tab | 用户明确偏好；短中篇报告更合适 |
| `transition: all` / 弱 easing | 指定属性 + `cubic-bezier(0.23,1,0.32,1)` | Emil：避免 all；ease-out 更跟手 |
| 卡片 hover 仅变边框 | 边框 + 轻微抬起 + active scale 0.97 | 工程感反馈，仍克制 |
| 图表在工具区底部抢视线 | metrics 下独立数据一览 | 首屏信息顺序更顺 |
| 16px 全局偏松 | 14px 基线 + 更紧 section 间距 | 中等偏紧密度 |

---

## 9. 实现批次建议（给执行 Agent）

> 方案设计 Agent 不写生产代码。执行时建议分小步，每步可预览。

### Batch 1 — 视觉 token 与骨架（低风险）

1. 替换 `styles.css` CSS 变量为 B  
2. Header / metrics / cards / table / pills 皮肤  
3. 不改 JS 逻辑  
4. 本地打开 `site/index.html`（或静态 server）目测

### Batch 2 — 图表可读化

1. 重做 `charts.js` bar/histogram 输出（轴、值、高度）  
2. `index.html` + `render.js` 把两图并排上移  
3. 工具区不再重复放大图

### Batch 3 — 报告浮窗

1. 增加 modal DOM  
2. `app.js` 报告点击改 modal  
3. Esc / 遮罩 / 与 detail 关闭不冲突  
4. i18n 标题

### Batch 4 — 密度与细节 polish

1. discovery/tool 网格与字号  
2. toolbar 布局  
3. focus / active  
4. 760px / 1100px 响应式

### Batch 5 — 验证

1. 手工点：筛选、收藏、详情、三报告、语言切换、深链  
2. `python3 scripts/build_site.py` 确认 hash 更新成功  
3. 不跑数据管道；不 deploy 除非用户明确要求  
4. 可选：对照 dogfood 清单做一轮静态 QA

---

## 10. 验收标准

### 必须通过

- [ ] 无新后端接口、无新 JSON schema、无改 data 管道  
- [ ] 两张图有标题、副标题/单位、轴或等价刻度、柱上数值，桌面并排  
- [ ] 报告入口为 Header pill，打开为居中浮窗  
- [ ] 浮窗可切换三报告，内容仍来自现有 md  
- [ ] 风格整体为 Warm paper dark + amber，不再是过暗蓝黑  
- [ ] 筛选 / 详情 / 收藏 / i18n / 深链仍可用  
- [ ] `build_site.py` 成功生成 hash 资源  
- [ ] 移动端图表堆叠，modal 接近全宽可用  

### 加分

- [ ] reduced-motion 媒体查询下关闭非必要 transform  
- [ ] modal 焦点陷阱（Tab 循环）  
- [ ] 图表 aria-label 完整  

---

## 11. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 改 render 时误伤筛选逻辑 | 只改 className / 外层 HTML 字符串，不改 `SIC_filters.apply` |
| 报告 modal 与 detail Esc 冲突 | 统一 close 栈：先关最上层 |
| 图表在 5k 项目上聚合卡顿 | 继续现有一次 filter map；勿在每次 hover 重算 |
| 字体 CDN 慢 | Inter 已有；Space Grotesk 可选，失败不影响 |
| 用户觉得 B 仍偏暗 | token 已比 A/C 亮；可再把 `--color-bg` 微调到 `#211e1b` 而不改结构 |
| hash 文件与 index 不一致 | 只改源 `styles.css`/`js/*.js`，必跑 build_site |

---

## 12. 文档与原型索引

| 产物 | 路径 |
|------|------|
| 本方案 | `docs/design-drafts/2026-07-14-frontend-visual-redesign-spec.md` |
| 单页 v2 草稿 | `docs/design-drafts/2026-07-14-frontend-visual-redesign.html` |
| 五风格对照 | `docs/design-drafts/2026-07-14-frontend-style-variants.html`（选 B） |
| 产品决策 | `wiki/P1-产品决策日志.md`（同步追加） |

---

## 13. 给执行 Agent 的边界声明

```
允许：
- 修改 site/index.html, site/styles.css, site/js/* 源文件
- 运行 scripts/build_site.py 再生静态 hash
- 更新 wiki L4A / L1 中与前端展示相关的描述

禁止：
- 新增任何 HTTP API / 云函数 / 后端路由
- 修改 data/*.yaml 业务数据与评分字段
- 修改 weekly_analysis / collect / normalize 逻辑
- 未获用户确认前 git push / 正式站 deploy
```

---

## 14. 决策摘要（一句话）

> 在 **零后端变更** 前提下，把站点视觉升级为 **Warm paper dark（琥珀强调）**，重做可读并排图表，Header 报告 pill + **居中浮窗**阅读三份报告，其余数据与交互契约保持兼容。

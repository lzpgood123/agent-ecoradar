# 前端全面视觉重做（风格 B · Warm paper dark）实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在零后端变更前提下，把 `site/` 升级为 Warm paper dark（琥珀强调），修复图表可读性与 Header 报告入口，报告改为居中浮窗。

**架构：** 纯前端源文件改造 + `scripts/build_site.py` 再生 hash。数据仍只读现有 `site/data/*` 与 `site/reports/*.md`。项目详情保留右侧 `#detailOverlay`，仅换 B 皮肤；报告用独立 `#reportModal`。

**技术栈：** 原生 HTML/CSS/JS，零依赖 SVG 图表，既有事件委托。

**真相源：** `docs/design-drafts/2026-07-14-frontend-visual-redesign-spec.md`（§9 批次 + §10 验收）

**硬约束：**
- 不改 `data/**`、采集/评分/LLM/cron、JSON schema、后端接口
- 不引入框架/图表库
- URL query 协议兼容
- 未确认前不 push / 不 deploy
- 只改无 hash 源文件，再跑 `build_site.py`

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `site/styles.css` | B token、Header pills、metrics、charts-row、modal、toolbar、密度、响应式 |
| `site/index.html` | Header 布局、metrics/charts DOM、report modal DOM、theme-color |
| `site/js/charts.js` | 可读 bar/histogram（轴、网格、柱上数值、高度） |
| `site/js/render.js` | chart card 外壳、工具区不再塞大图逻辑、metrics 类名保持 |
| `site/js/app.js` | 报告 modal 打开/关闭；Esc 栈（先 report 再 detail）；tab 切换 |
| `site/js/i18n.js` | 图表标题/副标题、报告 meta、modal 相关文案 |
| `scripts/build_site.py` | 仅运行，不改逻辑 |

---

## 任务列表（对齐 spec §9）

### 任务 1：CSS token + B 皮肤（Batch 1）

**文件：**
- 修改：`site/styles.css`（全文 token 与组件皮肤）
- 修改：`site/index.html`（`theme-color`、可选 header class；暂不接 modal 逻辑也可先加 DOM 壳）

- [ ] **步骤 1：** 替换 `:root` 为 Warm paper dark tokens（spec §4.1–4.2）
- [ ] **步骤 2：** Header / topbar / nav report-pills / lang / metrics / cards / table / pills / score-badge / detail 皮肤
- [ ] **步骤 3：** 去掉蓝紫 `--color-accent-gradient` 主用法；分数徽章改琥珀 soft fill
- [ ] **步骤 4：** active `scale(0.97)`、hover 边框+微抬、focus amber ring；避免 `transition: all` 滥用
- [ ] **步骤 5：** 基线字号 ~14px；section h2 ~17–18px；站点标题 ~24–26px

### 任务 2：图表可读化 + 上移（Batch 2）

**文件：**
- 修改：`site/js/charts.js`
- 修改：`site/index.html`（`#chartsSection` / `.charts-row`）
- 修改：`site/js/render.js`（`renderToolOverview` / `renderScoreChart`）
- 修改：`site/js/i18n.js`（图表标题文案）
- 修改：`site/styles.css`（`.charts-row` / `.chart-card`）

- [ ] **步骤 1：** `barChart` 输出带 Y 轴刻度、网格、柱顶数值、X 短标签；高度 ~180–210
- [ ] **步骤 2：** `histogram` 沿用 5 桶，走增强 barChart
- [ ] **步骤 3：** DOM：metrics 下并排两张 chart-card；工具概览区移除底部大图容器
- [ ] **步骤 4：** render 写入 `#toolChart` / `#scoreChart`（card 内 body），外层标题可用 HTML 或 i18n
- [ ] **步骤 5：** 桌面 `1.15fr 0.85fr`，`max-width:1100px` 堆叠

### 任务 3：报告居中 modal（Batch 3）

**文件：**
- 修改：`site/index.html`（`#reportBackdrop` / `#reportModal`）
- 修改：`site/js/app.js`
- 修改：`site/js/render.js`（可选 `openReportModal` / `closeReportModal` 辅助）
- 修改：`site/styles.css`（modal）
- 修改：`site/js/i18n.js`

- [ ] **步骤 1：** 增加 modal DOM（spec §6.7）
- [ ] **步骤 2：** Header 报告改为 pill 按钮/链接组，`data-report` 文件名不变
- [ ] **步骤 3：** fetch `reports/<file>` + `SIC_render.renderReport(md)` → `#reportModalBody`
- [ ] **步骤 4：** tab 切换三报告；当前 active 高亮
- [ ] **步骤 5：** × / backdrop / Esc 关闭；body overflow 锁定
- [ ] **步骤 6：** Esc 栈：若 report 开则先关 report，否则关 detail

### 任务 4：密度与 polish（Batch 4）

**文件：**
- 修改：`site/styles.css`
- 修改：`site/index.html`（controls → toolbar 容器 class）
- 可选：`site/js/render.js` discovery/tool 字号结构微调（不改字段）

- [ ] **步骤 1：** discovery `minmax(240px,1fr)`；tool 紧凑网格
- [ ] **步骤 2：** search `.toolbar` 包住 controls
- [ ] **步骤 3：** 760 / 1100 响应式
- [ ] **步骤 4：** `@media (prefers-reduced-motion: reduce)` 关闭非必要 transform

### 任务 5：build + 功能回归（Batch 5）

- [ ] **步骤 1：** `python3 scripts/build_site.py`
- [ ] **步骤 2：** 确认 `site/index.html` 引用的 hash CSS/JS 文件存在
- [ ] **步骤 3：** 静态检查：报告 modal 标记、charts-row、无新后端路径
- [ ] **步骤 4：** 能跑则 `pytest tests/test_build_site_v2.py`（若存在且相关）
- [ ] **步骤 5：** 手工/脚本验收清单（筛选、收藏、详情、三报告、i18n、`?project=`、Esc）
- [ ] **步骤 6：** 更新 wiki L4A / L3 / L6（必要时 L1）+ wiki-checkpoint
- [ ] **步骤 7：** **不** push / deploy

---

## 验收清单（证据必须来自本轮命令）

- [ ] 无新后端接口 / 无改 data 管道
- [ ] 两图：标题/副标题、轴或刻度、柱上数值；桌面并排
- [ ] Header 报告 pill + 居中浮窗 + 三报告切换 + 现有 md
- [ ] 筛选/排序/chips/清空/收藏/导出/中英文/虚拟滚动
- [ ] 详情侧栏 + `?project=` 深链
- [ ] Esc / 遮罩 / × 与 detail 不互踩
- [ ] `build_site.py` 成功；hash 资源存在
- [ ] 视觉为 Warm paper dark + amber

---

## 实现备注

- 以代码 + 本 spec 为准；L4A 仍描述旧 Linear/Vercel 蓝紫主题时，实现后更新 wiki。
- 真实分数分布极度偏斜（大量 21–40）；柱上数值必须可读。
- 报告不进 `#detailOverlay`。

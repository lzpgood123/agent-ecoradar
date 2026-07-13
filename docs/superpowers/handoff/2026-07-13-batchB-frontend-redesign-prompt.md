# 新对话 Agent 启动提示词：批次 B - 前端审美重做

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是"Search in Coding"项目的开发 Agent。你的任务是实现**批次 B：前端审美重做**--将站点从「数据库后台」风格重做为 Linear/Vercel 现代深色审美，同时修复 dogfood 报告中的 15 个交互问题（分数展示、收藏筛选、结果计数、OR/AND 切换、详情面板加载态、评分明细展示、空字段隐藏、页脚、项目深链、键盘可访问性等）。

## 第一步：加载技能框架

立即调用 Skill 工具加载 `using-superpowers` 技能。这是你在该项目中工作的前置要求。

## 第二步：阅读项目上下文

按 `wiki/README.md` 的阅读路线图理解项目，必读：

1. `wiki/README.md` - 项目总索引和阅读路线图
2. `wiki/L1-全景.md` - 项目是什么、核心流程
3. `wiki/L3-代码地图.md` - 代码在哪、改哪个文件
4. `wiki/L4A-前端详解.md` - 前端状态机、组件体系、样式体系（**核心参考**）
5. `wiki/L6-经验录.md` - 相关坑和注意事项（重点读"前端零依赖"决策）

## 第三步：阅读设计文档

1. `docs/superpowers/specs/2026-07-13-site-optimization-v3-design.md` - **本次设计文档（核心）**，重点读"批次 B：前端审美重做"章节
2. `docs/ux-dogfood-report-2026-07-13.md` - **dogfood 报告**，42 个问题的详细诊断，重点读以下 15 个待修复项：
   - #1 分数展示改为"可量化分 /60"
   - #5 新增"只看收藏"筛选 checkbox
   - #6 writeState 保留 hash
   - #7 结果计数"显示 X / Y" + 清空筛选 + 活跃条件 chips
   - #8 OR/AND 改为真正的 radiogroup
   - #9 详情面板打开时立即显示 loading
   - #10 详情面板展示 score_detail 分项
   - #11 工具/类型显示人话名称
   - #12 空字段隐藏
   - #14 页脚：更新时间 + GitHub 仓库链接 + 数据说明
   - #15 项目深链 `?project=id`
   - #20 项目名可点击进详情
   - #27 添加 robots.txt + favicon + OG meta 标签
3. `wiki/P1-产品决策日志.md` - 用户偏好和产品约束（重点读 2026-07-13 的审美相关决策）

## 第四步：阅读实现计划

实现计划已存在于 `docs/superpowers/plans/2026-07-13-batchB-frontend-redesign.md`，直接按计划执行。

使用 `subagent-driven-development` 技能执行实现计划。每个子 Agent 必须遵循 TDD--先写测试再写实现（前端交互逻辑可在 `tests/` 中用 JS 逻辑测试或 build_site.py 级别测试）。

## 第五步：执行实现

按实现计划中的任务顺序执行。核心工作内容：

| 任务 | 内容 | 涉及文件 |
|------|------|---------|
| B1-视觉 | Hero 区域 + 卡片 + 色彩标签 + 留白 + 渐变 + 字体层级 + 表格 + 工具卡片 + Inter 字体 | `site/styles.css`, `site/index.html` |
| B2-交互 | dogfood 15 个修复（分数/收藏/计数/AND-OR/详情/评分/空字段/页脚/深链/名称点击/SEO） | `site/js/*.js`, `site/index.html` |
| B3-信息架构 | 指标卡移到 Hero 区域，分数分布图移到工具概览下方 | `site/js/render.js`, `site/index.html` |

## 第六步：验证

调用 `verification-before-completion` 技能进行验证：

### 视觉验收
- [ ] Hero 区域：大字号标题 + 总数据展示 + 渐变背景
- [ ] 卡片：box-shadow + 半透明边框（非纯色边框）
- [ ] 色彩标签：6 种 resource_type 各用不同颜色 pill（mcp=绿、skills=蓝、rules=紫、framework=橙、cli=青、tutorial=灰）
- [ ] 留白：区块间距加大，padding 加大
- [ ] 渐变：header 背景 #0f172a -> #1e293b，score badge 渐变
- [ ] 字体层级：h1=40px, h2=28px, h3=20px, 正文=16px
- [ ] 表格：hover 高亮，分数彩色圆形 badge，stars 带图标
- [ ] Inter 字体已加载

### 交互验收
- [ ] dogfood #1：分数展示改为"可量化分 /60"，质量分标注"待 LLM 分析"
- [ ] dogfood #5：新增"只看收藏"筛选 checkbox
- [ ] dogfood #6：筛选后 URL hash（含收藏 hash）保留
- [ ] dogfood #7：结果计数"显示 X / Y" + 清空筛选按钮 + 活跃条件 chips
- [ ] dogfood #8：OR/AND radiogroup，点已选项不翻转
- [ ] dogfood #9：详情面板打开时立即显示 loading
- [ ] dogfood #10：详情面板展示 score_detail（stars/activity/adoption/maturity 分项）
- [ ] dogfood #11：工具/类型显示人话名称
- [ ] dogfood #12：空字段隐藏（forks/license 为空时不展示该行）
- [ ] dogfood #14：页脚：更新时间 + GitHub 仓库链接 + 数据说明
- [ ] dogfood #15：项目深链 `?project=id`，打开时自动展开详情
- [ ] dogfood #20：项目名可点击进详情
- [ ] dogfood #27：robots.txt + favicon + OG meta 标签

### 信息架构验收
- [ ] dogfood #24：指标卡从搜索区中部移到 Hero 区域
- [ ] dogfood #40：分数分布图从搜索区上方移到工具概览区下方

### 整体验收
- [ ] 无 JS 控制台错误
- [ ] 移动端响应式正常（375px 宽度测试）
- [ ] 站点部署到 https://coding.lzpgood.online/ 并可访问

## 第七步：更新 Wiki

开发完成后，按 wiki 各文档底部的"更新指引"更新：
- `wiki/L3-代码地图.md` - 更新前端文件列表（如文件结构有变化）
- `wiki/L4A-前端详解.md` - **大幅更新**（新的视觉体系、交互修复、信息架构调整）
- `wiki/L6-经验录.md` - 记录前端审美重做的坑

## 关键约束

1. **零依赖原生 JS**：不引入任何前端框架或外部库（ADR-0006），Inter 字体通过 Google Fonts 或自托管加载
2. **不改数据结构**：`projects.yaml` 字段不变，前端读取已有字段
3. **不改 build_site.py**：构建逻辑（精简/详情 JSON、hash 文件名）不变
4. **CSS 自定义属性**：所有颜色值用 `var(--color-xxx)`，不硬编码
5. **频繁 commit**：每个任务完成后 commit

## 不能改动的部分

- `data/` 目录下的数据文件 - 由批次 A 修正
- `scripts/build_site.py` - 构建逻辑不变
- `scripts/score.py` / `scripts/normalize.py` - 评分/归一化逻辑不变
- `data/seed-tools.yaml` / `data/concepts.yaml` - 不变
- 后端 pipeline 逻辑

## 依赖关系

**本批次依赖批次 A 完成**：批次 A 修正了字段映射（forks/license/languages/stars/topics）和 resource_type 误标，前端才能正确展示补全后的数据。如果批次 A 未完成，详情面板的空字段隐藏（dogfood #12）和评分明细展示（dogfood #10）将基于不完整数据。

## 项目环境信息

- 操作系统：Ubuntu 24.04.4 LTS
- Python：3.12.3（用 python3）
- GitHub CLI：gh 已认证（lzpgood123）
- 工作目录：`/root/workspace/search in coding`
- 站点部署：`/var/www/coding.lzpgood.online/`（Nginx）
- 测试命令：`source .venv/bin/activate && python3 -m pytest tests/ -v`
- 站点构建：`python3 scripts/build_site.py`
- 站点部署：`python3 scripts/deploy_site.py`

## 注意事项

- 前端测试无法用 pytest 自动化，需在浏览器中手动验证所有交互
- 前端审美是主观的，以 Linear/Vercel 风格为参照，深色主题、简洁信息型
- 移动端测试：用浏览器 DevTools 模拟 375px 宽度
- Inter 字体加载需考虑性能：优先自托管或用 `font-display: swap`
- 用户偏好详细编号分步指导和精准区分状态含义
- 完成前必须验证对比确认无误

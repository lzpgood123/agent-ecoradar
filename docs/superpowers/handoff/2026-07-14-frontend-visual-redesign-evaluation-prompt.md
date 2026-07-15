# 评估提示词：前端 Warm paper dark 视觉重做

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是 **Search in Coding** 项目的**独立质量评估 Agent**。开发 Agent 声称已完成 **前端全面视觉重做（风格 B · Warm paper dark）**。你必须用**可复核证据**判定 **PASS / CONDITIONAL / FAIL**，**禁止**只听开发 Agent 自述。

你**不是**实现者：默认**不改代码**、不 push、不 deploy。若发现必须修的 P0，只在报告里列出修复建议与优先级，交给用户决定是否另开修复对话。

工作区：`/root/workspace/search in coding`  
线上站（若本轮未 deploy，以本地 `site/` 产物为准，并在报告中写明评估对象）：  
- 本地：`site/`（`python3 -m http.server` 或等价静态服务）  
- 线上：`https://coding.lzpgood.online/`（仅当用户确认已 deploy 后才作为主证据）

---

## 真相源（按此顺序读）

1. **`docs/design-drafts/2026-07-14-frontend-visual-redesign-spec.md`** — 设计与验收标准（核心）  
2. `docs/superpowers/handoff/` 中对应的**实现启动提示词**（若用户粘贴了实现对话结论，也作为声称清单）  
3. 对照原型（实现应对齐 **B**，不是 A/C/D/E）：  
   - `docs/design-drafts/2026-07-14-frontend-style-variants.html?style=B`  
4. `wiki/P1-产品决策日志.md` → 节 **2026-07-14（前端全面视觉重做 grilling）**  
5. `wiki/L4A-前端详解.md`、`wiki/L3-代码地图.md`、`wiki/L6-经验录.md`（检查是否已随实现更新）  
6. 实际代码与产物：`site/index.html`、`site/styles.css`、`site/js/*.js`（源文件 + build 后的 hash 文件）

---

## 评估方法

### 第一步：确认评估对象与边界

1. 查 git 状态：改动是否主要落在 `site/` 前端源文件 + build 产物？  
2. **硬边界抽查（任一失败可直接 FAIL 或至少 CONDITIONAL 且写清风险）：**  
   - 无新增后端路由 / API / 服务端接口  
   - 无改 `data/**` 业务 schema、采集、normalize、weekly LLM、评分管道（本任务不应动）  
   - 无引入 React/Vue/Tailwind/Chart 等依赖  
   - URL query 协议仍兼容：`q/tools/types/sort/mode/curated/recent/fav/project`  
3. 确认是否 **push / deploy**：按方案默认应**未**正式 deploy，除非用户另令。报告中单独写清。

### 第二步：视觉与信息架构（对照风格 B）

在浏览器或静态预览中检查，并保留截图/DOM/CSS 证据：

| # | 检查项 | 期望 |
|---|--------|------|
| V1 | 整体色板 | 暖石色深色底 + **琥珀/amber 强调**；不再是过暗近黑 + 蓝紫渐变主风格 |
| V2 | Header 报告入口 | 「推荐榜 / 生态周报 / 工具对比」为 **Header 右侧 pill/按钮组**，不是散落右上难看链接 |
| V3 | Metrics | Header 下约一行 4 个指标卡（总记录/推荐/官方工具/生态项目） |
| V4 | 图表位置 | **metrics 下方并排**（桌面）；不在工具概览底部占大块难读 |
| V5 | 图表可读性 | 每张图有标题（及副标题/单位）、轴或等价刻度、**柱上数值**；高度紧凑 |
| V6 | 发现区 | 紧凑卡片网格（约 3–4 列桌面）：分数 + 名 + 一行摘要 + 类型 pill |
| V7 | 工具概览 | 紧凑网格：工具名 + 项目数/推荐数；点击仍可筛选 |
| V8 | 搜索区 | 工具栏式控制条 + 表格；密度中等偏紧 |
| V9 | 类型 pill | 仍有类型色差，但饱和度克制，融入暖色体系 |
| V10 | 动效 | 克制：active/hover/modal/focus；无花哨整页入场动画 |

### 第三步：报告浮窗（用户强偏好）

| # | 检查项 | 期望 |
|---|--------|------|
| R1 | 打开方式 | 点 Header 报告 pill → **居中 modal/浮窗**，不是塞进右侧 detail 当报告主容器 |
| R2 | 内容来源 | 仍 fetch 现有 `site/reports/curated-top.md` / `weekly-report.md` / `tool-comparison.md` |
| R3 | 浮窗内切换 | 可在浮窗内切换三份报告（tab 或等价），无需关窗重开（若 spec 要求） |
| R4 | 关闭 | × / 遮罩 / Esc 可用；与项目详情关闭不互相踩坏 |
| R5 | 渲染 | 现有 markdown→HTML 仍可读（标题/列表/表格不崩） |

### 第四步：功能回归（不得为美化牺牲）

逐项点测或脚本辅助，**每项写证据**（操作步骤 + 结果）：

- [ ] 中英文切换  
- [ ] 工具/类型多选筛选、OR/AND、排序  
- [ ] 结果计数、活跃 chips、清空筛选  
- [ ] 只看推荐 / 最近 / 收藏  
- [ ] 虚拟滚动或分页加载更多仍工作  
- [ ] 收藏切换 + 导出收藏 URL  
- [ ] 项目详情可打开（默认侧栏 + B 皮肤可接受）  
- [ ] `?project=<id>` 深链仍打开对应详情  
- [ ] 工具卡片点击 → 筛选同步 + 跳到搜索区  
- [ ] 页脚更新时间 / GitHub 链接仍在  

### 第五步：构建与产物

```bash
cd "/root/workspace/search in coding"
# 源文件与 hash 引用一致
python3 scripts/build_site.py
# 或至少检查：index.html 引用的 styles.*.css / js/*.<hash>.js 文件存在
ls -la site/styles.css site/styles.*.css site/js/*.js | head -50
# 确认无误把手改 hash 当唯一源
```

- [ ] `build_site.py` 成功（或开发已跑通且产物自洽）  
- [ ] `index.html` 引用的 hashed CSS/JS 真实存在  
- [ ] 无把业务数据 JSON 改坏（抽查 `site/data/metrics.json` 等仍可加载）

### 第六步：Wiki 合规

- [ ] `L4A-前端详解` 是否反映新 CSS 变量、图表布局、报告 modal  
- [ ] `L3` / `L1` 若有展示层变化是否更新  
- [ ] `L6` 是否记录实现坑（若有）  
- [ ] **不应**出现虚假的后端/接口变更描述  

### 第七步：与原型 B 的偏差

打开 `docs/design-drafts/2026-07-14-frontend-style-variants.html?style=B`，对比生产实现：

- 允许：工程化细节差异、真实数据量导致的图表比例差异  
- 不允许：退回蓝紫 Linear 主风格、报告又变回难看侧栏主路径、图表又变无标注大图  

---

## 必过项（硬）

以下任一项不满足 → 结论不得为 **PASS**（应为 FAIL 或 CONDITIONAL，并说明）：

1. **无新增后端接口 / 未改数据管道契约**（边界未破）  
2. **图表可读**：有标题与数值（轴或等价信息），桌面并排，不再“巨大且看不懂”  
3. **报告为居中浮窗**（或等价居中 modal），Header 为 pill 入口  
4. **核心筛选 / 详情 / 收藏 / i18n / 深链** 仍可用  
5. **静态构建产物自洽**（源 + hash 引用正确）  
6. 整体视觉可识别为 **Warm paper dark + amber**，不是过暗蓝黑主调  

---

## 判定标准

| 结论 | 含义 |
|------|------|
| **PASS** | 硬项全过；仅有轻微视觉 polish 问题且不影响使用 |
| **CONDITIONAL** | 主路径可用，但有明确遗留（列出 P0/P1）；需小修后再评估或可带条件接受 |
| **FAIL** | 硬项失败、功能回归坏、或越界改了后端/数据管道 |

优先级标注：

- **P0**：阻断使用 / 破边界 / 报告或筛选不可用  
- **P1**：明显不符合 B 或 spec，但不阻断浏览  
- **P2**：纯 polish  

---

## 报告格式（必须按此输出）

```markdown
# 前端视觉重做评估报告（风格 B）

- 评估时间：
- 评估对象：本地 site/ | 线上 URL | 二者
- 结论：PASS | CONDITIONAL | FAIL

## 1. 边界与范围
| 检查 | 结果 | 证据 |
|------|------|------|
| 无新后端接口 | ✅/❌ | ... |
| 未改数据管道 | ✅/❌ | ... |
| 零依赖保持 | ✅/❌ | ... |
| push/deploy 状态 | 已/未 | ... |

## 2. 视觉与架构（V1–V10）
（表格：项 / ✅🟡❌ / 证据）

## 3. 报告浮窗（R1–R5）
（表格 + 证据）

## 4. 功能回归
（表格 + 证据）

## 5. 构建与产物
（命令输出摘要）

## 6. Wiki 合规
（读过哪些、是否过时）

## 7. 与原型 B 偏差
（关键差异列表）

## 8. 问题清单
| ID | 优先级 | 描述 | 建议 |
|----|--------|------|------|
| ... | P0/P1/P2 | ... | ... |

## 9. 总结
- 完成率：约 x%（相对 spec 验收清单）
- 是否建议用户接受上线/deploy：是 / 否 / 修好 P0 后再说
- 下一步建议：...
```

---

## 注意事项

- 你是**独立评估者**：开发 Agent 说 “done” 不算证据。  
- 区分「本地已改但未 deploy」与「线上已生效」——用户最怕弄坏现网，报告里必须写清评估的是哪一层。  
- 不要因为“更好看”就放宽功能回归失败。  
- 不要自行开始大重构；评估结束即停。  
- 中文输出报告。  

## 项目环境

- 工作区：`/root/workspace/search in coding`  
- 前端：静态 `site/`，构建 `python3 scripts/build_site.py`  
- 设计真相源：`docs/design-drafts/2026-07-14-frontend-visual-redesign-spec.md`  

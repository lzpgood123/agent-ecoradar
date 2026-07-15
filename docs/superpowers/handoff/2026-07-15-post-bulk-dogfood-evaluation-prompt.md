# 评估提示词：Post-Bulk 上线 Dogfood（四批完成后的站点验收）

> 将以下全部内容复制粘贴到**新对话**中作为第一条消息。  
> 本任务是**独立质量评估 / 探索性 QA**，不是开发、不是再跑 Batch1–4。

---

## 你的任务

你是 "Search in Coding" 的**独立站点评估 Agent**。

Post-bulk 四批（push → 前端性能 → 数据/normalize/首次 deploy → LLM 策略与 backlog）已完成，线上站点应展示约 **5165** 条数据，并具备：

- 搜索索引（search-index）
- 详情分片（`data/detail/*.json` + detail-index，**无**单体 projects-detail.json）
- 大量 LLM 字段（quality_score / tracking_priority / llm_summary 等）
- gzip JSON

你的目标：对 **https://coding.lzpgood.online/** 做系统性 dogfood，用**证据**判断站点是否达到可长期公开使用的质量，并产出结构化报告。

**结论只能是：`SHIP` / `SHIP_WITH_FIXES` / `NO_SHIP`。**

---

## 第一步：加载技能

1. 优先 `skill_view("dogfood")`，并按其 5 阶段流程（Plan → Explore → Collect → Categorize → Report）执行。
2. 若有浏览器工具：用 browser 做交互与截图证据。
3. 若无浏览器：用 curl + 读取线上 JSON + 本地 `site/` 对照，**明确标注「无浏览器，交互项降级为接口/静态检查」**。
4. 技能加载失败不要停工：继续按本提示词清单执行。

---

## 第二步：阅读最小上下文（不要重做四批开发）

必读（只读）：

1. `wiki/L1-全景.md`
2. `wiki/L4A-前端详解.md`（页面/筛选/详情）
3. `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`（验收目标与「不做什么」）
4. 可选：`wiki/L6-经验录.md` 最近条目

**禁止：**

- 改代码、改数据、deploy、push
- 启动 enrich / normalize / weekly_analysis
- 把本评估当成 Batch1–4 重跑

工作区：`/root/workspace/search in coding`  
输出目录建议：`docs/dogfood-post-bulk-2026-07-15/`（`report.md` + `screenshots/`）

---

## 第三步：基线事实核对（先证据后结论）

在开始交互前，先记录基线（命令 + 输出摘要）：

```bash
cd "/root/workspace/search in coding"

# 线上 metrics
curl -sS -m 20 https://coding.lzpgood.online/data/metrics.json | python3 -m json.tool | head -80

# 关键产物是否存在
curl -sS -m 20 -o /dev/null -w 'home:%{http_code}\n' https://coding.lzpgood.online/
curl -sS -m 20 -o /dev/null -w 'projects:%{http_code}\n' https://coding.lzpgood.online/data/projects.json
curl -sS -m 20 -o /dev/null -w 'search-index:%{http_code}\n' https://coding.lzpgood.online/data/search-index.json
curl -sS -m 20 -o /dev/null -w 'detail-index:%{http_code}\n' https://coding.lzpgood.online/data/detail-index.json
curl -sS -m 20 -o /dev/null -w 'legacy-detail:%{http_code}\n' https://coding.lzpgood.online/data/projects-detail.json

# gzip
curl -sS -m 20 -I -H 'Accept-Encoding: gzip' https://coding.lzpgood.online/data/projects.json | tr -d '\r' | grep -iE 'HTTP/|content-encoding|content-type|content-length'

# 本地对照（可选）
ls -lh site/data/projects.json site/data/search-index.json site/data/detail-index.json 2>/dev/null
ls site/data/detail 2>/dev/null | wc -l
```

**期望基线（允许小幅漂移，但要写明实测值）：**

| 项 | 期望 |
|----|------|
| home HTTP | 200 |
| metrics.projects | ≈ 5165 |
| search-index | 200 存在 |
| detail-index | 200 存在 |
| projects-detail.json | **404 或不存在**（已删除单体） |
| detail 分片 | 约 52 个（ceil(5165/100)） |
| projects.json gzip | `content-encoding: gzip` |

若基线严重不符（例如线上仍是旧数据、无分片），直接在报告标 **Critical**，可提前 `NO_SHIP`。

---

## 第四步：Dogfood 清单（按优先级）

每项记录：✅ / 🟡 / ❌ + 证据（URL、截图路径、curl 输出、控制台错误）。

### A. 首屏与导航（P0）

1. 首页可打开，Hero/指标区显示合理项目数（≈5165）
2. 主导航可用：发现 / 理解（报告）/ 搜索或等价入口
3. 无明显白屏、布局崩坏、字体/主题崩溃
4. 控制台无阻塞性 JS 错误（打开首页后检查）

### B. 列表与筛选（P0）

5. 项目列表可滚动/分页或虚拟列表可用，不是空白
6. resource_type 筛选：至少测 2 种（如 mcp-server、skills）有结果或正确空态
7. target_tools 筛选：至少测 2 种工具（如 claude-code、cursor）
8. 清空筛选 / 活跃条件 chips（若有）工作正常
9. 收藏：添加/取消/只看收藏（若有）不丢状态

### C. 搜索（P0，性能相关）

10. 输入常见词（如 `mcp`、`claude`、`cursor`）有结果
11. 输入无意义串有空态，不报错
12. 连续输入不应卡死页面（体感；若能量化，记输入到结果出现耗时）
13. 抽查：结果与关键词相关（不是完全乱序噪声）

### D. 详情面板 / 分片加载（P0）

14. 点击列表项打开详情（或 `?project=` 深链）
15. 详情有 loading → 内容替换，不长期空白
16. 详情展示关键字段：name、url、summary、resource_type、target_tools、分数
17. 有 LLM 的项目：quality / llm_summary（或等价文案）可见；未分析有合理占位
18. 网络面板或日志可证明详情走 `detail-index` + `detail/{n}.json`，**不是**单体 projects-detail
19. 连续打开 3–5 个不同项目，无卡死/错绑项目

### E. 报告与次要页（P1）

20. 报告入口可打开，至少 1 份报告有实质内容
21. 中英文切换（若有）：UI 文案切换；项目 summary 中文（若已翻译）不整站假双语崩溃

### F. 性能与载荷（P1）

22. 记录 projects.json 传输是否 gzip
23. 记录 search-index / detail 分片是否可访问
24. 首屏体感：是否可在合理时间交互（有浏览器则估；无浏览器则写网络体积与推断）
25. 大列表滚动是否明显掉帧/卡死（有浏览器才评）

### G. 数据质量抽检（P1，不重跑管道）

从线上或本地 `data/projects.yaml` / metrics 抽查：

26. tutorial 占比是否仍明显失控（参考门禁曾要求 ≤30%；现网应远好于旧 52%）
27. general-ai-coding 是否仍占绝大多数（应明显下降）
28. pending 约 200 量级可接受，但首页/列表不应大量“全坏”
29. 抽 10 个高星项目：标签/摘要是否离谱（记样本名）

### H. 已知遗留（核对，不自动 FAIL）

30. 仍有 ~200 pending 未分析 → 记 🟡 观察，除非导致主路径不可用
31. 工作区未跟踪 handoff/bak 文件 → **不在本评估范围**（除非影响线上）

---

## 第五步：问题分级

| 级别 | 含义 |
|------|------|
| **Critical** | 主路径不可用（首页挂、列表空、搜索挂、详情全挂、数据量级错误） |
| **High** | 核心功能严重受损（筛选失效、详情大量错绑、控制台错误阻断交互） |
| **Medium** | 可绕过的功能/体验问题 |
| **Low** | 文案、轻微样式、边缘态 |

去重后按 Critical → Low 排序。

---

## 第六步：结论规则

| 结论 | 条件 |
|------|------|
| **SHIP** | 无 Critical；High ≤1 且有明确 workaround；P0 清单基本全 ✅ |
| **SHIP_WITH_FIXES** | 无 Critical；有若干 High/Medium，需排期修复但仍可公开 |
| **NO_SHIP** | 存在 Critical，或 P0 多处 ❌，或线上数据/产物与 post-bulk 目标严重不符 |

**不要**因为还有 ~200 pending 就自动 NO_SHIP。

---

## 报告格式（必须）

写入：`docs/dogfood-post-bulk-2026-07-15/report.md`

```markdown
# Post-Bulk 上线 Dogfood 报告

- 日期：
- 站点：https://coding.lzpgood.online/
- 评估 Agent：
- 结论：SHIP | SHIP_WITH_FIXES | NO_SHIP

## 执行摘要
- 测了什么 / 没测什么
- 问题计数：Critical/High/Medium/Low
- 一句话建议

## 基线证据
- metrics.projects =
- search-index / detail-index / legacy-detail =
- gzip =
- 分片数 =

## P0 清单结果表
| # | 项 | 结果 | 证据 |
|---|----|------|------|

## 问题列表（按严重度）
### C1 / H1 / ...
- 标题
- 严重度 / 类别
- URL
- 复现步骤
- 期望 vs 实际
- 证据（截图 MEDIA: 路径 / curl / console）

## 数据质量抽检
- tutorial / general / pending 观察
- 10 个高星样本笔记

## 修复优先级建议（给下一开发批次）
1. ...
2. ...

## 测试环境与限制
- 是否有浏览器
- 网络/地区限制
```

聊天里用中文给用户一份**短摘要**（结论 + Top 问题 + 是否可继续公开）。

---

## 关键约束

1. **只评估，不修改**
2. **证据优先**：无证据不写 Critical
3. 截图用 `MEDIA:/absolute/path`（若平台支持）
4. 区分「功能坏了」与「还有 pending 未分析」
5. 不评估 Hermes 内部过程、不泄露密钥/服务器敏感路径到公开报告正文（路径可用相对 `docs/...`）

---

## 项目环境

- 站点：https://coding.lzpgood.online/
- 工作区：`/root/workspace/search in coding`
- 预期规模：5165 projects；detail 分片 ~52；无单体 detail
- 输出：`docs/dogfood-post-bulk-2026-07-15/report.md`

---

## 最终汇报（聊天）

1. 结论：`SHIP` / `SHIP_WITH_FIXES` / `NO_SHIP`
2. Critical/High 数量与 Top 3 问题
3. 报告文件路径
4. 建议的下一动作（修 bug 批次 / 可先公开 / 需先停）

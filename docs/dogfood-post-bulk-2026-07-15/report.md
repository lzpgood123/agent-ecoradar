# Post-Bulk 上线 Dogfood 报告

- 日期：2026-07-15
- 站点：https://coding.lzpgood.online/
- 评估 Agent：独立站点评估 Agent（Hermes / dogfood skill）
- 结论：**SHIP_WITH_FIXES**

## 执行摘要

- **测了什么**：线上基线（metrics / 产物 HTTP / gzip / 分片）、数据与前端逻辑对齐的搜索/筛选/列表池仿真、详情分片加载与 LLM 字段、报告文件可达性、静态资源完整性、CSP/安全头、数据质量抽检（tutorial / general / pending / 高星样本 / 路径泄露）。
- **没测什么**：**无浏览器工具**，交互项（真实点击、滚动帧率、控制台运行时错误、localStorage 收藏端到端、报告浮窗 DOM、中英文切换视觉）降级为接口 + 线上 JS 静态审查 + 本地/线上数据对照。大列表掉帧未测。
- **问题计数**：Critical **0** / High **1** / Medium **3** / Low **3**
- **一句话建议**：**可以继续公开使用**；主路径（首页、列表、搜索、详情分片、报告源文件）达标，建议尽快修 CSP 与 Google Fonts 冲突、清理 official-seed 的 `/root/...` 文案泄露，并观察首包体积与 stars 噪声。

## 基线证据

| 项 | 期望 | 实测 |
|----|------|------|
| home HTTP | 200 | **200**（HTML ~6893 B） |
| metrics.projects | ≈5165 | **5165** |
| tracking | pending ~200 可接受 | pending **201** / track **4495** / index **404** / reject **65** |
| curated / rejected | 有数据 | curated **40**，rejected **10**（metrics）；`data/curated-projects.json` **200** |
| search-index | 200 存在 | **200**，数组长度 **5165** |
| detail-index | 200 存在 | **200**，dict 长度 **5165**，chunk 0–**51** |
| projects-detail.json（单体） | 404 / 不存在 | **404** |
| detail 分片 | ~52 | **52** 个（`detail/0.json`…`detail/51.json` 抽样 0/1/51 均 200） |
| projects.json gzip | content-encoding: gzip | **gzip**；压缩传输约 **760 334 B (~743 KB)**，解压约 **6 377 867 B (~6.1 MB)** |
| search-index gzip | 有则更好 | **gzip**，约 **389 694 B** |
| 本地对照 | 一致 | 本地 `site/data` projects/search-index/detail-index 与线上 id 集合一致；detail 目录 **52** 文件 |

补充 metrics（线上 `data/metrics.json`）：

- resource_type：agent-framework 1529 / skills 1340 / cli-tool 1319 / mcp-server 1004 / **tutorial 953** / extension 370 / rules 178
- tool_coverage 示例：claude-code 2653 / cursor 903 / **general-ai-coding 51**
- ecosystem_projects：5090；official_tools：10

证据摘录见：`docs/dogfood-post-bulk-2026-07-15/evidence-baseline.txt`

## P0 清单结果表

| # | 项 | 结果 | 证据 |
|---|----|------|------|
| A1 | 首页可打开，Hero/指标合理 | ✅ | `home:200`；metrics.projects=5165；HTML 含 `#metrics` / 三区 section |
| A2 | 主导航：发现/理解(报告)/搜索 | ✅ | HTML：`#discoverySection`、`nav` 三报告链（weekly/tool-comparison/curated-top）、`#searchZone` |
| A3 | 无明显白屏/主题崩溃 | 🟡 | 静态壳完整、hashed CSS/JS 均 200；**CSP 拦截 Google Fonts** 可能导致回退系统字体（见 H1/M1） |
| A4 | 控制台无阻塞性 JS 错误 | 🟡 | **无浏览器**，未抓 runtime console；静态资源齐，逻辑文件无语法级缺失；CSP 可能产生 font 相关 console 报错 |
| B1 | 列表非空 / 分页逻辑存在 | ✅ | 默认列表池（排除 official-seed + reject）**5090**；`renderMore` + IntersectionObserver PAGE_SIZE=50 仍在线上 `render.ec3a64.js` |
| B2 | resource_type 筛选 ≥2 种 | ✅ | 仿真：`mcp-server`→1000，`skills`→1337，`tutorial`→905；无效类型→0 |
| B3 | target_tools 筛选 ≥2 种 | ✅ | `claude-code`→2648，`cursor`→902，`hermes-agent`→641 |
| B4 | 清空筛选 / chips | ✅ | `filters.clearAll` / `hasActiveFilters` / `renderActiveFilters` 存在于线上 JS |
| B5 | 收藏添加/取消/只看收藏 | ✅ | `SIC_data.toggleFav` + localStorage；`favoritesOnly` 在 `renderSearchZone` 前置 filter（非 apply 内，但可用） |
| C1 | 常见词搜索有结果 | ✅ | `mcp` 1220 / `claude` 2702 / `cursor` 905（search-index Map，~4–6 ms 仿真） |
| C2 | 无意义串空态 | ✅ | `zzzznotexist12345` → 0 |
| C3 | 连续输入不卡死 | 🟡 | 无浏览器体感；索引 includes 仿真亚 10 ms，**主耗时在首包下载**（projects ~1.7–2.1 s 量级） |
| C4 | 结果相关性抽查 | ✅ | mcp 结果含 headroom/goose 等 mcp-server；非纯噪声 |
| D1 | 详情打开 / 深链参数 | ✅ | `?project=` 由 `readState`→`_pendingProject`；`openDetail` loading→内容 |
| D2 | loading → 内容，不长期空白 | ✅ | 线上 `openDetail` 先写 `detail-loading` 再 `loadDetail` |
| D3 | 关键字段展示 | ✅ | 分片含 name/url/summary/resource_type/target_tools/分数/score_detail |
| D4 | LLM 字段 / 未分析占位 | ✅ | 已分析：`llm_summary` {zh,en}、`quality_score`；pending：`llm_summary=null`，UI 有 `qualityPending` |
| D5 | 走 detail-index + detail/{n}.json | ✅ | `data.js` 明确无单体 fallback；`projects-detail.json` 404；抽样 8 项目 chunk 命中 |
| D6 | 连续多项目不错绑 | ✅ | 多 id 分属 chunk 0/2/3，均 found 且 id 匹配 |
| E1 | 报告入口有实质内容 | ✅ | `reports/weekly-report.md` 200（~2 KB，含 5165 概况与 Top10）；tool-comparison / curated-top 200 |
| E2 | 中英文切换 | 🟡 | i18n 键齐全；**无浏览器**未点测；项目 summary 中文依赖 i18n 字段，未做全站假双语崩溃证明 |
| F1 | projects.json gzip | ✅ | Content-Encoding: gzip，~743 KB on wire |
| F2 | search-index / detail 可访问 | ✅ | 均 200 + gzip（detail/0 ~53 KB gzip） |
| F3 | 首屏可交互时间 | 🟡 | 无浏览器；串行 metrics+tools+projects+curated+search-index，projects+search 合计约 **3–4 s** 量级（本机到同源），**未达 spec「首屏 <2s」理想目标**但可加载 |
| F4 | 大列表滚动 | ⚪ | 无浏览器，未评 |
| G* | 数据质量 | 见下节 | tutorial/general 达标；pending 201 可观察 |

## 问题列表（按严重度）

### H1 — CSP 与 Google Fonts 冲突，字体链路失效

- **严重度**：High  
- **类别**：Functional / Console / Visual  
- **URL**：https://coding.lzpgood.online/  
- **复现步骤**：
  1. 打开首页 HTML，可见 `fonts.googleapis.com` / `fonts.gstatic.com` 预连接与 stylesheet。
  2. 读取响应头 `Content-Security-Policy`：`style-src 'self'`、`font-src 'self'`，**未**放行 Google Fonts。
  3. 浏览器将拦截外部字体 CSS（本评估无浏览器，依 CSP 规范推断；静态证据充分）。
- **期望**：要么允许字体域名，要么移除外部字体依赖、改用系统栈。  
- **实际**：HTML 依赖外部 Inter，CSP 禁止 → 字体不加载，可能有 console CSP 报错；页面仍可用（系统字体回退）。  
- **证据**：
  - HTML head 含 Google Fonts link  
  - 响应头：`content-security-policy: default-src 'self'; script-src 'self'; style-src 'self'; ... font-src 'self'; connect-src 'self' ...`  
- **影响**：非主路径阻断，但属线上一致性/体验问题；严格 CSP 环境下属明确配置错误。

### M1 — 首包体积与串行加载导致「首屏 <2s」目标偏紧

- **严重度**：Medium  
- **类别**：UX / Performance  
- **URL**：`/data/projects.json` + `/data/search-index.json`  
- **复现**：curl 计时（本机）：projects gzip ~**1.7–2.1 s** 下载 + search-index ~**2.2 s** 量级；前端 `loadAll` 串行 await。  
- **期望**（post-bulk batch2）：首屏 <2s、gzip 后尽量 <1MB（projects 已 ~743 KB，达标边缘）。  
- **实际**：gzip 良好；但解压后 projects 仍 **~6.1 MB**，解析+串行拉取使冷启动偏慢。  
- **证据**：gzip 760334 B / 解压 6377867 B；`data.js` loadAll 顺序 metrics→tools→projects→curated→search-index。

### M2 — official-seed summary / search-index 泄露服务器本地路径

- **严重度**：Medium  
- **类别**：Content / Privacy  
- **URL**：列表与详情中的 official 条目；search-index 文本  
- **复现**：线上 projects/search-index 中 5 条 summary 含 `/root/workspace/ai-coding-agents/...`  
- **期望**：公开站点无服务器绝对路径。  
- **实际**：5 个 official-seed 描述指向本机文档路径（进入 search-index，可被搜索到）。  
- **证据**（id）：`official-claude-code`、`official-codex-cli`、`official-goose`、`official-cursor`、`official-workbuddy-codebuddy`  
- **说明**：非密钥泄露；仍属公开面卫生问题。

### M3 — 部分高星仓库分类/标签仍偏粗或可疑

- **严重度**：Medium  
- **类别**：Content  
- **URL**：列表高星样本  
- **期望**：高星项目类型贴近真实（agent/skills/mcp 等）。  
- **实际抽检**：
  - `openclaw/openclaw` stars 极高、**reject**、类型 **tutorial**、tools 空 — 列表已排除 reject，合理。  
  - `ultraworkers/claw-code` 高分高星标为 **tutorial**（可能偏弱）。  
  - `agency-agents` tools **[]** 但仍 index/score 可用。  
  - stars 量级存在异常高值（GitHub 星数是否被污染/镜像需另议，非本批 Critical）。  
- **证据**：见「数据质量抽检」样本表。

### L1 — 稀有 resource_type 无 i18n 标签

- **严重度**：Low  
- **类别**：Content / UX  
- **实际**：`mcp-client` / `examples` / `collection` / `mcp-host` / `course` 等各 1 条，i18n `resourceTypes` 无键时回退原始 type 字符串。  
- **证据**：metrics rare types；i18n 文件检查。

### L2 — `reports/` 目录列表 403

- **严重度**：Low  
- **类别**：UX  
- **实际**：直接访问 `/reports/` → 403；具体 md 文件 200。站点通过 `fetch('reports/'+file)` 打开，**功能不受影响**。  
- **证据**：`reports/:403`，`reports/weekly-report.md:200`。

### L3 — empty `target_tools` 比例偏高（合法但体验偏空）

- **严重度**：Low  
- **类别**：Content  
- **实际**：全量 empty tools **1643/5165 (~31.8%)**；listable **1586/5090 (~31.2%)**。符合 batch3「允许空 tools」策略，筛选「按工具」时这些项目需靠类型/搜索露出。  
- **证据**：projects.json 统计。

## 数据质量抽检

### 门禁相关观察

| 指标 | 旧 bulk 问题 | 现网 | 判定 |
|------|--------------|------|------|
| tutorial 占比 | 52.3% | **953/5165 ≈ 18.45%**（listable ≈17.8%） | ✅ 远好于 ≤30% |
| general-ai-coding | 62.1% | **51/5165 ≈ 0.99%** | ✅ 远好于 ≤45% |
| pending | ~5120 | **201** | 🟡 可观察，主路径不依赖全量 LLM |
| quality_score > 0 | 极少 | **4950/5165** | ✅ 大量 LLM 字段已落地 |
| pending 且 quality>0 | — | **0** | 一致 |

### 10 个高星非 seed 样本笔记

| 项目 | stars | types | tools | score / q | tp | 笔记 |
|------|------|-------|-------|-----------|-----|------|
| openclaw/openclaw | 382882 | tutorial | [] | 49 / 0 | reject | 列表排除；类型粗 |
| obra/superpowers | 254195 | agent-framework, skills | hermes-agent | 83 / 34 | track | 合理 |
| affaan-m/ECC | 229393 | agent-framework, mcp-server | claude-code 等 | 83 / 34 | track | 合理 |
| ultraworkers/claw-code | 194755 | tutorial | codex-cli | 88 / 39 | track | 高分但 tutorial 存疑 |
| multica-ai/andrej-karpathy-skills | 191805 | skills, rules | claude-code | 76 / 31 | track | 合理 |
| mattpocock/skills | 169034 | skills | claude-code | 84 / 35 | track | 合理 |
| anthropics/skills | 160984 | skills | claude-code | 82 / 35 | track | 合理 |
| x1xhlol/system-prompts-and-models-of-ai-tools | 141905 | tutorial | 多工具 | 79 / 32 | track | 合集类→tutorial 可接受 |
| msitarzewski/agency-agents | 131253 | agent-framework | [] | 65 / 16 | index | tools 空 |
| garrytan/gstack | 121763 | skills, rules | claude-code | 84 / 35 | track | 合理 |

### 详情 LLM 抽样

- `github-dietrichgebert-ponytail`：`llm_summary.zh/en` 正常；`quality_detail` 四维齐全；`last_analyzed=2026-07-15`。  
- pending 例 `github-gsd-build-get-shit-done`：`quality_score=0`，`llm_summary=null`，UI 应显示 qualityPending。

## 修复优先级建议（给下一开发批次）

1. **P0 配置**：修正 CSP 与字体策略（放行 `fonts.googleapis.com`/`fonts.gstatic.com` **或**去掉 Google Fonts，统一系统字体）。  
2. **P0 内容卫生**：改写 5 条 official-seed summary，去掉 `/root/workspace/...`；重建 search-index 后 deploy。  
3. **P1 性能**：评估 projects 字段再瘦身 / 并行 fetch / 可选拆列表索引；逼近首屏 <2s。  
4. **P1 数据**：继续消化 pending（~201）；抽查高星 tutorial 误标；按需补 rare type i18n。  
5. **P2**：`reports/` 目录 403 可保持（防列举）或加索引页；监控异常 stars 源数据。

## 测试环境与限制

- **是否有浏览器**：**无**（dogfood browser 工具集不可用；`browser_navigate` 等不存在）。  
- **方法降级**：curl + 线上 JSON + 线上 hashed JS 静态审查 + 与本地 `site/` 对照 + 前端筛选/搜索逻辑 Python 复现。  
- **网络**：评估机与站点同源/近源；TTFB 含本机链路，**不代表**全球用户 CDN 体验。  
- **未改代码 / 未 deploy / 未跑 enrich·normalize·weekly_analysis**。  
- 交互项（真实滚动掉帧、收藏 UI 往返、报告浮窗视觉、语言切换截图）需后续有浏览器的 dogfood 补测。

## 结论判定依据

| 规则 | 状态 |
|------|------|
| Critical | **0** |
| High | **1**（CSP/Fonts，有系统字体 workaround，主路径可用） |
| P0 主路径 | 首页/列表/筛选/搜索/详情分片/报告源 **基本全 ✅** |
| 数据与 post-bulk 目标 | 5165、分片 52、无单体 detail、gzip、tutorial/general 达标 |

→ **SHIP_WITH_FIXES**（可继续公开；建议尽快修 H1 + M2，不必因 pending≈200 停站）。

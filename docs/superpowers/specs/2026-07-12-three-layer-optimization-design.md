# Search in Coding 三层优化设计

> 日期：2026-07-12
> 状态：待用户审查
> 作者：方案设计 Agent

## 背景

当前项目存在三层连锁问题：信息收集层有 24% 垃圾数据（含狗狗买卖、Google表格函数等完全无关内容），数据分析层评分完全由 source_type 决定而非内容质量（同来源项目分数差异极小），网站层代码不可维护且功能极度简陋（27行压缩 JS、618条全量渲染、假双语）。

## 问题诊断

### 信息收集层

| 问题 | 严重程度 | 数据支撑 |
|------|---------|---------|
| fallback-web 返回完全无关内容 | 严重 | 147条中含 morkie狗狗买卖、Google Sheets函数等 |
| Exa 不可用时无安全 fallback | 严重 | fallback到通用web搜索，结果不可控 |
| 查询静态、无自适应 | 中等 | queries.yaml 固定25条GitHub query + 8条Exa query |
| 工具覆盖不均匀 | 中强 | claude-code 156条 vs trae 63条 |
| 无包管理器追踪 | 低 | npm/PyPI/crates.io 数据缺失 |
| 无社区来源 | 中等 | Reddit/HN/博客RSS未覆盖 |

### 数据分析层

| 问题 | 严重程度 | 数据支撑 |
|------|---------|---------|
| 评分由来源决定非内容 | 严重 | github 14-22分, exa 13-16分, fallback 5-10分，同来源内差异极小 |
| 双语是假的 | 严重 | 618/618 条 zh == en |
| 分类无校验 | 中等 | 纯关键词匹配，无二级校验 |
| 无趋势数据 | 中等 | 所有记录 first_seen = 2026-07-06 |
| concepts/integration_surfaces 空置 | 低 | 仅10条有值（2%填充率） |
| 无内容相关性过滤 | 严重 | 狗狗买卖、文心一言等混入 |

### 网站层

| 问题 | 严重程度 | 数据支撑 |
|------|---------|---------|
| app.js 不可维护 | 严重 | 27行，全部逻辑压缩在一行 |
| 618条全量渲染 | 中强 | 无分页、无虚拟滚动 |
| 搜索无debounce | 中等 | 每次按键全量重渲染 |
| 报告只是裸.md链接 | 中等 | 浏览器直接打开原始markdown |
| 假双语 | 严重 | zh/en完全相同 |
| 移动端体验差 | 低 | 仅padding缩小 |

## 设计方案

### 第一层：信息收集重构

#### Phase 1 - 清源（立即执行）

**决策：砍掉 fallback-web 采集器**

理由：
1. 147条fallback-web中绝大多数是低质量或完全无关内容
2. GitHub + Exa 已覆盖461条有效数据
3. 噪声处理成本远大于补充价值
4. Exa不可用时跳过，等下次重试，不再用垃圾填充

**动作：**
- `collect_web.py` 停止调用，保留代码但标记为 deprecated
- 现有147条fallback-web记录：用关键词过滤清洗，与AI coding agent无关的移入rejected并标记 `cleanup-reason: irrelevant-content`
- `update_tracker.py` 中移除 fallback-web 步骤

**清洗规则：**
- URL域名白名单：github.com, npmjs.com, pypi.org, reddit.com, news.ycombinator.com, 官方博客域名
- 内容关键词校验：summary必须包含至少1个正向关键词（AI coding, agent, MCP, skills, cursor, claude code等）
- 负向关键词一票否决：puppies, dogs, rehoming, 狗, 宠物, chatgpt免费, AI工具箱, 文心一言等

#### Phase 2 - 扩源

**新增来源：**

| 来源 | 采集方式 | source_quality | 预期新增/天 |
|------|---------|---------------|------------|
| Reddit | Reddit API (r/ClaudeAI, r/cursor, r/OpenAI, r/LocalLLaMA等) | community | 5-15条 |
| Hacker News | Algolia HN Search API | community | 3-10条 |
| 博客RSS | feedparser, 预定义博客列表 | verified | 2-8条 |
| 包管理器 | npm registry API, PyPI JSON API | verified | 元数据增强 |

**博客RSS订阅列表（初始，URL在实现时确认）：**
- Anthropic Blog
- OpenAI Blog
- Replit Blog
- Sourcegraph Blog
- Continue.dev Blog
- Cursor Blog
- Zed Blog
- GitHub Blog

> 注：每个博客的 RSS feed URL 在实现阶段确认并写入 `data/blog-feeds.yaml`。

**包管理器元数据增强：**
- 对已有 GitHub 项目，检查是否有对应的 npm/PyPI 包
- 补全 `downloads`、`versions`、`last_publish` 字段
- 不作为独立来源，只增强现有记录

#### Phase 3 - 自适应

**查询生成器：**
- 基于 `seed-tools.yaml` 的 `extension_points` 和 `related_concepts` 自动生成搜索query
- 每个工具生成 5-10 条针对性query
- query模板：`"{tool_name} {extension_point} {intent}"`，intent包括 tutorial, best practices, example, comparison

**查询效果追踪：**
- 每条query记录返回结果数、有效结果数（通过质量门禁的比例）
- 有效率低于20%的query自动降权或淘汰
- 新query需要运行3次后才进入正式轮换

### 第二层：数据分析重构

#### 评分系统重构

**新评分模型（6维度，每项0-5，总计0-30 + 附加调整）：**

| 维度 | 旧逻辑 | 新逻辑 |
|------|--------|--------|
| ecosystem_value | 固定值(MCP/skills=4, 其他=3) | 基于扩展面数量：每支持1种extension_point +1，上限5 |
| activity | GitHub=2, 其他=1 | GitHub：基于`pushed_at`：90天内=5, 180天内=4, 365天内=3, 2年内=2, 更久=1；非GitHub：有明确日期且90天内=4, 365天内=3, 更久=2, 无日期=1 |
| adoption | stars阈值 | stars + downloads综合：stars>=10000或downloads>=10000=5, >=1000=4, >=100=3, >0=2, 0=1 |
| practicality | GitHub=3, 其他=2 | README完整度（>1000字=+1）、有示例代码=+1、有文档链接=+1，上限5 |
| novelty | 固定2 | first_seen在30天内=+2, 90天内=+1；内容独特性（与已有项目TF-IDF相似度<0.3=+2, <0.5=+1） |
| confidence | GitHub=4, Exa=3, fallback=2 | GitHub official repo=5, GitHub community=4, Reddit score>100=3, Exa=3, RSS=4, 其他=1 |

**附加调整保留：**
- source_weight、category_weight、penalty 逻辑不变
- 新增 `relevance_penalty`：内容相关性低于0.5的 -3，低于0.3的 -5

#### 分类系统升级

**两级分类：**
1. 第一级：关键词初筛（现有CATEGORY_RULES）
2. 第二级：校验规则——标为某分类的项目，summary/name中必须包含该分类的核心关键词

**新增字段：**
- `relevance_score`：0-1浮点数，基于正向关键词匹配度 + 负向关键词扣分
- `classification_confidence`：0-1浮点数，关键词匹配强度

#### 去重与去噪

**TF-IDF去重（baseline）：**
- 使用 scikit-learn TfidfVectorizer + cosine_similarity
- 只对比new_records与existing_records，避免O(n²)
- 重复记录标记 `duplicate_of` 字段并降分，不自动删除

**内容相关性过滤：**
- 正向关键词列表（至少匹配1个）：AI coding, coding agent, MCP, model context protocol, skills, hooks, cursor rules, claude code, codex, agentic, codebase, prompt engineering, context engineering
- 负向关键词一票否决：puppies, dogs, rehoming, pets, crypto, airdrop, 免费chatgpt, AI工具箱, 文心一言
- 不满足正向匹配或命中负向关键词的记录，relevance_score设为0，自动reject

#### 双语翻译

**短期（curated 60条）：**
- 调用翻译API（DeepL或Google Translate）对summary做真正翻译
- 缓存翻译结果到 `data/translations-cache/`（按 URL hash 命名）
- 翻译API不可用时回退到原英文

**长期（全部有效记录）：**
- 逐步翻译所有通过质量门禁的记录
- 每日翻译预算限制（如50条/天），避免API费用失控

#### 趋势数据

**新增快照机制：**
- 每次pipeline运行时，在 `data/snapshots/YYYY-MM-DD.json` 中记录：
  - 当日总记录数、分类分布、工具覆盖、平均分、curated/rejected数量
- `build_site.py` 读取历史快照生成趋势数据
- 站点展示：每日新增记录数、分类变化曲线、工具生态增长

### 第三层：网站重构

#### 代码结构

**保持零依赖原则，但拆分模块：**

```
site/
├── index.html          # 入口骨架（扩展结构）
├── styles.css          # 扩展，引入CSS自定义属性
├── js/
│   ├── i18n.js         # 双语配置和切换
│   ├── data.js         # 数据加载和状态管理
│   ├── filters.js      # 筛选和排序逻辑
│   ├── render.js       # 渲染函数（表格、卡片、详情）
│   ├── charts.js       # 原生SVG图表
│   └── app.js          # 入口和事件绑定
├── data/               # 构建生成的JSON数据
└── reports/            # 预生成报告（渲染版）
```

加载方式：多 `<script>` 标签（兼容性最好），或 `<script type="module">`（如果不需要支持老浏览器）。

#### 功能增强

| 功能 | 实现方式 | 优先级 |
|------|---------|--------|
| 分页（每页50条） | 纯JS分页逻辑 + 页码控件 | P0 |
| 搜索debounce | 300ms延迟 + requestAnimationFrame | P0 |
| 项目详情面板 | 点击行展开侧边面板（不跳转） | P1 |
| 报告站内渲染 | 轻量markdown渲染器（自写或marked.js本地版） | P1 |
| 数据可视化 | 原生SVG：分类饼图、工具柱状图、评分直方图 | P2 |
| URL深链接 | `#/project/{id}` hash路由 | P2 |
| 趋势页面 | 基于快照数据的SVG折线图 | P2 |
| 生态地图 | 工具节点 + 共享分类边的SVG图 | P3 |

#### 移动端优化

- 760px以下：表格转卡片布局
- 筛选控件折叠为抽屉式菜单
- 触摸友好交互区域（最小44px高度）

#### 样式重构

引入CSS自定义属性：
```css
:root {
  --color-bg: #0f172a;
  --color-surface: #111827;
  --color-card: #1e293b;
  --color-input: #020617;
  --color-text: #e2e8f0;
  --color-text-secondary: #cbd5e1;
  --color-text-muted: #94a3b8;
  --color-link: #93c5fd;
  --color-border: #334155;
  --color-accent: #2563eb;
  --radius: 12px;
  --spacing: 24px;
}
```

## 实现优先级

| 阶段 | 内容 | 预计工作量 |
|------|------|-----------|
| Phase 1A | 砍掉fallback-web + 清洗现有数据 | 小 |
| Phase 1B | 评分系统重构 + 分类校验 + 相关性过滤 | 中 |
| Phase 1C | 网站代码拆分 + 分页 + debounce | 中 |
| Phase 2A | 新增Reddit/HN/RSS来源 | 中 |
| Phase 2B | TF-IDF去重 + 双语翻译(curated) | 中 |
| Phase 2C | 网站功能增强（详情面板、报告渲染） | 中 |
| Phase 3A | 自适应查询生成器 | 大 |
| Phase 3B | 趋势数据 + 站点可视化 | 中 |
| Phase 3C | 生态地图 + 深链接 | 大 |

## 不做什么（YAGNI）

- 不引入前端框架（React/Vue等），保持零依赖
- 不引入数据库，继续用YAML/JSON + Git
- 不做用户账号/登录系统
- 不做实时数据更新（保持每日批量更新模式）
- 不做embedding/FAISS去重（当前规模TF-IDF足够）
- 不做全量翻译（先翻译curated 60条）

## 依赖关系

```
Phase 1A（清源） ──> Phase 1B（评分重构）──> Phase 1C（网站拆分）
                                              │
Phase 2A（扩源） ──> Phase 2B（去重+翻译）──> Phase 2C（网站增强）
                                              │
Phase 3A（自适应） ─────────────────────> Phase 3B（趋势+可视化）
                                              │
                                         Phase 3C（生态地图）
```

Phase 1A 是所有后续工作的前提——数据不干净，后面做什么都没意义。

# ⛔ 已废弃 — 请使用 `2026-07-14-batch2-frontend-perf-prompt.md`

> 本文档被 2026-07-14 handoff grilling 取代：前端性能现为**新批次2**；删除单体 detail fallback；搜索索引保持轻量四字段。  
> 真相源：`docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`

# 新对话 Agent 启动提示词：批次 3 - 前端性能优化（历史稿）

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是 "Search in Coding" 项目的开发 Agent。你的任务是**优化前端性能**，确保 5165 条数据下首屏加载 < 2s、搜索响应 < 50ms、详情按需加载。

具体改动：
1. `build_site.py`：生成搜索索引 JSON（扁平字符串），projects.json 精简
2. `render.js` / `filters.js`：搜索用预构建索引而非 `JSON.stringify`
3. `build_site.py`：`projects-detail.json` 分片（按 100 条一组），详情按需 fetch
4. 确认 Nginx gzip 对 JSON 启用
5. `data.js`：`loadDetail` 改为按需 fetch 分片

**前置条件**：批次 1（push + deploy）已完成。批次 2（normalize 改进）已完成或并行进行（本批次不依赖批次 2 的数据改动，只改 build_site 和前端 JS）。

---

## 第一步：加载技能框架

1. 优先调用 `skill_view("using-superpowers")`（或项目内等价 skill）。
2. **若加载失败**：不要停工。回退阅读并遵守：
   - 工作区 `HERMES.md`（superpowers-zh 规则）
   - `.hermes/skills/` 下相关 skill（如 `test-driven-development`、`verification-before-completion`）
3. 本任务必须 TDD：`build_site.py` 的改动先写测试。

---

## 第二步：阅读项目上下文

必读：

1. `wiki/README.md` - 总索引与阅读路线
2. `wiki/L1-全景.md` - 当前状态
3. `wiki/L3-代码地图.md` - 前端文件地图、后端文件地图（`build_site.py`）
4. `wiki/L4A-前端详解.md` - 模块详解（`data.js`、`filters.js`、`render.js`）、数据依赖、脚本加载顺序
5. `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md` - **设计文档（本任务的设计依据）**

实现前先核对事实（用工具读代码/数据，不要凭记忆）：

```bash
cd "/root/workspace/search in coding"

# 检查当前 JSON 体积
ls -lh site/data/projects.json site/data/projects-detail.json
wc -c site/data/projects.json site/data/projects-detail.json

# 检查搜索逻辑
grep -n "JSON.stringify" site/js/filters.js

# 检查 detail 加载逻辑
grep -n "loadDetail\|projects-detail" site/js/data.js

# 检查 build_site.py 的 write_json 和 detail 生成
grep -n "write_json\|detail\|slim\|SLIM" scripts/build_site.py
```

---

## 第三步：搜索索引优化

### 3.1 build_site.py 生成搜索索引

在 `build_site.py` 的 `main()` 中新增搜索索引生成：

```python
# 生成搜索索引（扁平字符串，只含搜索所需字段）
search_index = []
for p in projects:
    search_index.append({
        'id': p.get('id'),
        'text': ' '.join(filter(None, [
            p.get('name', ''),
            p.get('summary', ''),
            ' '.join(p.get('resource_type', [])),
            ' '.join(p.get('target_tools', [])),
        ])).lower()
    })
write_json('search-index.json', search_index)
```

### 3.2 data.js 加载搜索索引

在 `data.js` 的 `SIC_data` 对象中新增搜索索引加载：

```javascript
// loadAll 中新增
loadAll: async function(onProgress) {
    // ... 现有加载逻辑 ...
    // 新增：加载搜索索引
    this._searchIndex = await this.fetchJSON('data/search-index.json', onProgress, 'search-index');
    // ...
}
```

### 3.3 filters.js 使用搜索索引

在 `filters.js` 的 `apply()` 中，搜索关键词匹配改为用预构建索引：

```javascript
// 当前（慢）：
// if (q) { hay = JSON.stringify(p).toLowerCase(); if (!hay.includes(q.toLowerCase())) continue; }

// 改为（快）：
if (q) {
    const entry = SIC_data._searchIndex?.find(e => e.id === p.id);
    if (!entry || !entry.text.includes(q.toLowerCase())) continue;
}
```

**优化**：可以进一步用 Map 或 Object 建立 `id -> text` 映射，避免 `find()` 线性查找：

```javascript
// data.js 中构建映射
this._searchMap = {};
for (const e of this._searchIndex) {
    this._searchMap[e.id] = e.text;
}

// filters.js 中使用
if (q) {
    const hay = SIC_data._searchMap[p.id] || '';
    if (!hay.includes(q.toLowerCase())) continue;
}
```

---

## 第四步：projects-detail.json 分片

### 4.1 build_site.py 分片生成

在 `build_site.py` 的 `main()` 中，将单体 `projects-detail.json` 改为分片：

```python
import math

# 分片目录
detail_dir = ROOT / 'site/data/detail'
detail_dir.mkdir(parents=True, exist_ok=True)

# 清理旧分片
for old in detail_dir.glob('*.json'):
    old.unlink()

# 生成详情分片
details = [detail_project(p) for p in projects]
chunk_size = 100
total_chunks = math.ceil(len(details) / chunk_size)

for i in range(total_chunks):
    chunk = details[i * chunk_size : (i + 1) * chunk_size]
    chunk_path = detail_dir / f'{i}.json'
    chunk_path.write_text(json.dumps(chunk, ensure_ascii=False, indent=2), encoding='utf-8')

# 生成索引：project_id -> chunk_index
detail_index = {}
for i, p in enumerate(details):
    pid = p.get('id')
    if pid:
        detail_index[pid] = i // chunk_size
write_json('detail-index.json', detail_index)

# 不再生成单体 projects-detail.json（或保留作为 fallback，体积大但不阻塞）
```

### 4.2 data.js 按需 fetch 分片

修改 `data.js` 的 `loadDetail()`：

```javascript
loadDetail: async function(projectId) {
    // 已缓存
    if (this._detailCache && this._detailCache[projectId]) {
        return this._detailCache[projectId];
    }

    // 获取分片索引
    if (!this._detailIndex) {
        try {
            this._detailIndex = await this.fetchJSON('data/detail-index.json');
        } catch (e) {
            // fallback: 尝试单体 projects-detail.json
            return this._loadDetailLegacy(projectId);
        }
    }

    const chunkIdx = this._detailIndex[projectId];
    if (chunkIdx === undefined) return null;

    // fetch 对应分片
    const chunk = await this.fetchJSON(`data/detail/${chunkIdx}.json`);

    // 缓存整个分片（100 条）
    if (!this._detailCache) this._detailCache = {};
    for (const p of chunk) {
        this._detailCache[p.id] = p;
    }

    return this._detailCache[projectId];
},

// Legacy fallback：从单体 projects-detail.json 加载（兼容旧部署）
_loadDetailLegacy: async function(projectId) {
    if (!this._allDetails) {
        this._allDetails = await this.fetchJSON('data/projects-detail.json');
        this._detailMap = {};
        for (const p of this._allDetails) {
            this._detailMap[p.id] = p;
        }
    }
    return this._detailMap[projectId] || null;
}
```

---

## 第五步：projects.json 精简确认

检查 `SLIM_FIELDS` 列表，确认精简版不含大字段：

```python
SLIM_FIELDS = [
    'id', 'name', 'url', 'source_type', 'resource_type', 'target_tools',
    'summary', 'i18n', 'stars', 'forks', 'total_score', 'quantifiable_score',
    'quality_score', 'tracking_priority', 'last_updated', 'first_seen', 'last_seen',
    'license', 'languages', 'review_state',
]
```

**确认**：不含 `readme_preview`、`topics`、`score_detail`、`quality_detail`、`llm_summary`、`tags`、`maturity`、`status`、`repo`、`last_analyzed`、`benchmark_ref`。

**可选优化**：`write_json` 对大文件改用紧凑格式（`separators=(',', ':')`），减小体积约 30%。但保留 `indent=2` 配合 gzip 也可达到类似效果。

---

## 第六步：确认 Nginx gzip

```bash
# 检查当前 Nginx 配置
grep -r "gzip" /etc/nginx/

# 确认包含以下配置（在 http 块或站点 server 块中）
# gzip on;
# gzip_types application/json text/css application/javascript;
# gzip_min_length 1000;
# gzip_comp_level 6;

# 测试 gzip 是否生效
curl -s -H "Accept-Encoding: gzip" -I https://coding.lzpgood.online/data/projects.json | grep -i "content-encoding"
# 应返回: content-encoding: gzip
```

如果 gzip 未启用，在站点 Nginx 配置中添加：

```nginx
gzip on;
gzip_types application/json text/css application/javascript;
gzip_min_length 1000;
gzip_comp_level 6;
```

然后 `nginx -t && systemctl reload nginx`。

---

## 第七步：测试（TDD）

在 `tests/test_build_site_v2.py` 中新增测试：

```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate

# 1. 测试搜索索引生成
#    - build_site 后 search-index.json 存在
#    - 每条索引含 id 和 text 字段
#    - text 是扁平小写字符串

# 2. 测试详情分片
#    - build_site 后 site/data/detail/ 目录存在
#    - 每个分片文件含 ≤ 100 条项目
#    - detail-index.json 存在且 id -> chunk_index 映射正确
#    - 不再生成单体 projects-detail.json（或保留 fallback）

# 3. 测试精简 JSON 不含大字段
#    - projects.json 中无 readme_preview/topics/score_detail

python3 -m pytest tests/ -v
```

**全绿后**运行 `build_site.py` 验证实际输出。

---

## 第八步：构建并验证

```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate

# 1. 构建站点
python3 scripts/build_site.py

# 2. 检查产物
ls -lh site/data/projects.json site/data/search-index.json
ls site/data/detail/ | head -5
ls site/data/detail/ | wc -l  # 分片数：ceil(5165/100) = 52

# 3. 检查体积
wc -c site/data/projects.json site/data/search-index.json site/data/detail-index.json
du -sh site/data/detail/

# 4. 质量门禁
python3 scripts/quality_gate.py

# 5. 本地预览（可选）
# python3 -m http.server 8080 --directory site
# 访问 http://localhost:8080 测试搜索和详情
```

---

## 验证指标

| 指标 | 改进前 | 目标 |
|------|--------|------|
| projects.json 体积 | ~2-3MB | < 1MB（gzip 后 < 200KB） |
| projects-detail.json 体积 | ~5-10MB 单体 | 分片为 50-100KB/片 |
| 搜索方式 | JSON.stringify 全文匹配 | 预构建索引 includes 匹配 |
| 详情加载 | 全量加载单体 JSON | 按需 fetch 单分片（100 条/片） |
| 首屏加载 | 未知 | < 2s |
| 搜索响应 | 每次按键 ~100ms+ | < 50ms |

---

## 关键约束

1. **零依赖原生 JS** - 不引入任何前端框架或 npm 包
2. **不改数据结构** - `projects.yaml` 字段不变，只改 `build_site.py` 生成的 JSON 格式
3. **TDD for build_site.py** - 先写测试验证搜索索引生成、分片正确性
4. **不 deploy 不 push** - 只本地修改和验证
5. **保留 fallback** - `data.js` 的 `loadDetail` 保留单体 JSON fallback，兼容旧部署
6. **不改脚本加载顺序** - i18n.js -> data.js -> filters.js -> charts.js -> render.js -> app.js
7. **技能加载失败要回退** - 不卡死

---

## 项目环境信息

- 工作目录：`/root/workspace/search in coding`
- Python：3.12.3（`python3`）；测试用 `source .venv/bin/activate && python3 -m pytest tests/ -v`
- 线上站点：https://coding.lzpgood.online/（Nginx）
- 前端架构：零框架、零依赖纯原生 JS SPA，6 个 JS 模块通过多 `<script>` 标签加载
- 当前数据：5165 条
- build_site.py：生成精简 JSON + 详情 JSON + hash 文件名 + sitemap

---

## 最终汇报格式

完成后用中文汇报：

1. 改了哪些文件
2. 测试结果（命令 + 通过数）
3. 搜索索引：是否生成、条数、体积
4. 详情分片：分片数、每片体积、索引文件体积
5. projects.json 体积对比：前 -> 后
6. 搜索逻辑改动说明
7. Nginx gzip 确认结果
8. pipeline 各步结果
9. commit hash
10. 已知限制或遗留问题

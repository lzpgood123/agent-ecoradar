# 新对话 Agent 启动提示词：前端交互优化（表头排序 + 图表修复 + 分页）

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是"Search in Coding"项目的前端开发 Agent。你的任务是实现三个前端交互优化：表头点击排序、工具柱状图标签修复、每页 20 条 + 页码控件。

## 第一步：加载技能框架

立即调用 Skill 工具加载 `using-superpowers` 技能。

## 第二步：阅读项目上下文

必读：
1. `wiki/README.md` - 项目总索引
2. `wiki/L3-代码地图.md` - 代码在哪（重点看前端文件地图）
3. `wiki/L4A-前端详解.md` - 前端模块、事件委托、三区布局、CSS 变量
4. `wiki/L6-经验录.md` - 相关坑

## 第三步：阅读设计文档

1. `docs/superpowers/specs/2026-07-15-frontend-interaction-design.md` - **本次设计规格（核心）**

## 第四步：执行实现

### 只允许改的文件

| 文件 | 改动 |
|------|------|
| `site/index.html` | `<th>` 加 data-sort + sortable class；底部加 pagination 容器 |
| `site/js/filters.js` | 新增 sortDirection + toggleSort()；URL 增加 dir 和 page 参数 |
| `site/js/render.js` | PAGE_SIZE 改 20；renderSortIndicators()；renderPage()；renderPagination()；去掉 IntersectionObserver |
| `site/js/app.js` | 表头点击事件委托；页码点击事件委托 |
| `site/js/charts.js` | barChart() 改为水平布局 |
| `site/js/i18n.js` | 新增 pageOf 翻译 |
| `site/styles.css` | .sortable 样式；pagination 样式 |

### 不允许改的文件

- `site/js/data.js` - 不动
- `scripts/*` - 不动
- `data/*` - 不动

### 任务 1：表头点击排序

**index.html 改动：**
```html
<thead>
  <tr>
    <th class="sortable" data-sort="name" data-i18n="thName">名称</th>
    <th data-i18n="thType">类型</th>
    <th data-i18n="thTools">工具</th>
    <th class="sortable" data-sort="score" data-i18n="thScore">分数</th>
    <th class="sortable" data-sort="stars" data-i18n="thStars">Stars</th>
    <th data-i18n="thLink">链接</th>
  </tr>
</thead>
```

**filters.js 新增：**
```javascript
sortDirection: 'desc',  // 'asc' or 'desc'

toggleSort(field) {
  if (this.sortBy === field) {
    this.sortDirection = this.sortDirection === 'desc' ? 'asc' : 'desc';
  } else {
    this.sortBy = field;
    this.sortDirection = 'desc';
  }
},

// 在 apply() 的 rows.sort() 后，如果 sortDirection === 'asc'，reverse 结果
// 具体实现：在 switch case 的返回值中，asc 时取反
```

排序逻辑修改（在 apply() 中）：
```javascript
rows.sort((a, b) => {
  let cmp;
  switch (this.sortBy) {
    case 'name': cmp = SIC_i18n.textOf(a, 'name').localeCompare(SIC_i18n.textOf(b, 'name')); break;
    case 'stars': cmp = (b.stars || 0) - (a.stars || 0); break;
    // ... 其他 case
    default: cmp = (b.total_score || 0) - (a.total_score || 0);
  }
  return this.sortDirection === 'asc' ? -cmp : cmp;
});
```

**render.js 新增 renderSortIndicators()：**
```javascript
renderSortIndicators: function() {
  var ths = document.querySelectorAll('th[data-sort]');
  for (var i = 0; i < ths.length; i++) {
    var th = ths[i];
    var field = th.dataset.sort;
    var arrow = '';
    if (field === SIC_filters.sortBy) {
      arrow = SIC_filters.sortDirection === 'asc' ? ' ▲' : ' ▼';
    }
    // 只追加箭头到翻译文本后面，不覆盖 data-i18n
    var baseText = SIC_i18n.t(th.dataset.i18n);
    th.textContent = baseText + arrow;
  }
},
```

**app.js 事件委托：**
```javascript
// 表头点击排序
document.querySelector('thead').addEventListener('click', function(e) {
  var th = e.target.closest('th[data-sort]');
  if (!th) return;
  SIC_filters.toggleSort(th.dataset.sort);
  // 同步 select
  var sortEl = $('sort');
  if (sortEl) sortEl.value = SIC_filters.sortBy;
  SIC_render.renderSearchZone();
  SIC_render.renderSortIndicators();
  SIC_filters.writeState();
});
```

### 任务 2：工具柱状图改为水平布局

**charts.js 的 barChart() 重写为水平柱状图：**

```javascript
barChart(data, maxVal, options) {
  options = options || {};
  data = data || [];
  if (!data.length) return '<svg viewBox="0 0 320 60" style="width:100%;height:60px;"></svg>';

  var padL = 120;  // 左侧标签区域
  var padR = 40;   // 右侧数值区域
  var padT = 8;
  var padB = 24;
  var rowH = 28;   // 每行高度
  var barH = 16;   // 柱子高度

  var n = data.length;
  var chartW = 400; // 柱子区域宽度
  var width = padL + chartW + padR;
  var height = padT + n * rowH + padB;

  var values = data.map(function(d) { return Number(d.value) || 0; });
  var niceMax = this._niceMax(maxVal || Math.max.apply(Math, values.concat([1])));

  // Y 轴标签 + 柱子
  var rows = data.map(function(d, i) {
    var val = Math.max(0, Number(d.value) || 0);
    var barW = (val / niceMax) * chartW;
    var y = padT + i * rowH + (rowH - barH) / 2;
    var label = String(d.label || '');
    // 截断到 16 字符
    if (label.length > 16) label = label.slice(0, 15) + '…';

    return '<text x="' + (padL - 8) + '" y="' + (y + barH / 2 + 4) + '" text-anchor="end" font-size="11" fill="var(--color-text-secondary)">' + label + '</text>' +
      '<rect x="' + padL + '" y="' + y + '" width="' + barW + '" height="' + barH + '" fill="var(--color-accent)" rx="3"/>' +
      '<text x="' + (padL + barW + 6) + '" y="' + (y + barH / 2 + 4) + '" text-anchor="start" font-size="11" font-weight="600" fill="var(--color-text-secondary)">' + val + '</text>';
  }).join('');

  // X 轴刻度
  var tickCount = 4;
  var ticks = '';
  for (var t = 0; t <= tickCount; t++) {
    var v = Math.round((niceMax * t) / tickCount);
    var x = padL + (chartW * t / tickCount);
    ticks += '<line x1="' + x + '" y1="' + padT + '" x2="' + x + '" y2="' + (padT + n * rowH) + '" stroke="rgba(255,248,240,0.06)" stroke-width="1"/>' +
      '<text x="' + x + '" y="' + (height - 6) + '" text-anchor="middle" font-size="9" fill="var(--color-text-muted)">' + v + '</text>';
  }

  return '<svg viewBox="0 0 ' + width + ' ' + height + '" style="width:100%;height:auto;" role="img" aria-label="' + (options.ariaLabel || 'chart') + '">' + ticks + rows + '</svg>';
},
```

### 任务 3：每页 20 条 + 页码

**render.js 改动：**

```javascript
PAGE_SIZE: 20,
currentPage: 0,

// renderSearchZone 中重置 currentPage
renderSearchZone: function() {
  // ... 现有筛选逻辑 ...
  this.currentPage = 0;
  // ... 去掉 observer 代码 ...
  this.renderPage();
  this.renderPagination();
},

// 替换 renderMore 为 renderPage
renderPage: function() {
  var self = this;
  var start = this.currentPage * this.PAGE_SIZE;
  var end = Math.min(start + this.PAGE_SIZE, this.currentFiltered.length);
  var curatedIds = SIC_data.curatedIds();
  // ... 与现有 renderMore 相同的表格行生成逻辑 ...
  this.$('rows').innerHTML = html;  // 替换而非追加
},

renderPagination: function() {
  var self = this;
  var total = this.currentFiltered.length;
  var pages = Math.ceil(total / this.PAGE_SIZE);
  var current = this.currentPage + 1;  // 1-indexed for display
  var container = this.$('pagination');
  if (!container) return;

  if (pages <= 1) {
    container.innerHTML = '';
    return;
  }

  var html = '';
  // 上一页
  if (current > 1) {
    html += '<button class="page-btn" data-action="page" data-page="' + (current - 1) + '">‹</button>';
  }
  // 页码（带省略号）
  var startPage = Math.max(1, current - 2);
  var endPage = Math.min(pages, current + 2);
  if (startPage > 1) {
    html += '<button class="page-btn" data-action="page" data-page="1">1</button>';
    if (startPage > 2) html += '<span class="page-ellipsis">…</span>';
  }
  for (var p = startPage; p <= endPage; p++) {
    html += '<button class="page-btn' + (p === current ? ' active' : '') + '" data-action="page" data-page="' + p + '">' + p + '</button>';
  }
  if (endPage < pages) {
    if (endPage < pages - 1) html += '<span class="page-ellipsis">…</span>';
    html += '<button class="page-btn" data-action="page" data-page="' + pages + '">' + pages + '</button>';
  }
  // 下一页
  if (current < pages) {
    html += '<button class="page-btn" data-action="page" data-page="' + (current + 1) + '">›</button>';
  }
  // 页码信息
  html += '<span class="page-info">' + SIC_i18n.t('pageOf').replace('{cur}', current).replace('{total}', pages) + '</span>';

  container.innerHTML = html;
},
```

**app.js 页码点击：**
```javascript
// 在 handleGlobalClick 中添加 case 'page':
case 'page':
  var page = parseInt(btn.dataset.page, 10);
  SIC_render.currentPage = page - 1;  // 0-indexed
  SIC_render.renderPage();
  SIC_render.renderPagination();
  // 滚动到表格顶部
  var tableWrapper = document.querySelector('.table-wrapper');
  if (tableWrapper) tableWrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
  SIC_filters.writeState();
  break;
```

**filters.js URL state 增加 page：**
```javascript
// readState
if (qs.get('page')) this._pendingPage = parseInt(qs.get('page'), 10);

// writeState
if (SIC_render.currentPage > 0) qs.set('page', String(SIC_render.currentPage + 1));
```

**index.html 底部加容器：**
```html
<!-- 在 table-wrapper 后面 -->
<div id="pagination" class="pagination"></div>
```

**styles.css 新增：**
```css
/* Sortable headers */
.sortable { cursor: pointer; user-select: none; }
.sortable:hover { color: var(--color-accent-light); }

/* Pagination */
.pagination { display: flex; gap: 4px; justify-content: center; align-items: center; margin-top: 16px; flex-wrap: wrap; }
.page-btn { cursor: pointer; border: 1px solid var(--color-border); background: var(--color-card); color: var(--color-text-secondary); border-radius: var(--radius-xs); padding: 4px 12px; font-size: 13px; min-width: 32px; transition: all 0.15s; }
.page-btn:hover { border-color: var(--color-accent); color: var(--color-text); }
.page-btn.active { background: var(--color-accent); color: white; border-color: var(--color-accent); }
.page-ellipsis { color: var(--color-text-muted); padding: 0 4px; }
.page-info { color: var(--color-text-muted); font-size: 13px; margin-left: 8px; }
```

**i18n.js 新增：**
```javascript
// zh
pageOf: '第 {cur} 页 / 共 {total} 页',
// en
pageOf: 'Page {cur} of {total}',
```

### 改完后

```bash
cd "/root/workspace/search in coding"
python3 scripts/build_site.py
# 验证
python3 -c "import json; d=json.load(open('site/data/metrics.json')); print(f'Projects: {d[\"projects\"]}')"
```

## 第五步：验证

- [ ] 点击表头"名称" -> 按名称排序，显示 ▼
- [ ] 再点一次"名称" -> 切换为升序，显示 ▲
- [ ] 点击表头"分数" -> 切换为分数排序
- [ ] 点击表头"Stars" -> 切换为 Stars 排序
- [ ] `<select>` 排序与表头同步
- [ ] 工具覆盖分布图标签不重叠，完整显示工具名
- [ ] 每页显示 20 条
- [ ] 底部有页码控件
- [ ] 点击页码跳转
- [ ] 上一页/下一页正常
- [ ] 翻页后滚动到表格顶部
- [ ] URL 包含 page 参数
- [ ] 分数分布直方图仍正常（垂直）
- [ ] 筛选/收藏/详情等其他功能不受影响
- [ ] build_site.py 成功
- [ ] 无 JS 控制台错误

## 第六步：Commit + Deploy

```bash
git add site/
git commit -m "feat: table header sort + horizontal bar chart + pagination 20/page"
git push origin main
python3 scripts/deploy_site.py --dest /var/www/coding.lzpgood.online
```

## 关键约束

1. **只改前端**：不动 data/、scripts/、后端逻辑
2. **不改 data.js**：搜索索引和 detail 分片逻辑不动
3. **不引入图表库**：charts.js 仍用原生 SVG
4. **histogram 不变**：只有 barChart 改为水平
5. **去掉 IntersectionObserver**：改为分页模式
6. **URL 兼容**：增加 dir 和 page 参数，不影响现有参数

## 项目环境信息

- 工作目录：`/root/workspace/search in coding`
- Python：3.12.3（用 python3）
- 测试：`source .venv/bin/activate && python3 -m pytest tests/ -v`
- 站点：https://coding.lzpgood.online/
- 当前数据：5165 条项目
- 当前前端：Style B Warm paper dark，6 个 JS 模块

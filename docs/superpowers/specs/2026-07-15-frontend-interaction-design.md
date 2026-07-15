# 前端交互优化设计：表头排序 + 图表修复 + 分页

> 日期：2026-07-15
> 状态：用户已确认
> 作者：方案设计 Agent

## 背景

Style B 上线后，用户发现三个交互问题：表头不可排序、工具覆盖分布图标签重叠、无页码控件。

## 问题清单

| # | 问题 | 根因 |
|---|------|------|
| 1 | 表头不可点击排序 | `<th>` 无 data-sort 属性，排序只能用 `<select>` |
| 2 | 工具柱状图标签重叠 | 垂直柱状图 10 个工具标签挤在底部，8 字符截断仍重叠 |
| 3 | 无页码控件 | PAGE_SIZE=50 + IntersectionObserver 无限滚动，无页码 |

## 设计方案

### 1. 表头点击排序

**改动：**
- `<th>` 加 `data-sort` 属性（name/score/stars）和 `class="sortable"`
- 点击表头切换排序，再点切换升降序
- 表头显示 ▲/▼ 箭头
- 与现有 `<select>` 双向同步
- URL `sort` 参数同步

**文件：** index.html, app.js, filters.js, render.js, styles.css

**filters.js 新增：**
- `sortDirection: 'desc'` 字段
- `toggleSort(field)` 方法：点击已选中列切换方向，点击新列默认降序
- URL 增加 `dir` 参数（asc/desc）

**render.js 新增：**
- `renderSortIndicators()` 方法：在表头显示箭头
- 排序时考虑 sortDirection（升序用 reverse）

### 2. 工具柱状图改为水平布局

**改动：** `barChart()` 改为水平柱状图
- 标签放左侧（右对齐，完整显示工具名）
- 柱子从左往右延伸
- 数值标签在柱子末端
- 每行 28px，10 行 = 280px 高度
- 宽度 100% 响应式
- X 轴刻度（0, max/2, max）

**文件：** charts.js（只改 barChart，histogram 不变）

### 3. 每页 20 条 + 页码

**改动：**
- `PAGE_SIZE` 从 50 改为 20
- 去掉 IntersectionObserver 无限滚动
- 底部添加页码控件：`上一页 | 1 2 3 ... 10 | 下一页` + `第 X 页 / 共 Y 页`
- 点击页码跳转，URL 增加 `page` 参数
- 翻页后滚动到表格顶部

**文件：** render.js, filters.js, app.js, index.html, styles.css, i18n.js

**render.js 改动：**
- 新增 `currentPage: 0`
- `renderSearchZone()` 重置 currentPage=0
- `renderMore()` 改为 `renderPage(page)`：切片 `(page-1)*20` 到 `page*20`
- 新增 `renderPagination()`：渲染页码控件
- 去掉 IntersectionObserver 相关代码

**页码控件逻辑：**
- 当前页高亮
- 超过 7 页显示省略号
- 上一页/下一页在首尾页禁用
- 翻页不重新筛选，只切片

## 不做什么

- 不改数据结构
- 不改后端脚本
- 不改筛选/收藏/详情等现有功能
- 不引入图表库
- histogram 保持垂直

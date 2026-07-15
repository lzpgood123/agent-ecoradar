# 新对话 Agent 启动提示词：批次 2 — 前端性能优化

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是 "Search in Coding" 项目的开发 Agent。你的任务是：**优化前端性能（搜索索引 + 详情分片 + gzip 确认）**，使 5165 条数据可承载。

**前置**：批次 1 独立评估 PASS（代码已 push，站点未 deploy）。

设计真相源：`docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`（批次 2 章节 + 附录 C/D）。

完成后：评估 PASS → **push 代码** → **不 deploy** → 等待批次 3。

---

## 第一步：加载技能框架

1. `skill_view("using-superpowers")`（失败则读 `HERMES.md` / `.hermes/skills/`）
2. 必须 TDD：`test-driven-development` / `verification-before-completion`
3. 完成前 `wiki-checkpoint`

---

## 第二步：阅读项目上下文

必读：

1. `wiki/README.md`
2. `wiki/L1-全景.md`
3. `wiki/L3-代码地图.md`（`build_site.py`、前端 JS）
4. `wiki/L4A-前端详解.md`
5. `wiki/L5-接口契约.md`（站点数据文件约定）
6. `wiki/L6-经验录.md`
7. `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md` — **核心**

实现前用工具核对：

- 当前 `site/data/projects.json` / `projects-detail.json` 体积
- `filters.js` 是否仍 `JSON.stringify` 搜索
- `data.js` 的 `loadDetail` 实现
- `build_site.py` 的 `SLIM_FIELDS` / `write_json` / detail 生成

---

## 第三步：实现计划

实现计划可直接按 spec 批次 2 执行。若需拆任务，写入 `docs/superpowers/plans/` 后再做。

优先顺序：

1. 测试（搜索索引生成、分片正确、slim 不含大字段）
2. `build_site.py` 改动
3. `data.js` / `filters.js`（及 hashed 构建一致性）
4. Nginx gzip 确认
5. 本地 `build_site` + quality_gate + 手工抽检

---

## 第四步：执行实现

严格按 spec 批次 2 + 附录 C/D：

- 搜索索引字段：**仅** name + summary + resource_type + target_tools
- 详情：**100 条/片** + `detail-index.json`
- **删除**单体 `projects-detail.json`（构建与部署产物都不要保留）
- 搜索禁止 `JSON.stringify(project)` 全文匹配
- `loadDetail` **无**单体 fallback
- 零依赖原生 JS

---

## 第五步：验证

调用验证技能，至少确认：

- pytest 全绿
- `search-index.json` 存在且条数正确
- `site/data/detail/` 分片数 ≈ ceil(N/100)
- 无 `projects-detail.json`
- gzip 对 JSON 生效（curl Accept-Encoding 检查）
- 本地预览：搜索与详情可用

---

## 第六步：Git

评估前可先本地 commit。评估 PASS 后：

- **push** 代码
- **禁止 deploy**

---

## 第七步：更新 Wiki

至少更新：

- `wiki/L3-代码地图.md`（新数据文件：search-index / detail 分片）
- `wiki/L4A-前端详解.md`（搜索与 loadDetail）
- `wiki/L5-接口契约.md`（站点 JSON 契约）
- `wiki/L6-经验录.md`（若踩新坑）
- `wiki/L1-全景.md`（状态：前端性能已改、未 deploy）

---

## 关键约束

1. 零依赖原生 JS
2. 不改 `projects.yaml` schema
3. 不 deploy
4. 评估 PASS 前不要宣称完成
5. 技能加载失败要回退

## 不能改动的部分

- 评分公式 / LLM prompt
- 采集源策略（仅 GitHub）
- 前端框架选型
- 线上 webroot（本批不部署）

## 项目环境

- 工作目录：`/root/workspace/search in coding`
- Python：3.12 + `.venv`
- 测试：`source .venv/bin/activate && python3 -m pytest tests/ -v`
- 站点（本批不发布）：https://coding.lzpgood.online/

## 最终汇报格式（中文）

1. 改了哪些文件
2. 测试结果
3. 搜索索引 / 分片 / 体积证据
4. gzip 检查结果
5. push commit hash
6. 明确：**未 deploy**
7. 遗留问题

## 评估验收清单（给评估 Agent）

- [ ] 存在 `search-index.json`，字段符合轻量约定
- [ ] 搜索代码无 `JSON.stringify` 全文匹配
- [ ] detail 分片 + index 正确；**无**单体 `projects-detail.json`
- [ ] pytest / quality_gate 通过
- [ ] gzip 确认有证据
- [ ] 已 push、未 deploy
- [ ] wiki 已更新

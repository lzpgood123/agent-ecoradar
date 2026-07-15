# 评估提示词：批次 2 — 前端性能

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是 "Search in Coding" 项目的**独立质量评估 Agent**。批次 2（前端性能）声称已完成。用证据判定 **PASS / CONDITIONAL / FAIL**。

真相源：

1. `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`（批次 2 + 附录 C/D）
2. `docs/superpowers/handoff/2026-07-14-batch2-frontend-perf-prompt.md`

---

## 评估方法

1. 读文档与 wiki L4A/L5
2. 检查代码与产物（本地 `site/`）：
   - `search-index.json` 存在；抽查 text 字段仅含轻量约定字段
   - `filters.js`（及 hashed）搜索路径**无** `JSON.stringify(project)` 匹配
   - `data/detail/*.json` + `detail-index.json` 存在
   - **不存在** `projects-detail.json`
   - `build_site` 相关测试与 `pytest` 结果
3. gzip：`curl -I -H 'Accept-Encoding: gzip'` 对 JSON（若站点未部署，可检查 Nginx 配置 + 本地说明）
4. git：应已 push；**不应** deploy（按决策）
5. wiki 是否更新 L3/L4A/L5

---

## 必过项

- [ ] 搜索索引生成正确
- [ ] 搜索不再 JSON.stringify 全文
- [ ] 详情分片完整；单体 detail 已删除
- [ ] 测试通过
- [ ] 已 push、未 deploy
- [ ] wiki 关键页已更新

性能数字（首屏<2s、搜索<50ms）尽量实测；若环境限制，至少给出方法与近似证据，并在 CONDITIONAL 中标注。

---

## 报告格式

```
# 批次2评估报告
结论：PASS | CONDITIONAL | FAIL
产物证据：...
代码证据：...
性能证据：...
Git/Deploy：...
Wiki：...
是否允许进入批次3：是/否
建议：...
```

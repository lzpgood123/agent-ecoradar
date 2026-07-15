# 新对话 Agent 启动提示词：批次 3 — 数据补全 + normalize + 第一次 deploy

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是 "Search in Coding" 项目的开发 Agent。你的任务是：

1. 批量补全 `readme_preview`（目标 ≥60%）
2. 改进 `normalize.py`（topics + 关键词；**禁止** AI→cli-tool 兜底）
3. 重跑管道并达到硬指标（tutorial ≤30%，general-ai-coding ≤45%）
4. 适配空 `target_tools`
5. 评估 PASS 后 **push + 第一次 deploy**

**前置**：批次 2 独立评估 PASS（前端性能代码已 push，站点可能仍未 deploy）。

设计真相源：`docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`（批次 3 + 附录 A/B + 决策表）。

**批次 4 硬门禁也在本批验收**：readme≥60% **且** tutorial≤30%，否则本批 FAIL。

---

## 第一步：加载技能框架

1. `skill_view("using-superpowers")`（失败则读 `HERMES.md` / `.hermes/skills/`）
2. 必须 TDD + verification
3. 完成前 wiki-checkpoint

---

## 第二步：阅读项目上下文

必读：

1. `wiki/README.md`
2. `wiki/L1-全景.md`
3. `wiki/L3-代码地图.md`（normalize / enrich / score / finalize）
4. `wiki/L4B-后端详解.md`
5. `wiki/L5-接口契约.md`
6. `wiki/L6-经验录.md`（#16 readme 获取、#19 误标、#22 填充率、安全 merge）
7. `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md` — **核心**

实现前用工具核对当前分布：total / no_readme / tutorial / general / topics / LLM 字段样本。

---

## 第三步：执行前准备（防踩踏）

1. **暂停** daily collect cron：`2a0c271a031f`（pause）
2. 确认暂停成功后再跑长时间 enrich/normalize
3. 本批结束（无论成败）都要 **恢复** 该 cron，除非评估要求继续暂停

---

## 第四步：实现与管道

严格按 spec 批次 3：

### 4.1 TDD 先写测试

覆盖至少：

- topics → resource_type 映射
- 关键词扩展
- **无匹配仍 tutorial**（有 AI topics 也**不是** cli-tool）
- topics → target_tools
- 无匹配可返回 `[]`
- 安全 merge 不丢 LLM 字段
- official-seed 保护

全绿后再改实现 / 跑管道。

### 4.2 enrich → normalize → score → finalize → reports → build → quality_gate → pytest

细节见 spec；关键边界：

- README 获取用 `gh api .../readme` + base64
- normalize **不读** readme_preview
- 安全 merge 保留 LLM 字段
- 空 `target_tools`：前端/统计/quality_gate 同步适配

### 4.3 硬指标

| 指标 | 目标 |
|------|------|
| readme_preview | ≥ 60% |
| tutorial | ≤ 30%（硬） |
| general-ai-coding | ≤ 45% |
| empty target_tools | 允许 |
| LLM 字段抽查 | 未损坏 |

达不到 tutorial/readme 硬门槛 → 继续改规则/关键词并重跑，**不得**放行批次 4。

---

## 第五步：第一次 deploy（仅指标达标且自检通过后）

1. commit 变更（注意签名）
2. push
3. `python3 scripts/deploy_site.py --dest /var/www/coding.lzpgood.online`
4. 验证线上：条数、搜索（索引）、详情分片、报告、metrics

然后恢复 daily collect cron。

---

## 第六步：更新 Wiki

至少：

- L1 状态（5165 上线、填充率/分类新分布）
- L3 / L4B（normalize 签名与逻辑）
- L5（若字段/契约变化）
- L6 新坑即时记

---

## 关键约束

1. 禁止 AI topics → cli-tool 兜底
2. normalize 不读 README
3. 安全 merge LLM 字段
4. 执行窗口暂停 collect cron，结束后恢复
5. 不改评分公式 / LLM prompt
6. 硬指标不达标不算完成

## 不能改动的部分

- 采集源仅 GitHub
- 100 分制评分公式
- `llm_prompts.py`
- 前端零依赖架构（可适配空 target_tools 展示）

## 项目环境

- 工作目录：`/root/workspace/search in coding`
- `.venv` + pytest
- `gh` 已认证
- webroot：`/var/www/coding.lzpgood.online`
- daily collect job：`2a0c271a031f` → `search-in-coding-daily.sh`

## 最终汇报格式（中文）

1. 改动文件列表
2. 测试结果
3. 指标前→后（readme / tutorial / general / empty tools）
4. resource_type 分布
5. LLM 字段安全 merge 证据
6. cron pause/resume 证据
7. push + deploy 证据
8. 线上验证
9. 是否满足批次 4 硬门禁
10. 遗留问题

## 评估验收清单（给评估 Agent）

- [ ] readme_preview ≥ 60%
- [ ] tutorial ≤ 30%
- [ ] general-ai-coding ≤ 45%
- [ ] 无 cli-tool 错误兜底逻辑
- [ ] 允许空 target_tools 且站点可展示
- [ ] LLM 字段未冲掉
- [ ] pytest / quality_gate PASS
- [ ] 已 push + 第一次 deploy 成功
- [ ] daily collect cron 已恢复
- [ ] wiki 已更新

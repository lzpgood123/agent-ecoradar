# 评估提示词：批次 4 — LLM 策略 + backlog

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是 "Search in Coding" 项目的**独立质量评估 Agent**。批次 4 声称已完成。用证据判定 **PASS / CONDITIONAL / FAIL**。

真相源：

1. `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`（批次 4）
2. `docs/superpowers/handoff/2026-07-14-batch4-llm-strategy-prompt.md`

---

## 评估方法

### 0. 前置门禁（历史）

确认批次 3 评估为 PASS 后才开始的（报告/时间线）。若在门禁失败时仍大规模分析 → FAIL。

### 1. 代码/配置

- 并发 10（配置 + 调用链）
- stars 降序（测试或 dry-run 证据）
- KeyRotator 线程安全（如有改动）
- **未改** `llm_prompts.py` 模板与评分公式（diff 抽查）

### 2. Cron / 脚本命名（高危）

- `~/.hermes/scripts/search-in-coding-daily.sh` 仍是**采集**（update_tracker），**未被**改成 LLM 增量
- 存在独立 `search-in-coding-llm-daily.sh` + 对应 cron job
- weekly LLM 仍在
- `cron.script_timeout_seconds` 实际生效为 3600（或能证明不再 120s 杀进程）

### 3. Backlog 与 deploy

- pending / analyzed 前后对比（显著下降）
- 多轮执行记录
- **每轮** score+build+deploy 证据（或等价证明线上逐步更新）
- 高星项目优先被分析的证据

### 4. Wiki

L1/L4B/L6 是否更新

---

## 必过项

- [ ] 未覆盖 daily collect 脚本
- [ ] 新 LLM daily 脚本/job 存在
- [ ] timeout 修复有证据
- [ ] 并发 10 + stars 排序
- [ ] pending 明显下降 / 多轮推进
- [ ] 有多轮 deploy 证据
- [ ] prompt/评分未改
- [ ] 前置门禁遵守

---

## 报告格式

```
# 批次4评估报告
结论：PASS | CONDITIONAL | FAIL
前置门禁：...
代码/配置：...
Cron/脚本：...
Backlog 进度：...
Deploy 节奏：...
风险与建议：...
```

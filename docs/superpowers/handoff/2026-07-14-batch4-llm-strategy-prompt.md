# 新对话 Agent 启动提示词：批次 4 — LLM 策略 + 清空 backlog

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是 "Search in Coding" 项目的开发 Agent。你的任务是：

1. 提高 LLM 分析并发到 10，并按 stars 降序优先
2. 修正/配置 cron：timeout 3600 + **新建** LLM 日增量 job（不覆盖采集脚本）
3. 多轮半自动分析尽快清空 ~5120 pending
4. **每轮** score + build + deploy

**前置硬门禁（批次 3 评估必须 PASS）**：

- `readme_preview ≥ 60%`
- `tutorial ≤ 30%`

任一不满足 → **停止**，回报阻塞，不要开始分析。

设计真相源：`docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`（批次 4 + 决策 7/8/15/16/17）。

---

## 第一步：加载技能框架

1. `skill_view("using-superpowers")`（失败则回退 `HERMES.md`）
2. TDD for 排序/并发/配置读取/线程安全
3. verification + wiki-checkpoint

---

## 第二步：阅读项目上下文

必读：

1. `wiki/README.md`
2. `wiki/L1-全景.md`
3. `wiki/L3-代码地图.md`（weekly_analysis / llm_api）
4. `wiki/L4B-后端详解.md`（LLM / cron）
5. `wiki/L6-经验录.md`（cron timeout 坑）
6. `docs/evaluation-batch3-llm-analysis-2026-07-14.md`（历史问题）
7. `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md` — **核心**

实现前核对：

- 当前 pending / analyzed 数量
- `weekly_analysis.py` / `llm_api.py` 并发与排序
- `config/llm-analysis.yaml`
- `hermes cron list`
- 现有脚本：
  - `~/.hermes/scripts/search-in-coding-daily.sh` = **采集**（勿覆盖）
  - `~/.hermes/scripts/search-in-coding-weekly.sh` = 周一 LLM
- 现网曾出现 daily collect **120s timeout**

---

## 第三步：代码与配置（TDD）

按 spec 批次 4.1：

- workers/batch_size → 10（配置驱动优先）
- `get_projects_to_analyze` stars 降序
- KeyRotator 线程安全确认/修补
- **不改** prompt 模板与评分公式
- 安全 merge / official-seed 保护保持

pytest 全绿后 dry-run 确认高星优先。

---

## 第四步：Cron 与超时

按 spec 4.2：

1. `hermes config set cron.script_timeout_seconds 3600`
2. 验证 timeout 生效（不要只改文档）
3. **新建** `search-in-coding-llm-daily.sh` + 新 cron（Tue–Sat 03:30，200 条，skip-benchmarks + deploy）
4. **禁止**覆盖 `search-in-coding-daily.sh`（采集）
5. 保留 weekly LLM job

---

## 第五步：多轮清空 backlog

按 spec 4.3：

- 多轮（如 4–5 × 1000，或等价）
- **每轮后** score + build + **deploy**
- 续跑依赖 checkpoint / last_analyzed cutoff
- 小批量先冒烟（如 10 条）再放大

---

## 第六步：更新 Wiki

至少：

- L1（分析进度、cron 新 job）
- L4B（并发 10、日增量 LLM cron）
- L6（timeout 修复、脚本命名防覆盖）

---

## 关键约束

1. 批次 3 硬门禁不满足则不开始
2. 不覆盖 daily collect 脚本
3. 不改 prompt / 评分公式
4. 每轮都 deploy
5. timeout 必须验证到 3600 生效

## 不能改动的部分

- `llm_prompts.py` 模板内容
- `score.py` 公式
- 采集 daily 脚本职责
- 前端架构（除非展示 bug 阻塞验证）

## 项目环境

- 工作目录：`/root/workspace/search in coding`
- SenseNova / DeepSeek-V4-Flash 凭证池
- cron jobs 现状以 `hermes cron list` 为准
- 站点：https://coding.lzpgood.online/

## 最终汇报格式（中文）

1. 前置门禁核对证据
2. 代码/配置改动
3. 测试结果
4. timeout 修复证据
5. 新 LLM daily job id / 脚本路径
6. 多轮分析：每轮条数、累计 analyzed、deploy 结果
7. pending 前后对比
8. dry-run / 高星优先证据
9. commit hashes
10. 遗留问题

## 评估验收清单（给评估 Agent）

- [ ] 前置门禁成立时才执行
- [ ] 并发 10 + stars 降序有代码/测试证据
- [ ] `search-in-coding-daily.sh` 采集脚本未被覆盖
- [ ] 存在独立 `search-in-coding-llm-daily.sh` + cron
- [ ] script_timeout 实际为 3600（或等效生效）
- [ ] 多轮分析推进 pending 显著下降
- [ ] 每轮有 deploy 证据
- [ ] prompt/评分公式未改
- [ ] wiki 已更新

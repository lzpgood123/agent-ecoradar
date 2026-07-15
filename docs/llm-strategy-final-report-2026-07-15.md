# Search in Coding — LLM 策略优化完结汇报

> 日期：2026-07-15  
> 结论：**COMPLETE**  
> 站点：https://coding.lzpgood.online/  
> 终态 commit：`dcb9135`（已 push `main`）  
> 收口证据：`docs/llm-strategy-closeout-2026-07-15.md`

---

## 一、一句话结论

从「5165 条 bulk 入库后，99% 未 LLM 分析、周任务 3 并发跑不完」出发，完成了 **LLM 分析策略改造 + 吞吐提升 + 自动化稳态 + active backlog 清零**。  
**策略工程与可分析 backlog 均已收口；用户无需再操作。**

---

## 二、问题从哪里来（起点）

### 2.1 数据爆发

| 时间线 | 状态 |
|--------|------|
| bulk 前 | 约 293 条量级（日常追踪） |
| bulk 后（`8571786` 等） | **5165** 条（github 5155 + official-seed 10） |
| 直接后果 | 旧 LLM 节奏与并发完全不够用 |

### 2.2 当时 LLM 侧的核心矛盾

| 问题 | 起点表现 | 影响 |
|------|----------|------|
| 未分析占比极高 | 约 **99%** pending / 未 `last_analyzed` | 质量分 40 分位长期空白 |
| 并发过低 | `batch_size` / workers **3** | 全量需数小时，超默认 cron |
| 无优先级 | 分析顺序近乎随机/列表序 | 高星项目不优先 |
| cron 超时 | 曾出现 **120s** 杀进程 | 长任务必挂 |
| 吞吐模型 | 仅周一全量 | 无法消化数千 backlog |
| 脚本命名风险 | 日采集脚本名 `search-in-coding-daily.sh` | 若误覆盖会毁掉采集 |

### 2.3 与「整包 post-bulk」的关系（便于对照）

LLM 策略是 post-bulk 四批中的 **Batch4**，前置批次解决了「能上线、能搜、有 README、分类不崩」：

| 批次 | 主题 | 代表 commit | 对 LLM 的意义 |
|------|------|-------------|---------------|
| 1 | 只 push 不先 deploy | `a0d8a28` 等 | 代码/数据进远端 |
| 2 | 前端性能（索引+分片） | `ee55224` | 5165 条可承载展示 |
| 3 | readme + normalize + 首次 deploy | `65d4dcb` | LLM 输入质量↑；tutorial 门禁 |
| 4 | **LLM 策略** | `e49be2a` + `198cde4` | 本汇报主体 |
| 收口 | 清 active backlog | `dcb9135` | 策略完结 |
| 旁路小修 | 字体 CSP + 路径泄露 | `db12e7f` | 上线卫生（非 LLM 核心） |

设计真相源：`docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`  
（grilling 后顺序定为：1 push → 2 前端 → 3 数据/deploy → 4 LLM）

---

## 三、我们改了什么（策略本身）

### 3.1 并发与配置

| 项 | 改前 | 改后 |
|----|------|------|
| `api.batch_size` | 3 | **10** |
| `DEFAULT_BATCH_SIZE` | 3 | **10** |
| 配置驱动 | 硬编码为主 | 读 `config/llm-analysis.yaml` |
| 线程池 | 低并发 | `ThreadPoolExecutor max_workers=batch_size` |

### 3.2 分析优先级

| 项 | 改前 | 改后 |
|----|------|------|
| 候选顺序 | 过滤后顺序不稳 | **`stars` 降序** |
| 位置 | 易在 filter 后打乱 | `get_projects_to_analyze` / `pre_filter` **显式 sort** |
| 效果 | 低价值与高价值混跑 | 高星先拿 quality_score / tracking |

### 3.3 API 与可靠性

| 项 | 改前 | 改后 |
|----|------|------|
| Key 轮询 | 多 key 但并发下不安全风险 | `KeyRotator` + **`threading.Lock`** |
| 调用方式 | 直接 urllib / OpenAI 兼容（非 delegate_task） | **保持**（cron 无人审批，禁止依赖审批型委派） |
| Prompt / 评分公式 | — | **明确不改** `llm_prompts.py` 与 100 分制公式 |
| 增量落盘 | 已有思路 | 每批 checkpoint，可续跑 |
| archived | — | 分析候选 **跳过 archived**（不计入 active backlog） |

### 3.4 Cron 与超时（稳态）

| Job / 配置 | 作用 | 关键点 |
|------------|------|--------|
| `2a0c271a031f` + `search-in-coding-daily.sh` | 日采集 | **禁止覆盖**；仍是 `update_tracker.py` |
| `2aa9da554787` + `search-in-coding-weekly.sh` | 周一 LLM 全量/重评 | 含 benchmarks 等 |
| `f110f12e4d96` + `search-in-coding-llm-daily.sh` | **新建** Tue–Sat 03:30 增量 | `--max-projects 200 --skip-benchmarks` + deploy |
| `cron.script_timeout_seconds` | 长任务 | **3600**（从 120 类失败路径拉起来） |

这是策略改造里最关键的运维决策之一：  
**采集与 LLM 日增量脚本彻底分离**，避免「改 daily 脚本名/内容」误伤采集。

### 3.5 执行策略（如何吃 backlog）

| 阶段 | 做法 |
|------|------|
| Batch4 主体 | 多轮手动/半自动分析（约 5 轮量级）+ **每轮 score/build/deploy** |
| 收口 | 再 1 轮 `--max-projects 300 --skip-benchmarks` 清 active 残留 |
| 稳态 | 靠 **llm-daily 200/天** + **周一 weekly** 消化新增 |

---

## 四、数据怎么变（从崩到稳）

> 下列为过程锚点（约数/报告数）；终态以收口报告与 dry-run 为准。

| 阶段 | 未分析 / pending 量级 | quality 有分 | 说明 |
|------|----------------------|--------------|------|
| bulk 刚完成 | ~**5120** pending 量级 | ~**33** 已分析 | 几乎全是待 LLM |
| Batch4 多轮后 | pending ~**200** 量级 | ~**4950** | 吞吐打通，主 backlog 吃掉 |
| 收口前 active | active no_la **100**；含 archived 总 no_la **205** | 4950 | 高星失败残留 + archived 跳过 |
| **收口后（终态）** | active no_la **0**；dry-run **0**；pending_tp **106** | **5050** | active 可分析队列清空 |

### 终态口径（重要）

| 指标 | 终态 | 含义 |
|------|------|------|
| total | **5165** | 库规模不变 |
| dry-run `would analyze` | **0** | 没有 active 候选 |
| active `no_last_analyzed` | **0** | 可分析且未分析 = 0 |
| 含 archived 的 no_la | **105** | 设计跳过，不阻塞收口 |
| `quality_score > 0` | **5050** | LLM 质量分已覆盖主体 |
| tracking pending | **106** | 分级结果/含不可再分析项，≠「还能分析 100 条」 |
| 线上 | projects **5165**，HTTP 200 | 已 deploy |

---

## 五、关键交付物与提交

### 5.1 代码 / 配置 / 自动化

| 交付 | 说明 |
|------|------|
| `config/llm-analysis.yaml` | `batch_size: 10` |
| `scripts/weekly_analysis.py` | 配置驱动并发、stars 排序、批处理 |
| `scripts/llm_api.py` | KeyRotator 加锁、batch_analyze |
| `~/.hermes/scripts/search-in-coding-llm-daily.sh` | 日增量 LLM（新建） |
| 既有 weekly / daily collect 脚本 | 职责保持分离 |
| Hermes cron 三 job | 采集 / 周 LLM / 日 LLM |

### 5.2 代表 commits（LLM 主线）

| Commit | 内容 |
|--------|------|
| `e49be2a` | feat(batch4): 并发 10、stars 降序、llm-daily 路径 |
| `198cde4` | data(batch4): 多轮 LLM 进度 + 站点产物 |
| `dcb9135` | data(llm-closeout): 清 active backlog + 策略结案文档/wiki |

（旁路：`db12e7f` 为 dogfood 小修，不属于 LLM 策略本体，但同日线上卫生。）

### 5.3 文档

| 文档 | 作用 |
|------|------|
| `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md` | 含 Batch4 策略设计与 grilling 决策 |
| `docs/superpowers/handoff/2026-07-14-batch4-llm-strategy-prompt.md` | Batch4 执行路由 |
| `docs/superpowers/handoff/2026-07-15-llm-strategy-auto-closeout-prompt.md` | 单对话自动收口 |
| `docs/llm-strategy-closeout-2026-07-15.md` | 收口证据报告 |
| wiki L1 / L4B / L6 | 终态与经验（含 active/archived 计数口径） |

---

## 六、明确「做了 / 没做」

### 做了

- 提高并发到 10，并配置化  
- 按 stars 优先分析  
- Key 轮询线程安全  
- cron 超时 3600  
- 新建日增量 LLM，与采集脚本分离  
- 多轮清 backlog + 收口一轮 active 清零  
- 每阶段 deploy，线上 metrics 同步  
- 安全 merge / official-seed 等既有保护保持  

### 刻意没做（边界）

- **不改** `llm_prompts.py` 分析模板  
- **不改** 100 分制评分公式  
- **不**用 `delegate_task` 跑 cron 长分析（审批/超时不适合）  
- **不**覆盖日采集脚本  
- **不**把 archived 强行塞进分析队列  
- **不**把「tracking pending=106」误判为策略失败  

---

## 七、过程中的关键坑（已处理）

1. **120s script_timeout** 会杀死采集/分析 → 提到 **3600**  
2. **日采集与日 LLM 不能同名脚本** → `llm-daily` 独立文件 + 独立 job  
3. **WebUI 子 Agent 长任务易 600s 掐断** → 收口用本会话直接跑 `weekly_analysis`，避免错误委派  
4. **active vs archived backlog** → dry-run / active no_la 才是「还能不能分析」的口径  
5. **Batch4 中途 API 429/失败** → 可续跑；收口轮 100 success / 0 failed 补齐 active  

---

## 八、终态验收清单

| # | 项 | 结果 |
|---|----|------|
| 1 | batch_size=10 | PASS |
| 2 | stars 降序 | PASS |
| 3 | KeyRotator Lock | PASS |
| 4 | script_timeout=3600 | PASS |
| 5 | collect daily 独立且仍为采集 | PASS |
| 6 | llm-daily max=200 独立 job | PASS |
| 7 | weekly job 存在 | PASS |
| 8 | dry-run 待分析 = 0 | PASS |
| 9 | active no_last_analyzed = 0 | PASS |
| 10 | 线上 5165 + HTTP 200 | PASS |

**总评：COMPLETE**

---

## 九、从起点到终点的对照表

| 维度 | 一开始 | 最后 |
|------|--------|------|
| 库规模 | bulk 后 5165 | 5165（稳定） |
| LLM 覆盖 | ~几十条级 | **quality>0 ≈ 5050** |
| 可分析队列 | 数千 pending | **dry-run 0 / active 0** |
| 并发 | 3 | **10** |
| 优先级 | 无 | **高星优先** |
| 自动化 | 周一全量为主，易超时 | **日增量 + 周一 + 3600s** |
| 脚本风险 | 易误伤 daily collect | **三脚本职责分离** |
| 线上 | 大 JSON/未分析为主 | 可公开；策略已稳态 |
| 用户操作 | 需多轮 handoff/收口 | **无需再操作** |

---

## 十、之后只需「维持」，不必再开策略批

| 自动维持 | 说明 |
|----------|------|
| 日采集 `2a0c271a031f` | 新项目入库 |
| 日 LLM `f110f12e4d96` | 每天最多 200 条增量分析 |
| 周 LLM `2aa9da554787` | 重评 / benchmarks / 报告 |

**非本次范围、可另开产品批：**

- 浏览器补 dogfood  
- 冷启动性能（M1）  
- 分类噪声（M3）  
- handoff/docs 是否入库整理  

---

## 十一、给读者的总结

1. **改的是「怎么分析」**（并发、排序、cron、超时、脚本隔离），不是「分析什么 prompt / 怎么打分」。  
2. **结果是「能跑完 + 能自动续」**：从近全库未分析 → active 队列清空 + 日/周自动化。  
3. **完结标准已满足**：策略 7 项 + active backlog 0 + deploy + 文档/wiki。  
4. **你可以停手**；后续只靠 cron 维持即可。

---

*本汇报汇总 grilling 设计、Batch4 实现、多轮分析、dogfood 旁路与 2026-07-15 自动收口；细节证据以 `docs/llm-strategy-closeout-2026-07-15.md` 与 git 历史为准。*

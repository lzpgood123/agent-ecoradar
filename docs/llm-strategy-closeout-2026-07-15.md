# LLM 策略优化收口报告（2026-07-15）

**结论：COMPLETE**

工作区：`/root/workspace/search in coding`  
角色：收口执行 Agent（可自检，不做独立 dogfood 重开）  
范围：策略工程验收 + 清 active LLM backlog + deploy + 轻量验收 + git/wiki + 结案

---

## 1. 策略工程验收（全部通过）

| 检查项 | 期望 | 实测 | 结果 |
|--------|------|------|------|
| `config/llm-analysis.yaml` batch_size | 10 | `api.batch_size: 10` | PASS |
| `weekly_analysis.DEFAULT_BATCH_SIZE` | 10 | `DEFAULT_BATCH_SIZE = 10` | PASS |
| 候选排序 | stars 降序 | `to_analyze.sort(..., reverse=True)` 于 `get_projects_to_analyze` / `pre_filter` | PASS |
| KeyRotator 线程安全 | 有 Lock | `self._lock = threading.Lock()`；`next/mark_failed/reset` 均加锁 | PASS |
| cron.script_timeout_seconds | 3600 | `script_timeout 3600` | PASS |
| 日采集脚本 | 仅采集 | `search-in-coding-daily.sh` → `update_tracker.py`（job `2a0c271a031f`） | PASS |
| 日增量 LLM 脚本 | 独立，max 200 | `search-in-coding-llm-daily.sh` → `--max-projects 200 --skip-benchmarks` + deploy（job `f110f12e4d96`，Tue–Sat 03:30） | PASS |
| 周 LLM job | 存在 | `search-in-coding-weekly.sh`（job `2aa9da554787`，Mon 03:30） | PASS |
| dry-run 配置回显 | batch_size=10 | `batch_size=10 (config-driven)` | PASS |

未改：`llm_prompts.py`、评分公式、前端/CSP、Batch1–3 逻辑、全量 enrich/normalize。

---

## 2. 基线 → 终态

| 指标 | 基线 | 终态 |
|------|------|------|
| total projects | 5165 | 5165 |
| no_last_analyzed（含 archived） | 205 | 105 |
| **active no_last_analyzed** | **100** | **0** |
| archived no_last_analyzed（设计跳过） | 105 | 105 |
| candidates_to_analyze（dry-run） | 100 | **0** |
| pending tracking_priority | 201 | 106 |
| quality_score > 0 | 4950 | 5050 |
| last_analyzed 有值 | — | 5060 |

说明：高星但 `status=archived` 的条目（如 get-shit-done 等）按 `get_projects_to_analyze` 规则跳过，不计入可清 backlog。收口成功阈值以 **active no_la < 20** / `candidates_to_analyze` 为准。

---

## 3. 清 backlog 执行

- 轮次：**1 / 最多 3**（第 1 轮后 active backlog 已清零，无需 2–3 轮）
- 命令：`python3 scripts/weekly_analysis.py --max-projects 300 --skip-benchmarks`
- 结果：**100 success / 0 failed**；10 批 × batch_size=10
- 后续：rescore、snapshot、reports、build site 均成功（exit 0）
- 日志：`/tmp/weekly_analysis_round1.log`

Deploy：

1. 分析成功后：`python3 scripts/deploy_site.py --dest /var/www/coding.lzpgood.online` → `files: 82`
2. 收口前再 deploy 一次：同样成功

---

## 4. 收口验收证据

### 数据
- dry-run：`Dry run: would analyze 0 projects`
- metrics（线上 `/var/www/coding.lzpgood.online/data/metrics.json`）：
  - projects=5165
  - tracking_priorities: track=4571, index=419, pending=106, reject=69
- 今日分析样本（高星已分析）：obra/superpowers q=34 track；affaan-m/ECC q=34 track；ultraworkers/claw-code q=39 track 等

### 线上
- `curl https://coding.lzpgood.online/` → **HTTP 200**
- 部署目录含 `metrics.json` / `projects.json` / `search-index.json` / `detail/`（时间戳 2026-07-15 15:14–15:15）

### Cron（轻量）
- daily collect `2a0c271a031f` active，Last run ok
- weekly LLM `2aa9da554787` active
- llm-daily `f110f12e4d96` active，Last run ok
- script_timeout=3600 已确认

---

## 5. Git / Wiki

### 提交范围（仅允许）
- `data/projects.yaml`
- `docs/reports/*`、`site/data/*`、`site/reports/*`（构建产物惯例）
- wiki 最小更新：`wiki/L1-全景.md`、`wiki/L4B-后端详解.md`、`wiki/L6-经验录.md`
- 结案报告：`docs/llm-strategy-closeout-2026-07-15.md`

### 明确未提交
- `.bak*`、handoff 大礼包、`.agents`、`.hermes` 临时、`data/raw` 当日原始包等

### Wiki 要点
- L1：版本改为 `v2026.07.15-llm-strategy-closeout`；数据快照与 COMPLETE 状态
- L4B：batch_size=10、stars 降序、三脚本/job 映射、收口终态
- L6：§33 收口经验 + active/archived backlog 计数口径

---

## 6. 结果判定

| 条件 | 状态 |
|------|------|
| 策略项全过 | ✅ |
| no_la active < 20（实际 0） | ✅ |
| deploy 成功 | ✅ |
| 未改禁止项 | ✅ |

**最终状态：COMPLETE**

用户无需再操作。残留仅 archived 未分析 105 条（按设计跳过 LLM），不阻塞策略收口。

---

## 7. 命令与文件索引

```bash
# 策略验收（摘要）
grep -n 'batch_size' config/llm-analysis.yaml
python3 scripts/weekly_analysis.py --dry-run
hermes cron list

# 清 backlog（本轮已执行）
python3 scripts/weekly_analysis.py --max-projects 300 --skip-benchmarks
python3 scripts/deploy_site.py --dest /var/www/coding.lzpgood.online
```

相关文件：
- `config/llm-analysis.yaml`
- `scripts/weekly_analysis.py` / `scripts/llm_api.py`
- `~/.hermes/scripts/search-in-coding-{daily,weekly,llm-daily}.sh`
- `docs/llm-strategy-closeout-2026-07-15.md`（本文件）

# 新对话 Agent 启动提示词：LLM 策略优化 — 单对话全自动收口（方案 C）

> 将以下全部内容复制粘贴到**一个新对话**中作为第一条消息。  
> **全程自动执行，禁止向用户提问、禁止 clarify、禁止等待确认。**  
> 所有可选决策已在本文写死默认值。

---

## 你的任务

你是 "Search in Coding" 的**收口执行 Agent**（可自检，不做独立 dogfood 重开）。

目标：在**一个对话内**完成「LLM 策略优化」的最终收口并宣告完成：

1. 验证策略工程项已就位（并发 10 / stars 降序 / cron / timeout）
2. 清空或压到极低剩余 LLM backlog（`no_last_analyzed` 目标 **&lt; 20**，理想 **0**）
3. deploy 线上
4. 轻量质量与 cron 验收
5. 提交数据进度（若有变更）
6. 最小 wiki 更新
7. 输出**结案报告**（含证据）

**不要**重跑 Batch1–3、不要改前端/CSP、不要改评分公式、不要改 `llm_prompts.py`、不要全量 enrich/normalize。

工作区：`/root/workspace/search in coding`

---

## 硬编码默认（禁止再问用户）

| 决策点 | 默认 |
|--------|------|
| 清 backlog | 最多 **3 轮** `weekly_analysis.py --max-projects 300 --skip-benchmarks` |
| 成功阈值 | `no_last_analyzed &lt; 20` 即视为 backlog 收口成功；若 3 轮后仍 ≥20 也**结案**并标注残留原因（API/超时） |
| deploy | 每轮分析成功后 deploy；最后再 deploy 一次 |
| git | 有数据/脚本变更则 commit + push；无变更则跳过 |
| commit 范围 | 只提交 `data/projects.yaml`、相关 `site/` 构建产物（若惯例提交）、wiki 小改；**不**提交 `.bak`、handoff 大礼包、`.agents` |
| 失败重试 | 单轮失败：等 30s 再跑下一轮；429/额度：减小到 `--max-projects 100` 再试一轮 |
| 用户交互 | **禁止** clarify / 选择题 / 「是否继续」 |

---

## 第一步：环境与技能

1. `skill_view("using-superpowers")` 失败则读 `HERMES.md` 继续  
2. `cd "/root/workspace/search in coding" && source .venv/bin/activate`  
3. 确认无第二个 `enrich_projects` / 冲突写 `projects.yaml` 的进程；若有残留 enrich 且与 LLM 无关可忽略；若有另一个 `weekly_analysis` 在跑则 **wait 其结束** 再动手（最多等 45 分钟，超时则记录并仍尝试自己的轮次）

---

## 第二步：策略工程验收（只读 + 记录）

用命令收集证据，写入最终报告：

```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate

# 配置
grep -n 'batch_size' config/llm-analysis.yaml

# 代码要点
grep -n 'get_projects_to_analyze\|sort\|batch_size\|DEFAULT_BATCH_SIZE' scripts/weekly_analysis.py | head -40
grep -n 'Lock\|class KeyRotator\|max_workers' scripts/llm_api.py | head -30

# dry-run 排序
python3 scripts/weekly_analysis.py --dry-run 2>&1 | tail -40

# timeout
python3 - <<'PY'
import yaml
from pathlib import Path
print('script_timeout', yaml.safe_load(Path.home().joinpath('.hermes/config.yaml').read_text()).get('cron',{}).get('script_timeout_seconds'))
PY

# cron 与脚本
hermes cron list
ls -la ~/.hermes/scripts/search-in-coding-daily.sh \
       ~/.hermes/scripts/search-in-coding-weekly.sh \
       ~/.hermes/scripts/search-in-coding-llm-daily.sh
# 确认 daily collect 仍是 update_tracker，llm-daily 是 weekly_analysis --max-projects 200
head -20 ~/.hermes/scripts/search-in-coding-daily.sh
head -30 ~/.hermes/scripts/search-in-coding-llm-daily.sh
```

**必须全部为真（否则修到为真再继续，仍禁止问用户）：**

| 检查项 | 期望 |
|--------|------|
| batch_size | 10 |
| stars 降序 | dry-run Top 按 stars 降序 |
| KeyRotator | 有锁 |
| script_timeout | 3600 |
| collect 脚本 | `update_tracker` / 采集，**不是** LLM 增量 |
| llm-daily 脚本 | `weekly_analysis --max-projects 200`，独立文件名 |
| weekly job | 存在 |

若 `batch_size` 不是 10：直接改 `config/llm-analysis.yaml` 为 10。  
若 llm-daily 脚本缺失：按既有约定创建 `~/.hermes/scripts/search-in-coding-llm-daily.sh` 并确保 cron job 存在（`hermes cron list` 有则不重建；无则创建 Tue–Sat 03:30 no_agent）。  
若 timeout 不是 3600：`hermes config set cron.script_timeout_seconds 3600`。

---

## 第三步：基线计数

```bash
python3 - <<'PY'
import yaml
from pathlib import Path
ps=yaml.safe_load(Path('data/projects.yaml').read_text())
n=len(ps)
no_la=sum(1 for p in ps if not p.get('last_analyzed'))
pending=sum(1 for p in ps if p.get('tracking_priority')=='pending')
qs=sum(1 for p in ps if (p.get('quality_score') or 0)>0)
print(f'BASELINE total={n} no_last_analyzed={no_la} pending_tp={pending} quality_gt0={qs}')
todo=sorted([p for p in ps if not p.get('last_analyzed')], key=lambda p: p.get('stars') or 0, reverse=True)[:8]
for p in todo:
    print(f"  pending_stars={p.get('stars')} {p.get('name')}")
PY
```

记录 BASELINE。

---

## 第四步：自动清 backlog（核心）

循环最多 **3 轮**：

```bash
# 每轮（第 1–2 轮用 300；若遇 429 则该轮改 100）
python3 scripts/weekly_analysis.py --max-projects 300 --skip-benchmarks
# 成功则：
python3 scripts/deploy_site.py --dest /var/www/coding.lzpgood.online
# 再统计 no_last_analyzed / pending
```

规则：

1. 每轮前后打印计数  
2. 若 `no_last_analyzed &lt; 20`：**立即停止循环**，进入验收  
3. 若本轮 `no_last_analyzed` 不下降：下一轮改 `--max-projects 100`，sleep 60  
4. 若进程超时/杀死：从断点再跑（脚本本身跳过已分析）  
5. 禁止 `delegate_task` 跑长 LLM（WebUI 子 Agent 易 600s 掐断）；**本对话直接 terminal 前台或 background+wait**  
6. 长任务用足够 timeout（单轮可 background + `process wait`，总等待可到 90 分钟/轮）

---

## 第五步：收口验收（方案 C 轻量）

### 5.1 数据

```bash
python3 - <<'PY'
import yaml
from pathlib import Path
ps=yaml.safe_load(Path('data/projects.yaml').read_text())
n=len(ps)
no_la=sum(1 for p in ps if not p.get('last_analyzed'))
pending=sum(1 for p in ps if p.get('tracking_priority')=='pending')
qs=sum(1 for p in ps if (p.get('quality_score') or 0)>0)
print(f'FINAL total={n} no_last_analyzed={no_la} pending_tp={pending} quality_gt0={qs}')
# 高星已分析抽 5
hi=sorted([p for p in ps if (p.get('stars') or 0)>=5000 and p.get('last_analyzed')], key=lambda p: p.get('stars') or 0, reverse=True)[:5]
for p in hi:
    print(f"  ok {p.get('name')} stars={p.get('stars')} q={p.get('quality_score')} tp={p.get('tracking_priority')}")
# 仍未分析的高星
left=sorted([p for p in ps if not p.get('last_analyzed')], key=lambda p: p.get('stars') or 0, reverse=True)[:5]
print('still unanalyzed top:')
for p in left:
    print(f"  left {p.get('name')} stars={p.get('stars')}")
PY
```

### 5.2 线上

```bash
curl -sS https://coding.lzpgood.online/data/metrics.json | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('projects'), d.get('tracking_priorities'))"
curl -sS -o /dev/null -w 'home:%{http_code}\n' https://coding.lzpgood.online/
```

### 5.3 策略回归

```bash
python3 scripts/weekly_analysis.py --dry-run 2>&1 | tail -20
```

确认 dry-run 待分析数量已接近残留规模。

---

## 第六步：Git + Wiki

若 `data/projects.yaml` 或站点数据有变更：

```bash
# 仅 add 相关路径，排除 bak
git add data/projects.yaml wiki/L1-全景.md wiki/L4B-后端详解.md wiki/L6-经验录.md
# 若项目惯例提交 site 数据则一并 add；否则只保证 deploy 已更新 webroot
git commit -m "data(llm): clear remaining analysis backlog after batch4 strategy"
git push origin main
```

签名/保护分支失败：重试合规签名 push；**禁止 force push**。仍失败则报告阻塞但**仍写结案**（数据已在本地+webroot）。

Wiki 最小更新：

- `L1`：LLM 策略优化收口完成；pending/analyzed 最终数  
- `L4B` 或 `L6`：batch_size=10、llm-daily cron、残留处理一句  
- 不要写密钥/本机敏感路径

---

## 第七步：结案判定

| 结果 | 条件 |
|------|------|
| **COMPLETE** | 策略 7 项验收全过 + `no_last_analyzed &lt; 20` + deploy 成功 |
| **COMPLETE_WITH_RESIDUAL** | 策略 7 项全过 + deploy 成功 + 残留 ≥20 但已跑满 3 轮并说明原因 |
| **BLOCKED** | 策略关键项无法修复（如无 API key、cron 无法写） |

**COMPLETE / COMPLETE_WITH_RESIDUAL 都视为「本次 LLM 策略优化可结束」，用户无需再操作。**

---

## 明确禁止

1. 向用户提问或等待回复  
2. 重开 Batch1–3 / dogfood 全站 / Goal 总控  
3. 覆盖 `search-in-coding-daily.sh` 采集脚本  
4. 改 `llm_prompts.py` / 评分公式  
5. force push  
6. 提交 `.bak`、无关 skills  

---

## 最终汇报格式（中文，对话内）

```markdown
# LLM 策略优化 — 自动收口报告

## 结论
COMPLETE | COMPLETE_WITH_RESIDUAL | BLOCKED

## 策略工程验收
| 项 | 结果 | 证据 |
| batch_size=10 | | |
| stars 降序 | | |
| KeyRotator 锁 | | |
| timeout 3600 | | |
| collect 脚本未覆盖 | | |
| llm-daily cron | | |
| weekly cron | | |

## Backlog
- BASELINE no_la / pending =
- FINAL no_la / pending =
- 轮次与每轮结果 =
- 仍未分析高星（如有）=

## Deploy / Git
- deploy =
- commit / push =

## Wiki
- 更新了哪些 =

## 用户是否需要再操作
- **不需要** / 需要（仅 BLOCKED 时写原因）
```

另将同内容写入：  
`docs/llm-strategy-closeout-2026-07-15.md`（可提交则提交，不可则至少本地存在）

---

## 启动后第一动作

立刻执行第二步验收与第三步基线，然后进入第四步清 backlog——**不要等待用户发「开始」**。

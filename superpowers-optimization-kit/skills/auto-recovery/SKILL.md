---
name: auto-recovery
description: Use when a stage gate FAILs, tests fail, or implementation fails during a full-auto Superpowers delivery run. Classifies the failure, rotates to a new strategy (never repeating tried ones), re-runs the gate, and on strategy exhaustion writes a failure report and notifies the user without blocking other tasks.
---

# Auto Recovery — 失败恢复与策略旋转

## 概述

门禁 FAIL、测试失败或实现失败时，**不要等人、不要原地重试**。加载本 skill，按固定恢复算法：读取已试方法 → 分类失败 → 提出**与已试摘要不同**的新策略 → 执行 → 写入已试方法 → 重跑对应门禁。可无限重试，但每一轮必须换策略。策略穷尽时写失败报告、通知用户，**不阻塞后续任务**。

## 何时使用

- `gatekeeper` 子 Agent 返回 **FAIL**
- 实现阶段测试/构建/部署失败
- 验收证据收集失败、wiki 合规失败、完成门硬门槛未绿
- Goal 模式运行期任何「卡在门禁/实现」需要自动修复的时刻

**不适用：**

- Pre-grill 阶段 PRD 不可行（应回到用户修 PRD，不走本 skill）
- 仅需读文档、无失败发生
- 用户明确要求停机等待人工决策（仍可写失败报告后停）

## 输入契约

执行前必须拿到：

| 输入 | 说明 |
|------|------|
| 失败门禁/阶段 | 如 Intake / Spec+Plan / 实现 / 验收证据 / Wiki / 完成门 |
| 完成契约路径 | `docs/superpowers/contracts/YYYY-MM-DD-<topic>-contract.md` |
| 门禁报告路径 | `docs/superpowers/gates/...`（若有） |
| Goal 文档路径 | `docs/superpowers/goals/...`（若有） |
| 错误摘要 | 命令输出、断言失败、子 Agent FAIL 原因列表 |

## 恢复算法（写死，按序执行）

```text
1. 读取完成契约「已试方法」表
2. 分类失败：
   A. 技术失败 → 自动修复（换实现/测试/证据策略）
   B. PRD 矛盾/缺口 → decision-arbiter
      （Phase 0 若未装 decision-arbiter：写 failure-report 并停在报告，禁止瞎改 PRD 目标）
   C. 环境/权限缺失 → 写 failure-report
      （本应在 pre-grill 准备清单避免；不假装能本地绕过）
3. 生成「新策略」：方法摘要不得与已试方法列表中任一摘要相同
4. 执行新策略
5. 把方法写入完成契约「已试方法」表
6. 重新跑对应门禁（gatekeeper + delegate_task，禁止执行 Agent 自检放行）
7. 若无法再提出不同策略 → 写 failure-report → 通知用户 → 不阻塞其他任务
```

### 步骤 1：读取已试方法

1. 打开完成契约文件。
2. 定位 `## 已试方法（禁止原地踏步）` 表格。
3. 提取每一行的 **方法摘要** 列表 `TRIED[]`。
4. 若表不存在：按 completion-contract 模板补全后再继续；`TRIED` 为空。

### 步骤 2：分类失败

根据门禁报告 / 错误输出，**只选一类主因**（可备注次要因素）：

| 类别 | 判定信号 | 动作 |
|------|---------|------|
| **A. 技术失败** | 测试红、编译错、逻辑 bug、证据路径缺失、wiki 漏更、实现未覆盖 plan 步骤 | 自动修复；本 skill 主路径 |
| **B. PRD 矛盾/缺口** | 目标互斥、验收与非目标冲突、PRD 缺关键字段、与 P1/wiki 硬约束冲突 | 加载/调用 `decision-arbiter`；**禁止改 PRD 目标** |
| **C. 环境/权限缺失** | 无 API key、无端口、无网络、无写权限、依赖服务不可达、YOLO/工具策略挡住必要操作 | 写失败报告；可提示用户补准备清单；**不无限空转** |

**Phase 0 特例（decision-arbiter 未安装）：**

- 判为 B 时：直接走步骤 7 写 `failure-report`，在报告中标明「需 decision-arbiter / 人工仲裁」。
- 不得擅自删减 PRD 目标或验收场景来「过门」。

### 步骤 3：生成新策略（禁止原地踏步）

1. 根据类别 A/B/C 起草候选策略，写出 **一句话方法摘要**（≤80 字，动词开头，含关键手段）。
2. 规范化比较：去首尾空白、折叠空白、小写后与 `TRIED[]` 逐条比对。
3. **若与任一已试摘要相同 → 丢弃，换另一策略。**
4. 若穷尽合理不同策略仍无法提出新摘要 → 进入步骤 7。

**好的摘要示例：**

- `改用集成测试替代单元 mock 覆盖 /health`
- `按 L4B 补路由注册后再 curl 实测`
- `delegate decision-arbiter 仲裁端口冲突并写 P1`

**坏的摘要（禁止）：**

- `再试一次` / `fix` / `继续`（无信息）
- 与上一轮仅标点/同义词差异的伪新策略

### 步骤 4：执行新策略

- **A：** 改代码/测试/证据/文档；真实跑命令，保留输出路径。
- **B：** `delegate_task` 派决策仲裁 Agent（或 Phase 0 直接 failure-report）；仲裁结果写入 P1 与完成契约决策矩阵/未决项。
- **C：** 不再空转修复；记录缺失项，进入失败报告。

执行中遵守：

- 不改 PRD 目标与已冻结验收场景（可新增隐含缺口场景，标记 `冻结=后增`）
- 不跳过 `gatekeeper` 自批
- 不删除「已试方法」历史行

### 步骤 5：写入已试方法

在完成契约表格**追加一行**（不要改历史行）：

```markdown
| {N} | {失败门禁} | {方法摘要} | {结果：进行中/失败/通过} | {ISO 时间} |
```

规则：

- `方法摘要` 必须与步骤 3 采用的摘要一致
- 执行前可先写 `进行中`，门禁结果出来后更新为 `失败` 或 `通过`
- 同步更新契约「最后更新」时间戳

### 步骤 6：重跑对应门禁

必须通过 `gatekeeper` + `delegate_task` 独立校验，模板：

```text
delegate_task(
  goal="作为独立门禁校验 Agent，检查阶段 {STAGE} 是否通过",
  context="""
  项目根：{ROOT}
  完成契约：{CONTRACT_PATH}
  Goal 文档：{GOAL_PATH}
  PRD：{PRD_PATH}
  本阶段：{STAGE}
  本轮恢复策略：{STRATEGY_SUMMARY}
  必读：gatekeeper skill 中该阶段检查表
  输出：按 templates/gate-report.md 写到 docs/superpowers/gates/{date}-{stage}.md
  返回：PASS 或 FAIL + 原因列表
  """
)
```

判定：

- **PASS** 且报告文件存在 → 更新完成契约阶段字段；本 skill 结束，继续下一阶段
- **FAIL** → 将本轮已试方法结果标为 `失败`，**回到步骤 1**（无限重试，但必须新策略）

### 步骤 7：策略穷尽 → 失败报告

当无法提出与 `TRIED[]` 不同的合理新策略，或类别 C / Phase0-B 必须停机时：

1. 写失败报告到固定路径（见下）
2. 在对话中 **明确通知用户**（含报告路径 + 卡在哪一扇门）
3. **不阻塞其他任务**：可继续队列中的无关任务 / 其他 Goal；本任务标记为 blocked/failed，等待用户

## 失败报告

### 路径（强制）

```text
docs/superpowers/failures/YYYY-MM-DD-<topic>-failure.md
```

- 目录不存在则创建
- `<topic>` 与完成契约/Goal 文档 topic 一致（小写、连字符）
- 可参考 `templates/failure-report.md`（若优化包已安装该模板）

### 正文最低字段

```markdown
# 失败报告：{任务名称}

## 摘要
{一句话：卡在哪、为何策略穷尽}

## 卡在哪个门禁
- 阶段：{STAGE}
- 最近门禁报告：{path}
- 最近错误：{摘录}

## 已试方法列表
| # | 失败门禁 | 方法摘要 | 结果 | 时间 |
|---|---------|---------|------|------|
| …从完成契约复制… |

## 错误与资源消耗
- 关键/轮次：
- 主要错误类型：
- 命令/日志路径：
- 备注：

## 当前完成契约快照路径
{CONTRACT_PATH}

## 通知状态
- 已通知用户：是
- 是否阻塞其他任务：否
- 建议用户下一步：{补环境 / 修 PRD / 安装 decision-arbiter / 人工决策…}
```

## 与其他 skill 的关系

| Skill | 关系 |
|-------|------|
| `gatekeeper` | FAIL 时触发本 skill；修复后必须再经 gatekeeper |
| `completion-contract` | 已试方法表与硬门槛的唯一权威；本 skill 只追加已试行 |
| `decision-arbiter` | 类别 B 的处理出口；结果写 P1 |
| `goal-document` / Goal 模式 | 失败恢复策略章节应引用本 skill；策略穷尽不宣称 goal done |
| `wiki-checkpoint` | Wiki 门失败时按 A 类修复文档后再过门 |

## 核心规则（硬约束）

1. **无限重试，但必须换策略** — 禁止相同方法摘要重跑
2. **已试方法写入完成契约** — 不写在对话记忆里当唯一来源
3. **不改 PRD 目标** — 矛盾走仲裁或失败报告
4. **不自检放行** — 修复后必须 `delegate_task` 门禁
5. **策略穷尽不阻塞后续任务** — 写报告 + 通知 + 本任务停，其他任务可继续
6. **环境类失败不空转** — 类别 C 直接 failure-report

## 输出格式

每次恢复轮次结束时输出：

```text
=== Auto Recovery ===
阶段：{STAGE}
失败分类：A 技术 / B PRD / C 环境
本轮策略：{方法摘要}
与已试是否重复：否
执行结果：进行中 / 门禁 PASS / 门禁 FAIL / 策略穷尽
已试方法数：{N}
完成契约：{path}
失败报告：{path 或 无}
是否阻塞其他任务：否
下一步：重跑门禁 / 进入下阶段 / 等待用户
```

## 常见陷阱

1. **「再跑一遍同样命令」当新策略** — 摘要必须体现手段差异  
2. **修完自己宣布门禁通过** — 必须独立 gatekeeper  
3. **改 PRD 目标消红** — 禁止；走 B 或失败报告  
4. **已试方法只写在聊天里** — 必须落盘完成契约  
5. **策略穷尽后卡住整个队列** — 明确不阻塞其他任务  
6. **Phase 0 没有 decision-arbiter 还硬仲裁** — 写 failure-report  

## 验证清单

- [ ] 已读完成契约「已试方法」
- [ ] 失败已分类为 A/B/C
- [ ] 新策略摘要与所有已试摘要不同
- [ ] 已试方法表已追加本轮
- [ ] 修复后经 gatekeeper/`delegate_task` 重验
- [ ] 若穷尽：`docs/superpowers/failures/YYYY-MM-DD-<topic>-failure.md` 已写
- [ ] 已通知用户且声明不阻塞其他任务

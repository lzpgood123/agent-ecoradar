---
name: decision-arbiter
description: Use when a full-auto Superpowers run hits PRD contradictions or gaps (target conflicts, missing critical fields, acceptance vs non-goals, clash with P1/wiki). Arbitrates execution decisions only — never changes PRD goals — writes P1 with source=arbitration + confidence, updates the completion-contract decision matrix, and returns a concrete continue-execution decision.
---

# Decision Arbiter — PRD 矛盾/缺口仲裁

## 概述

全自动交付中遇到 **PRD 矛盾、缺口、与历史约束冲突** 时，**不要改 PRD 目标、不要硬停空等**。加载本 skill（或由 `auto-recovery` 路由为类别 B 后 `delegate_task` 派出独立决策仲裁 Agent），按固定仲裁算法：

1. 陈述矛盾双方  
2. 查 P1 历史决策 / 用户偏好  
3. 查 L6 相关坑  
4. 给出推断 + 置信度  
5. 写入 `wiki/P1-产品决策日志.md`（来源=`arbitration`，含置信度）  
6. 更新完成契约决策矩阵与未决项  
7. 返回**继续执行**的具体决策  

本 skill **只能细化执行决策**（端口、实现路径、默认值、证据形态、兼容策略等），**不能改写、删除或降级 PRD 目标与已冻结验收场景**。

## 何时使用

- Intake / 决策编译发现目标互斥、验收与非目标冲突、PRD 缺关键字段
- 实现或验收阶段发现 PRD 与 `P1` / wiki 硬约束冲突
- `auto-recovery` 将失败分类为 **B. PRD 矛盾/缺口**
- 完成契约「决策矩阵」存在 `open` / `conflict` / 未决项需仲裁后才能过门

**不适用：**

- 技术失败（测试红、编译错、证据路径缺失）→ 走 `auto-recovery` 类别 A
- 环境/权限/密钥/端口不可达 → 走 `auto-recovery` 类别 C / failure-report
- 想改 PRD 目标语义或删减验收场景来「消红」→ **禁止**；应回到用户改 PRD（pre-grill）或 failure-report
- 纯实现细节且 PRD/P1 已有明确答案 → 直接按既有约束执行，无需仲裁

## 职责边界（硬约束）

| 允许 | 禁止 |
|------|------|
| 细化执行决策（默认值、选型、兼容路径、证据形态） | 改写 / 删除 / 降级 PRD 目标 |
| 在 PRD 隐含缺口上**新增**验收场景（`冻结=后增`） | 删除或降级已冻结验收场景 |
| 写入 P1（`✅决策` / `🎨偏好`，来源=`arbitration`） | 用聊天结论代替落盘 P1 / 契约 |
| 更新完成契约决策矩阵与未决项 open→resolved | 实现业务功能代码（仲裁 Agent 不写功能） |
| 置信度 low 时仍给出可执行默认并标明风险 | 置信度低就静默假定「用户一定同意」且不写 P1 |

**原则（对齐 D3 / D14 / D15）：** 用户 PRD 永远最高；Agent 只能细化，不能改目标；仲裁结果必须固化到 P1，成为永久约束。

## 输入契约

执行前必须拿到：

| 输入 | 说明 |
|------|------|
| 矛盾/缺口描述 | 双方陈述或缺失字段清单 |
| PRD 路径 | 用户 PRD 或 examples 中的 PRD |
| 完成契约路径 | `docs/superpowers/contracts/YYYY-MM-DD-<topic>-contract.md` |
| Goal 文档路径 | `docs/superpowers/goals/...`（若有） |
| 触发来源 | 门禁阶段名 / auto-recovery 轮次 / 执行 Agent 自检发现 |
| 相关证据 | 门禁报告、错误摘录、冲突的 plan/spec 片段（若有） |

## 仲裁算法（写死，按序执行）

```text
1. 陈述矛盾双方
2. 查 P1 历史决策 / 用户偏好
3. 查 L6 相关坑
4. 给出推断 + 置信度 high/med/low
5. 写入 wiki/P1-产品决策日志.md：
   标签=✅决策 或 🎨偏好
   来源=arbitration
   内容含置信度
6. 更新完成契约决策矩阵
7. 返回：继续执行的具体决策
```

### 步骤 1：陈述矛盾双方

用固定结构写清冲突，禁止含糊：

```markdown
## 矛盾陈述
- 决策点：{一句话命名}
- 方 A：{PRD/验收/非目标中的主张}（出处：{路径/章节}）
- 方 B：{另一主张或缺失默认}（出处：{路径/章节/现象}）
- 冲突类型：目标互斥 | 验收 vs 非目标 | 缺关键字段 | 与 P1/wiki 硬约束冲突
- 若放任不决的影响：{卡住哪扇门 / 无法实现哪条场景}
```

**缺口**（只有一方缺失）时：方 B 写「PRD 未规定；需执行默认」。

若陈述后发现**并非 PRD 矛盾**（纯技术/环境）→ **停止本 skill**，交回 `auto-recovery` 重分类为 A 或 C。

### 步骤 2：查 P1 历史决策 / 用户偏好

1. 打开 `wiki/P1-产品决策日志.md`（不存在则记录「P1 缺失」，置信度上限 med，仍可推断但必须创建/初始化后再写）。
2. 优先读：
   - 「用户偏好（固定置顶）」
   - 「决策时间线」中与决策点相关的 `✅决策` / `❌否决` / `🎨偏好` / `⏸️搁置`
3. 摘录 **可继承约束** 列表 `P1_HITS[]`（原文短摘 + 日期/标签）。
4. 若历史决策已明确覆盖本决策点 → 优先继承，置信度倾向 **high**。

### 步骤 3：查 L6 相关坑

1. 打开 `wiki/L6-经验录.md`（不存在则 `L6_HITS=[]`，备注缺失）。
2. 检索与决策点相关的坑、设计决策、反模式。
3. 摘录 `L6_HITS[]`；与 P1 冲突时：**不改 PRD 目标**；执行层优先避坑，并在推断中写明取舍理由。

### 步骤 4：推断 + 置信度

综合 PRD 字面义（最高）→ P1 偏好/决策 → L6 避坑 → 工程常识，给出**唯一**可执行决策。

| 置信度 | 条件 |
|--------|------|
| **high** | PRD 字面可推出，或 P1 已有同题 `✅决策`/`🎨偏好` 且无反例 |
| **med** | PRD 隐含 + P1/L6 方向一致，但无逐字规定 |
| **low** | 多处沉默或弱冲突；仅能选「可逆、范围最小」的默认以继续执行 |

**推断规则：**

1. **永不改 PRD 目标语义**；若方 A/B 都是「目标级」互斥且无法在执行层兼容 → 停止仲裁实现，写 failure-report / 建议用户修 PRD（不假装已解决）。
2. 能兼容则选**兼容双方目标**的执行方案（例如双路径、特性开关、文档化默认）。
3. 仅偏好冲突：跟 P1 `🎨偏好`；无偏好则选可逆默认 + **low/med**。
4. 输出必须是**可执行指令**（做什么、不做什么、默认值、文件/接口影响），不是「再讨论」。

### 步骤 5：写入 wiki/P1-产品决策日志.md

在**当日**时间线表格**追加**一行（不要改历史行；目录/文件不存在则先按 project-wiki 骨架创建最小 P1）：

```markdown
| {标签} | {决策摘要}（置信度={high|med|low}；仲裁：{方A} vs {方B} → {选定}） | arbitration | {关联契约/PRD/门禁路径} |
```

| 字段 | 规则 |
|------|------|
| 标签 | 执行级确定项用 `✅决策`；口味/风格/交互倾向用 `🎨偏好` |
| 来源 | **必须**为 `arbitration`（小写），便于审计与后续继承 |
| 内容 | **必须**含置信度；建议含矛盾一句话与选定执行决策 |
| 关联 | 完成契约路径、PRD 路径、触发门禁报告（若有） |

写入后可选：若项目要求 wiki 合规，提示后续 `wiki-checkpoint`（仲裁 Agent 至少保证 P1 行已落盘）。

### 步骤 6：更新完成契约决策矩阵

打开完成契约，更新（权威字段对齐 `completion-contract`）：

**决策矩阵**追加或更新一行：

```markdown
| {N} | {决策点} | {选定的执行决策} | arbitration | {high|med|low} |
```

- `来源` 列使用 `arbitration`（可与 PRD|P1|wiki|inferred 并存于历史行；本行固定 arbitration）
- 同步 `最后更新` 时间戳

**未决项**：将对应问题从 `open` → `resolved`，处理方式写仲裁摘要 + P1 关联。

```markdown
| {N} | {原问题} | resolved | decision-arbiter：{一句话决策}；P1 已写 |
```

若因目标级互斥无法仲裁：未决项保持 `open`，**不得**勾选硬门槛「无未决冲突」，并交 `auto-recovery` / failure-report。

### 步骤 7：返回继续执行决策

向调用方（执行 Agent 或 auto-recovery）返回固定结构，便于直接续跑：

```text
=== Decision Arbiter ===
决策点：{名称}
矛盾类型：{类型}
选定决策：{可执行的具体决策}
置信度：high | med | low
依据：P1={摘要或无}；L6={摘要或无}；PRD边界={未改目标}
P1 写入：wiki/P1-产品决策日志.md（来源=arbitration）
完成契约：{CONTRACT_PATH}（决策矩阵已更新；未决项 open→resolved 或仍 open）
可否继续执行：是 | 否（目标级互斥需用户修 PRD）
下一步：{执行 Agent 应立即做的 1–3 条动作}
```

- **可否继续执行=是** → 调用方按「下一步」继续，并视需要重跑 `gatekeeper`
- **=否** → 不得 realization 强行过门；走 failure-report / 通知用户修 PRD

## delegate_task 调用模板

执行 Agent 或 `auto-recovery`（类别 B）**应派出独立决策仲裁 Agent**，禁止执行 Agent 在无落盘 P1/契约的情况下口头消红。

```text
delegate_task(
  goal="作为独立决策仲裁 Agent，仲裁 PRD 矛盾/缺口并写入 P1 与完成契约",
  context="""
  项目根：{ROOT}
  完成契约：{CONTRACT_PATH}
  Goal 文档：{GOAL_PATH}
  PRD：{PRD_PATH}
  触发阶段/门禁：{STAGE}
  矛盾/缺口：
  {CONFLICT_STATEMENT}
  必读：
  - decision-arbiter skill（本 skill 全文算法）
  - wiki/P1-产品决策日志.md
  - wiki/L6-经验录.md
  - 完成契约决策矩阵与未决项
  硬约束：
  - 禁止改 PRD 目标与已冻结验收场景
  - 只能细化执行决策
  - 写入 P1 时 来源=arbitration，内容含置信度；标签=✅决策 或 🎨偏好
  - 更新完成契约决策矩阵；未决项 open→resolved（若可裁决）
  输出：
  - 更新后的 P1 行已落盘
  - 完成契约已更新
  - 按 decision-arbiter「=== Decision Arbiter ===」块返回
  返回：可否继续执行 + 具体决策 + 置信度
  """
)
```

### 占位符

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `{ROOT}` | 项目根绝对路径 | `/root/workspace/agent-ecoradar` |
| `{CONTRACT_PATH}` | 完成契约路径 | `docs/superpowers/contracts/2026-07-19-health-endpoint-contract.md` |
| `{GOAL_PATH}` | Goal 文档路径 | `docs/superpowers/goals/...` |
| `{PRD_PATH}` | PRD 路径 | `docs/.../prd.md` 或 kit examples |
| `{STAGE}` | 触发阶段 | `intake` / `implement` / `evidence` 等 |
| `{CONFLICT_STATEMENT}` | 步骤 1 矛盾陈述全文 | 方 A vs 方 B |

### 调用方规则

1. 收到返回后**核对** P1 与完成契约文件是否已写（不信任纯对话）。
2. 若 `可否继续执行=是`：按「下一步」执行，再经 `gatekeeper`（禁止自检放行）。
3. 若 `=否` 或仲裁 Agent 未写 P1：视为类别 B 未解决 → `auto-recovery` 换策略或 failure-report。
4. 仲裁 Agent **不实现功能代码**；实现仍由项目搭建 / 执行 Agent 完成。

## 与 auto-recovery 联动

| 环节 | 行为 |
|------|------|
| 失败分类 | `auto-recovery` 步骤 2 判为 **B. PRD 矛盾/缺口** 时，**必须**加载/调用本 skill |
| 策略摘要示例 | `delegate decision-arbiter 仲裁端口冲突并写 P1` |
| 禁止 | 类别 B 时改 PRD 目标、删验收场景、或 Phase 未装本 skill 时硬编造决策 |
| Phase 0 无本 skill | auto-recovery 写 failure-report，标明「需 decision-arbiter / 人工仲裁」 |
| 仲裁成功后 | auto-recovery 将已试方法结果更新，**重跑对应 gatekeeper** |
| 仲裁失败（目标互斥） | 保持未决 open → 策略穷尽路径 / 通知用户修 PRD；**不阻塞其他任务** |

**路由口诀：** 技术失败 → A 自修；**PRD 矛盾/缺口 → 本 skill**；环境缺失 → C 报告。

## 与其他 skill 的关系

| Skill | 关系 |
|-------|------|
| `auto-recovery` | 类别 B 的处理出口；本 skill 是其委托目标 |
| `completion-contract` | 决策矩阵与未决项的权威落盘处；仲裁后 open→resolved |
| `gatekeeper` | 矛盾/缺口类 FAIL 经 recovery 路由到本 skill；仲裁后须重验 |
| `goal-document` / Goal 模式 | 不可改边界仍高于仲裁；仲裁只填执行空隙 |
| `project-wiki` / `wiki-checkpoint` | P1/L6 读写规范；仲裁写 P1 后可触发检查点 |
| `pre-grill` | 启动前不可行应回到用户修 PRD，不滥用运行期仲裁绕过可行性 |

## 输出与落盘检查清单

- [ ] 矛盾双方已陈述（类型明确）
- [ ] 已查 P1（偏好 + 时间线）与 L6
- [ ] 推断含置信度 high/med/low
- [ ] `wiki/P1-产品决策日志.md` 追加行：标签 ✅决策 或 🎨偏好，**来源=arbitration**，内容含置信度
- [ ] 完成契约决策矩阵已更新；相关未决项 resolved（或明确仍 open）
- [ ] **未**改 PRD 目标 / **未**删降冻结场景
- [ ] 返回 `=== Decision Arbiter ===` 块且「下一步」可执行
- [ ] 调用方将重跑门禁（若来自 FAIL）

## 常见陷阱

1. **改 PRD 目标消矛盾** — 禁止；只能执行层细化或请用户改 PRD  
2. **只在对话里裁决、不写 P1** — 违反 D15；后续会话无法继承  
3. **来源写成 inferred/讨论 而非 arbitration** — 审计断裂；必须 `arbitration`  
4. **置信度 low 却当 high 扩 scope** — low 必须选可逆、最小默认  
5. **目标级互斥仍返回继续执行=是** — 应否并 failure-report  
6. **仲裁 Agent 顺手写业务代码** — 越权；只写 P1 + 契约 + 返回决策  
7. **技术失败误走仲裁** — 应交回 auto-recovery 重分类 A  
8. **删除已冻结验收场景** — 禁止；仅可 `冻结=后增` 补隐含缺口场景  

## 验证清单

- [ ] frontmatter `name: decision-arbiter`
- [ ] 职责仅限 PRD 矛盾/缺口；明确禁止改 PRD 目标
- [ ] 仲裁算法 7 步完整且可按序执行
- [ ] P1 写入规则含标签、来源=arbitration、置信度
- [ ] 完成契约决策矩阵 + 未决项更新规则齐全
- [ ] `delegate_task` 模板与占位符齐全
- [ ] 与 `auto-recovery` 类别 B 联动说明明确
- [ ] 返回块含「可否继续执行」与具体下一步

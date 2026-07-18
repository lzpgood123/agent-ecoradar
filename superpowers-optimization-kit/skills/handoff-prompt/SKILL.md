---
name: handoff-prompt
description: Use when design+plan are ready for a new conversation (Mode A launch prompt), or when starting/resuming full-auto Goal delivery (Mode B Goal launch card). Mode B is preferred for unattended runs; Mode A is the semi-manual fallback.
---

# Handoff Prompt — 启动提示词 / Goal 启动卡

## 概述

本 skill 提供两种交接模式：

| 模式 | 名称 | 用途 | 优先级 |
|------|------|------|--------|
| **B** | Goal 模式启动卡 | 全自动：确认准备清单 → 打开 Goal → `/goal` 声明 | **全自动优先** |
| **A** | 复制到新对话 | 半人工：7 步启动提示词，用户粘贴到新会话 | 半人工回退 |

**默认选择：** 已有（或即将生成）Goal 文档、用户要无人值守交付 → **模式 B**。无 Goal、仅 spec/plan 人工交接 → **模式 A**。

提示词 / 启动卡都是「路由指南」——告诉执行方读什么、按什么顺序做、边界在哪——**不重复** spec/plan/Goal 中的技术细节。

## 何时使用

- 方案设计完成 spec+plan 后，需要交给新对话执行（模式 A）
- pre-grill / goal-document 完成后，需要给用户一份可执行的 `/goal` 启动说明（模式 B）
- 用户说「启动提示词」「交接 prompt」「Goal 怎么开跑」「handoff」
- 全自动链路中断后，需要重新给出启动卡（模式 B）

**不适用：**

- 设计尚未完成（先 brainstorming / pre-grill）
- 任务简单到不需要 spec/plan/Goal（当前对话直接做完）
- 写给人读的进度 handoff 文档（非 agent 执行路由）

## 核心原则

1. **路由指南，不是技术文档** — 引用路径，不复制正文
2. **全自动优先 B，A 为半人工回退** — 勿在已有 Goal 时仍只给模式 A
3. **双输出：对话 + 文件** — 对话可复制；同时归档到 `docs/superpowers/handoff/`
4. **边界 > 细节** — 「不能改什么」比「怎么实现」更重要
5. **模式 B 不跳门禁** — 启动卡必须写明：运行期 6 门禁不可跳；失败看 `failures/`

---

## 模式 B：Goal 模式启动卡（全自动优先）

### 何时用模式 B

- 已有 Goal 文档：`docs/superpowers/goals/YYYY-MM-DD-<topic>-goal.md`
- 用户刚完成 pre-grill 准备清单确认
- 用户要求 `/goal` 无人值守

### 生成时机

`goal-document` 完成后（或用户请求「怎么启动 Goal」时）**自动或按需**生成本启动卡。

1. **保存到文件** — `docs/superpowers/handoff/YYYY-MM-DD-<topic>-goal-launch.md`
2. **输出在对话中** — 供用户确认清单后执行 `/goal`

### 模式 B 输出模板

```
# Goal 模式启动卡：{任务名称}

> 全自动优先路径。确认准备清单后，用下方 `/goal` 声明启动无人值守。

---

## 1. 确认准备清单（全部勾选后再 /goal）

打开 Goal 文档中的「准备清单」并逐项确认，至少包括：

- [ ] PRD 路径可读：`{PRD 路径}`
- [ ] Goal 文档已确认：`{Goal 路径}`
- [ ] 完成契约骨架存在：`{契约路径}`
- [ ] 环境 / 权限 / 配置就绪（见 Goal 准备清单）
- [ ] Hermes Goal 模式可用；建议 `goals.max_turns` ≥ 100
- [ ] 用户已明确允许无人值守（YOLO / 等效授权，按项目约定）

未完成清单 → **禁止**启动 `/goal`，退回 `pre-grill` 或补齐环境。

## 2. 打开 Goal 文档（执行 Agent 第一步）

`/goal` 启动后，执行 Agent **第一步必须全文阅读**：

`{Goal 路径}`

Goal 是唯一主指令。完成契约权威副本：

`{契约路径}`

## 3. /goal 声明（用户触发）

    /goal 根据 Goal 文档 {Goal 路径} 无人值守完成：{一句话 Goal 声明}

将上述整行交给用户执行；Agent **不代替用户**偷偷启动。

## 4. 运行期硬规则（不可跳门禁）

1. 固定 6 阶段顺序，每阶段结束必须 `gatekeeper` + `delegate_task` 独立校验
2. 执行 Agent **不得自检放行**
3. 门禁 FAIL → `auto-recovery`（策略旋转）；禁止跳过、禁止自降门槛
4. PRD 矛盾/缺口 → `decision-arbiter`（**不改 PRD 目标**）
5. 宣布完成仅当完成契约硬门槛 **4/4 全绿** 且 `可否宣布完成=是`
6. 阶段 5 必须跑 `wiki-checkpoint`；通过报告路径写入完成契约证据

阶段顺序：Intake → Spec+Plan → 实现 → 验收证据 → Wiki/合规 → 完成门

## 5. 失败时看哪里

| 类型 | 路径 |
|------|------|
| 门禁报告 | `docs/superpowers/gates/` |
| 失败 / 策略穷尽 | `docs/superpowers/failures/` |
| 完成契约（进度与已试方法） | `{契约路径}` |
| Goal 主指令 | `{Goal 路径}` |

策略穷尽时：**不宣称完成**；保持契约 `可否宣布完成=否`，以 failures 报告收尾。

## 6. 关键约束（摘要）

{从 Goal「不可改边界」与 PRD 摘 2–5 条；细节以 Goal/PRD 为准}

## 7. 回退

若无法使用 Goal 模式，改用本 skill **模式 A**（半人工 7 步启动提示词）——需已有 spec/plan。
```
### 模式 B 填充指南

| 字段 | 来源 |
|------|------|
| 任务名称 | Goal / PRD 标题 |
| PRD / Goal / 契约路径 | goal-document 输出的真实路径 |
| 一句话 Goal 声明 | Goal 文档顶部声明 |
| 关键约束 | Goal「不可改边界」+ PRD 非目标 |

---

## 模式 A：复制到新对话（半人工回退）

### 何时用模式 A

- 无 Goal 文档，只有 spec + plan
- 用户明确要求「复制到新对话」的 7 步提示词
- 全自动不可用时的半人工回退

### 生成时机

方案设计 agent 在 `writing-plans` 完成后可加载本技能生成模式 A 提示词：

1. **保存到文件** — `docs/superpowers/handoff/YYYY-MM-DD-<topic>-agent-prompt.md`
2. **输出在对话中** — 供用户复制粘贴

### 模式 A 输出模板

```
# 新对话 Agent 启动提示词：{任务名称}

> 将以下全部内容复制粘贴到新对话中作为第一条消息。
> （半人工模式 A。若已有 Goal 文档，优先改用模式 B / `/goal`。）

---

## 你的任务

你是"{项目名称}"项目的开发 Agent。你的任务是实现**{任务简述}**。

## 第零步：加载 Superpowers 技能框架

**这是不可跳过的第一步。** 立即调用 Skill 工具加载 `using-superpowers` 技能。这是你在该项目中工作的前置要求——不加载此技能，后续所有步骤将无法正确执行。

以下技能将在各阶段按需加载：
- `using-superpowers` → 第零步，立即加载
- `test-driven-development` → 第五步执行实现时加载
- `verification-before-completion` → 第六步验证时加载
- `wiki-checkpoint` → 第七步更新 Wiki 后加载

## 第二步：阅读项目上下文

按 `wiki/README.md` 的阅读路线图理解项目，必读：

1. `wiki/README.md` — 项目总索引和阅读路线图
2. `wiki/L1-全景.md` — 项目是什么、核心流程
3. `wiki/L3-代码地图.md` — 代码在哪、改哪个文件
4. `wiki/P1-产品决策日志.md` — 用户偏好和产品约束
5. `wiki/L6-经验录.md` — 相关坑和注意事项

按任务类型选读：
- 前端任务 → 加读 `wiki/L4A-前端详解.md`
- 后端任务 → 加读 `wiki/L4B-后端详解.md` + `wiki/L5-接口契约.md`
- 全栈任务 → 上述全部

## 第三步：阅读设计文档

1. `{spec 路径}` — **本次实现的设计文档（核心）**
2. `{plan 路径}` — 实现计划（如有）

## 第四步：创建实现计划

{如果 plan 已存在，写"实现计划已存在于 `{plan 路径}`，直接按计划执行。"}
{如果 plan 不存在，写"调用 `writing-plans` 技能，基于设计文档创建实现计划，保存到 `docs/superpowers/plans/`。"}

## 第五步：执行实现

使用 `subagent-driven-development` 技能执行实现计划。每个子 Agent 必须遵循 TDD——先加载 `test-driven-development` 技能，先写测试再写实现。

{如果有多任务建议拆分，在此列出}

## 第六步：验证

调用 `verification-before-completion` 技能进行验证：

{列出验证项，从 spec 中提取}

## 第七步：更新 Wiki

开发完成后，按 wiki 各文档底部的"更新指引"更新：
{列出需要更新的 wiki 文档，从 spec 中判断影响范围}

更新完成后，加载 `wiki-checkpoint` 技能，确认读/写合规并输出合规报告。

## 关键约束

{从 spec 和 P1-产品决策日志提取的硬约束，2-5 条}

## 不能改动的部分

{从 spec 和 L2-架构 提取的不可变区域}

## 项目环境信息

- 操作系统：{从当前环境获取}
- Python：{版本}
- 后端启动：{命令}
- 后端测试：{命令}
- 当前 AI 模型：{从 .env 或 config.py 提取}

## 注意事项

{从 P1-产品决策日志的用户偏好 + L6-经验录的相关坑中提取}
```

### 模式 A 填充指南

| 字段 | 信息来源 | 说明 |
|------|---------|------|
| 任务名称 | spec 标题 | 简短描述 |
| 项目名称 | wiki/L1-全景 产品定位 | 如有 |
| 任务简述 | spec 核心功能概述 | 一句话 |
| spec / plan 路径 | 实际文件路径 | 相对项目根 |
| 验证项 | spec 验收标准 | 每条一行 |
| wiki 更新列表 | 影响范围 | 前端/后端/接口/经验 |
| 关键约束 | spec + P1 | 2-5 条 |
| 不可变部分 | spec + L2 | 逐条列出 |
| 环境信息 | 当前运行环境 | 勿写死过期值 |
| 注意事项 | P1 + L6 | 逐条列出 |

---

## 模式选择决策

```
有 PRD 且要无人值守？
  ├─ 是 → pre-grill → goal-document → 【模式 B】
  └─ 否 → 仅有 spec/plan 人工交接？
        ├─ 是 → 【模式 A】
        └─ 当前对话可做完 → 不需要本 skill
```

## 常见错误

| 错误 | 修复 |
|------|------|
| 已有 Goal 仍只给模式 A | 全自动优先模式 B；A 仅回退 |
| 模式 B 省略「不跳门禁」 | 启动卡必须写明 6 门 + 禁止自批 |
| 模式 B 不写 failures/ 路径 | 失败时执行方必须知道看哪里 |
| 把 spec/Goal 技术细节整段复制进提示词 | 改为路径引用 |
| 忘记模式 A「第零步」using-superpowers | 新 agent 不加载框架则 TDD/验证/wiki 全失效 |
| 忘记「不能改动的部分」 | 从 spec / Goal 边界 / L2 提取 |
| 只输出对话不存文件 | 必须写入 `docs/superpowers/handoff/` |
| 代替用户执行 `/goal` | 模式 B 只输出声明；由用户触发 |

## 与其它 skill 的协作

| Skill | 关系 |
|-------|------|
| `pre-grill` | 上游可行性；模式 B 准备清单来源 |
| `goal-document` | 模式 B 的 Goal 路径与声明来源 |
| `completion-contract` / `gatekeeper` / `auto-recovery` | 模式 B 运行期引用 |
| `wiki-checkpoint` | 模式 A 第七步；模式 B 阶段 5 / 完成门证据 |
| `project-wiki` | 双方均依赖 wiki 路线图 |

## 示例

- 模式 A 参考：`docs/superpowers/handoff/2026-07-11-input-expansion-agent-prompt.md`（若仓库中存在）
- 模式 B 对照：`examples/mvp-goal-document.md` + Goal 文档内准备清单与 `/goal` 声明

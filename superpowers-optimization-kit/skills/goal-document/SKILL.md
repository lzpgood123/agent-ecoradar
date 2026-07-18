---
name: goal-document
description: Use after pre-grill deems a PRD feasible. Builds the full Goal document that drives Hermes /goal unattended execution, including stage flow, gates, recovery, and completion contract skeleton.
---

# Goal Document — Goal 文档生成

## 概述

在 pre-grill 判定 PRD **可行**之后，本 skill 生成驱动 Hermes `/goal` 无人值守执行的 **Goal 文档**。文档包含：Goal 声明、完成契约骨架、不可改边界、6 阶段流程、失败恢复策略、准备清单。

原则：

1. **Goal 文档是执行 Agent 的唯一主指令** — `/goal` 启动后第一步必须全文阅读本文件
2. **完成契约双写** — Goal 内嵌契约章节，并复制权威副本到 `docs/superpowers/contracts/`
3. **阶段门禁不可自批** — 6 阶段结束均经 `gatekeeper` + `delegate_task`；FAIL 走 `auto-recovery`
4. **不改 PRD 目标** — 只提取、结构化、标注来源，不降级、不删改目标语义

## 何时使用

- pre-grill 输出「可行」结论后，生成 Goal 文档
- 用户已有可行 PRD，直接请求「生成 Goal / 启动无人值守」
- 需要刷新 Goal 声明或契约骨架路径（任务名/topic 变更时）

**不适用：**

- PRD 尚未通过可行性分析（先跑 `pre-grill`）
- 运行期阶段推进 / 门禁校验（用 `gatekeeper` / `completion-contract`）
- 失败策略旋转（用 `auto-recovery`）

## 输入契约

执行前必须拿到：

| 输入 | 必需 | 说明 |
|------|------|------|
| PRD 路径 | 是 | 用户 PRD 文件路径（可读） |
| pre-grill 可行性结论 | 是 | 须为「可行」；含准备清单要点 |
| 决定性文件路径列表 | 否 | 规格/约束/接口等补充文件 |
| wiki / P1 | 否 | 若存在：README、L1、P1、L6（框架任务再读 P3） |
| 目标项目根 | 建议 | 默认可推断为当前仓库根 |
| topic | 建议 | 小写英文/数字/连字符；缺省从任务名/PRD 主题派生 |

若可行性结论缺失或为「不可行」→ **停止**，退回 `pre-grill`，不生成 Goal。

## 输出契约

| 输出 | 路径 / 形式 |
|------|-------------|
| Goal 文档 | `docs/superpowers/goals/YYYY-MM-DD-<topic>-goal.md` |
| Goal 声明 | 一句话，供用户 `/goal <声明>` |
| 完成契约（内嵌） | Goal 文档内 `## 完成契约` 章节 |
| 完成契约（权威副本） | `docs/superpowers/contracts/YYYY-MM-DD-<topic>-contract.md` |

目录不存在时先创建：

```text
docs/superpowers/goals/
docs/superpowers/contracts/
```

日期为生成当日 `YYYY-MM-DD`；topic 一经确定，文件名后续不因内容小改而改名。

## 模板来源

1. 优先复制 `superpowers-optimization-kit/templates/goal-document.md`
2. 若尚未安装模板：按模板一级标题顺序手写等价结构（见下方「文档结构」）
3. 契约权威副本优先对齐 `templates/completion-contract.md`（字段与 `completion-contract` skill 一致）

## 文档结构（一级标题顺序固定）

```markdown
# Goal 文档：{任务名称}

## 元信息
## Goal 声明（给 /goal）
## 完成契约
### PRD 目标清单
### 验收场景骨架
### 决策矩阵
### 未决项
### 可否宣布完成
## 不可改边界
## 阶段流程
### 阶段 1：Intake / 决策编译
### 阶段 2：Spec + Plan
### 阶段 3：实现
### 阶段 4：验收证据
### 阶段 5：Wiki / 合规
### 阶段 6：完成门
## 失败恢复策略
## 准备清单
## 变更日志
```

不得删减一级标题；阶段 1–6 必须全部出现。

## 填充算法（逐步执行，禁止跳步）

### 步骤 0：校验输入

1. 确认 PRD 路径可读
2. 确认 pre-grill 结论为**可行**
3. 读取可选决定性文件、wiki/P1（若存在）
4. 确定 `任务名称`、`topic`、`创建日期`、`目标项目根`

### 步骤 1：复制模板

1. 创建 `docs/superpowers/goals/`（如不存在）
2. 复制 `templates/goal-document.md` → `docs/superpowers/goals/YYYY-MM-DD-<topic>-goal.md`
3. 替换标题与元信息占位符：

| 字段 | 填充规则 |
|------|----------|
| 任务名称 | 来自 PRD 标题或用户给定 |
| PRD 路径 | 输入的 PRD 路径 |
| 完成契约路径 | `docs/superpowers/contracts/YYYY-MM-DD-<topic>-contract.md` |
| 创建日期 | 当日 |
| 创建来源 | `pre-grill + goal-document` |
| 目标项目根 | 项目根路径 |
| 决定性文件 | 可选列表；无则写「无」或仅 PRD |

### 步骤 2：提取目标 → PRD 目标清单

1. 从 PRD 提取**可测**目标（功能/验收条款拆成独立行）
2. 每行：`# | 目标 | 来源=PRD | 覆盖状态=pending | 证据路径=空`
3. **禁止**改写目标语义；可把长句拆成多条可测目标
4. 非目标不要写入目标清单（写入「不可改边界」）

### 步骤 3：场景 → 验收场景骨架

1. 来源优先级：PRD 验收条款 → P1/wiki 补充 → 每项目标至少 1 条隐含场景（标注 inferred 时可在决策矩阵说明）
2. 每行：`场景 | 类型(功能/回归/合规) | 证据要求 | 状态=pending | 证据路径=空 | 冻结=是`（骨架阶段可写 `骨架`，Intake 后统一冻结为 `是`）
3. 证据要求必须可操作（命令、产物类型），禁止「验证通过」空话

### 步骤 4：决策矩阵

1. 列出实现前需锁定的决策点（接口形状、范围边界、落点模块等）
2. **来源标注**必须是：`PRD` | `P1` | `wiki` | `inferred` 之一（可组合，如 `PRD + wiki`）
3. 置信度：`high` | `medium` | `low`
4. `inferred` 项须可在 Intake 复核；冲突写入未决项

### 步骤 5：不可改边界

写入至少四类：

1. **PRD 目标不可改写、不可降级、不可删除**
2. **非目标**（来自 PRD）
3. **项目约束**（环境/权限/模块边界/部署等，来自 PRD、wiki、决定性文件）
4. **禁止**：改 Hermes 源码、改无关业务模块、伪造测试/证据、跳过门禁自批、删除已冻结验收场景

### 步骤 6：粘贴 6 阶段流程

以模板「阶段流程」为底，**必须显式引用**下列 skill 名：

| 阶段 | 必须引用 |
|------|----------|
| 全文总则 | `gatekeeper`、`delegate_task`、`auto-recovery` |
| 阶段 1 Intake | `completion-contract`、`gatekeeper`；（矛盾时）`decision-arbiter` |
| 阶段 2 Spec+Plan | `gatekeeper` |
| 阶段 3 实现 | `gatekeeper` |
| 阶段 4 验收证据 | `gatekeeper` |
| 阶段 5 Wiki/合规 | `wiki-checkpoint`、`gatekeeper` |
| 阶段 6 完成门 | `completion-contract` 硬门槛、`gatekeeper`；向 goal judge 显式声明完成 |

硬规则写进文档正文：

- 每阶段结束必须 `gatekeeper` + `delegate_task` 独立子 Agent
- 执行 Agent **不得自检放行**
- FAIL → `auto-recovery`

### 步骤 7：失败恢复策略

至少包含：

1. 门禁 FAIL / 测试失败 / 实现失败 → 加载 `auto-recovery`
2. 读完成契约「已试方法」；新策略摘要不得与已试相同
3. PRD 矛盾/缺口 → `decision-arbiter`（写入 P1）；环境/权限缺失 → 失败报告，不扩 scope
4. 策略穷尽 → `templates/failure-report.md` → `docs/superpowers/failures/`，通知用户，不阻塞其他任务
5. 禁止原地重复同一失败方法；禁止跳过门禁

### 步骤 8：准备清单（来自 pre-grill）

把 pre-grill 清单落入 Goal，并**强制包含**：

- [ ] PRD 路径可读且目标可测
- [ ] 所需环境/依赖/端口/密钥已就绪
- [ ] 权限足够（读仓库、跑测试、写 `docs/superpowers/`）
- [ ] Hermes Goal 模式可用；建议 **`goals.max_turns` ≥ 100**
- [ ] 是否启用 YOLO/自动批准工具已明确
- [ ] 相关 wiki（若存在）可读：README、L1、P1、L6

用户确认完成后再启动 `/goal`。

### 步骤 9：生成 Goal 声明

格式固定：

```text
根据 Goal 文档 {path} 无人值守完成：{一句话}
```

- `{path}` = Goal 文档相对项目根路径（如 `docs/superpowers/goals/2026-07-19-health-endpoint-goal.md`）
- `{一句话}` = 可测交付摘要（来自 PRD 核心目标）

写入 `## Goal 声明（给 /goal）` 代码块。

### 步骤 10：双写完成契约

1. Goal 内 `## 完成契约` 已填骨架（目标/场景/决策/未决/可否宣布完成=否）
2. 创建 `docs/superpowers/contracts/`（如不存在）
3. 复制/写入权威副本 `docs/superpowers/contracts/YYYY-MM-DD-<topic>-contract.md`：
   - 结构遵循 `completion-contract` skill / `templates/completion-contract.md`
   - 同步 PRD 目标、验收场景、决策矩阵、未决项
   - 硬门槛四项未勾选；`可否宣布完成=否`
   - `关联 Goal` / `关联 PRD` 填路径；`当前阶段` 可为 Intake 前或空
4. 运行期更新以 **contracts 副本** 为准；Goal 内嵌章节为初始化快照

### 步骤 11：变更日志与落盘

1. 变更日志追加：`YYYY-MM-DD | 初始化 Goal 文档 | goal-document`
2. 写回 Goal 文件与契约文件
3. 输出固定格式块（见下）

## 与 Hermes Goal 模式映射

| Hermes 侧 | 本 skill 产出 / 约定 |
|-----------|----------------------|
| `/goal` 文本 | = Goal 声明（`根据 Goal 文档 {path} 无人值守完成：{一句话}`） |
| 执行 Agent 第一步 | **必须** `read` Goal 文档**全文**（不得只读声明） |
| 阶段门禁 | 用 `gatekeeper` + `delegate_task`；执行 Agent 禁止自检放行 |
| 最终完成 | 契约硬门槛 4/4 全绿且 `可否宣布完成=是` 后，**显式声明完成**，供 goal judge 判 done |
| 回合预算 | 准备清单写明建议 **`goals.max_turns` ≥ 100** |
| 失败 | `auto-recovery`；穷尽则失败报告，不伪造成功 |

用户启动示例：

```text
/goal 根据 Goal 文档 docs/superpowers/goals/YYYY-MM-DD-<topic>-goal.md 无人值守完成：{一句话}
```

## 输出格式（强制）

生成成功后必须在对话中输出：

```text
=== Goal 文档已生成 ===
Goal 路径：docs/superpowers/goals/YYYY-MM-DD-<topic>-goal.md
契约路径：docs/superpowers/contracts/YYYY-MM-DD-<topic>-contract.md
Goal 声明：根据 Goal 文档 docs/superpowers/goals/YYYY-MM-DD-<topic>-goal.md 无人值守完成：{一句话}
下一步：用户确认准备清单后执行 /goal <上述声明>
建议：goals.max_turns ≥ 100
```

## 与其它 skill 的协作

| Skill | 关系 |
|-------|------|
| `pre-grill` | 上游；可行后触发本 skill；准备清单来源 |
| `completion-contract` | 契约权威格式与运行期更新；本 skill 只建骨架并双写 |
| `gatekeeper` | Goal 阶段流程嵌入 6 门禁；运行期独立校验 |
| `auto-recovery` | 失败恢复策略章节引用；门禁 FAIL 去向 |
| `decision-arbiter` | 矛盾/缺口仲裁（Intake / recovery 路由） |
| `wiki-checkpoint` | 阶段 5 合规检查 |
| `handoff-prompt` | 兼容旧 handoff；Goal 模式优先本文件 |

## 红线

1. pre-grill 未判可行就生成 Goal
2. 改写/删除/降级 PRD 目标
3. 缺少 6 阶段任一节或未引用 gatekeeper / completion-contract / auto-recovery
4. 只写 Goal 不写 `contracts/` 权威副本（或反之只写契约无 Goal）
5. Goal 声明路径与真实文件路径不一致
6. 暗示执行 Agent 可自检放行门禁
7. 准备清单省略 `goals.max_turns ≥ 100`

## 验证清单

- [ ] frontmatter `name: goal-document`
- [ ] 输入含 PRD、可选决定性文件、wiki/P1、pre-grill 可行结论
- [ ] 输出路径为 `docs/superpowers/goals/YYYY-MM-DD-<topic>-goal.md`
- [ ] 存在 Goal 声明供 `/goal` 使用
- [ ] Goal 内嵌完成契约章节，且已复制到 `contracts/`
- [ ] 填充算法覆盖：模板 → 目标 → 场景 → 决策矩阵 → 边界 → 6 阶段 → 失败恢复 → 准备清单
- [ ] 6 阶段引用 `gatekeeper` / `completion-contract` / `auto-recovery`（及 wiki-checkpoint / decision-arbiter 按需）
- [ ] 映射说明：`/goal` 文本、第一步读全文、门禁 `delegate_task`、`goals.max_turns` ≥ 100
- [ ] 输出 `=== Goal 文档已生成 ===` 块

## 快速检查清单（执行本 skill 时）

- [ ] 已读 PRD + pre-grill 可行结论
- [ ] 已复制模板并填满固定章节
- [ ] 目标/场景/决策/边界来源可追溯
- [ ] 双写 Goal + contracts
- [ ] Goal 声明可直接粘贴到 `/goal`
- [ ] 准备清单含 max_turns 建议
- [ ] 已输出固定格式块

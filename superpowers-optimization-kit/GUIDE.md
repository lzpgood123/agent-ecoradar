# Superpowers Optimization Guide

> 本文档供**框架讨论 Agent** 执行。每项优化明确列出需要修改的文件和具体操作。
> 读完本文档后，你**必须逐项执行**以下操作，不可跳过。
> 角色说明详见 `ROLES.md`。执行前请先加载 `superpowers-optimizer` skill 作为入口。

---

## 执行前检查

在开始前，确认以下文件存在：

- `.trae/rules/superpowers-zh.md` — superpowers 技能框架
- `AGENTS.md` — 项目级 Agent 规则

如果不存在，先安装 superpowers-zh 框架。

---

## 优化一：Wiki 体系

**目标：** 让每个新 Agent 进入项目时，自动按路线图阅读 wiki，而非从零读代码。

### 操作 1.1：复制 skill 文件

将 `skills/project-wiki/SKILL.md` 复制到 `.trae/skills/project-wiki/SKILL.md`。

```bash
mkdir -p .trae/skills/project-wiki
cp skills/project-wiki/SKILL.md .trae/skills/project-wiki/SKILL.md
```

### 操作 1.2：修改 superpowers-zh.md

在 `.trae/rules/superpowers-zh.md` 中做两处修改：

**修改 A —— 更新技能数：**

找到：
```
你已加载 superpowers-zh 技能框架（XX 个 skills）。
```
将 `XX` 改为 `XX + 1`（即原有数量 +1）。

**修改 B —— 在 skill 表格中添加一行：**

在 `| finishing-a-development-branch | ...` 和 `| mcp-builder | ...` 之间插入：
```
| project-wiki | 当初始化新项目文档体系、构建跨 Agent 项目全息手册、或用户要求"构建wiki"、"初始化项目手册"、"生成项目文档"时使用。一次性构建 wiki/ 目录 + 写入 AGENTS.md 维护规则 |
```

### 操作 1.3：修改 AGENTS.md

在 `AGENTS.md` 中，找到 `### 阅读顺序` 章节，在其后新增一个 `### 项目手册（Wiki）` 章节。

**注意：** 如果 AGENTS.md 中已有「项目手册（Wiki）」章节，跳过此操作。AGENTS.md 的 wiki 章节将在此后的「优化三：Wiki Checkpoint」中被替换为强化版本。

插入以下内容：

```markdown
### 项目手册（Wiki）

新对话进入项目时，优先按 `wiki/README.md` 的阅读路线图理解项目。wiki 是分层级、自顶向下的项目全息手册，11 个文档覆盖从全景到产品方向的全部维度。开发完成后，按 wiki 各文档底部的"更新指引"更新对应文档。

\`\`\`
wiki/
├── README.md           # 总索引 + 阅读路线图
├── L1-全景.md           # 项目是什么
├── L2-架构.md           # 系统怎么搭的
├── L3-代码地图.md       # 代码在哪
├── L4A-前端详解.md       # 前端怎么改
├── L4B-后端详解.md       # 后端怎么改
├── L5-接口契约.md       # 数据怎么流
├── L6-经验录.md         # 踩过什么坑
├── P1-产品决策日志.md     # 产品往哪走（方案设计 agent 维护）
├── P2-功能扩展路线图.md   # 待实现功能规划（方案设计 agent 维护）
└── P3-框架演进.md         # 框架怎么变（框架讨论 agent 维护）
\`\`\`
```

### 操作 1.4：初始化 Wiki

加载 `project-wiki` skill，让 Agent 自动创建 wiki 目录、派子 Agent 分析项目、填充 11 篇文档。

**提示：** 此操作只需执行一次。之后 wiki 由 AGENTS.md 规则自动维护。

---

## 优化二：Handoff Prompt

**目标：** 方案设计 agent 完成 spec+plan 后，自动生成可直接复制到新对话的启动提示词。

### 操作 2.1：复制 skill 文件

将 `skills/handoff-prompt/SKILL.md` 复制到 `.trae/skills/handoff-prompt/SKILL.md`。

```bash
mkdir -p .trae/skills/handoff-prompt
cp skills/handoff-prompt/SKILL.md .trae/skills/handoff-prompt/SKILL.md
```

### 操作 2.2：修改 superpowers-zh.md

在 `.trae/rules/superpowers-zh.md` 中做两处修改：

**修改 A —— 更新技能数：**

找到：
```
你已加载 superpowers-zh 技能框架（XX 个 skills）。
```
将 `XX` 改为 `XX + 1`（即原有数量 +1）。

**修改 B —— 在 skill 表格中添加一行：**

在 `| finishing-a-development-branch | ...` 和 `| mcp-builder | ...` 之间插入：
```
| handoff-prompt | 当设计文档和实现计划完成后，需要生成一份可在新对话中执行的启动提示词时使用。方案设计 agent 自动加载，生成 7 步路由指南，输出在对话中供用户复制 |
```

---

## 优化三：Wiki Checkpoint

**目标：** 在声称工作完成前，自动检查 wiki 读/写合规，未通过不可声称完成。

### 操作 3.1：复制 skill 文件

将 `skills/wiki-checkpoint/SKILL.md` 复制到 `.trae/skills/wiki-checkpoint/SKILL.md`。

```bash
mkdir -p .trae/skills/wiki-checkpoint
cp skills/wiki-checkpoint/SKILL.md .trae/skills/wiki-checkpoint/SKILL.md
```

### 操作 3.2：修改 superpowers-zh.md

在 `.trae/rules/superpowers-zh.md` 中做三处修改：

**修改 A —— 更新技能数：**

找到：
```
你已加载 superpowers-zh 技能框架（XX 个 skills）。
```
将 `XX` 改为 `XX + 1`。

**修改 B —— 在 skill 表格中添加一行：**

在 `| verification-before-completion | ...` 和 `| workflow-runner | ...` 之间插入：
```
| wiki-checkpoint | 在声称工作完成前使用，检查 wiki 读/写合规——确认已读必读文档、已更新应更新的文档，输出合规报告 |
```

**修改 C —— 新增第 5 条核心规则：**

在核心规则列表末尾追加：
```
5. **Wiki 优先** — 进入项目先读 `wiki/README.md` 路线图理解项目；完成工作后按 wiki 各文档底部的「更新指引」更新对应文档；发现新坑立即追加到 `wiki/L6-经验录.md`
```

### 操作 3.3：强化 AGENTS.md 的 wiki 章节

将 AGENTS.md 中 `### 项目手册（Wiki）` 章节**完整替换**为以下内容：

```markdown
### 项目手册（Wiki）

**Wiki 是项目的唯一真相源。** 新 Agent 进入项目时不从零读代码，而是按 wiki 路线图理解项目。所有 Agent 必须遵守以下规则：

#### 进入规则（所有 Agent，不可跳过）

1. 进入项目后，**第一步**读 `wiki/README.md`，找到自己角色的阅读路线
2. 按路线图读 3-5 个文档，建立项目心智模型，**然后**才开始工作
3. 禁止跳过 wiki 直接读代码——除非 wiki 中不存在相关信息

#### 各角色必读清单

| 角色 | 必读文档 | 时机 |
|------|---------|------|
| 方案设计 Agent | P1-产品决策日志（了解用户偏好和历史决策）→ L1-全景（了解产品现状） | 讨论前 |
| 项目搭建 Agent | L3-代码地图（定位文件）→ L6-经验录（避坑）→ 按任务选读 L4A/L4B/L5 | 开发前 |
| 框架讨论 Agent | P3-框架演进（了解历史变更）→ L2-架构（了解技术边界） | 讨论前 |

#### 更新规则（开发者，不可跳过）

开发完成后，**必须**按以下对应关系更新 wiki：

| 变更类型 | 更新文档 | 更新内容 |
|---------|---------|---------|
| 新增/删除文件 | L3-代码地图 | 文件列表和功能说明 |
| 前端代码变更 | L4A-前端详解 | 函数列表、CSS 变量、交互逻辑 |
| 后端代码变更 | L4B-后端详解 | 路由、Pydantic 模型、AI 适配层 |
| API 接口变更 | L5-接口契约 | 接口契约、State 结构 |
| 发现新坑/修复 Bug | L6-经验录 | **立即追加**，不等开发完成 |
| 项目状态变化 | L1-全景 | 当前版本、功能摘要 |
| 方案设计讨论 | P1-产品决策日志 | 新想法、决策、偏好（讨论后追加） |
| 框架变更 | P3-框架演进 | 框架快照 + 变更时间线 |

#### 更新原则

- **即时更新** — L6-经验录发现即记录，不等阶段结束
- **谁变更谁更新** — 项目搭建 agent 更新 L1/L3/L4/L5，方案设计 agent 更新 P1，框架讨论 agent 更新 P3
- **更新后自查** — 加载 `wiki-checkpoint` skill 确认合规

\`\`\`
wiki/
├── README.md           # 总索引 + 阅读路线图
├── L1-全景.md           # 项目是什么
├── L2-架构.md           # 系统怎么搭的
├── L3-代码地图.md       # 代码在哪
├── L4A-前端详解.md       # 前端怎么改
├── L4B-后端详解.md       # 后端怎么改
├── L5-接口契约.md       # 数据怎么流
├── L6-经验录.md         # 踩过什么坑
├── P1-产品决策日志.md     # 产品往哪走（方案设计 agent 维护）
├── P2-功能扩展路线图.md   # 12 个待实现功能规划（方案设计 agent 维护）
└── P3-框架演进.md         # 框架怎么变（框架讨论 agent 维护）
\`\`\`
```

---

## 技能安装目录检测（优化四~九通用）

从优化四起，skill 安装目录**不要写死**。按以下顺序检测并导出 `SKILLS_DIR`：

```bash
# 优先 Hermes，否则 Trae
if [ -d .hermes/skills ] || [ -d .hermes ]; then
  SKILLS_DIR=".hermes/skills"
elif [ -d .trae/skills ] || [ -d .trae ]; then
  SKILLS_DIR=".trae/skills"
else
  # 默认走 Hermes 约定；若项目只用 Trae，可改为 .trae/skills
  SKILLS_DIR=".hermes/skills"
fi
mkdir -p "$SKILLS_DIR"
echo "Using SKILLS_DIR=$SKILLS_DIR"
```

规则：
- 若存在 `.hermes/skills` 或 `.hermes/` → 使用 `.hermes/skills`
- 否则若存在 `.trae/skills` 或 `.trae/` → 使用 `.trae/skills`
- 两者都没有 → 创建并使用 `.hermes/skills`（除非用户明确要求 Trae）
- 下文所有 `cp skills/<name>/... "$SKILLS_DIR/<name>/..."` 均指该检测结果
- 优化一~三若目标项目已是 Hermes，也应改用同一 `SKILLS_DIR`（历史文档写的是 `.trae/skills`，以检测结果为准）

技能表文件同理：
- Hermes 项目：优先更新 `HERMES.md`（若存在）或 `.hermes/rules/superpowers-zh.md` / 项目内 `superpowers-zh` 规则文件
- Trae 项目：更新 `.trae/rules/superpowers-zh.md`
- 项目级规则：`AGENTS.md`（若存在）

下文用 `RULES_FILE` 指「当前项目的 superpowers 技能表文件」（`superpowers-zh.md` 或等价 `HERMES.md` 技能表段落）。

---

## 全自动工作流公共准备

**目标：** 为 Goal 模式运行期产物建立目录，并（推荐）落地空白模板。

### 操作 P.1：创建运行期目录

```bash
mkdir -p docs/superpowers/{goals,contracts,gates,failures,handoff,templates}
```

| 目录 | 用途 |
|------|------|
| `docs/superpowers/goals/` | Goal 文档 |
| `docs/superpowers/contracts/` | 完成契约活文档 |
| `docs/superpowers/gates/` | 门禁报告 |
| `docs/superpowers/failures/` | 策略穷尽失败报告 |
| `docs/superpowers/handoff/` | 兼容旧 handoff 启动卡 |
| `docs/superpowers/templates/` | 可选：包内模板副本 |

### 操作 P.2：复制模板（可选但推荐）

```bash
cp templates/goal-document.md docs/superpowers/templates/
cp templates/completion-contract.md docs/superpowers/templates/
cp templates/gate-report.md docs/superpowers/templates/
cp templates/failure-report.md docs/superpowers/templates/
```

**是否改技能表 / AGENTS：** 否（仅目录与模板）。

**验证：**
- [ ] `docs/superpowers/goals/`、`contracts/`、`gates/`、`failures/` 存在
- [ ] （若执行 P.2）上述 4 个模板文件存在于 `docs/superpowers/templates/`

---

## 优化四：Pre-grill

**目标：** 用户提交 PRD 后进入人机可行性循环；仅在可行且准备清单确认后，才产出 Goal 文档启动入口。

### 操作 4.1：复制 skill 文件

```bash
# 先完成「技能安装目录检测」得到 $SKILLS_DIR
mkdir -p "$SKILLS_DIR/pre-grill"
cp skills/pre-grill/SKILL.md "$SKILLS_DIR/pre-grill/SKILL.md"
```

### 操作 4.2：修改技能表（`superpowers-zh.md` / `HERMES.md`）

**需要改技能表：是。** 在 `RULES_FILE` 中：

**修改 A —— 更新技能数：** `XX` → `XX + 1`。

**修改 B —— 在 skill 表格添加一行：**

```
| pre-grill | 当用户以 PRD 启动全自动交付时使用。做人机可行性循环、准备清单，确认后触发 Goal 文档生成，禁止未可行即 /goal |
```

### 操作 4.3：修改 AGENTS.md（如有）

**需要改 AGENTS：推荐。** 若 `AGENTS.md` 存在且尚无全自动交付说明，追加简短指向：

```markdown
### 全自动交付（Goal 模式）

用户提交 PRD 启动无人值守交付时，先加载 `pre-grill` 做可行性与准备清单；可行后再生成 Goal 文档，由用户执行 `/goal`。运行期产物在 `docs/superpowers/{goals,contracts,gates,failures}/`。
```

**验证：**
- [ ] `$SKILLS_DIR/pre-grill/SKILL.md` 存在
- [ ] 技能表含 `pre-grill` 且技能数 +1
- [ ] （推荐）`AGENTS.md` 提及 pre-grill / Goal 模式

---

## 优化五：Goal Document

**目标：** pre-grill 判定可行后，生成驱动 Hermes `/goal` 的完整 Goal 文档（阶段流程、门禁、恢复、完成契约骨架）。

### 操作 5.1：复制 skill 文件

```bash
mkdir -p "$SKILLS_DIR/goal-document"
cp skills/goal-document/SKILL.md "$SKILLS_DIR/goal-document/SKILL.md"
```

### 操作 5.2：修改技能表

**需要改技能表：是。**

**修改 A —— 技能数 +1。**

**修改 B —— 表格添加：**

```
| goal-document | 当 pre-grill 判定 PRD 可行后使用。生成完整 Goal 文档（阶段流程、门禁、恢复、完成契约骨架），供 Hermes /goal 无人值守执行 |
```

### 操作 5.3：AGENTS.md

**需要改 AGENTS：否**（公共准备与 pre-grill 章节已覆盖路径约定）。若项目有独立「文档产出路径」表，可补充一行：Goal 文档 → `docs/superpowers/goals/`。

**验证：**
- [ ] `$SKILLS_DIR/goal-document/SKILL.md` 存在
- [ ] 技能表含 `goal-document` 且技能数 +1

---

## 优化六：Completion Contract

**目标：** 以活文档完成契约跟踪目标覆盖、验收场景、证据、未决项、已试方法；硬门槛全绿才可宣布完成。

### 操作 6.1：复制 skill 文件

```bash
mkdir -p "$SKILLS_DIR/completion-contract"
cp skills/completion-contract/SKILL.md "$SKILLS_DIR/completion-contract/SKILL.md"
```

### 操作 6.2：修改技能表

**需要改技能表：是。**

**修改 A —— 技能数 +1。**

**修改 B —— 表格添加：**

```
| completion-contract | 当初始化或更新全自动交付的完成契约时使用。管理目标、验收场景、证据、未决项、已试方法与硬门槛完成状态；未全绿禁止宣布完成 |
```

### 操作 6.3：AGENTS.md

**需要改 AGENTS：推荐。** 可在全自动交付章节补充：完成契约路径 `docs/superpowers/contracts/`，宣布完成前须加载 `completion-contract` 核对硬门槛。

**验证：**
- [ ] `$SKILLS_DIR/completion-contract/SKILL.md` 存在
- [ ] 技能表含 `completion-contract` 且技能数 +1
- [ ] `docs/superpowers/contracts/` 目录存在

---

## 优化七：Gatekeeper

**目标：** 固定 6 阶段门禁；通过 `delegate_task` 派独立子 Agent 校验，执行 Agent 不得自检放行。

### 操作 7.1：复制 skill 文件

```bash
mkdir -p "$SKILLS_DIR/gatekeeper"
cp skills/gatekeeper/SKILL.md "$SKILLS_DIR/gatekeeper/SKILL.md"
```

### 操作 7.2：修改技能表

**需要改技能表：是。**

**修改 A —— 技能数 +1。**

**修改 B —— 表格添加：**

```
| gatekeeper | 在全自动工作流每个固定阶段门禁使用。通过 delegate_task 派独立门禁校验 Agent；执行 Agent 不得自批放行 |
```

### 操作 7.3：AGENTS.md / ROLES

**需要改 AGENTS：可选**（指向 gate 报告目录即可）。  
**需要对照 ROLES：是（验证项）** — 确认包内 `ROLES.md` 已描述「门禁校验 Agent」（由 `delegate_task` 产生，只校验不改业务代码）。安装到目标项目时，若项目有自己的角色文档，同步门禁角色说明。

**验证：**
- [ ] `$SKILLS_DIR/gatekeeper/SKILL.md` 存在
- [ ] 技能表含 `gatekeeper` 且技能数 +1
- [ ] `docs/superpowers/gates/` 目录存在
- [ ] ROLES（包内或项目内）含门禁校验角色

---

## 优化八：Decision Arbiter

**目标：** 运行期遇 PRD 矛盾/缺口时仲裁**执行决策**（不改 PRD 目标），写入 P1（`source=arbitration`）并更新完成契约决策矩阵。

### 操作 8.1：复制 skill 文件

```bash
mkdir -p "$SKILLS_DIR/decision-arbiter"
cp skills/decision-arbiter/SKILL.md "$SKILLS_DIR/decision-arbiter/SKILL.md"
```

### 操作 8.2：修改技能表

**需要改技能表：是。**

**修改 A —— 技能数 +1。**

**修改 B —— 表格添加：**

```
| decision-arbiter | 当全自动运行遇 PRD 矛盾或缺口时使用。只仲裁执行决策、不改 PRD 目标；写入 P1（source=arbitration+置信度）并更新完成契约决策矩阵 |
```

### 操作 8.3：AGENTS.md / ROLES

**需要改 AGENTS：可选。**  
**需要对照 ROLES：是（验证项）** — 确认含「决策仲裁 Agent」边界：只仲裁并写 P1，不实现功能、不改 PRD 目标。

**验证：**
- [ ] `$SKILLS_DIR/decision-arbiter/SKILL.md` 存在
- [ ] 技能表含 `decision-arbiter` 且技能数 +1
- [ ] ROLES 含决策仲裁角色

---

## 优化九：Auto Recovery

**目标：** 门禁 FAIL / 测试失败 / 实现失败时分类失败、轮换新策略（禁止重复已试方法）、重跑门禁；策略穷尽则写失败报告并通知用户，不阻塞其他任务。

### 操作 9.1：复制 skill 文件

```bash
mkdir -p "$SKILLS_DIR/auto-recovery"
cp skills/auto-recovery/SKILL.md "$SKILLS_DIR/auto-recovery/SKILL.md"
```

### 操作 9.2：修改技能表

**需要改技能表：是。**

**修改 A —— 技能数 +1。**

**修改 B —— 表格添加：**

```
| auto-recovery | 当阶段门禁 FAIL、测试失败或实现失败时使用。分类失败、换策略重试（禁止重复已试方法）、重跑门禁；策略穷尽写失败报告并通知用户，不阻塞其他任务 |
```

### 操作 9.3：AGENTS.md

**需要改 AGENTS：可选。** 可注明失败报告路径 `docs/superpowers/failures/`。

**验证：**
- [ ] `$SKILLS_DIR/auto-recovery/SKILL.md` 存在
- [ ] 技能表含 `auto-recovery` 且技能数 +1
- [ ] `docs/superpowers/failures/` 目录存在

---

## 执行后验证

全部操作完成后，确认以下事项：

### 原三层优化（一~三）

- [ ] `$SKILLS_DIR/project-wiki/SKILL.md` 存在（或历史路径 `.trae/skills/project-wiki/SKILL.md`）
- [ ] `$SKILLS_DIR/handoff-prompt/SKILL.md` 存在
- [ ] `$SKILLS_DIR/wiki-checkpoint/SKILL.md` 存在
- [ ] 技能表（`superpowers-zh.md` / `HERMES.md`）含 Wiki 优先核心规则
- [ ] `AGENTS.md` 包含强化的「项目手册（Wiki）」章节（含进入规则、必读清单、更新规则、更新原则）
- [ ] `wiki/` 目录已初始化（11 个文档）
- [ ] `docs/superpowers/handoff/` 目录已创建

### 全自动工作流（四~九 + 公共准备）

- [ ] 6 个新 skill 文件存在：
  - [ ] `$SKILLS_DIR/pre-grill/SKILL.md`
  - [ ] `$SKILLS_DIR/goal-document/SKILL.md`
  - [ ] `$SKILLS_DIR/completion-contract/SKILL.md`
  - [ ] `$SKILLS_DIR/gatekeeper/SKILL.md`
  - [ ] `$SKILLS_DIR/decision-arbiter/SKILL.md`
  - [ ] `$SKILLS_DIR/auto-recovery/SKILL.md`
- [ ] 4 个模板存在（包内 `templates/` 或已复制到 `docs/superpowers/templates/`）：
  - [ ] `goal-document.md`
  - [ ] `completion-contract.md`
  - [ ] `gate-report.md`
  - [ ] `failure-report.md`
- [ ] 运行期目录存在：`docs/superpowers/{goals,contracts,gates,failures}/`
- [ ] 技能表技能数已累计更新（相对安装前至少 +9：原 3 + 新 6），且表格包含全部 9 个优化 skill
- [ ] `ROLES.md`（包内或项目同步版）含门禁校验角色与决策仲裁角色
- [ ] `README.md` 工作流图为 pre-grill → Goal 模式（`/goal`）→ 6 阶段门禁（而非仅「复制 handoff 到新对话」）

---

## 扩展新优化

当你需要添加新的优化 skill 时，按以下最小步骤操作：

1. **创建 skill 文件** → 放到 `skills/<skill-name>/SKILL.md`
2. **修改 superpowers-zh.md / HERMES.md** → 更新技能数 + 在表格添加一行
3. **修改 AGENTS.md** → 如果新优化需要项目级规则，追加对应章节
4. **更新 superpowers-optimizer skill** → 如果新优化需要加入执行流程
5. **在本 GUIDE.md 追加新章节** → 写明操作步骤（含 `$SKILLS_DIR` 复制命令、是否改技能表、验证项）
6. **更新 README.md** → 在 skill 列表、目录结构和工作流图中添加新条目
7. **更新 ROLES.md** → 如果新优化涉及角色职责变化
8. **如需运行期产物** → 在 `docs/superpowers/` 下约定目录，并更新「执行后验证」清单
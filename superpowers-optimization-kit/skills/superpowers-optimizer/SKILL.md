---
name: superpowers-optimizer
description: Use when the user wants to install or upgrade the full-auto Superpowers workflow optimization kit — wiki/handoff/checkpoint plus pre-grill, Goal documents, gates, arbitration, completion contracts, and auto-recovery. Load this skill as the entry point; it reads GUIDE.md and applies the full kit to the project.
---

# Superpowers Optimizer — 全自动工作流优化执行器

## 概述

你是**框架讨论 Agent**。你的职责是把目标项目的 Superpowers 工作流从「半人工多轮对话」升级为「PRD + 一条 `/goal` → 无人值守交付」，并保留 Wiki / Handoff / Checkpoint 三层基础能力。

加载本 skill 后，你将按以下流程**全量**执行优化包（优化一~九 + 公共准备）。

## 角色定义

此优化包涉及多个 Agent 角色，你当前是框架讨论 Agent。详见 `ROLES.md`。

| 角色 | 一句话 | 你当前 |
|------|--------|--------|
| 方案设计 Agent | 和用户讨论产品方向；全自动路径下跑 pre-grill / 产出 Goal | ❌ |
| 项目搭建 Agent | 按 Goal 文档无人值守执行开发 | ❌ |
| 框架讨论 Agent | 优化 superpowers 框架本身、安装本优化包 | ✅ **你** |
| 门禁校验 Agent | `delegate_task` 独立校验，不改业务代码 | ❌（运行期） |
| 决策仲裁 Agent | PRD 矛盾/缺口仲裁，写 P1，不改 PRD 目标 | ❌（运行期） |

## 执行流程

### 第一步：告知用户（全自动工作流，而非仅三层 Wiki）

在开始任何操作前，向用户输出以下信息：

> 我将作为**框架讨论 Agent**，安装 **Superpowers 全自动工作流优化包**（共 9 项能力）。即将进行的操作：
>
> **公共准备**
> 1. 检测技能安装目录：优先 `.hermes/skills`，否则 `.trae/skills`
> 2. 创建 `docs/superpowers/{goals,contracts,gates,failures,handoff}`（推荐再复制 `templates/`）
>
> **原三层优化（一~三）**
> 3. 复制 skill：`project-wiki`、`handoff-prompt`、`wiki-checkpoint`
> 4. 修改技能表（`superpowers-zh.md` / `HERMES.md`）与 `AGENTS.md`（Wiki 优先 + 强化 wiki 章节）
> 5. 按需初始化 `wiki/`（已存在则跳过）
>
> **全自动工作流（四~九）**
> 6. 复制 6 个 skill：`pre-grill`、`goal-document`、`completion-contract`、`gatekeeper`、`decision-arbiter`、`auto-recovery`
> 7. 在技能表为上述 6 个 skill 各加一行并累计更新技能数
> 8. 按 GUIDE 补充 `AGENTS.md` 全自动交付说明（如有）
>
> 安装后，项目将具备：Wiki 手册、Handoff、Wiki Checkpoint，以及 **PRD → pre-grill → Goal 文档 → `/goal` 无人值守 + 6 阶段门禁 + 仲裁 + 完成契约 + 自动恢复**。
>
> 是否继续？

**等待用户确认后，再执行第二步。**

### 第二步：阅读优化指南

读取同目录优化包中的 `GUIDE.md`（相对本 skill：`../../GUIDE.md`，或仓库内 `superpowers-optimization-kit/GUIDE.md`），**逐项全量执行**其中的操作。GUIDE 已列出每个优化要改的文件、复制命令与验证项——按步骤执行，不要自行删减「四~九」。

### 第三步：按 GUIDE 全量执行

顺序建议：

1. **技能安装目录检测** → 得到 `$SKILLS_DIR`（优先 `.hermes/skills`，否则 `.trae/skills`）
2. **公共准备** → 创建 `docs/superpowers/{goals,contracts,gates,failures,...}`；可选复制 4 个 templates
3. **优化一~三** → Wiki / Handoff / Wiki Checkpoint（复制 skill + 技能表 + AGENTS + 初始化 wiki）
4. **优化四~九** → 六个全自动 skill 全部复制，并更新技能表（每项 +1）
5. 对照 `ROLES.md` / `README.md`：安装后的项目文档应能指向 pre-grill → Goal 模式工作流与门禁/仲裁角色（包内文档已定义；若项目另有角色说明则同步）

跳过规则：
- skill 文件已存在且内容一致 → 可跳过复制
- wiki 已初始化 → 跳过 project-wiki 初始化
- 目录已存在 → 不重复纠结创建失败

### 第四步：验证

按 GUIDE.md 底部「执行后验证」清单逐项确认，至少覆盖：

- 原 3 个 skill + **6 个新 skill** 均在 `$SKILLS_DIR`
- **4 个模板**存在（包内 `templates/` 或 `docs/superpowers/templates/`）
- **goals / contracts / gates / failures** 目录存在
- 技能表含全部 9 个优化 skill，技能数相对安装前至少 +9
- ROLES 含门禁 / 仲裁角色（包内或已同步）
- README 工作流为 pre-grill → Goal 模式（若本次只装 skill、未改 README，确认包内 README 已是该图；任务 10 负责重写 README 时以包为准）

### 第五步：告知完成（9 项能力摘要）

向用户输出：

> 全自动工作流优化安装完成。变更摘要：
>
> **9 项能力**
> 1. **Wiki 体系**（project-wiki）— 分层项目手册，Agent 按路线图自服务
> 2. **Handoff Prompt**（handoff-prompt）— 设计→实现启动卡（兼容 Goal 模式启动）
> 3. **Wiki Checkpoint**（wiki-checkpoint）— 完成前 wiki 读/写合规硬检查
> 4. **Pre-grill**（pre-grill）— PRD 可行性人机循环 + 准备清单
> 5. **Goal Document**（goal-document）— 生成驱动 `/goal` 的 Goal 文档
> 6. **Completion Contract**（completion-contract）— 活文档完成契约与硬门槛
> 7. **Gatekeeper**（gatekeeper）— 6 阶段独立门禁（delegate_task）
> 8. **Decision Arbiter**（decision-arbiter）— PRD 矛盾/缺口执行仲裁 → P1
> 9. **Auto Recovery**（auto-recovery）— 换策略重试；穷尽则失败报告不阻塞
>
> **目录**
> - skills → `$SKILLS_DIR`（检测结果）
> - 运行期 → `docs/superpowers/{goals,contracts,gates,failures,handoff}/`
>
> **使用方式（安装后）**
> 1. 用户提交 PRD → 加载 `pre-grill`
> 2. 可行并确认准备清单 → 生成 Goal 文档
> 3. 用户执行：`/goal 根据 Goal 文档 <path> 无人值守完成：…`
> 4. 运行期走门禁 / 契约 / 仲裁 / 恢复；完成门硬门槛全绿才可宣布完成

## 注意事项

- 修改技能表时，技能数必须精确（当前数 + 本次新增数；全量安装合计 +9）
- 修改 `AGENTS.md` 时，不要覆盖已有项目级规则，只追加 wiki / 全自动交付相关章节
- 技能目录检测：**优先 `.hermes/skills`，否则 `.trae/skills`**；不要写死只认 Trae
- 若 wiki 目录已存在，跳过初始化
- 若 skill 文件已存在，跳过复制（或按用户要求覆盖升级）
- 本 skill **不改** Hermes 源码、不改业务代码、不改原始 Superpowers 本体；只安装优化包 skills 与项目规则/目录
- README 全面重写可能由独立任务完成；本入口仍须按 GUIDE 装齐 9 项 skill 与目录，完成摘要必须列满 9 项能力

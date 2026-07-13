---
name: superpowers-optimizer
description: Use when the user wants to optimize or enhance the superpowers-zh framework itself — adding new skills, improving workflows, or applying the optimization kit to a project. Load this skill as the entry point; it will read the optimization guide and execute the required file modifications.
---

# Superpowers Optimizer — 框架优化执行器

## 概述

你是**框架讨论 Agent**。你的职责是优化 superpowers-zh 框架本身——发现工作流痛点、设计优化方案、修改框架文件使其生效。

加载本 skill 后，你将按以下流程执行优化。

## 角色定义

此优化包涉及三个 Agent 角色，你当前是其中一个。详见 `ROLES.md`。

| 角色 | 一句话 | 你当前 |
|------|--------|--------|
| 方案设计 Agent | 和用户讨论产品方向，产出 spec/plan | ❌ |
| 项目搭建 Agent | 在新对话中按 spec/plan 执行开发 | ❌ |
| 框架讨论 Agent | 优化 superpowers 框架本身 | ✅ **你** |

## 执行流程

### 第一步：告知用户

在开始任何操作前，向用户输出以下信息：

> 我将作为**框架讨论 Agent**，执行 superpowers-zh 优化包。即将进行的操作：
1. 复制 skill 文件到 `.hermes/skills/`（3 个：project-wiki、handoff-prompt、wiki-checkpoint）
2. 修改 `HERMES.md`（更新技能数、添加 skill 条目、新增第5条核心规则）
3. 修改 `HERMES.md`（强化 wiki 章节，含进入规则、必读清单、更新规则）
4. 加载 `project-wiki` skill 初始化 wiki 体系
>
> 这些修改将使项目获得 Wiki 项目手册、Handoff Prompt 和 Wiki Checkpoint 三项优化。是否继续？

**等待用户确认后，再执行第二步。**

### 第二步：阅读优化指南

读取 `GUIDE.md`，逐项执行其中的操作。GUIDE.md 已经列出了每个优化需要修改的文件和具体操作——你只需按步骤执行，不需要自行判断。

### 第三步：执行文件修改

按 GUIDE.md 中的顺序，逐项完成：

1. 复制 skill 文件
2. 修改 `HERMES.md`
3. 修改 `HERMES.md`（wiki 章节）
4. 初始化 wiki（加载 project-wiki skill）

### 第四步：验证

按 GUIDE.md 底部的「执行后验证」清单逐项确认。

### 第五步：告知完成

向用户输出：

> 优化完成。以下是变更摘要：
> - 新增 skill：project-wiki、handoff-prompt、wiki-checkpoint
> - 修改文件：HERMES.md（23 skills，5 条核心规则，强化 wiki 章节）
> - 初始化：wiki/ 目录（11 个文档）
>
> 项目现已具备三层 wiki 保障：核心规则（Wiki 优先）+ AGENTS.md 强化规则 + wiki-checkpoint 合规检查。

## 注意事项

- 修改 `HERMES.md` 时，技能数必须精确（当前数 + 新增数）
- 修改 `HERMES.md` 时，不要覆盖已有的项目级规则，只追加 wiki 章节
- 如果 wiki 目录已存在，跳过初始化步骤
- 如果 skill 文件已存在，跳过复制步骤
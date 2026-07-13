---
name: handoff-prompt
description: Use when a design spec and implementation plan are complete and the user needs a launch prompt to copy into a new conversation for execution. Generates a structured 7-step prompt that routes the new agent through wiki reading, design doc absorption, and implementation execution — without duplicating technical details already in spec/plan files.
---

# Handoff Prompt — 启动提示词生成器

## 概述

方案设计 agent 完成 spec+plan 后，生成一份可直接复制粘贴到新对话的启动提示词。提示词是「路由指南」——告诉新 agent 读什么、按什么顺序做、边界在哪——**不重复** spec/plan 中的技术细节。

## 何时使用

- 方案设计 agent 完成设计文档（spec）和实现计划（plan）后
- 用户准备将开发任务交给新对话执行
- 用户说"帮我写一个启动提示词"、"生成 agent prompt"、"写一个交接提示词"

**不适用的场景：**
- 设计尚未完成（先走 brainstorming）
- 任务简单到不需要 spec/plan（直接在当前对话完成）
- 生成的是 handoff 交接文档（给人读的，不是给 agent 执行的）

## 核心原则

1. **提示词是路由指南，不是技术文档** — 引用 spec/plan/wiki，不复制内容
2. **7 步流程固定，内容按需填充** — 可变部分用 `{}` 标记，由方案设计 agent 填入
3. **输出在对话中，不存文件** — 用户直接复制粘贴使用
4. **边界 > 细节** — 写清楚「不能改什么」比写清楚「怎么实现」更重要

## 生成时机

方案设计 agent 在 `writing-plans` 完成后，**自动加载本技能**生成启动提示词。生成后直接输出在对话中，不写入文件。

## 输出模板

### 模板结构

```
# 新对话 Agent 启动提示词：{任务名称}

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是"{项目名称}"项目的开发 Agent。你的任务是实现**{任务简述}**。

## 第一步：加载技能框架

立即调用 Skill 工具加载 `using-superpowers` 技能。这是你在该项目中工作的前置要求。

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

使用 `subagent-driven-development` 技能执行实现计划。每个子 Agent 必须遵循 TDD——先写测试再写实现。

{如果有多任务建议拆分，在此列出}

## 第六步：验证

调用 `verification-before-completion` 技能进行验证：

{列出验证项，从 spec 中提取}

## 第七步：更新 Wiki

开发完成后，按 wiki 各文档底部的"更新指引"更新：
{列出需要更新的 wiki 文档，从 spec 中判断影响范围}

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

### 填充指南

方案设计 agent 填充模板时，按以下优先级获取信息：

| 字段 | 信息来源 | 说明 |
|------|---------|------|
| 任务名称 | spec 标题 | 简短描述，如"输入扩展功能实现" |
| 项目名称 | wiki/L1-全景 产品定位 | 如"优者" |
| 任务简述 | spec 核心功能概述 | 一句话 |
| spec 路径 | 实际文件路径 | 相对于项目根目录 |
| plan 路径 | 实际文件路径，如无则标注"待创建" | 同上 |
| 任务拆分 | spec 中的实现建议 | 可选，复杂任务建议列出 |
| 验证项 | spec 中的验收标准 | 每条一行 |
| wiki 更新列表 | 按影响范围判断 | 前端/后端/接口/经验 |
| 关键约束 | spec 约束章节 + P1-产品决策日志用户偏好 | 2-5 条 |
| 不可变部分 | spec 明确标注 + L2-架构关键边界 | 逐条列出 |
| 环境信息 | 当前运行环境 | 从终端或配置提取 |
| 注意事项 | P1-产品决策日志偏好 + L6-经验录相关坑 | 逐条列出 |

## 常见错误

| 错误 | 修复 |
|------|------|
| 把 spec 的技术细节全部复制进提示词 | 提示词是路由指南，技术细节在 spec 里。删掉，改为引用 |
| 忘记标注「不能改动的部分」 | 这是最重要的约束。从 spec 和 L2-架构提取 |
| 忘记引用 P1-产品决策日志 | 新 agent 不知道用户偏好，可能做出不符合用户口味的设计 |
| 忘记引用 L6-经验录的相关坑 | 新 agent 会重蹈覆辙 |
| 环境信息写死而非从当前环境获取 | 环境可能变化，始终从当前终端或配置中提取 |
| 输出存为文件 | 提示词必须直接输出在对话中，让用户复制粘贴 |

## 示例

参见 `docs/superpowers/handoff/2026-07-11-input-expansion-agent-prompt.md` 作为参考。
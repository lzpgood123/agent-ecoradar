---
name: wiki-checkpoint
description: Use when claiming work is complete, before committing or marking a task as done. Verifies that the agent has read the correct wiki documents for their role and updated the wiki documents required by their changes. Outputs a compliance report with pass/fail for each wiki obligation.
---

# Wiki Checkpoint — Wiki 合规检查点

## 概述

在声称工作完成前，检查 wiki 的「读」和「写」是否合规。本 skill 应在 `verification-before-completion` 流程中加载。

## 何时使用

- 开发任务完成后，commit 之前
- 方案设计讨论结束后
- 框架变更完成后
- 任何声称「完成」的时刻

## 检查流程

### 第一步：识别角色

根据你当前执行的任务类型，确定你的角色：

| 你做了什么 | 你的角色 |
|-----------|---------|
| 与用户讨论产品方向、写了 spec/plan | 方案设计 Agent |
| 写了代码、改了文件 | 项目搭建 Agent |
| 改了 superpowers 配置、skill、wiki 结构 | 框架讨论 Agent |

### 第二步：检查「读」合规

逐项确认你是否在开始工作前读了必读文档：

**方案设计 Agent：**
- [ ] 读了 `wiki/P1-产品决策日志.md`（了解用户偏好和历史决策）
- [ ] 读了 `wiki/L1-全景.md`（了解产品现状）

**项目搭建 Agent：**
- [ ] 读了 `wiki/L3-代码地图.md`（定位文件）
- [ ] 读了 `wiki/L6-经验录.md`（避坑）
- [ ] 按任务类型读了 `wiki/L4A-前端详解.md` 或 `wiki/L4B-后端详解.md`
- [ ] 如涉及接口变更，读了 `wiki/L5-接口契约.md`

**框架讨论 Agent：**
- [ ] 读了 `wiki/P3-框架演进.md`（了解历史变更）
- [ ] 读了 `wiki/L2-架构.md`（了解技术边界）

### 第三步：检查「写」合规

根据你实际做的变更，逐项确认 wiki 更新：

| 我做了什么 | 需要更新 | 已更新？ |
|-----------|---------|----------|
| 新增/删除文件 | `wiki/L3-代码地图.md` | [ ] |
| 前端代码变更 | `wiki/L4A-前端详解.md` | [ ] |
| 后端代码变更 | `wiki/L4B-后端详解.md` | [ ] |
| API 接口变更 | `wiki/L5-接口契约.md` | [ ] |
| 发现/修复 Bug | `wiki/L6-经验录.md` | [ ] |
| 项目状态变化 | `wiki/L1-全景.md` | [ ] |
| 方案设计讨论 | `wiki/P1-产品决策日志.md` | [ ] |
| 框架变更 | `wiki/P3-框架演进.md` | [ ] |

### 第四步：输出合规报告

按以下格式输出：

```
=== Wiki 合规检查 ===

角色：{你的角色}
[✅/❌] 读合规 — {通过的项数}/{总项数}
  ✅ wiki/P1-产品决策日志.md
  ❌ wiki/L1-全景.md（未读）
[✅/❌] 写合规 — {通过的项数}/{总项数}
  ✅ wiki/L3-代码地图.md（新增了 app.js 的说明）
  ❌ wiki/L6-经验录.md（缺少本次修复的坑记录）

总体：{✅ 通过 / ❌ 未通过}

{如果未通过，列出待修复项}
```

### 第五步：修复未通过项

如果检查未通过，**立即修复**，然后重新运行本检查。不可在未通过状态下声称完成。

## 红线

以下情况视为违规，**必须修复后才能继续**：

- 跳过 wiki 直接读代码（除非 wiki 中不存在相关信息）
- 开发完成后未更新任何 wiki 文档
- 发现新坑但未追加到 L6-经验录
- 检查报告显示 ❌ 但仍然声称完成

## 注意

- 本 skill 是**验证流程的一部分**，不是可选项
- 如果 wiki 中不存在相关信息，在检查报告中注明「wiki 无相关内容」
- 如果某项变更不在更新规则表中（如纯文档变更），注明「不适用」
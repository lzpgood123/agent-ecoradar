---
name: wiki-checkpoint
description: Use when claiming work is complete, before the completion gate, or before commit/done. Verifies wiki read/write obligations and outputs a compliance report. In full-auto Goal mode, the report path must be written into the completion-contract evidence for hard gate 4.
---

# Wiki Checkpoint — Wiki 合规检查点

## 概述

在声称工作完成前，检查 wiki 的「读」和「写」是否合规，并输出合规报告。

本 skill 是验证与完成链路的一部分：

- 半人工：应在 `verification-before-completion` 流程中加载
- **全自动：完成门（阶段 6）之前必须通过**；阶段 5「Wiki / 合规」门禁以本报告为 PASS 依据

## 何时使用

- 开发任务完成后，commit 之前
- 方案设计讨论结束后
- 框架变更完成后
- 任何声称「完成」的时刻
- **全自动 Goal 模式：进入完成门前必须通过本检查**（通常在阶段 5 执行；完成门硬门槛 4 复核）

**不适用：**

- 用口头「wiki 应该没问题」代替报告
- 跳过报告路径登记就宣布完成契约硬门槛 4 为绿

## 全自动强制规则（完成契约）

在 Goal / 完成契约模式下：

1. **完成门前必须通过** — 总体未通过时不得进入或放行完成门
2. **报告必须落盘** — 将合规报告写入可定位文件，推荐：

   `docs/superpowers/evidence/YYYY-MM-DD-<topic>-wiki-checkpoint.md`

   （或项目约定的 evidence 目录；路径必须真实存在）

3. **报告路径必须写入完成契约证据** — 更新权威契约  
   `docs/superpowers/contracts/YYYY-MM-DD-<topic>-contract.md`：
   - 硬门槛第 4 项「Wiki/检查点合规」的关联证据路径 = 本报告路径
   - 和/或验收场景 / 变更日志中登记同一路径  
   仅对话里贴报告、契约无路径 → **硬门槛 4 视为未满足**
4. 报告内容须可机读为通过（如含 `总体：✅ 通过` 或等价 PASS）

半人工模式同样建议保存报告；全自动下路径入契约为**硬要求**。

## 检查流程

### 第一步：识别角色

根据你当前执行的任务类型，确定你的角色：

| 你做了什么 | 你的角色 |
|-----------|---------|
| 与用户讨论产品方向、写了 spec/plan | 方案设计 Agent |
| 写了代码、改了文件 | 项目搭建 Agent / Goal 执行 Agent |
| 改了 superpowers 配置、skill、wiki 结构 | 框架讨论 Agent |
| 全自动跑完实现与证据阶段 | Goal 执行 Agent（按项目搭建义务检查读/写） |

### 第二步：检查「读」合规

逐项确认你是否在开始工作前读了必读文档：

**方案设计 Agent：**
- [ ] 读了 `wiki/P1-产品决策日志.md`（了解用户偏好和历史决策）
- [ ] 读了 `wiki/L1-全景.md`（了解产品现状）

**项目搭建 / Goal 执行 Agent：**
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

按以下格式输出（对话 + 全自动时写入证据文件）：

```
=== Wiki 合规检查 ===

角色：{你的角色}
报告路径：{docs/superpowers/evidence/... 或 N/A}
[✅/❌] 读合规 — {通过的项数}/{总项数}
  ✅ wiki/P1-产品决策日志.md
  ❌ wiki/L1-全景.md（未读）
[✅/❌] 写合规 — {通过的项数}/{总项数}
  ✅ wiki/L3-代码地图.md（新增了 app.js 的说明）
  ❌ wiki/L6-经验录.md（缺少本次修复的坑记录）

总体：{✅ 通过 / ❌ 未通过}

{如果未通过，列出待修复项}
{全自动：若通过，下一步把报告路径写入完成契约硬门槛 4 证据}
```

### 第五步：修复未通过项

如果检查未通过，**立即修复**，然后重新运行本检查。不可在未通过状态下声称完成。

全自动下 FAIL → 由 `gatekeeper` 判定阶段 5 FAIL → 调用 `auto-recovery`，**不得**进入完成门。

### 第六步（全自动）：登记完成契约

当总体通过时：

1. 确认报告文件路径存在
2. 加载或直接更新 `completion-contract`：将路径写入硬门槛 4 / 证据字段
3. 输出契约更新确认（路径已登记）

## 红线

以下情况视为违规，**必须修复后才能继续**：

- 跳过 wiki 直接读代码（除非 wiki 中不存在相关信息）
- 开发完成后未更新任何 wiki 文档
- 发现新坑但未追加到 L6-经验录
- 检查报告显示 ❌ 但仍然声称完成
- **全自动：完成门前无通过报告，或报告路径未写入完成契约证据**

## 与其它 skill 的协作

| Skill | 关系 |
|-------|------|
| `gatekeeper` | 阶段 5 检查「wiki-checkpoint 报告通过」 |
| `completion-contract` | 硬门槛 4 需要本报告路径作为证据 |
| `auto-recovery` | 阶段 5 / 完成门因 wiki 失败时的恢复入口 |
| `handoff-prompt` | 模式 A 第七步；模式 B 要求阶段 5 跑本 skill |
| `verification-before-completion` | 半人工流程中常与本 skill 串联 |

## 注意

- 本 skill 是**验证 / 完成流程的一部分**，不是可选项
- 如果 wiki 中不存在相关信息，在检查报告中注明「wiki 无相关内容」
- 如果某项变更不在更新规则表中（如纯文档变更），注明「不适用」
- 新建项目尚无 wiki 时：先建立最小 wiki 或明确「本任务豁免项」并记入契约未决项（豁免须用户/Goal 边界允许，不得默示跳过）

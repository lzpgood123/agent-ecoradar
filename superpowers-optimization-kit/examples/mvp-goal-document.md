# Goal 文档：健康检查端点

## 元信息

| 字段 | 值 |
|------|-----|
| 任务名称 | 健康检查端点 |
| PRD 路径 | superpowers-optimization-kit/examples/mvp-backend-prd.md |
| 完成契约路径 | docs/superpowers/contracts/2026-07-18-health-endpoint-contract.md |
| 创建日期 | 2026-07-18 |
| 创建来源 | pre-grill + goal-document（样例，供人工对照） |
| 目标项目根 | {安装优化包后的目标项目根} |
| 决定性文件 | superpowers-optimization-kit/examples/mvp-backend-prd.md |

## Goal 声明（给 /goal）

```
根据 Goal 文档 docs/superpowers/goals/2026-07-18-health-endpoint-goal.md 无人值守完成：为后端增加 GET /health，返回 {"status":"ok"} 且测试与证据齐全
```

> 用户在 Hermes 中执行：`/goal <上述声明>`。执行 Agent 第一步必须全文阅读本 Goal 文档。

## 完成契约

> 活文档。运行时以 `docs/superpowers/contracts/` 下副本为准；本处为初始化骨架。
> 规则：PRD 目标不可改；验收场景可新增隐含缺口，禁止删除/降级已冻结场景；硬门槛全绿才可宣布完成。

### PRD 目标清单

| # | 目标 | 来源 | 覆盖状态 | 证据路径 |
|---|------|------|---------|---------|
| 1 | 提供 `GET /health`，HTTP 200，JSON 含 `"status":"ok"` | PRD | pending | |
| 2 | 相关自动化测试真实通过 | PRD | pending | |
| 3 | 若项目已有 wiki 且路由变更，更新 L4B/L5 | PRD | pending | |

### 验收场景骨架

| # | 场景 | 类型 | 证据要求 | 状态 | 证据路径 | 冻结 |
|---|------|------|---------|------|---------|------|
| 1 | 服务启动后 curl /health 返回 status=ok | 功能 | `curl -s localhost:<port>/health` 输出含 `"status":"ok"`，HTTP 200 | pending | | 是 |
| 2 | 健康检查相关测试通过 | 回归 | 测试命令真实 stdout/stderr 与 exit code 0 | pending | | 是 |
| 3 | wiki 路由文档已按需更新或确认无需更新 | 合规 | wiki-checkpoint 报告或「无 wiki/无需更新」说明 | pending | | 是 |

### 决策矩阵

| # | 决策点 | 决策 | 来源 | 置信度 |
|---|--------|------|------|--------|
| 1 | 响应体格式 | 固定 JSON `{"status":"ok"}`，不扩展字段 | PRD | high |
| 2 | 认证 | 不做认证，端点公开可访问 | PRD 非目标 | high |
| 3 | 前端/部署 | 不改前端、不改部署架构 | PRD 非目标 | high |
| 4 | 实现落点 | 在现有后端路由层增加 handler，不新建无关服务 | inferred | medium |

### 未决项

| # | 问题 | 状态 | 处理方式 |
|---|------|------|---------|
| — | 无 | closed | — |

### 可否宣布完成

- **否**（初始化默认；仅当完成契约硬门槛 4/4 全绿后改为「是」）

## 不可改边界

- **PRD 目标不可改写、不可降级、不可删除**
- **非目标**（来自 PRD）：不改前端；不做认证；不改部署架构
- **项目约束**：不改无关模块；测试必须真实跑通；禁止伪造 curl/测试输出
- **禁止**：改 Hermes 源码、跳过门禁自批、删除已冻结验收场景

## 阶段流程

每个阶段结束必须通过 `gatekeeper` skill 派 `delegate_task` 独立子 Agent 校验；执行 Agent **不得自检放行**。FAIL 则调用 `auto-recovery`。

### 阶段 1：Intake / 决策编译

1. 加载 `completion-contract` skill，初始化完成契约活文档（路径见元信息）
2. 将上表 3 条 PRD 目标与 3 条验收场景写入契约并冻结场景
3. 确认决策矩阵无 open 矛盾
4. 门禁：`gatekeeper` → Intake → 报告写入 `docs/superpowers/gates/`

### 阶段 2：Spec + Plan

1. 产出覆盖本 PRD 的简短 spec + 可执行 plan（含路由、测试、验证 curl）
2. 核对未触碰前端/认证/部署
3. 门禁：`gatekeeper` → Spec+Plan

### 阶段 3：实现

1. 实现 `GET /health`；补充/更新测试
2. 真实运行测试并保留输出
3. 门禁：`gatekeeper` → 实现

### 阶段 4：验收证据

1. 实测 curl 场景，保存输出到证据路径
2. 保存测试通过日志
3. 门禁：`gatekeeper` → 验收证据

### 阶段 5：Wiki / 合规

1. 若项目有 wiki 且后端路由变更：更新 L4B/L5
2. 加载 `wiki-checkpoint`；报告路径写入契约
3. 门禁：`gatekeeper` → Wiki/合规

### 阶段 6：完成门

1. 加载 `completion-contract`，硬门槛四项全检
2. 4/4 全绿后将「可否宣布完成」改为「是」
3. 门禁：`gatekeeper` → 完成门
4. 显式声明完成，供 `/goal` judge 判 done

## 失败恢复策略

1. 门禁 FAIL / 测试失败 / 实现失败 → 加载 `auto-recovery`
2. 读取完成契约「已试方法」；新策略摘要不得与已试相同
3. PRD 矛盾/缺口 → `decision-arbiter`；环境/端口/依赖缺失 → 写失败报告并停止
4. 策略穷尽 → `templates/failure-report.md` → `docs/superpowers/failures/`，通知用户
5. 禁止原地重复同一方法；禁止跳过门禁

## 准备清单

- [ ] PRD 可读：`superpowers-optimization-kit/examples/mvp-backend-prd.md`
- [ ] 后端可本地启动；端口已知或可配置
- [ ] 可运行项目既有测试命令
- [ ] 写权限：`docs/superpowers/{goals,contracts,gates,failures}/`
- [ ] Hermes Goal 模式可用；建议 `goals.max_turns` ≥ 100
- [ ] 是否 YOLO/自动批准工具已明确
- [ ] 若有 wiki：README、L1、P1、L6 可读

## 变更日志

| 时间 | 变更 | 作者 |
|------|------|------|
| 2026-07-18 | 按模板填充 MVP 健康检查端点样例 | goal-document 样例 |

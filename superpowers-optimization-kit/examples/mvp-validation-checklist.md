# MVP 验收清单

> 对应 plan 任务 12。用于验证「全自动工作流优化包」Phase 0 最小闭环是否齐备。  
> **本清单是静态/半动态验收**，不要求在本仓库内真实改业务代码并完成一次无人值守交付。

## 静态验收（不启动业务服务）

- [ ] `templates/` 4 个文件齐全：
  - [ ] `goal-document.md`
  - [ ] `completion-contract.md`
  - [ ] `gate-report.md`
  - [ ] `failure-report.md`
- [ ] skills 存在：
  - [ ] `pre-grill`
  - [ ] `goal-document`
  - [ ] `completion-contract`
  - [ ] `gatekeeper`
  - [ ] `auto-recovery`
  - [ ] `decision-arbiter`
  - [ ] （保留）`project-wiki` / `handoff-prompt` / `wiki-checkpoint` / `superpowers-optimizer`
- [ ] `README.md` 描述全自动主链路：`pre-grill → /goal → 6 门禁`
- [ ] `ROLES.md` 含门禁校验 / 决策仲裁 / 完成契约维护
- [ ] `GUIDE.md` 含优化四~九与目录准备（goals/contracts/gates/failures）
- [ ] `superpowers-optimizer` 入口文案为全自动工作流（9 项能力）
- [ ] 用 `examples/mvp-backend-prd.md` 对照 `examples/mvp-goal-document.md`：Goal 模板字段齐全、验收场景含 `/health`

## 动态验收（在已安装优化包的真实项目上）

- [ ] 提交 MVP PRD → `pre-grill` 判定可行（或给出不可行原因后循环）
- [ ] 生成 Goal 文档到 `docs/superpowers/goals/`
- [ ] 生成完成契约到 `docs/superpowers/contracts/`
- [ ] 模拟 Intake 门禁：按 `gatekeeper` 检查表出 PASS 报告到 `docs/superpowers/gates/`
- [ ] 模拟完成门：硬门槛未全绿时 `可否宣布完成` 必须为否
- [ ] 模拟一次 FAIL：`auto-recovery` 要求换策略并写入完成契约「已试方法」

## 不做（MVP 外）

- 不要求真实业务功能自动写完
- 不要求 3 次 meta 验收一次做完
- 不改 Hermes 源码
- 不改目标项目业务逻辑（除非该项目另开交付任务）

## 快速自检命令

```bash
# 在优化包根目录执行
ls templates/*.md
ls skills/pre-grill/SKILL.md skills/goal-document/SKILL.md \
   skills/completion-contract/SKILL.md skills/gatekeeper/SKILL.md \
   skills/decision-arbiter/SKILL.md skills/auto-recovery/SKILL.md
rg -n "pre-grill|goal-document|gatekeeper|completion-contract|decision-arbiter|auto-recovery" \
  README.md ROLES.md GUIDE.md skills/superpowers-optimizer/SKILL.md
```

## 通过标准

静态验收全部勾选 = **优化包 Phase 0 文档/skill 完成**。  
动态验收全部勾选 = **目标项目上 MVP 闭环可跑**（可另开交付会话）。

# 评估提示词：批次 1 — push only

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是 "Search in Coding" 项目的**独立质量评估 Agent**。批次 1（push only）声称已完成。你必须用证据判定 **PASS / CONDITIONAL / FAIL**，不得信任执行 Agent 自述。

设计与验收源：

1. `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`（批次 1 + 决策表）
2. `docs/superpowers/handoff/2026-07-14-batch1-push-only-prompt.md`（评估清单）

---

## 评估方法

1. 读 wiki/L1 与上述文档
2. 用 git / gh 核对，不凭记忆：
   - `git status -sb`、`git log --oneline origin/main..HEAD`、`git log --oneline -5`
   - `gh api` / 浏览器无法访问时用 `gh` 查 remote main
3. 确认**未 deploy**：对比线上 metrics/projects 与「本批是否可能改变线上」；至少证明本批未运行 deploy（日志/时间戳/站点文件 mtime 等）
4. 确认未提交无关未跟踪文件（handoff/spec/bak 等不应出现在 push commits 里）

---

## 必过项（任一失败 → FAIL）

- [ ] 本地目标 commits 已在 GitHub `main`
- [ ] 本批无 force push
- [ ] 本批未 deploy
- [ ] 未把未跟踪 design/handoff/备份提交进仓库
- [ ] 未改业务代码/数据（相对 push 前已有 commits 而言）

---

## 报告格式（中文）

```
# 批次1评估报告
结论：PASS | CONDITIONAL | FAIL
证据：
- ...
风险：
- ...
是否允许进入批次2：是/否
建议：
- ...
```

只有 **PASS** 才允许启动批次 2。CONDITIONAL 必须列出必须补做项。

# 新对话 Agent 启动提示词：批次 1 — push only

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是 "Search in Coding" 项目的开发 Agent。你的任务是：**把本地已有 commits 推送到 GitHub `main`，不做任何 deploy，不提交未跟踪文件。**

设计真相源：`docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`（批次 1 章节 + 已确认决策表）。

完成后停住，等待独立评估 Agent PASS，再进入批次 2。

---

## 第一步：加载技能框架

1. 优先 `skill_view("using-superpowers")`（或项目内等价 skill）。
2. 失败则阅读并遵守工作区 `HERMES.md` 与 `.hermes/skills/` 相关 skill。
3. 本批无代码修改，无需 TDD。

---

## 第二步：阅读项目上下文

必读：

1. `wiki/README.md`
2. `wiki/L1-全景.md`
3. `wiki/L6-经验录.md`（git/branch protection / 签名相关坑）
4. `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md` — **本批设计依据**

核对事实（用工具，不凭记忆）：

- `git log --oneline -5`、`git status -sb`
- 本地是否 ahead of `origin/main`
- 工作区是否有未跟踪 design/handoff/备份文件（**不要提交它们**）

---

## 第三步：执行

按 spec 批次 1：

1. 仅 `git push origin main` 推送**已有** commits
2. 验证 GitHub 最新 commit
3. **禁止** `deploy_site.py` / 任何线上发布
4. 冲突时：`git pull --rebase origin main` 后再 push；仍失败则停并报告
5. 签名/branch protection 失败：停并报告，**禁止 force push**

---

## 第四步：验证

- GitHub `https://github.com/lzpgood123/search-in-coding` 显示本地已有 commits
- 本批未改代码/数据
- 本批未 deploy
- 未把未跟踪 handoff/spec/备份加入 git

---

## 第五步：Wiki

本批若仅 push、无状态变化可记，按需在 `wiki/L1-全景.md` 注明「代码已 push、站点未 deploy」；无代码结构变化则不必改 L3/L4/L5。

---

## 关键约束

1. **不 deploy**
2. **不修改代码/数据**
3. **不 git add** 未跟踪 handoff/spec/备份/临时 skills
4. **不 force push**
5. 技能加载失败要回退，不卡死

## 不能改动的部分

- 线上 webroot 内容
- `data/projects.yaml` 与任何脚本逻辑
- 现有 cron 配置

## 项目环境

- 工作目录：`/root/workspace/search in coding`
- 仓库：https://github.com/lzpgood123/search-in-coding
- 站点（本批不动）：https://coding.lzpgood.online/
- branch protection：require signatures + enforce admins

## 最终汇报格式（中文）

1. push 前 `git status` / ahead 数
2. push 结果与 commit hashes
3. 是否发生 rebase/冲突
4. 明确声明：**未 deploy**
5. 明确声明：未提交无关未跟踪文件
6. 遗留问题

## 评估验收清单（给评估 Agent）

- [ ] 仅推送了已有 commits
- [ ] 未 deploy
- [ ] 未提交未跟踪 design/handoff/备份
- [ ] 无 force push
- [ ] GitHub main 与本地目标 commits 一致

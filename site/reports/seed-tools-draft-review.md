# seed-tools draft review — 31 工具封闭名单

> 生成自 `scripts/draft_seed_tools.py`。现有 **10** 条，
目标 **31**，本次新增草稿 **21** 条。

## 使用说明

1. 审阅下方「新增草稿」与「不确定字段」
2. 修正 `data/seed-tools.yaml` 中的 id / name / aliases / repo
3. 确认项：`status: draft` → `status: active`
4. **CodeBuddy** 必须复用已有 `workbuddy-codebuddy`，勿新建 `codebuddy`
5. 确认后由执行 Agent 跑 `onboard_tool.py --all-pending`（勿在审前全量 active）

## 已匹配（保留，不重复插入）

| 展示名 | 建议 id | 现有 id | status | 备注 |
|--------|---------|---------|--------|------|
| Cursor | `cursor` | `cursor` | active |  |
| Codex | `codex-cli` | `codex-cli` | active |  |
| Trae | `trae` | `trae` | active |  |
| Antigravity | `antigravity-cli` | `antigravity-cli` | active |  |
| Qoder | `qoder` | `qoder` | active |  |
| CodeBuddy | `workbuddy-codebuddy` | `workbuddy-codebuddy` | active | MERGE: reuse existing id workbuddy-codebuddy; do NOT create codebuddy. |
| OpenCode | `opencode` | `opencode` | active |  |
| Goose | `goose` | `goose` | active |  |
| Claude Code | `claude-code` | `claude-code` | active |  |
| Hermes Agent | `hermes-agent` | `hermes-agent` | active |  |

## 新增草稿（status=draft）

| 展示名 | id | tool_kind | repo | 不确定字段 |
|--------|-----|-----------|------|------------|
| GitHub Copilot | `github-copilot` | open | `github/copilot.vim` | notes:Product is closed; repo points to open editor integration. |
| Windsurf | `windsurf` | open | `Exafunction/codeium` | notes:Main product closed; codeium org has public integrations. |
| Kiro | `kiro` | closed | `null` | repo, notes:Likely closed product; verify public repo before opening., tool_kind=closed (confirm) |
| Zed | `zed` | open | `zed-industries/zed` | — |
| Warp | `warp` | open | `warpdotdev/Warp` | notes:Desktop app mostly closed; public repo may be sparse. |
| Aider | `aider` | open | `Aider-AI/aider` | — |
| 通义灵码 | `tongyi-lingma` | closed | `null` | repo, notes:Closed product; ecosystem search via aliases only., tool_kind=closed (confirm) |
| Comate | `comate` | closed | `null` | repo, notes:Closed product likely., tool_kind=closed (confirm) |
| CodeGeeX | `codegeex` | open | `THUDM/CodeGeeX` | — |
| Cline | `cline` | open | `cline/cline` | — |
| Kilo Code | `kilo-code` | open | `Kilo-Org/kilocode` | — |
| Junie | `junie` | closed | `null` | repo, notes:Closed JetBrains product., tool_kind=closed (confirm) |
| Continue | `continue` | open | `continuedev/continue` | — |
| Augment Code | `augment-code` | closed | `null` | repo, notes:Likely closed product., tool_kind=closed (confirm) |
| Tabnine | `tabnine` | closed | `null` | repo, notes:Closed product., tool_kind=closed (confirm) |
| Manus | `manus` | closed | `null` | repo, notes:Closed agent product; ecosystem mentions only., tool_kind=closed (confirm) |
| v0.dev | `v0-dev` | closed | `null` | repo, notes:Closed SaaS builder., tool_kind=closed (confirm) |
| Lovable | `lovable` | closed | `null` | repo, notes:Closed SaaS; formerly GPT Engineer ecosystem., tool_kind=closed (confirm) |
| Replit | `replit` | closed | `null` | repo, notes:Closed product platform., tool_kind=closed (confirm) |
| Bolt.new | `bolt-new` | open | `stackblitz/bolt.new` | — |
| OpenClaw | `openclaw` | closed | `null` | repo, website, docs, notes:Uncertain product identity/repo — user should verify., tool_kind=closed (confirm) |

### 草稿明细

#### GitHub Copilot (`github-copilot`)

- **vendor:** GitHub / Microsoft
- **primary_type:** ai-assistant
- **repo:** `github/copilot.vim`
- **website:** https://github.com/features/copilot
- **aliases:** GitHub Copilot, Copilot, gh copilot, copilot.vim
- **tool_kind:** open
- **status:** draft / **onboard_state:** pending
- **不确定字段:** notes:Product is closed; repo points to open editor integration.
- **备注:** Product is closed; repo points to open editor integration.

#### Windsurf (`windsurf`)

- **vendor:** Codeium / Exafunction
- **primary_type:** ai-ide
- **repo:** `Exafunction/codeium`
- **website:** https://windsurf.com
- **aliases:** Windsurf, Codeium Windsurf, windsurf editor
- **tool_kind:** open
- **status:** draft / **onboard_state:** pending
- **不确定字段:** notes:Main product closed; codeium org has public integrations.
- **备注:** Main product closed; codeium org has public integrations.

#### Kiro (`kiro`)

- **vendor:** AWS
- **primary_type:** ai-ide
- **repo:** `None`
- **website:** https://kiro.dev
- **aliases:** Kiro, Kiro IDE, AWS Kiro
- **tool_kind:** closed
- **status:** draft / **onboard_state:** pending
- **不确定字段:** repo, notes:Likely closed product; verify public repo before opening., tool_kind=closed (confirm)
- **备注:** Likely closed product; verify public repo before opening.

#### Zed (`zed`)

- **vendor:** Zed Industries
- **primary_type:** ai-ide
- **repo:** `zed-industries/zed`
- **website:** https://zed.dev
- **aliases:** Zed, Zed editor, zed.dev
- **tool_kind:** open
- **status:** draft / **onboard_state:** pending

#### Warp (`warp`)

- **vendor:** Warp
- **primary_type:** terminal-agent
- **repo:** `warpdotdev/Warp`
- **website:** https://www.warp.dev
- **aliases:** Warp, Warp terminal, Warp AI
- **tool_kind:** open
- **status:** draft / **onboard_state:** pending
- **不确定字段:** notes:Desktop app mostly closed; public repo may be sparse.
- **备注:** Desktop app mostly closed; public repo may be sparse.

#### Aider (`aider`)

- **vendor:** Aider
- **primary_type:** terminal-agent
- **repo:** `Aider-AI/aider`
- **website:** https://aider.chat
- **aliases:** Aider, aider-chat, Aider AI
- **tool_kind:** open
- **status:** draft / **onboard_state:** pending

#### 通义灵码 (`tongyi-lingma`)

- **vendor:** Alibaba Cloud
- **primary_type:** ai-assistant
- **repo:** `None`
- **website:** https://lingma.aliyun.com
- **aliases:** 通义灵码, Tongyi Lingma, Lingma, Alibaba Lingma
- **tool_kind:** closed
- **status:** draft / **onboard_state:** pending
- **不确定字段:** repo, notes:Closed product; ecosystem search via aliases only., tool_kind=closed (confirm)
- **备注:** Closed product; ecosystem search via aliases only.

#### Comate (`comate`)

- **vendor:** Baidu
- **primary_type:** ai-assistant
- **repo:** `None`
- **website:** https://comate.baidu.com
- **aliases:** Comate, Baidu Comate, 文心快码
- **tool_kind:** closed
- **status:** draft / **onboard_state:** pending
- **不确定字段:** repo, notes:Closed product likely., tool_kind=closed (confirm)
- **备注:** Closed product likely.

#### CodeGeeX (`codegeex`)

- **vendor:** Zhipu AI
- **primary_type:** ai-assistant
- **repo:** `THUDM/CodeGeeX`
- **website:** https://codegeex.cn
- **aliases:** CodeGeeX, codegeex, 智谱 CodeGeeX
- **tool_kind:** open
- **status:** draft / **onboard_state:** pending

#### Cline (`cline`)

- **vendor:** Cline
- **primary_type:** ide-extension
- **repo:** `cline/cline`
- **website:** https://cline.bot
- **aliases:** Cline, Claude Dev, cline.bot
- **tool_kind:** open
- **status:** draft / **onboard_state:** pending

#### Kilo Code (`kilo-code`)

- **vendor:** Kilo
- **primary_type:** ide-extension
- **repo:** `Kilo-Org/kilocode`
- **website:** https://kilo.ai
- **aliases:** Kilo Code, KiloCode, kilo-code
- **tool_kind:** open
- **status:** draft / **onboard_state:** pending

#### Junie (`junie`)

- **vendor:** JetBrains
- **primary_type:** ai-assistant
- **repo:** `None`
- **website:** https://www.jetbrains.com/junie/
- **aliases:** Junie, JetBrains Junie
- **tool_kind:** closed
- **status:** draft / **onboard_state:** pending
- **不确定字段:** repo, notes:Closed JetBrains product., tool_kind=closed (confirm)
- **备注:** Closed JetBrains product.

#### Continue (`continue`)

- **vendor:** Continue
- **primary_type:** ide-extension
- **repo:** `continuedev/continue`
- **website:** https://continue.dev
- **aliases:** Continue, Continue.dev, continue-dev
- **tool_kind:** open
- **status:** draft / **onboard_state:** pending

#### Augment Code (`augment-code`)

- **vendor:** Augment
- **primary_type:** ai-assistant
- **repo:** `None`
- **website:** https://www.augmentcode.com
- **aliases:** Augment Code, Augment, augmentcode
- **tool_kind:** closed
- **status:** draft / **onboard_state:** pending
- **不确定字段:** repo, notes:Likely closed product., tool_kind=closed (confirm)
- **备注:** Likely closed product.

#### Tabnine (`tabnine`)

- **vendor:** Tabnine
- **primary_type:** ai-assistant
- **repo:** `None`
- **website:** https://www.tabnine.com
- **aliases:** Tabnine, TabNine, tabnine
- **tool_kind:** closed
- **status:** draft / **onboard_state:** pending
- **不确定字段:** repo, notes:Closed product., tool_kind=closed (confirm)
- **备注:** Closed product.

#### Manus (`manus`)

- **vendor:** Manus
- **primary_type:** agent-platform
- **repo:** `None`
- **website:** https://manus.im
- **aliases:** Manus, Manus AI, manus.im
- **tool_kind:** closed
- **status:** draft / **onboard_state:** pending
- **不确定字段:** repo, notes:Closed agent product; ecosystem mentions only., tool_kind=closed (confirm)
- **备注:** Closed agent product; ecosystem mentions only.

#### v0.dev (`v0-dev`)

- **vendor:** Vercel
- **primary_type:** ai-builder
- **repo:** `None`
- **website:** https://v0.dev
- **aliases:** v0.dev, v0, Vercel v0
- **tool_kind:** closed
- **status:** draft / **onboard_state:** pending
- **不确定字段:** repo, notes:Closed SaaS builder., tool_kind=closed (confirm)
- **备注:** Closed SaaS builder.

#### Lovable (`lovable`)

- **vendor:** Lovable
- **primary_type:** ai-builder
- **repo:** `None`
- **website:** https://lovable.dev
- **aliases:** Lovable, Lovable.dev, GPT Engineer
- **tool_kind:** closed
- **status:** draft / **onboard_state:** pending
- **不确定字段:** repo, notes:Closed SaaS; formerly GPT Engineer ecosystem., tool_kind=closed (confirm)
- **备注:** Closed SaaS; formerly GPT Engineer ecosystem.

#### Replit (`replit`)

- **vendor:** Replit
- **primary_type:** ai-builder
- **repo:** `None`
- **website:** https://replit.com
- **aliases:** Replit, Replit Agent, Ghostwriter
- **tool_kind:** closed
- **status:** draft / **onboard_state:** pending
- **不确定字段:** repo, notes:Closed product platform., tool_kind=closed (confirm)
- **备注:** Closed product platform.

#### Bolt.new (`bolt-new`)

- **vendor:** StackBlitz
- **primary_type:** ai-builder
- **repo:** `stackblitz/bolt.new`
- **website:** https://bolt.new
- **aliases:** Bolt.new, Bolt, StackBlitz Bolt
- **tool_kind:** open
- **status:** draft / **onboard_state:** pending

#### OpenClaw (`openclaw`)

- **vendor:** OpenClaw
- **primary_type:** terminal-agent
- **repo:** `None`
- **website:** —
- **aliases:** OpenClaw, openclaw
- **tool_kind:** closed
- **status:** draft / **onboard_state:** pending
- **不确定字段:** repo, website, docs, notes:Uncertain product identity/repo — user should verify., tool_kind=closed (confirm)
- **备注:** Uncertain product identity/repo — user should verify.

## 合并策略提醒

- **CodeBuddy** ↔ 现有 `workbuddy-codebuddy`（已匹配则本报告「已匹配」区可见）
- **Codex** ↔ 现有 `codex-cli`
- **Antigravity** ↔ 现有 `antigravity-cli`
- 闭源/无主仓：`tool_kind=closed`，`repo: null`，仍用 aliases 做生态查询
- 封闭名单：不自动发现第 32 个工具

## 下一步

```bash
# 用户审改完成后：
python3 scripts/seed_tools_schema.py --validate --list-active
python3 scripts/derive_queries.py --dry-run
python3 scripts/onboard_tool.py --all-pending --dry-run
# 用户明确授权后再真实 onboard
```

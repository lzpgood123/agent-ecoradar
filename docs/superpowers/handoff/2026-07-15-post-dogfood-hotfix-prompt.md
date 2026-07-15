# 新对话 Agent 启动提示词：Post-Dogfood 小修（CSP/字体 + 路径泄露）

> 将以下全部内容复制粘贴到**新对话**中作为第一条消息。  
> 本任务是**小修复批次**，不是重跑 Batch1–4，也不是 Goal 总控。

---

## 你的任务

你是 "Search in Coding" 项目的开发 Agent。dogfood 结论为 **`SHIP_WITH_FIXES`**（可继续公开）。你只需修两个问题并重新部署：

1. **H1（High）**：CSP 与 Google Fonts 冲突 → **方案 A：去掉 Google Fonts 外链，改用系统字体栈**（不要放宽 CSP）
2. **M2（Medium）**：5 条 `official-seed` 的 summary / search-index 泄露 `/root/workspace/ai-coding-agents/...` 本地路径 → 改成公开安全文案

完成后：`build_site`（或等价重建 search-index）→ **deploy** → 用证据验收。

**不要**改评分公式、不要跑 enrich/normalize 全量、不要清全部 pending、不要动 LLM prompt。

---

## 第一步：加载技能框架

1. 优先 `skill_view("using-superpowers")`（失败则读 `HERMES.md` / `.hermes/skills/`）
2. 改代码前：相关逻辑用测试或最小回归命令验证
3. 完成前：`verification-before-completion` 思维——先有命令输出证据再声称完成
4. 若改了前端/数据展示：按需更新 `wiki/L4A` / `L6` / `L1` 相关一句

---

## 第二步：阅读上下文（只读）

必读：

1. `docs/dogfood-post-bulk-2026-07-15/report.md` — **问题真相源（H1/M2）**
2. `site/index.html` — Google Fonts link 现状
3. Nginx 站点 CSP（只读确认，默认**不改 CSP**）：常见路径  
   `/etc/nginx/sites-available/coding.lzpgood.online`
4. `data/projects.yaml` 中 5 个 official-seed（或 `data/seed-tools` / 生成 official 的源头，以实际写入 summary 的源为准）
5. `scripts/build_site.py` — 如何重建 search-index / 站点
6. 可选：`wiki/L4A-前端详解.md`、公开仓库隐私规则（若提交公开仓，禁止本机路径）

工作区：`/root/workspace/search in coding`

---

## 第三步：修复 H1（方案 A）

### 目标

- 页面**不再请求** `fonts.googleapis.com` / `fonts.gstatic.com`
- 字体使用系统栈（如 `Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` 中去掉对未加载 Inter 的硬依赖，或直接系统栈）
- **不放宽** Nginx CSP（保持 `style-src 'self'; font-src 'self'`）

### 建议步骤

1. 编辑 `site/index.html`（及任何生成 index 的模板/源，如果 index 是构建产物则改源再 build）：
   - 删除 `preconnect` 到 Google Fonts
   - 删除 Google Fonts stylesheet `<link>`
2. 检查 CSS（`site/css/*.css` 或源）：
   - `font-family` 改为可靠系统栈；可保留 `Inter` 作首位但必须有完整 fallback，避免“字体名存在但文件 404”的错觉——**推荐直接系统栈**
3. 若 CSS/HTML 经 hash 构建：跑站点构建脚本，确保线上引用的 hashed 文件同步更新
4. **不要**为了 Inter 去改 CSP 放行 Google

### 验收

```bash
# 首页 HTML 不应再出现 fonts.googleapis / fonts.gstatic
curl -sS https://coding.lzpgood.online/ | grep -iE 'fonts\.googleapis|fonts\.gstatic' && echo 'FAIL still has google fonts' || echo 'OK no google fonts links'

# CSP 仍应限制 style/font 到 self（允许确认未放宽）
curl -sSI https://coding.lzpgood.online/ | tr -d '\r' | grep -i content-security-policy
```

---

## 第四步：修复 M2（路径泄露）

### 已知 5 条（id）

| id | name |
|----|------|
| `official-claude-code` | Claude Code |
| `official-codex-cli` | OpenAI Codex CLI |
| `official-goose` | Goose |
| `official-cursor` | Cursor |
| `official-workbuddy-codebuddy` | WorkBuddy / CodeBuddy |

当前 summary 形态类似：

`Official seed profile for ..., based on local source document /root/workspace/ai-coding-agents/....md`

### 改写原则

- **删除**一切绝对路径：`/root/...`、`/home/...`、本机 workspace
- 改为公开安全描述，例如：
  - 中文/英文均可，但须专业、无内部路径
  - 示例：`Official seed profile for Claude Code (Anthropic AI coding agent).`  
  - 或保留“官方种子条目”语义，**不要**提 local source document 路径
- 若 `i18n.zh.summary` / `i18n.en.summary` 也有路径，一并清理
- 找到**源头**：是直接写在 `data/projects.yaml`，还是 seed 脚本每次覆盖？  
  - 若脚本会覆盖：改脚本/seed 源数据，避免下次管道写回路径
  - 至少保证本次 deploy 后线上干净

### 重建索引与站点

路径在 summary 里会进入 `search-index.json`，必须重建：

```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate
# 按项目惯例；通常：
python3 scripts/build_site.py
# 若 quality_gate 轻量可跑：
python3 scripts/quality_gate.py
```

确认本地：

```bash
# 应为 0 命中
rg -n '/root/workspace|/home/[^/]+/' site/data/projects.json site/data/search-index.json site/data/detail -g '*.json' || true
python3 - <<'PY'
import json,re
from pathlib import Path
pat=re.compile(r'/root/workspace|/home/')
for f in ['site/data/projects.json','site/data/search-index.json']:
    t=Path(f).read_text(encoding='utf-8',errors='replace')
    print(f, 'LEAK' if pat.search(t) else 'clean')
PY
```

---

## 第五步：Deploy

```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate
python3 scripts/deploy_site.py --dest /var/www/coding.lzpgood.online
# 或项目等价部署命令；以 scripts/deploy_site.py 为准
```

部署后**线上**再验：

```bash
curl -sS https://coding.lzpgood.online/ | grep -iE 'fonts\.googleapis|fonts\.gstatic' && echo FAIL || echo OK_fonts
curl -sS https://coding.lzpgood.online/data/search-index.json | python3 -c "import sys,re;t=sys.stdin.read();print('LEAK' if re.search(r'/root/workspace|/home/',t) else 'clean')"
curl -sS https://coding.lzpgood.online/data/projects.json | python3 -c "import sys,re;t=sys.stdin.read();print('LEAK' if re.search(r'/root/workspace|/home/',t) else 'clean')"
# 冒烟
curl -sS -o /dev/null -w 'home:%{http_code}\n' https://coding.lzpgood.online/
curl -sS -o /dev/null -w 'detail0:%{http_code}\n' https://coding.lzpgood.online/data/detail/0.json
```

---

## 第六步：Git

- 提交与本修复相关的代码/数据/站点源（**不要**提交 `.bak`、临时 skills、无关 `.agents`）
- commit message 建议：`fix: remove google fonts for CSP; scrub official-seed local paths`
- push 到 `origin/main`（遵守签名/branch protection；禁止 force push）
- 若 official 数据很大：确保 diff 可审，只改必要 summary 字段

---

## 第七步：Wiki（最小更新）

- `wiki/L6-经验录.md`：追加一条 — 公开站 CSP 与外链字体不可并存；official-seed 禁止写本机路径  
- 若 L4A 写死了 Inter/Google Fonts，改一句字体策略  
- L1 可补：dogfood `SHIP_WITH_FIXES` 后小修已上线（若你完成 deploy）

---

## 完成标准（全部满足才算完成）

- [ ] 线上 HTML **无** Google Fonts 链接
- [ ] CSP **未**为字体放宽（仍 self）
- [ ] 线上 `projects.json` / `search-index.json` **无** `/root/workspace` 或明显本机 home 路径
- [ ] 5 个 official-seed id 的 summary 已是公开安全文案
- [ ] deploy 成功；首页与 detail 分片 HTTP 200
- [ ] 相关测试/quality_gate（若跑了）通过
- [ ] git commit + push（若环境允许）
- [ ] L6 至少记一笔

---

## 明确禁止

1. 放宽 CSP 以迁就 Google Fonts（否决方案 B）
2. 全量 enrich / normalize / 多轮 LLM
3. 删除或大改 5165 条业务数据（只 scrub 文案）
4. 提交密钥、bak、本机其它项目路径
5. force push

---

## 项目环境

- 工作区：`/root/workspace/search in coding`
- 站点：https://coding.lzpgood.online/
- webroot：`/var/www/coding.lzpgood.online`
- dogfood 报告：`docs/dogfood-post-bulk-2026-07-15/report.md`
- Python：`.venv` + `python3`

---

## 最终汇报格式（中文）

1. 改了哪些文件  
2. H1：改前/改后（HTML 是否还有 Google Fonts；CSP 是否未放宽）  
3. M2：5 条 id 的新 summary 原文 + 线上 grep 无路径证据  
4. build / deploy 命令与结果  
5. commit hash / push 结果  
6. wiki 是否更新  
7. 遗留（M1 冷启动、M3 分类噪声、pending≈200 可只列不修）

---

## 评估验收清单（若另开评估对话）

- [ ] 线上无 Google Fonts 请求点
- [ ] CSP 仍为 font/style self
- [ ] 线上 JSON 无 `/root/workspace`
- [ ] 首页/搜索/详情冒烟通过
- [ ] 未引入新的公开路径/密钥泄露

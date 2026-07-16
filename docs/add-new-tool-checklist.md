# 添加新追踪工具

> 现在只需 **两步**：编辑 `data/seed-tools.yaml` → 等系统自动接入（或用命令立即接入）。

---

## 快速接入

### 方式一：只改 YAML（推荐）

在 `data/seed-tools.yaml` 末尾添加一条新工具定义：

```yaml
- id: my-new-tool          # 唯一标识，小写连字符
  name: My New Tool         # 显示名称
  aliases:                  # 各种叫法（用于搜索匹配）
    - My New Tool
    - my-new-tool
  # repo: owner/repo       # 可选：有公开主仓时填写；无则留空或省略
  status: active            # active = 立即参与采集；draft = 暂不采集
```

**就这么简单。** 系统会在次日自动：

1. 从 active 工具派生 GitHub 搜索查询（`derive_queries.py`）
2. 采集新工具相关项目（`collect_github.py`）
3. 归一化、评分、构建站点
4. 如有 pending 工具，排队标准接入（`onboard_tool.py`）
5. 优先对新项目运行 LLM 分析
6. 部署到正式站（由 LLM cron 负责）

### 方式二：立即接入（不等次日）

```bash
cd /root/workspace/agent-ecoradar
source .venv/bin/activate

# 立即接入单个工具
python3 scripts/onboard_tool.py --id my-new-tool

# 先看看会做什么（不实际执行）
python3 scripts/onboard_tool.py --id my-new-tool --dry-run

# 跳过 LLM 分析（更快，LLM 交给日常 cron）
python3 scripts/onboard_tool.py --id my-new-tool --skip-llm

# 跳过部署（只构建不发布）
python3 scripts/onboard_tool.py --id my-new-tool --skip-deploy

# 批量接入所有 pending 工具
python3 scripts/onboard_tool.py --all-pending
```

---

## 字段说明

### 最小必填字段（人手写）

| 字段 | 说明 | 示例 |
|------|------|------|
| `id` | 工具唯一标识（小写、连字符） | `windsurf` |
| `name` | 显示名称 | `Windsurf` |
| `aliases` | 搜索匹配用的各种叫法 | `["Windsurf", "Codeium Windsurf"]` |

### 可选字段

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `repo` | GitHub 仓库 `owner/repo` | 无（`tool_kind` 自动设为 `closed`） |
| `status` | `active` / `draft` / `disabled` | `active` |
| `vendor` | 厂商 | - |
| `primary_type` | 类型如 `terminal-agent` / `ai-ide` | - |
| `website` / `docs` | 官网和文档 URL | - |
| `config_files` | 配置文件类型如 `CLAUDE.md` | - |
| `extension_points` | 扩展点如 `skills` / `mcp` / `hooks` | - |
| `related_concepts` | 相关概念 | - |
| `tracking_priority` | 追踪优先级 `high` / `medium` / `low` | - |

### 系统自动管理的字段（不用手写）

| 字段 | 说明 | 由谁管理 |
|------|------|---------|
| `tool_kind` | `open`（有 repo）/ `closed`（无 repo） | `seed_tools_schema.py` 自动推断 |
| `onboard_state` | `pending` → `running` → `done` / `failed` | `onboard_tool.py` 状态机 |
| `onboarded_at` | 最近成功接入时间 | `onboard_tool.py` |
| `onboard_error` | 最近失败原因 | `onboard_tool.py` |

---

## 无主仓工具（tool_kind=closed）

有些工具没有公开的 GitHub 主仓库（如闭源 IDE）。对于这类工具：

- **省略 `repo` 字段** 或设为 `null`
- 系统自动设置 `tool_kind=closed`
- 仍会生成生态搜索查询（如 `{tool name} skills`、`{tool name} mcp`）
- 采集到的生态项目正常进入评分和展示

---

## 标准接入流水线

`onboard_tool.py` 对每个工具执行以下步骤：

```
1. 校验最小字段（id, name, aliases）
2. 标记 onboard_state=running
3. 专项采集（用工具 aliases 生成查询，限流，非全库 bulk）
4. normalize.py（合并进 projects.yaml，保护已有 LLM 字段）
5. score.py（更新可量化分 0-60）
6. 可选 LLM 分析（weekly_analysis.py --max-projects N）
7. finalize + generate_reports + build_site
8. deploy_site.py（可 --skip-deploy）
9. 标记 onboard_state=done 或 failed
```

**注意：** 标准接入 **不会** 调用 `initial_collection.py` 做全库历史 bulk。
每个工具只做增量专项采集。

---

## 批处理多个工具

```bash
# 查看哪些工具需要接入
python3 scripts/detect_seed_tools_diff.py --dry-run

# 一次性接入所有 pending 工具
python3 scripts/onboard_tool.py --all-pending

# 批处理时单工具失败不阻断后续
# failed 工具可稍后重试
```

---

## 注意事项

1. **aliases 要精确**：包含全称、连字符写法、常见缩写。避免太通用的词（如单独写 `code`、`agent`）。
2. **draft 状态**：设 `status: draft` 可先添加但不参与采集。审改后改为 `active` 即可。
3. **封闭名单**：Agent EcoRadar 追踪 31 个 AI Coding 工具（封闭名单），不自动发现名单外工具。
4. **构建 ≠ 部署**：`build_site.py` 只生成 `site/` 产物；上线需 `deploy_site.py` 或由 LLM cron 自动处理。
5. **不修改评分/schema**：如需调整评分权重，改 `config/scoring.yaml`，不要为新工具改评分逻辑。

---

## 相关脚本

| 脚本 | 作用 |
|------|------|
| `scripts/seed_tools_schema.py` | seed-tools 校验与状态管理 |
| `scripts/derive_queries.py` | 从 active 工具派生 GitHub 查询 |
| `scripts/detect_seed_tools_diff.py` | 检测需要接入的工具 |
| `scripts/onboard_tool.py` | 标准接入流水线 CLI |
| `scripts/collect_github.py` | GitHub 搜索采集 |
| `scripts/normalize.py` | 数据归一化 |
| `scripts/score.py` | 可量化评分 |
| `scripts/weekly_analysis.py` | LLM 分析 |
| `scripts/build_site.py` | 站点构建 |
| `scripts/deploy_site.py` | 部署到正式站 |

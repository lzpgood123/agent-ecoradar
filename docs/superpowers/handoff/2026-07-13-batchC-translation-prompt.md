# 新对话 Agent 启动提示词：批次 C - 翻译

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是"Search in Coding"项目的开发 Agent。你的任务是实现**批次 C：翻译**--将 274 条项目的英文 summary 通过 SenseNova API（DeepSeek-V4-Flash）翻译成中文，翻译结果缓存到 `data/translations-cache/`，并写入 `projects.yaml` 的 `i18n.zh.summary` 字段，消除「假双语」问题（dogfood 报告 Issue #3）。

## 第一步：加载技能框架

立即调用 Skill 工具加载 `using-superpowers` 技能。这是你在该项目中工作的前置要求。

## 第二步：阅读项目上下文

按 `wiki/README.md` 的阅读路线图理解项目，必读：

1. `wiki/README.md` - 项目总索引和阅读路线图
2. `wiki/L1-全景.md` - 项目是什么、核心流程
3. `wiki/L3-代码地图.md` - 代码在哪、改哪个文件

## 第三步：阅读设计文档

1. `docs/superpowers/specs/2026-07-13-site-optimization-v3-design.md` - **本次设计文档（核心）**，重点读"批次 C：翻译"章节
2. `docs/ux-dogfood-report-2026-07-13.md` - dogfood 报告，重点读 Issue #3（中英双语几乎是假双语，274/274 zh==en）

## 第四步：阅读实现计划

实现计划已存在于 `docs/superpowers/plans/2026-07-13-batchC-translation.md`，直接按计划执行。

使用 `subagent-driven-development` 技能执行实现计划。每个子 Agent 必须遵循 TDD--先写测试再写实现。

## 第五步：执行实现

按实现计划中的任务顺序执行。核心工作内容：

| 任务 | 内容 | 涉及文件 |
|------|------|---------|
| 1 | 翻译脚本核心实现（translate_summaries.py + 测试） | `scripts/translate_summaries.py`, `tests/test_translate_summaries.py` |
| 2 | 更新 .gitignore（translations-cache 不入 Git） | `.gitignore` |
| 3 | Dry-run 验证（确认 274 条待翻译） | - |
| 4 | 小批量翻译验证（3 条，验证 API 连通） | `data/projects.yaml`, `data/translations-cache/` |
| 5 | 全量翻译（274 条，3 并发，约 5-15 分钟） | `data/projects.yaml`, `data/translations-cache/` |
| 6 | 重建站点并验证（中文 UI 下 summary 显示中文） | `site/data/projects.json` |
| 7 | 更新 Wiki | `wiki/L3-代码地图.md`, `wiki/L6-经验录.md` |

### 关键技术细节

**API 调用：**
- API endpoint：`https://token.sensenova.cn/v1/chat/completions`
- 模型：`deepseek-v4-flash`
- 13 个 API key 轮询（从 `~/.hermes/auth.json` 的 `credential_pool.custom:sensenova` 读取）
- 每批 3 并发（ThreadPoolExecutor）
- urllib 做 HTTP 请求，不依赖 requests/httpx
- key 轮询 + 失败重试（最多 3 次，指数退避）

**缓存机制：**
- 翻译结果按 URL hash（md5 前 16 位）缓存到 `data/translations-cache/`
- 缓存文件 JSON 格式：`{"zh": "中文摘要", "en": "English summary"}`
- 重复运行脚本时，已缓存的项目直接从缓存读取，不重复调用 API

**写入 projects.yaml：**
- 翻译结果写入 `i18n.zh.summary` 字段
- 确保 `i18n.en.summary` 也设置（如果之前缺失）

## 第六步：验证

调用 `verification-before-completion` 技能进行验证：

- [ ] `scripts/translate_summaries.py` 可 `--dry-run`，正确显示 274 条待翻译
- [ ] `scripts/translate_summaries.py --limit 3` 实际运行成功，3 个项目被翻译
- [ ] `data/translations-cache/` 有缓存文件，JSON 格式含 `zh` 和 `en` 字段
- [ ] 全量翻译后，`i18n.zh.summary` 与 `i18n.en.summary` 不再完全相同（274/274 -> 接近 0/274）
- [ ] 站点重建后，中文 UI 下 summary 显示中文
- [ ] `data/translations-cache/` 在 `.gitignore` 中，不进入 Git
- [ ] API key 从 `~/.hermes/auth.json` 读取，代码中无硬编码 key
- [ ] 所有测试通过（`source .venv/bin/activate && python3 -m pytest tests/test_translate_summaries.py -v`）
- [ ] 站点部署到 https://coding.lzpgood.online/ 并可访问

## 第七步：更新 Wiki

开发完成后，按 wiki 各文档底部的"更新指引"更新：
- `wiki/L3-代码地图.md` - 新增 `scripts/translate_summaries.py`
- `wiki/L6-经验录.md` - 记录批量翻译的坑（API 速率限制、key 轮询、缓存机制）

## 关键约束

1. **不改前端代码**：本批只写翻译脚本 + 更新 projects.yaml，前端代码不变
2. **翻译缓存不入 Git**：`data/translations-cache/` 加入 `.gitignore`
3. **API key 不硬编码**：从 `~/.hermes/auth.json` 读取，代码中无 key
4. **TDD**：先写测试再写实现
5. **频繁 commit**：每个任务完成后 commit
6. **urllib 做 HTTP**：不依赖 requests/httpx，只用标准库

## 不能改动的部分

- 前端代码（`site/`）- 不变
- `scripts/build_site.py` - 构建逻辑不变
- `data/projects.yaml` 的数据结构 - 只更新 `i18n.zh.summary` 值
- `data/seed-tools.yaml` / `data/concepts.yaml` - 不变
- `scripts/score.py` / `scripts/normalize.py` - 不变

## 依赖关系

**本批次依赖批次 A 完成**：批次 A 修正了 summary 字段（补充缺失项目、修正字段映射），翻译需要基于最终版 summary。如果批次 A 未完成，翻译可能翻译到不完整或不准确的 summary。

## 项目环境信息

- 操作系统：Ubuntu 24.04.4 LTS（内核 6.8.0-111-generic）
- Python：3.12.3（用 python3，不要用 python）
- GitHub CLI：gh 已认证（lzpgood123）
- 工作目录：`/root/workspace/search in coding`
- 站点部署：`/var/www/coding.lzpgood.online/`（Nginx）
- 测试命令：`source .venv/bin/activate && python3 -m pytest tests/ -v`（**pytest 需要在 .venv 中运行**）
- 站点构建：`python3 scripts/build_site.py`
- 站点部署：`python3 scripts/deploy_site.py`
- LLM API 凭证：存储在 `~/.hermes/auth.json` 的 `credential_pool.custom:sensenova` 中（13 个 key）
- LLM API endpoint：`https://token.sensenova.cn/v1/chat/completions`
- LLM 模型：`deepseek-v4-flash`

## 注意事项

- **API key 安全**：不要在代码中硬编码 key，从 `~/.hermes/auth.json` 读取
- **API 速率限制**：13 个 key 轮询，遇到 429 时指数退避 + 切换 key
- **LLM 输出不稳定**：JSON 解析需要容错（code block 包裹、周围有文本等情况）
- **翻译缓存**：`data/translations-cache/` 不入 Git（已在 .gitignore 中）
- **断点续传**：如果翻译中途失败，可重复运行脚本，已缓存的项目不会重复翻译
- **全量翻译耗时**：274 条 / 3 并发 ≈ 90 轮，预计 5-15 分钟
- 用户偏好详细编号分步指导和精准区分状态含义
- 完成前必须验证对比确认无误

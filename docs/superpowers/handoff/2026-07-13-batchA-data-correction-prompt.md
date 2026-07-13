# 新对话 Agent 启动提示词：批次 A - 数据层修正

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是"Search in Coding"项目的开发 Agent。你的任务是实现**批次 A：数据层修正**--修正 seed-tools repo 路径、手动补充缺失的知名项目、修正 normalize.py 字段映射（forks/license/languages/stars/topics/readme_preview）、修正 resource_type 误标（skill 被标成 tutorial），为后续批次 B（前端审美重做）和批次 C（翻译）提供正确的数据基础。

## 第一步：加载技能框架

立即调用 Skill 工具加载 `using-superpowers` 技能。这是你在该项目中工作的前置要求。

## 第二步：阅读项目上下文

按 `wiki/README.md` 的阅读路线图理解项目，必读：

1. `wiki/README.md` - 项目总索引和阅读路线图
2. `wiki/L1-全景.md` - 项目是什么、核心流程
3. `wiki/L3-代码地图.md` - 代码在哪、改哪个文件
4. `wiki/L4B-后端详解.md` - 数据管道流程、评分系统、分类系统
5. `wiki/L6-经验录.md` - 相关坑和注意事项（重点读"双语不完整"、"分类过宽"条目）

## 第三步：阅读设计文档

1. `docs/superpowers/specs/2026-07-13-site-optimization-v3-design.md` - **本次设计文档（核心）**，重点读"批次 A：数据层修正"章节
2. `wiki/P1-产品决策日志.md` - 用户偏好和产品约束（重点读 2026-07-13 的数据修正相关决策）
3. `docs/ux-dogfood-report-2026-07-13.md` - dogfood 报告，重点读 Issue #1（评分全空）、#4（类型误标）、#12（字段空值）

## 第四步：阅读实现计划

实现计划已存在于 `docs/superpowers/plans/2026-07-13-batchA-data-correction.md`，直接按计划执行。

使用 `subagent-driven-development` 技能执行实现计划。每个子 Agent 必须遵循 TDD--先写测试再写实现。

## 第五步：执行实现

按实现计划中的任务顺序执行。核心工作内容：

| 任务 | 内容 | 涉及文件 |
|------|------|---------|
| A1 | 修正 seed-tools.yaml repo 路径（goose/cursor/opencode/qoder） | `data/seed-tools.yaml` |
| A2 | 手动补充缺失知名项目（continue/aider/cline/roo 等） | `data/projects.yaml` |
| A3 | 修正 normalize.py 字段映射（forks/license/languages/stars/topics/readme_preview） | `scripts/normalize.py` |
| A4 | 修正 resource_type 误标（至少 curated Top 40） | `scripts/normalize.py` + `data/projects.yaml` |

## 第六步：验证

调用 `verification-before-completion` 技能进行验证：

- [ ] `data/seed-tools.yaml` 中 goose/cursor/opencode/qoder 的 repo 路径正确
- [ ] `data/projects.yaml` 新增 continue/aider/cline/roo 等缺失项目
- [ ] `forks` 字段非空率显著提升（从 0/274 改善）
- [ ] `license` 字段非空率显著提升（从 0/274 改善）
- [ ] `languages` 字段 null 值显著减少（从 67 条减少）
- [ ] `stars` 字段缺失条目减少（从 63 条减少）
- [ ] curated Top 40 高星项目 resource_type 不再有 skill 误标为 tutorial
- [ ] 所有测试通过（`source .venv/bin/activate && python3 -m pytest tests/ -v`）
- [ ] `python3 scripts/build_site.py` 正常构建
- [ ] 站点部署到 https://coding.lzpgood.online/ 并可访问

## 第七步：更新 Wiki

开发完成后，按 wiki 各文档底部的"更新指引"更新：
- `wiki/L1-全景.md` - 更新项目状态（数据修正完成）
- `wiki/L3-代码地图.md` - 如有新增脚本则更新
- `wiki/L4B-后端详解.md` - 更新字段映射说明
- `wiki/L6-经验录.md` - 记录数据修正的坑

## 关键约束

1. **不改前端代码**：本批只修正数据层，前端代码（`site/`）由批次 B 处理
2. **不改数据结构**：`projects.yaml` 字段不变，只补全/修正值
3. **不改 build_site.py**：构建逻辑不变
4. **TDD**：normalize.py 的修改先写测试
5. **频繁 commit**：每个任务完成后 commit
6. **用 gh CLI 获取项目数据**：`gh repo view --json` 补充缺失项目

## 不能改动的部分

- `data/concepts.yaml` - 概念定义不变
- 前端代码（`site/`）- 批次 B 处理
- `scripts/build_site.py` - 构建逻辑不变
- `scripts/score.py` 的 quantifiable_score 逻辑 - 不变
- 数据字段结构（只改值，不改字段名）

## 项目环境信息

- 操作系统：Ubuntu 24.04.4 LTS（内核 6.8.0-111-generic）
- Python：3.12.3（用 python3，不要用 python）
- GitHub CLI：gh 已认证（lzpgood123）
- 工作目录：`/root/workspace/search in coding`
- 站点部署：`/var/www/coding.lzpgood.online/`（Nginx）
- 测试命令：`source .venv/bin/activate && python3 -m pytest tests/ -v`（**pytest 需要在 .venv 中运行**）
- Pipeline 入口：`python3 scripts/update_tracker.py --skip-collect`
- 站点构建：`python3 scripts/build_site.py`
- 站点部署：`python3 scripts/deploy_site.py`

## 注意事项

- 补充缺失项目时用 `gh repo view <org>/<repo> --json name,description,stargazerCount,forkCount,licenseInfo,primaryLanguage,languages,repositoryTopics,url,updatedAt` 获取完整数据
- normalize.py 字段映射修正后，需要重新对已有数据跑一遍 normalize 或手动修正
- resource_type 误标修正需要人工判断，不能纯靠关键词规则
- 用户偏好详细编号分步指导和精准区分状态含义
- 完成前必须验证对比确认无误

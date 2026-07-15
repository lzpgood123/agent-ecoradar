# ⛔ 已废弃 — 请使用 `2026-07-14-batch1-push-only-prompt.md`

> 本文档被 2026-07-14 handoff grilling 否决：批次1 改为 **只 push 不 deploy**，编号与顺序已重排。  
> 真相源：`docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`

# 新对话 Agent 启动提示词：批次 1 - push + deploy（历史稿）

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是 "Search in Coding" 项目的开发 Agent。你的任务非常简单但关键：**将已完成的 5165 条数据推送到 GitHub 和线上站点**。

当前状态：一次性历史回溯 bulk 采集已完成，`data/projects.yaml` 从 293 条增长到 5165 条，本地 commit `8571786` 已就绪但**未 push、未 deploy**。本地衍生链路（validate / score / finalize / reports / build / quality_gate）已全部 PASS。

**你只做两件事：git push + deploy。不修改任何代码或数据。**

---

## 第一步：加载技能框架

1. 优先调用 `skill_view("using-superpowers")`（或项目内等价 skill）。
2. **若加载失败**：不要停工。回退阅读并遵守：
   - 工作区 `HERMES.md`（superpowers-zh 规则）
   - `.hermes/skills/` 下相关 skill
3. 本任务不涉及代码修改，无需 TDD。

---

## 第二步：阅读项目上下文

必读：

1. `wiki/README.md` - 总索引与阅读路线
2. `wiki/L1-全景.md` - 当前状态（注意"本地未 push/deploy"）

快速核对：

```bash
cd "/root/workspace/search in coding"
git log --oneline -5          # 确认 commit 8571786 在最新
git status                     # 确认工作区干净
python3 -c "
import yaml
with open('data/projects.yaml') as f:
    projects = yaml.safe_load(f)
print(f'Total projects: {len(projects)}')
"  # 确认数据条数 5165
```

---

## 第三步：执行 push

```bash
cd "/root/workspace/search in coding"
git push origin main
```

**验证**：
- push 成功，无冲突
- GitHub 仓库 https://github.com/lzpgood123/search-in-coding 显示最新 commit

---

## 第四步：执行 deploy

```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate
python3 scripts/deploy_site.py --dest /var/www/coding.lzpgood.online
```

**注意**：
- `deploy_site.py` 从 `site/` 目录复制到 webroot
- 如果 `SEARCH_IN_CODING_WEBROOT` 环境变量已设置，可省略 `--dest`
- 部署后自动 `chown -R www-data:www-data`

---

## 第五步：验证站点

1. **访问站点**：https://coding.lzpgood.online/
2. **检查数据条数**：页面 Hero 区域应显示 5165 条项目
3. **检查搜索功能**：输入关键词，确认结果正常
4. **检查详情面板**：点击项目，确认详情正常加载
5. **检查报告页面**：点击导航中的报告链接，确认报告可访问

```bash
# 命令行验证
curl -s https://coding.lzpgood.online/data/metrics.json | python3 -m json.tool | head -20
# 确认 "projects": 5165

curl -s https://coding.lzpgood.online/data/projects.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Projects in JSON: {len(data)}')
print(f'Sample: {data[0][\"name\"] if data else \"empty\"}')
"
```

---

## 关键约束

1. **不修改任何代码或数据** - 只执行 push 和 deploy
2. **不运行采集脚本** - 不执行 `initial_collection.py`、`collect_github.py` 等
3. **不运行 normalize/score/finalize** - 本地衍生链路已跑过，不需重跑
4. **如果 push 有冲突**：`git pull --rebase origin main` 后再 push；如仍冲突，停下来报告
5. **如果 deploy 失败**：检查 `site/index.html` 是否存在、webroot 路径是否正确、权限是否足够

---

## 项目环境信息

- 工作目录：`/root/workspace/search in coding`
- Python：3.12.3（`python3`）；虚拟环境 `.venv`
- GitHub 仓库：https://github.com/lzpgood123/search-in-coding
- 线上站点：https://coding.lzpgood.online/（Nginx + Let's Encrypt TLS）
- webroot：`/var/www/coding.lzpgood.online`
- 当前数据：5165 条（github 5155 + official-seed 10）
- 本地 commit：`8571786`（未 push）

---

## 最终汇报格式

完成后用中文汇报：

1. `git push` 结果（commit hash、是否有冲突）
2. `deploy_site.py` 输出（文件数、目标路径）
3. 站点验证结果（条数、搜索、详情、报告）
4. `metrics.json` 中 `projects` 字段值
5. 如有任何异常或警告，如实报告

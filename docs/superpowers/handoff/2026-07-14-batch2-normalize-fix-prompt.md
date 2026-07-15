# ⛔ 已废弃 — 请使用 `2026-07-14-batch3-data-normalize-deploy-prompt.md`

> 本文档被 2026-07-14 handoff grilling 取代：数据/normalize 现为**新批次3**，且含第一次 deploy；并取消 cli-tool 兜底等决策。  
> 真相源：`docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md`

# 新对话 Agent 启动提示词：批次 2 - 补全 readme_preview + 改进 normalize（历史稿）

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是 "Search in Coding" 项目的开发 Agent。你的任务是**改进数据质量**：

1. 对约 4874 个无 `readme_preview` 的项目批量获取 README 前 500 字符
2. 改进 `normalize.py` 的 `resource_types_for()` 和 `target_tools_for()`，利用 `topics` 字段提升分类准确率
3. 重新跑 normalize + score + build_site + quality_gate
4. 验证 tutorial 占比下降、general-ai-coding 占比下降

**前置条件**：批次 1（push + deploy）已完成。

---

## 第一步：加载技能框架

1. 优先调用 `skill_view("using-superpowers")`（或项目内等价 skill）。
2. **若加载失败**：不要停工。回退阅读并遵守：
   - 工作区 `HERMES.md`（superpowers-zh 规则）
   - `.hermes/skills/` 下相关 skill（如 `test-driven-development`、`verification-before-completion`、`wiki-checkpoint`）
3. 本任务必须 TDD：先改/加测试，pytest 全绿后再跑管道。

---

## 第二步：阅读项目上下文

必读：

1. `wiki/README.md` - 总索引与阅读路线
2. `wiki/L1-全景.md` - 当前状态
3. `wiki/L3-代码地图.md` - 重点 `scripts/normalize.py`、`scripts/enrich_projects.py`、`scripts/score.py`
4. `wiki/L4B-后端详解.md` - 分类系统、数据管道、安全 merge
5. `wiki/L6-经验录.md` - 相关坑（#16 gh CLI 不支持 readme 字段、#19 resource_type 误标、#22 字段填充率）
6. `docs/superpowers/specs/2026-07-14-post-bulk-optimization-design.md` - **设计文档（本任务的设计依据）**

实现前先核对事实（用工具读代码/数据，不要凭记忆）：

- `scripts/normalize.py` 的 `resource_types_for()` 和 `target_tools_for()` 现状
- `scripts/enrich_projects.py` 的 `fetch_readme()` 和 `needs_enrichment()` 现状
- `data/projects.yaml` 中 `topics` 字段的填充情况
- 当前分类分布：tutorial 52.3%、general-ai-coding 62.1%、readme_preview 仅 5.6%

```bash
cd "/root/workspace/search in coding"
python3 -c "
import yaml
from collections import Counter
with open('data/projects.yaml') as f:
    projects = yaml.safe_load(f)
total = len(projects)
no_readme = sum(1 for p in projects if not p.get('readme_preview'))
has_topics = sum(1 for p in projects if p.get('topics'))
tutorial = sum(1 for p in projects if 'tutorial' in (p.get('resource_type') or []))
general = sum(1 for p in projects if 'general-ai-coding' in (p.get('target_tools') or []))
print(f'Total: {total}')
print(f'No readme_preview: {no_readme} ({no_readme/total*100:.1f}%)')
print(f'Has topics: {has_topics} ({has_topics/total*100:.1f}%)')
print(f'Tutorial: {tutorial} ({tutorial/total*100:.1f}%)')
print(f'general-ai-coding: {general} ({general/total*100:.1f}%)')
"
```

---

## 第三步：补全 readme_preview

### 3.1 确认 enrich_projects.py 可用

`scripts/enrich_projects.py` 已实现 README 获取：
- `fetch_readme(full_name)`: 通过 `gh api repos/{full_name}/readme --jq .content` + base64 解码
- `clean_readme_preview(readme, limit=500)`: 清理 HTML 标签，截取前 500 字符
- `needs_enrichment(project)`: 检查 `readme_preview` 是否为空
- 断点续传：每 5 批保存 `data/projects.yaml`
- 并发：`--batch-size` 参数（默认 3）

### 3.2 执行

```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate

# 批量获取 README，5 并发
python3 scripts/enrich_projects.py --batch-size 5

# 预计耗时：4874 条 ÷ 5 并发 ≈ 975 批 × ~3s/批 ≈ 50 分钟
# 中断后可重复运行，已获取的会跳过
```

### 3.3 验证

```bash
python3 -c "
import yaml
with open('data/projects.yaml') as f:
    projects = yaml.safe_load(f)
total = len(projects)
has_readme = sum(1 for p in projects if p.get('readme_preview'))
print(f'readme_preview 填充率: {has_readme}/{total} = {has_readme/total*100:.1f}%')
"
# 目标：≥ 60%
```

**注意**：
- `gh repo view --json` **不支持** `readme` 字段（L6 #16），必须用 `gh api repos/{repo}/readme --jq .content`
- `forks=0`、`topics=[]` 是合法填充值，不应触发重新获取（L6 #22）
- 部分 repo 可能无 README（返回空），这是正常结果

---

## 第四步：改进 normalize.py

### 4.1 改进 resource_types_for()

**当前签名**：`resource_types_for(text: str) -> list[str]`

**改为**：`resource_types_for(text: str, topics: list[str] = None) -> list[str]`

**改动要点**：

1. **新增 topics 检查**（在 Phase 1 具体类型匹配之后、tutorial 兜底之前）：

```python
# Phase 1.5: 检查 topics 字段
if topics:
    topics_lower = [t.lower() for t in topics]
    TOPIC_TO_TYPE = {
        'mcp-server': 'mcp-server',
        'model-context-protocol': 'mcp-server',
        'mcp': 'mcp-server',
        'claude-skills': 'skills',
        'agent-skills': 'skills',
        'skills': 'skills',
        'cursor-rules': 'rules',
        'cursorrules': 'rules',
        'rules': 'rules',
        'agent-framework': 'agent-framework',
        'multi-agent': 'agent-framework',
        'cli': 'cli-tool',
        'cli-tool': 'cli-tool',
        'command-line': 'cli-tool',
    }
    for topic in topics_lower:
        if topic in TOPIC_TO_TYPE and TOPIC_TO_TYPE[topic] not in types:
            types.append(TOPIC_TO_TYPE[topic])
```

2. **扩展关键词列表**（在 `RESOURCE_TYPE_RULES` 中补充）：

| 标签 | 新增关键词 |
|------|-----------|
| mcp-server | `mcp tool`, `mcp integration`, `mcp gateway`, `mcp hub` |
| skills | `claude code skills`, `agent skills`, `skill library`, `prompt library`, `command library` |
| rules | `coding rules`, `ai rules`, `behavioral guidance`, `system prompt` |
| agent-framework | `agent runtime`, `agent platform`, `agent sdk`, `coding agent`, `code agent` |
| cli-tool | `developer tool`, `devtool`, `code assistant`, `ai assistant`, `code completion` |

3. **改进 tutorial 兜底逻辑**：

```python
# 当前：return types or ['tutorial']
# 改为：
if types:
    return types

# 无任何具体类型匹配时的兜底
if topics:
    topics_lower = [t.lower() for t in topics]
    AI_CODING_HINTS = ['ai', 'llm', 'gpt', 'agent', 'coding', 'developer', 'programming',
                       'machine-learning', 'deep-learning', 'nlp', 'code', 'dev']
    if any(hint in ' '.join(topics_lower) for hint in AI_CODING_HINTS):
        return ['cli-tool']  # 通用开发工具，比 tutorial 更合理

return ['tutorial']  # 真正不确定才兜底
```

4. **更新调用处**：`github_record()` 中调用 `resource_types_for(text)` 改为 `resource_types_for(text, topics)`，将已提取的 `topics` 列表传入。

### 4.2 改进 target_tools_for()

**当前签名**：`target_tools_for(text: str, tools: list) -> list[str]`

**改为**：`target_tools_for(text: str, tools: list, topics: list[str] = None) -> list[str]`

**改动要点**：

1. **新增 topics 检查**（在现有 alias 匹配之后）：

```python
# 检查 topics 中的工具关联
if topics:
    topics_lower = [t.lower() for t in topics]
    for t in tools:
        aliases = [a.lower() for a in t.get('aliases', []) + [t.get('id', '')]]
        for topic in topics_lower:
            if any(a in topic or topic in a for a in aliases):
                if t['id'] not in ids:
                    ids.append(t['id'])
```

2. **改进兜底逻辑**：

```python
# 当前：return ids or ['general-ai-coding']
# 改为：
if ids:
    return ids

# 无匹配时的兜底
if topics:
    topics_lower = [t.lower() for t in topics]
    AI_HINTS = ['ai', 'llm', 'gpt', 'agent', 'coding', 'developer', 'programming']
    if any(hint in ' '.join(topics_lower) for hint in AI_HINTS):
        return ['general-ai-coding']  # AI 相关但无明确工具，标泛生态

return []  # 真正无关联，返回空列表
```

3. **更新调用处**：`github_record()` 中调用 `target_tools_for(text, tools)` 改为 `target_tools_for(text, tools, topics)`。

### 4.3 注意事项

- `github_record()` 中 `topics` 变量在调用 `resource_types_for()` 和 `target_tools_for()` 之前已提取，直接传入即可
- **安全 merge**：`normalize.py` 的 `main()` 和 `from_github()` 的 merge 逻辑必须保留 LLM 字段（`quality_score`, `quality_detail`, `tracking_priority`, `last_analyzed`, `benchmark_ref`）。当前 merge 逻辑在 `main()` 中用 `by[url] = r` 整条覆盖 —— **检查这是否会冲掉 LLM 字段**。如果会，改为安全 merge（只更新 GitHub 可量化字段，保留 LLM 字段）
- **official-seed 保护**：`source_type=official-seed` 的记录不被降级

---

## 第五步：测试（TDD）

在 `tests/test_normalize_fields.py` 中新增/修改测试：

```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate

# 1. 测试 resource_types_for 带 topics 参数
#    - topics 含 'mcp-server' -> 标 mcp-server
#    - topics 含 'claude-skills' -> 标 skills
#    - 无 text 匹配但 topics 含 'ai' -> 标 cli-tool（非 tutorial）
#    - 无 text 匹配且 topics 为空 -> 标 tutorial（兜底）

# 2. 测试 target_tools_for 带 topics 参数
#    - topics 含 'claude-code' -> 关联 claude-code
#    - topics 含 'cursor' -> 关联 cursor
#    - 无匹配且 topics 含 'ai' -> ['general-ai-coding']
#    - 无匹配且 topics 为空 -> []

# 3. 测试扩展关键词
#    - 'mcp gateway' -> mcp-server
#    - 'agent sdk' -> agent-framework
#    - 'code assistant' -> cli-tool

# 4. 测试安全 merge 不冲掉 LLM 字段
#    - 已有 quality_score=25 的项目，normalize 后 quality_score 仍为 25

python3 -m pytest tests/ -v
```

**全绿后才允许**执行管道重跑。

---

## 第六步：重新跑管道

```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate

python3 scripts/normalize.py
python3 scripts/score.py
python3 scripts/finalize_data.py
python3 scripts/generate_reports.py
python3 scripts/build_site.py
python3 scripts/quality_gate.py

# 等价：python3 scripts/update_tracker.py --skip-collect
# 注意：不要加 --deploy
```

---

## 第七步：验证

```bash
python3 -c "
import yaml
from collections import Counter
with open('data/projects.yaml') as f:
    projects = yaml.safe_load(f)
total = len(projects)

# readme_preview 填充率
has_readme = sum(1 for p in projects if p.get('readme_preview'))
print(f'readme_preview: {has_readme}/{total} = {has_readme/total*100:.1f}% (目标 ≥60%)')

# tutorial 占比
tutorial = sum(1 for p in projects if 'tutorial' in (p.get('resource_type') or []))
print(f'tutorial: {tutorial}/{total} = {tutorial/total*100:.1f}% (目标 ≤30%)')

# general-ai-coding 占比
general = sum(1 for p in projects if 'general-ai-coding' in (p.get('target_tools') or []))
print(f'general-ai-coding: {general}/{total} = {general/total*100:.1f}% (目标 ≤45%)')

# 空 target_tools
empty_tools = sum(1 for p in projects if not p.get('target_tools'))
print(f'empty target_tools: {empty_tools}/{total} = {empty_tools/total*100:.1f}%')

# resource_type 分布
rt_counter = Counter()
for p in projects:
    for rt in (p.get('resource_type') or []):
        rt_counter[rt] += 1
print('Resource type breakdown:')
for rt, cnt in rt_counter.most_common():
    print(f'  {rt}: {cnt} ({cnt/total*100:.1f}%)')

# LLM 字段抽查（安全 merge 验证）
analyzed = [p for p in projects if p.get('quality_score', 0) > 0]
print(f'LLM analyzed (quality_score > 0): {len(analyzed)}')
if analyzed:
    sample = analyzed[0]
    print(f'  Sample: {sample.get(\"name\")} - quality_score={sample.get(\"quality_score\")}, last_analyzed={sample.get(\"last_analyzed\")}')
"
```

---

## 关键约束

1. **安全 merge 保留 LLM 字段** - `quality_score`, `quality_detail`, `tracking_priority`, `last_analyzed`, `benchmark_ref` 不被覆盖
2. **TDD** - 先改测试，pytest 全绿后再跑管道
3. **不 deploy 不 push** - 只本地修改和验证
4. **不改评分公式** - `score.py` 逻辑不变
5. **不改 prompt 模板** - `llm_prompts.py` 不变
6. **official-seed 保护** - `tracking_priority=track` 不变
7. **enrich_projects.py 可中断续跑** - 已支持断点续传，中断后重跑即可
8. **技能加载失败要回退** - 不卡死

---

## 项目环境信息

- 工作目录：`/root/workspace/search in coding`
- Python：3.12.3（`python3`）；测试用 `source .venv/bin/activate && python3 -m pytest tests/ -v`
- GitHub CLI：`gh` 已认证
- 当前数据：5165 条；readme_preview 仅 5.6%；tutorial 52.3%；general-ai-coding 62.1%
- 管道：`python3 scripts/update_tracker.py --skip-collect`（不要加 `--deploy`）

---

## 最终汇报格式

完成后用中文汇报：

1. 改了哪些文件
2. 测试结果（命令 + 通过数）
3. readme_preview 填充率：前 -> 后
4. tutorial 占比：前 -> 后
5. general-ai-coding 占比：前 -> 后
6. resource_type 分布对比
7. LLM 字段抽查：安全 merge 未损坏证据
8. pipeline 各步结果
9. commit hash
10. 已知限制或遗留问题

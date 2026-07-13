# 批次 A：数据层修正 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。每个任务结束后必须 commit。遇到 `gh` 命令失败时先检查网络和认证状态（`gh auth status`），不要跳过验证步骤。

**目标：** 修正 seed-tools.yaml 中 4 个错误 repo 路径；手动补充 6 个缺失知名项目；修正 normalize.py 字段映射（forks/license/languages/stars/topics）并新增 readme_preview 字段；修正 curated Top 40 项目中 skill 被误标为 tutorial 的 resource_type 问题。

**架构：** 本批次纯数据层修改，不涉及前端。任务 1~3 修改数据文件和采集/归一化脚本，任务 4 修改 resource_types_for() 匹配逻辑并重新生成 curated-projects.yaml。所有 `gh repo view` 命令需要认证过的 GitHub CLI。

**技术栈：** Python 3.12+, GitHub CLI (gh), PyYAML, pytest

**关联文档：**
- 设计规格：`docs/superpowers/specs/2026-07-13-site-optimization-v3-design.md`（批次 A 章节）
- 前置批次：`docs/superpowers/plans/2026-07-12-batch1-data-foundation.md`
- 数据字典：`docs/data-dictionary.md`

---

## 文件结构

### 新建文件

| 文件 | 职责 |
|------|------|
| `scripts/add_missing_projects.py` | 通过 `gh repo view` 获取缺失知名项目信息，用 normalize.py 的 github_record() 格式加入 projects.yaml |

### 修改文件

| 文件 | 修改内容 |
|------|---------|
| `data/seed-tools.yaml` | 修正 goose/cursor/opencode/qoder 的 repo 路径 |
| `scripts/collect_github.py` | repo_view() 函数的 `--json` fields 添加 `readme` |
| `scripts/normalize.py` | github_record() 修正字段映射 + 新增 topics/readme_preview；resource_types_for() 改进匹配逻辑 |
| `data/projects.yaml` | 重新归一化后更新（forks/license/languages/topics/readme_preview 填充） |
| `data/curated-projects.yaml` | 重新生成，修正 resource_type 误标 |

---

## 任务 1：修正 seed-tools.yaml repo 路径

**文件：**
- 修改：`data/seed-tools.yaml`

**问题说明：** 以下 4 个工具的 `repo` 字段路径错误或不完整，导致 `gh repo view` 无法获取正确的仓库信息：

| 工具 ID | 当前 repo | 正确 repo | 原因 |
|---------|----------|----------|------|
| goose | `aaif-goose/goose` | `block/goose` | Block 收购后仓库迁移 |
| cursor | `cursor/cursor` | `getcursor/cursor` | org 名错误 |
| opencode | `anomalyco/opencode` | `sst/opencode` | 仓库已迁移到 sst org |
| qoder | `qoderAI` | `QoderAI/qoder` | 缺少 org 前缀，格式不完整 |

- [ ] **步骤 1：验证正确 repo 路径**

逐个验证正确路径是否存在：

```bash
cd "/root/workspace/search in coding"
gh repo view block/goose --json nameWithOwner,url 2>&1 | head -5
gh repo view getcursor/cursor --json nameWithOwner,url 2>&1 | head -5
gh repo view sst/opencode --json nameWithOwner,url 2>&1 | head -5
gh repo view QoderAI/qoder --json nameWithOwner,url 2>&1 | head -5
```

预期：每个命令输出包含 `nameWithOwner` 和 `url` 的 JSON，无错误。如果某个 repo 路径不存在，需要搜索正确路径：`gh search repos "qoder" --limit 5 --json fullName,description,stargazersCount`

- [ ] **步骤 2：修正 seed-tools.yaml 中的 4 个 repo 路径**

使用 patch 工具修改 `data/seed-tools.yaml`，将以下 4 处 repo 值替换：

1. `"repo": "aaif-goose/goose"` → `"repo": "block/goose"`
2. `"repo": "cursor/cursor"` → `"repo": "getcursor/cursor"`
3. `"repo": "anomalyco/opencode"` → `"repo": "sst/opencode"`
4. `"repo": "qoderAI"` → `"repo": "QoderAI/qoder"`

- [ ] **步骤 3：验证修改后路径可访问**

```bash
cd "/root/workspace/search in coding"
for repo in block/goose getcursor/cursor sst/opencode QoderAI/qoder; do
  echo "=== $repo ==="
  gh repo view "$repo" --json nameWithOwner,stargazerCount 2>&1 | head -3
done
```

预期：全部 4 个 repo 都能返回 nameWithOwner 和 stargazerCount，无错误。

- [ ] **步骤 4：Commit**

```bash
cd "/root/workspace/search in coding"
git add data/seed-tools.yaml
git commit -m "fix: correct repo paths in seed-tools.yaml (goose→block, cursor→getcursor, opencode→sst, qoder→QoderAI/qoder)"
```

---

## 任务 2：手动补充缺失知名项目

**文件：**
- 创建：`scripts/add_missing_projects.py`

**问题说明：** 以下 6 个知名 AI coding agent 生态项目在 projects.yaml 中缺失，需要通过 `gh repo view` 获取信息并加入数据集：

| 项目 | 说明 |
|------|------|
| `continuedev/continue` | Continue — 开源 AI 代码助手 VSCode/JetBrains 插件 |
| `paul-gauthier/aider` | Aider — 命令行 AI pair programming 工具 |
| `cline/cline` | Cline — VSCode 自主编码 agent |
| `RooCodeInc/Roo-Code` | Roo Code (原 Roo Vet) — VSCode AI coding agent |
| `block/goose` | Goose — Block 的开源 AI agent |
| `getcursor/cursor` | Cursor — AI IDE |

- [ ] **步骤 1：创建 add_missing_projects.py 脚本**

```python
#!/usr/bin/env python3
"""Manually add missing well-known projects to data/projects.yaml.

Uses `gh repo view` to fetch repo details, then normalizes via
normalize.github_record() and merges into projects.yaml (dedup by URL).
"""
import argparse
import json
import sys
import datetime
from pathlib import Path

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_jsonish, save_jsonish, run
from normalize import github_record, resource_types_for, target_tools_for

MISSING_REPOS = [
    'continuedev/continue',
    'paul-gauthier/aider',
    'cline/cline',
    'RooCodeInc/Roo-Code',
    'block/goose',
    'getcursor/cursor',
]


def fetch_repo_details(full_name):
    """Fetch repo details via gh repo view with all needed fields including readme."""
    fields = (
        'nameWithOwner,description,url,homepageUrl,'
        'stargazerCount,forkCount,licenseInfo,repositoryTopics,'
        'primaryLanguage,pushedAt,createdAt,updatedAt,isArchived,'
        'latestRelease,readme'
    )
    cmd = f'gh repo view {full_name} --json {fields}'
    r = run(cmd, timeout=120)
    if r.returncode != 0:
        print(f'  WARNING: failed to fetch {full_name}: {r.stderr.strip()}', file=sys.stderr)
        return None
    return json.loads(r.stdout or '{}')


def main():
    ap = argparse.ArgumentParser(description='Add missing well-known projects to projects.yaml')
    ap.add_argument('--dry-run', action='store_true', help='Print what would be added without writing')
    ap.add_argument('--repos', nargs='*', default=MISSING_REPOS, help='Repo full names to add')
    args = ap.parse_args()

    tools = load_jsonish('data/seed-tools.yaml')
    existing = load_jsonish('data/projects.yaml') if (ROOT / 'data/projects.yaml').exists() else []

    # Build URL set for dedup
    existing_urls = {p.get('url') for p in existing if p.get('url')}
    by_url = {p.get('url'): p for p in existing if p.get('url')}

    now = datetime.date.today().isoformat()
    added = []
    skipped = []

    for repo_full in args.repos:
        print(f'Fetching {repo_full}...')
        details = fetch_repo_details(repo_full)
        if not details:
            skipped.append(repo_full)
            continue

        url = details.get('url') or f'https://github.com/{repo_full}'
        if url in existing_urls:
            print(f'  SKIP: {repo_full} already exists (url={url})')
            skipped.append(repo_full)
            continue

        rec = github_record(details, tools)
        if not rec:
            print(f'  SKIP: {repo_full} produced null record')
            skipped.append(repo_full)
            continue

        # Add readme_preview
        readme = details.get('readme') or ''
        rec['readme_preview'] = readme[:500] if readme else ''

        # Add topics
        topics_raw = details.get('repositoryTopics') or []
        if isinstance(topics_raw, list):
            rec['topics'] = [t.get('name') if isinstance(t, dict) else t for t in topics_raw]
        else:
            rec['topics'] = []

        rec['first_seen'] = now
        rec['last_seen'] = now
        rec['tracking_priority'] = 'track'  # manually added = high priority

        added.append(rec)
        by_url[url] = rec
        print(f'  ADDED: {repo_full} (stars={rec.get("stars")}, types={rec.get("resource_type")})')

    # Merge: existing + added
    all_projects = list(by_url.values())

    stats = {
        'fetched': len(args.repos),
        'added': len(added),
        'skipped': len(skipped),
        'total_before': len(existing),
        'total_after': len(all_projects),
    }
    print(json.dumps(stats, ensure_ascii=False, indent=2))

    if not args.dry_run and added:
        save_jsonish('data/projects.yaml', all_projects)
        print(f'Written {len(all_projects)} projects to data/projects.yaml')
    elif args.dry_run:
        print('(dry-run, no changes written)')


if __name__ == '__main__':
    main()
```

- [ ] **步骤 2：Dry-run 验证脚本**

```bash
cd "/root/workspace/search in coding"
python3 scripts/add_missing_projects.py --dry-run
```

预期：输出 6 个 repo 的 fetch 结果，显示 added 和 skipped 统计。如果某些 repo 已存在则显示 SKIP。

- [ ] **步骤 3：执行实际添加**

```bash
cd "/root/workspace/search in coding"
python3 scripts/add_missing_projects.py
```

预期：新增 0~6 条记录（取决于哪些已存在），total_after 比 total_before 增加。

- [ ] **步骤 4：验证新增项目存在于 projects.yaml**

```bash
cd "/root/workspace/search in coding"
python3 -c "
import yaml
data = yaml.safe_load(open('data/projects.yaml'))
target_repos = ['continuedev/continue','paul-gauthier/aider','cline/cline','RooCodeInc/Roo-Code','block/goose','getcursor/cursor']
for repo in target_repos:
    found = [p for p in data if p.get('repo','').lower() == repo.lower()]
    status = f'OK stars={found[0].get(\"stars\")}' if found else 'MISSING'
    print(f'{repo:<35} {status}')
"
```

预期：全部 6 个项目显示 OK，每个都有 stars 值。

- [ ] **步骤 5：Commit**

```bash
cd "/root/workspace/search in coding"
git add scripts/add_missing_projects.py data/projects.yaml
git commit -m "feat: add 6 missing well-known projects (continue, aider, cline, roo, goose, cursor)"
```

---

## 任务 3：修正 normalize.py 字段映射 + 新增 readme_preview

**文件：**
- 修改：`scripts/collect_github.py`
- 修改：`scripts/normalize.py`

**问题说明：**

当前数据质量问题（来自 dogfood 报告 + spec 设计文档）：

| 字段 | 当前状态 | 根因 |
|------|---------|------|
| forks | 274/274 条为 null | 搜索结果不含 forkCount，repo-details 有但可能被搜索结果覆盖 |
| license | 274/274 条为 null | 同上，licenseInfo 只在 repo_view 中获取 |
| languages | 67 条为 null | primaryLanguage 提取逻辑有缺陷 |
| stars | 63 条缺失 | stargazersCount vs stargazerCount 字段名不一致 |
| topics | 不存在 | 未提取 repositoryTopics |
| readme_preview | 不存在 | 未获取 readme 字段 |

- [ ] **步骤 1：修改 collect_github.py 的 repo_view() 添加 readme 字段**

在 `scripts/collect_github.py` 的 `repo_view()` 函数中，将 `readme` 加入 `--json` fields 列表。

当前代码（第 14~16 行）：
```python
def repo_view(full_name):
    fields='nameWithOwner,description,url,homepageUrl,stargazerCount,forkCount,licenseInfo,repositoryTopics,primaryLanguage,pushedAt,createdAt,updatedAt,isArchived,latestRelease'
    cmd=f"gh repo view {full_name} --json {fields}"
```

修改为：
```python
def repo_view(full_name):
    fields='nameWithOwner,description,url,homepageUrl,stargazerCount,forkCount,licenseInfo,repositoryTopics,primaryLanguage,pushedAt,createdAt,updatedAt,isArchived,latestRelease,readme'
    cmd=f"gh repo view {full_name} --json {fields}"
```

- [ ] **步骤 2：修改 normalize.py 的 github_record() 函数**

将 `scripts/normalize.py` 的 `github_record()` 函数（第 44~82 行）替换为以下修正版本。关键修改点：

1. **stars**：兼容 `stargazerCount` 和 `stargazersCount`
2. **forks**：兼容 `forkCount` 和 `forks`
3. **license**：正确提取 `licenseInfo.spdxId`，处理 null
4. **languages**：优先用 `primaryLanguage.name`，处理 null
5. **topics**（新增）：从 `repositoryTopics` 提取 topic name 列表
6. **readme_preview**（新增）：从 `readme` 字段截取前 500 字符
7. **优先使用 repo-details 数据**：当同一 repo 同时出现在搜索结果和 repo-details 中时，repo-details 数据更完整，应优先

替换后的完整函数：

```python
def github_record(it, tools):
    fn = it.get('fullName') or it.get('nameWithOwner')
    url = it.get('url') or (f'https://github.com/{fn}' if fn else None)
    name = fn or it.get('name') or url
    if not url or not name:
        return None
    desc = it.get('description') or ''
    text = f'{name} {desc}'

    # --- Stars: handle both stargazerCount (repo view) and stargazersCount (search) ---
    stars = it.get('stargazerCount')
    if stars is None:
        stars = it.get('stargazersCount')

    summary = desc[:240] or name

    # --- License: extract spdxId from licenseInfo, handle null/None ---
    license_info = it.get('licenseInfo')
    if isinstance(license_info, dict):
        license_id = license_info.get('spdxId')
        # GitHub returns "NOASSERTION" when license can't be determined
        license_val = None if license_id in ('NOASSERTION', None) else license_id
    else:
        license_val = None

    # --- Forks: handle both forkCount (repo view) and forks ---
    forks = it.get('forkCount')
    if forks is None:
        forks = it.get('forks')

    # --- Languages: prefer primaryLanguage.name, filter null ---
    primary_lang = it.get('primaryLanguage')
    if isinstance(primary_lang, dict):
        lang_name = primary_lang.get('name')
    else:
        lang_name = it.get('language')  # search API uses 'language' string field
    languages = [lang_name] if lang_name else []

    # --- Topics: extract from repositoryTopics (list of {name: ...}) ---
    topics_raw = it.get('repositoryTopics') or []
    if isinstance(topics_raw, list):
        topics = [t.get('name') if isinstance(t, dict) else t for t in topics_raw]
        topics = [t for t in topics if t]  # filter None/empty
    else:
        topics = []

    # --- readme_preview: first 500 chars of readme ---
    readme = it.get('readme') or ''
    readme_preview = readme[:500] if readme else ''

    return {
        'id': slug('github-' + name),
        'name': name,
        'url': url,
        'repo': fn,
        'source_type': 'github',
        'resource_type': resource_types_for(text),
        'target_tools': target_tools_for(text, tools),
        'summary': summary,
        'i18n': i18n_fields(name, summary),
        'status': 'archived' if it.get('isArchived') else 'unknown',
        'license': license_val,
        'stars': stars,
        'forks': forks,
        'last_updated': it.get('updatedAt') or it.get('pushedAt'),
        'first_seen': None,
        'last_seen': None,
        'maturity': 'unknown',
        'languages': languages,
        'topics': topics,
        'readme_preview': readme_preview,
        'tags': [],
        'review_state': 'auto-indexed',
        'quantifiable_score': 0,  # will be calculated by score.py
        'quality_score': 0,  # will be filled by weekly LLM analysis
        'total_score': 0,
        'score_detail': {},
        'tracking_priority': 'pending',
        'last_analyzed': None,
        'benchmark_ref': None,
    }
```

- [ ] **步骤 3：修改 normalize.py 的 from_github() 优先使用 repo-details 数据**

当前 `from_github()` 函数遍历所有 JSON 文件，搜索结果和 repo-details 都会被处理，后处理的覆盖先处理的。需要确保 repo-details.json 的数据（更完整）优先于搜索结果（字段不全）。

将 `from_github()` 函数（第 84~99 行）替换为：

```python
def from_github():
    tools = load_jsonish('data/seed-tools.yaml')
    by_url = {}  # dedup by URL, repo-details wins over search results

    for d in sorted((ROOT / 'data/raw/github').glob('*')):
        for p in sorted(d.glob('*.json')):
            if p.name.endswith('-error.json'):
                continue
            data = json.loads(p.read_text(encoding='utf-8'))
            items = data if isinstance(data, list) else data.get('results', [])
            if p.name == 'repo-details.json':
                items = data
            for it in items:
                rec = github_record(it, tools)
                if not rec:
                    continue
                url = rec.get('url')
                existing = by_url.get(url)
                if existing:
                    # Merge: prefer repo-details fields (non-null) over search results
                    for k, v in rec.items():
                        if v is not None and (existing.get(k) is None or existing.get(k) == []):
                            existing[k] = v
                    # Always update resource_type/target_tools from richer data
                    if len(rec.get('resource_type', [])) > len(existing.get('resource_type', [])):
                        existing['resource_type'] = rec['resource_type']
                else:
                    by_url[url] = rec
    return list(by_url.values())
```

- [ ] **步骤 4：验证字段提取逻辑（单元测试）**

```bash
cd "/root/workspace/search in coding"
python3 -c "
import sys, json
sys.path.insert(0, 'scripts')
from normalize import github_record

# Simulate repo-view data (richer)
repo_view_item = {
    'nameWithOwner': 'test/repo',
    'description': 'A test skill for Claude Code',
    'url': 'https://github.com/test/repo',
    'stargazerCount': 1234,
    'forkCount': 56,
    'licenseInfo': {'spdxId': 'MIT'},
    'repositoryTopics': [{'name': 'claude'}, {'name': 'skill'}],
    'primaryLanguage': {'name': 'Python'},
    'updatedAt': '2025-07-01T00:00:00Z',
    'isArchived': False,
    'readme': '# Test Repo\n\nThis is a test readme.' + 'x' * 600,
}
rec = github_record(repo_view_item, [])
assert rec['stars'] == 1234, f'stars={rec[\"stars\"]}'
assert rec['forks'] == 56, f'forks={rec[\"forks\"]}'
assert rec['license'] == 'MIT', f'license={rec[\"license\"]}'
assert rec['languages'] == ['Python'], f'languages={rec[\"languages\"]}'
assert rec['topics'] == ['claude', 'skill'], f'topics={rec[\"topics\"]}'
assert len(rec['readme_preview']) == 500, f'readme_preview len={len(rec[\"readme_preview\"])}'
assert 'NOASSERTION' not in str(rec['license'])
print('PASS: repo-view field extraction')

# Simulate search data (sparse)
search_item = {
    'fullName': 'test/search-repo',
    'description': 'A search result',
    'url': 'https://github.com/test/search-repo',
    'stargazersCount': 100,
    'language': 'JavaScript',
    'updatedAt': '2025-06-01T00:00:00Z',
}
rec2 = github_record(search_item, [])
assert rec2['stars'] == 100, f'stars={rec2[\"stars\"]}'
assert rec2['forks'] is None, f'forks={rec2[\"forks\"]}'
assert rec2['languages'] == ['JavaScript'], f'languages={rec2[\"languages\"]}'
assert rec2['topics'] == [], f'topics={rec2[\"topics\"]}'
assert rec2['readme_preview'] == '', f'readme_preview={rec2[\"readme_preview\"]}'
print('PASS: search-result field extraction')

# Test null license
null_license_item = {
    'nameWithOwner': 'test/null-license',
    'url': 'https://github.com/test/null-license',
    'stargazerCount': 10,
    'licenseInfo': None,
    'forkCount': 1,
}
rec3 = github_record(null_license_item, [])
assert rec3['license'] is None
print('PASS: null license handling')

# Test NOASSERTION license
noassert_item = {
    'nameWithOwner': 'test/noassert',
    'url': 'https://github.com/test/noassert',
    'stargazerCount': 10,
    'licenseInfo': {'spdxId': 'NOASSERTION'},
    'forkCount': 1,
}
rec4 = github_record(noassert_item, [])
assert rec4['license'] is None, f'license={rec4[\"license\"]}'
print('PASS: NOASSERTION license handling')
"
```

预期：全部 5 个断言通过，输出 5 行 PASS。

- [ ] **步骤 5：重新运行 normalize 填充新字段**

```bash
cd "/root/workspace/search in coding"
python3 scripts/normalize.py
```

预期：输出 `{"normalized_new": N, "total": M}` JSON，M 大于之前（包含任务 2 新增的项目）。

- [ ] **步骤 6：验证字段填充率提升**

```bash
cd "/root/workspace/search in coding"
python3 -c "
import yaml
data = yaml.safe_load(open('data/projects.yaml'))
total = len(data)
forks_filled = sum(1 for p in data if p.get('forks') is not None)
license_filled = sum(1 for p in data if p.get('license') is not None)
lang_filled = sum(1 for p in data if p.get('languages') and p['languages'][0] is not None)
stars_filled = sum(1 for p in data if p.get('stars') is not None)
topics_filled = sum(1 for p in data if p.get('topics'))
readme_filled = sum(1 for p in data if p.get('readme_preview'))
print(f'Total: {total}')
print(f'Forks filled:     {forks_filled}/{total} ({forks_filled*100//total}%)')
print(f'License filled:   {license_filled}/{total} ({license_filled*100//total}%)')
print(f'Languages filled: {lang_filled}/{total} ({lang_filled*100//total}%)')
print(f'Stars filled:     {stars_filled}/{total} ({stars_filled*100//total}%)')
print(f'Topics filled:    {topics_filled}/{total} ({topics_filled*100//total}%)')
print(f'Readme filled:    {readme_filled}/{total} ({readme_filled*100//total}%)')
"
```

预期：forks/license/topics/readme_preview 填充率应显著提升（取决于 raw 数据是否包含 repo-details.json；如果只有搜索结果数据，forks/license/readme 仍为 null，需要先运行 `python3 scripts/collect_github.py` 重新采集）。

**注意：** 如果填充率没有提升，说明 raw/github 目录下的数据是旧的搜索结果格式（不含 forkCount/licenseInfo/readme）。此时需要重新采集：

```bash
cd "/root/workspace/search in coding"
python3 scripts/collect_github.py --limit 20
python3 scripts/normalize.py
```

然后重新运行步骤 6 验证。

- [ ] **步骤 7：Commit**

```bash
cd "/root/workspace/search in coding"
git add scripts/collect_github.py scripts/normalize.py data/projects.yaml
git commit -m "fix: normalize.py field mapping (forks/license/languages/topics) + add readme_preview, collect_github.py adds readme to gh repo view"
```

---

## 任务 4：修正 resource_type 误标

**文件：**
- 修改：`scripts/normalize.py`（resource_types_for 函数）
- 修改：`data/curated-projects.yaml`（重新生成）

**问题说明：** 当前 `resource_types_for()` 的匹配逻辑有两个缺陷：

1. **skill 被误标为 tutorial**：如 `caveman`（summary 含 "Claude Code skill"）被标为 `tutorial` 而非 `skills`。根因是 migrate_data.py 的 `migrate_category_to_resource_type()` 对没有匹配旧 category 的项目默认返回 `['tutorial']`，且 `resource_types_for()` 的 'tutorial' 规则过于宽泛（'guide' 等词会误匹配）。

2. **匹配优先级问题**：当文本同时含 'skill' 和 'guide' 时，可能同时匹配 'skills' 和 'tutorial'，但应优先标为 'skills'。

**典型误标案例（curated Top 10）：**

| 项目 | 当前 resource_type | 应为 | summary 关键词 |
|------|-------------------|------|---------------|
| JuliusBrussee/caveman | tutorial | skills | "Claude Code skill" |
| blader/humanizer | tutorial | skills | "Claude Code skill" |
| virgiliojr94/book-to-skill | tutorial | skills | "Claude Code skill" |
| SimoneAvogadro/android-reverse-engineering-skill | tutorial | skills | "Claude Code skill" |
| zarazhangrui/codebase-to-course | tutorial | skills | "Claude Code skill" |
| gemini-cli-extensions/conductor | tutorial | skills | "Gemini CLI extension" |

- [ ] **步骤 1：改进 resource_types_for() 函数的匹配逻辑**

将 `scripts/normalize.py` 中的 `RESOURCE_TYPE_RULES` 和 `resource_types_for()` 函数替换为以下版本。关键改进：

1. **新增 'extension' 规则**：匹配 "extension"、"plugin" 等
2. **调整 'tutorial' 规则**：移除过于宽泛的 'guide'，只保留明确的教学内容词
3. **添加优先级逻辑**：skills/extension/mcp-server/rules 优先于 tutorial，避免 skill 项目误标
4. **增加 'skill' 的匹配精度**：确保 "Claude Code skill"、"agent skill" 等短语优先匹配

替换代码：

```python
# Resource type rules: ordered by priority (earlier = higher priority)
RESOURCE_TYPE_RULES = {
    'mcp-server': ['mcp server', 'model context protocol', 'mcp server', 'mcp tool', 'mcp integration'],
    'skills': ['claude code skill', 'claude skill', 'agent skill', 'coding skill',
               'skill pack', 'skill collection', 'skills &', 'skills and',
               'prompt pack', 'slash command', 'custom command',
               'skill that', 'skills for', 'skill to', 'skill set'],
    'extension': ['extension', 'plugin', 'addon', 'add-on'],
    'rules': ['agents.md', 'claude.md', 'cursor rules', '.cursorrules',
              'ruleset', 'instruction file', 'rules file', 'rules for',
              'cursor rule', 'rules .mdc', 'rules mdc'],
    'agent-framework': ['agent framework', 'multi-agent', 'subagent',
                        'agent orchestration', 'agentic framework', 'agent system',
                        'agent desktop', 'autonomous agent'],
    'cli-tool': ['cli ', 'cli tool', 'command line', 'terminal',
                 'codebase index', 'repo map', 'repository map',
                 'semantic search', 'codebase indexing', 'code search',
                 'cli extension'],
    'tutorial': ['tutorial', 'best practice', 'case study',
                 'benchmark', 'evaluation', 'eval harness', 'leaderboard',
                 'awesome list', 'curated list'],
}

ZH_RE = re.compile(r'[\u4e00-\u9fff]')


def i18n_fields(name, summary):
    name = name or ''
    summary = summary or ''
    return {'zh': {'name': name, 'summary': summary}, 'en': {'name': name, 'summary': summary}}

def has_any(text, phrases):
    low = text.lower()
    return any(p.lower() in low for p in phrases)

def target_tools_for(text, tools):
    low = text.lower()
    ids = []
    for t in tools:
        aliases = t.get('aliases', []) + [t.get('name', ''), t.get('id', '')]
        if any(a and a.lower() in low for a in aliases):
            ids.append(t['id'])
    return ids or ['general-ai-coding']

def resource_types_for(text):
    """Determine resource_type tags from project text.

    Rules are checked in priority order: concrete types (mcp-server, skills,
    extension, rules, agent-framework, cli-tool) are checked first.
    'tutorial' is only assigned if no concrete type matches AND tutorial
    keywords are present. If nothing matches at all, default to ['tutorial'].
    """
    low = text.lower()
    types = []

    # Phase 1: check concrete resource types (priority order)
    for rt in ['mcp-server', 'skills', 'extension', 'rules', 'agent-framework', 'cli-tool']:
        phrases = RESOURCE_TYPE_RULES.get(rt, [])
        if has_any(low, phrases):
            types.append(rt)

    # Phase 2: check tutorial (lower priority — only as additional tag)
    if has_any(low, RESOURCE_TYPE_RULES.get('tutorial', [])):
        types.append('tutorial')

    return types or ['tutorial']
```

- [ ] **步骤 2：验证 resource_types_for() 匹配逻辑**

```bash
cd "/root/workspace/search in coding"
python3 -c "
import sys
sys.path.insert(0, 'scripts')
from normalize import resource_types_for

# Should be 'skills' not 'tutorial'
assert 'skills' in resource_types_for('JuliusBrussee/caveman Claude Code skill that cuts 65% of tokens'), 'caveman failed'
assert 'skills' in resource_types_for('blader/humanizer Claude Code skill that removes signs of AI-generated writing'), 'humanizer failed'
assert 'skills' in resource_types_for('Turn any technical book PDF into a Claude Code skill'), 'book-to-skill failed'
assert 'skills' in resource_types_for('Claude Code skill to support Android reverse engineering'), 'android-skill failed'
assert 'extension' in resource_types_for('Conductor is a Gemini CLI extension that allows you to specify'), 'conductor failed'

# Should still detect tutorial when appropriate
assert 'tutorial' in resource_types_for('Best practices for AI coding agents tutorial'), 'tutorial failed'

# Should detect mcp-server
assert 'mcp-server' in resource_types_for('Claude Code as one-shot MCP server'), 'mcp failed'

# Should detect rules
assert 'rules' in resource_types_for('Curated list of awesome Cursor Rules .mdc files'), 'rules failed'

# Should detect agent-framework
assert 'agent-framework' in resource_types_for('Multi-agent orchestration framework'), 'framework failed'

print('PASS: all resource_types_for assertions passed')
"
```

预期：全部断言通过，输出 `PASS: all resource_types_for assertions passed`。

- [ ] **步骤 3：重新生成 curated-projects.yaml**

重新运行归一化和评分流程，使修正后的 resource_types_for() 生效到 curated-projects.yaml：

```bash
cd "/root/workspace/search in coding"
# 1. 重新归一化（应用新的 resource_types_for 逻辑）
python3 scripts/normalize.py

# 2. 重新评分
python3 scripts/score.py

# 3. 重新生成 curated-projects.yaml（如果 score.py 或 finalize_data.py 自动生成）
python3 scripts/finalize_data.py
```

**注意：** 如果 `finalize_data.py` 不自动生成 `curated-projects.yaml`，检查 `score.py` 是否生成：

```bash
cd "/root/workspace/search in coding"
# 查看 score.py 或 finalize_data.py 是否写 curated-projects.yaml
grep -l 'curated-projects' scripts/*.py
```

如果需要手动生成 curated Top 40：

```bash
cd "/root/workspace/search in coding"
python3 -c "
import yaml
data = yaml.safe_load(open('data/projects.yaml'))
# Sort by total_score desc, take top 40
sorted_data = sorted(data, key=lambda x: x.get('total_score', 0) or 0, reverse=True)
top40 = sorted_data[:40]
with open('data/curated-projects.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(top40, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
print(f'Written {len(top40)} curated projects')
"
```

- [ ] **步骤 4：验证 curated Top 40 的 resource_type 修正**

```bash
cd "/root/workspace/search in coding"
python3 -c "
import yaml
data = yaml.safe_load(open('data/curated-projects.yaml'))
print(f'Total curated: {len(data)}')
print()
misclassified = []
for p in data:
    rt = p.get('resource_type') or []
    summary = (p.get('summary') or '').lower()
    repo = p.get('repo', '')
    # Check: if summary contains 'skill' but resource_type doesn't include 'skills'
    if 'skill' in summary and 'skills' not in rt:
        misclassified.append((repo, rt, summary[:60]))
    # Check: if summary contains 'extension' but resource_type doesn't include 'extension'
    if 'extension' in summary and 'extension' not in rt and 'skills' not in rt:
        misclassified.append((repo, rt, summary[:60]))

if misclassified:
    print('STILL MISCLASSIFIED:')
    for repo, rt, s in misclassified:
        print(f'  {repo:<50} {rt}  | {s}')
else:
    print('OK: no skill/extension projects misclassified as tutorial')

# Show resource_type distribution
from collections import Counter
rt_counter = Counter()
for p in data:
    for r in (p.get('resource_type') or []):
        rt_counter[r] += 1
print()
print('Resource type distribution:')
for rt, count in rt_counter.most_common():
    print(f'  {rt:<20} {count}')
"
```

预期：
- "OK: no skill/extension projects misclassified as tutorial"
- resource_type 分布中 `skills` 数量增加，`tutorial` 数量减少

- [ ] **步骤 5：Commit**

```bash
cd "/root/workspace/search in coding"
git add scripts/normalize.py data/curated-projects.yaml data/projects.yaml
git commit -m "fix: improve resource_types_for() matching logic — skills no longer misclassified as tutorial, add extension type"
```

---

## 验收标准

- [ ] `data/seed-tools.yaml` 中 goose/cursor/opencode/qoder 的 repo 路径全部正确，`gh repo view` 可访问
- [ ] `scripts/add_missing_projects.py` 脚本存在且可运行，6 个知名项目（continue/aider/cline/roo/goose/cursor）已加入 projects.yaml
- [ ] `scripts/collect_github.py` 的 `repo_view()` 函数 `--json` fields 包含 `readme`
- [ ] `scripts/normalize.py` 的 `github_record()` 正确映射以下字段：
  - [ ] stars（兼容 stargazerCount / stargazersCount）
  - [ ] forks（兼容 forkCount / forks）
  - [ ] license（licenseInfo.spdxId，NOASSERTION → null）
  - [ ] languages（primaryLanguage.name，过滤 null）
  - [ ] topics（新增，从 repositoryTopics 提取）
  - [ ] readme_preview（新增，readme 前 500 字符）
- [ ] `scripts/normalize.py` 的 `from_github()` 优先使用 repo-details 数据（merge 策略）
- [ ] `scripts/normalize.py` 的 `resource_types_for()` 改进后：
  - [ ] 含 "Claude Code skill" 的项目标为 `skills` 而非 `tutorial`
  - [ ] 含 "extension" 的项目标为 `extension`
  - [ ] `tutorial` 仅在无具体类型匹配且含教学关键词时才分配
- [ ] `data/curated-projects.yaml` 中 Top 40 项目无 skill 被误标为 tutorial
- [ ] 所有 4 个任务都已 commit

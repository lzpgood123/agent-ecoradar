# 新对话 Agent 启动提示词：自运行加固（10 个修复任务）

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是"Search in Coding"项目的运维加固 Agent。项目已完成所有功能开发，进入自运行阶段。grilling 发现 10 个运维可靠性问题需要修复。

完整设计规格见：`docs/superpowers/specs/2026-07-15-self-running-hardening-design.md`

## 决策背景

- **daily cron 不 deploy**：这是刻意设计，不是 bug。每天采集的新数据等到 LLM cron（Tue-Sat 或周一）分析后才 deploy 上线。保持原始设计不变。
- **LLM cron 负责 deploy**：daily LLM（Tue-Sat）和 weekly LLM（周一）都在分析后 deploy。
- **采集和 LLM 错开 2 小时**：03:00 采集完成后，05:00 LLM 分析，避免 `projects.yaml` 写冲突。

## 项目环境信息

- 工作目录：`/root/workspace/search in coding`
- Python：3.12.3（用 python3，需要 `source .venv/bin/activate`）
- Hermes cron 4 个 job：
  - `2a0c271a031f` daily 采集 03:00 `search-in-coding-daily.sh`
  - `f110f12e4d96` daily LLM 03:30 Tue-Sat `search-in-coding-llm-daily.sh`
  - `2aa9da554787` weekly LLM 03:30 Mon `search-in-coding-weekly.sh`
  - `7388b6c788e8` weekly release 09:00 Mon（无脚本）
- 站点：https://coding.lzpgood.online/（Nginx，`/var/www/coding.lzpgood.online/`）
- GitHub Actions 3 个 workflow：update-data、publish-site、release
- SenseNova 13 个 key 在 `~/.hermes/auth.json`（`credential_pool.custom:sensenova`）
- GitHub CLI `gh` 已认证
- 数据：5165 项目（4571 track / 69 reject / 525 pending）

## 关键约束

1. **daily cron 不加 `--deploy`**：保持原始设计，LLM cron 负责 deploy
2. **不改评分公式**：`score.py` 的 100 分制保持不变
3. **不改前端框架**：vanilla JS + 分片 JSON 保持不变
4. **不改 LLM prompt**：`llm_prompts.py` 保持不变
5. **TDD for 新脚本**：`archive_low_score.py`、`refresh_track_projects.py`、`cleanup_disk.py` 需要先写测试
6. **频繁 commit**：每个任务完成后 commit 一次

## 修复后的自运行时间线

```
03:00  daily  采集 + 评分 + 构建（不 deploy）（每日）
05:00  daily  LLM 增量 200 条 + deploy（Tue-Sat）
05:00  weekly LLM 全量重评 + 报告 + deploy（周一）
09:00  weekly release 禁用（GitHub Actions 自动处理）
push   GitHub Actions Publish Site（实时）
```

---

## 任务 1：daily cron 脚本加 source venv

**问题**：`~/.hermes/scripts/search-in-coding-daily.sh` 没有 `source .venv/bin/activate`，依赖系统 Python 恰好有 PyYAML，不可靠。

**步骤**：

```bash
# 1. 查看当前脚本
cat ~/.hermes/scripts/search-in-coding-daily.sh
```

当前内容（无 venv）：
```bash
#!/bin/bash
# Wrapper: Run Search in Coding daily pipeline via update_tracker.py
cd /root/workspace/search\ in\ coding || { echo "ERROR: workdir not found"; exit 1; }
/usr/bin/python3 scripts/update_tracker.py 2>&1
exit $?
```

修改为：
```bash
cat > ~/.hermes/scripts/search-in-coding-daily.sh << 'SCRIPT'
#!/bin/bash
# Wrapper: Run Search in Coding daily pipeline via update_tracker.py
cd /root/workspace/search\ in\ coding || { echo "ERROR: workdir not found"; exit 1; }
source .venv/bin/activate
python3 scripts/update_tracker.py 2>&1
exit $?
SCRIPT
chmod +x ~/.hermes/scripts/search-in-coding-daily.sh
```

**验证**：
```bash
# 确认脚本内容
cat ~/.hermes/scripts/search-in-coding-daily.sh
# 确认有 source .venv/bin/activate
grep "source .venv" ~/.hermes/scripts/search-in-coding-daily.sh
# 确认没有 --deploy
grep -c "deploy" ~/.hermes/scripts/search-in-coding-daily.sh  # 应为 0
```

---

## 任务 2：daily LLM cron 从 03:30 改到 05:00

**问题**：daily 采集 03:00 + daily LLM 03:30，只有 30 分钟间隔，5165 条数据采集可能超时导致写冲突。

**步骤**：

```bash
# 1. 查看当前 cron
hermes cron list

# 2. 找到 daily LLM incremental 的 job_id
# 预期 job_id: f110f12e4d96
# 当前 schedule: 30 3 * * 2-6
# 目标 schedule: 0 5 * * 2-6

# 3. 更新 schedule（如果 hermes cron 支持 update）
hermes cron update --job-id f110f12e4d96 --schedule "0 5 * * 2-6"

# 如果不支持 update，删除重建：
# hermes cron remove --job-id f110f12e4d96
# hermes cron create \
#   --name "Search in Coding daily LLM incremental" \
#   --schedule "0 5 * * 2-6" \
#   --no-agent \
#   --script "search-in-coding-llm-daily.sh" \
#   --workdir "/root/workspace/search in coding"
```

**验证**：
```bash
hermes cron list | grep -A5 "daily LLM"
# 确认 schedule 为 0 5 * * 2-6
# 确认 Next run 为 05:00
```

---

## 任务 3：weekly LLM cron 从 03:30 改到 05:00

**问题**：周一 03:00 daily 采集和 03:30 weekly LLM 同样存在时间冲突。

**步骤**：

```bash
# 1. 找到 weekly LLM analysis 的 job_id
# 预期 job_id: 2aa9da554787
# 当前 schedule: 30 3 * * 1
# 目标 schedule: 0 5 * * 1

# 2. 更新 schedule
hermes cron update --job-id 2aa9da554787 --schedule "0 5 * * 1"

# 如果不支持 update，删除重建：
# hermes cron remove --job-id 2aa9da554787
# hermes cron create \
#   --name "Search in Coding weekly LLM analysis" \
#   --schedule "0 5 * * 1" \
#   --no-agent \
#   --script "search-in-coding-weekly.sh" \
#   --workdir "/root/workspace/search in coding"
```

**验证**：
```bash
hermes cron list | grep -A5 "weekly LLM"
# 确认 schedule 为 0 5 * * 1
# 确认 Next run 为周一 05:00
```

---

## 任务 4：禁用 weekly release cron

**问题**：Hermes cron `7388b6c788e8`（weekly auto release，周一 09:00）与 GitHub Actions `release.yml` 功能重叠。`release.yml` 在 VERSION 变更时自动创建 Release。

**步骤**：

```bash
# 1. 查看 weekly release cron
hermes cron list | grep -A5 "weekly.*release"

# 2. Pause 或 remove
# 方案 A：pause（推荐，保留配置以备恢复）
hermes cron pause --job-id 7388b6c788e8

# 方案 B：remove（彻底删除）
# hermes cron remove --job-id 7388b6c788e8
```

**验证**：
```bash
hermes cron list | grep -A5 "release"
# 确认状态为 paused 或已删除
# 确认 GitHub Actions release.yml 仍在
cat .github/workflows/release.yml | head -5
```

---

## 任务 5：修复 GitHub Actions update-data.yml

**问题**：两个原因导致失败：
1. PyYAML 未安装（只 `pip install pytest`）
2. `--exa-limit` 参数不存在（`update_tracker.py` 不支持）

**当前 update-data.yml 关键部分**：
```yaml
      - name: Install test dependencies
        run: python3 -m pip install pytest
      - name: Update tracker data
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          python3 scripts/update_tracker.py \
            --github-limit "${{ inputs.github_limit || '20' }}" \
            --exa-limit "${{ inputs.exa_limit || '3' }}"
```

**修改步骤**：

修改 `.github/workflows/update-data.yml`：

1. Install step 加 `pyyaml`：
```yaml
      - name: Install test dependencies
        run: python3 -m pip install pytest pyyaml
```

2. Update tracker step 去掉 `--exa-limit`：
```yaml
      - name: Update tracker data
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          python3 scripts/update_tracker.py \
            --github-limit "${{ inputs.github_limit || '20' }}"
```

3. 同时去掉 workflow_dispatch inputs 中的 exa_limit 定义（可选，保留也无害但建议清理）：
```yaml
on:
  workflow_dispatch:
    inputs:
      github_limit:
        description: GitHub search results per query
        default: '20'
```

**验证**：
```bash
# 确认 pyyaml 在 install step
grep "pyyaml" .github/workflows/update-data.yml
# 确认没有 --exa-limit
grep -c "exa-limit" .github/workflows/update-data.yml  # 应为 0
```

**Commit**：
```bash
git add .github/workflows/update-data.yml
git commit -m "fix: update-data.yml - add pyyaml, remove invalid --exa-limit param"
```

---

## 任务 6：track 项目分批刷新 GitHub API

**问题**：daily 采集只搜索新项目，不刷新已有 track 项目（4571 个）的 stars/forks/last_updated。一次性刷新全部会触发 GitHub API rate limit（5000/h）。

**目标**：写新脚本 `scripts/refresh_track_projects.py`，每天刷新 1000 个 track 项目，约 5 天轮一遍全部。集成到 daily cron。

### 步骤 1：TDD - 先写测试

创建 `tests/test_refresh_track_projects.py`：

```python
"""Test track project refresh logic."""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class TestSelectProjectsToRefresh:
    def test_selects_track_projects_only(self):
        from refresh_track_projects import select_projects_to_refresh
        projects = [
            {'id': '1', 'tracking_priority': 'track', 'repo': 'a/b', 'last_seen': '2026-07-10'},
            {'id': '2', 'tracking_priority': 'reject', 'repo': 'c/d', 'last_seen': '2026-07-10'},
            {'id': '3', 'tracking_priority': 'pending', 'repo': 'e/f', 'last_seen': '2026-07-10'},
        ]
        selected = select_projects_to_refresh(projects, batch_size=10)
        ids = [p['id'] for p in selected]
        assert '1' in ids
        assert '2' not in ids
        assert '3' not in ids

    def test_skips_official_seed(self):
        from refresh_track_projects import select_projects_to_refresh
        projects = [
            {'id': '1', 'tracking_priority': 'track', 'source_type': 'official-seed', 'repo': 'a/b'},
            {'id': '2', 'tracking_priority': 'track', 'source_type': 'github', 'repo': 'c/d'},
        ]
        selected = select_projects_to_refresh(projects, batch_size=10)
        ids = [p['id'] for p in selected]
        assert '2' in ids
        assert '1' not in ids  # official-seed 跳过

    def test_skips_projects_without_repo(self):
        from refresh_track_projects import select_projects_to_refresh
        projects = [
            {'id': '1', 'tracking_priority': 'track', 'repo': 'a/b', 'last_seen': '2026-07-10'},
            {'id': '2', 'tracking_priority': 'track', 'repo': None, 'last_seen': '2026-07-10'},
            {'id': '3', 'tracking_priority': 'track', 'last_seen': '2026-07-10'},  # no repo key
        ]
        selected = select_projects_to_refresh(projects, batch_size=10)
        ids = [p['id'] for p in selected]
        assert '1' in ids
        assert '2' not in ids
        assert '3' not in ids

    def test_sorts_by_last_seen_oldest_first(self):
        from refresh_track_projects import select_projects_to_refresh
        projects = [
            {'id': 'new', 'tracking_priority': 'track', 'repo': 'a/b', 'last_seen': '2026-07-15'},
            {'id': 'old', 'tracking_priority': 'track', 'repo': 'c/d', 'last_seen': '2026-07-01'},
            {'id': 'mid', 'tracking_priority': 'track', 'repo': 'e/f', 'last_seen': '2026-07-10'},
        ]
        selected = select_projects_to_refresh(projects, batch_size=10)
        ids = [p['id'] for p in selected]
        assert ids == ['old', 'mid', 'new']  # oldest first

    def test_respects_batch_size(self):
        from refresh_track_projects import select_projects_to_refresh
        projects = [
            {'id': str(i), 'tracking_priority': 'track', 'repo': f'a/b{i}', 'last_seen': '2026-07-01'}
            for i in range(50)
        ]
        selected = select_projects_to_refresh(projects, batch_size=10)
        assert len(selected) == 10


class TestMergeRefreshedData:
    def test_updates_stars_and_forks(self):
        from refresh_track_projects import merge_refreshed_data
        existing = {
            'id': '1', 'name': 'test', 'repo': 'a/b',
            'stars': 100, 'forks': 10,
            'quality_score': 30, 'tracking_priority': 'track',
            'llm_summary': 'important',
        }
        refreshed = {
            'stargazerCount': 150, 'forkCount': 20,
            'updatedAt': '2026-07-15T00:00:00Z',
        }
        merged = merge_refreshed_data(existing, refreshed)
        assert merged['stars'] == 150
        assert merged['forks'] == 20
        assert merged['last_updated'] == '2026-07-15T00:00:00Z'
        # LLM 字段必须保留
        assert merged['quality_score'] == 30
        assert merged['tracking_priority'] == 'track'
        assert merged['llm_summary'] == 'important'

    def test_preserves_summary_if_empty_in_refresh(self):
        from refresh_track_projects import merge_refreshed_data
        existing = {'id': '1', 'summary': 'old summary', 'repo': 'a/b'}
        refreshed = {'description': '', 'stargazerCount': 100}
        merged = merge_refreshed_data(existing, refreshed)
        assert merged['summary'] == 'old summary'
```

运行测试确认 RED：
```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate
python3 -m pytest tests/test_refresh_track_projects.py -v
# 预期：全部 FAIL（模块不存在）
```

### 步骤 2：实现脚本

创建 `scripts/refresh_track_projects.py`：

```python
#!/usr/bin/env python3
"""Refresh GitHub metadata for tracked projects in batches.

Each run refreshes a batch of track-priority projects by calling
`gh repo view` to get latest stars/forks/topics/last_updated.
Designed to run daily as part of the collect pipeline.

Usage:
    python3 scripts/refresh_track_projects.py                # default batch 1000
    python3 scripts/refresh_track_projects.py --batch-size 500
    python3 scripts/refresh_track_projects.py --dry-run      # show what would be refreshed
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_jsonish, save_jsonish, today


def select_projects_to_refresh(projects, batch_size=1000):
    """Select track-priority projects to refresh, sorted by oldest last_seen first.

    Skips:
    - official-seed projects (managed separately)
    - non-track projects
    - projects without a repo field
    """
    candidates = []
    for p in projects:
        if p.get('tracking_priority') != 'track':
            continue
        if p.get('source_type') == 'official-seed':
            continue
        if not p.get('repo'):
            continue
        candidates.append(p)

    # Sort by last_seen ascending (oldest first); None sorts first
    candidates.sort(key=lambda p: p.get('last_seen') or '0000-01-01')
    return candidates[:batch_size]


def fetch_repo_data(full_name, timeout=30):
    """Fetch latest repo metadata via gh repo view."""
    fields = 'nameWithOwner,description,url,stargazerCount,forkCount,licenseInfo,repositoryTopics,primaryLanguage,pushedAt,createdAt,updatedAt,isArchived,latestRelease'
    cmd = f'gh repo view {full_name} --json {fields}'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout or '{}')
    except json.JSONDecodeError:
        return None


def merge_refreshed_data(existing, refreshed):
    """Merge refreshed GitHub data into existing project record.

    Preserves LLM fields: quality_score, quality_detail, tracking_priority,
    last_analyzed, benchmark_ref, llm_summary.
    """
    out = dict(existing)  # shallow copy

    if not refreshed:
        return out

    # Refresh quantifiable fields
    out['stars'] = refreshed.get('stargazerCount', existing.get('stars'))
    out['forks'] = refreshed.get('forkCount', existing.get('forks'))
    out['last_updated'] = refreshed.get('updatedAt') or refreshed.get('pushedAt') or existing.get('last_updated')

    if refreshed.get('isArchived'):
        out['status'] = 'archived'

    # Refresh topics
    topics_raw = refreshed.get('repositoryTopics') or []
    if isinstance(topics_raw, list):
        topics = [t.get('name') if isinstance(t, dict) else t for t in topics_raw]
        out['topics'] = [t for t in topics if t]

    # Refresh license
    license_info = refreshed.get('licenseInfo')
    if isinstance(license_info, dict):
        license_id = license_info.get('spdxId') or license_info.get('key')
        if license_id and license_id not in ('NOASSERTION', None, '', 'none'):
            out['license'] = license_id

    # Refresh languages
    primary_lang = refreshed.get('primaryLanguage')
    if isinstance(primary_lang, dict) and primary_lang.get('name'):
        out['languages'] = [primary_lang['name']]

    # Summary: only fill if existing is empty
    if not (out.get('summary') or '').strip():
        desc = refreshed.get('description') or ''
        if desc:
            out['summary'] = desc[:240]

    # Update last_seen
    out['last_seen'] = today()

    return out


def main():
    ap = argparse.ArgumentParser(description='Refresh track projects GitHub metadata in batches')
    ap.add_argument('--batch-size', type=int, default=1000, help='Number of projects to refresh per run')
    ap.add_argument('--dry-run', action='store_true', help='Show what would be refreshed without making changes')
    args = ap.parse_args()

    projects = load_jsonish('data/projects.yaml')
    to_refresh = select_projects_to_refresh(projects, batch_size=args.batch_size)

    print(f'Track projects to refresh: {len(to_refresh)} (batch_size={args.batch_size})')

    if args.dry_run:
        for p in to_refresh[:10]:
            print(f'  {p.get("repo")} (last_seen={p.get("last_seen")})')
        if len(to_refresh) > 10:
            print(f'  ... and {len(to_refresh) - 10} more')
        return

    if not to_refresh:
        print('No projects to refresh')
        return

    # Build lookup by id
    by_id = {p.get('id'): p for p in projects}

    success = 0
    failed = 0
    for p in to_refresh:
        repo = p.get('repo')
        pid = p.get('id')
        try:
            refreshed = fetch_repo_data(repo)
            if refreshed:
                by_id[pid] = merge_refreshed_data(p, refreshed)
                success += 1
            else:
                failed += 1
                print(f'  FAILED: {repo}')
        except (subprocess.TimeoutExpired, Exception) as e:
            failed += 1
            print(f'  ERROR: {repo}: {e}')

    # Save updated projects
    save_jsonish('data/projects.yaml', list(by_id.values()))

    print(json.dumps({
        'refreshed': success,
        'failed': failed,
        'total_track': sum(1 for p in projects if p.get('tracking_priority') == 'track'),
        'batch_size': args.batch_size,
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
```

运行测试确认 GREEN：
```bash
python3 -m pytest tests/test_refresh_track_projects.py -v
# 预期：全部 PASS
```

### 步骤 3：集成到 daily cron 脚本

修改 `~/.hermes/scripts/search-in-coding-daily.sh`，在 `update_tracker.py` 之后加 refresh：

```bash
cat > ~/.hermes/scripts/search-in-coding-daily.sh << 'SCRIPT'
#!/bin/bash
# Wrapper: Run Search in Coding daily pipeline via update_tracker.py
cd /root/workspace/search\ in\ coding || { echo "ERROR: workdir not found"; exit 1; }
source .venv/bin/activate

# Step 1: Collect + normalize + score + build (no deploy)
python3 scripts/update_tracker.py 2>&1

# Step 2: Refresh track projects metadata (batch 1000/day, ~5 day cycle)
echo "=== Refreshing track projects ==="
python3 scripts/refresh_track_projects.py --batch-size 1000 2>&1

exit $?
SCRIPT
chmod +x ~/.hermes/scripts/search-in-coding-daily.sh
```

### 步骤 4：验证 + Commit

```bash
# 验证 dry-run
cd "/root/workspace/search in coding"
source .venv/bin/activate
python3 scripts/refresh_track_projects.py --dry-run --batch-size 5

# 验证 daily 脚本
cat ~/.hermes/scripts/search-in-coding-daily.sh

# Commit
git add scripts/refresh_track_projects.py tests/test_refresh_track_projects.py
git commit -m "feat: add refresh_track_projects.py - batch refresh track project metadata"
```

---

## 任务 7：写归档脚本 scripts/archive_low_score.py

**问题**：69 条 reject + 部分 score < 20 的低分项目长期占用 `projects.yaml`（12MB），影响 build 性能。

**目标**：将 `tracking_priority == 'reject'` 或 `total_score < 20` 且 `source_type != 'official-seed'` 的项目移到 `data/archive-projects.yaml`。

### 步骤 1：TDD - 先写测试

创建 `tests/test_archive_low_score.py`：

```python
"""Test archive_low_score.py logic."""
import pytest
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class TestSelectProjectsToArchive:
    def test_archives_reject_projects(self):
        from archive_low_score import select_projects_to_archive
        projects = [
            {'id': '1', 'tracking_priority': 'reject', 'total_score': 50, 'source_type': 'github'},
            {'id': '2', 'tracking_priority': 'track', 'total_score': 50, 'source_type': 'github'},
        ]
        to_archive = select_projects_to_archive(projects, score_threshold=20)
        ids = [p['id'] for p in to_archive]
        assert '1' in ids
        assert '2' not in ids

    def test_archives_low_score_projects(self):
        from archive_low_score import select_projects_to_archive
        projects = [
            {'id': '1', 'tracking_priority': 'track', 'total_score': 15, 'source_type': 'github'},
            {'id': '2', 'tracking_priority': 'track', 'total_score': 25, 'source_type': 'github'},
        ]
        to_archive = select_projects_to_archive(projects, score_threshold=20)
        ids = [p['id'] for p in to_archive]
        assert '1' in ids
        assert '2' not in ids

    def test_does_not_archive_official_seed(self):
        from archive_low_score import select_projects_to_archive
        projects = [
            {'id': '1', 'tracking_priority': 'reject', 'total_score': 0, 'source_type': 'official-seed'},
            {'id': '2', 'tracking_priority': 'track', 'total_score': 5, 'source_type': 'official-seed'},
        ]
        to_archive = select_projects_to_archive(projects, score_threshold=20)
        assert len(to_archive) == 0  # official-seed 永不归档

    def test_archives_at_exact_threshold_excluded(self):
        from archive_low_score import select_projects_to_archive
        projects = [
            {'id': '1', 'tracking_priority': 'track', 'total_score': 20, 'source_type': 'github'},
            {'id': '2', 'tracking_priority': 'track', 'total_score': 19, 'source_type': 'github'},
        ]
        to_archive = select_projects_to_archive(projects, score_threshold=20)
        ids = [p['id'] for p in to_archive]
        assert '2' in ids
        assert '1' not in ids  # score == 20 不归档（< 20 才归档）

    def test_handles_missing_total_score(self):
        from archive_low_score import select_projects_to_archive
        projects = [
            {'id': '1', 'tracking_priority': 'pending', 'source_type': 'github'},  # no total_score
        ]
        to_archive = select_projects_to_archive(projects, score_threshold=20)
        ids = [p['id'] for p in to_archive]
        assert '1' in ids  # missing score treated as 0
```

### 步骤 2：实现脚本

创建 `scripts/archive_low_score.py`：

```python
#!/usr/bin/env python3
"""Archive low-score and rejected projects.

Moves projects with tracking_priority == 'reject' or total_score < threshold
to data/archive-projects.yaml, removing them from data/projects.yaml.
Official-seed projects are never archived.

Usage:
    python3 scripts/archive_low_score.py                # dry-run, threshold=20
    python3 scripts/archive_low_score.py --apply        # execute
    python3 scripts/archive_low_score.py --apply --threshold 15
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_jsonish, save_jsonish


def select_projects_to_archive(projects, score_threshold=20):
    """Select projects to archive based on reject status or low score.

    Criteria:
    - tracking_priority == 'reject', OR
    - total_score < score_threshold
    - source_type != 'official-seed' (never archive official seeds)
    """
    to_archive = []
    for p in projects:
        if p.get('source_type') == 'official-seed':
            continue
        if p.get('tracking_priority') == 'reject':
            to_archive.append(p)
            continue
        score = p.get('total_score')
        try:
            score = int(score or 0)
        except (TypeError, ValueError):
            score = 0
        if score < score_threshold:
            to_archive.append(p)
    return to_archive


def main():
    ap = argparse.ArgumentParser(description='Archive low-score and rejected projects')
    ap.add_argument('--threshold', type=int, default=20, help='Score threshold (projects below this are archived)')
    ap.add_argument('--apply', action='store_true', help='Execute the archive (default: dry-run)')
    args = ap.parse_args()

    projects = load_jsonish('data/projects.yaml')
    to_archive = select_projects_to_archive(projects, score_threshold=args.threshold)
    archive_ids = {p.get('id') for p in to_archive}
    remaining = [p for p in projects if p.get('id') not in archive_ids]

    # Load existing archive
    archive_path = ROOT / 'data' / 'archive-projects.yaml'
    existing_archive = load_jsonish(str(archive_path)) if archive_path.exists() else []

    print(json.dumps({
        'apply': args.apply,
        'threshold': args.threshold,
        'total_projects': len(projects),
        'to_archive': len(to_archive),
        'remaining': len(remaining),
        'existing_archive': len(existing_archive),
    }, ensure_ascii=False, indent=2))

    if not to_archive:
        print('No projects to archive')
        return

    if not args.apply:
        print('\nDry run - projects that would be archived:')
        for p in to_archive[:20]:
            print(f"  {p.get('id')} score={p.get('total_score', 0)} priority={p.get('tracking_priority')}")
        if len(to_archive) > 20:
            print(f'  ... and {len(to_archive) - 20} more')
        return

    # Merge into existing archive (avoid duplicates)
    existing_ids = {p.get('id') for p in existing_archive}
    new_archive = [p for p in to_archive if p.get('id') not in existing_ids]
    all_archive = existing_archive + new_archive

    save_jsonish('data/projects.yaml', remaining)
    save_jsonish('data/archive-projects.yaml', all_archive)

    print(f'\nArchived {len(new_archive)} new projects to data/archive-projects.yaml')
    print(f'projects.yaml: {len(projects)} -> {len(remaining)}')


if __name__ == '__main__':
    main()
```

### 步骤 3：验证 + Commit

```bash
# 运行测试
python3 -m pytest tests/test_archive_low_score.py -v

# Dry-run 看看会归档多少
python3 scripts/archive_low_score.py --threshold 20

# Commit
git add scripts/archive_low_score.py tests/test_archive_low_score.py
git commit -m "feat: add archive_low_score.py - archive reject/low-score projects"
```

---

## 任务 8：weekly_analysis.py 加 API key 监控

**问题**：13 个 API key 轮换使用，但没有记录每个 key 的调用次数和失败状态。当前 `KeyRotator` 只在内存中 `mark_failed`，下次运行就重置了。

**目标**：在 `llm_api.py` 的 `KeyRotator` 中加入 key 使用统计，`weekly_analysis.py` 运行结束后将统计写入 `data/llm-key-stats.json`。

### 步骤 1：修改 llm_api.py - KeyRotator 加统计

在 `KeyRotator.__init__` 中加统计字典，在 `next()` 和 `mark_failed()` 中更新统计，新增 `get_stats()` 方法。

修改 `scripts/llm_api.py`：

```python
class KeyRotator:
    """Round-robin key rotation with failure tracking and usage stats (thread-safe)."""

    def __init__(self, keys):
        self.keys = list(keys)
        self.index = 0
        self.failed = set()
        self._lock = threading.Lock()
        # Key monitoring stats
        self._stats = {}
        for k in self.keys:
            # Use last 8 chars as identifier for logging (don't expose full key)
            kid = k[-8:]
            self._stats[kid] = {
                'calls': 0,
                'success': 0,
                'failed': 0,
                'fail_reasons': [],
            }

    def next(self):
        with self._lock:
            available = [k for k in self.keys if k not in self.failed]
            if not available:
                self.failed.clear()
                available = self.keys
            if not available:
                raise RuntimeError('No API keys available')
            for _ in range(len(self.keys)):
                k = self.keys[self.index % len(self.keys)]
                self.index += 1
                if k not in self.failed:
                    kid = k[-8:]
                    self._stats[kid]['calls'] += 1
                    return k
            return available[0]

    def mark_success(self, key):
        with self._lock:
            kid = key[-8:]
            if kid in self._stats:
                self._stats[kid]['success'] += 1

    def mark_failed(self, key, reason=None):
        with self._lock:
            self.failed.add(key)
            kid = key[-8:]
            if kid in self._stats:
                self._stats[kid]['failed'] += 1
                if reason:
                    self._stats[kid]['fail_reasons'].append(str(reason))

    def get_stats(self):
        """Return a copy of per-key usage statistics."""
        with self._lock:
            import copy as _copy
            return _copy.deepcopy(self._stats)

    def reset(self):
        with self._lock:
            self.failed.clear()
```

### 步骤 2：修改 call_with_retry 记录成功/失败

修改 `call_with_retry` 函数，在成功时调 `mark_success`，失败时传 reason 给 `mark_failed`：

```python
def call_with_retry(prompt, system_prompt, rotator, max_retries=3):
    """Call LLM with key rotation and retry on failure."""
    last_error = None
    for attempt in range(max_retries):
        key = None
        try:
            key = rotator.next()
            result = call_llm(prompt, system_prompt, key=key)
            if result:
                rotator.mark_success(key)
                return result
            else:
                rotator.mark_failed(key, 'empty_response')
        except KeyError as e:
            if key is not None:
                rotator.mark_failed(key, f'auth_error: {e}')
            print(f'  Key failed, rotating... (attempt {attempt+1}/{max_retries})')
        except RateLimitError:
            if key is not None:
                rotator.mark_failed(key, 'rate_limit_429')
            time.sleep(5 * (attempt + 1))
            print(f'  Rate limited, waiting... (attempt {attempt+1}/{max_retries})')
        except Exception as e:
            if key is not None:
                rotator.mark_failed(key, f'exception: {e}')
            last_error = e
            print(f'  Error: {e} (attempt {attempt+1}/{max_retries})')
    print(f'  All retries exhausted: {last_error}')
    return None
```

### 步骤 3：修改 weekly_analysis.py - 保存 key 统计

在 `weekly_analysis.py` 的 `main()` 函数末尾加保存统计逻辑。

需要修改 `run_analysis()` 函数，让 `batch_analyze` 返回 rotator stats。修改 `batch_analyze` 在 `llm_api.py` 中返回 stats：

```python
def batch_analyze(items, prompt_fn, system_prompt, max_workers=3):
    """Analyze a batch of items concurrently. Returns (results_dict, key_stats)."""
    keys = load_api_keys()
    if not keys:
        print('ERROR: No API keys found')
        return {}, {}

    rotator = KeyRotator(keys)
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, item in enumerate(items):
            prompt = prompt_fn(item)
            future = executor.submit(call_with_retry, prompt, system_prompt, rotator)
            futures[future] = i

        for future in as_completed(futures):
            idx = futures[future]
            try:
                text = future.result()
                if text:
                    results[idx] = parse_json_response(text)
                else:
                    results[idx] = None
            except Exception as e:
                print(f'  Item {idx} failed: {e}')
                results[idx] = None

    return results, rotator.get_stats()
```

在 `weekly_analysis.py` 的 `main()` 中，在分析完成后保存 stats：

```python
import json as _json

# 在 main() 的 Step 2 之后（run_analysis 之后）加：
    # Save LLM key stats
    stats_path = ROOT / 'data' / 'llm-key-stats.json'
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    
    # run_analysis 需要 return key_stats（修改 run_analysis 接收并透传）
    # 如果 batch_analyze 返回了 stats，保存
    # ... 在 run_analysis 中将 stats 透传出来
    
    # 简化方案：直接在 run_analysis 中保存
```

**简化实现**：在 `run_analysis()` 函数中，`batch_analyze` 调用后直接保存 stats：

```python
def run_analysis(projects, max_projects=None, batch_size=None):
    # ... existing code ...
    
    all_key_stats = {}
    
    for i in range(0, len(to_analyze), batch_size):
        batch = to_analyze[i:i + batch_size]
        # ... existing code ...
        
        results, key_stats = batch_analyze(batch, prompt_fn, ANALYSIS_SYSTEM, max_workers=batch_size)
        
        # Merge key stats
        for kid, stat in key_stats.items():
            if kid not in all_key_stats:
                all_key_stats[kid] = {'calls': 0, 'success': 0, 'failed': 0, 'fail_reasons': []}
            all_key_stats[kid]['calls'] += stat['calls']
            all_key_stats[kid]['success'] += stat['success']
            all_key_stats[kid]['failed'] += stat['failed']
            all_key_stats[kid]['fail_reasons'].extend(stat['fail_reasons'])
        
        # ... existing merge code ...
    
    # Save key stats
    stats_path = ROOT / 'data' / 'llm-key-stats.json'
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_entry = {
        'date': today(),
        'total_calls': sum(s['calls'] for s in all_key_stats.values()),
        'total_success': sum(s['success'] for s in all_key_stats.values()),
        'total_failed': sum(s['failed'] for s in all_key_stats.values()),
        'keys': all_key_stats,
    }
    
    # Append to existing stats history
    existing_stats = []
    if stats_path.exists():
        try:
            existing_stats = _json.loads(stats_path.read_text(encoding='utf-8'))
            if not isinstance(existing_stats, list):
                existing_stats = [existing_stats]
        except (_json.JSONDecodeError, Exception):
            existing_stats = []
    
    existing_stats.append(stats_entry)
    # Keep only last 30 entries
    existing_stats = existing_stats[-30:]
    stats_path.write_text(_json.dumps(existing_stats, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Key stats saved: {stats_path}')
    
    return updated_projects
```

### 步骤 4：验证 + Commit

```bash
# 运行已有测试确保不破坏
python3 -m pytest tests/test_weekly_analysis.py tests/test_llm_api.py -v

# Dry-run 验证
python3 scripts/weekly_analysis.py --dry-run

# Commit
git add scripts/llm_api.py scripts/weekly_analysis.py
git commit -m "feat: add API key monitoring - log per-key call/success/fail stats"
```

---

## 任务 9：weekly_analysis.py 加降级策略

**问题**：daily LLM 增量分析固定 200 条，如果多个 key 同时触发 429，当前 `call_with_retry` 只重试 3 次后放弃，没有降级机制。

**目标**：检测 429 错误比例超过 30% 时，自动将 `--max-projects` 减半，标记 `degraded_mode: true`。下次运行 429 比例 < 10% 时恢复。

### 步骤 1：在 weekly_analysis.py 中加降级逻辑

在 `run_analysis()` 函数中，每个 batch 完成后检查 429 比例。如果超过阈值，减少剩余分析量。

在 `scripts/weekly_analysis.py` 的 `run_analysis()` 函数中加降级检查：

```python
def run_analysis(projects, max_projects=None, batch_size=None):
    """Run LLM analysis on projects in batches with degradation support."""
    if batch_size is None:
        batch_size = get_batch_size()
    to_analyze = get_projects_to_analyze(projects, max_projects)

    if not to_analyze:
        print(f'No projects need analysis (all analyzed within 7 days)')
        return projects

    # Degradation state
    original_count = len(to_analyze)
    degraded_mode = False
    total_429_errors = 0
    total_calls = 0

    print(f'Projects to analyze: {len(to_analyze)}')

    analyze_ids = {p.get('id') for p in to_analyze}
    all_results = {}
    all_key_stats = {}
    updated_projects = list(projects)

    def merge_into_projects(source_projects, results_map):
        merged = []
        for p in source_projects:
            pid = p.get('id')
            if pid in results_map:
                merged.append(merge_analysis_result(p, results_map[pid]))
            else:
                merged.append(p)
        return merged

    for i in range(0, len(to_analyze), batch_size):
        batch = to_analyze[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(to_analyze) - 1) // batch_size + 1
        print(f'\n--- Batch {batch_num}/{total_batches} ({len(batch)} projects) ---')

        def prompt_fn(p):
            return project_analysis_prompt(p)

        results, key_stats = batch_analyze(batch, prompt_fn, ANALYSIS_SYSTEM, max_workers=batch_size)

        # Merge key stats
        for kid, stat in key_stats.items():
            if kid not in all_key_stats:
                all_key_stats[kid] = {'calls': 0, 'success': 0, 'failed': 0, 'fail_reasons': []}
            all_key_stats[kid]['calls'] += stat['calls']
            all_key_stats[kid]['success'] += stat['success']
            all_key_stats[kid]['failed'] += stat['failed']
            all_key_stats[kid]['fail_reasons'].extend(stat['fail_reasons'])

        # Count 429 errors for degradation
        batch_429 = sum(1 for s in all_key_stats.values()
                        for r in s['fail_reasons'] if '429' in r or 'rate_limit' in r)
        batch_calls = sum(s['calls'] for s in all_key_stats.values())
        total_429_errors = batch_429
        total_calls = batch_calls

        for idx, result in results.items():
            project_id = batch[idx].get('id') if idx < len(batch) else None
            if project_id:
                all_results[project_id] = result
                status = 'OK' if result else 'FAILED'
                print(f'  {batch[idx].get("name", "?")}: {status}')

        updated_projects = merge_into_projects(projects, all_results)
        save_jsonish('data/projects.yaml', updated_projects)
        print(f'  Checkpoint saved ({len(all_results)} analyzed so far)')

        # Degradation check: if 429 rate > 30%, cut remaining work in half
        if total_calls > 10:  # only check after enough data
            rate_429 = total_429_errors / total_calls
            if rate_429 > 0.3 and not degraded_mode:
                degraded_mode = True
                remaining_batches = total_batches - batch_num
                if remaining_batches > 0:
                    # Skip half of remaining batches
                    skip_count = remaining_batches // 2
                    new_end = len(to_analyze) - (skip_count * batch_size)
                    to_analyze = to_analyze[:max(new_end, i + batch_size)]
                    print(f'  ⚠️  DEGRADED MODE: 429 rate {rate_429:.0%} > 30%, '
                          f'reducing remaining projects by half')
                    total_batches = (len(to_analyze) - 1) // batch_size + 1

    success_count = sum(1 for r in all_results.values() if r is not None)
    fail_count = sum(1 for r in all_results.values() if r is None)
    print(f'\nAnalysis complete: {success_count} success, {fail_count} failed')
    if degraded_mode:
        print(f'  ⚠️  Run was in DEGRADED MODE (analyzed {len(all_results)}/{original_count})')

    # Save key stats (same as task 8)
    stats_path = ROOT / 'data' / 'llm-key-stats.json'
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_entry = {
        'date': today(),
        'total_calls': sum(s['calls'] for s in all_key_stats.values()),
        'total_success': sum(s['success'] for s in all_key_stats.values()),
        'total_failed': sum(s['failed'] for s in all_key_stats.values()),
        'degraded_mode': degraded_mode,
        '429_errors': total_429_errors,
        'keys': all_key_stats,
    }
    import json as _json
    existing_stats = []
    if stats_path.exists():
        try:
            existing_stats = _json.loads(stats_path.read_text(encoding='utf-8'))
            if not isinstance(existing_stats, list):
                existing_stats = [existing_stats]
        except (_json.JSONDecodeError, Exception):
            existing_stats = []
    existing_stats.append(stats_entry)
    existing_stats = existing_stats[-30:]
    stats_path.write_text(_json.dumps(existing_stats, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Key stats saved: {stats_path}')

    return updated_projects
```

### 步骤 2：修改 daily LLM cron 脚本支持降级恢复

修改 `~/.hermes/scripts/search-in-coding-llm-daily.sh`，在上次降级模式下恢复全量：

```bash
cat > ~/.hermes/scripts/search-in-coding-llm-daily.sh << 'SCRIPT'
#!/bin/bash
# Daily LLM incremental analysis for Search in Coding (Tue–Sat)
set -euo pipefail

cd /root/workspace/search\ in\ coding || { echo "ERROR: workdir not found"; exit 1; }
source .venv/bin/activate

echo "=== LLM Daily Analysis Start: $(date) ==="

# Check if last run was degraded; if so, still try full 200 (auto-recovery)
MAX_PROJECTS=200
if [ -f data/llm-key-stats.json ]; then
  LAST_DEGRADED=$(python3 -c "
import json
try:
    data = json.load(open('data/llm-key-stats.json'))
    if isinstance(data, list) and data:
        last = data[-1]
        print('true' if last.get('degraded_mode') else 'false')
    else:
        print('false')
except: print('false')
" 2>/dev/null || echo "false")
  if [ "$LAST_DEGRADED" = "true" ]; then
    echo "Last run was degraded, attempting full recovery with $MAX_PROJECTS projects"
  fi
fi

# Incremental LLM analysis + deploy
python3 scripts/weekly_analysis.py \
  --max-projects $MAX_PROJECTS \
  --skip-benchmarks \
  2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "=== Deploying site ==="
  python3 scripts/deploy_site.py --dest /var/www/coding.lzpgood.online 2>&1
  EXIT_CODE=$?
fi

echo "=== LLM Daily Analysis End: $(date), exit=$EXIT_CODE ==="
exit $EXIT_CODE
SCRIPT
chmod +x ~/.hermes/scripts/search-in-coding-llm-daily.sh
```

### 步骤 3：验证 + Commit

```bash
# 运行已有测试
python3 -m pytest tests/test_weekly_analysis.py -v

# Dry-run
python3 scripts/weekly_analysis.py --dry-run

# Commit
git add scripts/weekly_analysis.py scripts/llm_api.py
git commit -m "feat: add 429 degradation strategy - auto-reduce analysis volume on rate limit"
```

---

## 任务 10：写清理脚本 scripts/cleanup_disk.py

**问题**：`data/raw/` 每天增长，`data/snapshots/` 每周增长。已有 `archive_raw.py` 处理 raw 归档，但不处理 snapshots 和 raw-archive 过期清理。

**目标**：统一清理脚本，raw 30 天、snapshots 90 天、raw-archive 90 天。

### 步骤 1：TDD - 先写测试

创建 `tests/test_cleanup_disk.py`：

```python
"""Test cleanup_disk.py logic."""
import pytest
import sys
import tempfile
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class TestParseDate:
    def test_parses_valid_date(self):
        from cleanup_disk import parse_date
        d = parse_date('2026-07-15')
        assert d == datetime.date(2026, 7, 15)

    def test_returns_none_for_invalid(self):
        from cleanup_disk import parse_date
        assert parse_date('not-a-date') is None
        assert parse_date('2026-13-45') is None
        assert parse_date('') is None


class TestFindExpiredDirs:
    def test_finds_old_raw_dirs(self, tmp_path):
        from cleanup_disk import find_expired_dirs
        # Create old and recent dirs
        old = tmp_path / '2026-06-01'
        recent = tmp_path / '2026-07-14'
        old.mkdir()
        recent.mkdir()
        today = datetime.date(2026, 7, 15)
        expired = find_expired_dirs(tmp_path, keep_days=30, today=today)
        names = [d.name for d in expired]
        assert '2026-06-01' in names
        assert '2026-07-14' not in names

    def test_skips_non_date_dirs(self, tmp_path):
        from cleanup_disk import find_expired_dirs
        (tmp_path / 'not-a-date').mkdir()
        (tmp_path / '2026-06-01').mkdir()
        today = datetime.date(2026, 7, 15)
        expired = find_expired_dirs(tmp_path, keep_days=30, today=today)
        names = [d.name for d in expired]
        assert '2026-06-01' in names
        assert 'not-a-date' not in names


class TestFindExpiredFiles:
    def test_finds_old_snapshot_files(self, tmp_path):
        from cleanup_disk import find_expired_files
        # Create old and recent JSON files
        old = tmp_path / '2026-04-01.json'
        recent = tmp_path / '2026-07-14.json'
        old.write_text('{}')
        recent.write_text('{}')
        today = datetime.date(2026, 7, 15)
        expired = find_expired_files(tmp_path, keep_days=90, today=today)
        names = [f.name for f in expired]
        assert '2026-04-01.json' in names
        assert '2026-07-14.json' not in names

    def test_skips_non_date_files(self, tmp_path):
        from cleanup_disk import find_expired_files
        (tmp_path / 'config.json').write_text('{}')
        (tmp_path / '2026-04-01.json').write_text('{}')
        today = datetime.date(2026, 7, 15)
        expired = find_expired_files(tmp_path, keep_days=90, today=today)
        names = [f.name for f in expired]
        assert '2026-04-01.json' in names
        assert 'config.json' not in names
```

### 步骤 2：实现脚本

创建 `scripts/cleanup_disk.py`：

```python
#!/usr/bin/env python3
"""Disk cleanup for old raw data, snapshots, and archives.

Cleans:
- data/raw/<source>/<date>/  — delete dirs older than --raw-days (default 30)
- data/snapshots/<date>.json — delete files older than --snapshot-days (default 90)
- data/raw-archive/<source>/<date>.tar.gz — delete archives older than --archive-days (default 90)

Does NOT clean: .venv/, cache/, site/

Usage:
    python3 scripts/cleanup_disk.py                # dry-run
    python3 scripts/cleanup_disk.py --apply        # execute deletion
    python3 scripts/cleanup_disk.py --apply --raw-days 15
"""
import argparse
import datetime
import json
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT


def parse_date(name):
    """Parse a date string, return date object or None."""
    try:
        return datetime.date.fromisoformat(name)
    except (ValueError, TypeError):
        return None


def find_expired_dirs(parent, keep_days, today=None):
    """Find subdirectories named as dates older than keep_days."""
    if today is None:
        today = datetime.date.today()
    expired = []
    if not parent.exists():
        return expired
    for d in sorted(parent.iterdir()):
        if not d.is_dir():
            continue
        dt = parse_date(d.name)
        if dt is None:
            continue
        if (today - dt).days > keep_days:
            expired.append(d)
    return expired


def find_expired_files(parent, keep_days, today=None):
    """Find files named <date>.json older than keep_days."""
    if today is None:
        today = datetime.date.today()
    expired = []
    if not parent.exists():
        return expired
    for f in sorted(parent.iterdir()):
        if not f.is_file():
            continue
        # Extract date from filename (e.g., "2026-04-01.json" -> "2026-04-01")
        stem = f.stem
        dt = parse_date(stem)
        if dt is None:
            continue
        if (today - dt).days > keep_days:
            expired.append(f)
    return expired


def main():
    ap = argparse.ArgumentParser(description='Clean up old raw data, snapshots, and archives')
    ap.add_argument('--raw-days', type=int, default=30, help='Delete raw dirs older than N days (default 30)')
    ap.add_argument('--snapshot-days', type=int, default=90, help='Delete snapshot files older than N days (default 90)')
    ap.add_argument('--archive-days', type=int, default=90, help='Delete archived tar.gz older than N days (default 90)')
    ap.add_argument('--apply', action='store_true', help='Execute deletion (default: dry-run)')
    args = ap.parse_args()

    today = datetime.date.today()
    actions = []

    # 1. Clean data/raw/<source>/<date>/
    raw_root = ROOT / 'data' / 'raw'
    if raw_root.exists():
        for source in ['github', 'exa', 'web']:
            source_dir = raw_root / source
            expired = find_expired_dirs(source_dir, args.raw_days, today)
            for d in expired:
                actions.append({
                    'action': 'delete_dir',
                    'path': str(d),
                    'age_days': (today - parse_date(d.name)).days,
                })
                if args.apply:
                    shutil.rmtree(d)

    # 2. Clean data/snapshots/<date>.json
    snapshots_dir = ROOT / 'data' / 'snapshots'
    expired_snaps = find_expired_files(snapshots_dir, args.snapshot_days, today)
    for f in expired_snaps:
        actions.append({
            'action': 'delete_file',
            'path': str(f),
            'age_days': (today - parse_date(f.stem)).days,
        })
        if args.apply:
            f.unlink()

    # 3. Clean data/raw-archive/<source>/<date>.tar.gz
    archive_root = ROOT / 'data' / 'raw-archive'
    if archive_root.exists():
        for source in ['github', 'exa', 'web']:
            source_dir = archive_root / source
            if source_dir.exists():
                for f in sorted(source_dir.iterdir()):
                    if not f.is_file() or not f.name.endswith('.tar.gz'):
                        continue
                    # Extract date from filename (e.g., "2026-06-01.tar.gz")
                    stem = f.name.replace('.tar.gz', '')
                    dt = parse_date(stem)
                    if dt is None:
                        continue
                    if (today - dt).days > args.archive_days:
                        actions.append({
                            'action': 'delete_archive',
                            'path': str(f),
                            'age_days': (today - dt).days,
                        })
                        if args.apply:
                            f.unlink()

    # Summary
    total_size = 0
    for a in actions:
        p = Path(a['path'])
        if p.exists():
            if p.is_file():
                total_size += p.stat().st_size
            elif p.is_dir():
                for fp in p.rglob('*'):
                    if fp.is_file():
                        total_size += fp.stat().st_size

    print(json.dumps({
        'apply': args.apply,
        'today': today.isoformat(),
        'raw_days': args.raw_days,
        'snapshot_days': args.snapshot_days,
        'archive_days': args.archive_days,
        'actions_count': len(actions),
        'estimated_size_mb': round(total_size / 1024 / 1024, 1),
        'actions': actions[:50],  # show first 50
    }, ensure_ascii=False, indent=2))

    if not args.apply and actions:
        print(f'\nDry run: {len(actions)} items would be cleaned. Use --apply to execute.')


if __name__ == '__main__':
    main()
```

### 步骤 3：验证 + Commit

```bash
# 运行测试
python3 -m pytest tests/test_cleanup_disk.py -v

# Dry-run 看看会清理什么
python3 scripts/cleanup_disk.py

# Commit
git add scripts/cleanup_disk.py tests/test_cleanup_disk.py
git commit -m "feat: add cleanup_disk.py - clean old raw/snapshots/archives"
```

---

## 最终验证清单

完成所有 10 个任务后，执行以下验证：

```bash
cd "/root/workspace/search in coding"
source .venv/bin/activate

# 1. 验证 daily cron 脚本（有 venv，无 deploy）
cat ~/.hermes/scripts/search-in-coding-daily.sh
grep "source .venv" ~/.hermes/scripts/search-in-coding-daily.sh
grep -c "deploy" ~/.hermes/scripts/search-in-coding-daily.sh  # 应为 0

# 2. 验证 cron 时间
hermes cron list | grep -E "daily|LLM|weekly|release"
# daily 采集: 0 3 * * *
# daily LLM: 0 5 * * 2-6
# weekly LLM: 0 5 * * 1
# weekly release: paused 或已删除

# 3. 验证 GitHub Actions
grep "pyyaml" .github/workflows/update-data.yml
grep -c "exa-limit" .github/workflows/update-data.yml  # 应为 0

# 4. 验证新脚本存在且有测试
ls -la scripts/refresh_track_projects.py scripts/archive_low_score.py scripts/cleanup_disk.py
ls -la tests/test_refresh_track_projects.py tests/test_archive_low_score.py tests/test_cleanup_disk.py

# 5. 运行所有测试
python3 -m pytest tests/ -v --tb=short

# 6. 验证 dry-run
python3 scripts/refresh_track_projects.py --dry-run --batch-size 5
python3 scripts/archive_low_score.py --threshold 20
python3 scripts/cleanup_disk.py

# 7. 验证 weekly_analysis.py 不破坏
python3 scripts/weekly_analysis.py --dry-run

# 8. 编译检查
python3 -m py_compile scripts/refresh_track_projects.py scripts/archive_low_score.py scripts/cleanup_disk.py scripts/llm_api.py scripts/weekly_analysis.py
```

## 最终 Commit

```bash
cd "/root/workspace/search in coding"
git add -A
git status
# 确认没有意外文件
git commit -m "feat: self-running hardening - 10 ops fixes

- daily cron: add source venv (no --deploy)
- daily LLM cron: 03:30 -> 05:00 (avoid write conflict)
- weekly LLM cron: 03:30 -> 05:00 (avoid write conflict)
- weekly release cron: disabled (GitHub Actions covers it)
- update-data.yml: add pyyaml, remove --exa-limit
- refresh_track_projects.py: batch refresh 1000/day
- archive_low_score.py: archive reject/low-score projects
- weekly_analysis.py: API key monitoring + 429 degradation
- cleanup_disk.py: clean raw(30d)/snapshots(90d)/archives(90d)
"
git push origin main
```

## 关键约束（再次强调）

1. **daily cron 不加 `--deploy`**：保持原始设计，LLM cron 负责 deploy
2. **不改评分公式**：`score.py` 的 100 分制保持不变
3. **不改前端框架**：vanilla JS + 分片 JSON 保持不变
4. **不改 LLM prompt**：`llm_prompts.py` 保持不变
5. **TDD for 新脚本**：`archive_low_score.py`、`refresh_track_projects.py`、`cleanup_disk.py` 需要先写测试
6. **频繁 commit**：每个任务完成后 commit 一次

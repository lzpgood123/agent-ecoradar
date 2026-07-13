# 批次 C：翻译 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将 274 条项目的英文 summary 通过 SenseNova API（DeepSeek-V4-Flash）翻译成中文，翻译结果缓存到 `data/translations-cache/`，并写入 `projects.yaml` 的 `i18n.zh.summary` 字段，消除「假双语」问题（dogfood #3）。

**架构：** 独立 Python 脚本 `scripts/translate_summaries.py`，通过 urllib 直接调用 SenseNova OpenAI 兼容 API。从 `~/.hermes/auth.json` 的 `credential_pool.custom:sensenova` 读取 13 个 API key，使用 `KeyRotator` 轮询。每批 3 并发（ThreadPoolExecutor），翻译结果按 URL hash 缓存到 `data/translations-cache/`，最终写入 `projects.yaml` 的 `i18n.zh.summary`。

**技术栈：** Python 3.12+（urllib, json, hashlib, concurrent.futures）, SenseNova API (OpenAI 兼容), PyYAML

**关联文档：**
- 设计规格：`docs/superpowers/specs/2026-07-13-site-optimization-v3-design.md`（"批次 C：翻译"章节）
- dogfood 报告：`docs/ux-dogfood-report-2026-07-13.md` Issue #3（中英双语几乎是假双语）
- P1-产品决策日志：`wiki/P1-产品决策日志.md`（"双语翻译先 curated 后全量"决策）

**前置条件：** 批次 A 已完成（summary 字段已修正为最终版，无后续修改）

**环境约束：**
- SenseNova API：base_url=`https://token.sensenova.cn/v1/chat/completions`，model=`deepseek-v4-flash`
- 凭证池：13 个 API key（存储在 `~/.hermes/auth.json` 的 `credential_pool.custom:sensenova` 中）
- API 模式：OpenAI 兼容 chat/completions
- 不使用 Hermes delegate_task（避免审批阻塞）
- HTTP 请求用 urllib，不依赖 requests/httpx
- 翻译缓存目录 `data/translations-cache/` 不入 Git（需加入 .gitignore）
- API key 不硬编码在代码中，从 `~/.hermes/auth.json` 读取

---

## 文件结构

### 新建文件

| 文件 | 职责 |
|------|------|
| `scripts/translate_summaries.py` | 主脚本：读取 projects.yaml -> 翻译 summary -> 缓存 -> 写回 i18n.zh.summary |
| `tests/test_translate_summaries.py` | 翻译脚本测试 |
| `data/translations-cache/` | 翻译缓存目录（按 URL hash 命名，不入 Git） |

### 修改文件

| 文件 | 修改内容 |
|------|---------|
| `.gitignore` | 添加 `data/translations-cache/` |

### 不修改的文件

| 文件 | 原因 |
|------|------|
| 前端代码（`site/`） | 本批不改前端 |
| `scripts/build_site.py` | 构建逻辑不变 |
| `data/projects.yaml` 的数据结构 | 只更新 `i18n.zh.summary` 值，不改字段结构 |
| `scripts/llm_api.py`（若已存在） | 复用其 `KeyRotator`；若不存在则在本脚本中内联实现 |

---

## API key 读取方式

```python
import json
from pathlib import Path

auth = json.loads(Path.home().joinpath('.hermes/auth.json').read_text())
pool = auth.get('credential_pool', {}).get('custom:sensenova', [])
keys = [e['access_token'] for e in pool if isinstance(e, dict) and e.get('access_token','').startswith('sk-')]
```

---

## 任务 1：翻译脚本核心实现

**文件：**
- 创建：`scripts/translate_summaries.py`
- 创建：`tests/test_translate_summaries.py`

- [ ] **步骤 1：编写翻译脚本测试**

```python
# tests/test_translate_summaries.py
"""Test the summary translation script."""
import pytest
import sys
import json
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class TestCacheKey:
    def test_cache_key_is_md5_prefix(self):
        from translate_summaries import cache_key
        url = 'https://github.com/foo/bar'
        expected = hashlib.md5(url.encode('utf-8')).hexdigest()[:16]
        assert cache_key(url) == expected

    def test_cache_key_deterministic(self):
        from translate_summaries import cache_key
        assert cache_key('https://github.com/a/b') == cache_key('https://github.com/a/b')


class TestCacheIO:
    def test_get_cached_returns_none_if_not_exists(self, tmp_path):
        from translate_summaries import get_cached
        with patch('translate_summaries.CACHE_DIR', tmp_path):
            assert get_cached('https://github.com/nonexistent/repo') is None

    def test_save_and_get_cached(self, tmp_path):
        from translate_summaries import save_cached, get_cached
        with patch('translate_summaries.CACHE_DIR', tmp_path):
            url = 'https://github.com/foo/bar'
            data = {'zh': '这是中文摘要', 'en': 'This is English summary'}
            save_cached(url, data)
            result = get_cached(url)
            assert result is not None
            assert result['zh'] == '这是中文摘要'
            assert result['en'] == 'This is English summary'


class TestNeedsTranslation:
    def test_english_summary_needs_translation(self):
        from translate_summaries import needs_translation
        project = {
            'summary': 'A CLI tool for AI coding',
            'i18n': {'zh': {'summary': 'A CLI tool for AI coding'}, 'en': {'summary': 'A CLI tool for AI coding'}}
        }
        assert needs_translation(project) is True

    def test_already_translated_skips(self):
        from translate_summaries import needs_translation
        project = {
            'summary': 'A CLI tool for AI coding',
            'i18n': {'zh': {'summary': '一个 AI 编程的命令行工具'}, 'en': {'summary': 'A CLI tool for AI coding'}}
        }
        assert needs_translation(project) is False

    def test_empty_summary_skips(self):
        from translate_summaries import needs_translation
        project = {'summary': '', 'i18n': {}}
        assert needs_translation(project) is False

    def test_already_has_chinese_skips(self):
        from translate_summaries import needs_translation
        project = {
            'summary': '这是一个中文描述',
            'i18n': {'zh': {'summary': '这是一个中文描述'}, 'en': {'summary': '这是一个中文描述'}}
        }
        assert needs_translation(project) is False


class TestLoadApiKeys:
    def test_load_keys_from_auth_json(self):
        from translate_summaries import load_api_keys
        keys = load_api_keys()
        assert isinstance(keys, list)
        for k in keys:
            assert isinstance(k, str)
            assert k.startswith('sk-')

    def test_no_auth_file_returns_empty(self, tmp_path):
        from translate_summaries import load_api_keys
        with patch.object(Path, 'home', return_value=tmp_path):
            keys = load_api_keys()
            assert keys == []


class TestKeyRotator:
    def test_round_robin(self):
        from translate_summaries import KeyRotator
        rotator = KeyRotator(['key1', 'key2', 'key3'])
        assert rotator.next() == 'key1'
        assert rotator.next() == 'key2'
        assert rotator.next() == 'key3'
        assert rotator.next() == 'key1'

    def test_skips_failed_keys(self):
        from translate_summaries import KeyRotator
        rotator = KeyRotator(['key1', 'key2', 'key3'])
        rotator.mark_failed('key2')
        assert rotator.next() == 'key1'
        assert rotator.next() == 'key3'

    def test_all_failed_resets(self):
        from translate_summaries import KeyRotator
        rotator = KeyRotator(['key1', 'key2'])
        rotator.mark_failed('key1')
        rotator.mark_failed('key2')
        # Should reset and return a key
        k = rotator.next()
        assert k in ('key1', 'key2')


class TestBuildPrompt:
    def test_prompt_contains_summary(self):
        from translate_summaries import build_translation_prompt
        prompt = build_translation_prompt('A great CLI tool for coding')
        assert 'A great CLI tool for coding' in prompt
        assert '中文' in prompt or 'Chinese' in prompt.lower() or 'translate' in prompt.lower()
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd "/root/workspace/search in coding" && source .venv/bin/activate && python3 -m pytest tests/test_translate_summaries.py -v`
预期：FAIL（模块不存在）

- [ ] **步骤 3：编写 translate_summaries.py**

```python
#!/usr/bin/env python3
"""Batch-translate project summaries to Chinese using SenseNova API.

Reads projects.yaml, translates each project's English summary to Chinese
via DeepSeek-V4-Flash, caches results by URL hash, and writes translations
back into i18n.zh.summary.

Usage:
    python3 scripts/translate_summaries.py              # translate all 274
    python3 scripts/translate_summaries.py --limit 5    # translate only 5
    python3 scripts/translate_summaries.py --dry-run    # show what would be done
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure scripts/ is on sys.path for common import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT, load_jsonish, save_jsonish

# === Constants ===

API_URL = 'https://token.sensenova.cn/v1/chat/completions'
MODEL = 'deepseek-v4-flash'
CACHE_DIR = ROOT / 'data' / 'translations-cache'
MAX_WORKERS = 3  # concurrent translation requests

TRANSLATION_SYSTEM = (
    "You are a professional translator specializing in software and AI technology. "
    "Translate the given English text into natural, fluent Chinese (Simplified). "
    "Keep technical terms, project names, and proper nouns in English. "
    "Respond with JSON only: {\"translated\": \" translated text \"}"
)


# === API Key Management ===

def load_api_keys():
    """Load API keys from ~/.hermes/auth.json credential pool."""
    auth_path = Path.home() / '.hermes' / 'auth.json'
    if not auth_path.exists():
        return []
    try:
        data = json.loads(auth_path.read_text(encoding='utf-8'))
        pool = data.get('credential_pool', {}).get('custom:sensenova', [])
        keys = []
        for entry in pool:
            if isinstance(entry, dict):
                key = entry.get('access_token', '')
                if key and key.startswith('sk-'):
                    keys.append(key)
            elif isinstance(entry, str) and entry.startswith('sk-'):
                keys.append(entry)
        return keys
    except (json.JSONDecodeError, KeyError):
        return []


class KeyRotator:
    """Round-robin key rotation with failure tracking."""

    def __init__(self, keys):
        self.keys = list(keys)
        self.index = 0
        self.failed = set()

    def next(self):
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
                return k
        return available[0]

    def mark_failed(self, key):
        self.failed.add(key)

    def reset(self):
        self.failed.clear()


# === Cache ===

def cache_key(url):
    """Generate cache key from URL (md5 hex, first 16 chars)."""
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:16]


def get_cached(url):
    """Get cached translation by URL."""
    key = cache_key(url)
    path = CACHE_DIR / f'{key}.json'
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return None
    return None


def save_cached(url, translation):
    """Save translation to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = cache_key(url)
    path = CACHE_DIR / f'{key}.json'
    path.write_text(
        json.dumps(translation, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


# === Translation Logic ===

def needs_translation(project):
    """Check if a project's summary needs translation.

    Returns True if:
    - summary is non-empty
    - summary contains English text (not already Chinese)
    - i18n.zh.summary is missing or identical to English summary
    """
    summary = project.get('summary', '')
    if not summary or len(summary) < 5:
        return False

    # Already has Chinese? Skip.
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', summary))
    if has_chinese:
        return False

    zh_summary = ''
    i18n = project.get('i18n', {})
    if isinstance(i18n, dict):
        zh = i18n.get('zh', {})
        if isinstance(zh, dict):
            zh_summary = zh.get('summary', '')

    # If zh.summary already differs from English, it's translated.
    if zh_summary and zh_summary != summary:
        return False

    return True


def build_translation_prompt(summary):
    """Build the LLM prompt for translating a summary."""
    return f"""Translate the following English text to Chinese (Simplified):

{summary[:500]}

Respond with JSON: {{"translated": "translated text here"}}"""


def call_llm(prompt, system_prompt, key, timeout=60):
    """Call SenseNova API. Returns response text or None."""
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': prompt},
    ]
    payload = {
        'model': MODEL,
        'messages': messages,
        'temperature': 0.3,
        'max_tokens': 1000,
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result.get('choices', [{}])[0].get('message', {}).get('content', '')
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')[:500] if e.fp else ''
        if e.code in (401, 403):
            raise KeyError(f'Auth failed: {e.code}')
        if e.code == 429:
            raise RateLimitError('Rate limited')
        print(f'  API error {e.code}: {error_body}')
        return None
    except (urllib.error.URLError, TimeoutError) as e:
        print(f'  Network error: {e}')
        return None


class RateLimitError(Exception):
    pass


def translate_with_retry(prompt, system_prompt, rotator, max_retries=3):
    """Translate with key rotation and retry."""
    for attempt in range(max_retries):
        try:
            key = rotator.next()
            result = call_llm(prompt, system_prompt, key)
            if result:
                return result
        except KeyError:
            rotator.mark_failed(key)
            print(f'  Key failed, rotating... (attempt {attempt+1}/{max_retries})')
        except RateLimitError:
            time.sleep(5 * (attempt + 1))
            print(f'  Rate limited, waiting... (attempt {attempt+1}/{max_retries})')
        except Exception as e:
            print(f'  Error: {e} (attempt {attempt+1}/{max_retries})')
    print(f'  All retries exhausted')
    return None


def parse_translation(text):
    """Extract translated text from LLM response."""
    if not text:
        return None
    text = text.strip()
    # Try direct JSON parse
    try:
        data = json.loads(text)
        return data.get('translated')
    except json.JSONDecodeError:
        pass
    # Try extracting from markdown code block
    md_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if md_match:
        try:
            data = json.loads(md_match.group(1).strip())
            return data.get('translated')
        except json.JSONDecodeError:
            pass
    # Try finding JSON object
    json_match = re.search(r'\{[^}]+\}', text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            return data.get('translated')
        except json.JSONDecodeError:
            pass
    # Fallback: use raw text if it looks like Chinese
    if re.search(r'[\u4e00-\u9fff]', text):
        return text.strip()
    return None


def translate_one(project, rotator):
    """Translate a single project's summary.

    Returns (project_id, translated_zh_summary) or (project_id, None).
    """
    url = project.get('url', '')
    summary = project.get('summary', '')

    # Check cache first
    cached = get_cached(url)
    if cached and cached.get('zh'):
        return project.get('id'), cached['zh']

    # Call LLM
    prompt = build_translation_prompt(summary)
    raw = translate_with_retry(prompt, TRANSLATION_SYSTEM, rotator)
    if not raw:
        return project.get('id'), None

    zh = parse_translation(raw)
    if not zh:
        return project.get('id'), None

    # Cache result
    save_cached(url, {'zh': zh, 'en': summary})
    return project.get('id'), zh


def run_translation(projects, limit=None, dry_run=False):
    """Run batch translation on projects.

    Args:
        projects: list of project dicts
        limit: max number of projects to translate (None = all)
        dry_run: if True, only report what would be done

    Returns:
        (total, translated_count, skipped_count, failed_count)
    """
    # Filter projects needing translation
    to_translate = [p for p in projects if needs_translation(p)]
    if limit:
        to_translate = to_translate[:limit]

    total = len(to_translate)
    print(f'Projects needing translation: {total}')
    print(f'Total projects in file: {len(projects)}')

    if dry_run:
        for p in to_translate[:10]:
            print(f'  - {p.get("id")}: {p.get("summary", "")[:60]}...')
        if total > 10:
            print(f'  ... and {total - 10} more')
        return total, 0, 0, 0

    keys = load_api_keys()
    if not keys:
        print('ERROR: No API keys found in ~/.hermes/auth.json')
        return total, 0, 0, total

    print(f'Loaded {len(keys)} API keys')
    rotator = KeyRotator(keys)

    translated_count = 0
    skipped_count = 0
    failed_count = 0

    # Build translation tasks
    tasks = {p.get('id'): p for p in to_translate}
    results = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for pid, project in tasks.items():
            future = executor.submit(translate_one, project, rotator)
            futures[future] = pid

        for future in as_completed(futures):
            pid = futures[future]
            try:
                proj_id, zh = future.result()
                if zh:
                    results[pid] = zh
                    translated_count += 1
                else:
                    failed_count += 1
                    print(f'  FAILED: {pid}')
            except Exception as e:
                failed_count += 1
                print(f'  EXCEPTION: {pid}: {e}')

            # Progress
            done = translated_count + failed_count + skipped_count
            if done % 10 == 0 or done == total:
                print(f'  Progress: {done}/{total} (translated={translated_count}, failed={failed_count})')

    # Write translations back to projects
    for p in projects:
        pid = p.get('id')
        if pid in results:
            i18n = p.setdefault('i18n', {})
            zh = i18n.setdefault('zh', {})
            zh['summary'] = results[pid]
            # Also ensure en.summary is set
            en = i18n.setdefault('en', {})
            if not en.get('summary'):
                en['summary'] = p.get('summary', '')

    print(f'\nTranslation complete: {translated_count} translated, {failed_count} failed')
    return total, translated_count, skipped_count, failed_count


# === Main ===

def main():
    parser = argparse.ArgumentParser(description='Batch translate project summaries to Chinese')
    parser.add_argument('--limit', type=int, default=None, help='Max projects to translate')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be translated')
    parser.add_argument('--file', default='data/projects.yaml', help='Data file to read/write')
    args = parser.parse_args()

    print(f'=== Summary Translation ===')
    projects = load_jsonish(args.file)
    print(f'Loaded {len(projects)} projects from {args.file}')

    total, translated, skipped, failed = run_translation(
        projects, limit=args.limit, dry_run=args.dry_run
    )

    if not args.dry_run and translated > 0:
        save_jsonish(args.file, projects)
        print(f'Saved {len(projects)} projects to {args.file}')
        print(f'Cache files in: {CACHE_DIR}')

    # Exit code: 0 if all succeeded, 1 if any failed
    sys.exit(1 if failed > 0 else 0)


if __name__ == '__main__':
    main()
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd "/root/workspace/search in coding" && source .venv/bin/activate && python3 -m pytest tests/test_translate_summaries.py -v`
预期：PASS

- [ ] **步骤 5：验证脚本语法**

运行：`cd "/root/workspace/search in coding" && python3 -m py_compile scripts/translate_summaries.py`
预期：无错误

- [ ] **步骤 6：Commit**

```bash
cd "/root/workspace/search in coding"
git add scripts/translate_summaries.py tests/test_translate_summaries.py
git commit -m "feat: add batch summary translation script with SenseNova API + cache + key rotation"
```

---

## 任务 2：更新 .gitignore

**文件：**
- 修改：`.gitignore`

- [ ] **步骤 1：添加翻译缓存目录到 .gitignore**

在 `.gitignore` 末尾添加：
```
# Translation cache (not for git)
data/translations-cache/
```

- [ ] **步骤 2：验证 .gitignore 生效**

运行：`cd "/root/workspace/search in coding" && git status`
预期：`data/translations-cache/` 不出现在 untracked 列表中

- [ ] **步骤 3：Commit**

```bash
cd "/root/workspace/search in coding"
git add .gitignore
git commit -m "chore: add translations-cache to gitignore"
```

---

## 任务 3：Dry-run 验证

- [ ] **步骤 1：运行 dry-run 确认待翻译数量**

运行：`cd "/root/workspace/search in coding" && python3 scripts/translate_summaries.py --dry-run`
预期输出：
- `Loaded 274 projects from data/projects.yaml`
- `Projects needing translation: 274`（或略少，取决于是否有已翻译的）
- 显示前 10 个待翻译项目

- [ ] **步骤 2：运行 dry-run with limit**

运行：`cd "/root/workspace/search in coding" && python3 scripts/translate_summaries.py --dry-run --limit 5`
预期：显示 5 个待翻译项目

---

## 任务 4：小批量实际翻译验证

- [ ] **步骤 1：翻译 3 个项目验证 API 连通**

运行：`cd "/root/workspace/search in coding" && python3 scripts/translate_summaries.py --limit 3`
预期：
- 3 个项目翻译成功
- `data/translations-cache/` 下生成 3 个 `.json` 缓存文件
- `data/projects.yaml` 中对应项目的 `i18n.zh.summary` 已更新为中文

- [ ] **步骤 2：验证缓存文件格式**

运行：`cd "/root/workspace/search in coding" && ls data/translations-cache/`
预期：至少 3 个 `.json` 文件

检查缓存内容（任选一个）：
```bash
cat data/translations-cache/*.json | head -5
```
预期：JSON 格式，含 `zh` 和 `en` 字段

- [ ] **步骤 3：验证 projects.yaml 更新**

运行：`cd "/root/workspace/search in coding" && python3 -c "
import yaml
data = yaml.safe_load(open('data/projects.yaml'))
for p in data:
    zh = p.get('i18n',{}).get('zh',{}).get('summary','')
    en = p.get('i18n',{}).get('en',{}).get('summary','')
    if zh != en and zh:
        print(f'{p[\"id\"]}: zh={zh[:40]}...')
        break
"`
预期：至少有 1 条项目的 `i18n.zh.summary` 与 `i18n.en.summary` 不同

- [ ] **步骤 4：Commit 小批量验证结果**

```bash
cd "/root/workspace/search in coding"
git add data/projects.yaml
git commit -m "feat: translate 3 project summaries to Chinese (validation run)"
```

---

## 任务 5：全量翻译

- [ ] **步骤 1：执行全量翻译**

运行：`cd "/root/workspace/search in coding" && python3 scripts/translate_summaries.py`
预期：
- 274 条项目翻译（减去已翻译的 3 条 = 约 271 条）
- 进度每 10 条打印一次
- 最终输出 `Translation complete: XXX translated, 0 failed`

**注意：** 全量翻译约需 271 条 / 3 并发 ≈ 90 轮 API 调用，预计 5-15 分钟。如果中途失败，脚本可重复运行（缓存机制保证已翻译的不会重复调用 API）。

- [ ] **步骤 2：处理失败项**

如果有失败的项目，检查失败原因：
```bash
cd "/root/workspace/search in coding"
python3 scripts/translate_summaries.py --dry-run
```
如果仍有未翻译项目，重新运行翻译脚本。

- [ ] **步骤 3：验证翻译覆盖率**

运行：
```bash
cd "/root/workspace/search in coding"
python3 -c "
import yaml, re
data = yaml.safe_load(open('data/projects.yaml'))
total = 0
translated = 0
failed = 0
for p in data:
    summary = p.get('summary', '')
    if not summary or len(summary) < 5:
        continue
    if re.search(r'[\u4e00-\u9fff]', summary):
        continue
    total += 1
    zh = p.get('i18n',{}).get('zh',{}).get('summary','')
    en = p.get('i18n',{}).get('en',{}).get('summary','')
    if zh and zh != en:
        translated += 1
    else:
        failed += 1
        print(f'  NOT TRANSLATED: {p[\"id\"]}')
print(f'Total English summaries: {total}')
print(f'Translated: {translated}')
print(f'Not translated: {failed}')
"
```
预期：`Not translated: 0`（或接近 0，个别极端情况可接受）

- [ ] **步骤 4：Commit 全量翻译结果**

```bash
cd "/root/workspace/search in coding"
git add data/projects.yaml
git commit -m "feat: batch translate all 274 project summaries to Chinese"
```

---

## 任务 6：重建站点并验证

- [ ] **步骤 1：重新构建站点**

运行：`cd "/root/workspace/search in coding" && python3 scripts/build_site.py`
预期：站点 JSON 文件包含中文 summary

- [ ] **步骤 2：验证站点 JSON 含中文翻译**

运行：
```bash
cd "/root/workspace/search in coding"
python3 -c "
import json
data = json.load(open('site/data/projects.json'))
zh_eq_en = 0
zh_diff = 0
for p in data:
    zh = p.get('i18n',{}).get('zh',{}).get('summary','')
    en = p.get('i18n',{}).get('en',{}).get('summary','')
    if zh == en:
        zh_eq_en += 1
    else:
        zh_diff += 1
print(f'zh==en (not translated): {zh_eq_en}')
print(f'zh!=en (translated): {zh_diff}')
"
```
预期：`zh!=en (translated)` 接近 274

- [ ] **步骤 3：部署站点**

运行：`cd "/root/workspace/search in coding" && python3 scripts/deploy_site.py`
预期：部署成功

- [ ] **步骤 4：线上验证**

访问 https://coding.lzpgood.online/，验证：
- 切换到「中文」后，项目卡片/表格/详情面板的 summary 显示中文
- 不再有「假双语」现象（dogfood #3 已修复）

---

## 任务 7：更新 Wiki

- [ ] **步骤 1：更新 wiki/L3-代码地图.md**

新增 `scripts/translate_summaries.py` 条目，说明其职责。

- [ ] **步骤 2：更新 wiki/L6-经验录.md**

新增经验条目：
- 标题：批量翻译 274 条 summary
- 现象：i18n.zh.summary 与 i18n.en.summary 完全相同（274/274），中文用户看到的是英文
- 解决方案：用 SenseNova API（DeepSeek-V4-Flash）批量翻译，13 key 轮询，3 并发，URL hash 缓存
- 注意事项：API key 从 `~/.hermes/auth.json` 读取，不硬编码；缓存目录不入 Git

---

## 验收标准

- [ ] `scripts/translate_summaries.py` 可 `--dry-run`，正确显示待翻译数量
- [ ] `scripts/translate_summaries.py --limit 3` 实际运行成功，3 个项目被翻译
- [ ] `data/translations-cache/` 有缓存文件，JSON 格式含 `zh` 和 `en` 字段
- [ ] `data/projects.yaml` 中 `i18n.zh.summary` 与 `i18n.en.summary` 不再完全相同
- [ ] 全量翻译后，274 条项目的 `i18n.zh.summary` 均为中文（或接近 100%）
- [ ] 站点重建后，中文 UI 下 summary 显示中文
- [ ] `data/translations-cache/` 在 `.gitignore` 中，不进入 Git
- [ ] API key 从 `~/.hermes/auth.json` 读取，代码中无硬编码 key
- [ ] 所有测试通过（`python3 -m pytest tests/test_translate_summaries.py -v`）
- [ ] 站点部署到 https://coding.lzpgood.online/ 并可访问

#!/usr/bin/env python3
"""One-time historical bulk collection of GitHub projects (stars-tier strategy).

Strategy (grilling 2026-07-14):
  - Time lower bound: created:>2024-01-01
  - Tiers L1→L5b by stars; no <100 stars this round
  - L1–L3: keyword-free full search + thin negative filter
  - L4: monthly + thin negative + weak positive
  - L5a/b: topic/keyword monthly + strict filter + stars≥3
  - Code search补漏 with tracking_priority=pending
  - Safe merge into data/projects.yaml (never clobber LLM fields / official-seed)
  - Checkpoint: search keys (tier|query|month_or_all) + completed_details fullNames

Usage:
    python3 scripts/initial_collection.py --dry-run
    python3 scripts/initial_collection.py
    python3 scripts/initial_collection.py --skip-existing
    python3 scripts/initial_collection.py  # resume via checkpoint automatically
"""
from __future__ import annotations

import argparse
import base64
import copy
import datetime
import json
import re
import sys
import time
from pathlib import Path

from common import ROOT, load_jsonish, save_jsonish, run, today

CHECKPOINT_FILE = ROOT / 'data' / 'initial-collection-checkpoint.json'
OUTPUT_DIR = ROOT / 'data' / 'raw' / 'github-initial'
DETAIL_BATCH_SIZE = 20
SEARCH_PAGE_LIMIT = 100  # gh search repos max fetch per call; no --page flag
MAX_SEARCH_PAGES = 3     # soft cap via limit = page * SEARCH_PAGE_LIMIT if API supports; we use single call limit

# ---------------------------------------------------------------------------
# Tier table
# ---------------------------------------------------------------------------

STAR_TIERS = [
    {
        'id': 'L1',
        'stars': '>=100000',
        'monthly': False,
        'search_mode': 'full',          # no keyword
        'filter_mode': 'thin_negative',
    },
    {
        'id': 'L2',
        'stars': '50000..99999',
        'monthly': False,
        'search_mode': 'full',
        'filter_mode': 'thin_negative',
    },
    {
        'id': 'L3',
        'stars': '10000..49999',
        'monthly': False,
        'search_mode': 'full',
        'filter_mode': 'thin_negative',
    },
    {
        'id': 'L4',
        'stars': '1000..9999',
        'monthly': True,
        'search_mode': 'full',
        'filter_mode': 'weak_positive',
    },
    {
        'id': 'L5a',
        'stars': '500..999',
        # adaptive: try full range first; only expand to months if hit page cap
        'monthly': 'adaptive',
        'search_mode': 'topic_keyword',
        'filter_mode': 'strict',
    },
    {
        'id': 'L5b',
        'stars': '100..499',
        'monthly': 'adaptive',
        'search_mode': 'topic_keyword',
        'filter_mode': 'strict',
    },
]

# ---------------------------------------------------------------------------
# Filter word lists
# ---------------------------------------------------------------------------

# Thin negative: L1–L3 always; also applied on other tiers.
# Avoid bare 'game' / 'cheat' (false positives on cheat sheet).
THIN_NEGATIVE = [
    'crypto', 'airdrop', 'miner', 'mining pool', 'puppies', 'dogs',
    '宠物', '赌', 'casino', 'gambling', 'nft drop', 'token airdrop',
    'solana meme', 'shitcoin', 'porn', 'nsfw',
]

# Weak positive: L4 — broad AI / coding-agent related words
# Note: short tokens (ai/mcp/gpt/rag) use word-boundary matching in _has_any.
WEAK_POSITIVE = [
    'ai', 'llm', 'gpt', 'claude', 'cursor', 'codex', 'mcp', 'agent',
    'coding agent', 'prompt', 'copilot', 'openai', 'anthropic',
    'gemini', 'opencode', 'agentic', 'langchain', 'autogen',
    'chatbot', 'transformer', 'ollama', 'vllm', 'rag',
    'code generation', 'code assistant', 'devtools', 'developer tool',
    'machine learning', 'deep learning', 'neural', 'foundation model',
    'large language', 'genai', 'generative',
]

# Coding signal for L4 refinement (applied only to NEW L4 candidates before detail)
CODING_SIGNAL = [
    'code', 'coding', 'developer', 'devtools', 'cli', 'ide', 'vscode',
    'agent', 'mcp', 'skill', 'prompt', 'copilot', 'cursor', 'claude',
    'codex', 'gemini', 'opencode', 'goose', 'llm', 'gpt', 'openai',
    'anthropic', 'repo', 'github', 'pr review', 'pull request',
    'codebase', 'programming', 'software engineer', 'dev tool',
]


def has_coding_signal(item) -> bool:
    return _has_any(_filter_text(item), CODING_SIGNAL)


# Strict positive: L5 + code search — more specific AI coding agent ecosystem
STRICT_POSITIVE = [
    'coding agent', 'code agent', 'agentic coding', 'agentic',
    'mcp server', 'mcp-server', 'model context protocol',
    'cursor rules', 'cursorrules', '.cursorrules', 'cursor rule',
    'claude code', 'claude-code', 'claude skill', 'claude.md',
    'agents.md', 'codex cli', 'codex-cli',
    'gemini cli', 'opencode', 'goose', 'hermes agent',
    'skills', 'skill pack', 'agent skill',
    'hooks', 'slash command', 'subagent',
    'ai coding', 'ai-coding', 'coding assistant',
    'devin', 'aider', 'continue.dev', 'cline', 'roo code',
    'pr review agent', 'code review agent',
    'context engineering', 'repo map', 'codebase index',
    'spec driven', 'agent framework', 'multi-agent',
    'workbuddy', 'codebuddy', 'qoder', 'trae',
]

# ---------------------------------------------------------------------------
# Query generators
# ---------------------------------------------------------------------------


def generate_topic_queries():
    """Generate GitHub topic search queries."""
    topics = [
        'claude-code', 'cursor-rules', 'mcp-server', 'agent-skills',
        'ai-coding', 'coding-agent', 'agentic-coding',
        'claude-skills', 'cursor-mcp', 'codex-cli',
        'gemini-cli', 'opencode', 'goose-ai',
        'ai-agent', 'llm-agent', 'devtools',
        'cursor-ai', 'continue-dev', 'aider',
    ]
    return [f'topic:{t}' for t in topics]


def generate_keyword_queries():
    """Generate keyword search queries for L5."""
    return [
        '"claude code" skills',
        '"claude code" mcp',
        '"claude code" hooks',
        '"cursor rules" mdc',
        '"cursor" mcp server',
        '"codex cli" AGENTS.md',
        '"codex" skills',
        '"gemini cli" extension',
        '"gemini cli" mcp',
        'opencode agent commands',
        'opencode mcp',
        'goose recipes extensions',
        'goose mcp agent',
        'qoder ai coding',
        'trae agent mcp',
        'workbuddy agent skills',
        'codebuddy agent',
        'hermes agent skills',
        'hermes agent cron',
        'AI coding agent context engineering',
        'mcp server coding agent',
        'AI PR review agent',
        'spec driven development AI coding',
        'codebase indexing AI coding agent',
        'continue.dev extension',
        'aider AI coding',
        'cline vscode agent',
        'roo code agent',
    ]


def generate_code_search_queries():
    """Generate code search queries for config file discovery."""
    return [
        'filename:CLAUDE.md',
        'filename:.cursorrules',
        'filename:AGENTS.md',
        'filename:.mdc path:.cursor/rules',
        'mcpServers extension:json',
    ]


def default_month_end(now: datetime.date | None = None) -> str:
    """Return current YYYY-MM for dynamic end of month range."""
    d = now or datetime.date.today()
    return f'{d.year:04d}-{d.month:02d}'


def generate_month_ranges(start, end):
    """Generate list of (first_day, last_day) tuples for each month."""
    start_year, start_month = int(start[:4]), int(start[5:7])
    end_year, end_month = int(end[:4]), int(end[5:7])
    ranges = []
    y, m = start_year, start_month
    while (y, m) <= (end_year, end_month):
        first = datetime.date(y, m, 1)
        if m == 12:
            last = datetime.date(y, 12, 31)
        else:
            last = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
        ranges.append((first.isoformat(), last.isoformat()))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return ranges


def build_tier_search_jobs(tier, month_ranges, topic_queries, keyword_queries, created_lower='2024-01-01'):
    """Build list of search jobs for a tier.

    Each job: {tier, query, stars, created, month_or_all, filter_mode, adaptive?}

    monthly values:
      - False: single full-range job (created:>lower)
      - True: one job per month
      - 'adaptive': one full-range probe job per query (month_or_all=all);
        runner expands to months only when raw hits the page cap
    """
    jobs = []
    stars = tier['stars']
    filter_mode = tier['filter_mode']
    tid = tier['id']
    monthly = tier.get('monthly', False)

    if tier['search_mode'] == 'full':
        queries = ['']  # keyword-free
    else:
        queries = list(topic_queries) + list(keyword_queries)

    if monthly is True:
        for start, end in month_ranges:
            created = f'{start}..{end}'
            for q in queries:
                jobs.append({
                    'tier': tid,
                    'query': q,
                    'stars': stars,
                    'created': created,
                    'month_or_all': created,
                    'filter_mode': filter_mode,
                    'adaptive': False,
                })
    elif monthly == 'adaptive':
        created = f'>{created_lower}'
        for q in queries:
            jobs.append({
                'tier': tid,
                'query': q,
                'stars': stars,
                'created': created,
                'month_or_all': 'all',
                'filter_mode': filter_mode,
                'adaptive': True,
            })
    else:
        created = f'>{created_lower}'
        for q in queries:
            jobs.append({
                'tier': tid,
                'query': q,
                'stars': stars,
                'created': created,
                'month_or_all': 'all',
                'filter_mode': filter_mode,
                'adaptive': False,
            })
    return jobs


def expand_topics_from_seeds(seeds, existing=None):
    """Build extra topic:X queries from seed repo topics (lightweight).

    `seeds` may be list of dicts with 'topics' already populated, or with 'repo'
    only (caller may pre-fetch). Existing bare topic names are not duplicated.
    """
    existing = set(existing or [])
    # normalize existing: accept both 'claude-code' and 'topic:claude-code'
    existing_bare = set()
    for e in existing:
        existing_bare.add(e.replace('topic:', '') if isinstance(e, str) else e)

    out = []
    seen = set(existing_bare)
    for s in seeds or []:
        topics = s.get('topics') or []
        for t in topics:
            if not t or not isinstance(t, str):
                continue
            bare = t.strip().lower()
            if not bare or bare in seen:
                continue
            seen.add(bare)
            out.append(f'topic:{bare}')
    return out


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def _filter_text(item) -> str:
    """Build text blob from fullName + description + topics."""
    name = item.get('fullName') or item.get('nameWithOwner') or item.get('name') or ''
    desc = item.get('description') or ''
    topics = item.get('topics') or item.get('repositoryTopics') or []
    topic_names = []
    for t in topics:
        if isinstance(t, dict):
            topic_names.append(t.get('name') or '')
        else:
            topic_names.append(str(t or ''))
    return f"{name} {desc} {' '.join(topic_names)}".lower()


def _stars_of(item) -> int:
    for k in ('stargazersCount', 'stargazerCount', 'stars'):
        v = item.get(k)
        if v is not None:
            try:
                return int(v)
            except (TypeError, ValueError):
                pass
    return 0


def _has_any(text: str, phrases) -> bool:
    """Phrase match with word-boundary care for short tokens (ai, mcp, gpt, rag)."""
    low = text.lower()
    for p in phrases:
        p = p.lower()
        if len(p) <= 3:
            # word boundary for short tokens to avoid 'ai' in 'email'/'train'
            if re.search(rf'(?<![a-z0-9]){re.escape(p)}(?![a-z0-9])', low):
                return True
        else:
            if p in low:
                return True
    return False


def passes_filter(item, mode='thin_negative') -> bool:
    """Return True if item should be kept for the given filter mode.

    modes:
      - thin_negative: drop if negative hit
      - weak_positive: negative veto + at least 1 weak positive
      - strict: negative veto + at least 1 strict positive + stars>=3
    """
    text = _filter_text(item)
    stars = _stars_of(item)

    if _has_any(text, THIN_NEGATIVE):
        return False

    if mode == 'thin_negative':
        return True

    if mode == 'weak_positive':
        return _has_any(text, WEAK_POSITIVE)

    if mode == 'strict':
        if stars < 3:
            return False
        return _has_any(text, STRICT_POSITIVE)

    return True


# ---------------------------------------------------------------------------
# Safe merge
# ---------------------------------------------------------------------------

LLM_PRESERVE_FIELDS = (
    'quality_score',
    'quality_detail',
    'tracking_priority',
    'last_analyzed',
    'benchmark_ref',
)

# GitHub quantifiable fields safe to refresh on existing records
GITHUB_REFRESH_FIELDS = (
    'stars', 'forks', 'license', 'topics', 'languages',
    'last_updated', 'status', 'readme_preview', 'name', 'repo',
)


def _has_analysis_trace(rec: dict) -> bool:
    if not rec:
        return False
    if rec.get('last_analyzed'):
        return True
    qs = rec.get('quality_score')
    try:
        if qs is not None and float(qs) > 0:
            return True
    except (TypeError, ValueError):
        pass
    qd = rec.get('quality_detail')
    if isinstance(qd, dict) and any(v for v in qd.values()):
        return True
    return False


def safe_merge_record(existing, incoming, today=None, skip_existing=False):
    """Merge incoming GitHub-normalized record into existing.

    Rules:
      - None existing → new record with first/last_seen=today, tracking_priority=pending
      - skip_existing=True and existing → return existing unchanged
      - official-seed: keep source_type/name/tracking_priority/LLM fields; refresh harmless meta
      - otherwise: refresh GitHub quant fields; preserve LLM/human fields; keep non-empty summary/i18n
    """
    day = today or datetime.date.today().isoformat()

    if existing is None:
        rec = copy.deepcopy(incoming)
        rec['first_seen'] = rec.get('first_seen') or day
        rec['last_seen'] = day
        rec.setdefault('tracking_priority', 'pending')
        rec.setdefault('quality_score', 0)
        return rec

    if skip_existing:
        return existing

    out = copy.deepcopy(existing)
    inc = incoming or {}

    # official-seed protection
    if out.get('source_type') == 'official-seed':
        for k in GITHUB_REFRESH_FIELDS:
            if k == 'name':
                continue  # keep seed display name
            v = inc.get(k)
            if v is not None and v != '' and v != []:
                out[k] = v
        if not out.get('repo') and inc.get('repo'):
            out['repo'] = inc['repo']
        out['last_seen'] = day
        out['source_type'] = 'official-seed'
        out['tracking_priority'] = 'track'
        return out

    # refresh GitHub quantifiable fields
    for k in GITHUB_REFRESH_FIELDS:
        v = inc.get(k)
        if v is None or v == '' or v == []:
            continue
        if k == 'name' and out.get('name') and out.get('source_type') == 'official-seed':
            continue
        out[k] = v

    # summary: only fill if old empty
    if not (out.get('summary') or '').strip():
        if inc.get('summary'):
            out['summary'] = inc['summary']

    # i18n: keep existing non-empty better i18n
    old_i18n = out.get('i18n') or {}
    new_i18n = inc.get('i18n') or {}
    if not old_i18n:
        out['i18n'] = new_i18n
    else:
        # keep old if it has non-empty zh/en summaries
        def _summ(block, lang):
            return ((block or {}).get(lang) or {}).get('summary') or ''
        keep = bool(_summ(old_i18n, 'zh').strip() or _summ(old_i18n, 'en').strip())
        if not keep and new_i18n:
            out['i18n'] = new_i18n

    # preserve LLM / human fields
    for k in LLM_PRESERVE_FIELDS:
        if k in existing and existing.get(k) is not None:
            # always preserve tracking_priority / last_analyzed / quality_* if set on existing
            if k == 'tracking_priority' and existing.get(k):
                out[k] = existing[k]
            elif k in ('quality_score', 'quality_detail', 'last_analyzed', 'benchmark_ref'):
                if existing.get(k) not in (None, '', {}, 0, 0.0) or _has_analysis_trace(existing):
                    out[k] = existing.get(k)

    # review_state: keep non-default if analysis trace
    if _has_analysis_trace(existing) or (
        existing.get('review_state') and existing.get('review_state') != 'auto-indexed'
    ):
        out['review_state'] = existing.get('review_state')

    # first_seen keep; last_seen update
    out['first_seen'] = existing.get('first_seen') or day
    out['last_seen'] = day

    # never let incoming overwrite source_type to degrade
    if existing.get('source_type') == 'official-seed':
        out['source_type'] = 'official-seed'

    return out


def index_projects(projects):
    """Build lookup maps by url and by repo/fullName."""
    by_url = {}
    by_repo = {}
    for p in projects or []:
        url = (p.get('url') or '').rstrip('/')
        repo = (p.get('repo') or '').lower()
        if url:
            by_url[url] = p
        if repo:
            by_repo[repo] = p
        # also index github.com/{repo} form
        if not repo and url and 'github.com/' in url:
            tail = url.split('github.com/', 1)[-1].strip('/')
            if tail:
                by_repo[tail.lower()] = p
    return by_url, by_repo


def find_existing(record, by_url, by_repo):
    url = (record.get('url') or '').rstrip('/')
    repo = (record.get('repo') or '').lower()
    if url and url in by_url:
        return by_url[url]
    if repo and repo in by_repo:
        return by_repo[repo]
    return None


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------


class CheckpointManager:
    """Manage checkpoint for resume support.

    Search key: tier|query|month_or_all
    Details: completed_details list/set of fullName
    """

    def __init__(self, path):
        self.path = Path(path)
        self.data = self._load()

    def _load(self):
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError):
                raw = {}
        else:
            raw = {}
        # normalize structure
        if 'completed' not in raw:
            raw['completed'] = {}
        if 'completed_details' not in raw:
            raw['completed_details'] = []
        if 'stats' not in raw:
            raw['stats'] = {
                'total_queries': 0,
                'total_results': 0,
                'total_searches': 0,
                'total_search_results': 0,
            }
        # ensure list uniqueness
        if not isinstance(raw['completed_details'], list):
            raw['completed_details'] = list(raw['completed_details'])
        return raw

    def _search_key(self, tier, query, month_or_all):
        return f'{tier}|{query}|{month_or_all}'

    def mark_search_done(self, tier, query, month_or_all, pages=1, results_count=0):
        key = self._search_key(tier, query, month_or_all)
        self.data['completed'][key] = {
            'tier': tier,
            'query': query,
            'month_or_all': month_or_all,
            'pages': pages,
            'results': results_count,
            'timestamp': datetime.datetime.now().isoformat(),
        }
        self.data['stats']['total_searches'] = len(self.data['completed'])
        self.data['stats']['total_queries'] = len(self.data['completed'])
        # recompute total results from completed to avoid double-count on rewrite
        self.data['stats']['total_search_results'] = sum(
            (v.get('results') or 0) for v in self.data['completed'].values()
        )
        self.data['stats']['total_results'] = self.data['stats']['total_search_results']
        self._write()

    def is_search_done(self, tier, query, month_or_all):
        key = self._search_key(tier, query, month_or_all)
        return key in self.data['completed']

    # ---- legacy API (old tests / old checkpoints) ----
    def save(self, query, month_range, pages, results_count):
        """Legacy: query×month key stored under tier=legacy."""
        self.mark_search_done('legacy', query, month_range, pages=pages, results_count=results_count)

    def is_done(self, query, month_range):
        return self.is_search_done('legacy', query, month_range)

    def mark_detail_done(self, full_name):
        if not full_name:
            return
        details = self.data.setdefault('completed_details', [])
        if full_name not in details:
            details.append(full_name)
            self._write()

    def is_detail_done(self, full_name):
        return full_name in set(self.data.get('completed_details') or [])

    def completed_details(self):
        return list(self.data.get('completed_details') or [])

    def get_progress(self):
        return {
            'total_searches': len(self.data.get('completed') or {}),
            'total_queries': len(self.data.get('completed') or {}),
            'total_search_results': self.data.get('stats', {}).get('total_search_results')
            or self.data.get('stats', {}).get('total_results') or 0,
            'total_results': self.data.get('stats', {}).get('total_search_results')
            or self.data.get('stats', {}).get('total_results') or 0,
            'completed_details': len(self.data.get('completed_details') or []),
        }

    def _write(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )


# ---------------------------------------------------------------------------
# GitHub search / detail helpers
# ---------------------------------------------------------------------------


def gh_search_repos(query, stars, created, sort='stars', limit=SEARCH_PAGE_LIMIT):
    """Search GitHub repos using gh CLI flags (created/stars as flags).

    Note: free-text qualifiers for created/stars are unreliable in gh 2.67;
    always pass --created / --stars flags. `query` may be empty for full search.
    """
    # Build command carefully with shell quoting via json.dumps for free text
    q_part = ''
    if query:
        q_part = f' {json.dumps(query)}'
    fields = (
        'fullName,description,stargazersCount,url,updatedAt,language,'
        'forksCount,isArchived,createdAt'
    )
    cmd = (
        f'gh search repos{q_part}'
        f' --stars {json.dumps(str(stars))}'
        f' --created {json.dumps(str(created))}'
        f' --sort {sort}'
        f' --limit {int(limit)}'
        f' --json {fields}'
    )
    r = run(cmd, timeout=180)
    if r.returncode != 0:
        return [], r.stderr or r.stdout
    try:
        return json.loads(r.stdout or '[]'), None
    except json.JSONDecodeError as e:
        return [], str(e)


def gh_search_code(query, limit=SEARCH_PAGE_LIMIT):
    """Search GitHub code for config file discovery."""
    cmd = f'gh search code {json.dumps(query)} --limit {int(limit)} --json repository,path'
    r = run(cmd, timeout=180)
    if r.returncode != 0:
        return [], r.stderr or r.stdout
    try:
        return json.loads(r.stdout or '[]'), None
    except json.JSONDecodeError as e:
        return [], str(e)


def fetch_readme(full_name: str) -> str:
    """Fetch README text via gh api; empty string on failure."""
    cmd = f'gh api repos/{full_name}/readme --jq .content'
    rr = run(cmd, timeout=60)
    if rr.returncode != 0 or not (rr.stdout or '').strip():
        return ''
    try:
        return base64.b64decode(rr.stdout.strip()).decode('utf-8', errors='replace')
    except Exception:
        return ''


def repo_view(full_name: str, fetch_readme_text: bool = True) -> dict | None:
    """gh repo view + optional README first 500 chars."""
    fields = (
        'nameWithOwner,description,url,homepageUrl,stargazerCount,forkCount,'
        'licenseInfo,repositoryTopics,primaryLanguage,pushedAt,createdAt,'
        'updatedAt,isArchived,latestRelease'
    )
    cmd = f'gh repo view {full_name} --json {fields}'
    r = run(cmd, timeout=120)
    # core API pacing (~5000/hr); keep light to finish bulk history run
    time.sleep(0.12)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or '').lower()
        if 'rate limit' in err or 'secondary rate' in err or '403' in err:
            print(f'  rate limit on repo view {full_name}; sleeping 70s')
            time.sleep(70)
            r = run(cmd, timeout=120)
            time.sleep(0.12)
            if r.returncode != 0:
                return None
        else:
            return None
    try:
        rec = json.loads(r.stdout or '{}')
    except json.JSONDecodeError:
        return None
    if fetch_readme_text:
        readme = fetch_readme(full_name)
        time.sleep(0.05)
        rec['readme'] = readme[:500] if readme else ''
    else:
        rec['readme'] = ''
    return rec


def fetch_seed_topics(repo: str) -> list:
    """Best-effort topics for a seed repo; empty on failure."""
    if not repo:
        return []
    cmd = f'gh repo view {repo} --json repositoryTopics'
    r = run(cmd, timeout=60)
    if r.returncode != 0:
        return []
    try:
        data = json.loads(r.stdout or '{}')
    except json.JSONDecodeError:
        return []
    topics_raw = data.get('repositoryTopics') or []
    out = []
    for t in topics_raw:
        if isinstance(t, dict) and t.get('name'):
            out.append(t['name'])
        elif isinstance(t, str):
            out.append(t)
    return out


# ---------------------------------------------------------------------------
# Collection phases
# ---------------------------------------------------------------------------

CANDIDATES_FILE = OUTPUT_DIR / 'candidates.json'
SEARCH_CACHE_DIR = OUTPUT_DIR / 'search-cache'


def _cache_key(tier, query, month_or_all) -> str:
    raw = f'{tier}|{query}|{month_or_all}'
    return re.sub(r'[^a-zA-Z0-9._-]+', '_', raw)[:180]


def load_search_cache(tier, query, month_or_all):
    path = SEARCH_CACHE_DIR / f'{_cache_key(tier, query, month_or_all)}.json'
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None


def save_search_cache(tier, query, month_or_all, kept_items):
    SEARCH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = SEARCH_CACHE_DIR / f'{_cache_key(tier, query, month_or_all)}.json'
    # store compact kept items
    compact = []
    for it in kept_items:
        compact.append({
            'fullName': it.get('fullName'),
            'description': it.get('description') or '',
            'stargazersCount': it.get('stargazersCount') or it.get('stargazerCount') or 0,
            'url': it.get('url'),
            'language': it.get('language'),
            'forksCount': it.get('forksCount'),
            'isArchived': it.get('isArchived'),
            'createdAt': it.get('createdAt'),
            'updatedAt': it.get('updatedAt'),
        })
    path.write_text(json.dumps(compact, ensure_ascii=False), encoding='utf-8')


def load_candidates():
    if not CANDIDATES_FILE.exists():
        return {}
    try:
        data = json.loads(CANDIDATES_FILE.read_text(encoding='utf-8'))
        # normalize: fullName -> (item, filter_mode, tier)
        out = {}
        if isinstance(data, dict):
            for fn, val in data.items():
                if isinstance(val, dict) and 'item' in val:
                    out[fn] = (val['item'], val.get('filter_mode', 'thin_negative'), val.get('tier', '?'))
                elif isinstance(val, list) and len(val) == 3:
                    out[fn] = (val[0], val[1], val[2])
        return out
    except (json.JSONDecodeError, OSError):
        return {}


def save_candidates(all_candidates):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    serial = {}
    for fn, (item, mode, tier) in all_candidates.items():
        serial[fn] = {'item': item, 'filter_mode': mode, 'tier': tier}
    CANDIDATES_FILE.write_text(json.dumps(serial, ensure_ascii=False), encoding='utf-8')


def _execute_one_search(job, checkpoint, stats):
    """Run a single non-adaptive search job; return (kept, raw_count).

    Resume behavior:
      - if search key done AND cache exists → return cache
      - if search key done BUT cache missing → re-fetch (old runs lost results)
    """
    tier = job['tier']
    query = job['query']
    month_or_all = job['month_or_all']

    if checkpoint.is_search_done(tier, query, month_or_all):
        cached = load_search_cache(tier, query, month_or_all)
        if cached is not None:
            stats['skipped_search'] += 1
            # recover raw count from checkpoint entry
            key = f'{tier}|{query}|{month_or_all}'
            raw_n = (checkpoint.data.get('completed') or {}).get(key, {}).get('results') or len(cached)
            return cached, int(raw_n)
        # cache miss: fall through and re-fetch
        print(f"  cache-miss re-fetch {tier}|{query or '(full)'}|{month_or_all}")

    limit = SEARCH_PAGE_LIMIT * MAX_SEARCH_PAGES  # up to 300
    results, err = gh_search_repos(
        query=query,
        stars=job['stars'],
        created=job['created'],
        limit=limit,
    )
    # polite pause for search API (~30 req/min)
    time.sleep(2.1)
    if err:
        print(f"  ERROR search {tier}|{query}|{month_or_all}: {str(err)[:200]}")
        stats['search_errors'] += 1
        err_l = str(err).lower()
        if 'rate limit' in err_l or 'api rate limit' in err_l or 'secondary rate' in err_l:
            print('  rate limit — sleeping 65s then one retry...')
            time.sleep(65)
            results, err = gh_search_repos(
                query=query,
                stars=job['stars'],
                created=job['created'],
                limit=limit,
            )
            time.sleep(2.1)
            if err:
                err_l2 = str(err).lower()
                if 'rate limit' in err_l2 or 'secondary rate' in err_l2:
                    raise RuntimeError(f'rate limit hit after retry: {err[:300]}')
                print(f"  ERROR retry failed: {str(err)[:200]}")
                checkpoint.mark_search_done(tier, query, month_or_all, pages=0, results_count=0)
                save_search_cache(tier, query, month_or_all, [])
                return [], 0
        else:
            checkpoint.mark_search_done(tier, query, month_or_all, pages=0, results_count=0)
            save_search_cache(tier, query, month_or_all, [])
            return [], 0

    kept = []
    for item in results:
        if passes_filter(item, mode=job['filter_mode']):
            kept.append(item)
        else:
            stats['filtered'] += 1

    pages = max(1, (len(results) + SEARCH_PAGE_LIMIT - 1) // SEARCH_PAGE_LIMIT) if results else 0
    checkpoint.mark_search_done(tier, query, month_or_all, pages=pages, results_count=len(results))
    save_search_cache(tier, query, month_or_all, kept)
    stats['search_results'] += len(results)
    stats['kept'] += len(kept)
    print(f"  {tier}|{query or '(full)'}|{month_or_all}: raw={len(results)} kept={len(kept)}")
    return kept, len(results)


def run_search_job(job, checkpoint, stats, month_ranges=None, created_lower='2024-01-01'):
    """Execute one search job; adaptive jobs expand to months if page-capped.

    Returns list of raw search items that pass filter.
    """
    if not job.get('adaptive'):
        kept, _ = _execute_one_search(job, checkpoint, stats)
        return kept

    # Adaptive: probe full range first
    probe = dict(job)
    probe['created'] = f'>{created_lower}'
    probe['month_or_all'] = 'all'
    probe['adaptive'] = False

    kept, raw_n = _execute_one_search(probe, checkpoint, stats)
    limit = SEARCH_PAGE_LIMIT * MAX_SEARCH_PAGES
    if raw_n < limit:
        return kept

    # Hit page cap — expand to monthly for this query
    print(f"  adaptive expand {job['tier']}|{job['query'] or '(full)'}: raw={raw_n}>={limit}, monthly split")
    all_kept = list(kept)
    for start, end in (month_ranges or []):
        mjob = {
            'tier': job['tier'],
            'query': job['query'],
            'stars': job['stars'],
            'created': f'{start}..{end}',
            'month_or_all': f'{start}..{end}',
            'filter_mode': job['filter_mode'],
            'adaptive': False,
        }
        mkept, _ = _execute_one_search(mjob, checkpoint, stats)
        all_kept.extend(mkept)
    return all_kept


def collect_code_search(checkpoint, stats):
    """Run code search queries; return set of fullNames.

    Results are cached under search-cache so resume can rebuild the set even
    after a refine pass dropped code candidates that lacked descriptions.
    """
    queries = generate_code_search_queries()
    repos = set()
    for query in queries:
        cached = load_search_cache('code', query, 'code-search')
        if cached is not None:
            for r in cached:
                repo = r.get('repository') or {}
                fn = repo.get('nameWithOwner') or r.get('fullName') or r.get('repository')
                if isinstance(fn, dict):
                    fn = fn.get('nameWithOwner')
                if isinstance(fn, str) and fn:
                    repos.add(fn)
            if checkpoint.is_search_done('code', query, 'code-search'):
                stats['skipped_search'] += 1
            print(f"  code:{query}: from_cache={len(cached)} unique_so_far={len(repos)}")
            continue

        if checkpoint.is_search_done('code', query, 'code-search'):
            # Done but no cache (older run) — cannot rebuild; skip
            stats['skipped_search'] += 1
            print(f"  code:{query}: checkpoint done, no cache — skip rebuild")
            continue

        results, err = gh_search_code(query, limit=SEARCH_PAGE_LIMIT * MAX_SEARCH_PAGES)
        time.sleep(2.5)
        if err:
            print(f"  ERROR code:{query}: {str(err)[:200]}")
            stats['search_errors'] += 1
            err_l = str(err).lower()
            if 'rate limit' in err_l or 'secondary rate' in err_l:
                print('  code search rate limit — sleep 65s + retry once')
                time.sleep(65)
                results, err = gh_search_code(query, limit=SEARCH_PAGE_LIMIT * MAX_SEARCH_PAGES)
                time.sleep(2.5)
                if err and ('rate limit' in str(err).lower() or 'secondary' in str(err).lower()):
                    raise RuntimeError(f'code search rate limit: {err[:300]}')
                if err:
                    checkpoint.mark_search_done('code', query, 'code-search', pages=0, results_count=0)
                    continue
            else:
                checkpoint.mark_search_done('code', query, 'code-search', pages=0, results_count=0)
                continue
        # normalize cache entries to include fullName for easier reload
        cache_rows = []
        for r in results:
            repo = r.get('repository') or {}
            fn = repo.get('nameWithOwner')
            if fn:
                repos.add(fn)
                cache_rows.append({'fullName': fn, 'repository': {'nameWithOwner': fn}})
        save_search_cache('code', query, 'code-search', cache_rows if cache_rows else results)
        checkpoint.mark_search_done('code', query, 'code-search', pages=1, results_count=len(results))
        print(f"  code:{query}: raw={len(results)} unique_so_far={len(repos)}")
    return repos


def detail_and_merge(full_names, tools, checkpoint, skip_existing, stats, label='details',
                     fetch_readme_text=True):
    """Fetch details for fullNames, normalize, safe-merge into projects.yaml every N=20."""
    from normalize import github_record

    existing = load_jsonish('data/projects.yaml') or []
    by_url, by_repo = index_projects(existing)
    day = today()
    pending_details = []
    processed = 0
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    todo = [fn for fn in full_names if not checkpoint.is_detail_done(fn)]
    print(f'  {label}: {len(todo)} to fetch (skip {len(full_names) - len(todo)} done) '
          f'readme={fetch_readme_text}')

    for fn in todo:
        detail = repo_view(fn, fetch_readme_text=fetch_readme_text)
        if not detail:
            stats['detail_errors'] += 1
            checkpoint.mark_detail_done(fn)  # don't infinite-retry hard failures
            continue

        # code-search candidates may need post-filter with full metadata
        # Build a synthetic item for strict filter
        topics_raw = detail.get('repositoryTopics') or []
        topic_names = [
            (t.get('name') if isinstance(t, dict) else t) for t in topics_raw
        ]
        topic_names = [t for t in topic_names if t]
        filter_item = {
            'fullName': detail.get('nameWithOwner') or fn,
            'description': detail.get('description') or '',
            'topics': topic_names,
            'stargazerCount': detail.get('stargazerCount') or 0,
        }
        # For code search path we always use strict; for star-tier path candidates
        # already passed tier filter, but re-check thin_negative on rich text is fine.
        # Caller can set stats['force_strict']
        mode = stats.get('detail_filter_mode') or 'thin_negative'
        if not passes_filter(filter_item, mode=mode):
            stats['filtered'] += 1
            checkpoint.mark_detail_done(fn)
            continue

        rec = github_record(detail, tools)
        if not rec:
            checkpoint.mark_detail_done(fn)
            continue

        # force pending for new code-search items (github_record already sets pending)
        found = find_existing(rec, by_url, by_repo)
        if found is None and stats.get('force_pending'):
            rec['tracking_priority'] = 'pending'

        merged = safe_merge_record(found, rec, today=day, skip_existing=skip_existing)
        if found is None:
            existing.append(merged)
            by_url[(merged.get('url') or '').rstrip('/')] = merged
            if merged.get('repo'):
                by_repo[merged['repo'].lower()] = merged
            stats['added'] += 1
        else:
            # replace in list
            for i, p in enumerate(existing):
                if p is found or (
                    (p.get('url') or '').rstrip('/') == (found.get('url') or '').rstrip('/')
                ):
                    existing[i] = merged
                    break
            by_url[(merged.get('url') or '').rstrip('/')] = merged
            if merged.get('repo'):
                by_repo[merged['repo'].lower()] = merged
            if not skip_existing:
                stats['updated'] += 1
            else:
                stats['skipped_existing'] += 1

        pending_details.append(detail)
        checkpoint.mark_detail_done(fn)
        processed += 1

        if processed % DETAIL_BATCH_SIZE == 0:
            # flush raw details + projects
            _append_raw_details(pending_details)
            pending_details = []
            save_jsonish('data/projects.yaml', existing)
            print(f'  checkpoint flush: processed={processed} total_projects={len(existing)}')

    if pending_details:
        _append_raw_details(pending_details)
    save_jsonish('data/projects.yaml', existing)
    return existing


def _append_raw_details(details):
    """Append details to OUTPUT_DIR/repo-details.jsonl (json lines) for resume evidence."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / 'repo-details.jsonl'
    with path.open('a', encoding='utf-8') as f:
        for d in details:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')


def print_dry_run(month_ranges, topic_queries, keyword_queries, code_queries, seed_topics):
    print('=== DRY RUN: Initial Collection plan ===')
    print(f'Created lower bound: >2024-01-01')
    print(f'Month ranges ({len(month_ranges)}): {month_ranges[0]} .. {month_ranges[-1]}')
    print(f'Topic queries ({len(topic_queries)}): {topic_queries}')
    print(f'Keyword queries ({len(keyword_queries)}): {keyword_queries[:5]}... (+{max(0,len(keyword_queries)-5)} more)')
    print(f'Code search queries: {code_queries}')
    print(f'Seed-expanded topics: {seed_topics}')
    print()
    total_jobs = 0
    for tier in STAR_TIERS:
        jobs = build_tier_search_jobs(
            tier, month_ranges, topic_queries, keyword_queries, created_lower='2024-01-01'
        )
        total_jobs += len(jobs)
        print(f"  {tier['id']} stars={tier['stars']} monthly={tier['monthly']} "
              f"mode={tier['search_mode']} filter={tier['filter_mode']} jobs={len(jobs)}")
        if jobs:
            sample = jobs[0]
            print(f"    sample: query={sample['query']!r} created={sample['created']}")
    print(f'Total search jobs (excl. code): {total_jobs}')
    print('Means: stars-tier main search + topic/keyword (L5) + seed topic expand + code search')
    print('NOT doing: dependents API, README link extraction, stars<100')
    print(f'Search page limit per query: {SEARCH_PAGE_LIMIT * MAX_SEARCH_PAGES} (gh --limit)')
    print(f'Detail batch flush every: {DETAIL_BATCH_SIZE}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description='One-time bulk GitHub collection (stars-tier)')
    ap.add_argument('--start', default='2024-01', help='Start month YYYY-MM (default 2024-01)')
    ap.add_argument('--end', default=None, help='End month YYYY-MM (default: current month)')
    ap.add_argument('--resume', action='store_true', help='Resume from checkpoint (default behavior)')
    ap.add_argument('--dry-run', action='store_true', help='Print plan without executing')
    ap.add_argument('--skip-existing', action='store_true',
                    help='Only append brand-new projects; do not refresh existing')
    ap.add_argument('--skip-code-search', action='store_true', help='Skip code search phase')
    ap.add_argument('--skip-seed-topics', action='store_true', help='Skip seed topic expansion')
    ap.add_argument('--max-details', type=int, default=0,
                    help='Optional cap on detail fetches this run (0=unlimited)')
    ap.add_argument('--search-only', action='store_true', help='Only run search phases; skip details')
    ap.add_argument('--details-only', action='store_true',
                    help='Skip searches; refine + fetch details for existing candidates')
    ap.add_argument('--no-readme', action='store_true',
                    help='Skip README fetch during details (faster bulk run)')
    args, _ = ap.parse_known_args()

    end = args.end or default_month_end()
    month_ranges = generate_month_ranges(args.start, end)
    topic_queries = generate_topic_queries()
    keyword_queries = generate_keyword_queries()
    code_queries = generate_code_search_queries()

    # seed topic expansion (lightweight; failures skipped)
    seed_topics = []
    if not args.skip_seed_topics:
        try:
            tools_seed = load_jsonish('data/seed-tools.yaml') or []
            seeds_for_expand = []
            if args.dry_run:
                # don't call API in dry-run; just show intent
                seeds_for_expand = [{'repo': t.get('repo'), 'topics': []} for t in tools_seed if t.get('repo')]
            else:
                for t in tools_seed:
                    repo = t.get('repo')
                    if not repo:
                        continue
                    try:
                        topics = fetch_seed_topics(repo)
                        seeds_for_expand.append({'repo': repo, 'topics': topics})
                    except Exception as e:
                        print(f'  seed topics skip {repo}: {e}')
            bare_existing = [q.replace('topic:', '') for q in topic_queries]
            seed_topics = expand_topics_from_seeds(seeds_for_expand, existing=bare_existing)
            # merge into topic list for L5
            for st in seed_topics:
                if st not in topic_queries:
                    topic_queries.append(st)
        except Exception as e:
            print(f'  seed topic expansion failed (non-fatal): {e}')

    if args.dry_run:
        print_dry_run(month_ranges, topic_queries, keyword_queries, code_queries, seed_topics)
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint = CheckpointManager(CHECKPOINT_FILE)
    tools = load_jsonish('data/seed-tools.yaml') or []

    stats = {
        'search_results': 0,
        'kept': 0,
        'filtered': 0,
        'search_errors': 0,
        'detail_errors': 0,
        'added': 0,
        'updated': 0,
        'skipped_existing': 0,
        'skipped_search': 0,
        'by_tier_kept': {},
    }

    print(f'=== Initial Collection: {args.start} → {end} (created >2024-01-01) ===')
    print(f'Month ranges: {len(month_ranges)} | skip_existing={args.skip_existing}')
    print(f'Checkpoint: {CHECKPOINT_FILE}')

    # Phase: stars tiers L1 → L5b
    all_candidates = load_candidates()  # fullName -> (item, filter_mode, tier)
    if all_candidates:
        print(f'Resumed candidates from disk: {len(all_candidates)}')

    try:
        if not args.details_only:
            for tier in STAR_TIERS:
                print(f"\n--- Tier {tier['id']} stars={tier['stars']} filter={tier['filter_mode']} monthly={tier.get('monthly')} ---")
                jobs = build_tier_search_jobs(
                    tier, month_ranges, topic_queries, keyword_queries, created_lower='2024-01-01'
                )
                print(f"  planned probe/jobs: {len(jobs)}")
                tier_kept = 0
                for job in jobs:
                    items = run_search_job(
                        job, checkpoint, stats,
                        month_ranges=month_ranges,
                        created_lower='2024-01-01',
                    )
                    for it in items:
                        fn = it.get('fullName')
                        if not fn:
                            continue
                        # prefer higher tier (first seen) — L1 first so keep first
                        if fn not in all_candidates:
                            all_candidates[fn] = (it, job['filter_mode'], tier['id'])
                            tier_kept += 1
                    # persist after each job so resume never loses candidates
                    save_candidates(all_candidates)
                stats['by_tier_kept'][tier['id']] = tier_kept
                progress = checkpoint.get_progress()
                print(f"  Tier {tier['id']} done. new_unique={tier_kept} "
                      f"searches_done={progress['total_searches']} candidates={len(all_candidates)}")
                # save progress log
                (OUTPUT_DIR / f"tier-{tier['id']}-progress.json").write_text(
                    json.dumps({
                        'tier': tier['id'],
                        'new_unique': tier_kept,
                        'candidates_total': len(all_candidates),
                        'checkpoint': progress,
                        'timestamp': datetime.datetime.now().isoformat(),
                    }, ensure_ascii=False, indent=2),
                    encoding='utf-8',
                )

            # Phase: code search
            code_repos = set()
            if not args.skip_code_search:
                print('\n--- Code search ---')
                code_repos = collect_code_search(checkpoint, stats)
                for fn in code_repos:
                    if fn not in all_candidates:
                        all_candidates[fn] = (
                            {'fullName': fn, 'description': '', 'stargazersCount': 0},
                            'strict',
                            'code',
                        )
                        save_candidates(all_candidates)
        else:
            print('details-only: skipping search phases')

        # Save candidate list
        cand_file = OUTPUT_DIR / 'unique-repos.json'
        cand_file.write_text(
            json.dumps(sorted(all_candidates.keys()), ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        print(f'\nCandidates unique: {len(all_candidates)} → {cand_file}')
        save_candidates(all_candidates)

        # Refine candidates before expensive detail fetches:
        # L1–L3 keyword-free search is noisy; keep only AI-related NEW repos.
        # Existing projects are always kept so GitHub quant fields can refresh.
        existing_projects = load_jsonish('data/projects.yaml') or []
        _, existing_by_repo = index_projects(existing_projects)
        existing_repos = set(existing_by_repo.keys())

        refined = {}
        dropped = {'L1': 0, 'L2': 0, 'L3': 0, 'L4': 0, 'L5a': 0, 'L5b': 0, 'code': 0, 'other': 0}
        for fn, (item, mode, tier) in all_candidates.items():
            repo_key = (fn or '').lower()
            is_known = repo_key in existing_repos
            if is_known:
                refined[fn] = (item, mode, tier)
                continue
            # New repos: L1–L3 require weak positive (AI signal);
            # L4 requires weak positive AND coding signal; L5/code strict
            # code-search items often lack description until repo_view — keep them
            if tier == 'code':
                keep = True
            elif tier in ('L1', 'L2', 'L3'):
                keep = passes_filter(item, mode='weak_positive')
            elif tier == 'L4':
                keep = passes_filter(item, mode='weak_positive') and has_coding_signal(item)
            else:
                keep = passes_filter(item, mode='strict')
            if keep:
                refined[fn] = (item, mode, tier)
            else:
                dropped[tier if tier in dropped else 'other'] = dropped.get(tier if tier in dropped else 'other', 0) + 1
        print(f'Refined candidates: {len(all_candidates)} → {len(refined)}; dropped_new={dropped}')
        all_candidates = refined
        save_candidates(all_candidates)
        cand_file.write_text(
            json.dumps(sorted(all_candidates.keys()), ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

        if args.search_only:
            print('search-only: skipping details')
            progress = checkpoint.get_progress()
            print(json.dumps({'candidates': len(all_candidates), 'checkpoint': progress}, ensure_ascii=False, indent=2))
            return

        # Phase: details + merge
        print(f'\n--- Fetch details + safe merge ---')
        # Priority order: high-signal tiers first
        tier_rank = {'L1': 0, 'L2': 1, 'L3': 2, 'L5a': 3, 'L5b': 4, 'code': 5, 'L4': 6}

        def _stars(item):
            try:
                return int(item.get('stargazersCount') or item.get('stargazerCount') or item.get('stars') or 0)
            except Exception:
                return 0

        ordered = sorted(
            all_candidates.items(),
            key=lambda kv: (tier_rank.get(kv[1][2], 9), -_stars(kv[1][0]), kv[0]),
        )
        star_names = [fn for fn, (_, mode, t) in ordered if t != 'code']
        code_only = [fn for fn, (_, mode, t) in ordered if t == 'code']

        if args.max_details and args.max_details > 0:
            star_names = star_names[: args.max_details]

        # Prefer richer filter at detail time for star tiers (topics available after repo view)
        stats['detail_filter_mode'] = 'weak_positive'
        fetch_readme_text = not args.no_readme
        detail_and_merge(
            star_names, tools, checkpoint, args.skip_existing, stats,
            label='star-tier', fetch_readme_text=fetch_readme_text,
        )

        if code_only and not args.skip_code_search:
            stats['detail_filter_mode'] = 'strict'
            stats['force_pending'] = True
            detail_and_merge(
                code_only, tools, checkpoint, args.skip_existing, stats,
                label='code-search', fetch_readme_text=fetch_readme_text,
            )

    except RuntimeError as e:
        print(f'\nSTOPPED: {e}')
        print('Checkpoint saved. Re-run the same command to resume.')
        progress = checkpoint.get_progress()
        print(json.dumps({'checkpoint': progress, 'stats': stats}, ensure_ascii=False, indent=2))
        sys.exit(2)

    # Final summary
    final_projects = load_jsonish('data/projects.yaml') or []
    progress = checkpoint.get_progress()
    summary = {
        'start': args.start,
        'end': end,
        'search_operations_completed': progress['total_searches'],
        'total_search_results': progress['total_search_results'],
        'unique_candidates': len(all_candidates),
        'completed_details': progress['completed_details'],
        'stats': {
            k: v for k, v in stats.items()
            if k not in ('detail_filter_mode', 'force_pending')
        },
        'total_projects': len(final_projects),
        'skip_existing': args.skip_existing,
    }
    print('\n=== Summary ===')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    (OUTPUT_DIR / 'run-summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )


if __name__ == '__main__':
    main()

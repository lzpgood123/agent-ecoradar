#!/usr/bin/env python3
"""One-time historical bulk collection of GitHub projects.

Searches GitHub for AI coding agent ecosystem projects from 2025-01 to present.
Uses four search strategies: topic search, keyword search, dependents, code search.
Supports checkpoint/resume for interrupted runs.

Usage:
    python3 scripts/initial_collection.py --start 2025-01 --end 2025-07
    python3 scripts/initial_collection.py --resume  # resume from checkpoint
"""
import argparse
import json
import datetime
from pathlib import Path

from common import ROOT, load_jsonish, save_jsonish, slug, run, today

CHECKPOINT_FILE = ROOT / 'data' / 'initial-collection-checkpoint.json'
OUTPUT_DIR = ROOT / 'data' / 'raw' / 'github-initial'


def generate_topic_queries():
    """Generate GitHub topic search queries."""
    topics = [
        'claude-code', 'cursor-rules', 'mcp-server', 'agent-skills',
        'ai-coding', 'coding-agent', 'agentic-coding',
        'claude-skills', 'cursor-mcp', 'codex-cli',
        'gemini-cli', 'opencode', 'goose-ai',
    ]
    return [f'topic:{t}' for t in topics]


def generate_keyword_queries():
    """Generate keyword search queries."""
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


def generate_dependents_targets():
    """Official repos to fetch dependents for."""
    tools = load_jsonish('data/seed-tools.yaml')
    return [t['repo'] for t in tools if t.get('repo')]


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


class CheckpointManager:
    """Manage checkpoint for resume support."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = self._load()

    def _load(self):
        if self.path.exists():
            return json.loads(self.path.read_text(encoding='utf-8'))
        return {'completed': {}, 'stats': {'total_queries': 0, 'total_results': 0}}

    def save(self, query, month_range, pages, results_count):
        key = f'{query}::{month_range}'
        self.data['completed'][key] = {
            'query': query,
            'month': month_range,
            'pages': pages,
            'results': results_count,
            'timestamp': datetime.datetime.now().isoformat(),
        }
        self.data['stats']['total_queries'] = len(self.data['completed'])
        self.data['stats']['total_results'] += results_count
        self._write()

    def is_done(self, query, month_range):
        key = f'{query}::{month_range}'
        return key in self.data['completed']

    def get_progress(self):
        return {
            'total_queries': len(self.data['completed']),
            'total_results': self.data['stats']['total_results'],
        }

    def _write(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding='utf-8')


def gh_search_repos(query, created_range, sort='stars', limit=100, page=1):
    """Search GitHub repos with date range filter."""
    start, end = created_range
    full_query = f'{query} created:{start}..{end}'
    fields = 'fullName,description,stargazersCount,url,updatedAt,language,forkCount,isArchived'
    cmd = f'gh search repos {json.dumps(full_query)} --sort {sort} --limit {limit} --page {page} --json {fields}'
    r = run(cmd, timeout=180)
    if r.returncode != 0:
        return [], r.stderr
    return json.loads(r.stdout or '[]'), None


def gh_search_code(query, limit=100, page=1):
    """Search GitHub code for config file discovery."""
    cmd = f'gh search code {json.dumps(query)} --limit {limit} --page {page} --json repository,path'
    r = run(cmd, timeout=180)
    if r.returncode != 0:
        return [], r.stderr
    return json.loads(r.stdout or '[]'), None


def collect_topic_and_keyword(queries, month_ranges, checkpoint, outdir):
    """Run topic and keyword searches across all month ranges."""
    all_repos = set()  # use fullName for dedup

    for query in queries:
        for mr in month_ranges:
            mr_key = f'{mr[0]}..{mr[1]}'
            if checkpoint.is_done(query, mr_key):
                continue

            total_results = 0
            for page in range(1, 4):  # max 3 pages
                results, err = gh_search_repos(query, mr, page=page, limit=100)
                if err:
                    print(f'  ERROR: {query} {mr_key} page {page}: {err[:200]}')
                    break
                if not results:
                    break
                total_results += len(results)
                for r in results:
                    fn = r.get('fullName')
                    if fn:
                        all_repos.add(fn)

            checkpoint.save(query, mr_key, min(3, (total_results // 100) + 1), total_results)
            print(f'  {query} [{mr_key}]: {total_results} results')

    return all_repos


def collect_code_search(checkpoint, outdir):
    """Run code searches to find repos with specific config files."""
    queries = generate_code_search_queries()
    all_repos = set()

    for query in queries:
        if checkpoint.is_done(query, 'code-search'):
            continue
        total = 0
        for page in range(1, 4):
            results, err = gh_search_code(query, page=page, limit=100)
            if err or not results:
                break
            total += len(results)
            for r in results:
                repo = r.get('repository', {})
                fn = repo.get('nameWithOwner')
                if fn:
                    all_repos.add(fn)
        checkpoint.save(query, 'code-search', 1, total)
        print(f'  code:{query}: {total} results, {len(all_repos)} unique repos')

    return all_repos


def main():
    ap = argparse.ArgumentParser(description='One-time bulk GitHub collection')
    ap.add_argument('--start', default='2025-01', help='Start month YYYY-MM')
    ap.add_argument('--end', default='2025-07', help='End month YYYY-MM')
    ap.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    ap.add_argument('--dry-run', action='store_true', help='Print queries without executing')
    ap.parse_known_args()

    args, _ = ap.parse_known_args()

    if args.dry_run:
        print('Topic queries:', generate_topic_queries())
        print('Keyword queries:', generate_keyword_queries())
        print('Code search queries:', generate_code_search_queries())
        print('Dependents targets:', generate_dependents_targets())
        print('Month ranges:', generate_month_ranges(args.start, args.end))
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint = CheckpointManager(CHECKPOINT_FILE)
    month_ranges = generate_month_ranges(args.start, args.end)

    print(f'=== Initial Collection: {args.start} to {args.end} ===')
    print(f'Month ranges: {len(month_ranges)}')

    # Phase 1: Topic + Keyword searches
    print('\n--- Phase 1: Topic + Keyword searches ---')
    topic_queries = generate_topic_queries()
    keyword_queries = generate_keyword_queries()
    all_queries = topic_queries + keyword_queries
    print(f'Queries: {len(all_queries)} x {len(month_ranges)} months = {len(all_queries) * len(month_ranges)} search operations')

    repo_set_1 = collect_topic_and_keyword(all_queries, month_ranges, checkpoint, OUTPUT_DIR)

    # Phase 2: Code search
    print('\n--- Phase 2: Code search ---')
    repo_set_2 = collect_code_search(checkpoint, OUTPUT_DIR)

    # Merge all unique repos
    all_repos = repo_set_1 | repo_set_2
    print(f'\n=== Summary ===')
    print(f'Topic/keyword unique repos: {len(repo_set_1)}')
    print(f'Code search unique repos: {len(repo_set_2)}')
    print(f'Total unique repos: {len(all_repos)}')

    # Save repo list for enrichment (repo_view to get full details)
    repo_list_file = OUTPUT_DIR / 'unique-repos.json'
    repo_list_file.write_text(json.dumps(sorted(all_repos), ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Repo list saved to: {repo_list_file}')

    # Phase 3: Fetch details for each repo (this is the slow part)
    print(f'\n--- Phase 3: Fetching details for {len(all_repos)} repos ---')
    details = []
    from normalize import github_record
    tools = load_jsonish('data/seed-tools.yaml')

    for i, fn in enumerate(sorted(all_repos)):
        if (i + 1) % 50 == 0:
            print(f'  Progress: {i+1}/{len(all_repos)}')
        # Use gh repo view to get full details
        fields = 'nameWithOwner,description,url,homepageUrl,stargazerCount,forkCount,licenseInfo,repositoryTopics,primaryLanguage,pushedAt,createdAt,updatedAt,isArchived,latestRelease'
        cmd = f'gh repo view {fn} --json {fields}'
        r = run(cmd, timeout=60)
        if r.returncode != 0:
            continue
        try:
            detail = json.loads(r.stdout or '{}')
            details.append(detail)
        except json.JSONDecodeError:
            continue

    # Save raw details
    details_file = OUTPUT_DIR / 'repo-details.json'
    details_file.write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Details saved: {len(details)} repos')

    # Normalize into projects format
    records = []
    for it in details:
        rec = github_record(it, tools)
        if rec:
            records.append(rec)

    # Merge with existing projects (dedup by URL)
    existing = load_jsonish('data/projects.yaml')
    by_url = {r.get('url') or r['id']: r for r in existing}
    now = today()
    for r in records:
        r['first_seen'] = r.get('first_seen') or now
        r['last_seen'] = now
        by_url[r.get('url') or r['id']] = r

    save_jsonish('data/projects.yaml', list(by_url.values()))

    progress = checkpoint.get_progress()
    print(json.dumps({
        'search_operations_completed': progress['total_queries'],
        'total_search_results': progress['total_results'],
        'unique_repos_found': len(all_repos),
        'details_fetched': len(details),
        'records_normalized': len(records),
        'total_projects': len(by_url),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import argparse, json, re
from common import ROOT, load_jsonish, save_jsonish, slug

# Resource type rules: ordered by priority (earlier = higher priority)
RESOURCE_TYPE_RULES = {
    'mcp-server': ['mcp server', 'model context protocol', 'mcp', 'mcp tool', 'mcp integration'],
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

    # Phase 2: check tutorial (lower priority - only as additional tag)
    if has_any(low, RESOURCE_TYPE_RULES.get('tutorial', [])):
        types.append('tutorial')

    return types or ['tutorial']

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

    # --- License: extract from licenseInfo, handle null/None ---
    license_info = it.get('licenseInfo')
    if isinstance(license_info, dict):
        # gh repo view --json uses 'spdxId' (may be None); gh search uses 'key'
        license_id = license_info.get('spdxId')
        if not license_id:
            license_id = license_info.get('key')
        # GitHub returns "NOASSERTION" when license can't be determined
        license_val = None if license_id in ('NOASSERTION', None, '', 'none') else license_id
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

def main():
    ap = argparse.ArgumentParser(description='Normalize raw collector outputs into data/projects.yaml')
    ap.add_argument('--source', choices=['all', 'github'], default='all')
    ap.parse_known_args()
    existing = load_jsonish('data/projects.yaml') if (ROOT / 'data/projects.yaml').exists() else []
    recs = from_github()
    by = {r.get('url') or r['id']: r for r in existing}
    import datetime
    now = datetime.date.today().isoformat()
    for r in recs:
        r['first_seen'] = r.get('first_seen') or now
        r['last_seen'] = now
        by[r.get('url') or r['id']] = r
    save_jsonish('data/projects.yaml', list(by.values()))
    print(json.dumps({'normalized_new': len(recs), 'total': len(by)}, ensure_ascii=False))

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Auto-finalize Search in Coding data.

No manual review is required. Curated and rejected datasets are generated from
source quality, score, category value, and target-tool coverage rules.
"""
import argparse
import collections
import datetime
import json
from common import load_jsonish, save_jsonish, normalize_project_fields, total_score

CURATED_MIN = 60
REJECTED_MIN = 25
GITHUB_MIN = 40
NON_GITHUB_MIN = 15

HIGH_VALUE_CATEGORIES = {
    'mcp-acp-a2a',
    'skills-prompts',
    'rules-instructions',
    'context-engineering',
    'agent-harness',
    'testing-review-ci',
}

def ensure_official_seed(projects, tools):
    by_id = {p.get('id'): p for p in projects}
    now = datetime.date.today().isoformat()
    for t in tools:
        rid = 'official-' + t['id']
        if rid not in by_id:
            by_id[rid] = {
                'id': rid,
                'name': t['name'],
                'url': t.get('website') or t.get('docs') or (f"https://github.com/{t['repo']}" if t.get('repo') else ''),
                'repo': t.get('repo'),
                'source_type': 'official-seed',
                'category': ['official-tool', t.get('primary_type', 'official-tool')],
                'target_tools': [t['id']],
                'concepts': t.get('related_concepts', []),
                'summary': f"Official seed profile for {t['name']}",
                'why_it_matters': 'Primary target tool for the Search in Coding tracker.',
                'status': 'active',
                'license': None,
                'stars': None,
                'forks': None,
                'last_updated': now,
                'first_seen': now,
                'last_seen': now,
                'maturity': 'unknown',
                'integration_surfaces': t.get('extension_points', []),
                'languages': [],
                'tags': ['target-tool', 'official-seed'],
                'score': {'ecosystem_value': 5, 'activity': 3, 'adoption': 3, 'practicality': 5, 'novelty': 3, 'confidence': 5},
                'notes': '',
                'review_state': 'auto-reviewed',
                'record_kind': 'official-tool',
                'source_quality': 'verified',
                'ranking_scope': 'official',
            }
    return list(by_id.values())

def auto_level(p):
    score = total_score(p)
    source = p.get('source_type')
    cats = set(p.get('category') or [])
    if p.get('ranking_scope') == 'learning-resource':
        return 'reference'
    if source == 'github' and score >= 17 and cats & HIGH_VALUE_CATEGORIES:
        return 'try-now'
    if score >= 15:
        return 'watch'
    if source == 'exa':
        return 'reference'
    return 'watch'

def auto_note(p):
    score = total_score(p)
    source = p.get('source_type')
    cats = ', '.join(p.get('category') or [])
    return f"Auto-selected by scoring rules: source={source}, score={score}, categories={cats}."

def main():
    ap = argparse.ArgumentParser(description='Auto-generate curated/rejected datasets from scoring rules')
    ap.add_argument('--curated-min', type=int, default=CURATED_MIN)
    ap.add_argument('--rejected-min', type=int, default=REJECTED_MIN)
    args = ap.parse_args()

    projects = ensure_official_seed(load_jsonish('data/projects.yaml'), load_jsonish('data/seed-tools.yaml'))
    for p in projects:
        normalize_project_fields(p)
        if p.get('record_kind') == 'official-tool':
            p['review_state'] = 'auto-reviewed'
            p['ranking_scope'] = 'official'
        elif p.get('review_state') == 'reviewed':
            p['review_state'] = 'auto-reviewed'

    candidates = [p for p in projects if p.get('record_kind') != 'official-tool' and p.get('ranking_scope') in ('ecosystem', 'learning-resource')]
    candidates = sorted(candidates, key=total_score, reverse=True)

    curated = []
    seen = set()
    def add_curated(p):
        if p.get('id') in seen:
            return
        q = dict(p)
        q['review_state'] = 'auto-reviewed'
        q['recommendation_level'] = auto_level(q)
        q['curation_note'] = auto_note(q)
        curated.append(q)
        seen.add(q.get('id'))

    # Strong verified GitHub ecosystem records.
    for p in candidates:
        if p.get('source_type') == 'github' and p.get('ranking_scope') == 'ecosystem' and len([x for x in curated if x.get('source_type') == 'github']) < GITHUB_MIN:
            add_curated(p)

    # Verified Exa / non-GitHub resources as reference material.
    for p in candidates:
        if p.get('source_type') != 'github' and len([x for x in curated if x.get('source_type') != 'github']) < NON_GITHUB_MIN:
            add_curated(p)

    # Ensure each target tool has at least a little curated coverage when possible.
    tools = [t['id'] for t in load_jsonish('data/seed-tools.yaml')]
    for tid in tools:
        if any(tid in (p.get('target_tools') or []) for p in curated):
            continue
        for p in candidates:
            if tid in (p.get('target_tools') or []):
                add_curated(p)
                break

    for p in candidates:
        if len(curated) >= args.curated_min:
            break
        add_curated(p)

    curated_ids = {p['id'] for p in curated}
    rejected = []
    for p in sorted(projects, key=total_score):
        if len(rejected) >= args.rejected_min:
            break
        if p.get('record_kind') == 'official-tool' or p.get('id') in curated_ids:
            continue
        weak = (
            total_score(p) <= 9 or
            p.get('source_type') == 'fallback-web' or
            p.get('target_tools') == ['general-ai-coding'] or
            p.get('source_quality') in ('fallback', 'unverified')
        )
        if weak:
            q = dict(p)
            q['review_state'] = 'auto-rejected'
            q['ranking_scope'] = 'excluded'
            q['rejection_reason'] = 'Auto-rejected by scoring/source-quality rules: low confidence, fallback/noisy, generic, duplicate, or weak direct relevance.'
            rejected.append(q)

    rejected_ids = {p['id'] for p in rejected}
    for p in projects:
        if p['id'] in curated_ids:
            p['review_state'] = 'auto-reviewed'
        elif p['id'] in rejected_ids:
            p['review_state'] = 'auto-rejected'
            p['ranking_scope'] = 'excluded'

    save_jsonish('data/projects.yaml', projects)
    save_jsonish('data/curated-projects.yaml', curated)
    save_jsonish('data/rejected-projects.yaml', rejected)
    print(json.dumps({
        'mode': 'auto-scored',
        'projects': len(projects),
        'curated': len(curated),
        'rejected': len(rejected),
        'curated_github': sum(1 for p in curated if p.get('source_type') == 'github'),
        'curated_non_github': sum(1 for p in curated if p.get('source_type') != 'github'),
    }, ensure_ascii=False))

if __name__ == '__main__':
    main()

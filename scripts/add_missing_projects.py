#!/usr/bin/env python3
"""Manually add missing well-known projects to data/projects.yaml.

Uses `gh repo view` to fetch repo details, then normalizes via
normalize.github_record() and merges into projects.yaml (dedup by URL).
README is fetched separately via gh api (gh repo view --json does not
support a 'readme' field).
"""
import argparse
import base64
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
    """Fetch repo details via gh repo view (no readme -- not supported)."""
    fields = (
        'nameWithOwner,description,url,homepageUrl,'
        'stargazerCount,forkCount,licenseInfo,repositoryTopics,'
        'primaryLanguage,pushedAt,createdAt,updatedAt,isArchived,'
        'latestRelease'
    )
    cmd = f'gh repo view {full_name} --json {fields}'
    r = run(cmd, timeout=120)
    if r.returncode != 0:
        print(f'  WARNING: failed to fetch {full_name}: {r.stderr.strip()}', file=sys.stderr)
        return None
    return json.loads(r.stdout or '{}')


def fetch_readme(full_name):
    """Fetch README via gh api and decode from base64."""
    cmd = f'gh api repos/{full_name}/readme --jq .content'
    r = run(cmd, timeout=60)
    if r.returncode != 0:
        return ''
    try:
        raw = r.stdout.strip()
        return base64.b64decode(raw).decode('utf-8', errors='replace')
    except Exception:
        return ''


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

        # Fetch README separately (gh repo view --json doesn't support 'readme')
        readme = fetch_readme(repo_full)
        details['readme'] = readme

        rec = github_record(details, tools)
        if not rec:
            print(f'  SKIP: {repo_full} produced null record')
            skipped.append(repo_full)
            continue

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

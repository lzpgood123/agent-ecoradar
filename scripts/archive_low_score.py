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

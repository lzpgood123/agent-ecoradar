#!/usr/bin/env python3
"""Score projects with the new 100-point system.

Quantifiable score (60 points): Stars + Activity + Adoption + Maturity
Quality score (40 points): Preserved from weekly LLM analysis (0 if not yet analyzed)
Total = Quantifiable + Quality
"""
import argparse
import datetime
import json

from common import load_jsonish, save_jsonish
from migrate_data import calc_quantifiable_score


def score_detail_for(p):
    """Return detailed breakdown of the quantifiable score."""
    stars = p.get('stars') or 0
    try:
        stars = int(stars)
    except (TypeError, ValueError):
        stars = 0

    if stars >= 50000:
        stars_s = 20
    elif stars >= 10000:
        stars_s = 16
    elif stars >= 5000:
        stars_s = 12
    elif stars >= 1000:
        stars_s = 8
    elif stars >= 100:
        stars_s = 4
    elif stars > 0:
        stars_s = 2
    else:
        stars_s = 0

    last_updated = p.get('last_updated') or p.get('last_seen') or ''
    activity_s = 1
    if last_updated:
        try:
            d = datetime.date.fromisoformat(last_updated[:10])
            days = (datetime.date.today() - d).days
            if days <= 90:
                activity_s = 15
            elif days <= 180:
                activity_s = 12
            elif days <= 365:
                activity_s = 8
            elif days <= 730:
                activity_s = 4
        except (ValueError, TypeError):
            pass

    forks = p.get('forks') or 0
    try:
        forks = int(forks)
    except (TypeError, ValueError):
        forks = 0
    if forks >= 1000:
        adoption_s = 10
    elif forks >= 100:
        adoption_s = 7
    elif forks >= 10:
        adoption_s = 4
    elif forks > 0:
        adoption_s = 2
    else:
        adoption_s = 0

    maturity_s = 0
    if p.get('license'):
        maturity_s += 2
    if p.get('status') and p.get('status') not in ('unknown',):
        maturity_s += 3
    if p.get('languages'):
        maturity_s += 2
    if p.get('tags'):
        for tag in (p.get('tags') or []):
            if 'release' in tag.lower() or 'v1' in tag.lower() or 'stable' in tag.lower():
                maturity_s += 3
                break
    if p.get('maturity') and p.get('maturity') not in ('unknown',):
        maturity_s += 5
    maturity_s = min(maturity_s, 15)

    return {
        'stars': stars_s,
        'activity': activity_s,
        'adoption': adoption_s,
        'maturity': maturity_s,
    }


def main():
    ap = argparse.ArgumentParser(description='Score projects with 100-point system (quantifiable only)')
    ap.parse_known_args()

    projects = load_jsonish('data/projects.yaml')

    for p in projects:
        # Calculate quantifiable score
        detail = score_detail_for(p)
        q_score = sum(detail.values())
        p['quantifiable_score'] = q_score
        p['score_detail'] = detail

        # Preserve existing quality_score or default to 0
        if 'quality_score' not in p:
            p['quality_score'] = 0

        # Total = quantifiable + quality
        p['total_score'] = q_score + p['quality_score']

    save_jsonish('data/projects.yaml', projects)

    stats = {
        'scored': len(projects),
        'avg_score': round(sum(p.get('total_score', 0) for p in projects) / max(len(projects), 1), 1),
        'max_score': max((p.get('total_score', 0) for p in projects), default=0),
        'min_score': min((p.get('total_score', 0) for p in projects), default=0),
    }
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == '__main__':
    main()

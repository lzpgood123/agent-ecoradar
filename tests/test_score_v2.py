"""Test the new 100-point scoring system (quantifiable part only)."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from migrate_data import calc_quantifiable_score


class TestStarsScore:
    def test_50k_stars(self):
        p = {'stars': 50000}
        score = calc_quantifiable_score(p)
        # stars component should be 20, plus default activity=1, maturity varies
        assert score >= 20

    def test_10k_stars(self):
        p = {'stars': 10000}
        score = calc_quantifiable_score(p)
        assert score >= 16

    def test_1k_stars(self):
        p = {'stars': 1000}
        score = calc_quantifiable_score(p)
        assert score >= 8

    def test_0_stars(self):
        p = {'stars': 0}
        score = calc_quantifiable_score(p)
        # stars=0, activity=1 (default), adoption=0, maturity=0
        assert score >= 1  # at least default activity

    def test_none_stars(self):
        p = {'stars': None}
        score = calc_quantifiable_score(p)
        assert score >= 1


import datetime


class TestActivityScore:
    def test_recent_project(self):
        # Use a date within the last 90 days
        recent = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        p = {'stars': 0, 'last_updated': recent}
        score = calc_quantifiable_score(p)
        # activity=15 for <90 days
        assert score >= 15

    def test_old_project(self):
        p = {'stars': 0, 'last_updated': '2024-01-01T00:00:00Z'}
        score = calc_quantifiable_score(p)
        # activity=1 for >2 years
        assert score <= 3  # activity=1 + minimal others


class TestAdoptionScore:
    def test_high_forks(self):
        p = {'stars': 0, 'forks': 1000}
        score = calc_quantifiable_score(p)
        assert score >= 10  # adoption=10

    def test_no_forks(self):
        p = {'stars': 0, 'forks': 0}
        score = calc_quantifiable_score(p)
        assert score >= 1  # just default activity


class TestTotalScoreRange:
    def test_max_score(self):
        recent = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        p = {
            'stars': 50000,
            'forks': 1000,
            'last_updated': recent,
            'license': 'MIT',
            'maturity': 'stable',
            'languages': ['Python'],
            'status': 'active',
        }
        score = calc_quantifiable_score(p)
        assert score <= 60
        assert score >= 40  # should be high

    def test_min_score(self):
        p = {'stars': 0, 'forks': 0}
        score = calc_quantifiable_score(p)
        assert score >= 1  # at least default activity
        assert score <= 5

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

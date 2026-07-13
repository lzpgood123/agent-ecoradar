"""Test the rewritten score.py main function."""
import pytest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class TestScoreV2Main:
    def test_scores_all_projects(self, tmp_path, monkeypatch):
        """score.py should process all projects and update quantifiable_score."""
        import score

        # Create a minimal test projects.yaml
        test_projects = [
            {
                'id': 'test-1',
                'name': 'Test Project',
                'source_type': 'github',
                'stars': 1000,
                'forks': 50,
                'last_updated': '2025-07-01T00:00:00Z',
                'target_tools': ['claude-code'],
                'resource_type': ['mcp-server'],
                'tracking_priority': 'pending',
                'license': 'MIT',
            },
        ]

        # Mock load_jsonish to return our test data
        def mock_load(rel):
            if rel == 'data/projects.yaml':
                return test_projects
            if rel == 'config/scoring-v2.yaml':
                return {}
            return []

        def mock_save(rel, data):
            pass

        monkeypatch.setattr(score, 'load_jsonish', mock_load)
        monkeypatch.setattr(score, 'save_jsonish', mock_save)

        score.main()

        p = test_projects[0]
        assert 'quantifiable_score' in p
        assert p['quantifiable_score'] > 0
        assert p['quantifiable_score'] <= 60
        assert p['total_score'] == p['quantifiable_score']  # quality_score = 0
        assert 'score_detail' in p

    def test_updates_existing_quality_score(self, tmp_path, monkeypatch):
        """If a project already has quality_score from LLM, preserve it."""
        import score

        test_projects = [
            {
                'id': 'test-1',
                'name': 'Test',
                'source_type': 'github',
                'stars': 500,
                'forks': 10,
                'last_updated': '2025-07-01T00:00:00Z',
                'target_tools': ['claude-code'],
                'resource_type': ['skills'],
                'tracking_priority': 'track',
                'quality_score': 30,  # pre-existing from LLM
            },
        ]

        def mock_load(rel):
            if rel == 'data/projects.yaml':
                return test_projects
            return []

        def mock_save(rel, data):
            pass

        monkeypatch.setattr(score, 'load_jsonish', mock_load)
        monkeypatch.setattr(score, 'save_jsonish', mock_save)

        score.main()

        p = test_projects[0]
        assert p['quality_score'] == 30  # preserved
        assert p['total_score'] == p['quantifiable_score'] + 30

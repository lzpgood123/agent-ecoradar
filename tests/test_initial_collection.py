"""Test the initial bulk collection script."""
import pytest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class TestQueryGeneration:
    def test_generates_topic_queries(self):
        from initial_collection import generate_topic_queries
        queries = generate_topic_queries()
        assert len(queries) > 0
        # Should include tool-specific topics
        assert any('claude-code' in q for q in queries)
        assert any('mcp-server' in q for q in queries)

    def test_generates_keyword_queries(self):
        from initial_collection import generate_keyword_queries
        queries = generate_keyword_queries()
        assert len(queries) > 0
        assert any('claude code' in q for q in queries)

    def test_generates_code_search_queries(self):
        from initial_collection import generate_code_search_queries
        queries = generate_code_search_queries()
        assert len(queries) > 0
        assert any('CLAUDE.md' in q for q in queries)

    def test_month_ranges(self):
        from initial_collection import generate_month_ranges
        ranges = generate_month_ranges('2025-01', '2025-07')
        assert len(ranges) == 7  # Jan to Jul
        assert ranges[0] == ('2025-01-01', '2025-01-31')
        assert ranges[-1] == ('2025-07-01', '2025-07-31')


class TestCheckpointManager:
    def test_save_and_load_checkpoint(self, tmp_path):
        from initial_collection import CheckpointManager
        ckpt = CheckpointManager(tmp_path / 'checkpoint.json')
        ckpt.save('topic:claude-code', '2025-01', 2, 50)
        assert ckpt.is_done('topic:claude-code', '2025-01')
        assert not ckpt.is_done('topic:claude-code', '2025-02')

    def test_get_progress(self, tmp_path):
        from initial_collection import CheckpointManager
        ckpt = CheckpointManager(tmp_path / 'checkpoint.json')
        ckpt.save('q1', '2025-01', 1, 30)
        ckpt.save('q2', '2025-01', 1, 20)
        progress = ckpt.get_progress()
        assert progress['total_queries'] == 2
        assert progress['total_results'] == 50

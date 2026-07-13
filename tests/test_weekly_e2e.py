"""End-to-end test for weekly analysis pipeline (with mocked LLM)."""
import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class TestWeeklyE2E:
    """Test the full pipeline with mocked LLM calls."""

    @pytest.fixture
    def mock_projects(self):
        return [
            {
                'id': 'test-1', 'name': 'Test MCP Server', 'url': 'https://github.com/test/mcp-server',
                'source_type': 'github', 'stars': 500, 'forks': 20, 'status': 'active',
                'summary': 'A Claude Code MCP server for code indexing',
                'target_tools': ['claude-code'], 'resource_type': ['mcp-server'],
                'quantifiable_score': 15, 'quality_score': 0, 'total_score': 15,
                'tracking_priority': 'pending', 'last_analyzed': None,
                'languages': ['Python'], 'license': 'MIT', 'last_updated': '2025-07-01',
                'review_state': 'auto-indexed', 'i18n': {'zh': {'name': 'Test', 'summary': 'test'}, 'en': {'name': 'Test', 'summary': 'test'}},
            },
            {
                'id': 'test-2', 'name': 'Cursor Rules Pack', 'url': 'https://github.com/test/cursor-rules',
                'source_type': 'github', 'stars': 200, 'forks': 10, 'status': 'active',
                'summary': 'Collection of cursor rules for various frameworks',
                'target_tools': ['cursor'], 'resource_type': ['rules'],
                'quantifiable_score': 10, 'quality_score': 0, 'total_score': 10,
                'tracking_priority': 'pending', 'last_analyzed': None,
                'languages': ['TypeScript'], 'license': None, 'last_updated': '2025-06-01',
                'review_state': 'auto-indexed', 'i18n': {'zh': {'name': 'Test2', 'summary': 'test2'}, 'en': {'name': 'Test2', 'summary': 'test2'}},
            },
        ]

    def test_full_pipeline_with_mock(self, mock_projects, tmp_path, monkeypatch):
        """Test pipeline: pre-filter -> analyze -> rescore -> save."""
        from weekly_analysis import pre_filter, merge_analysis_result, rescore_all

        # Mock LLM response
        mock_analysis = {
            'relevance_score': 0.9,
            'resource_type': ['mcp-server'],
            'target_tools': ['claude-code'],
            'tracking_priority': 'track',
            'quality_score': 30,
            'quality_detail': {'relevance': 8, 'practicality': 8, 'novelty': 7, 'ecosystem_value': 7},
            'llm_summary': {'zh': '优秀的MCP服务器', 'en': 'Excellent MCP server'},
            'analysis_notes': 'Active development, good docs',
        }

        # Step 1: pre-filter
        filtered = pre_filter(mock_projects)
        assert len(filtered) == 2  # both active

        # Step 2: merge analysis
        analyzed = [merge_analysis_result(p, mock_analysis) for p in filtered]
        assert analyzed[0]['quality_score'] == 30
        assert analyzed[0]['total_score'] == 15 + 30  # quantifiable + quality
        assert analyzed[0]['tracking_priority'] == 'track'
        assert analyzed[0]['last_analyzed'] is not None
        assert analyzed[0]['llm_summary']['zh'] == '优秀的MCP服务器'
        assert analyzed[0]['llm_summary']['en'] == 'Excellent MCP server'

        # Step 3: rescore
        rescored = rescore_all(analyzed)
        for p in rescored:
            assert p['total_score'] == p['quantifiable_score'] + p['quality_score']

    def test_pipeline_with_none_analysis(self, mock_projects):
        """Test that None analysis results don't break the pipeline."""
        from weekly_analysis import pre_filter, merge_analysis_result, rescore_all

        filtered = pre_filter(mock_projects)

        # Simulate failed LLM analysis (None result)
        analyzed = [merge_analysis_result(p, None) for p in filtered]
        # Original scores should be preserved
        assert analyzed[0]['quality_score'] == 0
        assert analyzed[0]['total_score'] == 15  # unchanged

        rescored = rescore_all(analyzed)
        assert all(p['total_score'] == p['quantifiable_score'] + p.get('quality_score', 0) for p in rescored)

    def test_benchmark_update_and_rescore(self, mock_projects, tmp_path):
        """Test benchmark update flow with mock LLM."""
        from benchmark_manager import BenchmarkManager
        from weekly_analysis import rescore_all

        # Set up benchmarks in temp file
        bm = BenchmarkManager(tmp_path / 'benchmarks.yaml')

        # Simulate LLM-selected benchmarks
        llm_result = {
            'benchmarks': {
                '标杆': {'project_id': 'test-1', 'reason': 'Top project'},
                '优秀': {'project_id': 'test-2', 'reason': 'Good project'},
            }
        }
        bm.update_from_llm(llm_result, mock_projects)

        # Verify benchmarks saved
        loaded = bm.load()
        assert loaded['标杆']['project_id'] == 'test-1'
        assert loaded['优秀']['project_id'] == 'test-2'

    def test_snapshot_generation(self, mock_projects, tmp_path):
        """Test snapshot file generation."""
        from weekly_analysis import save_snapshot

        # Mock ROOT to use tmp_path
        import weekly_analysis
        original_root = weekly_analysis.ROOT
        weekly_analysis.ROOT = tmp_path
        try:
            save_snapshot(mock_projects)
            snapshot_path = tmp_path / 'data' / 'snapshots' / f'{__import__("datetime").date.today().isoformat()}.json'
            assert snapshot_path.exists()
            import json
            snapshot = json.loads(snapshot_path.read_text())
            assert snapshot['total_projects'] == 2
            assert snapshot['analyzed_count'] == 0  # quality_score is 0
        finally:
            weekly_analysis.ROOT = original_root

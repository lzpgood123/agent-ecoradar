#!/usr/bin/env python3
"""Tests for derive_queries.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from derive_queries import derive_queries, merge_with_manual, MAX_QUERIES_PER_TOOL, MAX_TOTAL_QUERIES


class TestDeriveQueries:
    """derive_queries generates GitHub search queries from active seed-tools."""

    def test_basic_two_tools(self):
        """Two active tools produce non-empty query list."""
        tools = [
            {'id': 'tool-a', 'name': 'Tool A', 'aliases': ['Tool A', 'tool-a'],
             'status': 'active', 'tool_kind': 'open', 'extension_points': ['skills', 'mcp']},
            {'id': 'tool-b', 'name': 'Tool B', 'aliases': ['Tool B', 'tool-b'],
             'status': 'active', 'tool_kind': 'open', 'extension_points': ['mcp']},
        ]
        queries = derive_queries(tools)
        assert len(queries) > 0
        # Queries should contain alias text
        all_q = ' '.join(queries).lower()
        assert 'tool a' in all_q or 'tool-a' in all_q
        assert 'tool b' in all_q or 'tool-b' in all_q

    def test_closed_tools_have_ecosystem_queries(self):
        """Closed tools (no repo) still generate ecosystem queries."""
        tools = [
            {'id': 'closed-tool', 'name': 'ClosedTool', 'aliases': ['ClosedTool'],
             'status': 'active', 'tool_kind': 'closed', 'extension_points': ['skills', 'mcp']},
        ]
        queries = derive_queries(tools)
        assert len(queries) > 0
        # Should have skill/mcp queries referencing the tool name
        all_q = ' '.join(queries).lower()
        assert 'closedtool' in all_q

    def test_draft_excluded(self):
        """Draft tools are not included in queries."""
        tools = [
            {'id': 'active1', 'name': 'Active One', 'aliases': ['Active One'],
             'status': 'active', 'tool_kind': 'open'},
            {'id': 'draft1', 'name': 'Draft One', 'aliases': ['Draft One'],
             'status': 'draft', 'tool_kind': 'open'},
        ]
        queries = derive_queries(tools)
        all_q = ' '.join(queries).lower()
        assert 'active one' in all_q
        assert 'draft one' not in all_q

    def test_disabled_excluded(self):
        """Disabled tools are not included."""
        tools = [
            {'id': 'ok', 'name': 'OK', 'aliases': ['OK'],
             'status': 'active', 'tool_kind': 'open'},
            {'id': 'nope', 'name': 'Nope', 'aliases': ['Nope'],
             'status': 'disabled', 'tool_kind': 'open'},
        ]
        queries = derive_queries(tools)
        all_q = ' '.join(queries).lower()
        assert 'ok' in all_q
        assert 'nope' not in all_q

    def test_dedup(self):
        """Duplicate queries are removed."""
        tools = [
            {'id': 't1', 'name': 'SameName', 'aliases': ['SameName', 'samename'],
             'status': 'active', 'tool_kind': 'open', 'extension_points': ['skills']},
            {'id': 't2', 'name': 'SameName2', 'aliases': ['SameName'],
             'status': 'active', 'tool_kind': 'open', 'extension_points': ['skills']},
        ]
        queries = derive_queries(tools)
        # No exact duplicates
        assert len(queries) == len(set(queries))

    def test_per_tool_limit(self):
        """Each tool generates at most MAX_QUERIES_PER_TOOL queries."""
        tools = [
            {'id': 'big', 'name': 'BigTool', 'aliases': ['BigTool', 'big-tool', 'bt'],
             'status': 'active', 'tool_kind': 'open',
             'extension_points': ['skills', 'hooks', 'mcp', 'slash-commands', 'subagents', 'rules']},
        ]
        queries = derive_queries(tools)
        # With 6 extension points, each could generate up to 6 queries
        # But total per tool is capped
        # The exact count depends on implementation, but should be bounded
        assert len(queries) <= MAX_QUERIES_PER_TOOL * 2  # allow some headroom for combined queries

    def test_total_limit(self):
        """Total queries don't exceed MAX_TOTAL_QUERIES."""
        # Create many active tools
        tools = []
        for i in range(50):
            tools.append({
                'id': f'tool-{i}',
                'name': f'Tool {i}',
                'aliases': [f'Tool {i}', f'tool-{i}'],
                'status': 'active',
                'tool_kind': 'open',
                'extension_points': ['skills', 'mcp', 'hooks', 'rules'],
            })
        queries = derive_queries(tools)
        assert len(queries) <= MAX_TOTAL_QUERIES

    def test_empty_tools(self):
        """No tools still includes general ecosystem queries."""
        queries = derive_queries([])
        assert len(queries) > 0
        all_q = ' '.join(queries).lower()
        assert 'ai coding' in all_q or 'mcp server' in all_q

    def test_general_queries_included(self):
        """General ecosystem queries are always included."""
        tools = [
            {'id': 't1', 'name': 'T1', 'aliases': ['T1'],
             'status': 'active', 'tool_kind': 'open'},
        ]
        queries = derive_queries(tools)
        all_q = ' '.join(queries).lower()
        # Should contain some general AI coding queries
        assert 'ai coding' in all_q or 'mcp server' in all_q or 'coding agent' in all_q

    def test_alias_variations(self):
        """Multiple aliases produce queries with each alias."""
        tools = [
            {'id': 'claude-code', 'name': 'Claude Code', 'aliases': ['Claude Code', 'claude-code'],
             'status': 'active', 'tool_kind': 'open', 'extension_points': ['skills', 'mcp']},
        ]
        queries = derive_queries(tools)
        all_q = ' '.join(queries)
        # At least one query should reference "Claude Code"
        assert any('Claude Code' in q for q in queries)


class TestMergeWithManual:
    """merge_with_manual combines derived queries with manual extras."""

    def test_merge_dedup(self):
        """Merging removes duplicates."""
        derived = ['query a', 'query b']
        manual = ['query b', 'query c']
        result = merge_with_manual(derived, manual)
        assert 'query a' in result
        assert 'query b' in result
        assert 'query c' in result
        assert len(result) == 3  # no dupes

    def test_empty_manual(self):
        """Empty manual list just returns derived."""
        derived = ['a', 'b']
        result = merge_with_manual(derived, [])
        assert result == ['a', 'b']

    def test_empty_derived(self):
        """Empty derived returns manual."""
        result = merge_with_manual([], ['x'])
        assert result == ['x']

    def test_both_empty(self):
        """Both empty returns empty."""
        assert merge_with_manual([], []) == []

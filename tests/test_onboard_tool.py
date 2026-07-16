#!/usr/bin/env python3
"""Tests for onboard_tool.py"""
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

import onboard_tool


class TestOnboardStateMachine:
    """onboard_tool state machine transitions."""

    def test_dry_run_does_not_change_seed_tools(self, tmp_path):
        """dry-run should not modify seed-tools onboard_state."""
        seed_tools = [
            {'id': 'test-tool', 'name': 'Test', 'aliases': ['Test'],
             'status': 'active', 'tool_kind': 'open', 'onboard_state': 'pending',
             'repo': 'test/repo', 'extension_points': ['skills']},
        ]
        # Mock load/save to use tmp_path
        seed_path = tmp_path / 'seed-tools.yaml'
        import yaml
        seed_path.write_text(yaml.dump(seed_path if False else seed_tools, allow_unicode=True))

        with patch.object(onboard_tool, 'load_seed_tools', return_value=seed_tools), \
             patch.object(onboard_tool, 'save_seed_tools') as mock_save:
            result = onboard_tool.onboard_single('test-tool', dry_run=True)
            # Should NOT save
            assert mock_save.call_count == 0
            # Tool should still be pending
            assert result['state'] == 'dry_run'

    def test_pending_to_running_to_done(self, tmp_path):
        """Normal flow: pending -> running -> done."""
        seed_tools = [
            {'id': 'test-tool', 'name': 'Test', 'aliases': ['Test'],
             'status': 'active', 'tool_kind': 'open', 'onboard_state': 'pending',
             'repo': 'test/repo', 'extension_points': ['skills']},
        ]

        saved_states = []

        def mock_save(tools):
            saved_states.append([dict(t) for t in tools])

        with patch.object(onboard_tool, 'load_seed_tools', return_value=seed_tools), \
             patch.object(onboard_tool, 'save_seed_tools', side_effect=mock_save), \
             patch.object(onboard_tool, 'run_pipeline', return_value={'ok': True, 'steps': []}):
            result = onboard_tool.onboard_single('test-tool', dry_run=False)

        assert result['state'] == 'done'
        # save_seed_tools should have been called with running then done
        assert len(saved_states) >= 2
        # First save should have running
        assert saved_states[0][0]['onboard_state'] == 'running'
        # Last save should have done
        assert saved_states[-1][0]['onboard_state'] == 'done'

    def test_failure_sets_failed(self, tmp_path):
        """Pipeline failure sets onboard_state=failed with error."""
        seed_tools = [
            {'id': 'fail-tool', 'name': 'Fail', 'aliases': ['Fail'],
             'status': 'active', 'tool_kind': 'open', 'onboard_state': 'pending',
             'repo': 'fail/repo'},
        ]

        with patch.object(onboard_tool, 'load_seed_tools', return_value=seed_tools), \
             patch.object(onboard_tool, 'save_seed_tools') as mock_save, \
             patch.object(onboard_tool, 'run_pipeline', side_effect=RuntimeError('API timeout')):
            result = onboard_tool.onboard_single('fail-tool', dry_run=False)

        assert result['state'] == 'failed'
        assert 'API timeout' in result.get('error', '')
        # Last save should have failed state
        last_call_args = mock_save.call_args[0][0]
        assert last_call_args[0]['onboard_state'] == 'failed'
        assert 'API timeout' in last_call_args[0].get('onboard_error', '')

    def test_tool_not_found(self):
        """Nonexistent tool id -> error."""
        with patch.object(onboard_tool, 'load_seed_tools', return_value=[]):
            result = onboard_tool.onboard_single('nonexistent', dry_run=True)
        assert result['state'] == 'error'
        assert 'not found' in result.get('error', '').lower()

    def test_not_active_skipped(self):
        """Draft tool is skipped."""
        seed_tools = [
            {'id': 'draft1', 'name': 'Draft', 'aliases': ['Draft'],
             'status': 'draft', 'onboard_state': 'pending'},
        ]
        with patch.object(onboard_tool, 'load_seed_tools', return_value=seed_tools):
            result = onboard_tool.onboard_single('draft1', dry_run=True)
        assert result['state'] == 'skipped'
        assert 'not active' in result.get('reason', '').lower()

    def test_already_done_skipped(self):
        """Already-done tool is skipped (unless --force)."""
        seed_tools = [
            {'id': 'done1', 'name': 'Done', 'aliases': ['Done'],
             'status': 'active', 'onboard_state': 'done'},
        ]
        with patch.object(onboard_tool, 'load_seed_tools', return_value=seed_tools):
            result = onboard_tool.onboard_single('done1', dry_run=True)
        assert result['state'] == 'skipped'
        assert 'done' in result.get('reason', '').lower()


class TestOnboardAllPending:
    """onboard_all_pending batch processing."""

    def test_processes_all_pending(self):
        """All pending tools are processed in order."""
        tools = [
            {'id': 't1', 'name': 'T1', 'aliases': ['T1'], 'status': 'active',
             'onboard_state': 'pending', 'repo': 't1/repo'},
            {'id': 't2', 'name': 'T2', 'aliases': ['T2'], 'status': 'active',
             'onboard_state': 'pending', 'repo': 't2/repo'},
            {'id': 't3', 'name': 'T3', 'aliases': ['T3'], 'status': 'active',
             'onboard_state': 'done', 'repo': 't3/repo'},
        ]

        with patch.object(onboard_tool, 'load_seed_tools', return_value=tools), \
             patch.object(onboard_tool, 'save_seed_tools') as mock_save, \
             patch.object(onboard_tool, 'run_pipeline', return_value={'ok': True, 'steps': []}):
            results = onboard_tool.onboard_all_pending(dry_run=False)

        # Only t1 and t2 should be processed
        assert len(results) == 2
        assert results[0]['tool_id'] == 't1'
        assert results[1]['tool_id'] == 't2'
        assert all(r['state'] == 'done' for r in results)

    def test_single_failure_continues(self):
        """One tool failure doesn't stop the batch."""
        tools = [
            {'id': 'ok', 'name': 'OK', 'aliases': ['OK'], 'status': 'active',
             'onboard_state': 'pending', 'repo': 'ok/repo'},
            {'id': 'bad', 'name': 'Bad', 'aliases': ['Bad'], 'status': 'active',
             'onboard_state': 'pending', 'repo': 'bad/repo'},
            {'id': 'ok2', 'name': 'OK2', 'aliases': ['OK2'], 'status': 'active',
             'onboard_state': 'pending', 'repo': 'ok2/repo'},
        ]

        def mock_pipeline(tool, **kwargs):
            if isinstance(tool, dict) and tool.get('id') == 'bad':
                raise RuntimeError('Simulated failure')
            return {'ok': True, 'steps': []}

        with patch.object(onboard_tool, 'load_seed_tools', return_value=tools), \
             patch.object(onboard_tool, 'save_seed_tools'), \
             patch.object(onboard_tool, 'run_pipeline', side_effect=mock_pipeline):
            results = onboard_tool.onboard_all_pending(dry_run=False)

        assert len(results) == 3
        states = [r['state'] for r in results]
        assert 'done' in states
        assert 'failed' in states
        assert states.count('done') == 2
        assert states.count('failed') == 1

    def test_dry_run_no_changes(self):
        """Dry run doesn't modify anything."""
        tools = [
            {'id': 't1', 'name': 'T1', 'aliases': ['T1'], 'status': 'active',
             'onboard_state': 'pending', 'repo': 't1/repo'},
        ]
        with patch.object(onboard_tool, 'load_seed_tools', return_value=tools), \
             patch.object(onboard_tool, 'save_seed_tools') as mock_save:
            results = onboard_tool.onboard_all_pending(dry_run=True)

        assert len(results) == 1
        assert results[0]['state'] == 'dry_run'
        assert mock_save.call_count == 0

    def test_no_pending(self):
        """No pending tools -> empty results."""
        tools = [
            {'id': 'done1', 'name': 'D1', 'aliases': ['D1'], 'status': 'active',
             'onboard_state': 'done'},
        ]
        with patch.object(onboard_tool, 'load_seed_tools', return_value=tools):
            results = onboard_tool.onboard_all_pending(dry_run=False)
        assert results == []

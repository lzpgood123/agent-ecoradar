#!/usr/bin/env python3
"""Tests for detect_seed_tools_diff.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from detect_seed_tools_diff import detect_pending_onboard, update_snapshot, load_snapshot


class TestDetectPendingOnboard:
    """detect_pending_onboard finds tools that need onboarding."""

    def test_new_active_tool_is_pending(self):
        """Tool in seed-tools but not in snapshot -> pending."""
        tools = [
            {'id': 'existing', 'name': 'Existing', 'aliases': ['Existing'],
             'status': 'active', 'onboard_state': 'done'},
            {'id': 'new-tool', 'name': 'New', 'aliases': ['New'],
             'status': 'active', 'onboard_state': 'pending'},
        ]
        snapshot = {'active_ids': ['existing']}
        pending = detect_pending_onboard(tools, snapshot)
        assert 'new-tool' in pending
        assert 'existing' not in pending

    def test_done_tool_not_pending(self):
        """Tool with onboard_state=done is not pending even if not in snapshot."""
        tools = [
            {'id': 'done-tool', 'name': 'Done', 'aliases': ['Done'],
             'status': 'active', 'onboard_state': 'done'},
        ]
        snapshot = {'active_ids': []}
        pending = detect_pending_onboard(tools, snapshot)
        assert 'done-tool' not in pending

    def test_failed_tool_is_pending(self):
        """Tool with onboard_state=failed -> needs retry -> pending."""
        tools = [
            {'id': 'failed-tool', 'name': 'Failed', 'aliases': ['Failed'],
             'status': 'active', 'onboard_state': 'failed'},
        ]
        snapshot = {'active_ids': ['failed-tool']}
        pending = detect_pending_onboard(tools, snapshot)
        assert 'failed-tool' in pending

    def test_draft_not_pending(self):
        """Draft tools are not pending (not active)."""
        tools = [
            {'id': 'draft1', 'name': 'Draft', 'aliases': ['Draft'],
             'status': 'draft', 'onboard_state': 'pending'},
        ]
        snapshot = {'active_ids': []}
        pending = detect_pending_onboard(tools, snapshot)
        assert 'draft1' not in pending

    def test_disabled_not_pending(self):
        """Disabled tools are not pending."""
        tools = [
            {'id': 'dis1', 'name': 'Dis', 'aliases': ['Dis'],
             'status': 'disabled', 'onboard_state': 'pending'},
        ]
        snapshot = {'active_ids': []}
        pending = detect_pending_onboard(tools, snapshot)
        assert 'dis1' not in pending

    def test_empty_snapshot_all_active_pending(self):
        """Empty snapshot -> all active non-done tools are pending."""
        tools = [
            {'id': 'a', 'name': 'A', 'aliases': ['A'], 'status': 'active', 'onboard_state': 'pending'},
            {'id': 'b', 'name': 'B', 'aliases': ['B'], 'status': 'active', 'onboard_state': 'done'},
            {'id': 'c', 'name': 'C', 'aliases': ['C'], 'status': 'active', 'onboard_state': 'pending'},
        ]
        snapshot = {'active_ids': []}
        pending = detect_pending_onboard(tools, snapshot)
        assert set(pending) == {'a', 'c'}

    def test_empty_tools(self):
        """No tools -> no pending."""
        assert detect_pending_onboard([], {'active_ids': []}) == []

    def test_running_tool_not_pending(self):
        """Tool currently running is not re-pending."""
        tools = [
            {'id': 'running', 'name': 'Running', 'aliases': ['Running'],
             'status': 'active', 'onboard_state': 'running'},
        ]
        snapshot = {'active_ids': []}
        pending = detect_pending_onboard(tools, snapshot)
        assert 'running' not in pending


class TestSnapshotIO:
    """Snapshot load/update round-trip."""

    def test_load_missing_snapshot(self, tmp_path):
        """Missing snapshot file returns empty snapshot."""
        result = load_snapshot(str(tmp_path / 'nonexistent.json'))
        assert result == {'active_ids': []}

    def test_update_and_load(self, tmp_path):
        """update_snapshot writes and load_snapshot reads back."""
        snap_path = str(tmp_path / 'snapshot.json')
        tools = [
            {'id': 'a', 'status': 'active'},
            {'id': 'b', 'status': 'active'},
            {'id': 'c', 'status': 'draft'},
        ]
        update_snapshot(tools, snap_path)
        loaded = load_snapshot(snap_path)
        assert set(loaded['active_ids']) == {'a', 'b'}
        assert 'c' not in loaded['active_ids']

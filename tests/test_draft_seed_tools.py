#!/usr/bin/env python3
"""Tests for draft_seed_tools.py"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from draft_seed_tools import (
    CANONICAL_31,
    build_draft_entry,
    match_existing_tool,
    plan_drafts,
    render_review_report,
)


EXISTING_10 = [
    {
        "id": "claude-code",
        "name": "Claude Code",
        "aliases": ["Claude Code", "claude-code"],
        "repo": "anthropics/claude-code",
        "status": "active",
        "tool_kind": "open",
        "onboard_state": "done",
    },
    {
        "id": "codex-cli",
        "name": "OpenAI Codex CLI",
        "aliases": ["Codex CLI", "OpenAI Codex", "codex"],
        "repo": "openai/codex",
        "status": "active",
        "tool_kind": "open",
        "onboard_state": "done",
    },
    {
        "id": "antigravity-cli",
        "name": "Antigravity CLI / Gemini CLI",
        "aliases": ["Antigravity CLI", "Gemini CLI", "agy"],
        "repo": "google-gemini/gemini-cli",
        "status": "active",
        "tool_kind": "open",
        "onboard_state": "done",
    },
    {
        "id": "opencode",
        "name": "OpenCode",
        "aliases": ["OpenCode", "opencode ai"],
        "repo": "sst/opencode",
        "status": "active",
        "tool_kind": "open",
        "onboard_state": "done",
    },
    {
        "id": "goose",
        "name": "Goose",
        "aliases": ["Goose", "Block Goose"],
        "repo": "block/goose",
        "status": "active",
        "tool_kind": "open",
        "onboard_state": "done",
    },
    {
        "id": "qoder",
        "name": "Qoder / QoderWork",
        "aliases": ["Qoder", "QoderWork"],
        "repo": "QoderAI/qoder-action",
        "status": "active",
        "tool_kind": "open",
        "onboard_state": "done",
    },
    {
        "id": "trae",
        "name": "Trae / Trae Work",
        "aliases": ["Trae", "Trae Agent"],
        "repo": "bytedance/trae-agent",
        "status": "active",
        "tool_kind": "open",
        "onboard_state": "done",
    },
    {
        "id": "workbuddy-codebuddy",
        "name": "WorkBuddy / CodeBuddy",
        "aliases": ["WorkBuddy", "CodeBuddy", "腾讯云代码助手"],
        "repo": None,
        "status": "active",
        "tool_kind": "closed",
        "onboard_state": "done",
    },
    {
        "id": "cursor",
        "name": "Cursor",
        "aliases": ["Cursor", "Cursor AI"],
        "repo": "getcursor/cursor",
        "status": "active",
        "tool_kind": "open",
        "onboard_state": "done",
    },
    {
        "id": "hermes-agent",
        "name": "Hermes Agent",
        "aliases": ["Hermes Agent", "Nous Hermes"],
        "repo": "NousResearch/hermes-agent",
        "status": "active",
        "tool_kind": "open",
        "onboard_state": "done",
    },
]


class TestCanonical31:
    def test_exactly_31_entries(self):
        assert len(CANONICAL_31) == 31

    def test_unique_suggested_ids(self):
        ids = [c["suggested_id"] for c in CANONICAL_31]
        assert len(ids) == len(set(ids))

    def test_codebuddy_maps_to_existing_id(self):
        codebuddy = next(c for c in CANONICAL_31 if c["display_name"] == "CodeBuddy")
        assert codebuddy["suggested_id"] == "workbuddy-codebuddy"


class TestMatchExisting:
    def test_match_by_id(self):
        canon = next(c for c in CANONICAL_31 if c["suggested_id"] == "cursor")
        hit = match_existing_tool(canon, EXISTING_10)
        assert hit is not None
        assert hit["id"] == "cursor"

    def test_match_codex_display_to_codex_cli(self):
        canon = next(c for c in CANONICAL_31 if c["display_name"] == "Codex")
        hit = match_existing_tool(canon, EXISTING_10)
        assert hit is not None
        assert hit["id"] == "codex-cli"

    def test_match_codebuddy_to_workbuddy(self):
        canon = next(c for c in CANONICAL_31 if c["display_name"] == "CodeBuddy")
        hit = match_existing_tool(canon, EXISTING_10)
        assert hit is not None
        assert hit["id"] == "workbuddy-codebuddy"

    def test_no_match_for_new_tool(self):
        canon = next(c for c in CANONICAL_31 if c["display_name"] == "Windsurf")
        hit = match_existing_tool(canon, EXISTING_10)
        assert hit is None


class TestBuildDraftEntry:
    def test_missing_tool_is_draft_pending(self):
        canon = next(c for c in CANONICAL_31 if c["display_name"] == "Windsurf")
        entry = build_draft_entry(canon)
        assert entry["status"] == "draft"
        assert entry["onboard_state"] == "pending"
        assert entry["id"] == "windsurf"
        assert entry["name"] == "Windsurf"
        assert "Windsurf" in entry["aliases"]

    def test_no_repo_means_closed(self):
        canon = next(c for c in CANONICAL_31 if c["display_name"] == "Tabnine")
        entry = build_draft_entry(canon)
        assert not entry.get("repo")
        assert entry["tool_kind"] == "closed"

    def test_with_repo_means_open(self):
        canon = next(c for c in CANONICAL_31 if c["display_name"] == "Aider")
        entry = build_draft_entry(canon)
        assert entry.get("repo")
        assert entry["tool_kind"] == "open"


class TestPlanDrafts:
    def test_no_duplicate_insert_for_existing(self):
        plan = plan_drafts(EXISTING_10)
        assert len(plan["matched"]) == 10
        assert len(plan["to_add"]) == 21
        existing_ids = {t["id"] for t in EXISTING_10}
        for draft in plan["to_add"]:
            assert draft["id"] not in existing_ids
            assert draft["status"] == "draft"

    def test_idempotent_when_all_present(self):
        # Simulate full set already present (matched + drafts as if applied)
        plan1 = plan_drafts(EXISTING_10)
        full = EXISTING_10 + plan1["to_add"]
        plan2 = plan_drafts(full)
        assert plan2["to_add"] == []
        assert len(plan2["matched"]) == 31

    def test_merged_result_count(self):
        plan = plan_drafts(EXISTING_10)
        merged = plan["merged"]
        assert len(merged) == 31
        ids = [t["id"] for t in merged]
        assert len(ids) == len(set(ids))
        assert "workbuddy-codebuddy" in ids
        assert "codebuddy" not in ids  # must not invent duplicate CodeBuddy id


class TestReviewReport:
    def test_report_lists_uncertain_fields(self):
        plan = plan_drafts(EXISTING_10)
        md = render_review_report(plan)
        assert "seed-tools draft review" in md.lower() or "审阅" in md
        assert "draft" in md.lower() or "草稿" in md
        # uncertain fields section for new drafts
        assert "uncertain" in md.lower() or "不确定" in md
        assert "Windsurf" in md or "windsurf" in md
        # CodeBuddy merge note
        assert "CodeBuddy" in md or "workbuddy" in md

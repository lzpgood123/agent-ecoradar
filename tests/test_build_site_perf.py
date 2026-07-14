# tests/test_build_site_perf.py
"""Batch 2 frontend perf: search-index + detail shards (no monolithic detail)."""
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def _sample_projects():
    return [
        {
            "id": f"github-proj-{i}",
            "name": f"Proj {i}",
            "url": f"https://github.com/o/r{i}",
            "source_type": "github",
            "resource_type": ["mcp-server"] if i % 2 == 0 else ["tutorial"],
            "target_tools": ["claude-code"] if i % 3 == 0 else ["general-ai-coding"],
            "summary": f"Summary for project {i}",
            "i18n": {
                "zh": {"name": f"项目{i}", "summary": f"摘要{i}"},
                "en": {"name": f"Proj {i}", "summary": f"Summary {i}"},
            },
            "stars": i,
            "forks": 0,
            "total_score": i,
            "quantifiable_score": i,
            "quality_score": 0,
            "tracking_priority": "pending",
            "last_updated": "2026-07-01",
            "first_seen": "2026-07-01",
            "last_seen": "2026-07-14",
            "license": "MIT",
            "languages": ["Python"],
            "review_state": "auto-indexed",
            "score_detail": {"stars": 1},
            "quality_detail": {},
            "llm_summary": None,
            "benchmark_ref": None,
            "last_analyzed": None,
            "repo": f"o/r{i}",
            "tags": ["ai"],
            "maturity": "unknown",
            "status": "active",
            "readme_preview": "long " * 50,
            "topics": ["mcp", "ai"],
        }
        for i in range(250)
    ]


class TestSearchIndex:
    def test_build_search_text_only_lightweight_fields(self):
        from build_site import build_search_text

        p = {
            "id": "x",
            "name": "Hello MCP",
            "summary": "A Tool",
            "resource_type": ["mcp-server", "skills"],
            "target_tools": ["claude-code"],
            "topics": ["should-not-appear"],
            "languages": ["Python"],
            "license": "MIT",
            "url": "https://example.com",
            "readme_preview": "secret body",
        }
        text = build_search_text(p)
        assert text == "hello mcp a tool mcp-server skills claude-code"
        assert "should-not-appear" not in text
        assert "python" not in text
        assert "mit" not in text
        assert "example.com" not in text
        assert "secret" not in text

    def test_build_search_index_shape(self):
        from build_site import build_search_index

        projects = _sample_projects()[:3]
        idx = build_search_index(projects)
        assert len(idx) == 3
        for entry, p in zip(idx, projects):
            assert set(entry.keys()) == {"id", "text"}
            assert entry["id"] == p["id"]
            assert isinstance(entry["text"], str)
            assert entry["text"] == entry["text"].lower()
            assert p["name"].lower() in entry["text"]
            assert p["summary"].lower() in entry["text"]


class TestDetailShards:
    def test_chunk_size_constant(self):
        from build_site import DETAIL_CHUNK_SIZE

        assert DETAIL_CHUNK_SIZE == 100

    def test_build_detail_shards_and_index(self, tmp_path):
        from build_site import DETAIL_CHUNK_SIZE, build_detail_shards, detail_project

        projects = [detail_project(p) for p in _sample_projects()]
        detail_dir = tmp_path / "detail"
        index = build_detail_shards(projects, detail_dir)

        n = len(projects)
        expected_chunks = math.ceil(n / DETAIL_CHUNK_SIZE)
        shard_files = sorted(detail_dir.glob("*.json"), key=lambda p: int(p.stem))
        assert len(shard_files) == expected_chunks
        assert set(index.keys()) == {p["id"] for p in projects}

        # first project in chunk 0, project 100 in chunk 1
        assert index[projects[0]["id"]] == 0
        assert index[projects[100]["id"]] == 1
        assert index[projects[249]["id"]] == 2

        # each shard has at most 100 items; last has remainder
        for i, f in enumerate(shard_files):
            chunk = json.loads(f.read_text(encoding="utf-8"))
            assert f.stem == str(i)
            if i < expected_chunks - 1:
                assert len(chunk) == DETAIL_CHUNK_SIZE
            else:
                assert len(chunk) == n % DETAIL_CHUNK_SIZE or len(chunk) == DETAIL_CHUNK_SIZE
            for item in chunk:
                assert item["id"] in index
                assert index[item["id"]] == i

    def test_build_detail_shards_clears_old_files(self, tmp_path):
        from build_site import build_detail_shards, detail_project

        detail_dir = tmp_path / "detail"
        detail_dir.mkdir()
        stale = detail_dir / "99.json"
        stale.write_text("[]", encoding="utf-8")

        projects = [detail_project(p) for p in _sample_projects()[:5]]
        build_detail_shards(projects, detail_dir)
        assert not stale.exists()
        assert (detail_dir / "0.json").exists()


class TestNoMonolithicDetail:
    def test_write_site_data_does_not_emit_projects_detail(self, tmp_path, monkeypatch):
        """Integration-ish: helper that writes site data must not create projects-detail.json."""
        from build_site import write_search_and_detail_artifacts

        site_data = tmp_path / "data"
        site_data.mkdir()
        # pre-existing monolith must be removed
        mono = site_data / "projects-detail.json"
        mono.write_text("[]", encoding="utf-8")

        projects = _sample_projects()[:120]
        write_search_and_detail_artifacts(projects, site_data)

        assert not mono.exists()
        assert (site_data / "search-index.json").exists()
        assert (site_data / "detail-index.json").exists()
        assert (site_data / "detail" / "0.json").exists()
        assert (site_data / "detail" / "1.json").exists()

        search = json.loads((site_data / "search-index.json").read_text(encoding="utf-8"))
        assert len(search) == 120
        dindex = json.loads((site_data / "detail-index.json").read_text(encoding="utf-8"))
        assert len(dindex) == 120

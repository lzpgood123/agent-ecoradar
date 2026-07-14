"""Test the initial bulk collection script (stars-tier strategy)."""
import datetime
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class TestQueryGeneration:
    def test_generates_topic_queries(self):
        from initial_collection import generate_topic_queries
        queries = generate_topic_queries()
        assert len(queries) > 0
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

    def test_month_ranges_fixed(self):
        from initial_collection import generate_month_ranges
        ranges = generate_month_ranges('2025-01', '2025-07')
        assert len(ranges) == 7
        assert ranges[0] == ('2025-01-01', '2025-01-31')
        assert ranges[-1] == ('2025-07-01', '2025-07-31')

    def test_month_ranges_from_2024_to_today(self, monkeypatch):
        from initial_collection import generate_month_ranges, default_month_end

        class FixedDate(datetime.date):
            @classmethod
            def today(cls):
                return cls(2026, 7, 14)

        monkeypatch.setattr(datetime, 'date', FixedDate)
        # re-import helpers that call date.today if needed
        start = '2024-01'
        end = default_month_end()
        ranges = generate_month_ranges(start, end)
        assert ranges[0] == ('2024-01-01', '2024-01-31')
        assert ranges[-1][0].startswith('2026-07')
        assert len(ranges) == 31  # 2024-01 .. 2026-07


class TestStarTiers:
    def test_tier_constants_cover_l1_to_l5b(self):
        from initial_collection import STAR_TIERS
        ids = [t['id'] for t in STAR_TIERS]
        assert ids == ['L1', 'L2', 'L3', 'L4', 'L5a', 'L5b']
        assert STAR_TIERS[0]['stars'] == '>=100000'
        assert STAR_TIERS[1]['stars'] == '50000..99999'
        assert STAR_TIERS[2]['stars'] == '10000..49999'
        assert STAR_TIERS[3]['stars'] == '1000..9999'
        assert STAR_TIERS[4]['stars'] == '500..999'
        assert STAR_TIERS[5]['stars'] == '100..499'
        # no <100 tier (lowest is 100..499)
        assert STAR_TIERS[-1]['stars'] == '100..499'
        assert not any(t['stars'].startswith('<') for t in STAR_TIERS)

    def test_build_tier_queries_l1_no_keyword_all_time(self):
        from initial_collection import build_tier_search_jobs, STAR_TIERS
        jobs = build_tier_search_jobs(
            STAR_TIERS[0],
            month_ranges=[('2024-01-01', '2024-01-31')],
            topic_queries=['topic:claude-code'],
            keyword_queries=['"claude code" skills'],
            created_lower='2024-01-01',
        )
        assert len(jobs) == 1
        assert jobs[0]['query'] == ''
        assert jobs[0]['stars'] == '>=100000'
        assert jobs[0]['created'] == '>2024-01-01'
        assert jobs[0]['month_or_all'] == 'all'

    def test_build_tier_queries_l4_monthly(self):
        from initial_collection import build_tier_search_jobs, STAR_TIERS
        months = [('2024-01-01', '2024-01-31'), ('2024-02-01', '2024-02-29')]
        jobs = build_tier_search_jobs(
            STAR_TIERS[3],
            month_ranges=months,
            topic_queries=['topic:x'],
            keyword_queries=['kw'],
            created_lower='2024-01-01',
        )
        assert len(jobs) == 2
        assert all(j['query'] == '' for j in jobs)
        assert jobs[0]['created'] == '2024-01-01..2024-01-31'
        assert jobs[0]['stars'] == '1000..9999'

    def test_build_tier_queries_l5_topic_keyword_monthly(self):
        from initial_collection import build_tier_search_jobs, STAR_TIERS
        months = [('2024-01-01', '2024-01-31')]
        jobs = build_tier_search_jobs(
            STAR_TIERS[4],
            month_ranges=months,
            topic_queries=['topic:claude-code'],
            keyword_queries=['"claude code" skills'],
            created_lower='2024-01-01',
        )
        # L5 is adaptive: one full-range probe per query (not forced monthly)
        assert len(jobs) == 2
        assert {j['query'] for j in jobs} == {'topic:claude-code', '"claude code" skills'}
        assert all(j['stars'] == '500..999' for j in jobs)
        assert all(j['created'] == '>2024-01-01' for j in jobs)
        assert all(j['month_or_all'] == 'all' for j in jobs)
        assert all(j.get('adaptive') is True for j in jobs)


class TestFilters:
    def _item(self, name='owner/repo', desc='', topics=None, stars=10):
        return {
            'fullName': name,
            'description': desc,
            'topics': topics or [],
            'stargazersCount': stars,
            'stars': stars,
        }

    def test_l1_thin_negative_drops_crypto(self):
        from initial_collection import passes_filter
        item = self._item(desc='best crypto airdrop miner bot', stars=200000)
        assert passes_filter(item, mode='thin_negative') is False

    def test_l1_thin_negative_keeps_ai_tool(self):
        from initial_collection import passes_filter
        item = self._item(name='openai/codex', desc='AI coding agent CLI', stars=200000)
        assert passes_filter(item, mode='thin_negative') is True

    def test_l4_weak_positive_requires_ai_word(self):
        from initial_collection import passes_filter
        ok = self._item(desc='cursor rules for typescript', stars=2000)
        bad = self._item(desc='general kubernetes toolkit', stars=2000)
        assert passes_filter(ok, mode='weak_positive') is True
        assert passes_filter(bad, mode='weak_positive') is False

    def test_l4_negative_still_applies(self):
        from initial_collection import passes_filter
        item = self._item(desc='llm crypto airdrop farming', stars=2000)
        assert passes_filter(item, mode='weak_positive') is False

    def test_l5_strict_requires_specific_positive(self):
        from initial_collection import passes_filter
        strict_ok = self._item(desc='awesome mcp server for coding agents', stars=200)
        weak_only = self._item(desc='ai chatbot for customer support', stars=200)
        assert passes_filter(strict_ok, mode='strict') is True
        assert passes_filter(weak_only, mode='strict') is False

    def test_l5_stars_below_3_dropped(self):
        from initial_collection import passes_filter
        item = self._item(desc='claude code skills pack', stars=2)
        assert passes_filter(item, mode='strict') is False
        item2 = self._item(desc='claude code skills pack', stars=3)
        assert passes_filter(item2, mode='strict') is True

    def test_filter_uses_topics(self):
        from initial_collection import passes_filter
        item = self._item(desc='misc utilities', topics=['mcp-server', 'coding-agent'], stars=50)
        assert passes_filter(item, mode='strict') is True


class TestSafeMerge:
    def _existing_llm(self):
        return {
            'id': 'github-openai-codex',
            'name': 'openai/codex',
            'url': 'https://github.com/openai/codex',
            'repo': 'openai/codex',
            'source_type': 'github',
            'summary': 'old summary kept if non-empty',
            'stars': 100,
            'forks': 10,
            'quality_score': 35,
            'quality_detail': {'relevance': 9},
            'tracking_priority': 'track',
            'last_analyzed': '2026-07-14',
            'benchmark_ref': 'github-openai-codex',
            'review_state': 'auto-curated',
            'first_seen': '2026-07-01',
            'last_seen': '2026-07-01',
            'i18n': {'zh': {'name': 'codex', 'summary': '中文摘要'}, 'en': {'name': 'codex', 'summary': 'en'}},
            'readme_preview': 'old readme',
        }

    def _incoming(self):
        return {
            'id': 'github-openai-codex',
            'name': 'openai/codex',
            'url': 'https://github.com/openai/codex',
            'repo': 'openai/codex',
            'source_type': 'github',
            'summary': 'fresh description from github',
            'stars': 999,
            'forks': 88,
            'license': 'Apache-2.0',
            'topics': ['ai', 'cli'],
            'languages': ['Rust'],
            'last_updated': '2026-07-14T00:00:00Z',
            'status': 'unknown',
            'readme_preview': 'new readme preview text',
            'quality_score': 0,
            'quality_detail': {},
            'tracking_priority': 'pending',
            'last_analyzed': None,
            'benchmark_ref': None,
            'review_state': 'auto-indexed',
            'first_seen': None,
            'last_seen': None,
            'i18n': {'zh': {'name': 'openai/codex', 'summary': 'fresh description from github'},
                     'en': {'name': 'openai/codex', 'summary': 'fresh description from github'}},
        }

    def test_merge_preserves_llm_fields(self):
        from initial_collection import safe_merge_record
        existing = self._existing_llm()
        incoming = self._incoming()
        merged = safe_merge_record(existing, incoming, today='2026-07-14', skip_existing=False)
        assert merged['quality_score'] == 35
        assert merged['quality_detail'] == {'relevance': 9}
        assert merged['tracking_priority'] == 'track'
        assert merged['last_analyzed'] == '2026-07-14'
        assert merged['benchmark_ref'] == 'github-openai-codex'
        assert merged['review_state'] == 'auto-curated'
        assert merged['first_seen'] == '2026-07-01'
        assert merged['last_seen'] == '2026-07-14'
        assert merged['stars'] == 999
        assert merged['forks'] == 88
        assert merged['summary'] == 'old summary kept if non-empty'
        assert merged['i18n']['zh']['summary'] == '中文摘要'

    def test_merge_new_record_appends(self):
        from initial_collection import safe_merge_record
        incoming = self._incoming()
        merged = safe_merge_record(None, incoming, today='2026-07-14', skip_existing=False)
        assert merged['first_seen'] == '2026-07-14'
        assert merged['last_seen'] == '2026-07-14'
        assert merged['tracking_priority'] == 'pending'
        assert merged['quality_score'] == 0

    def test_skip_existing_returns_existing_unchanged(self):
        from initial_collection import safe_merge_record
        existing = self._existing_llm()
        incoming = self._incoming()
        merged = safe_merge_record(existing, incoming, today='2026-07-14', skip_existing=True)
        assert merged is existing
        assert merged['stars'] == 100
        assert merged['last_seen'] == '2026-07-01'

    def test_official_seed_not_downgraded(self):
        from initial_collection import safe_merge_record
        seed = {
            'id': 'official-claude-code',
            'name': 'Claude Code',
            'url': 'https://github.com/anthropics/claude-code',
            'repo': 'anthropics/claude-code',
            'source_type': 'official-seed',
            'tracking_priority': 'track',
            'quality_score': 40,
            'last_analyzed': '2026-07-14',
            'summary': 'Official seed summary',
            'stars': 1,
            'first_seen': '2026-07-01',
            'last_seen': '2026-07-01',
        }
        incoming = {
            'id': 'github-anthropics-claude-code',
            'name': 'anthropics/claude-code',
            'url': 'https://github.com/anthropics/claude-code',
            'repo': 'anthropics/claude-code',
            'source_type': 'github',
            'tracking_priority': 'pending',
            'quality_score': 0,
            'summary': 'github desc',
            'stars': 50000,
            'forks': 1000,
            'readme_preview': 'readme',
        }
        merged = safe_merge_record(seed, incoming, today='2026-07-14', skip_existing=False)
        assert merged['source_type'] == 'official-seed'
        assert merged['tracking_priority'] == 'track'
        assert merged['quality_score'] == 40
        assert merged['name'] == 'Claude Code'
        # harmless github metadata refresh allowed
        assert merged['stars'] == 50000
        assert merged['forks'] == 1000
        assert merged['last_seen'] == '2026-07-14'


class TestCheckpointManager:
    def test_search_key_and_detail_skip(self, tmp_path):
        from initial_collection import CheckpointManager
        ckpt = CheckpointManager(tmp_path / 'checkpoint.json')
        ckpt.mark_search_done('L1', '', 'all', pages=1, results_count=10)
        assert ckpt.is_search_done('L1', '', 'all')
        assert not ckpt.is_search_done('L2', '', 'all')

        ckpt.mark_detail_done('owner/repo-a')
        ckpt.mark_detail_done('owner/repo-b')
        assert ckpt.is_detail_done('owner/repo-a')
        assert not ckpt.is_detail_done('owner/repo-c')
        assert set(ckpt.completed_details()) == {'owner/repo-a', 'owner/repo-b'}

    def test_get_progress(self, tmp_path):
        from initial_collection import CheckpointManager
        ckpt = CheckpointManager(tmp_path / 'checkpoint.json')
        ckpt.mark_search_done('L4', '', '2024-01-01..2024-01-31', pages=1, results_count=30)
        ckpt.mark_search_done('L4', '', '2024-02-01..2024-02-29', pages=1, results_count=20)
        ckpt.mark_detail_done('a/b')
        progress = ckpt.get_progress()
        assert progress['total_searches'] == 2
        assert progress['total_search_results'] == 50
        assert progress['completed_details'] == 1

    def test_legacy_save_compat(self, tmp_path):
        """Old CheckpointManager.save API still works if present for old tests."""
        from initial_collection import CheckpointManager
        ckpt = CheckpointManager(tmp_path / 'checkpoint.json')
        # new API uses mark_search_done; keep save as alias if provided
        if hasattr(ckpt, 'save'):
            ckpt.save('topic:claude-code', '2025-01', 2, 50)
            assert ckpt.is_done('topic:claude-code', '2025-01') or ckpt.is_search_done(
                'legacy', 'topic:claude-code', '2025-01'
            )
        else:
            ckpt.mark_search_done('legacy', 'topic:claude-code', '2025-01', 2, 50)
            assert ckpt.is_search_done('legacy', 'topic:claude-code', '2025-01')


class TestSeedTopicExpansion:
    def test_expand_topics_from_seed_list(self):
        from initial_collection import expand_topics_from_seeds
        seeds = [
            {'repo': 'anthropics/claude-code', 'topics': ['claude-code', 'ai']},
            {'repo': 'openai/codex', 'topics': ['codex', 'ai-coding']},
        ]
        topics = expand_topics_from_seeds(seeds, existing=['claude-code'])
        assert 'topic:ai' in topics
        assert 'topic:codex' in topics
        assert 'topic:ai-coding' in topics
        # existing not duplicated as bare topic if already present
        assert topics.count('topic:claude-code') <= 1

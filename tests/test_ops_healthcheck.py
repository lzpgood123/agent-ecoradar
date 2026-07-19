"""Test ops_healthcheck pure logic and signal collection."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


class TestEvaluateStatus:
    def test_all_green_is_ok(self):
        from ops_healthcheck import evaluate_status

        result = evaluate_status(
            {
                "last_daily_ok": True,
                "last_llm_ok": True,
                "disk_free_gb": 12.0,
                "llm_degraded": False,
                "quality_gate": "PASS",
                "deploy_age_hours": 6.0,
                "failed_onboards": 0,
            }
        )
        assert result["level"] == "ok"
        assert all(c["level"] == "ok" for c in result["checks"])

    def test_critical_failure_is_fail(self):
        from ops_healthcheck import evaluate_status

        result = evaluate_status(
            {
                "last_daily_ok": False,
                "last_llm_ok": True,
                "disk_free_gb": 12.0,
                "llm_degraded": False,
                "quality_gate": "PASS",
                "deploy_age_hours": 6.0,
                "failed_onboards": 0,
            }
        )
        assert result["level"] == "fail"
        daily = next(c for c in result["checks"] if c["id"] == "daily")
        assert daily["level"] == "fail"

    def test_degraded_or_disk_warn(self):
        from ops_healthcheck import evaluate_status

        result = evaluate_status(
            {
                "last_daily_ok": True,
                "last_llm_ok": True,
                "disk_free_gb": 3.5,
                "llm_degraded": True,
                "quality_gate": "PASS",
                "deploy_age_hours": 6.0,
                "failed_onboards": 0,
            }
        )
        assert result["level"] == "warn"
        disk = next(c for c in result["checks"] if c["id"] == "disk")
        llm = next(c for c in result["checks"] if c["id"] == "llm_keys")
        assert disk["level"] == "warn"
        assert llm["level"] == "warn"

    def test_quality_gate_fail_is_fail(self):
        from ops_healthcheck import evaluate_status

        result = evaluate_status(
            {
                "last_daily_ok": True,
                "last_llm_ok": True,
                "disk_free_gb": 12.0,
                "llm_degraded": False,
                "quality_gate": "FAIL",
                "deploy_age_hours": 6.0,
                "failed_onboards": 0,
            }
        )
        assert result["level"] == "fail"
        qg = next(c for c in result["checks"] if c["id"] == "quality_gate")
        assert qg["level"] == "fail"

    def test_failed_onboards_warn(self):
        from ops_healthcheck import evaluate_status

        result = evaluate_status(
            {
                "last_daily_ok": True,
                "last_llm_ok": True,
                "disk_free_gb": 12.0,
                "llm_degraded": False,
                "quality_gate": "PASS",
                "deploy_age_hours": 6.0,
                "failed_onboards": 2,
            }
        )
        assert result["level"] == "warn"
        onboard = next(c for c in result["checks"] if c["id"] == "onboard")
        assert onboard["level"] == "warn"

    def test_stale_deploy_warn(self):
        from ops_healthcheck import evaluate_status

        result = evaluate_status(
            {
                "last_daily_ok": True,
                "last_llm_ok": True,
                "disk_free_gb": 12.0,
                "llm_degraded": False,
                "quality_gate": "PASS",
                "deploy_age_hours": 72.0,
                "failed_onboards": 0,
            }
        )
        assert result["level"] == "warn"
        deploy = next(c for c in result["checks"] if c["id"] == "deploy")
        assert deploy["level"] == "warn"

    def test_missing_deploy_is_warn(self):
        from ops_healthcheck import evaluate_status

        result = evaluate_status(
            {
                "last_daily_ok": True,
                "last_llm_ok": True,
                "disk_free_gb": 12.0,
                "llm_degraded": False,
                "quality_gate": "PASS",
                "deploy_age_hours": None,
                "failed_onboards": 0,
            }
        )
        assert result["level"] == "warn"
        deploy = next(c for c in result["checks"] if c["id"] == "deploy")
        assert deploy["level"] == "warn"


class TestCollectSignals:
    def test_parse_latest_cron_success(self, tmp_path):
        from ops_healthcheck import parse_latest_cron_run

        job_dir = tmp_path / "2a0c271a031f"
        job_dir.mkdir()
        (job_dir / "2026-07-16_03-28-52.md").write_text(
            "# Cron Job: daily\n\n**Run Time:** 2026-07-16 03:28:52\n\n"
            '{"status": "PASS", "deploy": false}\n',
            encoding="utf-8",
        )
        ok, age_hours, path = parse_latest_cron_run(tmp_path, "2a0c271a031f")
        assert ok is True
        assert path is not None
        assert age_hours is not None
        assert age_hours >= 0

    def test_parse_latest_cron_failed_marker(self, tmp_path):
        from ops_healthcheck import parse_latest_cron_run

        job_dir = tmp_path / "2a0c271a031f"
        job_dir.mkdir()
        (job_dir / "2026-07-16_03-00-00.md").write_text(
            "# Cron Job: daily (FAILED)\n\nerror boom\n",
            encoding="utf-8",
        )
        ok, _age, path = parse_latest_cron_run(tmp_path, "2a0c271a031f")
        assert ok is False
        assert path is not None

    def test_parse_missing_job_dir(self, tmp_path):
        from ops_healthcheck import parse_latest_cron_run

        ok, age, path = parse_latest_cron_run(tmp_path, "missing")
        assert ok is None
        assert age is None
        assert path is None

    def test_parse_system_cron_log_success(self, tmp_path):
        from ops_healthcheck import parse_cron_log_file, parse_latest_cron_run

        log = tmp_path / "daily.log"
        log.write_text(
            '=== Deriving queries ===\n{"status": "PASS", "steps": 9, "deploy": false}\n'
            "Track projects to refresh: 1000\n",
            encoding="utf-8",
        )
        ok, age, path = parse_cron_log_file(log)
        assert ok is True
        assert path == log
        assert age is not None and age >= 0

        # Also via parse_latest_cron_run with .log job id
        ok2, _age2, path2 = parse_latest_cron_run(tmp_path, "daily.log")
        assert ok2 is True
        assert path2 == log

        # And via bare name + .log suffix auto
        ok3, _age3, path3 = parse_latest_cron_run(tmp_path, "daily")
        assert ok3 is True
        assert path3 == log

    def test_parse_system_cron_log_empty_is_missing(self, tmp_path):
        from ops_healthcheck import parse_cron_log_file

        log = tmp_path / "llm-daily.log"
        log.write_text("", encoding="utf-8")
        ok, age, path = parse_cron_log_file(log)
        assert ok is None
        assert path == log
        assert age is not None

    def test_collect_signals_falls_back_to_system_logs(self, tmp_path):
        from ops_healthcheck import collect_signals

        hermes_dir = tmp_path / "hermes-cron"
        hermes_dir.mkdir()
        system_dir = tmp_path / "system-cron"
        system_dir.mkdir()
        (system_dir / "daily.log").write_text(
            '{"status": "PASS", "steps": 9}\nNo tools need onboarding.\n',
            encoding="utf-8",
        )
        # weekly as llm fallback (no llm-daily.log)
        (system_dir / "weekly.log").write_text(
            "=== Weekly LLM Analysis Start ===\n"
            '{"status": "PASS"}\n=== Weekly End ===\n',
            encoding="utf-8",
        )
        root = tmp_path / "proj"
        (root / "data").mkdir(parents=True)
        (root / "data" / "seed-tools.yaml").write_text("[]\n", encoding="utf-8")
        metrics = tmp_path / "metrics.json"
        metrics.write_text("{}", encoding="utf-8")

        signals = collect_signals(
            root=root,
            cron_output_dir=hermes_dir,
            system_cron_output_dir=system_dir,
            webroot_metrics=metrics,
        )
        assert signals["last_daily_ok"] is True
        assert signals["last_llm_ok"] is True
        assert signals["quality_gate"] == "PASS"
        assert signals["daily_output"] and signals["daily_output"].endswith("daily.log")
        assert signals["llm_output"] and signals["llm_output"].endswith("weekly.log")

    def test_read_llm_degraded_true(self, tmp_path):
        from ops_healthcheck import read_llm_degraded

        p = tmp_path / "llm-key-stats.json"
        p.write_text(
            json.dumps(
                [
                    {"date": "2026-07-14", "degraded_mode": False},
                    {"date": "2026-07-15", "degraded_mode": True, "429_errors": 3},
                ]
            ),
            encoding="utf-8",
        )
        assert read_llm_degraded(p) is True

    def test_read_llm_degraded_false(self, tmp_path):
        from ops_healthcheck import read_llm_degraded

        p = tmp_path / "llm-key-stats.json"
        p.write_text(
            json.dumps([{"date": "2026-07-15", "degraded_mode": False}]),
            encoding="utf-8",
        )
        assert read_llm_degraded(p) is False

    def test_count_failed_onboards(self, tmp_path):
        from ops_healthcheck import count_failed_onboards

        p = tmp_path / "seed-tools.yaml"
        p.write_text(
            "- id: a\n  onboard_state: done\n"
            "- id: b\n  onboard_state: failed\n"
            "- id: c\n  onboard_state: pending\n"
            "- id: d\n  onboard_state: failed\n",
            encoding="utf-8",
        )
        assert count_failed_onboards(p) == 2

    def test_deploy_age_from_metrics(self, tmp_path):
        from ops_healthcheck import deploy_age_hours

        metrics = tmp_path / "metrics.json"
        metrics.write_text("{}", encoding="utf-8")
        # touch mtime to ~2h ago
        past = (datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()
        import os

        os.utime(metrics, (past, past))
        age = deploy_age_hours(metrics)
        assert age is not None
        assert 1.5 <= age <= 3.0

    def test_quality_gate_from_cron_output(self, tmp_path):
        from ops_healthcheck import parse_quality_gate_from_text

        text = '{\"status\": \"PASS\", \"errors\": []}'
        assert parse_quality_gate_from_text(text) == "PASS"
        text2 = "# Cron (FAILED)\nquality_gate FAIL"
        assert parse_quality_gate_from_text(text2) in ("FAIL", "UNKNOWN")

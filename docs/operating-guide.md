# Operating Guide

## Daily discovery

1. Run `python3 scripts/collect_github.py --limit 20`.
2. Run `python3 scripts/collect_exa.py --limit 3` if Exa is configured.
3. If Exa is unavailable, run `python3 scripts/collect_web.py --limit 5` and keep fallback labels.
4. Run `python3 scripts/normalize.py --source all`.
5. Run `python3 scripts/score.py`.

## Weekly report

```bash
python3 scripts/finalize_data.py
python3 scripts/generate_reports.py
python3 scripts/build_site.py
python3 scripts/quality_gate.py
```

## Monthly audit

Review `data/curated-projects.yaml`, `data/rejected-projects.yaml`, and `docs/reports/source-quality-audit.md`.

## Hermes cron setup

Use the prompt files in `.hermes/cron-prompts/` when creating cron jobs. Do not schedule them recursively from inside cron runs.

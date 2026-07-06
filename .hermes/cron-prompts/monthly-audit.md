# Monthly Audit

Run in `/root/workspace/search in coding`.

1. Pull latest `main`.
2. Run `python3 scripts/update_tracker.py --github-limit 30 --exa-limit 5`.
2. Audit curated and rejected datasets.
3. Check Exa availability and source quality.
4. Produce a monthly trend summary.
5. Commit and push updated `data/`, `docs/reports/`, and `site/` outputs when quality gates pass.
6. Do not fabricate sources; label fallback data clearly.

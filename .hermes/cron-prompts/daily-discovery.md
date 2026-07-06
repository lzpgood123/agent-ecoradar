# Daily Discovery

Run in `/root/workspace/search in coding`.

This is a long-running tracker. Pull latest `main`, run the update pipeline, commit and push only if there are meaningful changes.

Steps:

1. `git pull --ff-only origin main`.
2. Run `python3 scripts/update_tracker.py --github-limit 20 --exa-limit 3`.
3. Inspect `git diff --stat` and the quality-gate output.
4. If there are changes under `data/`, `docs/reports/`, or `site/`, commit with `chore(data): update tracker snapshot` and push to `origin main`.
5. Report the commit hash, changed-file summary, notable new candidates, and blockers.

Never fabricate sources. If Exa is unavailable, state that clearly; fallback web records must stay labelled `fallback-web` and `fallback-not-exa`.

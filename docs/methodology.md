# Methodology

1. Start from seed tools in `data/seed-tools.yaml`.
2. Query GitHub using authenticated `gh` and save raw JSON.
3. Query Exa semantic search with `mcporter call 'exa.web_search_exa(...)'` and save raw JSON/text.
4. Normalize raw results into `data/projects.yaml`.
5. Deduplicate by repo, URL, and normalized name.
6. Classify records by category, target tools, and concepts.
7. Score records using `config/scoring.yaml` plus `scripts/score.py`.
8. Mark records as `auto-indexed`, `auto-curated`, or `auto-rejected`.
9. Generate reports and site data.

Never fabricate search results. If a source is unavailable, record the blocker.

# Daily Discovery

Run in `/root/workspace/search in coding`.

1. Use `gh` to collect new GitHub records from `data/queries.yaml`.
2. Use Exa via `mcporter call 'exa.web_search_exa(query: "...", count: 3)'` for semantic web discovery.
3. Save raw outputs under `data/raw/`.
4. Normalize and score.
5. Report only notable new candidates and blockers.

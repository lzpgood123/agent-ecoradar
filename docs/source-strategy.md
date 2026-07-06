# Source Strategy

## GitHub

Use `gh search repos`, `gh repo view`, `gh api`, and release endpoints. Save raw outputs under `data/raw/github/YYYY-MM-DD/`.

## Exa

Use Exa as the preferred semantic web search source:

```bash
source ~/.agent-reach-venv/bin/activate
mcporter call 'exa.web_search_exa(query: "Claude Code ecosystem extensions plugins MCP skills rules best practices", count: 3)'
```

If Exa fails, fallback sources may be used, but must be labeled as fallback.

## Official docs

Track product docs, changelogs, blogs, marketplace pages, and GitHub orgs.

## Community

Track tutorials, case studies, HN/Reddit/X/YouTube/Chinese community content when accessible.

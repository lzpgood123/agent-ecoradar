# Data Dictionary

## Common fields

- `id`: stable record id.
- `name`: project/source name.
- `url`: canonical URL.
- `repo`: GitHub owner/repo when applicable.
- `source_type`: `github`, `official-seed`, `exa`, `fallback-web`, etc.
- `record_kind`: `official-tool`, `ecosystem-project`, `article`, `tutorial`, `fallback-result`.
- `source_quality`: `verified`, `fallback`, `unverified`, `blocked`.
- `ranking_scope`: `official`, `ecosystem`, `learning-resource`, `excluded`.
- `category`: taxonomy labels.
- `target_tools`: target tool ids.
- `review_state`: `reviewed`, `unreviewed`, `rejected`.
- `recommendation_level`: curated recommendation such as `try-now`, `watch`, `reference`.

## Source quality

Fallback web data is never Exa data. It is marked `fallback-web` and tagged `fallback-not-exa`.

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
- `review_state`: auto-maintenance state: `auto-indexed`, `auto-curated`, or `auto-rejected`.
- `recommendation_level`: auto-curated recommendation such as `try-now`, `watch`, `reference`, or `experimental`.
- `i18n`: bilingual display fields: `i18n.zh.name`, `i18n.zh.summary`, `i18n.en.name`, `i18n.en.summary`.
- `score_reason`: explainable scoring components loaded from `config/scoring.yaml`.

## Source quality

Fallback web data is never Exa data. It is marked `fallback-web` and tagged `fallback-not-exa`.

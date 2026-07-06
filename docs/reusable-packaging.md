# Reusable Packaging

To reuse this tracker for another ecosystem:

1. Replace `data/seed-tools.yaml`.
2. Replace or extend `data/queries.yaml`.
3. Update taxonomy only if new categories are needed.
4. Run collectors.
5. Normalize, score, and build the site.
6. Use `scripts/export_pack.py` to package the reusable template.

Keep scripts generic; ecosystem-specific facts belong in data files and prompts.

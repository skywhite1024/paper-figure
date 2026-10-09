# Catalog and review

1. Import a citation with pinned source commit/line; keep `not_reviewed`
2. Inspect actual figure pixels, caption, page/version and specific rights; mark `blocked` if needed
3. Work as `in_progress`: choose native extraction for vector sources, manual reconstruction for flattened figures
4. Preserve original layout/colors/details. Separate unavoidable raster assets and log exactly what remains pixel-based
5. Validate JSON, export editable formats, inspect original versus rendered output, check text and connector/path construction
6. Mark `recreated` only when a usable scene exists, retaining review caveats. Reserve `verified` for complete defined manual fidelity and target-editor checks
7. Batch only exports `recreated` / `verified`; failures are per item, unreviewed rows untouched, nonzero failure exit

A catalog paper uses `id`, `title`, `url`, `status`, optional `diagram` relative to catalog directory. Recreated/verified entries need a scene path. One current selected figure per paper is supported; legacy figures can be exported separately.

Output hashes verify bytes, not semantic correctness. Preview checks do not prove native Microsoft PowerPoint editing. Public redistribution requires separate rights review and user authorization, not just an arXiv link.

## Paper-scoped published outputs

Each paper owns `output/<paper-id>/`, including native editable formats, preview PNG, original comparison PNG, fixed-version source PDF, `sources.json`, export manifest, validation record, README and `comparison.html`. The root output folder has only shared indexes/summary.

Render to `build/aspire/` and `build/roboreact/`, then run `python research/refresh_outputs.py --from-build build`. This verifies hashes before publishing diagram files, preserves the original PDF/source image, and resets changed outputs to pending review. `research/package_release.py` packages this canonical nested layout rather than reconstructing the obsolete flat layout.

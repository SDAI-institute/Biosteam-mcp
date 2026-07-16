# Reference

Quick-reference material distilled from building the tutorials.

| File | What |
|------|------|
| [cheatsheet.md](cheatsheet.md) | Copy-pasteable snippets for every layer (thermo → TEA → LCA → QSDsan) |
| [glossary.md](glossary.md) | Core vocabulary: process modeling, TEA, LCA, uncertainty, QSDsan |
| [troubleshooting.md](troubleshooting.md) | Real errors → causes → fixes, incl. version-specific gotchas |

## Key version-specific facts (envShilab: BioSTEAM 2.51 / thermosteam 0.51 / QSDsan 1.4)
- `bst.Model(sys, indicators=[...])` — constructor uses `indicators`, not `metrics`.
- `model.spearman_r()` returns **two** DataFrames (rho, p-values).
- Impact aggregators need `sys.operating_hours` set (they return annual values).
- `qs.SanUnit` is the base class (not under `qsdsan.sanunits`).
- Distillation reflux/stages live in `design_results`, not attributes.

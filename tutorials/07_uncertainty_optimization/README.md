# Tier 7 — Uncertainty & optimization

Report ranges, not point values — and optimize designs. `bst.Model` couples uncertain
`Parameter`s to output `Metric`s. The same machinery is shared by QSDsan.

## Learning objectives
- Build a `Model` with `Parameter`s (chaospy distributions) and `Metric`s.
- Run **Monte Carlo** and report a metric distribution (P5 / P50 / P95).
- Rank uncertainty drivers with **Spearman** sensitivity (`spearman_r` → rho + p-values).
- **Optimize** a design variable against a metric (`scipy.optimize`).

## Contents
| File | What |
|------|------|
| `07_uncertainty_and_optimization.py` | Runnable percent-format script |
| `07_uncertainty_and_optimization.ipynb` | Executed notebook with real outputs |

## Key API notes
- `bst.Model(system, indicators=[...])` — this version uses **`indicators`**, not
  `metrics`, in the constructor.
- `model.spearman_r()` returns **two** DataFrames (rho, p-values).

**Next:** [Tier 8 — Expert integration](../08_expert_integration/).

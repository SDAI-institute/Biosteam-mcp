# Tier 7 â€” Uncertainty & optimization

Report ranges, not point values â€” and optimize designs. `bst.Model` couples uncertain
`Parameter`s to output `Metric`s. The same machinery is shared by QSDsan.

## Learning objectives
- Build a `Model` with `Parameter`s (chaospy distributions) and `Metric`s.
- Run **Monte Carlo** and report a metric distribution (P5 / P50 / P95).
- Rank uncertainty drivers with **Spearman** sensitivity (`spearman_r` â†’ rho + p-values).

# Results — Optimize, then quantify uncertainty

Two-stage expert workflow on an ethanol concentration process: optimize the design,
then quantify MSP uncertainty *at the optimum*.

## Stage 1 — optimization (minimize MSP)
Gradient-free `differential_evolution` over heater temperature and flash vapor fraction.

| Design | Heater T | Flash V | MSP |
|--------|----------|---------|-----|
| Baseline | 355.0 K | 0.50 | $0.1951/kg |
| **Optimum** | **348.7 K** | **0.650** | **$0.1592/kg** |

Improvement: **$0.036/kg (−18%)** — lower heating duty (cost) + higher recovery.
A gradient (L-BFGS-B) method stalls on this flat/noisy surface; the gradient-free
optimizer finds the real optimum.

## Stage 2 — uncertainty at the optimum (250-sample Monte Carlo)
| MSP percentile | Value |
|----------------|-------|
| P5 | $0.1137/kg |
| P50 | $0.1627/kg |
| P95 | $0.2160/kg |

Dominant driver of remaining uncertainty: **feedstock price** (Spearman ρ ≈ 1.0);
target IRR and electricity price are negligible here.

## Takeaway
Quantifying uncertainty at the *nominal* design would misstate the risk profile.
Optimize first, then characterize the distribution of the metric at that design —
and note that the residual uncertainty is external (feedstock market), not something
more process tuning can remove.

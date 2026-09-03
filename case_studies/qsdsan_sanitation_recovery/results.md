# Results — Sanitation & nutrient recovery under uncertainty

QSDsan resource-recovery step on municipal wastewater (1000 m³/hr), analyzed with
300-sample Monte Carlo over recovery efficiencies and influent load.

## Headline numbers
| Metric | Value |
|--------|-------|
| Baseline P recovered | 6.40 kg/hr |
| P recovered — P50 | 7.00 kg/hr |
| P recovered — 90% interval | 4.81 – 9.49 kg/hr |
| Effluent TN (mean) | 28.0 mg/L (range 20–36) |

## Sensitivity (Spearman rho vs P recovered)
| Parameter | rho |
|-----------|-----|
| Influent PO₄ concentration | 0.911 |
| P recovery efficiency | 0.356 |
| N recovery efficiency | 0.058 |

**Takeaway:** phosphorus recovery is dominated by the *influent load*, not the unit's
efficiency — so upstream source separation / load management matters more than tuning
the recovery step. A point estimate would have hidden that.

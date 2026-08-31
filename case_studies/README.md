# Case studies

Five end-to-end studies, each with a runnable script, an **executed** notebook, and a
`results.md` recording reproducible headline numbers.

| Study | Domain | Headline |
|-------|--------|----------|
| [biorefinery_cornstover_ethanol](biorefinery_cornstover_ethanol/) | Biorefinery TEA | MSP ≈ **$0.69/kg** ethanol; FCI $360 MM; 68 units |
| [biodiesel_lipidcane](biodiesel_lipidcane/) | Co-product allocation | biodiesel footprint 1.95→2.68 kg CO₂e/kg by allocation basis; IRR 20.8% |
| [qsdsan_sanitation_recovery](qsdsan_sanitation_recovery/) | Sanitation + uncertainty | P recovery P50 7.0 kg/hr (90% CI 4.8–9.5); influent load dominates |
| [cross_framework_lca](cross_framework_lca/) | LCA reconciliation | BioSTEAM vs independent aggregation reconcile **exactly** |
| [optimization_uncertainty](optimization_uncertainty/) | Optimize + uncertainty | MSP −18% by optimization; then P50 $0.163 (CI $0.11–$0.22) |

## Run any of them
```powershell
conda activate envShilab
python case_studies/<folder>/<script>.py
```

These build on the [tutorials](../tutorials/); each study's README lists the tiers it
applies.

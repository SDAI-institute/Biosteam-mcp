# Results â€” Optimize, then quantify uncertainty

Two-stage expert workflow on an ethanol concentration process: optimize the design,
then quantify MSP uncertainty *at the optimum*.

## Stage 1 â€” optimization (minimize MSP)
Gradient-free `differential_evolution` over heater temperature and flash vapor fraction.

| Design | Heater T | Flash V | MSP |
|--------|----------|---------|-----|
| Baseline | 355.0 K | 0.50 | $0.1951/kg |
| **Optimum** | **348.7 K** | **0.650** | **$0.1592/kg** |


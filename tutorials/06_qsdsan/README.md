# Tier 6 — QSDsan: sanitation & resource recovery

QSDsan extends BioSTEAM to sanitation systems: `WasteStream`s with wastewater
composite variables, `SanUnit`s, 100+ published unit models, and dynamic simulation.

## Learning objectives
- Load QSDsan `Components` and build a `WasteStream` by concentration.
- Read composite variables (COD, BOD, TN, TP) and compute nutrient loads.
- Write a `SanUnit` and assemble/simulate a QSDsan `System`.
- Quantify removal efficiency and recovered resource mass.

## Contents
| File | What |
|------|------|
| `06_qsdsan_sanitation.py` | Runnable percent-format script |
| `06_qsdsan_sanitation.ipynb` | Executed notebook with real outputs |

## Going further
QSDsan also does **dynamic** process simulation (ASM/ADM models via `Process`
objects) and ships validated systems in **EXPOsan**. The [QSDsan case
study](../../case_studies/qsdsan_sanitation_recovery/) builds one end-to-end with
uncertainty.

**Next:** [Tier 7 — Uncertainty & optimization](../07_uncertainty_optimization/).

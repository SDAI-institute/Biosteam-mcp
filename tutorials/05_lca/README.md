# Tier 5 — Life-cycle assessment (LCA)

Attach environmental impacts to a system: characterization factors, aggregation, and
allocation.

## Learning objectives
- Define an impact indicator and set CFs on streams (`set_CF`) and electricity
  (`PowerUtility.set_CF`).
- Aggregate a system's annual impact (`get_total_feeds_impact`,
  `get_net_electricity_impact`) — remember to set `sys.operating_hours`.
- Express impact per unit product and apply **mass / energy / economic allocation**
  to a co-product — and see how much the choice matters.

## Contents
| File | What |
|------|------|
| `05_lca_impacts_allocation.py` | Runnable percent-format script |
| `05_lca_impacts_allocation.ipynb` | Executed notebook with real outputs |

## Connects to
Your wider ecosystem: BioSTEAM supplies the **foreground** inventory; openLCA /
Brightway supply **background** CFs. The [cross-framework LCA case
study](../../case_studies/cross_framework_lca/) reconciles the two.

**Next:** [Tier 6 — QSDsan](../06_qsdsan/).

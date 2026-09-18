# %% [markdown]
# # Tier 8 â€” Expert integration & the MCP-facing API
#
# The capstone. Two ideas:
#
# 1. **One results contract.** BioSTEAM and QSDsan share the same `System`/`TEA`/
#    `Model` base classes, so a *single* `summarize_system` function works across
#    frameworks and across models â€” from a toy flowsheet to a published biorefinery.
# 2. That contract is exactly what the **MCP server** (Phase 3) returns. Designing it
#    here, against the real API, is what makes the MCP spec trustworthy.

# %%
import warnings
warnings.filterwarnings("ignore")

import biosteam as bst

# %% [markdown]
# ## 1. A uniform results contract
#
# `summarize_system` takes a simulated system (and optional TEA + product) and returns
# a plain, JSON-friendly dict. Plain dict = trivially serializable over MCP.

# %%
def summarize_system(system, tea=None, product=None):
    """Return a JSON-friendly summary of a simulated BioSTEAM/QSDsan system."""
    summary = {
        "system": system.ID,
        "n_units": len(system.units),
        "units": [u.ID for u in system.units],
        "installed_equipment_cost_MM": round(system.installed_equipment_cost / 1e6, 3),
        "feeds": {s.ID: round(s.F_mass, 1) for s in system.feeds},
        "products": {s.ID: round(s.F_mass, 1) for s in system.products},
    }
    if tea is not None:
        summary["tea"] = {
            "FCI_MM": round(tea.FCI / 1e6, 3),
            "FOC_MM_per_yr": round(tea.FOC / 1e6, 3),
            "VOC_MM_per_yr": round(tea.VOC / 1e6, 3),
            "NPV_MM": round(tea.NPV / 1e6, 2),
        }
        if product is not None:
            summary["tea"]["MSP_usd_per_kg"] = round(float(tea.solve_price(product)), 4)
    return summary

# %% [markdown]
# ## 2. Apply it to a published biorefinery
#

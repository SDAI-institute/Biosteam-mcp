# %% [markdown]
# # Tier 8 — Expert integration & the MCP-facing API
#
# The capstone. Two ideas:
#
# 1. **One results contract.** BioSTEAM and QSDsan share the same `System`/`TEA`/
#    `Model` base classes, so a *single* `summarize_system` function works across
#    frameworks and across models — from a toy flowsheet to a published biorefinery.
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
# The `biorefineries` package ships peer-reviewed BioSTEAM models. Load cornstover→
# ethanol and summarize it through the *same* contract — no bespoke extraction code.

# %%
from biorefineries import cornstover as cs
cs.load()
cs_summary = summarize_system(cs.cornstover_sys, tea=cs.cornstover_tea, product=cs.ethanol)
print("Cornstover biorefinery:")
for k, v in cs_summary.items():
    if k not in ("units", "feeds", "products"):
        print(f"  {k}: {v}")
print(f"  MSP = ${cs_summary['tea']['MSP_usd_per_kg']}/kg ethanol")
print(f"  units in system: {cs_summary['n_units']}")

# %% [markdown]
# ## 3. The same contract on a toy system
#
# The point of a contract: it doesn't care how big or which framework. Here a 3-unit
# flowsheet returns the identically-shaped dict.

# %%
bst.main_flowsheet.clear()
bst.settings.set_thermo(["Water", "Ethanol"])
feed = bst.Stream("feed", Water=1000, Ethanol=500, units="kmol/hr", T=298.15)
H1 = bst.HXutility("H1", ins=feed, outs="hot", T=360)
F1 = bst.Flash("F1", ins=H1 - 0, outs=("vapor", "liquid"), V=0.5, P=101325)
P1 = bst.Pump("P1", ins=F1 - 1, outs="bottoms")
toy = bst.System.from_units("toy_sys", units=[H1, F1, P1])
toy.simulate()
toy_summary = summarize_system(toy)          # no TEA -> tea key simply absent
print("Toy system:")
for k, v in toy_summary.items():
    print(f"  {k}: {v}")

# %% [markdown]
# ## 4. Cross-framework note
#
# `qsdsan.System`, `qsdsan.TEA`, and `qsdsan.Model` **subclass** their BioSTEAM
# counterparts, so `summarize_system` accepts a QSDsan system unchanged — the toolchain
# (and the MCP) is framework-agnostic by construction.

# %%
import qsdsan as qs
print("qs.System is a bst.System subclass:", issubclass(qs.System, bst.System))
print("qs.TEA    is a bst.TEA    subclass:", issubclass(qs.TEA, bst.TEA))

# %% [markdown]
# ## 5. This is the MCP tool contract
#
# The dict below is the shape `simulate_system` / `get_tea_results` will return over
# MCP (Phase 3): stable keys, primitive values, framework-agnostic.

# %%
import json
print(json.dumps({k: v for k, v in cs_summary.items() if k != "units"}, indent=2)[:600])

mcp_contract = {
    "cornstover_MSP_usd_kg": cs_summary["tea"]["MSP_usd_per_kg"],
    "cornstover_n_units": cs_summary["n_units"],
    "toy_installed_cost_MM": toy_summary["installed_equipment_cost_MM"],
}
print(mcp_contract)

# %% [markdown]
# ## You can now…
# - write one framework-agnostic results contract for BioSTEAM *and* QSDsan;
# - drive it from a published biorefinery and a toy system identically;
# - see why the MCP tool outputs are just this dict serialized.
#
# **Next:** the [case studies](../../case_studies/) apply everything end-to-end, and
# [`mcp/SPEC.md`](../../mcp/SPEC.md) turns this contract into the server's tool schemas.
print("Tier 8 complete.")

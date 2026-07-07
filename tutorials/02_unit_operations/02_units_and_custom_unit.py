# %% [markdown]
# # Tier 2 — Unit operations
#
# Units are the equipment that transform streams. This tier covers:
#
# 1. Built-in units: a reactor (with a `Reaction`), a heat exchanger, and a
#    distillation column.
# 2. How units carry **design** and **purchase-cost** results after simulation.
# 3. Writing your own **custom `Unit`** subclass.

# %%
import warnings
warnings.filterwarnings("ignore")

import biosteam as bst
import thermosteam as tmo
from thermosteam.reaction import Reaction

bst.settings.set_thermo(["Water", "Ethanol", "AceticAcid", "EthylAcetate", "Glycerol"])
print("BioSTEAM", bst.__version__)

# %% [markdown]
# ## 1. A reaction inside a custom unit
#
# thermosteam's `Reaction` describes stoichiometry + conversion. Esterification:
# acetic acid + ethanol → ethyl acetate + water. We'll wrap it in a **custom Unit**
# to show the pattern you'll reuse for any bespoke equipment.
#
# A `Unit` subclass declares inlet/outlet counts and implements `_run` (the mass/
# energy balance). Optionally `_design` and `_cost` add sizing and purchase cost.

# %%
class Esterifier(bst.Unit):
    """Isothermal esterification reactor with a fixed acetic-acid conversion."""
    _N_ins = 1
    _N_outs = 1

    def __init__(self, ID="", ins=None, outs=(), thermo=None, *, conversion=0.6, T=353.15):
        super().__init__(ID, ins, outs, thermo)
        self.conversion = conversion
        self.T = T
        self.reaction = Reaction(
            "AceticAcid + Ethanol -> EthylAcetate + Water",
            reactant="AceticAcid", X=conversion,
        )

    def _run(self):
        effluent = self.outs[0]
        effluent.copy_like(self.ins[0])
        self.reaction(effluent)     # apply conversion in place
        effluent.T = self.T

feed = bst.Stream("feed", AceticAcid=100, Ethanol=120, units="kmol/hr", T=353.15)
R1 = Esterifier("R1", ins=feed, outs="reacted", conversion=0.6)
R1.simulate()
print(f"ethyl acetate produced = {R1.outs[0].imol['EthylAcetate']:.1f} kmol/hr")
R1.outs[0].show(flow="kmol/hr")

# %% [markdown]
# ## 2. A heat exchanger — design + cost after simulation
#
# `HXutility` heats/cools a stream to a target using a utility. After `simulate`,
# the unit exposes a `design_results` dict and a `purchase_cost`.

# %%
H1 = bst.HXutility("H1", ins=R1-0, outs="hot", T=370.15, rigorous=False)
H1.simulate()
print(f"duty        = {H1.Q/1e3:,.1f} MJ/hr")
print(f"area        = {H1.design_results.get('Area', float('nan')):,.1f} m2")
print(f"purchase $  = {H1.purchase_cost:,.0f}")

# %% [markdown]
# ## 3. Distillation — a rigorous built-in unit
#
# `BinaryDistillation` sizes a column to hit light/heavy-key recoveries. We separate
# water (light key) from glycerol (heavy key) — a wide-boiling, non-azeotropic pair
# (Tb 373 K vs 562 K), so McCabe–Thiele converges easily. It reports stages, reflux,
# and cost.
#
# > Aside: ethanol/water and ethyl-acetate/water form **azeotropes** that cap the
# > achievable purity; ordinary distillation can't cross them, which is exactly why
# > biorefineries reach for molecular sieves or extractive distillation.

# %%
feed2 = bst.Stream("feed2", Water=140, Glycerol=60, units="kmol/hr", T=373.15, P=101325)
D1 = bst.BinaryDistillation(
    "D1", ins=feed2, outs=("distillate", "bottoms"),
    LHK=("Water", "Glycerol"), k=1.5, Lr=0.99, Hr=0.99, P=101325,
)
D1.simulate()
print(f"actual stages    = {D1.design_results.get('Actual stages', 'n/a')}")
print(f"reflux ratio     = {D1.design_results['Reflux']:.2f}")
print(f"distillate water = {D1.outs[0].imol['Water']:.1f} kmol/hr "
      f"(purity {100*D1.outs[0].imass['Water']/D1.outs[0].F_mass:.1f}%)")
print(f"purchase $       = {D1.purchase_cost:,.0f}")

# %% [markdown]
# ## 4. Inspect design results generically
#
# Every unit exposes the same interface, so tooling (and the MCP server) can read
# design/cost from any unit uniformly.

# %%
for u in (R1, H1, D1):
    print(f"{u.ID:4s} {type(u).__name__:20s} purchase_cost=${u.purchase_cost:,.0f}")

summary = {
    "ethyl_acetate_kmol_hr": round(float(R1.outs[0].imol["EthylAcetate"]), 1),
    "hx_duty_MJ_hr": round(float(H1.Q) / 1e3, 1),
    "column_actual_stages": D1.design_results.get("Actual stages"),
}
print(summary)

# %% [markdown]
# ## You can now…
# - use built-in units (`HXutility`, `BinaryDistillation`) and read their
#   `design_results` and `purchase_cost`;
# - apply a `Reaction` with a conversion;
# - write a custom `Unit` subclass (`_N_ins`/`_N_outs`/`_run`).
#
# **Next — Tier 3 (`03_systems_flowsheets`)**: wire units into `System`s with recycle
# loops, converge them, and draw flowsheet diagrams.
print("Tier 2 complete.")

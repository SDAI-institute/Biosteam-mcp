# %% [markdown]
# # Tier 5 â€” Life-cycle assessment (LCA)
#
# BioSTEAM attaches **characterization factors (CFs)** to streams and utilities, then
# aggregates them over a `System` to a life-cycle impact (here **GWP**, kg CO2-eq).
# This tier:
#
# 1. Defines an impact indicator and sets CFs on feeds and electricity.
# 2. Computes the system's total feed + utility impact.
# 3. Expresses impact per kg of product and explores **allocation** (mass, energy,
#    economic) between a main product and a co-product.

# %%
import warnings
warnings.filterwarnings("ignore")

import biosteam as bst
from thermosteam.reaction import Reaction

bst.main_flowsheet.clear()
bst.settings.set_thermo(["Water", "Ethanol", "Glucose", "CO2"])
print("BioSTEAM", bst.__version__)

# %% [markdown]
# ## 1. Define an indicator and set characterization factors
#
# `define_impact_indicator` registers the metric; `stream.set_CF` and
# `PowerUtility.set_CF` attach per-kg / per-kWh factors (illustrative values).

# %%
GWP = "GWP"
bst.settings.define_impact_indicator(GWP, "kg*CO2e")

feed = bst.Stream("feed", Glucose=100, Water=900, units="kmol/hr")
feed.set_CF(GWP, 1.20)                       # 1.20 kg CO2e per kg glucose feed (cradle-to-gate)
bst.PowerUtility.set_CF(GWP, 0.45)           # 0.45 kg CO2e per kWh grid electricity
print("feed GWP CF   :", feed.get_CF(GWP), "kg CO2e/kg")
print("power GWP CF  :", bst.PowerUtility.get_CF(GWP), "kg CO2e/kWh")

# %% [markdown]
# ## 2. A small fermentation + recovery system
#
# Glucose â†’ ethanol + CO2, then a pump (draws electricity) and a flash concentrate.

# %%
class Fermenter(bst.Unit):
    _N_ins = 1
    _N_outs = 1
    def __init__(self, ID="", ins=None, outs=(), thermo=None, *, X=0.9):
        super().__init__(ID, ins, outs, thermo)
        self.reaction = Reaction("Glucose -> 2 Ethanol + 2 CO2", reactant="Glucose", X=X)
    def _run(self):
        out = self.outs[0]

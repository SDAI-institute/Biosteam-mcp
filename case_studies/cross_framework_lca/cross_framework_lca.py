# %% [markdown]
# # Case study â€” Cross-framework LCA
#
# LCA splits into a **foreground** (the process you model) and a **background** (grid
# electricity, chemical production, transport â€” supplied by databases like ecoinvent
# via openLCA or Brightway). BioSTEAM produces the foreground *inventory*; the
# background contributes *characterization factors (CFs)*.
#
# This case study:
# 1. Extracts a foreground inventory from a BioSTEAM system.
# 2. Applies a background CF table (a stand-in for an openLCA/Brightway lookup).
# 3. Reconciles BioSTEAM's built-in aggregation against an independent calculation â€”
#    they must agree, which is how you trust a coupled BioSTEAM â†” openLCA workflow.

# %%
import warnings
warnings.filterwarnings("ignore")

import biosteam as bst

bst.main_flowsheet.clear()
bst.settings.set_thermo(["Water", "Ethanol", "Glucose", "CO2"])
GWP = "GWP"
bst.settings.define_impact_indicator(GWP, "kg*CO2e")
print("BioSTEAM", bst.__version__)

# %% [markdown]
# ## 1. A foreground process (fermentation â†’ concentration)

# %%
from thermosteam.reaction import Reaction

feed = bst.Stream("glucose_feed", Glucose=100, Water=900, units="kmol/hr")

class Fermenter(bst.Unit):
    _N_ins = 1; _N_outs = 1
    def __init__(self, ID="", ins=None, outs=(), thermo=None, *, X=1.0):
        super().__init__(ID, ins, outs, thermo)
        self.reaction = Reaction("Glucose -> 2 Ethanol + 2 CO2", reactant="Glucose", X=X)
    def _run(self):
        out = self.outs[0]; out.copy_like(self.ins[0]); self.reaction(out); out.T = 305.15

R1 = Fermenter("R1", ins=feed, outs="broth")
P1 = bst.Pump("P1", ins=R1 - 0, outs="pumped", P=3e5)

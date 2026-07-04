# %% [markdown]
# # Tier 3 â€” Systems, flowsheets, and recycle convergence
#
# A `System` sequences units and **solves recycle loops** to a consistent steady
# state. This tier builds a system with a real recycle and watches it converge.
#
# 1. The flowsheet registry (how units/streams are named and found).
# 2. A recycle loop: reactor â†’ separator â†’ recycle the unreacted feed.
# 3. Convergence: what "the recycle stream stopped changing" means numerically.
# 4. Process specifications (`@u.add_specification`).

# %%
import warnings
warnings.filterwarnings("ignore")

import biosteam as bst
from thermosteam.reaction import Reaction

bst.main_flowsheet.clear()
bst.settings.set_thermo(["Water", "Ethanol", "Glucose"])
print("BioSTEAM", bst.__version__)

# %% [markdown]
# ## 1. Build units that form a loop
#
# Fresh glucose is mixed with a **recycle** stream, fermented (glucose â†’ ethanol) at
# incomplete conversion, then a separator pulls out ethanol product and returns the
# unconverted glucose/water back to the mixer. That return path is the recycle.

# %%
fresh = bst.Stream("fresh", Glucose=100, Water=900, units="kmol/hr")
recycle = bst.Stream("recycle")           # empty for now; the loop fills it

M1 = bst.Mixer("M1", ins=(fresh, recycle), outs="mixed")

class Fermenter(bst.Unit):
    _N_ins = 1
    _N_outs = 1
    def __init__(self, ID="", ins=None, outs=(), thermo=None, *, X=0.7, T=305.15):
        super().__init__(ID, ins, outs, thermo)
        self.T = T   # fermentation temperature (32 C)
        self.reaction = Reaction("Glucose -> 2 Ethanol + 2 Water", reactant="Glucose", X=X)
    def _run(self):
        out = self.outs[0]
        out.copy_like(self.ins[0])
        self.reaction(out)
        out.T = self.T

R1 = Fermenter("R1", ins=M1-0, outs="broth", X=0.7)

# Split: 99% of ethanol leaves as product; unconverted glucose recycles.
S1 = bst.Splitter("S1", ins=R1-0, outs=("product", recycle),
                  split=dict(Ethanol=0.99, Water=0.5, Glucose=0.02))


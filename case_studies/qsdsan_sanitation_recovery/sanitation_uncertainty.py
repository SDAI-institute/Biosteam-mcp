# %% [markdown]
# # Case study â€” Sanitation & nutrient recovery under uncertainty (QSDsan)
#
# A resource-recovery sanitation step treats municipal wastewater and recovers N and P.
# Real recovery efficiencies and influent loads are *uncertain*, so we wrap the system
# in a `Model` and run Monte Carlo to get **distributions** of recovered phosphorus and
# effluent quality â€” the deliverable a sanitation designer actually reports.

# %%
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import chaospy as cp
import qsdsan as qs
import biosteam as bst

cmps = qs.Components.load_default()
qs.set_thermo(cmps)
print("QSDsan", qs.__version__)

# %% [markdown]
# ## System: influent + a nutrient-recovery SanUnit

# %%
inf = qs.WasteStream("influent")
inf.set_flow_by_concentration(
    flow_tot=1000,
    concentrations={"S_F": 200, "X_B_Subst": 150, "S_NH4": 40, "S_PO4": 8},
    units=("m3/hr", "mg/L"),
)

class NutrientRecovery(qs.SanUnit):
    _N_ins = 1
    _N_outs = 2
    def __init__(self, ID="", ins=None, outs=(), thermo=None,
                 init_with="WasteStream", *, N_recovery=0.6, P_recovery=0.8):
        super().__init__(ID, ins, outs, thermo, init_with=init_with)
        self.N_recovery = N_recovery
        self.P_recovery = P_recovery
    def _run(self):
        influent = self.ins[0]
        effluent, recovered = self.outs
        effluent.copy_like(influent)
        recovered.empty()
        for cmp, frac in (("S_NH4", self.N_recovery), ("S_PO4", self.P_recovery)):
            moved = influent.imass[cmp] * frac
            effluent.imass[cmp] -= moved
            recovered.imass[cmp] += moved

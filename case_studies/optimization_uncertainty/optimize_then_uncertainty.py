# %% [markdown]
# # Case study â€” Optimize, then quantify uncertainty
#
# The realistic expert workflow is two-stage: first **optimize** the design against a
# metric, then **quantify the uncertainty** of that metric *at the optimum* (not at the
# nominal design). This case study does both on an ethanol concentration process:
#
# 1. Optimize two operating variables (heater temperature, flash vapor fraction) to
#    minimize MSP.
# 2. Fix the optimum and run Monte Carlo over economic uncertainty â†’ MSP distribution.

# %%
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import chaospy as cp
import biosteam as bst
from scipy.optimize import differential_evolution

bst.main_flowsheet.clear()
bst.settings.set_thermo(["Water", "Ethanol"])
print("BioSTEAM", bst.__version__)

# %% [markdown]
# ## System + TEA

# %%
class ConventionalTEA(bst.TEA):
    def __init__(self, system, IRR=0.10, duration=(2020, 2040),
                 depreciation="MACRS7", income_tax=0.21, operating_days=330,
                 lang_factor=3.0, construction_schedule=(0.4, 0.6), WC_over_FCI=0.05,
                 labor_cost=2e6, fringe_benefits=0.4, property_tax=0.001,
                 property_insurance=0.005, maintenance=0.01, administration=0.005):
        super().__init__(system, IRR, duration, depreciation, income_tax,
                         operating_days, lang_factor, construction_schedule,
                         startup_months=0, startup_FOCfrac=0, startup_VOCfrac=0,
                         startup_salesfrac=0, WC_over_FCI=WC_over_FCI,
                         finance_interest=0, finance_years=0, finance_fraction=0)
        self.labor_cost = labor_cost; self.fringe_benefits = fringe_benefits
        self.property_tax = property_tax; self.property_insurance = property_insurance
        self.maintenance = maintenance; self.administration = administration
    def _FOC(self, FCI):
        return (FCI * (self.property_tax + self.property_insurance
                       + self.maintenance + self.administration)
                + self.labor_cost * (1 + self.fringe_benefits))

feed = bst.Stream("feed", Water=1000, Ethanol=500, units="kmol/hr", T=298.15, price=0.10)
H1 = bst.HXutility("H1", ins=feed, outs="hot", T=355)
F1 = bst.Flash("F1", ins=H1 - 0, outs=("vapor", "liquid"), V=0.5, P=101325)
P1 = bst.Pump("P1", ins=F1 - 1, outs="bottoms")
product = F1.outs[0]; product.price = 0.80
sys = bst.System.from_units("opt_sys", units=[H1, F1, P1])
sys.simulate()

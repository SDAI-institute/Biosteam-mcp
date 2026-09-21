# %% [markdown]
# # Tier 7 â€” Uncertainty & optimization
#
# Real studies report *ranges*, not single numbers, and often *optimize* a design.
# BioSTEAM's `Model` couples uncertain `Parameter`s to output `Metric`s so you can:
#
# 1. Run **Monte Carlo** over uncertain inputs â†’ a distribution of the metric.
# 2. Rank input importance with **Spearman** sensitivity.
# 3. **Optimize** a design variable against the metric.
#
# The same `Model` machinery is shared by QSDsan, so this pattern transfers directly.

# %%
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import chaospy as cp
import biosteam as bst
from scipy.optimize import minimize_scalar

bst.main_flowsheet.clear()
bst.settings.set_thermo(["Water", "Ethanol"])
print("BioSTEAM", bst.__version__, "| chaospy", cp.__version__)

# %% [markdown]
# ## 1. A system + TEA (from Tier 4)

# %%
class ConventionalTEA(bst.TEA):
    def __init__(self, system, IRR=0.10, duration=(2020, 2040),
                 depreciation="MACRS7", income_tax=0.21, operating_days=330,
                 lang_factor=3.0, construction_schedule=(0.4, 0.6),
                 WC_over_FCI=0.05, labor_cost=2e6, fringe_benefits=0.4,
                 property_tax=0.001, property_insurance=0.005,
                 maintenance=0.01, administration=0.005):
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
H1 = bst.HXutility("H1", ins=feed, outs="hot", T=360)
F1 = bst.Flash("F1", ins=H1 - 0, outs=("vapor", "liquid"), V=0.5, P=101325)
P1 = bst.Pump("P1", ins=F1 - 1, outs="bottoms")
product = F1.outs[0]; product.price = 0.80
sys = bst.System.from_units("mc_sys", units=[H1, F1, P1])
sys.simulate()
tea = ConventionalTEA(sys)
print(f"baseline MSP = ${tea.solve_price(product):.4f}/kg")

# %% [markdown]
# ## 2. Build a Model: one metric, three uncertain parameters
#

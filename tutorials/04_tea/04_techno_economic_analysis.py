# %% [markdown]
# # Tier 4 â€” Techno-economic analysis (TEA)
#
# TEA turns a simulated `System` into money: capital cost, operating cost, cash
# flows, and the **minimum selling price (MSP)** â€” the product price at which net
# present value is zero. This tier:
#
# 1. Subclasses `bst.TEA` (you implement `_FOC`; the rest have sane defaults).
# 2. Reads CAPEX (FCI), OPEX (FOC + VOC), NPV, and IRR.
# 3. Solves for MSP and runs a one-variable price sensitivity.

# %%
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import biosteam as bst

bst.main_flowsheet.clear()
bst.settings.set_thermo(["Water", "Ethanol"])
print("BioSTEAM", bst.__version__)

# %% [markdown]
# ## 1. A conventional TEA
#
# `bst.TEA` handles depreciation, taxes, working capital, and discounting. The only
# method you *must* provide is `_FOC` (fixed operating cost) â€” here labor plus
# capital-linked charges. Defaults for `_DPI/_TDC/_FCI` pass installed cost through.

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
        self.labor_cost = labor_cost
        self.fringe_benefits = fringe_benefits
        self.property_tax = property_tax
        self.property_insurance = property_insurance
        self.maintenance = maintenance
        self.administration = administration

    def _FOC(self, FCI):
        return (FCI * (self.property_tax + self.property_insurance
                       + self.maintenance + self.administration)
                + self.labor_cost * (1 + self.fringe_benefits))

# %% [markdown]
# ## 2. A small costed process
#

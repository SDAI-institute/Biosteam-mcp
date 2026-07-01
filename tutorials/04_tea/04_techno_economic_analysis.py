# %% [markdown]
# # Tier 4 — Techno-economic analysis (TEA)
#
# TEA turns a simulated `System` into money: capital cost, operating cost, cash
# flows, and the **minimum selling price (MSP)** — the product price at which net
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
# method you *must* provide is `_FOC` (fixed operating cost) — here labor plus
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
# Heat a feed, flash off an ethanol-rich vapor, pump the bottoms. Streams carry a
# `price`, so the TEA sees feedstock cost and product revenue.

# %%
feed = bst.Stream("feed", Water=1000, Ethanol=500, units="kmol/hr", T=298.15, price=0.10)
H1 = bst.HXutility("H1", ins=feed, outs="hot", T=360)
F1 = bst.Flash("F1", ins=H1 - 0, outs=("vapor", "liquid"), V=0.5, P=101325)
P1 = bst.Pump("P1", ins=F1 - 1, outs="bottoms")
product = F1.outs[0]
product.price = 0.80          # $/kg ethanol-rich vapor product

sys = bst.System.from_units("tea_sys", units=[H1, F1, P1])
sys.simulate()

# %% [markdown]
# ## 3. Build the TEA and read the headline economics

# %%
tea = ConventionalTEA(sys)
print(f"FCI  (capital)         = ${tea.FCI/1e6:,.2f} MM")
print(f"FOC  (fixed opex)      = ${tea.FOC/1e6:,.2f} MM/yr")
print(f"VOC  (variable opex)   = ${tea.VOC/1e6:,.2f} MM/yr")
print(f"annual sales           = ${tea.sales/1e6:,.2f} MM/yr")
print(f"NPV @ IRR={tea.IRR:.0%}       = ${tea.NPV/1e6:,.1f} MM")

# %% [markdown]
# ## 4. Minimum selling price (MSP)
#
# `solve_price` finds the product price that drives NPV to zero — the classic
# biorefinery metric, and the most robust one to report.
#
# > `solve_IRR` is the dual metric (the return at the current price), but it's only
# > meaningful when capital is realistic relative to throughput. This teaching toy has
# > negligible CAPEX (≈$0.36 MM) on a large stream, so its IRR blows up to nonsense —
# > we compute a believable IRR in the **cornstover case study** instead.

# %%
msp = tea.solve_price(product)
print(f"MSP (NPV=0)            = ${msp:,.4f}/kg")

# %% [markdown]
# ## 5. Cash-flow table
#
# The year-by-year cash-flow dataframe underlies every metric above.

# %%
cashflow = tea.get_cashflow_table()
print(cashflow.iloc[:6, :5])

# %% [markdown]
# ## 6. One-variable sensitivity: MSP vs feedstock price
#
# Sweep feedstock price and re-solve MSP — the simplest sensitivity, and a preview of
# the systematic `Model`-based uncertainty analysis in Tier 7.

# %%
feed_prices = np.linspace(0.05, 0.20, 6)
msps = []
for p in feed_prices:
    feed.price = p
    sys.simulate()
    msps.append(tea.solve_price(product))
feed.price = 0.10  # restore

for fp, m in zip(feed_prices, msps):
    print(f"  feed ${fp:.2f}/kg -> MSP ${m:.4f}/kg")
slope = (msps[-1] - msps[0]) / (feed_prices[-1] - feed_prices[0])
print(f"dMSP/dFeedPrice ~ {slope:.2f} (kg product per kg feed sensitivity)")

summary = {
    "FCI_MM": round(tea.FCI / 1e6, 2),
    "MSP_usd_per_kg": round(float(msp), 4),
    "dMSP_dFeedPrice": round(float(slope), 2),
}
print(summary)

# %% [markdown]
# ## You can now…
# - subclass `bst.TEA` (implement `_FOC`) and attach it to a system;
# - read FCI / FOC / VOC / NPV;
# - solve the **minimum selling price** and inspect the cash-flow table;
# - run a one-variable sensitivity.
#
# **Next — Tier 5 (`05_lca`)**: attach environmental impacts (characterization
# factors, allocation) to the same kind of system.
print("Tier 4 complete.")

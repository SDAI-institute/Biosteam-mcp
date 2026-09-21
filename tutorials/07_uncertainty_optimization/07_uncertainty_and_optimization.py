# %% [markdown]
# # Tier 7 — Uncertainty & optimization
#
# Real studies report *ranges*, not single numbers, and often *optimize* a design.
# BioSTEAM's `Model` couples uncertain `Parameter`s to output `Metric`s so you can:
#
# 1. Run **Monte Carlo** over uncertain inputs → a distribution of the metric.
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
# The metric is MSP. Parameters get chaospy **distributions**. Price parameters are
# *uncoupled* (no re-simulation needed); the flash vapor fraction is *coupled*
# (changes the mass balance, so the system re-simulates).

# %%
def get_MSP():
    return tea.solve_price(product)

model = bst.Model(sys, indicators=[bst.Metric("MSP", get_MSP, "USD/kg")])

@model.parameter(name="Feedstock price", element=feed, kind="isolated",
                 units="USD/kg", distribution=cp.Triangle(0.05, 0.10, 0.16))
def set_feed_price(price):
    feed.price = price

@model.parameter(name="Electricity price", element="TEA", kind="isolated",
                 units="USD/kWh", distribution=cp.Uniform(0.05, 0.12))
def set_power_price(price):
    bst.PowerUtility.price = price

@model.parameter(name="Flash vapor fraction", element=F1, coupled=True,
                 units="-", distribution=cp.Uniform(0.35, 0.65))
def set_V(V):
    F1.V = V

print("parameters:", [p.name for p in model.parameters])

# %% [markdown]
# ## 3. Monte Carlo
#
# Draw a Latin-hypercube sample, evaluate the model, and summarize the MSP
# distribution — the deliverable of an uncertainty analysis.

# %%
np.random.seed(42)
samples = model.sample(N=200, rule="L")
model.load_samples(samples)
model.evaluate()

msp_dist = np.asarray(model.table.iloc[:, -1], dtype=float)
p5, p50, p95 = np.percentile(msp_dist, [5, 50, 95])
print(f"MSP  mean = ${msp_dist.mean():.4f}/kg")
print(f"MSP  P5   = ${p5:.4f}/kg")
print(f"MSP  P50  = ${p50:.4f}/kg")
print(f"MSP  P95  = ${p95:.4f}/kg")
print(f"90% interval width = ${p95 - p5:.4f}/kg")

# %% [markdown]
# ## 4. Spearman sensitivity
#
# Spearman rank correlation between each parameter and MSP ranks the drivers of
# uncertainty (the classic "tornado" ordering). |ρ| near 1 = dominant driver.

# %%
rho, pvalues = model.spearman_r()      # two DataFrames: rho and p-values
rho.columns = ["Spearman rho vs MSP"]
ranked = rho.reindex(rho["Spearman rho vs MSP"].abs().sort_values(ascending=False).index)
print(ranked.round(3))

# %% [markdown]
# ## 5. Optimization
#
# Find the flash vapor fraction that *minimizes* MSP. `minimize_scalar` drives a
# bounded search; each trial re-simulates and re-solves the TEA.

# %%
def msp_at_V(V):
    F1.V = float(V)
    sys.simulate()
    return tea.solve_price(product)

opt = minimize_scalar(msp_at_V, bounds=(0.35, 0.65), method="bounded")
F1.V = 0.5; sys.simulate()   # restore baseline
print(f"optimal V*   = {opt.x:.3f}")
print(f"MSP at V*    = ${opt.fun:.4f}/kg")

summary = {
    "MSP_P50_usd_kg": round(float(p50), 4),
    "MSP_P90_width": round(float(p95 - p5), 4),
    "top_driver": ranked.index[0][-1],
    "optimal_V": round(float(opt.x), 3),
}
print(summary)

# %% [markdown]
# ## You can now…
# - build a `Model` with `Parameter`s (chaospy distributions) and `Metric`s;
# - run Monte Carlo and report a metric distribution (P5/P50/P95);
# - rank uncertainty drivers with Spearman sensitivity;
# - optimize a design variable against a metric.
#
# **Next — Tier 8 (`08_expert_integration`)**: cross-framework BioSTEAM↔QSDsan, custom
# property packages, and the clean API surface the MCP server will expose.
print("Tier 7 complete.")

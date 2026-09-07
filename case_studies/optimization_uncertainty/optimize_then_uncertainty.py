# %% [markdown]
# # Case study — Optimize, then quantify uncertainty
#
# The realistic expert workflow is two-stage: first **optimize** the design against a
# metric, then **quantify the uncertainty** of that metric *at the optimum* (not at the
# nominal design). This case study does both on an ethanol concentration process:
#
# 1. Optimize two operating variables (heater temperature, flash vapor fraction) to
#    minimize MSP.
# 2. Fix the optimum and run Monte Carlo over economic uncertainty → MSP distribution.

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
tea = ConventionalTEA(sys)
msp0 = tea.solve_price(product)
print(f"baseline (T=355 K, V=0.50) MSP = ${msp0:.4f}/kg")

# %% [markdown]
# ## Stage 1 — optimize (heater T, flash V) to minimize MSP
#
# A bounded 2-variable minimization. The surface is flat/noisy near the nominal point,
# so a gradient method stalls — we use gradient-free `differential_evolution`, which
# reliably finds the real optimum. Every trial re-simulates and re-solves the TEA.

# %%
def msp_at(x):
    T, V = x
    H1.T = float(T)
    F1.V = float(V)
    try:
        sys.simulate()
        return tea.solve_price(product)
    except Exception:
        return 1e3      # penalize infeasible points

bounds = [(345.0, 372.0), (0.35, 0.65)]
opt = differential_evolution(msp_at, bounds, seed=1, maxiter=20, tol=1e-5,
                             polish=True, updating="deferred")
T_opt, V_opt = opt.x
H1.T, F1.V = T_opt, V_opt
sys.simulate()
msp_opt = tea.solve_price(product)
print(f"optimal T* = {T_opt:.1f} K,  V* = {V_opt:.3f}")
print(f"optimal MSP = ${msp_opt:.4f}/kg  (improved ${msp0 - msp_opt:.4f}/kg vs baseline)")

# %% [markdown]
# ## Stage 2 — uncertainty at the optimum
#
# Hold the optimized design; vary the *economic* inputs (feed price, electricity, IRR)
# and report the MSP distribution the project would actually face.

# %%
def get_MSP():
    return tea.solve_price(product)

model = bst.Model(sys, indicators=[bst.Metric("MSP", get_MSP, "USD/kg")])

@model.parameter(name="Feedstock price", element=feed, kind="isolated",
                 distribution=cp.Triangle(0.05, 0.10, 0.16))
def _p_feed(p): feed.price = p

@model.parameter(name="Electricity price", element="TEA", kind="isolated",
                 distribution=cp.Uniform(0.05, 0.12))
def _p_pow(p): bst.PowerUtility.price = p

@model.parameter(name="Target IRR", element="TEA", kind="isolated",
                 distribution=cp.Uniform(0.08, 0.15))
def _p_irr(r): tea.IRR = r

np.random.seed(11)
samples = model.sample(N=250, rule="L")
model.load_samples(samples)
model.evaluate()
msp_dist = np.asarray(model.table.iloc[:, -1], dtype=float)
p5, p50, p95 = np.percentile(msp_dist, [5, 50, 95])
print(f"MSP at optimum: P5=${p5:.4f}  P50=${p50:.4f}  P95=${p95:.4f} /kg")

rho, _ = model.spearman_r()
rho.columns = ["rho"]
ranked = rho.reindex(rho["rho"].abs().sort_values(ascending=False).index)
print("drivers of remaining MSP uncertainty:")
print(ranked.round(3))

results = {
    "baseline_MSP": round(float(msp0), 4),
    "optimal_T_K": round(float(T_opt), 1),
    "optimal_V": round(float(V_opt), 3),
    "optimal_MSP": round(float(msp_opt), 4),
    "MSP_P50_at_opt": round(float(p50), 4),
    "MSP_P90_range": [round(float(p5), 4), round(float(p95), 4)],
}
print(results)
print("Optimization + uncertainty case study complete.")

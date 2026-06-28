# %% [markdown]
# # Tier 5 — Life-cycle assessment (LCA)
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
# Glucose → ethanol + CO2, then a pump (draws electricity) and a flash concentrate.

# %%
class Fermenter(bst.Unit):
    _N_ins = 1
    _N_outs = 1
    def __init__(self, ID="", ins=None, outs=(), thermo=None, *, X=0.9):
        super().__init__(ID, ins, outs, thermo)
        self.reaction = Reaction("Glucose -> 2 Ethanol + 2 CO2", reactant="Glucose", X=X)
    def _run(self):
        out = self.outs[0]
        out.copy_like(self.ins[0])
        self.reaction(out)
        out.T = 305.15

R1 = Fermenter("R1", ins=feed, outs="broth", X=1.0)   # complete conversion (keeps the flash off solid glucose)
P1 = bst.Pump("P1", ins=R1 - 0, outs="pumped", P=3e5)
F1 = bst.Flash("F1", ins=P1 - 0, outs=("vapor", "beer"), V=0.3, P=101325)

sys = bst.System.from_units("lca_sys", units=[R1, P1, F1])
sys.simulate()

# The impact aggregators return *annual* impacts, so the system needs operating
# hours. 330 days/yr is the biorefinery convention.
OPERATING_HOURS = 24 * 330
sys.operating_hours = OPERATING_HOURS

# Ethanol leaves in both vapor and beer; total ethanol mass produced:
ethanol_kg = sum(s.imass["Ethanol"] for s in (F1.outs[0], F1.outs[1]))     # kg/hr
co2_kg = sum(s.imass["CO2"] for s in (F1.outs[0], F1.outs[1]))             # kg/hr
ethanol_annual = ethanol_kg * OPERATING_HOURS                              # kg/yr
print(f"ethanol produced = {ethanol_kg:,.0f} kg/hr  ({ethanol_annual/1e6:,.1f} kt/yr)")
print(f"CO2 produced     = {co2_kg:,.0f} kg/hr")

# %% [markdown]
# ## 3. Aggregate the life-cycle impact
#
# `get_total_feeds_impact` sums feed CFs; `get_net_electricity_impact` covers power.
# Both are **annual**; their sum is the system's gross GWP per year.

# %%
feeds_gwp = sys.get_total_feeds_impact(GWP)          # kg CO2e/yr
power_gwp = sys.get_net_electricity_impact(GWP)      # kg CO2e/yr
total_gwp = feeds_gwp + power_gwp
print(f"feeds GWP        = {feeds_gwp/1e6:,.2f} kt CO2e/yr")
print(f"electricity GWP  = {power_gwp/1e6:,.2f} kt CO2e/yr")
print(f"total gross GWP  = {total_gwp/1e6:,.2f} kt CO2e/yr")
print(f"GWP intensity    = {total_gwp/ethanol_annual:,.3f} kg CO2e / kg ethanol")

# %% [markdown]
# ## 4. Allocation between ethanol and CO2 co-product
#
# When a process makes more than one saleable output, total impact must be *allocated*.
# Three common bases give three different ethanol footprints — allocation choice is a
# reported LCA decision, not a detail.

# %%
# Mass allocation
mass_frac = ethanol_kg / (ethanol_kg + co2_kg)
# Energy allocation (LHV proxy: ethanol ~26.8 MJ/kg, CO2 ~0)
E_eth, E_co2 = 26.8, 0.0
energy_frac = (ethanol_kg * E_eth) / (ethanol_kg * E_eth + co2_kg * E_co2)
# Economic allocation (prices: ethanol 0.80, CO2 0.05 $/kg)
p_eth, p_co2 = 0.80, 0.05
econ_frac = (ethanol_kg * p_eth) / (ethanol_kg * p_eth + co2_kg * p_co2)

for name, frac in [("mass", mass_frac), ("energy", energy_frac), ("economic", econ_frac)]:
    allocated = total_gwp * frac / ethanol_annual
    print(f"{name:9s} allocation -> {allocated:,.3f} kg CO2e / kg ethanol  (frac={frac:.2f})")

summary = {
    "gross_GWP_kt_per_yr": round(float(total_gwp) / 1e6, 2),
    "ethanol_GWP_mass_alloc": round(float(total_gwp * mass_frac / ethanol_annual), 3),
    "ethanol_GWP_energy_alloc": round(float(total_gwp * energy_frac / ethanol_annual), 3),
}
print(summary)

# %% [markdown]
# ## You can now…
# - define an impact indicator and set CFs on streams and electricity;
# - aggregate a system's life-cycle impact (`get_total_feeds_impact`,
#   `get_net_electricity_impact`);
# - express impact per unit product and apply mass / energy / economic **allocation**.
#
# This connects to your wider ecosystem: BioSTEAM gives the foreground inventory;
# openLCA / Brightway supply background CFs. The **cross-framework LCA case study**
# reconciles the two.
#
# **Next — Tier 6 (`06_qsdsan`)**: QSDsan for sanitation & resource-recovery systems.
print("Tier 5 complete.")

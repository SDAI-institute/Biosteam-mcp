# %% [markdown]
# # Case study — Cross-framework LCA
#
# LCA splits into a **foreground** (the process you model) and a **background** (grid
# electricity, chemical production, transport — supplied by databases like ecoinvent
# via openLCA or Brightway). BioSTEAM produces the foreground *inventory*; the
# background contributes *characterization factors (CFs)*.
#
# This case study:
# 1. Extracts a foreground inventory from a BioSTEAM system.
# 2. Applies a background CF table (a stand-in for an openLCA/Brightway lookup).
# 3. Reconciles BioSTEAM's built-in aggregation against an independent calculation —
#    they must agree, which is how you trust a coupled BioSTEAM ↔ openLCA workflow.

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
# ## 1. A foreground process (fermentation → concentration)

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
F1 = bst.Flash("F1", ins=P1 - 0, outs=("vapor", "beer"), V=0.3, P=101325)
sys = bst.System.from_units("fg_sys", units=[R1, P1, F1])
sys.simulate()
sys.operating_hours = 24 * 330

# %% [markdown]
# ## 2. Background CF table (stand-in for an openLCA / Brightway lookup)
#
# In production these come from your database ecosystem. Here we hard-code
# representative cradle-to-gate GWP factors and attach them.

# %%
BACKGROUND_CF = {           # kg CO2e per kg (streams) / per kWh (electricity)
    "glucose_feed": 1.20,
    "electricity": 0.45,
}
feed.set_CF(GWP, BACKGROUND_CF["glucose_feed"])
bst.PowerUtility.set_CF(GWP, BACKGROUND_CF["electricity"])

# %% [markdown]
# ## 3a. BioSTEAM's built-in aggregation

# %%
feeds_gwp = sys.get_total_feeds_impact(GWP)         # kg CO2e/yr
power_gwp = sys.get_net_electricity_impact(GWP)     # kg CO2e/yr
biosteam_total = feeds_gwp + power_gwp
print(f"BioSTEAM feeds GWP  = {feeds_gwp/1e6:,.3f} kt/yr")
print(f"BioSTEAM power GWP  = {power_gwp/1e6:,.3f} kt/yr")
print(f"BioSTEAM TOTAL      = {biosteam_total/1e6:,.3f} kt/yr")

# %% [markdown]
# ## 3b. Independent inventory × CF calculation
#
# Pull the foreground inventory ourselves and multiply by the CF table — exactly what
# an external tool (openLCA/Brightway) would do with the same inventory.

# %%
hours = sys.operating_hours
inventory = {
    "glucose_feed": feed.F_mass * hours,                              # kg/yr
    "electricity": sum(u.power_utility.rate for u in sys.units
                       if u.power_utility) * hours,                   # kWh/yr
}
manual_total = sum(inventory[k] * BACKGROUND_CF[k] for k in inventory)
print("Foreground inventory (per yr):")
for k, v in inventory.items():
    print(f"  {k:14s} {v:14,.0f}  x CF {BACKGROUND_CF[k]:.2f}  = {v*BACKGROUND_CF[k]/1e6:,.3f} kt CO2e")
print(f"independent TOTAL   = {manual_total/1e6:,.3f} kt/yr")

# %% [markdown]
# ## 4. Reconciliation
#
# The two paths must match to within rounding — proof the foreground inventory and CF
# application are consistent, so results are portable between BioSTEAM and openLCA/BW.

# %%
rel_err = abs(biosteam_total - manual_total) / biosteam_total
print(f"relative difference = {rel_err:.2e}")
print(f"reconciled: {rel_err < 1e-6}")

results = {
    "biosteam_total_kt_yr": round(float(biosteam_total) / 1e6, 3),
    "independent_total_kt_yr": round(float(manual_total) / 1e6, 3),
    "reconciled": bool(rel_err < 1e-6),
}
print(results)
print("Cross-framework LCA case study complete.")

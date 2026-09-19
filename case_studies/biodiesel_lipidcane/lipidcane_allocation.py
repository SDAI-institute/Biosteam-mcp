# %% [markdown]
# # Case study — Lipidcane → biodiesel (co-product allocation & TEA)
#
# Lipidcane is engineered sugarcane accumulating oil; the biorefinery makes **biodiesel
# and ethanol** together (plus electricity). Multiple saleable products make this the
# natural case for **allocation** — the same total impact splits differently by mass,
# energy, or economic value. We also read its techno-economics.

# %%
import warnings
warnings.filterwarnings("ignore")

from biorefineries import lipidcane as lc

lc.load()
sys = lc.lipidcane_sys
tea = lc.lipidcane_tea
biodiesel, ethanol = lc.biodiesel, lc.ethanol
print("units in system:", len(sys.units))

# %% [markdown]
# ## Co-products and techno-economics

# %%
bd_kg, et_kg = biodiesel.F_mass, ethanol.F_mass
print(f"biodiesel = {bd_kg:,.0f} kg/hr")
print(f"ethanol   = {et_kg:,.0f} kg/hr")
print(f"IRR             = {tea.solve_IRR():.1%}")
print(f"FCI             = ${tea.FCI/1e6:,.1f} MM")
print(f"MSP biodiesel   = ${tea.solve_price(biodiesel):.4f}/kg")

# %% [markdown]
# ## Allocation between biodiesel and ethanol
#
# Suppose the process carries a total upstream GWP `G` (kg CO2e/hr). How much belongs
# to biodiesel? It depends entirely on the allocation basis.

# %%
G = 40_000.0     # illustrative total system GWP, kg CO2e/hr

# Mass basis
mass_frac = bd_kg / (bd_kg + et_kg)
# Energy basis (LHV: biodiesel ~37.5 MJ/kg, ethanol ~26.8 MJ/kg)
LHV_bd, LHV_et = 37.5, 26.8
energy_frac = (bd_kg * LHV_bd) / (bd_kg * LHV_bd + et_kg * LHV_et)
# Economic basis (prices: biodiesel 1.38, ethanol 0.72 $/kg)
p_bd, p_et = 1.38, 0.72
econ_frac = (bd_kg * p_bd) / (bd_kg * p_bd + et_kg * p_et)

print("Biodiesel's share of impact and its per-kg footprint:")
for name, frac in [("mass", mass_frac), ("energy", energy_frac), ("economic", econ_frac)]:
    per_kg = G * frac / bd_kg
    print(f"  {name:9s}: {frac:5.1%} of total  ->  {per_kg:.3f} kg CO2e / kg biodiesel")

# %% [markdown]
# The spread across bases is the point: allocation choice materially changes the
# reported biodiesel footprint, so it must be stated explicitly in any LCA.

# %%
results = {
    "biodiesel_kg_hr": round(float(bd_kg), 0),
    "ethanol_kg_hr": round(float(et_kg), 0),
    "IRR": round(float(tea.solve_IRR()), 3),
    "MSP_biodiesel_usd_kg": round(float(tea.solve_price(biodiesel)), 4),
    "biodiesel_mass_alloc_frac": round(float(mass_frac), 3),
    "biodiesel_energy_alloc_frac": round(float(energy_frac), 3),
    "biodiesel_economic_alloc_frac": round(float(econ_frac), 3),
}
print(results)
print("Lipidcane case study complete.")

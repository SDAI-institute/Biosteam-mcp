# %% [markdown]
# # Case study â€” Lipidcane â†’ biodiesel (co-product allocation & TEA)
#
# Lipidcane is engineered sugarcane accumulating oil; the biorefinery makes **biodiesel
# and ethanol** together (plus electricity). Multiple saleable products make this the
# natural case for **allocation** â€” the same total impact splits differently by mass,
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

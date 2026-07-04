# %% [markdown]
# # Tier 3 — Systems, flowsheets, and recycle convergence
#
# A `System` sequences units and **solves recycle loops** to a consistent steady
# state. This tier builds a system with a real recycle and watches it converge.
#
# 1. The flowsheet registry (how units/streams are named and found).
# 2. A recycle loop: reactor → separator → recycle the unreacted feed.
# 3. Convergence: what "the recycle stream stopped changing" means numerically.
# 4. Process specifications (`@u.add_specification`).

# %%
import warnings
warnings.filterwarnings("ignore")

import biosteam as bst
from thermosteam.reaction import Reaction

bst.main_flowsheet.clear()
bst.settings.set_thermo(["Water", "Ethanol", "Glucose"])
print("BioSTEAM", bst.__version__)

# %% [markdown]
# ## 1. Build units that form a loop
#
# Fresh glucose is mixed with a **recycle** stream, fermented (glucose → ethanol) at
# incomplete conversion, then a separator pulls out ethanol product and returns the
# unconverted glucose/water back to the mixer. That return path is the recycle.

# %%
fresh = bst.Stream("fresh", Glucose=100, Water=900, units="kmol/hr")
recycle = bst.Stream("recycle")           # empty for now; the loop fills it

M1 = bst.Mixer("M1", ins=(fresh, recycle), outs="mixed")

class Fermenter(bst.Unit):
    _N_ins = 1
    _N_outs = 1
    def __init__(self, ID="", ins=None, outs=(), thermo=None, *, X=0.7, T=305.15):
        super().__init__(ID, ins, outs, thermo)
        self.T = T   # fermentation temperature (32 C)
        self.reaction = Reaction("Glucose -> 2 Ethanol + 2 Water", reactant="Glucose", X=X)
    def _run(self):
        out = self.outs[0]
        out.copy_like(self.ins[0])
        self.reaction(out)
        out.T = self.T

R1 = Fermenter("R1", ins=M1-0, outs="broth", X=0.7)

# Split: 99% of ethanol leaves as product; unconverted glucose recycles.
S1 = bst.Splitter("S1", ins=R1-0, outs=("product", recycle),
                  split=dict(Ethanol=0.99, Water=0.5, Glucose=0.02))

# %% [markdown]
# ## 2. Assemble the System — BioSTEAM finds the recycle automatically
#
# Passing the units (or just the feed) lets BioSTEAM trace connectivity, detect the
# recycle loop, and choose a solve order.

# %%
sys = bst.System.from_units("ferm_sys", units=[M1, R1, S1])
print("units in solve order:", [u.ID for u in sys.units])
print("recycle stream(s):", [s.ID for s in (sys.recycle if isinstance(sys.recycle, list) else [sys.recycle])])

# %% [markdown]
# ## 3. Simulate and read convergence
#
# `simulate()` iterates the loop until the recycle stream is self-consistent.

# %%
sys.simulate()
product = S1.outs[0]
print(f"ethanol product = {product.imol['Ethanol']:.1f} kmol/hr")
print(f"glucose in recycle = {recycle.imol['Glucose']:.2f} kmol/hr")
sys.show()

# %% [markdown]
# ## 4. Overall conversion is higher than one pass
#
# Recycling unconverted glucose raises overall conversion above the single-pass 70%.

# %%
fresh_glucose = fresh.imol["Glucose"]
lost_glucose = product.imol["Glucose"]        # glucose leaving unconverted in product
overall_conversion = 1 - lost_glucose / fresh_glucose
print(f"single-pass conversion : 70%")
print(f"overall conversion     : {100*overall_conversion:.1f}%")

# %% [markdown]
# ## 5. Process specifications
#
# A **specification** runs custom logic every time a unit simulates, *before* its
# built-in `_run` (`run=True`). Here a spec raises single-pass conversion to 80%.
#
# Watch what *doesn't* happen: total ethanol barely moves (198→199 kmol/hr). Because
# the recycle already returns unconverted glucose, **overall** conversion is ~99%
# regardless of single-pass X — so the bottleneck is the recycle/separation, not the
# reactor. That is the kind of insight a system-level model gives you that a single
# unit cannot.

# %%
ethanol_before = product.imol["Ethanol"]

@R1.add_specification(run=True)
def boost_conversion():
    R1.reaction.X = 0.80

sys.simulate()
ethanol_after = product.imol["Ethanol"]
print(f"ethanol at X=0.70 : {ethanol_before:.1f} kmol/hr")
print(f"ethanol at X=0.80 : {ethanol_after:.1f} kmol/hr  (spec-driven)")
print(f"fermenter outlet T = {R1.outs[0].T:.2f} K (held at 32 C by the unit)")

summary = {
    "ethanol_kmol_hr": round(float(ethanol_after), 1),
    "overall_conversion_pct": round(100 * float(overall_conversion), 1),
    "n_units": len(sys.units),
}
print(summary)

# %% [markdown]
# ## You can now…
# - build units that form a recycle loop and let `System.from_units` find it;
# - simulate to convergence and read steady-state recycle flows;
# - reason about single-pass vs overall conversion;
# - attach a process `specification`.
#
# > Diagrams: `sys.diagram()` renders a flowsheet (needs the Graphviz `dot`
# > executable on PATH). It's omitted from this executed notebook so it runs
# > anywhere; try it locally once Graphviz is installed.
#
# **Next — Tier 4 (`04_tea`)**: put economics on a system — CAPEX, OPEX, and the
# minimum selling price.
print("Tier 3 complete.")

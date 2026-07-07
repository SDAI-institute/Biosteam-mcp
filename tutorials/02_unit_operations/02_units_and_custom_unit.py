# %% [markdown]
# # Tier 2 â€” Unit operations
#
# Units are the equipment that transform streams. This tier covers:
#
# 1. Built-in units: a reactor (with a `Reaction`), a heat exchanger, and a
#    distillation column.
# 2. How units carry **design** and **purchase-cost** results after simulation.
# 3. Writing your own **custom `Unit`** subclass.

# %%
import warnings
warnings.filterwarnings("ignore")

import biosteam as bst
import thermosteam as tmo
from thermosteam.reaction import Reaction

bst.settings.set_thermo(["Water", "Ethanol", "AceticAcid", "EthylAcetate", "Glycerol"])
print("BioSTEAM", bst.__version__)

# %% [markdown]
# ## 1. A reaction inside a custom unit
#
# thermosteam's `Reaction` describes stoichiometry + conversion. Esterification:
# acetic acid + ethanol â†’ ethyl acetate + water. We'll wrap it in a **custom Unit**
# to show the pattern you'll reuse for any bespoke equipment.
#
# A `Unit` subclass declares inlet/outlet counts and implements `_run` (the mass/
# energy balance). Optionally `_design` and `_cost` add sizing and purchase cost.

# %%
class Esterifier(bst.Unit):
    """Isothermal esterification reactor with a fixed acetic-acid conversion."""
    _N_ins = 1
    _N_outs = 1

    def __init__(self, ID="", ins=None, outs=(), thermo=None, *, conversion=0.6, T=353.15):
        super().__init__(ID, ins, outs, thermo)
        self.conversion = conversion
        self.T = T
        self.reaction = Reaction(
            "AceticAcid + Ethanol -> EthylAcetate + Water",
            reactant="AceticAcid", X=conversion,
        )

    def _run(self):
        effluent = self.outs[0]
        effluent.copy_like(self.ins[0])

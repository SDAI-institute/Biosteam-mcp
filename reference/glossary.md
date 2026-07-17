# Glossary

Core vocabulary across process modeling, TEA, and LCA.

## Process modeling
- **thermosteam** â€” the thermodynamic engine (chemicals, property packages, streams,
  equilibrium) BioSTEAM is built on.
- **Chemical / Chemicals** â€” a species and its properties / a property package.
- **Stream** â€” flowing material: molar flows plus a state (T, P, phase).
- **Unit** â€” equipment that transforms streams (reactor, column, HX, pumpâ€¦).
- **System** â€” units wired together and solved, including **recycle** loops.
- **Recycle / convergence** â€” a stream fed back upstream; the system iterates until it
  is self-consistent.
- **Specification** â€” custom logic run when a unit simulates, to encode operating policy.
- **VLE** â€” vaporâ€“liquid equilibrium; the basis of flashing and distillation.
- **Azeotrope** â€” a composition where vapor and liquid are equal, capping ordinary
  distillation purity.

## Techno-economics (TEA)
- **CAPEX / FCI** â€” capital expenditure / fixed capital investment.
- **Installed equipment cost** â€” purchase cost Ã— installation factors.
- **OPEX** â€” operating expenditure = **FOC** (fixed: labor, maintenance, insurance) +

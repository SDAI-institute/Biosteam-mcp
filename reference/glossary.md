# Glossary

Core vocabulary across process modeling, TEA, and LCA.

## Process modeling
- **thermosteam** — the thermodynamic engine (chemicals, property packages, streams,
  equilibrium) BioSTEAM is built on.
- **Chemical / Chemicals** — a species and its properties / a property package.
- **Stream** — flowing material: molar flows plus a state (T, P, phase).
- **Unit** — equipment that transforms streams (reactor, column, HX, pump…).
- **System** — units wired together and solved, including **recycle** loops.
- **Recycle / convergence** — a stream fed back upstream; the system iterates until it
  is self-consistent.
- **Specification** — custom logic run when a unit simulates, to encode operating policy.
- **VLE** — vapor–liquid equilibrium; the basis of flashing and distillation.
- **Azeotrope** — a composition where vapor and liquid are equal, capping ordinary
  distillation purity.

## Techno-economics (TEA)
- **CAPEX / FCI** — capital expenditure / fixed capital investment.
- **Installed equipment cost** — purchase cost × installation factors.
- **OPEX** — operating expenditure = **FOC** (fixed: labor, maintenance, insurance) +
  **VOC** (variable: feedstocks, utilities).
- **NPV** — net present value of discounted cash flows.
- **IRR** — internal rate of return (discount rate giving NPV = 0).
- **MSP / MPSP** — minimum (product) selling price: the price that makes NPV = 0 at the
  target IRR. The headline biorefinery metric.
- **MACRS** — the U.S. accelerated depreciation schedule.

## Life-cycle assessment (LCA)
- **Foreground** — the process you model (BioSTEAM supplies this inventory).
- **Background** — upstream supply chains (grid power, chemical production) from
  databases like ecoinvent via **openLCA** / **Brightway**.
- **Characterization factor (CF)** — impact per unit of a flow (e.g. kg CO₂e/kg).
- **GWP** — global warming potential (kg CO₂e).
- **Allocation** — splitting shared impact among co-products by **mass**, **energy**
  (LHV), or **economic** value. The basis materially changes results and must be stated.
- **Displacement / substitution** — crediting a co-product for impacts it avoids
  elsewhere (an alternative to allocation).

## Uncertainty & optimization
- **Model / Parameter / Metric (Indicator)** — BioSTEAM's uncertainty harness: outputs
  (Metrics) as functions of uncertain inputs (Parameters).
- **Monte Carlo** — sampling inputs to get output distributions (report P5/P50/P95).
- **Latin hypercube** (`rule="L"`) — a space-filling sampling scheme.
- **Spearman rank correlation (ρ)** — ranks input importance (tornado ordering).

## QSDsan
- **QSDsan** — quantitative sustainable design for sanitation & resource recovery,
  built on BioSTEAM.
- **WasteStream** — a stream with wastewater composite variables.
- **Composite variables** — COD, BOD, TN (total N), TP (total P), TSS — aggregate
  wastewater quality indicators.
- **SanUnit** — a QSDsan unit operation (`qs.SanUnit`).
- **ASM / ADM** — Activated Sludge / Anaerobic Digestion Models (dynamic process models).
- **EXPOsan** — the library of validated QSDsan example systems.

"""Tool wrappers over the BioSTEAM engine.

Each tool is a thin async adapter: validate read-only mode where relevant, offload the
blocking engine call, and return its ``{success, ...}`` envelope unchanged. Registered
on the shared ``mcp`` object via the decorators from ``app.py``.
"""

from __future__ import annotations

from typing import Any, Optional

from .app import (
    NATIVE_TASKS_ENABLED,
    engine,
    guard_readonly,
    mutate_tool,
    offload,
    read_tool,
)
from .job_runtime import jobs
from .schemas import arr


@read_tool(
    "list_biorefinery_models",
    "List published BioSTEAM biorefinery models that build_system can load.",
    {"models": arr({"type": "string"})},
)
async def list_biorefinery_models() -> dict:
    return await offload(engine.list_biorefinery_models)


@mutate_tool(
    "build_system",
    "Load a published biorefinery by name (e.g. 'cornstover', 'lipidcane') and register "
    "it. Returns a result_id plus a summary (units, feeds, products, installed cost).",
    {"result_id": {"type": "string"}, "summary": {"type": "object"}},
)
async def build_system(model_name: str) -> dict:
    if (blocked := guard_readonly()):
        return blocked
    return await offload(engine.build_system, model_name)


@mutate_tool(
    "build_system_from_spec",
    "Build a custom flowsheet from a JSON spec instead of a named biorefinery. "
    "spec = {thermo:[chemicals], thermo_model?:'default'|'ideal', "
    "streams:[{id, flows:{chem:amount}, units?, T?, P?, price?}], "
    "units:[{type, id, ins:[stream_id], outs:[new_stream_id], params:{}}], product?, "
    "attach_tea?}. `ideal` explicitly uses ideal activity/fugacity coefficients and "
    "mock Poynting correction for Raoult-law validation. Unit `type` is a BioSTEAM "
    "class name (e.g. 'Flash', 'HXutility', 'Pump', 'Mixer', 'BinaryDistillation'). "
    "Returns a result_id, summary, and the installed thermo-model metadata.",
    {"result_id": {"type": "string"}, "summary": {"type": "object"},
     "thermo": {"type": "object"}},
)
async def build_system_from_spec(spec: dict[str, Any]) -> dict:
    if (blocked := guard_readonly()):
        return blocked
    return await offload(engine.build_system_from_spec, spec)


@mutate_tool(
    "build_sanitation_system",
    "Build a QSDsan wastewater / nutrient-recovery system. spec = {flow_tot (m3/hr), "
    "concentrations:{component: mg/L} (e.g. S_F, X_B_Subst, S_NH4, S_PO4), N_recovery, "
    "P_recovery}. Returns a result_id and influent composite variables (COD/BOD/TN/TP). "
    "Use get_wastewater_results for removal + recovery.",
    {"result_id": {"type": "string"}, "summary": {"type": "object"}},
)
async def build_sanitation_system(spec: dict[str, Any]) -> dict:
    if (blocked := guard_readonly()):
        return blocked
    return await offload(engine.build_sanitation_system, spec)


@read_tool(
    "get_wastewater_results",
    "For a sanitation system: influent/effluent composite variables (COD, BOD, TN, TP), "
    "removal efficiency (%), and recovered nutrient mass (kg/hr).",
    {"influent": {"type": "object"}, "effluent": {"type": "object"},
     "removal_pct": {"type": "object"}, "recovered_kg_hr": {"type": "object"}},
)
async def get_wastewater_results(result_id: str) -> dict:
    return await offload(engine.get_wastewater_results, result_id)


@mutate_tool(
    "simulate_system",
    "Re-simulate a built system by result_id. Returns convergence summary "
    "(units, feeds, products, installed cost).",
)
async def simulate_system(result_id: str) -> dict:
    if (blocked := guard_readonly()):
        return blocked
    return await offload(engine.simulate_system, result_id)


@read_tool(
    "get_stream_results",
    "Inspect one stream in a built system for validation: phase, temperature (K), "
    "pressure (Pa), total/component mass flow (kg/hr), total/component molar flow "
    "(kmol/hr), volumetric flow (m3/hr), and enthalpy (kJ/hr).",
    {"stream": {"type": "object"}},
)
async def get_stream_results(result_id: str, stream_id: str) -> dict:
    return await offload(engine.get_stream_results, result_id, stream_id)


@read_tool(
    "get_vle_results",
    "Calculate bubble/dew equilibrium at a specified pressure for one stored stream's "
    "overall composition. Returns component order, overall mole fractions, bubble/dew "
    "temperatures (K), and liquid/vapor mole fractions. Read-only; intended for "
    "thermodynamic validation and experimental VLE comparison.",
    {"vle": {"type": "object"}},
)
async def get_vle_results(result_id: str, stream_id: str, pressure_Pa: float) -> dict:
    return await offload(engine.get_vle_results, result_id, stream_id, pressure_Pa)


@read_tool(
    "get_unit_results",
    "Inspect one unit operation without mutating the system: unit type, connected streams, "
    "unit-model-specific design results, power utility (kW and USD/hr), heat utilities, "
    "and purchase/installed costs. Interpret design-result names using the underlying "
    "BioSTEAM unit model rather than assuming cross-engine semantic equivalence.",
    {"unit": {"type": "object"}},
)
async def get_unit_results(result_id: str, unit_id: str) -> dict:
    return await offload(engine.get_unit_results, result_id, unit_id)


@read_tool(
    "get_tea_results",
    "Techno-economics of a built system: FCI, FOC, VOC, NPV, and the product's minimum "
    "selling price (MSP).",
    {"tea": {"type": "object"}},
)
async def get_tea_results(result_id: str) -> dict:
    return await offload(engine.get_tea_results, result_id)


@read_tool(
    "get_lca_results",
    "Foreground life-cycle impact of a built system for one indicator (e.g. 'GWP'). "
    "Provide background characterization factors as `cfs`: a map from feed-stream ID "
    "(and optionally 'electricity') to a per-kg / per-kWh factor. Returns the total and "
    "a per-flow breakdown (annual).",
    {"indicator": {"type": "string"}, "total": {"type": "number"}, "breakdown": {"type": "object"}},
)
async def get_lca_results(result_id: str, indicator: str, cfs: dict[str, float],
                          operating_days: int = 330) -> dict:
    return await offload(engine.get_lca_results, result_id, indicator, cfs, operating_days)


@mutate_tool(
    "run_uncertainty",
    "Monte Carlo over economic parameters; metric is the product MSP. `parameters` is a "
    "list of {name, target, dist}, where target is one of 'feedstock_price', "
    "'electricity_price', 'IRR', and dist is ['triangle', lo, mid, hi] or "
    "['uniform', lo, hi]. Returns the MSP distribution (mean, P5, P50, P95).",
    {"metric": {"type": "string"}, "distribution": {"type": "object"}},
    task=NATIVE_TASKS_ENABLED,
)
async def run_uncertainty(result_id: str, parameters: list[dict[str, Any]],
                          N: int = 200, seed: int = 42) -> dict:
    if (blocked := guard_readonly()):
        return blocked
    return await offload(engine.run_uncertainty, result_id, parameters, N, seed)


@mutate_tool(
    "run_uncertainty_async",
    "Start Monte Carlo uncertainty analysis as a background job and return immediately. "
    "Use get_job_status(job_id) until terminal=true, then get_job_result(job_id). "
    "This compatibility tool avoids holding one MCP request open for long calculations.",
    {"job_id": {"type": "string"}, "status": {"type": "string"},
     "terminal": {"type": "boolean"}},
)
async def run_uncertainty_async(result_id: str, parameters: list[dict[str, Any]],
                                N: int = 200, seed: int = 42) -> dict:
    if (blocked := guard_readonly()):
        return blocked
    return jobs.submit(
        "run_uncertainty", engine.run_uncertainty, result_id, parameters, N, seed
    )


@read_tool(
    "run_sensitivity",
    "Spearman rank-correlation sensitivity of MSP to each parameter, from the most "
    "recent run_uncertainty on this result_id. Ranks the drivers of uncertainty.",
    {"spearman": arr({"type": "object"})},
)
async def run_sensitivity(result_id: str) -> dict:
    return await offload(engine.run_sensitivity, result_id)


@mutate_tool(
    "optimize",
    "Optimize unit design/operating variables against a metric. `variables` is a list "
    "of {unit_id, attr, bounds:[lo,hi]} (e.g. {'unit_id':'F1','attr':'V','bounds':"
    "[0.35,0.65]}). `objective` is 'MSP' (minimize) or 'NPV' (maximize). Uses gradient-"
    "free differential evolution; leaves the system at the optimum.",
    {"objective": {"type": "string"}, "optimum": {"type": "object"},
     "objective_value": {"type": "number"}},
    task=NATIVE_TASKS_ENABLED,
)
async def optimize(result_id: str, variables: list[dict[str, Any]],
                   objective: str = "MSP", maxiter: int = 20) -> dict:
    if (blocked := guard_readonly()):
        return blocked
    return await offload(engine.optimize, result_id, variables, objective, 1, maxiter)


@mutate_tool(
    "optimize_async",
    "Start differential-evolution optimization as a background job and return a job_id "
    "immediately. Poll get_job_status and retrieve the terminal result with get_job_result.",
    {"job_id": {"type": "string"}, "status": {"type": "string"},
     "terminal": {"type": "boolean"}},
)
async def optimize_async(result_id: str, variables: list[dict[str, Any]],
                         objective: str = "MSP", maxiter: int = 20) -> dict:
    if (blocked := guard_readonly()):
        return blocked
    return jobs.submit(
        "optimize", engine.optimize, result_id, variables, objective, 1, maxiter
    )


@read_tool(
    "get_job_status",
    "Return status for a background job. Poll conservatively; terminal=true means the "
    "job is completed, failed, or cancelled.",
    {"job_id": {"type": "string"}, "status": {"type": "string"},
     "terminal": {"type": "boolean"}},
)
async def get_job_status(job_id: str) -> dict:
    return jobs.status(job_id)


@read_tool(
    "get_job_result",
    "Retrieve the completed result for a background job. If a future result contains a "
    "large top-level list, pass field plus offset/limit to page that list (limit <= 200).",
    {"job_id": {"type": "string"}, "ready": {"type": "boolean"},
     "result": {}},
)
async def get_job_result(job_id: str, field: Optional[str] = None,
                         offset: int = 0, limit: int = 50) -> dict:
    return jobs.result(job_id, field=field, offset=offset, limit=limit)


@read_tool(
    "list_jobs",
    "List recent background jobs for this BioSTEAM MCP process. Results are newest first.",
    {"jobs": arr({"type": "object"})},
)
async def list_jobs(limit: int = 20) -> dict:
    return jobs.list_jobs(limit)


@mutate_tool(
    "cancel_job",
    "Cancel a queued background job. A running BioSTEAM engine call is not force-killed "
    "because interrupting stateful simulation/optimization threads is unsafe; the response "
    "explicitly reports when cancellation is unsupported for an already-running job.",
)
async def cancel_job(job_id: str) -> dict:
    return jobs.cancel(job_id)


@mutate_tool(
    "dispose_job",
    "Remove a terminal background job and its stored result from the in-memory job registry.",
)
async def dispose_job(job_id: str) -> dict:
    return jobs.dispose(job_id)


@read_tool(
    "get_flowsheet_diagram",
    "Return the flowsheet as a node/edge graph (units + stream connections) and, when "
    "Graphviz is available, render an image to `save_path` (or a temp file). Set "
    "`include_image_base64=true` to also embed the image inline. Returns nodes, edges, "
    "feeds, products, image_path (and image_base64/image_mime when requested).",
    {"nodes": arr({"type": "object"}), "edges": arr({"type": "object"}),
     "image_path": {"type": ["string", "null"]},
     "image_base64": {"type": ["string", "null"]}},
)
async def get_flowsheet_diagram(result_id: str, save_path: Optional[str] = None,
                                fmt: str = "png", include_image_base64: bool = False) -> dict:
    return await offload(engine.get_flowsheet_diagram, result_id, save_path, fmt,
                         include_image_base64)


@mutate_tool(
    "dispose_result",
    "Free a stored result by result_id.",
)
async def dispose_result(result_id: str) -> dict:
    if (blocked := guard_readonly()):
        return blocked
    return await offload(engine.dispose_result, result_id)

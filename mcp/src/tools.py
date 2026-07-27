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

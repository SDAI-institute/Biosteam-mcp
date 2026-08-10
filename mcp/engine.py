"""Framework-facing core for the BioSTEAM/QSDsan MCP server.

This module is intentionally **MCP-agnostic**: it holds the process-modeling logic and
returns plain, JSON-friendly dicts using the shared `{success, ...}` envelope. The
FastMCP server (later phase) is a thin adapter that stores results under `result_id`s
and wraps these functions as `@mcp.tool`s.

Keeping the logic here means it is testable without a running MCP client â€” see
`test_engine.py`. The contract mirrors Tier 8's `summarize_system`.

Run a smoke demo:  python mcp/engine.py
"""

from __future__ import annotations

import warnings
from typing import Any, Optional

from src.handle_provenance import HandleProvenanceStore, runtime_fingerprint

warnings.filterwarnings("ignore")


# --- shared envelope ---------------------------------------------------------
def ok(**data: Any) -> dict:
    return {"success": True, **data}


def err(message: str) -> dict:
    return {"success": False, "error": message}


# --- default TEA for spec-built systems (same shape as the tutorials) --------
def _make_conventional_tea(system):
    import biosteam as bst

    class ConventionalTEA(bst.TEA):
        def __init__(self, sys):
            super().__init__(
                sys, IRR=0.10, duration=(2020, 2040), depreciation="MACRS7",
                income_tax=0.21, operating_days=330, lang_factor=3.0,
                construction_schedule=(0.4, 0.6), startup_months=0, startup_FOCfrac=0,
                startup_VOCfrac=0, startup_salesfrac=0, WC_over_FCI=0.05,
                finance_interest=0, finance_years=0, finance_fraction=0)
            self.labor_cost = 2e6
        def _FOC(self, FCI):
            return FCI * 0.025 + self.labor_cost * 1.4

    return ConventionalTEA(system)


# --- engine ------------------------------------------------------------------
class BioSTEAMEngine:
    """Stateful core: build systems, then analyze them by `result_id`."""

    def __init__(self, provenance: Optional[HandleProvenanceStore] = None) -> None:
        self._store: dict[str, dict] = {}
        self._counter = 0
        self._provenance = provenance or HandleProvenanceStore()
        self._recovered_handles: set[str] = set()
        self._recovery_errors: dict[str, str] = {}
        self._reconstructing = False

    # -- probes --
    def health_check(self) -> dict:
        try:
            import biosteam, thermosteam, qsdsan  # noqa: F401
            return ok(versions={
                "biosteam": biosteam.__version__,
                "thermosteam": thermosteam.__version__,
                "qsdsan": qsdsan.__version__,
            })
        except Exception as exc:  # noqa: BLE001
            return err(f"import failed: {exc}")

    def list_biorefinery_models(self) -> dict:
        # A curated subset known to load cleanly; extend as needed.
        return ok(models=["cornstover", "lipidcane", "sugarcane", "corn"])

    def _save_recipe(self, result_id: str, kind: str, payload: dict) -> None:
        if self._reconstructing:
            return
        body = dict(payload)
        body.setdefault("state", {})
        self._provenance.save(result_id, kind, body)

    def _allocate_result_id(self, prefix: str) -> str:
        """Allocate an ID that cannot overwrite a persisted pre-restart handle."""
        while True:
            self._counter += 1
            candidate = f"{prefix}_{self._counter}"
            if candidate in self._store:
                continue
            if self._provenance.get(candidate) is not None:
                continue
            return candidate

    def _update_recipe_state(self, result_id: str, **updates: Any) -> None:
        record = self._provenance.get(result_id)
        if record is None:
            return
        payload = dict(record.get("payload") or {})
        state = dict(payload.get("state") or {})
        state.update(updates)
        payload["state"] = state
        self._provenance.save(result_id, str(record.get("kind")), payload)

    @staticmethod
    def _apply_recovered_state(entry: dict, state: dict) -> None:
        system = entry["system"]
        if state.get("operating_hours") is not None:
            system.operating_hours = float(state["operating_hours"])
        overrides = state.get("unit_overrides") or {}
        if overrides:
            units = {getattr(unit, "ID", None): unit for unit in system.units}
            for key, value in overrides.items():
                unit_id, sep, attr = str(key).partition(".")
                if not sep or unit_id not in units:
                    raise ValueError(f"cannot restore unit override '{key}'")
                setattr(units[unit_id], attr, float(value))
            system.simulate()

    def _missing_result(self, result_id: str) -> dict:
        message = self._recovery_errors.get(result_id)
        if message:
            return err(message)
        return err(f"unknown result_id '{result_id}'")

    def _resolve_entry(self, result_id: str) -> Optional[dict]:
        entry = self._store.get(result_id)
        if entry is not None:
            return entry

        record = self._provenance.get(result_id)
        if record is None:
            return None
        if record.get("runtime") != runtime_fingerprint():
            self._recovery_errors[result_id] = (
                f"result_id '{result_id}' has persisted build provenance, but its scientific "
                "runtime fingerprint differs from the current BioSTEAM/ThermoSTEAM/QSDsan "
                "runtime; automatic reconstruction was refused"
            )
            return None

        kind = record.get("kind")
        payload = record.get("payload") or {}
        self._reconstructing = True
        try:
            if kind == "published_model":
                rebuilt = self.build_system(str(payload["model_name"]))
            elif kind == "custom_spec":
                rebuilt = self.build_system_from_spec(dict(payload["spec"]))
            elif kind == "sanitation_spec":
                rebuilt = self.build_sanitation_system(dict(payload["spec"]))
            else:
                self._recovery_errors[result_id] = (
                    f"result_id '{result_id}' has unsupported persisted provenance kind '{kind}'"
                )
                return None
        except Exception as exc:  # noqa: BLE001
            self._recovery_errors[result_id] = (
                f"could not reconstruct result_id '{result_id}' after restart: {type(exc).__name__}: {exc}"
            )
            return None
        finally:
            self._reconstructing = False

        if not isinstance(rebuilt, dict) or not rebuilt.get("success") or not rebuilt.get("result_id"):
            detail = rebuilt.get("error") if isinstance(rebuilt, dict) else repr(rebuilt)
            self._recovery_errors[result_id] = (
                f"could not reconstruct result_id '{result_id}' after restart: {detail}"
            )
            return None

        temporary_id = str(rebuilt["result_id"])
        recovered = self._store.pop(temporary_id, None)
        if temporary_id != result_id:
            self._provenance.delete(temporary_id)
        if recovered is None:
            self._recovery_errors[result_id] = (
                f"reconstruction for result_id '{result_id}' completed without a stored system"
            )
            return None
        try:
            self._apply_recovered_state(recovered, dict(payload.get("state") or {}))
        except Exception as exc:  # noqa: BLE001
            self._recovery_errors[result_id] = (
                f"reconstructed result_id '{result_id}' but could not restore its persisted state: "
                f"{type(exc).__name__}: {exc}"
            )
            return None
        recovered["recovered_after_restart"] = True
        recovered["provenance_kind"] = kind
        self._store[result_id] = recovered
        # Preserve the original recipe and mutation state under the original ID even
        # when a fresh process reuses the same generated temporary ID.
        self._provenance.save(result_id, str(kind), dict(payload))
        self._recovered_handles.add(result_id)
        self._recovery_errors.pop(result_id, None)
        return recovered

    # -- build --
    def build_system(self, model_name: str) -> dict:
        """Load a published biorefinery by name and register it."""
        try:
            import importlib
            mod = importlib.import_module(f"biorefineries.{model_name}")
            # Some published biorefinery modules explicitly expose a loaded flag and
            # cache their process model. Re-running their loader can still execute
            # post-load economic calculations (e.g., solve_price) on the cached
            # object graph. Avoid that reload-side mutation once the module reports
            # itself loaded; modules without an explicit flag retain the old behavior.
            if not bool(getattr(mod, "_biorefinery_loaded", False)):
                mod.load()
        except Exception as exc:  # noqa: BLE001
            return err(f"could not load biorefinery '{model_name}': {exc}")

        system = _find_attr(mod, [f"{model_name}_sys", "sys", "system"])
        tea = _find_attr(mod, [f"{model_name}_tea", "tea"])
        product = _find_attr(mod, ["ethanol", "biodiesel", "product"])
        if system is None:
            return err(f"no system object found on biorefineries.{model_name}")

        # Identify the primary feedstock: prefer a feed whose ID matches the model
        # name (e.g. 'cornstover', 'lipidcane'); otherwise the priced feed with the
        # largest mass flow. (Plain max-mass would wrongly pick cooling water.)
        feedstock = None
        try:
            feeds = list(system.feeds)
            named = [s for s in feeds if model_name.lower() in s.ID.lower()]
            if named:
                feedstock = max(named, key=lambda s: s.F_mass)
            else:
                priced = [s for s in feeds if getattr(s, "price", 0)]
                feedstock = max(priced or feeds, key=lambda s: s.F_mass) if feeds else None
        except Exception:  # noqa: BLE001
            pass

        result_id = self._allocate_result_id(f"sys_{model_name}")
        self._store[result_id] = {
            "system": system, "tea": tea, "product": product,
            "feedstock": feedstock, "model": None,
        }
        self._save_recipe(result_id, "published_model", {"model_name": model_name})
        return ok(result_id=result_id, summary=self._summary(system))

    # -- analysis --
    def simulate_system(self, result_id: str) -> dict:
        entry = self._resolve_entry(result_id)
        if entry is None:
            return self._missing_result(result_id)
        system = entry["system"]
        try:
            system.simulate()
        except Exception as exc:  # noqa: BLE001
            return err(f"simulation failed: {exc}")
        return ok(**self._summary(system))

    def get_stream_results(self, result_id: str, stream_id: str) -> dict:
        """Return a JSON-friendly thermodynamic state for one stream.

        This exposes the quantities needed for process-model validation without
        mutating the system: total/component mass flow, molar/volumetric flow,
        temperature, pressure, phase, and enthalpy. BioSTEAM flow rates are
        reported on their native hourly basis.
        """
        entry = self._resolve_entry(result_id)
        if entry is None:
            return self._missing_result(result_id)
        system = entry["system"]

        streams = {}
        for stream in list(system.feeds) + list(system.products):
            if getattr(stream, "ID", None):
                streams[stream.ID] = stream
        for unit in system.units:
            for stream in list(unit.ins) + list(unit.outs):
                if getattr(stream, "ID", None):
                    streams[stream.ID] = stream

        stream = streams.get(stream_id)
        if stream is None:
            return err(f"stream '{stream_id}' not found in result '{result_id}'")

        components = {}
        component_moles = {}
        for chemical in stream.chemicals:
            mass_amount = float(stream.imass[chemical.ID])
            mol_amount = float(stream.imol[chemical.ID])
            if abs(mass_amount) > 1e-12:
                components[chemical.ID] = mass_amount
            if abs(mol_amount) > 1e-12:
                component_moles[chemical.ID] = mol_amount

        mass_flow = float(stream.F_mass)
        enthalpy = float(stream.H)
        source = getattr(getattr(stream, "source", None), "ID", None)
        sink = getattr(getattr(stream, "sink", None), "ID", None)
        return ok(stream={
            "id": stream.ID,
            "phase": str(stream.phase),
            "temperature_K": float(stream.T),
            "pressure_Pa": float(stream.P),
            "mass_flow_kg_hr": mass_flow,
            "molar_flow_kmol_hr": float(stream.F_mol),
            "volumetric_flow_m3_hr": float(stream.F_vol),
            "enthalpy_kJ_hr": enthalpy,
            "specific_enthalpy_kJ_kg": enthalpy / mass_flow if mass_flow else None,
            "component_mass_flow_kg_hr": components,
            "component_molar_flow_kmol_hr": component_moles,
            "source_unit": source,
            "sink_unit": sink,
        })

    def get_vle_results(self, result_id: str, stream_id: str, pressure_Pa: float) -> dict:
        """Return bubble/dew equilibrium at a specified pressure for a stream composition.

        The stream's normalized overall molar composition is used as the bubble liquid
        composition and, separately, as the dew vapor composition. Returned component
        order is explicit so binary/multicomponent VLE validation does not rely on an
        external molecular-weight conversion or an implicit registry order.
        """
        entry = self._resolve_entry(result_id)
        if entry is None:
            return self._missing_result(result_id)
        system = entry["system"]
        streams = {}
        for stream in list(system.feeds) + list(system.products):
            if getattr(stream, "ID", None):
                streams[stream.ID] = stream
        for unit in system.units:
            for stream in list(unit.ins) + list(unit.outs):
                if getattr(stream, "ID", None):
                    streams[stream.ID] = stream
        stream = streams.get(stream_id)
        if stream is None:
            return err(f"stream '{stream_id}' not found in result '{result_id}'")
        try:
            pressure = float(pressure_Pa)
            bp = stream.bubble_point_at_P(pressure)
            dp = stream.dew_point_at_P(pressure)
            ids = list(bp.IDs)
            return ok(vle={
                "stream_id": stream.ID,
                "pressure_Pa": pressure,
                "components": ids,
                "overall_mole_fraction": {
                    ID: float(stream.imol[ID] / stream.F_mol) for ID in ids
                },
                "bubble": {
                    "temperature_K": float(bp.T),
                    "liquid_mole_fraction": {ID: float(x) for ID, x in zip(ids, bp.x)},
                    "vapor_mole_fraction": {ID: float(y) for ID, y in zip(ids, bp.y)},
                },
                "dew": {
                    "temperature_K": float(dp.T),
                    "liquid_mole_fraction": {ID: float(x) for ID, x in zip(ids, dp.x)},
                    "vapor_mole_fraction": {ID: float(y) for ID, y in zip(ids, dp.y)},
                },
            })
        except Exception as exc:  # noqa: BLE001
            return err(f"VLE calculation failed: {exc}")

    def get_unit_results(self, result_id: str, unit_id: str) -> dict:
        """Return read-only design and utility results for one unit operation.

        Values are reported in BioSTEAM's native result units. Design-result keys

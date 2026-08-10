"""Framework-facing core for the BioSTEAM/QSDsan MCP server.

This module is intentionally **MCP-agnostic**: it holds the process-modeling logic and
returns plain, JSON-friendly dicts using the shared `{success, ...}` envelope. The
FastMCP server (later phase) is a thin adapter that stores results under `result_id`s
and wraps these functions as `@mcp.tool`s.

Keeping the logic here means it is testable without a running MCP client — see
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
        and meanings are unit-model-specific; this method intentionally exposes
        them rather than normalizing unlike equipment models into a false common
        schema.
        """
        entry = self._resolve_entry(result_id)
        if entry is None:
            return self._missing_result(result_id)
        system = entry["system"]
        unit = next((u for u in system.units if getattr(u, "ID", None) == unit_id), None)
        if unit is None:
            return err(f"unit '{unit_id}' not found in result '{result_id}'")

        def json_safe(value):
            if value is None or isinstance(value, (str, bool, int, float)):
                return value
            if hasattr(value, "item"):
                try:
                    return json_safe(value.item())
                except Exception:  # noqa: BLE001
                    pass
            if isinstance(value, dict):
                return {str(k): json_safe(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [json_safe(v) for v in value]
            try:
                return float(value)
            except (TypeError, ValueError):
                return str(value)

        power = getattr(unit, "power_utility", None)
        power_result = None
        if power is not None:
            power_result = {
                "rate_kW": float(getattr(power, "rate", 0.0) or 0.0),
                "cost_USD_hr": float(getattr(power, "cost", 0.0) or 0.0),
            }

        heat_results = []
        for hu in getattr(unit, "heat_utilities", ()) or ():
            heat_results.append({
                "duty_kJ_hr": float(getattr(hu, "duty", 0.0) or 0.0),
                "flow_kmol_hr": float(getattr(hu, "flow", 0.0) or 0.0),
                "cost_USD_hr": float(getattr(hu, "cost", 0.0) or 0.0),
                "agent": getattr(getattr(hu, "agent", None), "ID", None),
            })

        return ok(unit={
            "id": unit.ID,
            "type": type(unit).__name__,
            "inlet_streams": [getattr(s, "ID", None) for s in unit.ins],
            "outlet_streams": [getattr(s, "ID", None) for s in unit.outs],
            "design_results": json_safe(dict(getattr(unit, "design_results", {}) or {})),
            "power_utility": power_result,
            "heat_utilities": heat_results,
            "baseline_purchase_costs_USD": json_safe(dict(getattr(unit, "baseline_purchase_costs", {}) or {})),
            "purchase_costs_USD": json_safe(dict(getattr(unit, "purchase_costs", {}) or {})),
            "installed_costs_USD": json_safe(dict(getattr(unit, "installed_costs", {}) or {})),
        })

    def get_tea_results(self, result_id: str) -> dict:
        entry = self._resolve_entry(result_id)
        if entry is None:
            return self._missing_result(result_id)
        tea, product = entry.get("tea"), entry.get("product")
        if tea is None:
            return err("no TEA attached to this system")
        out = {
            "FCI_MM": round(tea.FCI / 1e6, 3),
            "FOC_MM_per_yr": round(tea.FOC / 1e6, 3),
            "VOC_MM_per_yr": round(tea.VOC / 1e6, 3),
            "NPV_MM": round(tea.NPV / 1e6, 2),
        }
        if product is not None:
            out["MSP_usd_per_kg"] = round(float(tea.solve_price(product)), 4)
        return ok(tea=out)

    def get_lca_results(self, result_id: str, indicator: str,
                        cfs: dict[str, float], operating_days: int = 330) -> dict:
        """Compute a foreground life-cycle impact given background CFs.

        `cfs` maps feed-stream IDs (and optionally "electricity") to a per-kg / per-kWh
        characterization factor for `indicator`.
        """
        import biosteam as bst
        entry = self._resolve_entry(result_id)
        if entry is None:
            return self._missing_result(result_id)
        system = entry["system"]
        try:
            if indicator not in (bst.settings.impact_indicators or {}):
                bst.settings.define_impact_indicator(indicator, "kg*CO2e")
        except Exception:  # noqa: BLE001
            pass
        system.operating_hours = 24 * operating_days
        hours = system.operating_hours
        self._update_recipe_state(result_id, operating_hours=float(hours))

        total = 0.0
        breakdown = {}
        for s in system.feeds:
            cf = cfs.get(s.ID)
            if cf is None:
                continue
            contrib = s.F_mass * hours * cf
            breakdown[s.ID] = round(contrib, 1)
            total += contrib
        if "electricity" in cfs:
            kwh = sum(u.power_utility.rate for u in system.units
                      if u.power_utility) * hours
            contrib = kwh * cfs["electricity"]
            breakdown["electricity"] = round(contrib, 1)
            total += contrib

        return ok(indicator=indicator, total=round(total, 1), breakdown=breakdown)

    def build_system_from_spec(self, spec: dict) -> dict:
        """Build a custom flowsheet from a JSON spec and register it.

        spec = {
          "thermo": ["Water", "Ethanol"],
          "thermo_model": "default" | "ideal"?,
          "streams": [{"id","flows":{chem:amount},"units"?,"T"?,"P"?,"price"?}, ...],
          "units":   [{"type":"HXutility","id","ins":[stream_id...],
                       "outs":[new_stream_id...],"params":{...}}, ...],
          "product": "stream_id"?,        # for MSP
          "attach_tea": true?             # default true
        }
        """
        import biosteam as bst
        import thermosteam as tmo
        try:
            bst.main_flowsheet.clear()
            thermo_model = str(spec.get("thermo_model", "default")).strip().lower()
            chemicals = list(spec["thermo"])
            if thermo_model in {"default", "thermosteam-default"}:
                bst.settings.set_thermo(chemicals)
            elif thermo_model in {"ideal", "raoult", "raoults-law"}:
                thermo = tmo.Thermo(
                    chemicals,
                    Gamma=tmo.IdealActivityCoefficients,
                    Phi=tmo.IdealFugacityCoefficients,
                    PCF=tmo.MockPoyintingCorrectionFactors,
                )
                bst.settings.set_thermo(thermo)
                thermo_model = "ideal"
            else:
                return err(
                    f"unknown thermo_model '{spec.get('thermo_model')}'. "
                    "Supported values are 'default' and 'ideal'."
                )

            active_thermo = bst.settings.thermo
            thermo_metadata = {
                "model": thermo_model,
                "chemicals": list(active_thermo.chemicals.IDs),
                "Gamma": active_thermo.Gamma.__name__,
                "Phi": active_thermo.Phi.__name__,
                "PCF": active_thermo.PCF.__name__,
            }

            registry: dict[str, Any] = {}
            for sdef in spec.get("streams", []):
                kw = {k: sdef[k] for k in ("T", "P", "price") if k in sdef}
                s = bst.Stream(sdef["id"], units=sdef.get("units", "kmol/hr"),
                               **sdef.get("flows", {}), **kw)
                registry[sdef["id"]] = s

            units = []
            for udef in spec.get("units", []):
                cls = getattr(bst, udef["type"], None)
                if cls is None:
                    return err(f"unknown unit type '{udef['type']}'")
                ins = [registry[i] for i in udef.get("ins", [])]
                outs = list(udef.get("outs", []))
                u = cls(udef["id"], ins=ins, outs=outs, **udef.get("params", {}))
                units.append(u)
                for s in u.outs:               # register newly created outlet streams
                    registry[s.ID] = s

            system = bst.System.from_units(spec.get("id", "custom_sys"), units=units)
            system.simulate()

            tea = _make_conventional_tea(system) if spec.get("attach_tea", True) else None
            product = registry.get(spec.get("product")) if spec.get("product") else None
        except Exception as exc:  # noqa: BLE001
            return err(f"could not build system from spec: {exc}")

        result_id = self._allocate_result_id("sys_custom")
        self._store[result_id] = {
            "system": system, "tea": tea, "product": product,
            "feedstock": None, "model": None,
            "thermo_metadata": thermo_metadata,
        }
        self._save_recipe(result_id, "custom_spec", {"spec": spec})
        return ok(result_id=result_id, summary=self._summary(system), thermo=thermo_metadata)

    def build_sanitation_system(self, spec: dict) -> dict:
        """Build a QSDsan wastewater / nutrient-recovery system and register it.

        spec = {
          "flow_tot": 1000,                         # m3/hr
          "concentrations": {"S_F":200, "S_NH4":40, "S_PO4":8, ...},  # mg/L
          "N_recovery": 0.6, "P_recovery": 0.8      # fractions of NH4 / PO4 recovered
        }
        """
        try:
            import qsdsan as qs

            cmps = qs.Components.load_default()
            qs.set_thermo(cmps)

            influent = qs.WasteStream("influent")
            influent.set_flow_by_concentration(
                flow_tot=spec.get("flow_tot", 1000),
                concentrations=spec["concentrations"],
                units=("m3/hr", "mg/L"),
            )

            class NutrientRecovery(qs.SanUnit):
                _N_ins = 1
                _N_outs = 2
                def __init__(self, ID="", ins=None, outs=(), thermo=None,
                             init_with="WasteStream", *, N_recovery=0.6, P_recovery=0.8):
                    super().__init__(ID, ins, outs, thermo, init_with=init_with)
                    self.N_recovery = N_recovery
                    self.P_recovery = P_recovery
                def _run(self):
                    infl = self.ins[0]
                    eff, rec = self.outs
                    eff.copy_like(infl)
                    rec.empty()
                    for cmp, frac in (("S_NH4", self.N_recovery), ("S_PO4", self.P_recovery)):
                        moved = infl.imass[cmp] * frac
                        eff.imass[cmp] -= moved
                        rec.imass[cmp] += moved

            U1 = NutrientRecovery(
                "U1", ins=influent, outs=("effluent", "recovered"),
                N_recovery=spec.get("N_recovery", 0.6),
                P_recovery=spec.get("P_recovery", 0.8),
            )
            system = qs.System("sanitation_sys", path=[U1])
            system.simulate()
            effluent, recovered = U1.outs
        except Exception as exc:  # noqa: BLE001
            return err(f"could not build sanitation system: {exc}")

        result_id = self._allocate_result_id("sys_sanitation")
        self._store[result_id] = {
            "system": system, "tea": None, "product": None,
            "feedstock": None, "model": None, "kind": "sanitation",
            "influent": influent, "effluent": effluent, "recovered": recovered,
        }
        self._save_recipe(result_id, "sanitation_spec", {"spec": spec})
        summary = self._summary(system)
        summary["influent"] = {
            "COD_mgL": round(float(influent.COD), 1),
            "BOD_mgL": round(float(influent.BOD), 1),
            "TN_mgL": round(float(influent.TN), 1),
            "TP_mgL": round(float(influent.TP), 1),
        }
        return ok(result_id=result_id, summary=summary)

    def get_wastewater_results(self, result_id: str) -> dict:
        """Composite variables, removal efficiency, and recovered nutrient mass."""
        entry = self._resolve_entry(result_id)
        if entry is None:
            return self._missing_result(result_id)
        if entry.get("kind") != "sanitation":
            return err("this result is not a sanitation system "
                       "(build it with build_sanitation_system)")
        inf, eff, rec = entry["influent"], entry["effluent"], entry["recovered"]

        def composites(ws):
            return {"COD_mgL": round(float(ws.COD), 1), "BOD_mgL": round(float(ws.BOD), 1),
                    "TN_mgL": round(float(ws.TN), 1), "TP_mgL": round(float(ws.TP), 1)}

        return ok(
            influent=composites(inf),
            effluent=composites(eff),
            removal_pct={
                "COD": round(100 * (1 - eff.COD / inf.COD), 1) if inf.COD else None,
                "TN": round(100 * (1 - eff.TN / inf.TN), 1) if inf.TN else None,
                "TP": round(100 * (1 - eff.TP / inf.TP), 1) if inf.TP else None,
            },
            recovered_kg_hr={
                "N_as_NH4": round(float(rec.imass["S_NH4"]), 3),
                "P_as_PO4": round(float(rec.imass["S_PO4"]), 3),
            },
        )

    def optimize(self, result_id: str, variables: list[dict],
                 objective: str = "MSP", seed: int = 1, maxiter: int = 20) -> dict:
        """Optimize unit design/operating variables against a metric.

        variables: list of {"unit_id", "attr", "bounds":[lo,hi]}.
        objective: "MSP" (minimize) or "NPV" (maximize).
        """
        from scipy.optimize import differential_evolution

        entry = self._resolve_entry(result_id)
        if entry is None:
            return self._missing_result(result_id)
        system, tea, product = entry["system"], entry.get("tea"), entry.get("product")
        if objective.upper() == "MSP" and (tea is None or product is None):
            return err("MSP objective needs a system with a TEA and a product")
        if objective.upper() == "NPV" and tea is None:
            return err("NPV objective needs a system with a TEA")

        unit_by_id = {u.ID: u for u in system.units}
        for v in variables:
            if v["unit_id"] not in unit_by_id:
                return err(f"unknown unit_id '{v['unit_id']}'")

        def metric() -> float:
            if objective.upper() == "MSP":
                return float(tea.solve_price(product))
            return -float(tea.NPV)     # maximize NPV -> minimize -NPV

        def objective_fn(x) -> float:
            for val, v in zip(x, variables):
                setattr(unit_by_id[v["unit_id"]], v["attr"], float(val))
            try:
                system.simulate()
                return metric()
            except Exception:  # noqa: BLE001
                return 1e6

        bounds = [tuple(v["bounds"]) for v in variables]
        opt = differential_evolution(objective_fn, bounds, seed=seed, maxiter=maxiter,
                                     tol=1e-5, polish=True, updating="deferred")
        # leave the system at the optimum
        recovered_overrides = {}
        for val, v in zip(opt.x, variables):
            value_f = float(val)
            setattr(unit_by_id[v["unit_id"]], v["attr"], value_f)
            recovered_overrides[v["unit_id"] + "." + v["attr"]] = value_f
        system.simulate()
        self._update_recipe_state(result_id, unit_overrides=recovered_overrides)

        value = metric()
        if objective.upper() == "NPV":
            value = -value
        return ok(
            objective=objective.upper(),
            optimum={v["unit_id"] + "." + v["attr"]: round(float(x), 4)
                     for x, v in zip(opt.x, variables)},
            objective_value=round(float(value), 4),
        )

    def get_flowsheet_diagram(self, result_id: str, save_path: Optional[str] = None,
                              fmt: str = "png", include_image_base64: bool = False) -> dict:
        """Return the flowsheet as a node/edge graph, and render an image if possible.

        Set ``include_image_base64=True`` to also embed the rendered image inline as a
        base64 string (for clients that display images without file access).
        """
        import os
        entry = self._resolve_entry(result_id)
        if entry is None:
            return self._missing_result(result_id)
        system = entry["system"]

        nodes = [{"id": u.ID, "type": type(u).__name__} for u in system.units]
        edges = []
        for u in system.units:
            for s in u.outs:
                if s.sink is not None:
                    edges.append({"from": u.ID, "to": s.sink.ID, "stream": s.ID})
        feeds = [s.ID for s in system.feeds]
        products = [s.ID for s in system.products]

        image_path = None
        image_base64 = None
        try:
            base = save_path or os.path.join(
                os.environ.get("TEMP", "."), f"biosteam_{result_id}")
            base = base[:-4] if base.lower().endswith("." + fmt) else base
            system.diagram(file=base, format=fmt)
            candidate = base + "." + fmt
            if os.path.exists(candidate):
                image_path = candidate
                if include_image_base64:
                    import base64
                    with open(candidate, "rb") as fh:
                        image_base64 = base64.b64encode(fh.read()).decode("ascii")
        except Exception:  # noqa: BLE001 - diagram is best-effort (needs Graphviz)
            image_path = None

        result = ok(nodes=nodes, edges=edges, feeds=feeds, products=products,
                    image_path=image_path)
        if include_image_base64:
            result["image_base64"] = image_base64
            result["image_mime"] = f"image/{fmt}"
        return result

    def run_uncertainty(self, result_id: str, parameters: list[dict],
                        N: int = 200, seed: int = 42) -> dict:
        """Monte Carlo over economic parameters; metric = product MSP.

        `parameters`: list of {"name", "target", "dist"} where target is one of
        {"feedstock_price", "electricity_price", "IRR"} and dist is
        ["triangle", lo, mid, hi] or ["uniform", lo, hi].
        """
        import numpy as np
        import chaospy as cp
        import biosteam as bst

        entry = self._resolve_entry(result_id)
        if entry is None:
            return self._missing_result(result_id)
        system, tea, product = entry["system"], entry.get("tea"), entry.get("product")
        feedstock = entry.get("feedstock")
        if tea is None or product is None:
            return err("uncertainty needs a system with a TEA and a product")

        def make_dist(spec):
            kind = spec[0].lower()
            if kind == "triangle":
                return cp.Triangle(spec[1], spec[2], spec[3])
            if kind == "uniform":
                return cp.Uniform(spec[1], spec[2])
            raise ValueError(f"unknown distribution '{spec[0]}'")

        # Monte Carlo parameter setters mutate shared BioSTEAM/TEA state. Snapshot
        # every supported economic target so uncertainty analysis is observational:
        # callers must get the same baseline system back after this method returns.
        baseline = {
            "feedstock_price": float(feedstock.price) if feedstock is not None else None,
            "electricity_price": float(bst.PowerUtility.price),
            "IRR": float(tea.IRR),
            "product_price": float(product.price) if product is not None else None,
        }

        # All MCP-exposed uncertainty targets are economic only; none changes the
        # process mass/energy balance. BioSTEAM Model.evaluate() normally calls
        # system.simulate() for every sample, which can move recycle-dependent
        # state even when process specifications are unchanged. Refresh only the
        # operating-cost accounting from already-solved duties/flows so electricity
        # price changes propagate to TEA without re-running the process model.
        def refresh_operating_costs():
            for unit in system.cost_units:
                unit._load_operation_costs()

        model = bst.Model(
            system,
            indicators=[bst.Metric("MSP", lambda: tea.solve_price(product), "USD/kg")],
            specification=refresh_operating_costs,
        )
        for spec in parameters:
            target = spec["target"]
            dist = make_dist(spec["dist"])
            name = spec.get("name", target)
            if target == "feedstock_price":
                if feedstock is None:
                    return err("no feedstock stream identified for feedstock_price")
                model.parameter(name=name, element=feedstock, kind="isolated",
                                distribution=dist)(lambda v: setattr(feedstock, "price", v))
            elif target == "electricity_price":
                model.parameter(name=name, element="TEA", kind="isolated",
                                distribution=dist)(lambda v: setattr(bst.PowerUtility, "price", v))
            elif target == "IRR":
                model.parameter(name=name, element="TEA", kind="isolated",
                                distribution=dist)(lambda v: setattr(tea, "IRR", v))
            else:
                return err(f"unknown parameter target '{target}'")

        np.random.seed(seed)
        samples = model.sample(N=N, rule="L")
        model.load_samples(samples)
        try:
            model.evaluate()
        finally:
            if feedstock is not None and baseline["feedstock_price"] is not None:
                feedstock.price = baseline["feedstock_price"]
            bst.PowerUtility.price = baseline["electricity_price"]
            tea.IRR = baseline["IRR"]
            if product is not None and baseline["product_price"] is not None:
                product.price = baseline["product_price"]
            # Restore cached operating-cost accounting at the baseline economics
            # without another system.simulate(), which is non-idempotent for the
            # qualified cornstover recycle state.
            refresh_operating_costs()

        entry["model"] = model

        msp = np.asarray(model.table.iloc[:, -1], dtype=float)
        p5, p50, p95 = (float(x) for x in np.percentile(msp, [5, 50, 95]))
        return ok(metric="MSP_usd_per_kg", N=N, distribution={
            "mean": round(float(msp.mean()), 4),
            "P5": round(p5, 4), "P50": round(p50, 4), "P95": round(p95, 4),
        })

    def run_sensitivity(self, result_id: str) -> dict:
        """Spearman sensitivity from the most recent `run_uncertainty` on this result."""
        entry = self._resolve_entry(result_id)
        if entry is None:
            return self._missing_result(result_id)
        model = entry.get("model")
        if model is None:
            return err("call run_uncertainty before run_sensitivity")
        rho, _pvals = model.spearman_r()
        col = rho.iloc[:, 0]
        ranked = col.reindex(col.abs().sort_values(ascending=False).index)
        spearman = [{"parameter": str(idx[-1] if isinstance(idx, tuple) else idx),
                     "rho": round(float(v), 3)} for idx, v in ranked.items()]
        return ok(spearman=spearman)

    def dispose_result(self, result_id: str) -> dict:
        existed_in_memory = self._store.pop(result_id, None) is not None
        persisted = self._provenance.get(result_id) is not None
        if persisted:
            self._provenance.delete(result_id)
        self._recovered_handles.discard(result_id)
        self._recovery_errors.pop(result_id, None)
        if existed_in_memory or persisted:
            return ok()
        return err(f"unknown result_id '{result_id}'")

    # -- internal --
    @staticmethod
    def _summary(system) -> dict:
        try:
            installed = round(system.installed_equipment_cost / 1e6, 3)
        except Exception:  # noqa: BLE001 - SanUnits may lack costing
            installed = None
        return {
            "system": system.ID,
            "n_units": len(system.units),
            "installed_equipment_cost_MM": installed,
            "feeds": {s.ID: round(s.F_mass, 1) for s in system.feeds},
            "products": {s.ID: round(s.F_mass, 1) for s in system.products},
        }


def _find_attr(mod, names) -> Optional[Any]:
    for n in names:
        if hasattr(mod, n):
            return getattr(mod, n)
    return None


if __name__ == "__main__":
    eng = BioSTEAMEngine()
    print("health:", eng.health_check())
    built = eng.build_system("cornstover")
    print("build :", {k: v for k, v in built.items() if k != "summary"})
    rid = built["result_id"]
    print("tea   :", eng.get_tea_results(rid))
    print("lca   :", eng.get_lca_results(rid, "GWP", {"cornstover": 0.05, "electricity": 0.45}))
    print("free  :", eng.dispose_result(rid))

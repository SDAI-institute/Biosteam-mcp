"""Verify the BioSTEAM / QSDsan tutorial environment.

Run inside the target env (envShilab):

    python environment/verify_install.py

Prints the version of every package the tutorials depend on and exits non-zero
if any required import fails, so a broken environment is caught loudly before you
start executing notebooks.
"""

from __future__ import annotations

import importlib
import sys
from typing import Optional

# (import name, human label, required?)
PACKAGES = [
    ("biosteam", "BioSTEAM", True),
    ("thermosteam", "thermosteam", True),
    ("qsdsan", "QSDsan", True),
    ("biorefineries", "biorefineries", False),
    ("chaospy", "chaospy", False),
    ("numpy", "NumPy", True),
    ("pandas", "pandas", True),
    ("matplotlib", "matplotlib", False),
    ("nbconvert", "nbconvert", False),
]


def _version(mod) -> str:
    for attr in ("__version__", "version"):
        v = getattr(mod, attr, None)
        if isinstance(v, str):
            return v
    return "(no __version__)"


def main() -> int:
    print(f"Python {sys.version.split()[0]}  @  {sys.executable}\n")
    failures: list[str] = []
    rows: list[tuple[str, str]] = []

    for import_name, label, required in PACKAGES:
        try:
            mod = importlib.import_module(import_name)
            rows.append((label, _version(mod)))
        except Exception as exc:  # noqa: BLE001 - want the full reason
            mark = "REQUIRED" if required else "optional"
            rows.append((label, f"MISSING ({mark}): {exc.__class__.__name__}"))
            if required:
                failures.append(f"{label}: {exc}")

    width = max(len(label) for label, _ in rows)
    for label, info in rows:
        print(f"  {label.ljust(width)}  {info}")

    print()
    if failures:
        print("FAILED — required packages could not be imported:")
        for f in failures:
            print(f"  - {f}")
        print("\nFix: `conda activate envShilab && pip install -r environment/requirements.txt`")
        return 1

    print("OK — required packages import cleanly. Environment is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

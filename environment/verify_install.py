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

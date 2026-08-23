"""Build an executed .ipynb from a percent-format .py tutorial script.

Convention (so every `NN_*.py` doubles as a runnable script AND notebook source):

    # %% [markdown]
    # # A markdown cell
    # Body text; each line is a `# `-prefixed comment.

    # %%
    print("a code cell")          # real code, runs with `python NN_*.py`

Usage:
    python environment/build_notebook.py path/to/NN_name.py
    python environment/build_notebook.py path/to/NN_name.py --no-exec   # convert only

The generated notebook lands next to the source as `NN_name.ipynb`, executed
in-process (kernel = whatever Python runs this) so committed outputs are real.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook


def parse_percent(src: str):
    """Yield (kind, source) cells from percent-format text."""
    cells: list[tuple[str, list[str]]] = []
    kind = "code"
    buf: list[str] = []

    def flush():
        if buf and "".join(buf).strip():
            cells.append((kind, buf.copy()))
        buf.clear()

    for line in src.splitlines():
        stripped = line.strip()

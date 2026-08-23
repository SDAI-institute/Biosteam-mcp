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
        if stripped.startswith("# %%"):
            flush()
            kind = "markdown" if "[markdown]" in stripped else "code"
            continue
        buf.append(line)
    flush()

    for k, lines in cells:
        if k == "markdown":
            # Strip a single leading "# " / "#" from each comment line.
            md = []
            for ln in lines:
                if ln.startswith("# "):
                    md.append(ln[2:])
                elif ln.strip() == "#":
                    md.append("")
                else:
                    md.append(ln)
            yield "markdown", "\n".join(md).strip("\n")
        else:
            yield "code", "\n".join(lines).strip("\n")


def build(py_path: Path, execute: bool = True) -> Path:
    text = py_path.read_text(encoding="utf-8")
    nb = new_notebook()
    for kind, source in parse_percent(text):
        if not source.strip():
            continue
        nb.cells.append(
            new_markdown_cell(source) if kind == "markdown" else new_code_cell(source)
        )
    nb.metadata["kernelspec"] = {
        "display_name": "Python (envShilab)",
        "language": "python",
        "name": "envShilab",
    }

    if execute:
        from nbclient import NotebookClient

        client = NotebookClient(
            nb, timeout=1200, kernel_name="envShilab", allow_errors=False
        )
        client.execute()

    out_path = py_path.with_suffix(".ipynb")
    nbformat.write(nb, out_path)
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("script", type=Path)
    ap.add_argument("--no-exec", action="store_true", help="convert without executing")
    args = ap.parse_args()
    out = build(args.script, execute=not args.no_exec)
    print(f"wrote {out}{'' if args.no_exec else ' (executed)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

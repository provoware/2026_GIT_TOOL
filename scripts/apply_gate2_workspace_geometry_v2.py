#!/usr/bin/env python3
"""Idempotente Gate-2-Anwendung auf Basis des geprüften Codemods."""

from __future__ import annotations

import argparse
from pathlib import Path

import apply_gate2_workspace_geometry as base

TARGET = Path(__file__).resolve().parents[1] / "system" / "main_window.py"

# Der Basiscodemod hängt selbst genau ein Zeilenende an. Deshalb dürfen seine
# Templates nicht bereits mit einem Zeilenende enden.
base.METHODS = {name: template.rstrip("\n") for name, template in base.METHODS.items()}


def transform(source: str) -> str:
    return base.transform(source)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=TARGET)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    source = args.path.read_text(encoding="utf-8")
    result = transform(source)
    changed = result != source
    if args.check:
        return 1 if changed else 0
    if changed:
        args.path.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

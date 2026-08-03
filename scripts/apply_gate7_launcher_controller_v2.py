#!/usr/bin/env python3
"""Kanonischer Gate-7-Codemod mit normalisierten Refresh-Escapes."""

from __future__ import annotations

import argparse
from pathlib import Path

import apply_gate7_launcher_controller as base

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "system" / "launcher_gui.py"


def _normalize_refresh_template() -> None:
    template = base.METHODS["refresh"]
    template = template.replace(
        '"Fehler beim Aktualisieren.\n"',
        '"Fehler beim Aktualisieren.\\n"',
    )
    template = template.replace(
        'f"Ursache: {exc}\n"',
        'f"Ursache: {exc}\\n"',
    )
    template = template.replace(
        '"danach erneut auf „Übersicht aktualisieren“ klicken.\n"',
        '"danach erneut auf „Übersicht aktualisieren“ klicken.\\n"',
    )
    base.METHODS["refresh"] = template


def transform(source: str) -> str:
    _normalize_refresh_template()
    return base.transform(source)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    source = args.path.read_text(encoding="utf-8")
    transformed = transform(source)
    changed = transformed != source
    if changed and not args.check:
        args.path.write_text(transformed, encoding="utf-8")
    if args.check and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

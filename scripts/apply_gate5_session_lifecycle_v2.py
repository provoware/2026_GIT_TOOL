#!/usr/bin/env python3
"""Gate-5-Kompatibilitätswrapper für datengetriebene Launcher-Hilfe."""

from __future__ import annotations

import argparse
from pathlib import Path

import apply_gate5_session_lifecycle as base

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "system" / "launcher_gui.py"
DATA_DRIVEN_HELP_MARKER = '"autostart_check": self.autostart_check'


def transform(source: str) -> str:
    """Akzeptiert Inline- und Gate-7-Hilfe als gleichwertig integrierten Zustand."""

    original_help = base.AUTOSTART_HELP
    if DATA_DRIVEN_HELP_MARKER in source and original_help not in source:
        base.AUTOSTART_HELP = DATA_DRIVEN_HELP_MARKER
    try:
        return base.transform(source)
    finally:
        base.AUTOSTART_HELP = original_help


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
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

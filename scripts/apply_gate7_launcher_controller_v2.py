#!/usr/bin/env python3
"""Kanonischer Gate-7-Codemod mit Escape- und View-Synchronisierung."""

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


def _replace_once_or_done(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: erwartete Struktur nicht eindeutig ({count}).")
    return source.replace(old, new, 1)


def _connect_filter_views(source: str) -> str:
    result = _replace_once_or_done(
        source,
        '''        self.show_all_check = tk.Checkbutton(
            controls,
            text="Alle Module anzeigen (inkl. deaktiviert)",
            variable=self.show_all_var,
            command=self.refresh,
        )
''',
        '''        self.show_all_check = tk.Checkbutton(
            controls,
            text="Alle Module anzeigen (inkl. deaktiviert)",
            variable=self.show_all_var,
            command=lambda: self._set_show_all(
                bool(self.show_all_var.get()), record_action=True
            ),
        )
''',
        "Show-all-Command",
    )
    return _replace_once_or_done(
        result,
        '''        self.debug_check = tk.Checkbutton(
            controls,
            text="Debug-Details anzeigen",
            variable=self.debug_var,
            command=self.refresh,
        )
''',
        '''        self.debug_check = tk.Checkbutton(
            controls,
            text="Debug-Details anzeigen",
            variable=self.debug_var,
            command=lambda: self._set_debug(
                bool(self.debug_var.get()), record_action=True
            ),
        )
''',
        "Debug-Command",
    )


def transform(source: str) -> str:
    _normalize_refresh_template()
    return _connect_filter_views(base.transform(source))


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

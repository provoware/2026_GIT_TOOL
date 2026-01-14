#!/usr/bin/env python3
"""Erstellt einen Kontrastbericht für den GUI-Launcher."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "launcher_gui.json"
REPORT_PATH = ROOT_DIR / "reports" / "kontrastpruefung_launcher_gui.md"


def _load_config(path: Path) -> dict:
    if not path.exists():
        raise SystemExit("Fehler: launcher_gui.json fehlt.")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Fehler: JSON ungültig ({exc}).") from exc


def main() -> int:
    import sys

    sys.path.append(str(ROOT_DIR / "system"))
    from color_utils import contrast_ratio

    data = _load_config(CONFIG_PATH)
    themes = data.get("themes")
    if not isinstance(themes, dict) or not themes:
        raise SystemExit("Fehler: themes fehlen oder sind leer.")

    lines = [
        "# Kontrastprüfung GUI-Launcher",
        "",
        f"Stand: {date.today().isoformat()}",
        "",
        "Ziel: Kontrast ≥ 4,5:1 (WCAG AA für normalen Text).",
        "",
        "| Theme | Hintergrund/Text | Button/Label | Akzent/Hintergrund | Ergebnis |",
        "| --- | --- | --- | --- | --- |",
    ]

    for name, entry in themes.items():
        colors = entry.get("colors", {})
        bg = colors.get("background")
        fg = colors.get("foreground")
        button_bg = colors.get("button_background")
        button_fg = colors.get("button_foreground")
        accent = colors.get("accent")
        if not all([bg, fg, button_bg, button_fg, accent]):
            raise SystemExit(f"Fehler: Theme {name} ist unvollständig.")

        bg_fg = contrast_ratio(bg, fg)
        button = contrast_ratio(button_bg, button_fg)
        accent_bg = contrast_ratio(accent, bg)
        ok = all(value >= 4.5 for value in (bg_fg, button, accent_bg))
        status = "OK" if ok else "Prüfen"

        lines.append(
            "| {name} | {bg_fg:.2f} | {button:.2f} | {accent_bg:.2f} | {status} |".format(
                name=name,
                bg_fg=bg_fg,
                button=button,
                accent_bg=accent_bg,
                status=status,
            )
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Bericht geschrieben: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

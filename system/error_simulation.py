#!/usr/bin/env python3
"""Fehler-Simulation: typische Laienfehler prüfen und erklären."""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

import dependency_checker
import launcher_gui
import module_checker
from logging_center import get_logger
from logging_center import setup_logging as setup_logging_center


class ErrorSimulationError(Exception):
    """Fehler in der Fehler-Simulation."""


@dataclass(frozen=True)
class SimulationResult:
    title: str
    status: str
    message: str
    hint: str


def _simulate_missing_module_config() -> SimulationResult:
    try:
        module_checker.load_modules(Path("/pfad/zu/fehlend.json"))
    except module_checker.ModuleCheckError as exc:
        return SimulationResult(
            title="Modul-Liste fehlt",
            status="ok",
            message=str(exc),
            hint="Lösung: Datei config/modules.json prüfen oder neu anlegen.",
        )
    raise ErrorSimulationError("Simulation konnte Fehler nicht auslösen.")


def _simulate_invalid_gui_color() -> SimulationResult:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "launcher_gui.json"
        config_path.write_text(
            json.dumps(
                {
                    "default_theme": "hell",
                    "themes": {
                        "hell": {
                            "label": "Hell",
                            "colors": {
                                "background": "white",
                                "foreground": "#111111",
                                "accent": "#005ea5",
                                "button_background": "#e6f0fb",
                                "button_foreground": "#0b2d4d",
                                "status_success": "#1b5e20",
                                "status_error": "#b00020",
                                "status_busy": "#005ea5",
                                "status_foreground": "#ffffff",
                            },
                        }
                    },
                    "layout": {
                        "gap_xs": 4,
                        "gap_sm": 8,
                        "gap_md": 12,
                        "gap_lg": 16,
                        "gap_xl": 24,
                        "button_padx": 18,
                        "button_pady": 10,
                        "button_min_width": 18,
                        "button_font_size": 16,
                        "field_padx": 6,
                        "field_pady": 4,
                        "text_spacing": {"before": 4, "line": 2, "after": 4},
                        "focus_thickness": 2,
                    },
                }
            ),
            encoding="utf-8",
        )
        try:
            launcher_gui.load_gui_config(config_path)
        except launcher_gui.GuiLauncherError as exc:
            return SimulationResult(
                title="GUI-Farbe ungültig",
                status="ok",
                message=str(exc),
                hint="Lösung: Farben als Hex-Code (#fff oder #ffffff) eintragen.",
            )
    raise ErrorSimulationError("Simulation konnte Fehler nicht auslösen.")


def _simulate_invalid_dependency() -> SimulationResult:
    try:
        dependency_checker._normalize_module_name("")
    except dependency_checker.DependencyError as exc:
        return SimulationResult(
            title="Abhängigkeit leer",
            status="ok",
            message=str(exc),
            hint="Lösung: requirements.txt auf leere Zeilen prüfen.",
        )
    raise ErrorSimulationError("Simulation konnte Fehler nicht auslösen.")


def run_simulations() -> List[SimulationResult]:
    return [
        _simulate_missing_module_config(),
        _simulate_invalid_gui_color(),
        _simulate_invalid_dependency(),
    ]


def render_report(results: List[SimulationResult]) -> str:
    lines = ["Fehler-Simulation (Laienfehler):", ""]
    for result in results:
        lines.extend(
            [
                f"- Fall: {result.title}",
                f"  Ergebnis: {result.status}",
                f"  Meldung: {result.message}",
                f"  Hinweis: {result.hint}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fehler-Simulation: typische Laienfehler prüfen.",
    )
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging_center(args.debug)
    logger = get_logger("error_simulation")
    try:
        results = run_simulations()
    except ErrorSimulationError as exc:
        logger.error("Fehler-Simulation fehlgeschlagen: %s", exc)
        return 2
    print(render_report(results), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

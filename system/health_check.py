#!/usr/bin/env python3
"""Health-Check: prüft wichtige Dateien und Ordner vor dem Start."""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class HealthCheckError(Exception):
    """Fehler im Health-Check."""


@dataclass(frozen=True)
class CheckItem:
    path: Path
    label: str


def _ensure_items(items: Iterable[CheckItem], label: str) -> List[CheckItem]:
    if not isinstance(items, Iterable):
        raise HealthCheckError(f"{label} ist keine Liste.")
    items_list = list(items)
    if not items_list:
        raise HealthCheckError(f"{label} ist leer.")
    return items_list


def _check_dir(
    item: CheckItem,
    issues: List[str],
    repairs: List[str],
    self_repair: bool,
) -> None:
    if not item.path.exists():
        if self_repair:
            try:
                item.path.mkdir(parents=True, exist_ok=True)
                logging.info("Self-Repair: Ordner erstellt: %s (%s).", item.label, item.path)
                repairs.append(f"Ordner erstellt: {item.label} ({item.path}).")
                return
            except OSError as exc:
                issues.append(
                    f"Self-Repair fehlgeschlagen: Ordner {item.label} ({item.path}). Grund: {exc}"
                )
                return
        issues.append(f"Ordner fehlt: {item.label} ({item.path}).")
        return
    if not item.path.is_dir():
        issues.append(f"Pfad ist kein Ordner: {item.label} ({item.path}).")


def _check_file(
    item: CheckItem,
    issues: List[str],
    repairs: List[str],
    self_repair: bool,
    defaults: dict[Path, str],
) -> None:
    if not item.path.exists():
        if self_repair:
            default_content = defaults.get(item.path)
            if default_content is None:
                issues.append(f"Self-Repair: Keine Standarddaten für {item.label} ({item.path}).")
                return
            try:
                item.path.parent.mkdir(parents=True, exist_ok=True)
                item.path.write_text(default_content, encoding="utf-8")
                logging.info("Self-Repair: Datei erstellt: %s (%s).", item.label, item.path)
                repairs.append(f"Datei erstellt: {item.label} ({item.path}).")
                return
            except OSError as exc:
                issues.append(
                    f"Self-Repair fehlgeschlagen: Datei {item.label} ({item.path}). Grund: {exc}"
                )
                return
        issues.append(f"Datei fehlt: {item.label} ({item.path}).")
        return
    if not item.path.is_file():
        issues.append(f"Pfad ist keine Datei: {item.label} ({item.path}).")
        return
    if not os.access(item.path, os.R_OK):
        issues.append(f"Datei nicht lesbar: {item.label} ({item.path}).")


def _check_json(item: CheckItem, issues: List[str]) -> None:
    try:
        json.loads(item.path.read_text(encoding="utf-8"))
    except PermissionError:
        issues.append(f"JSON nicht lesbar: {item.label} ({item.path}).")
    except OSError as exc:
        issues.append(f"JSON nicht lesbar: {item.label} ({item.path}). Grund: {exc}")
    except FileNotFoundError:
        issues.append(f"JSON fehlt: {item.label} ({item.path}).")
    except json.JSONDecodeError:
        issues.append(f"JSON ungültig: {item.label} ({item.path}).")


def _check_executable(item: CheckItem, issues: List[str]) -> None:
    if not item.path.exists():
        issues.append(f"Skript fehlt: {item.label} ({item.path}).")
        return
    if not os.access(item.path, os.X_OK):
        issues.append(
            f"Skript ist nicht ausführbar: {item.label} ({item.path})." " Tipp: chmod +x ausführen."
        )


def _build_default_files(root: Path) -> dict[Path, str]:
    today = datetime.now(timezone.utc).date().isoformat()
    modules_payload = {
        "modules": [
            {
                "id": "platzhalter",
                "name": "Platzhalter (deaktiviert)",
                "path": "modules/platzhalter",
                "enabled": False,
                "description": "Dieser Eintrag ist deaktiviert und kann entfernt werden.",
            }
        ]
    }
    gui_payload = {
        "default_theme": "hell",
        "themes": {
            "hell": {
                "label": "Hell",
                "colors": {
                    "background": "#ffffff",
                    "foreground": "#1a1a1a",
                    "accent": "#005ea5",
                    "button_background": "#e6f0fb",
                    "button_foreground": "#0b2d4d",
                },
            },
            "kontrast": {
                "label": "Kontrast",
                "colors": {
                    "background": "#000000",
                    "foreground": "#ffffff",
                    "accent": "#ffcc00",
                    "button_background": "#1a1a1a",
                    "button_foreground": "#ffffff",
                },
            },
        },
    }
    test_gate_payload = {
        "threshold": 9,
        "todo_path": "todo.txt",
        "state_path": "data/test_state.json",
        "tests_command": ["bash", "scripts/run_tests.sh"],
    }
    selftest_payload = {
        "testcases": {
            "beispiel_modul": {"text": "Selbsttest"},
            "status": {"request": "Selbsttest"},
        }
    }

    return {
        root / "config" / "modules.json": json.dumps(modules_payload, indent=2, ensure_ascii=False)
        + "\n",
        root / "config" / "launcher_gui.json": json.dumps(gui_payload, indent=2, ensure_ascii=False)
        + "\n",
        root
        / "config"
        / "requirements.txt": (
            "# Python-Abhängigkeiten (pip-Pakete)\n"
            "# Beispiel: requests>=2.32.0\n"
            "# Hinweis: Leere Datei bedeutet, dass aktuell keine externen Pakete nötig sind.\n"
            "pytest>=8.0.0\n"
            "ruff>=0.5.0\n"
            "black>=24.0.0\n"
        ),
        root
        / "config"
        / "test_gate.json": json.dumps(test_gate_payload, indent=2, ensure_ascii=False)
        + "\n",
        root
        / "config"
        / "module_selftests.json": json.dumps(selftest_payload, indent=2, ensure_ascii=False)
        + "\n",
        root
        / "todo.txt": (
            "# To-Do-Liste\n"
            "# Format: [ ] JJJJ-MM-TT | Bereich | Titel | prüfen: ... | fertig wenn: ...\n"
        ),
        root / "CHANGELOG.md": "# Changelog\n\n## [Unreleased]\n- Platzhalter.\n",
        root
        / "DEV_DOKU.md": (
            "# DEV_DOKU\n\n## Zweck\nPlatzhalter für die Entwickler-Dokumentation.\n"
        ),
        root / "DONE.md": f"# DONE\n\n## {today}\n- Platzhalter.\n",
        root
        / "PROGRESS.md": (
            "# PROGRESS\n\n"
            f"Stand: {today}\n\n"
            "- Gesamt: 0 Tasks\n"
            "- Erledigt: 0 Tasks\n"
            "- Offen: 0 Tasks\n"
            "- Fortschritt: 0,00 %\n"
        ),
    }


def run_health_check(root: Path, self_repair: bool = False) -> tuple[List[str], List[str]]:
    ensure_path(root, "root", HealthCheckError)
    if not root.exists():
        raise HealthCheckError(f"Root-Verzeichnis fehlt: {root}")
    if not root.is_dir():
        raise HealthCheckError(f"Root ist kein Ordner: {root}")

    issues: List[str] = []
    repairs: List[str] = []
    defaults = _build_default_files(root) if self_repair else {}

    dir_items = _ensure_items(
        [
            CheckItem(root / "config", "Konfiguration"),
            CheckItem(root / "system", "System"),
            CheckItem(root / "scripts", "Skripte"),
            CheckItem(root / "modules", "Module"),
            CheckItem(root / "data", "Daten"),
            CheckItem(root / "logs", "Logs"),
            CheckItem(root / "tests", "Tests"),
            CheckItem(root / "src", "Quellcode"),
        ],
        "Ordnerliste",
    )
    for item in dir_items:
        _check_dir(item, issues, repairs, self_repair)

    file_items = _ensure_items(
        [
            CheckItem(root / "config" / "modules.json", "Modul-Liste"),
            CheckItem(root / "config" / "launcher_gui.json", "GUI-Konfiguration"),
            CheckItem(root / "config" / "requirements.txt", "Abhängigkeiten"),
            CheckItem(root / "config" / "test_gate.json", "Test-Sperre"),
            CheckItem(root / "todo.txt", "To-Do-Liste"),
            CheckItem(root / "CHANGELOG.md", "Changelog"),
            CheckItem(root / "DEV_DOKU.md", "Entwickler-Dokumentation"),
            CheckItem(root / "DONE.md", "Done-Liste"),
            CheckItem(root / "PROGRESS.md", "Fortschritt"),
        ],
        "Dateiliste",
    )
    for item in file_items:
        _check_file(item, issues, repairs, self_repair, defaults)

    json_items = _ensure_items(
        [
            CheckItem(root / "config" / "modules.json", "Modul-Liste"),
            CheckItem(root / "config" / "launcher_gui.json", "GUI-Konfiguration"),
            CheckItem(root / "config" / "test_gate.json", "Test-Sperre"),
        ],
        "JSON-Liste",
    )
    for item in json_items:
        _check_json(item, issues)

    script_items = _ensure_items(
        [
            CheckItem(root / "scripts" / "start.sh", "Start-Routine"),
            CheckItem(root / "scripts" / "run_tests.sh", "Testskript"),
            CheckItem(root / "klick_start.sh", "Klick&Start"),
        ],
        "Skriptliste",
    )
    for item in script_items:
        _check_executable(item, issues)

    return issues, repairs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Health-Check: Prüft wichtige Dateien und Ordner vor dem Start.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Projekt-Root (Standard: Repository-Wurzel).",
    )
    parser.add_argument(
        "--self-repair",
        action="store_true",
        help="Fehlende Ordner/Dateien automatisch anlegen (Selbstreparatur).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug-Modus aktivieren.",
    )
    return parser


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def _render_output(issues: Iterable[str], repairs: Iterable[str]) -> str:
    if not isinstance(issues, Iterable):
        raise HealthCheckError("issues ist keine Liste.")
    if not isinstance(repairs, Iterable):
        raise HealthCheckError("repairs ist keine Liste.")
    issues_list = list(issues)
    repairs_list = list(repairs)
    if not issues_list:
        if repairs_list:
            lines = ["Health-Check: Selbstreparatur abgeschlossen.", ""]
            lines.extend([f"- {repair}" for repair in repairs_list])
            lines.append("")
            lines.append("Health-Check: Alle wichtigen Dateien und Ordner sind vorhanden.")
            return "\n".join(lines)
        return "Health-Check: Alle wichtigen Dateien und Ordner sind vorhanden."

    lines = ["Health-Check: Probleme gefunden:", ""]
    lines.extend([f"- {issue}" for issue in issues_list])
    if repairs_list:
        lines.append("")
        lines.append("Hinweis: Selbstreparatur wurde ausgeführt.")
        lines.extend([f"- {repair}" for repair in repairs_list])
    lines.append("")
    lines.append("Bitte die Hinweise prüfen und die Struktur korrigieren.")
    return "\n".join(lines)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.debug)

    try:
        issues, repairs = run_health_check(args.root, self_repair=args.self_repair)
        if args.self_repair:
            logging.info("Self-Repair ist aktiv. Fehlende Basiselemente werden erstellt.")
    except HealthCheckError as exc:
        logging.error("Health-Check konnte nicht starten: %s", exc)
        return 2

    output = _render_output(issues, repairs)
    print(output)

    if issues:
        logging.error("Health-Check: %s Problem(e) gefunden.", len(issues))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

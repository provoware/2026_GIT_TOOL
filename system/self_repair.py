#!/usr/bin/env python3
"""Self-Repair: automatische Reparaturen für Dateien, JSON und Rechte."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path
from filename_fixer import run_fix as run_filename_fix
from logging_center import setup_logging as setup_logging_center

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class SelfRepairError(Exception):
    """Allgemeiner Fehler für die Self-Repair-Routine."""


@dataclass(frozen=True)
class RepairItem:
    path: Path
    label: str


def _ensure_items(items: Iterable[RepairItem], label: str) -> List[RepairItem]:
    if not isinstance(items, Iterable):
        raise SelfRepairError(f"{label} ist keine Liste.")
    items_list = list(items)
    if not items_list:
        raise SelfRepairError(f"{label} ist leer.")
    return items_list


def _hash_pin(pin: str, salt: str) -> str:
    if not isinstance(pin, str) or not pin:
        raise SelfRepairError("pin fehlt oder ist leer.")
    if not isinstance(salt, str) or not salt:
        raise SelfRepairError("salt fehlt oder ist leer.")
    return hashlib.sha256(f"{salt}{pin}".encode("utf-8")).hexdigest()


def build_default_files(root: Path) -> dict[Path, str]:
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
                    "status_success": "#1b5e20",
                    "status_error": "#b00020",
                    "status_busy": "#005ea5",
                    "status_foreground": "#ffffff",
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
                    "status_success": "#00ff00",
                    "status_error": "#ff0033",
                    "status_busy": "#ffcc00",
                    "status_foreground": "#000000",
                },
            },
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
    structure_payload = {
        "required_entry": "module.py",
        "entry_exceptions": [],
        "required_files": ["manifest.json", "module.py"],
    }
    suffix_payload = {
        "defaults": {
            "data": ".json",
            "logs": ".log",
        }
    }
    pin_salt = "provoware_default"
    pin_payload = {
        "enabled": False,
        "pin_hint": "Standard-PIN: 0000 (bitte ändern).",
        "pin_hash": _hash_pin("0000", pin_salt),
        "salt": pin_salt,
        "max_attempts": 3,
        "lock_min_seconds": 2,
        "lock_max_seconds": 7,
    }
    global_settings_payload = {
        "ui": {"default_theme": "auto", "contrast_mode": "normal"},
        "logging": {"level": "info", "debug": False},
        "autosave": {"enabled": True, "interval_minutes": 10},
    }
    selective_export_payload = {
        "default_preset": "support_pack",
        "output_dir": "data/exports",
        "base_name": "selective_export",
        "presets": {
            "support_pack": {
                "label": "Support-Paket (Logs, Config, Reports)",
                "includes": ["logs", "config", "reports"],
                "excludes": ["logs/*.old", "logs/*.bak"],
            },
            "logs_only": {
                "label": "Nur Logs",
                "includes": ["logs"],
                "excludes": ["logs/*.old", "logs/*.bak"],
            },
        },
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
        / "config"
        / "module_structure.json": json.dumps(structure_payload, indent=2, ensure_ascii=False)
        + "\n",
        root
        / "config"
        / "todo_config.json": json.dumps(
            {"todo_path": "todo.txt", "archive_path": "data/todo_archive.txt"},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        root
        / "config"
        / "filename_suffixes.json": json.dumps(suffix_payload, indent=2, ensure_ascii=False)
        + "\n",
        root
        / "config"
        / "global_settings.json": json.dumps(global_settings_payload, indent=2, ensure_ascii=False)
        + "\n",
        root
        / "config"
        / "selective_export.json": json.dumps(
            selective_export_payload, indent=2, ensure_ascii=False
        )
        + "\n",
        root / "config" / "pin.json": json.dumps(pin_payload, indent=2, ensure_ascii=False) + "\n",
        root
        / "data"
        / "pin_state.json": json.dumps(
            {"failed_attempts": 0, "locked_until": None}, indent=2, ensure_ascii=False
        )
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


def _backup_file(path: Path, dry_run: bool, repairs: List[str]) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.name}.bak_{timestamp}")
    if dry_run:
        repairs.append(f"Geplant: Backup anlegen: {backup}")
        return
    path.rename(backup)
    repairs.append(f"Backup angelegt: {backup}")


def _check_dir(
    item: RepairItem,
    issues: List[str],
    repairs: List[str],
    dry_run: bool,
) -> None:
    if not item.path.exists():
        if dry_run:
            repairs.append(f"Geplant: Ordner erstellen: {item.label} ({item.path}).")
            return
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
    if not item.path.is_dir():
        issues.append(f"Pfad ist kein Ordner: {item.label} ({item.path}).")


def _check_file(
    item: RepairItem,
    issues: List[str],
    repairs: List[str],
    dry_run: bool,
    defaults: dict[Path, str],
) -> None:
    if not item.path.exists():
        default_content = defaults.get(item.path)
        if default_content is None:
            issues.append(f"Self-Repair: Keine Standarddaten für {item.label} ({item.path}).")
            return
        if dry_run:
            repairs.append(f"Geplant: Datei erstellen: {item.label} ({item.path}).")
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
    if not item.path.is_file():
        issues.append(f"Pfad ist keine Datei: {item.label} ({item.path}).")
        return
    if not os.access(item.path, os.R_OK):
        if dry_run:
            repairs.append(f"Geplant: Leserechte setzen: {item.label} ({item.path}).")
            return
        try:
            mode = item.path.stat().st_mode
            item.path.chmod(mode | stat.S_IRUSR)
            logging.info("Self-Repair: Leserechte gesetzt: %s (%s).", item.label, item.path)
            repairs.append(f"Leserechte repariert: {item.label} ({item.path}).")
            return
        except OSError as exc:
            issues.append(
                f"Self-Repair fehlgeschlagen: Leserechte {item.label} ({item.path}). Grund: {exc}"
            )
            return


def _check_executable(
    item: RepairItem,
    issues: List[str],
    repairs: List[str],
    dry_run: bool,
) -> None:
    if not item.path.exists():
        issues.append(f"Skript fehlt: {item.label} ({item.path}).")
        return
    if not os.access(item.path, os.X_OK):
        if dry_run:
            repairs.append(f"Geplant: Ausführrechte setzen: {item.label} ({item.path}).")
            return
        try:
            mode = item.path.stat().st_mode
            item.path.chmod(mode | stat.S_IXUSR)
            logging.info(
                "Self-Repair: Ausführrechte gesetzt: %s (%s).",
                item.label,
                item.path,
            )
            repairs.append(f"Ausführrechte repariert: {item.label} ({item.path}).")
            return
        except OSError as exc:
            issues.append(
                f"Self-Repair fehlgeschlagen: Ausführrechte {item.label} ({item.path}). "
                f"Grund: {exc}"
            )
            return


def _check_json(
    item: RepairItem,
    issues: List[str],
    repairs: List[str],
    dry_run: bool,
    defaults: dict[Path, str],
) -> None:
    if not item.path.exists():
        return
    if not item.path.is_file():
        return
    try:
        json.loads(item.path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        default_content = defaults.get(item.path)
        if default_content is None:
            issues.append(f"JSON ungültig: {item.label} ({item.path}).")
            return
        try:
            _backup_file(item.path, dry_run, repairs)
            if dry_run:
                repairs.append(f"Geplant: JSON neu schreiben: {item.label} ({item.path}).")
                return
            item.path.write_text(default_content, encoding="utf-8")
            repairs.append(f"JSON repariert: {item.label} ({item.path}).")
        except OSError as exc:
            issues.append(
                f"Self-Repair fehlgeschlagen: JSON {item.label} ({item.path}). Grund: {exc}"
            )
    except OSError as exc:
        issues.append(f"JSON nicht lesbar: {item.label} ({item.path}). Grund: {exc}")


def run_self_repair(root: Path, dry_run: bool) -> tuple[List[str], List[str]]:
    ensure_path(root, "root", SelfRepairError)
    if not root.exists():
        raise SelfRepairError(f"Root-Verzeichnis fehlt: {root}")
    if not root.is_dir():
        raise SelfRepairError(f"Root ist kein Ordner: {root}")

    issues: List[str] = []
    repairs: List[str] = []
    defaults = build_default_files(root)

    dir_items = _ensure_items(
        [
            RepairItem(root / "config", "Konfiguration"),
            RepairItem(root / "system", "System"),
            RepairItem(root / "scripts", "Skripte"),
            RepairItem(root / "modules", "Module"),
            RepairItem(root / "data", "Daten"),
            RepairItem(root / "logs", "Logs"),
            RepairItem(root / "tests", "Tests"),
            RepairItem(root / "src", "Quellcode"),
        ],
        "Ordnerliste",
    )
    for item in dir_items:
        _check_dir(item, issues, repairs, dry_run)

    file_items = _ensure_items(
        [
            RepairItem(root / "config" / "modules.json", "Modul-Liste"),
            RepairItem(root / "config" / "launcher_gui.json", "GUI-Konfiguration"),
            RepairItem(root / "config" / "requirements.txt", "Abhängigkeiten"),
            RepairItem(root / "config" / "test_gate.json", "Test-Sperre"),
            RepairItem(root / "config" / "module_selftests.json", "Modul-Selbsttests"),
            RepairItem(root / "config" / "module_structure.json", "Modul-Struktur"),
            RepairItem(root / "config" / "todo_config.json", "To-Do-Konfig"),
            RepairItem(root / "config" / "filename_suffixes.json", "Suffix-Standards"),
            RepairItem(root / "config" / "global_settings.json", "Global-Settings"),
            RepairItem(root / "config" / "pin.json", "PIN-Konfiguration"),
            RepairItem(root / "data" / "pin_state.json", "PIN-Status"),
            RepairItem(root / "todo.txt", "To-Do-Liste"),
            RepairItem(root / "CHANGELOG.md", "Changelog"),
            RepairItem(root / "DEV_DOKU.md", "Entwickler-Dokumentation"),
            RepairItem(root / "DONE.md", "Done-Liste"),
            RepairItem(root / "PROGRESS.md", "Fortschritt"),
        ],
        "Dateiliste",
    )
    for item in file_items:
        _check_file(item, issues, repairs, dry_run, defaults)

    json_items = _ensure_items(
        [
            RepairItem(root / "config" / "modules.json", "Modul-Liste"),
            RepairItem(root / "config" / "launcher_gui.json", "GUI-Konfiguration"),
            RepairItem(root / "config" / "test_gate.json", "Test-Sperre"),
            RepairItem(root / "config" / "module_selftests.json", "Modul-Selbsttests"),
            RepairItem(root / "config" / "module_structure.json", "Modul-Struktur"),
            RepairItem(root / "config" / "todo_config.json", "To-Do-Konfig"),
            RepairItem(root / "config" / "filename_suffixes.json", "Suffix-Standards"),
            RepairItem(root / "config" / "global_settings.json", "Global-Settings"),
            RepairItem(root / "config" / "pin.json", "PIN-Konfiguration"),
            RepairItem(root / "data" / "pin_state.json", "PIN-Status"),
        ],
        "JSON-Liste",
    )
    for item in json_items:
        _check_json(item, issues, repairs, dry_run, defaults)

    script_items = _ensure_items(
        [
            RepairItem(root / "scripts" / "start.sh", "Start-Routine"),
            RepairItem(root / "scripts" / "run_tests.sh", "Testskript"),
            RepairItem(root / "klick_start.sh", "Klick&Start"),
        ],
        "Skriptliste",
    )
    for item in script_items:
        _check_executable(item, issues, repairs, dry_run)

    filename_fixes = run_filename_fix(root, dry_run)
    if filename_fixes:
        repairs.extend(filename_fixes)

    return issues, repairs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Self-Repair: repariert fehlende Dateien, JSON und Rechte automatisch.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Projekt-Root (Standard: Repository-Wurzel).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, nichts ändern.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug-Modus aktivieren.",
    )
    return parser


def setup_logging(debug: bool) -> None:
    setup_logging_center(debug)


def _render_output(issues: Iterable[str], repairs: Iterable[str], dry_run: bool) -> str:
    issues_list = list(issues)
    repairs_list = list(repairs)
    if not issues_list:
        if repairs_list:
            lines = [
                "Self-Repair: Ausgeführt.",
                "",
            ]
            lines.extend([f"- {repair}" for repair in repairs_list])
            lines.append("")
            lines.append("Self-Repair: Alle wichtigen Dateien und Ordner sind vorhanden.")
            return "\n".join(lines)
        return "Self-Repair: Keine Probleme gefunden."

    lines = ["Self-Repair: Probleme gefunden:", ""]
    lines.extend([f"- {issue}" for issue in issues_list])
    if repairs_list:
        lines.append("")
        lines.append(
            "Hinweis: Reparaturen wurden ausgeführt."
            if not dry_run
            else "Hinweis: Reparaturen sind geplant (dry-run)."
        )
        lines.extend([f"- {repair}" for repair in repairs_list])
    lines.append("")
    lines.append("Bitte die Hinweise prüfen und erneut starten.")
    return "\n".join(lines)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.debug)

    try:
        issues, repairs = run_self_repair(args.root, dry_run=args.dry_run)
    except SelfRepairError as exc:
        logging.error("Self-Repair konnte nicht starten: %s", exc)
        return 2

    output = _render_output(issues, repairs, args.dry_run)
    print(output)

    if issues:
        logging.error("Self-Repair: %s Problem(e) gefunden.", len(issues))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

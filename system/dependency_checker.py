#!/usr/bin/env python3
"""Prüft Python-Abhängigkeiten und installiert sie bei Bedarf."""

from __future__ import annotations

import argparse
import importlib.util
import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path

DEFAULT_REQUIREMENTS = Path(__file__).resolve().parents[1] / "config" / "requirements.txt"


class DependencyError(Exception):
    """Fehler bei der Abhängigkeitsprüfung."""


@dataclass(frozen=True)
class DependencyCheckResult:
    total: int
    missing: List[str]


def _strip_inline_comment(line: str) -> str:
    if not isinstance(line, str):
        raise DependencyError("Requirements-Zeile ist kein Text.")
    cleaned = line.strip()
    match = re.search(r"\s+#", cleaned)
    if match:
        cleaned = cleaned[: match.start()].strip()
    return cleaned


def _read_requirements(path: Path) -> List[str]:
    ensure_path(path, "requirements", DependencyError)
    if not path.exists():
        raise DependencyError(f"Requirements-Datei fehlt: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    requirements: List[str] = []
    for line in lines:
        cleaned = _strip_inline_comment(line)
        if not cleaned or cleaned.startswith("#"):
            continue
        requirements.append(cleaned)
    return requirements


def _normalize_module_name(requirement: str) -> str:
    if not isinstance(requirement, str) or not requirement.strip():
        raise DependencyError("Abhängigkeit ist leer oder ungültig.")

    cleaned = requirement.split(";")[0].strip()
    cleaned = cleaned.split("[")[0].strip()
    cleaned = re.split(r"[<>=!~]", cleaned)[0].strip()
    if not cleaned:
        raise DependencyError("Abhängigkeit enthält keinen Paketnamen.")
    return cleaned.replace("-", "_")


def _check_missing(requirements: Iterable[str]) -> DependencyCheckResult:
    missing: List[str] = []
    total = 0
    for requirement in requirements:
        module_name = _normalize_module_name(requirement)
        total += 1
        if importlib.util.find_spec(module_name) is None:
            missing.append(requirement)
    return DependencyCheckResult(total=total, missing=missing)


def _install_requirements(path: Path) -> None:
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(path)]
    logging.info("Starte Installation: %s", " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise DependencyError(
            "Installation der Abhängigkeiten fehlgeschlagen. "
            "Bitte prüfen Sie die Ausgabe von pip."
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prüft Python-Abhängigkeiten und installiert sie bei Bedarf.",
    )
    parser.add_argument(
        "--requirements",
        type=Path,
        default=DEFAULT_REQUIREMENTS,
        help="Pfad zur Requirements-Datei.",
    )
    parser.add_argument(
        "--no-auto-install",
        action="store_true",
        help="Installiert fehlende Pakete nicht automatisch.",
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


def _render_missing(missing: Iterable[str]) -> str:
    items = ", ".join(missing)
    return f"Fehlende Abhängigkeiten: {items}"


def _render_next_steps(no_auto_install: bool) -> List[str]:
    steps = [
        "Tipp: Abhängigkeiten installieren mit: python -m pip install -r config/requirements.txt.",
        "Hinweis: Im Safe-Mode werden keine Pakete installiert.",
    ]
    if no_auto_install:
        steps.append("Auto-Installation ist deaktiviert. Bitte Installation manuell starten.")
    else:
        steps.append("Auto-Installation ist aktiv und wird jetzt gestartet.")
    return steps


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.debug)

    try:
        requirements = _read_requirements(args.requirements)
    except DependencyError as exc:
        logging.error("Abhängigkeitsprüfung konnte nicht starten: %s", exc)
        return 2

    if not requirements:
        print("Abhängigkeiten: Keine Einträge in requirements.txt. Weiter.")
        return 0

    try:
        result = _check_missing(requirements)
    except DependencyError as exc:
        logging.error("Abhängigkeitsprüfung fehlgeschlagen: %s", exc)
        return 2

    if not result.missing:
        print("Abhängigkeiten: Alle Pakete vorhanden.")
        return 0

    print(_render_missing(result.missing))
    for line in _render_next_steps(args.no_auto_install):
        print(line)
    if args.no_auto_install:
        return 1

    print("Abhängigkeiten: Installation wird gestartet.")
    try:
        _install_requirements(args.requirements)
    except DependencyError as exc:
        logging.error("Abhängigkeits-Installation fehlgeschlagen: %s", exc)
        return 2

    result = _check_missing(requirements)
    if result.missing:
        logging.error("Nach der Installation fehlen weiterhin Pakete.")
        print(_render_missing(result.missing))
        return 2

    print("Abhängigkeiten: Installation erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

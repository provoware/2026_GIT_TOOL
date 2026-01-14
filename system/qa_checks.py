#!/usr/bin/env python3
"""Qualitäts-Checks für Fehlerklassifizierung und Ampelsystem."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


class QualityCheckError(Exception):
    """Fehler in den Qualitäts-Checks."""


Severity = str


@dataclass(frozen=True)
class FileIssue:
    label: str
    path: Path
    message: str
    severity: Severity


@dataclass(frozen=True)
class FileStatusReport:
    issues: List[FileIssue]
    traffic_light: str


def classify_issue(message: str) -> Severity:
    if not isinstance(message, str) or not message.strip():
        raise QualityCheckError("Fehlertext ist leer oder ungültig.")
    lowered = message.lower()
    severe_markers = ["fehlt", "ungültig", "nicht lesbar", "kein gültiges json", "kein json"]
    mild_markers = ["hinweis", "optional", "deaktiviert"]
    if any(marker in lowered for marker in severe_markers):
        return "schwer"
    if any(marker in lowered for marker in mild_markers):
        return "leicht"
    return "mittel"


def traffic_light(issues: Iterable[FileIssue]) -> str:
    severities = {issue.severity for issue in issues}
    if "schwer" in severities:
        return "rot"
    if "mittel" in severities or "leicht" in severities:
        return "gelb"
    return "grün"


def _read_json(path: Path) -> None:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QualityCheckError(f"JSON ist ungültig: {path}") from exc


def check_release_files(root: Path) -> FileStatusReport:
    if not isinstance(root, Path):
        raise QualityCheckError("root ist kein Pfad (Path).")

    checks = [
        ("config/modules.json", "Modul-Konfiguration", True, "json"),
        ("config/launcher_gui.json", "GUI-Konfiguration", True, "json"),
        ("config/pytest.ini", "Pytest-Konfiguration", True, "file"),
        ("config/ruff.toml", "Ruff-Konfiguration", True, "file"),
        ("config/black.toml", "Black-Konfiguration", True, "file"),
        ("config/module_selftests.json", "Modul-Selbsttests", True, "json"),
        ("todo.txt", "Kurzliste (todo.txt)", True, "file"),
        ("scripts/start.sh", "Startskript", True, "file"),
        ("scripts/run_tests.sh", "Tests-Skript", True, "file"),
    ]

    issues: List[FileIssue] = []
    for rel_path, label, required, check_type in checks:
        path = root / rel_path
        if not path.exists():
            severity = "schwer" if required else "mittel"
            issues.append(
                FileIssue(
                    label=label,
                    path=path,
                    message=f"Datei fehlt: {label} ({path}).",
                    severity=severity,
                )
            )
            continue
        if check_type == "json":
            try:
                _read_json(path)
            except QualityCheckError as exc:
                issues.append(
                    FileIssue(
                        label=label,
                        path=path,
                        message=str(exc),
                        severity="schwer",
                    )
                )
        if not path.is_file():
            issues.append(
                FileIssue(
                    label=label,
                    path=path,
                    message=f"Pfad ist keine Datei: {label} ({path}).",
                    severity="schwer",
                )
            )

    return FileStatusReport(issues=issues, traffic_light=traffic_light(issues))

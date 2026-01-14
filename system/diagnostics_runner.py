#!/usr/bin/env python3
"""Diagnose-Runner: startet Tests und sammelt Ergebnisse für die GUI."""

from __future__ import annotations

import argparse
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from config_utils import ensure_path

DEFAULT_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_tests.sh"


class DiagnosticsError(ValueError):
    """Fehler beim Diagnose-Lauf."""


@dataclass(frozen=True)
class DiagnosticsResult:
    status: str
    output: str
    exit_code: int
    duration_seconds: float
    command: List[str]


def _require_positive_int(value: int, label: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise DiagnosticsError(f"{label} ist keine gültige positive Zahl.")
    return value


def _build_command(script_path: Path) -> List[str]:
    if not isinstance(script_path, Path):
        raise DiagnosticsError("script_path ist kein Pfad (Path).")
    if not script_path.exists():
        raise DiagnosticsError(f"Diagnose-Skript fehlt: {script_path}")
    if not script_path.is_file():
        raise DiagnosticsError(f"Diagnose-Skript ist keine Datei: {script_path}")
    return ["bash", str(script_path)]


def run_diagnostics(script_path: Path, timeout_seconds: int = 900) -> DiagnosticsResult:
    ensure_path(script_path, "script_path", DiagnosticsError)
    timeout_seconds = _require_positive_int(timeout_seconds, "timeout_seconds")
    command = _build_command(script_path)
    start = time.time()
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.time() - start
        output = (exc.stdout or "") + (exc.stderr or "")
        return DiagnosticsResult(
            status="timeout",
            output=output.strip() or "Diagnose abgebrochen: Zeitlimit erreicht.",
            exit_code=124,
            duration_seconds=duration,
            command=command,
        )
    duration = time.time() - start
    combined = (result.stdout or "") + (result.stderr or "")
    status = "ok" if result.returncode == 0 else "error"
    output = combined.strip() or "Keine Ausgabe erhalten."
    return DiagnosticsResult(
        status=status,
        output=output,
        exit_code=result.returncode,
        duration_seconds=duration,
        command=command,
    )


def _format_summary(result: DiagnosticsResult) -> str:
    if not isinstance(result, DiagnosticsResult):
        raise DiagnosticsError("result ist ungültig.")
    duration = f"{result.duration_seconds:.1f}"
    return (
        "Diagnose-Ergebnis:\n"
        f"- Status: {result.status}\n"
        f"- Exit-Code: {result.exit_code}\n"
        f"- Dauer: {duration} Sekunden\n"
        f"- Kommando: {' '.join(result.command)}\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Startet die Diagnose (Tests + Qualität) und sammelt Ergebnisse.",
    )
    parser.add_argument(
        "--script",
        type=Path,
        default=DEFAULT_SCRIPT,
        help="Pfad zum Diagnose-Skript (Standard: scripts/run_tests.sh).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Zeitlimit in Sekunden (Standard: 900).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = run_diagnostics(args.script, timeout_seconds=args.timeout)
    except DiagnosticsError as exc:
        print(f"Diagnose fehlgeschlagen: {exc}")
        return 2

    print(_format_summary(result))
    print(result.output)
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

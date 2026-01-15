#!/usr/bin/env python3
"""Ein-Datei-Entry: startet die Start-Routine aus dem One-File-Build."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _resolve_root() -> Path:
    if getattr(sys, "frozen", False):
        base_path = Path(getattr(sys, "_MEIPASS", Path.cwd()))
        return base_path
    return Path(__file__).resolve().parents[1]


def _build_start_command(root: Path) -> list[str]:
    script_path = root / "scripts" / "start.sh"
    if not script_path.exists():
        raise FileNotFoundError(f"Start-Skript fehlt: {script_path}")
    return ["bash", str(script_path)]


def main() -> int:
    root = _resolve_root()
    bash_path = shutil.which("bash")
    if not bash_path:
        print("Fehler: Bash fehlt. Bitte bash installieren.")
        print("Lösung: Auf Linux bash nachinstallieren und erneut starten.")
        return 1

    try:
        command = _build_start_command(root)
    except FileNotFoundError as exc:
        print(f"Fehler: {exc}")
        print("Lösung: One-File-Build neu erstellen und alle Daten anhängen.")
        return 1

    print("One-File-Start: Start-Routine wird ausgeführt...")
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print(f"Fehler: Start-Routine beendet (Exit-Code: {result.returncode}).")
        print("Lösung: ./scripts/start.sh manuell ausführen und Logs prüfen.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

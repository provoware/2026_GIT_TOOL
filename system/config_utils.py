#!/usr/bin/env python3
"""Hilfsfunktionen für Pfad- und JSON-Validierung."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Type


def ensure_path(path: Path, label: str, error_cls: Type[Exception]) -> None:
    """Stellt sicher, dass ein echter Path übergeben wurde."""
    if not isinstance(path, Path):
        raise error_cls(f"{label} ist kein Pfad (Path).")


def load_json(
    path: Path,
    error_cls: Type[Exception],
    missing_label: str,
    invalid_label: str,
) -> dict:
    """Lädt JSON-Dateien mit klaren Fehlermeldungen."""
    ensure_path(path, "config_path", error_cls)
    if not isinstance(missing_label, str) or not missing_label.strip():
        raise error_cls("missing_label fehlt oder ist leer.")
    if not isinstance(invalid_label, str) or not invalid_label.strip():
        raise error_cls("invalid_label fehlt oder ist leer.")
    if not path.exists():
        raise error_cls(f"{missing_label}: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise error_cls(f"{invalid_label}: {path}") from exc

#!/usr/bin/env python3
"""Modul-Check: Prüft registrierte Module und deren Struktur."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

CONFIG_DEFAULT = Path(__file__).resolve().parents[1] / "config" / "modules.json"


class ModuleCheckError(Exception):
    """Allgemeiner Fehler für den Modul-Check."""


@dataclass(frozen=True)
class ModuleEntry:
    module_id: str
    name: str
    path: Path
    enabled: bool
    description: str


@dataclass(frozen=True)
class ModuleManifest:
    module_id: str
    name: str
    version: str
    description: str
    entry: str


def _ensure_path(path: Path, label: str) -> None:
    if not isinstance(path, Path):
        raise ModuleCheckError(f"{label} ist kein Pfad (Path).")


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise ModuleCheckError(f"Konfiguration fehlt: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModuleCheckError(f"Konfiguration ist kein gültiges JSON: {path}") from exc


def _resolve_path(root: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else root / candidate


def load_modules(config_path: Path) -> List[ModuleEntry]:
    _ensure_path(config_path, "config_path")
    data = _load_json(config_path)
    raw_modules = data.get("modules", [])
    if not isinstance(raw_modules, list) or not raw_modules:
        raise ModuleCheckError("Keine Module in der Konfiguration gefunden.")

    root = config_path.resolve().parents[1]
    entries: List[ModuleEntry] = []
    for entry in raw_modules:
        module_id = str(entry.get("id", "")).strip()
        name = str(entry.get("name", "")).strip()
        path_value = str(entry.get("path", "")).strip()
        enabled = bool(entry.get("enabled", False))
        description = str(entry.get("description", "")).strip()
        if not module_id or not name or not path_value:
            raise ModuleCheckError(
                "Modul-Eintrag unvollständig. Bitte id, name und path setzen."
            )
        entries.append(
            ModuleEntry(
                module_id=module_id,
                name=name,
                path=_resolve_path(root, path_value),
                enabled=enabled,
                description=description,
            )
        )
    return entries


def load_manifest(module_dir: Path) -> ModuleManifest:
    manifest_path = module_dir / "manifest.json"
    if not manifest_path.exists():
        raise ModuleCheckError(f"Manifest fehlt: {manifest_path}")
    data = _load_json(manifest_path)
    module_id = str(data.get("id", "")).strip()
    name = str(data.get("name", "")).strip()
    version = str(data.get("version", "")).strip()
    description = str(data.get("description", "")).strip()
    entry = str(data.get("entry", "")).strip()
    if not module_id or not name or not version or not entry:
        raise ModuleCheckError(
            f"Manifest unvollständig: {manifest_path}. Bitte id, name, version und entry setzen."
        )
    return ModuleManifest(
        module_id=module_id,
        name=name,
        version=version,
        description=description,
        entry=entry,
    )


def check_modules(entries: Iterable[ModuleEntry]) -> List[str]:
    issues: List[str] = []
    for entry in entries:
        if not entry.enabled:
            logging.info("Modul deaktiviert: %s", entry.module_id)
            continue
        if not entry.path.exists():
            issues.append(f"Modul fehlt: {entry.module_id} (Pfad: {entry.path})")
            continue
        try:
            manifest = load_manifest(entry.path)
        except ModuleCheckError as exc:
            issues.append(str(exc))
            continue
        entry_path = entry.path / manifest.entry
        if not entry_path.exists():
            issues.append(
                "Modul-Datei fehlt: "
                f"{manifest.entry} (Modul: {entry.module_id})"
            )
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Modul-Check: Prüft registrierte Module und deren Struktur.",
    )
    parser.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren")
    return parser


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.debug)

    try:
        entries = load_modules(args.config)
    except ModuleCheckError as exc:
        logging.error("Modul-Check konnte nicht gestartet werden: %s", exc)
        return 2

    issues = check_modules(entries)
    if issues:
        logging.error("Modul-Check fehlgeschlagen: %s Problem(e) gefunden.", len(issues))
        for issue in issues:
            logging.error("- %s", issue)
        logging.error("Bitte Konfiguration oder Modulstruktur korrigieren.")
        return 2

    logging.info("Modul-Check erfolgreich. Alle aktiven Module sind vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

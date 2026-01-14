#!/usr/bin/env python3
"""Modul-Check: Prüft registrierte Module und deren Struktur."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path
from logging_center import get_logger
from logging_center import setup_logging as setup_logging_center
from module_api_validator import validate_module_api
from module_registry import (
    ModuleEntry,
    ModuleManifest,
    ModuleRegistryError,
    load_registry,
)
from module_registry import (
    load_manifest as registry_load_manifest,
)
from module_registry import (
    resolve_entry_path as registry_resolve_entry_path,
)

CONFIG_DEFAULT = Path(__file__).resolve().parents[1] / "config" / "modules.json"


class ModuleCheckError(Exception):
    """Allgemeiner Fehler für den Modul-Check."""


def load_modules(config_path: Path) -> List[ModuleEntry]:
    ensure_path(config_path, "config_path", ModuleCheckError)
    try:
        registry = load_registry(config_path)
    except ModuleRegistryError as exc:
        raise ModuleCheckError(str(exc)) from exc
    return registry.entries


def load_manifest(module_dir: Path) -> ModuleManifest:
    try:
        return registry_load_manifest(module_dir)
    except ModuleRegistryError as exc:
        raise ModuleCheckError(str(exc)) from exc


def resolve_entry_path(module_dir: Path, entry: str) -> Path:
    try:
        return registry_resolve_entry_path(module_dir, entry)
    except ModuleRegistryError as exc:
        raise ModuleCheckError(str(exc)) from exc


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
        try:
            entry_path = resolve_entry_path(entry.path, manifest.entry)
        except ModuleCheckError as exc:
            issues.append(str(exc))
            continue
        if not entry_path.exists():
            issues.append("Modul-Datei fehlt: " f"{manifest.entry} (Modul: {entry.module_id})")
            continue
        issues.extend(validate_module_api(entry_path))
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Modul-Check: Prüft registrierte Module und deren Struktur.",
    )
    parser.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren")
    return parser


def setup_logging(debug: bool) -> None:
    setup_logging_center(debug)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.debug)
    logger = get_logger("module_check")

    try:
        entries = load_modules(args.config)
    except ModuleCheckError as exc:
        logger.error("Modul-Check konnte nicht gestartet werden: %s", exc)
        return 2

    issues = check_modules(entries)
    if issues:
        logger.error("Modul-Check fehlgeschlagen: %s Problem(e) gefunden.", len(issues))
        for issue in issues:
            logger.error("- %s", issue)
        logger.error("Bitte Konfiguration oder Modulstruktur korrigieren.")
        return 2

    logger.info("Modul-Check erfolgreich. Alle aktiven Module sind vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

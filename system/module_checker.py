#!/usr/bin/env python3
"""Modul-Check: Prüft registrierte Module und deren Struktur."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path, load_json
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
STRUCTURE_CONFIG_DEFAULT = (
    Path(__file__).resolve().parents[1] / "config" / "module_structure.json"
)


@dataclass(frozen=True)
class ModuleStructureConfig:
    required_entry: str
    entry_exceptions: frozenset[str]
    required_files: tuple[str, ...]


class ModuleCheckError(Exception):
    """Allgemeiner Fehler für den Modul-Check."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModuleCheckError(f"{label} ist leer oder ungültig.")
    return value.strip()


def _require_string_list(
    value: object,
    label: str,
    allow_empty: bool = True,
) -> tuple[str, ...]:
    if value is None:
        return tuple()
    if not isinstance(value, list):
        raise ModuleCheckError(f"{label} ist keine Liste.")
    if not value and not allow_empty:
        raise ModuleCheckError(f"{label} ist leer.")
    items: List[str] = []
    for entry in value:
        if not isinstance(entry, str) or not entry.strip():
            raise ModuleCheckError(f"{label} enthält ungültige Einträge.")
        items.append(entry.strip())
    return tuple(items)


def load_structure_config(
    config_path: Path = STRUCTURE_CONFIG_DEFAULT,
) -> ModuleStructureConfig:
    data = load_json(
        config_path,
        ModuleCheckError,
        "Struktur-Konfiguration fehlt",
        "Struktur-Konfiguration ist ungültig",
    )
    required_entry = _require_text(data.get("required_entry"), "required_entry")
    required_files = _require_string_list(
        data.get("required_files"),
        "required_files",
        allow_empty=False,
    )
    exceptions = _require_string_list(
        data.get("entry_exceptions", []),
        "entry_exceptions",
        allow_empty=True,
    )
    return ModuleStructureConfig(
        required_entry=required_entry,
        entry_exceptions=frozenset(exceptions),
        required_files=required_files,
    )


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


def check_modules(
    entries: Iterable[ModuleEntry],
    structure_config: ModuleStructureConfig | None = None,
) -> List[str]:
    issues: List[str] = []
    if structure_config is None:
        try:
            structure_config = load_structure_config()
        except ModuleCheckError as exc:
            return [str(exc)]
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
        if structure_config.required_files:
            for required in structure_config.required_files:
                required_path = entry.path / required
                if not required_path.exists():
                    issues.append(
                        "Modulstruktur unvollständig: "
                        f"{required} fehlt (Modul: {entry.module_id})."
                    )
        if (
            manifest.entry != structure_config.required_entry
            and entry.module_id not in structure_config.entry_exceptions
        ):
            issues.append(
                "Modulstruktur unzulässig: "
                f"entry muss '{structure_config.required_entry}' sein "
                f"(Modul: {entry.module_id})."
            )
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

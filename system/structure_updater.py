#!/usr/bin/env python3
"""Struktur- und Manifest-Updater: pflegt Baumstruktur, Register und Manifest."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from config_models import ConfigModelError, load_modules_config
from config_utils import ensure_path
from module_registry import ModuleRegistryError, load_manifest, resolve_entry_path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SKIP = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
}


class StructureUpdaterError(ValueError):
    """Fehler beim Struktur-Update."""


@dataclass(frozen=True)
class ModuleSnapshot:
    module_id: str
    name: str
    version: str
    entry: str
    path: str
    enabled: bool
    description: str


@dataclass(frozen=True)
class UpdateResult:
    tree_lines: List[str]
    manifest_payload: Dict[str, object]
    register_payload: Dict[str, object]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sorted_entries(path: Path, skip: Sequence[str]) -> List[Path]:
    entries = []
    for entry in path.iterdir():
        if entry.name in skip:
            continue
        if entry.name.startswith(".") and entry.name not in {".well-known"}:
            continue
        entries.append(entry)
    return sorted(entries, key=lambda p: (not p.is_dir(), p.name.lower()))


def _build_tree_lines(path: Path, skip: Sequence[str], prefix: str = "") -> List[str]:
    lines: List[str] = []
    entries = _sorted_entries(path, skip)
    for index, entry in enumerate(entries):
        connector = "└──" if index == len(entries) - 1 else "├──"
        label = f"{entry.name}/" if entry.is_dir() else entry.name
        lines.append(f"{prefix}{connector} {label}")
        if entry.is_dir():
            extension = "    " if index == len(entries) - 1 else "│   "
            lines.extend(_build_tree_lines(entry, skip, prefix + extension))
    return lines


def build_tree(root: Path, skip: Sequence[str]) -> List[str]:
    ensure_path(root, "root", StructureUpdaterError)
    if not root.exists():
        raise StructureUpdaterError(f"Root-Pfad existiert nicht: {root}")
    tree = [f"Projektstruktur ({root.name})", ""]
    tree.extend(_build_tree_lines(root, skip))
    tree.append("")
    tree.append(f"Stand: {_utc_now_iso()}")
    return tree


def _load_module_snapshots(root: Path) -> List[ModuleSnapshot]:
    config_path = root / "config" / "modules.json"
    if not config_path.exists():
        raise StructureUpdaterError(f"Module-Konfiguration fehlt: {config_path}")
    try:
        config = load_modules_config(config_path)
    except ConfigModelError as exc:
        raise StructureUpdaterError(str(exc)) from exc

    snapshots: List[ModuleSnapshot] = []
    for entry in config.modules:
        module_dir = (root / entry.path).resolve()
        if not module_dir.exists():
            raise StructureUpdaterError(f"Modulordner fehlt: {module_dir}")
        try:
            manifest = load_manifest(module_dir)
        except ModuleRegistryError as exc:
            raise StructureUpdaterError(str(exc)) from exc
        try:
            resolved_entry = resolve_entry_path(module_dir, manifest.entry)
        except ModuleRegistryError as exc:
            raise StructureUpdaterError(str(exc)) from exc
        if not resolved_entry.exists():
            raise StructureUpdaterError(f"Entry-Datei fehlt: {resolved_entry}")
        snapshots.append(
            ModuleSnapshot(
                module_id=manifest.module_id,
                name=manifest.name,
                version=manifest.version,
                entry=manifest.entry,
                path=str(Path(entry.path).as_posix()),
                enabled=entry.enabled,
                description=entry.description,
            )
        )
    return snapshots


def _build_manifest_payload(modules: Iterable[ModuleSnapshot]) -> Dict[str, object]:
    module_list = [
        {
            "id": module.module_id,
            "name": module.name,
            "version": module.version,
            "entry": module.entry,
            "path": module.path,
        }
        for module in modules
    ]
    return {
        "generated_at": _utc_now_iso(),
        "modules": module_list,
    }


def _build_register_payload(modules: Iterable[ModuleSnapshot]) -> Dict[str, object]:
    entries = [
        {
            "id": module.module_id,
            "name": module.name,
            "path": module.path,
            "entry": module.entry,
            "enabled": module.enabled,
            "description": module.description,
        }
        for module in modules
    ]
    return {
        "_hinweis": "Automatisch gepflegt. Bitte nicht manuell bearbeiten.",
        "generated_at": _utc_now_iso(),
        "entries": entries,
    }


def _write_json(path: Path, payload: Dict[str, object], write: bool) -> None:
    ensure_path(path, "path", StructureUpdaterError)
    content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if write:
        path.write_text(content, encoding="utf-8")


def run_update(root: Path, write: bool, skip: Sequence[str], logger: logging.Logger) -> UpdateResult:
    ensure_path(root, "root", StructureUpdaterError)
    tree_lines = build_tree(root, skip)
    module_snapshots = _load_module_snapshots(root)
    manifest_payload = _build_manifest_payload(module_snapshots)
    register_payload = _build_register_payload(module_snapshots)

    if write:
        tree_path = root / "data" / "baumstruktur.txt"
        tree_path.write_text("\n".join(tree_lines) + "\n", encoding="utf-8")
        logger.info("Baumstruktur aktualisiert: %s", tree_path)

        manifest_path = root / "data" / "manifest.json"
        _write_json(manifest_path, manifest_payload, write=True)
        logger.info("Manifest aktualisiert: %s", manifest_path)

        register_path = root / "data" / "dummy_register.json"
        _write_json(register_path, register_payload, write=True)
        logger.info("Register aktualisiert: %s", register_path)
    else:
        logger.info("Testlauf aktiv: Dateien werden nicht geschrieben.")

    return UpdateResult(
        tree_lines=tree_lines,
        manifest_payload=manifest_payload,
        register_payload=register_payload,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Aktualisiert baumstruktur.txt, manifest.json und dummy_register.json automatisch."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Projekt-Root (Standard: Repository-Wurzel).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Änderungen schreiben (sonst nur prüfen).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug-Ausgaben aktivieren.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    logger = logging.getLogger("structure-updater")

    try:
        run_update(args.root, args.write, sorted(DEFAULT_SKIP), logger)
    except StructureUpdaterError as exc:
        logger.error("Struktur-Update fehlgeschlagen: %s", exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from config_models import (
    ConfigModelError,
    ModulesConfigModel,
    load_modules_config,
)
from store import STORE


class ModuleRegistryError(ValueError):
    pass


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
    entry: str


class ModuleRegistry:
    def __init__(self, config_path: Path, entries: Iterable[ModuleEntry]) -> None:
        self.config_path = config_path
        self._entries = list(entries)
        self._index: Dict[str, ModuleEntry] = {entry.module_id: entry for entry in self._entries}

    @property
    def entries(self) -> List[ModuleEntry]:
        return list(self._entries)

    def list_modules(self, include_disabled: bool = False) -> List[ModuleEntry]:
        if include_disabled:
            return self.entries
        return [entry for entry in self._entries if entry.enabled]

    def get_module(self, module_id: str) -> Optional[ModuleEntry]:
        if not isinstance(module_id, str) or not module_id.strip():
            raise ModuleRegistryError("module_id ist leer oder ungültig.")
        return self._index.get(module_id.strip())


def load_registry(config_path: Path) -> ModuleRegistry:
    if not isinstance(config_path, Path):
        raise ModuleRegistryError("config_path ist kein Pfad (Path).")
    try:
        model = load_modules_config(config_path)
    except ConfigModelError as exc:
        raise ModuleRegistryError(str(exc)) from exc
    entries = _convert_entries(model, config_path)
    registry = ModuleRegistry(config_path=config_path, entries=entries)
    STORE.set_modules(registry.entries)
    return registry


def load_manifest(module_dir: Path) -> ModuleManifest:
    manifest_path = module_dir / "manifest.json"
    if not manifest_path.exists():
        raise ModuleRegistryError(f"Manifest fehlt: {manifest_path}")
    data = _load_json(manifest_path)
    module_id = _require_text(data.get("id"), "manifest.id")
    name = _require_text(data.get("name"), "manifest.name")
    version = _require_text(data.get("version"), "manifest.version")
    entry = _require_text(data.get("entry"), "manifest.entry")
    return ModuleManifest(module_id=module_id, name=name, version=version, entry=entry)


def resolve_entry_path(module_dir: Path, entry: str) -> Path:
    if not isinstance(module_dir, Path):
        raise ModuleRegistryError("module_dir ist kein Pfad (Path).")
    if not isinstance(entry, str) or not entry.strip():
        raise ModuleRegistryError("Manifest: entry fehlt oder ist leer.")
    entry_path = Path(entry)
    if entry_path.is_absolute():
        raise ModuleRegistryError("Manifest: entry darf kein absoluter Pfad sein.")
    if ".." in entry_path.parts:
        raise ModuleRegistryError(
            "Manifest: entry enthält unzulässige Pfadsegmente ('..') "
            "und liegt damit außerhalb des Modulordners."
        )
    resolved = (module_dir / entry_path).resolve()
    module_root = module_dir.resolve()
    if module_root not in resolved.parents and resolved != module_root:
        raise ModuleRegistryError("Manifest: entry liegt außerhalb des Modulordners.")
    return resolved


def _convert_entries(model: ModulesConfigModel, config_path: Path) -> List[ModuleEntry]:
    base_dir = config_path.resolve().parents[1]
    entries: List[ModuleEntry] = []
    for entry in model.modules:
        module_dir = _resolve_module_path(base_dir, entry.path)
        entries.append(
            ModuleEntry(
                module_id=entry.module_id,
                name=entry.name,
                path=module_dir,
                enabled=entry.enabled,
                description=entry.description,
            )
        )
    return entries


def _resolve_module_path(root: Path, module_path: str) -> Path:
    candidate = Path(module_path)
    if candidate.is_absolute():
        raise ModuleRegistryError("Modul-Pfad darf nicht absolut sein.")
    resolved = (root / candidate).resolve()
    root_dir = root.resolve()
    if root_dir not in resolved.parents and resolved != root_dir:
        raise ModuleRegistryError("Modul-Pfad liegt außerhalb des Projektordners.")
    return resolved


def _load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ModuleRegistryError(f"Manifest ist kein gültiges JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ModuleRegistryError("Manifest ist kein Objekt (dict).")
    return data


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModuleRegistryError(f"{field} ist leer oder ungültig.")
    return value.strip()

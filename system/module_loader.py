from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict


class ModuleLoaderError(ValueError):
    pass


@dataclass
class ModuleLoader:
    _cache: Dict[str, Any] = field(default_factory=dict)

    def load(self, module_id: str, entry_path: Path) -> Any:
        if not isinstance(module_id, str) or not module_id.strip():
            raise ModuleLoaderError("module_id ist leer oder ungültig.")
        if not isinstance(entry_path, Path):
            raise ModuleLoaderError("entry_path ist kein Pfad (Path).")
        cached = self._cache.get(module_id)
        if cached is not None:
            return cached
        if not entry_path.exists():
            raise ModuleLoaderError(f"Modul-Datei fehlt: {entry_path}")
        spec = importlib.util.spec_from_file_location(module_id, entry_path)
        if spec is None or spec.loader is None:
            raise ModuleLoaderError(f"Modul konnte nicht geladen werden: {entry_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._cache[module_id] = module
        return module


MODULE_LOADER = ModuleLoader()

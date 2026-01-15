from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from event_bus import EVENT_BUS


class ModuleLoaderError(ValueError):
    pass


ROOT_DIR = Path(__file__).resolve().parents[1]


def _ensure_root_on_path() -> None:
    root_str = str(ROOT_DIR)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


@dataclass
class ModuleLoader:
    _cache: Dict[tuple[str, Path], Any] = field(default_factory=dict)

    def load(self, module_id: str, entry_path: Path) -> Any:
        if not isinstance(module_id, str) or not module_id.strip():
            raise ModuleLoaderError("module_id ist leer oder ungültig.")
        if not isinstance(entry_path, Path):
            raise ModuleLoaderError("entry_path ist kein Pfad (Path).")
        cache_key = (module_id.strip(), entry_path.resolve())
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        if not entry_path.exists():
            raise ModuleLoaderError(f"Modul-Datei fehlt: {entry_path}")
        spec = importlib.util.spec_from_file_location(module_id, entry_path)
        if spec is None or spec.loader is None:
            raise ModuleLoaderError(f"Modul konnte nicht geladen werden: {entry_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_id] = module
        _ensure_root_on_path()
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_id, None)
            raise
        module.EVENT_BUS = EVENT_BUS
        if hasattr(module, "on_event") and callable(getattr(module, "on_event")):
            EVENT_BUS.subscribe("*", module.on_event)
        EVENT_BUS.emit("module_loaded", {"module_id": module_id, "entry": str(entry_path)})
        self._cache[cache_key] = module
        return module


MODULE_LOADER = ModuleLoader()

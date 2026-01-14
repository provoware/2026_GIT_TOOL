from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional

if TYPE_CHECKING:
    from module_registry import ModuleEntry


@dataclass
class AppStore:
    _modules: Dict[str, "ModuleEntry"] = field(default_factory=dict)
    _settings: Dict[str, Any] = field(default_factory=dict)
    _logging: Dict[str, Any] = field(default_factory=dict)

    def set_modules(self, entries: Iterable["ModuleEntry"]) -> None:
        self._modules = {entry.module_id: entry for entry in entries}

    def get_modules(self) -> List["ModuleEntry"]:
        return list(self._modules.values())

    def get_module(self, module_id: str) -> Optional["ModuleEntry"]:
        return self._modules.get(module_id)

    def set_setting(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def get_setting(self, key: str, default: Any | None = None) -> Any:
        return self._settings.get(key, default)

    def set_logging_state(self, key: str, value: Any) -> None:
        self._logging[key] = value

    def get_logging_state(self, key: str, default: Any | None = None) -> Any:
        return self._logging.get(key, default)


STORE = AppStore()

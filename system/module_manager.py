from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from logging_center import get_logger
from module_loader import MODULE_LOADER, ModuleLoaderError
from module_registry import (
    ModuleEntry,
    ModuleManifest,
    ModuleRegistry,
    ModuleRegistryError,
    load_manifest,
    load_registry,
    resolve_entry_path,
)


class ModuleManagerError(ValueError):
    """Fehler im Modul-Manager."""


@dataclass
class ModuleActionResult:
    status: str
    message: str
    payload: Dict[str, Any]


@dataclass
class ModuleState:
    entry: ModuleEntry
    manifest: Optional[ModuleManifest]
    entry_path: Optional[Path]
    active: bool
    module: Optional[Any]
    context: Optional[Any]
    last_status: str
    last_message: str
    error_message: Optional[str] = None


class ModuleManager:
    def __init__(self, config_path: Path, debug: bool = False) -> None:
        self._ensure_path(config_path, "config_path")
        self.config_path = config_path
        self.debug = debug
        self.logger = get_logger("module_manager")
        self.registry = self._load_registry(config_path)
        self._states: Dict[str, ModuleState] = {}
        self._load_states(self.registry.entries)

    def list_states(self, include_disabled: bool = True) -> list[ModuleState]:
        states = list(self._states.values())
        if include_disabled:
            return states
        return [state for state in states if state.entry.enabled]

    def get_state(self, module_id: str) -> ModuleState:
        module_id = self._require_text(module_id, "module_id")
        state = self._states.get(module_id)
        if state is None:
            raise ModuleManagerError(f"Modul nicht gefunden: {module_id}.")
        return state

    def activate_module(self, module_id: str) -> ModuleActionResult:
        state = self.get_state(module_id)
        if not state.entry.enabled:
            return self._result("warn", "Modul ist deaktiviert.", state)
        if state.error_message:
            return self._result("error", state.error_message, state)
        if state.active:
            return self._result("ok", "Modul ist bereits aktiv.", state)
        if state.entry_path is None:
            return self._result("error", "Modul-Pfad ist nicht verfügbar.", state)

        try:
            module = MODULE_LOADER.load(state.entry.module_id, state.entry_path)
        except (ModuleLoaderError, OSError, ImportError) as exc:
            return self._result("error", f"Modul konnte nicht geladen werden: {exc}", state)

        try:
            self._validate_module_functions(module)
        except ModuleManagerError as exc:
            return self._result("error", str(exc), state)

        context = None
        init_func = getattr(module, "init", None)
        if init_func is not None:
            if not callable(init_func):
                return self._result("error", "Modul-Init ist nicht aufrufbar.", state)
            try:
                context = self._call_with_optional_context(init_func)
            except Exception as exc:  # noqa: BLE001
                return self._result("error", f"Init fehlgeschlagen: {exc}", state)
            self._validate_optional_output(context, "init")

        state.module = module
        state.active = True
        state.context = context
        state.last_status = "ok"
        state.last_message = "Modul aktiviert."
        return self._result("ok", "Modul aktiviert.", state)

    def deactivate_module(self, module_id: str) -> ModuleActionResult:
        state = self.get_state(module_id)
        if not state.active:
            return self._result("ok", "Modul ist bereits deaktiviert.", state)
        module = state.module
        if module is None:
            state.active = False
            return self._result("warn", "Modul-Instanz fehlt, wurde aber deaktiviert.", state)

        exit_func = getattr(module, "exit", None)
        if exit_func is not None:
            if not callable(exit_func):
                return self._result("error", "Modul-Exit ist nicht aufrufbar.", state)
            try:
                output = self._call_exit(exit_func, state.context)
            except Exception as exc:  # noqa: BLE001
                return self._result("error", f"Exit fehlgeschlagen: {exc}", state)
            self._validate_optional_output(output, "exit")

        state.active = False
        state.module = None
        state.context = None
        state.last_status = "ok"
        state.last_message = "Modul deaktiviert."
        return self._result("ok", "Modul deaktiviert.", state)

    def deactivate_all(self) -> list[ModuleActionResult]:
        results: list[ModuleActionResult] = []
        for state in self.list_states(include_disabled=True):
            if state.active:
                results.append(self.deactivate_module(state.entry.module_id))
        return results

    def _load_registry(self, config_path: Path) -> ModuleRegistry:
        try:
            return load_registry(config_path)
        except ModuleRegistryError as exc:
            raise ModuleManagerError(str(exc)) from exc

    def _load_states(self, entries: Iterable[ModuleEntry]) -> None:
        for entry in entries:
            manifest = None
            entry_path = None
            error_message = None
            try:
                manifest = load_manifest(entry.path)
                entry_path = resolve_entry_path(entry.path, manifest.entry)
            except ModuleRegistryError as exc:
                error_message = f"Modul-Manifest fehlerhaft: {exc}"

            state = ModuleState(
                entry=entry,
                manifest=manifest,
                entry_path=entry_path,
                active=False,
                module=None,
                context=None,
                last_status="idle",
                last_message="Modul noch nicht geladen.",
                error_message=error_message,
            )
            self._states[entry.module_id] = state

    def _validate_module_functions(self, module: Any) -> None:
        for name in ("run", "validateInput", "validateOutput"):
            func = getattr(module, name, None)
            if func is None or not callable(func):
                raise ModuleManagerError(f"Pflichtfunktion fehlt oder ist ungültig: {name}.")
        if hasattr(module, "exit") and not callable(getattr(module, "exit")):
            raise ModuleManagerError("Exit-Funktion ist vorhanden, aber nicht aufrufbar.")
        if hasattr(module, "init") and not callable(getattr(module, "init")):
            raise ModuleManagerError("Init-Funktion ist vorhanden, aber nicht aufrufbar.")

    def _call_exit(self, func, context: Any) -> Any:
        signature = inspect.signature(func)
        if len(signature.parameters) == 0:
            return func()
        return func(context)

    def _call_with_optional_context(self, func) -> Any:
        signature = inspect.signature(func)
        if len(signature.parameters) == 0:
            return func()
        required = [
            param
            for param in signature.parameters.values()
            if param.default is inspect._empty
            and param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD)
        ]
        if not required:
            return func()
        return func(self._build_context())

    def _build_context(self) -> Dict[str, Any]:
        return {
            "config_path": str(self.config_path),
            "debug": self.debug,
        }

    def _validate_optional_output(self, output: Any, label: str) -> None:
        if output is None:
            return
        if not isinstance(output, dict):
            return
        status = output.get("status")
        message = output.get("message")
        if status is not None and not isinstance(status, str):
            raise ModuleManagerError(f"{label}: status ist ungültig.")
        if message is not None and not isinstance(message, str):
            raise ModuleManagerError(f"{label}: message ist ungültig.")

    def _result(self, status: str, message: str, state: ModuleState) -> ModuleActionResult:
        payload = {
            "module_id": state.entry.module_id,
            "name": state.entry.name,
            "active": state.active,
        }
        if not isinstance(status, str) or not status:
            raise ModuleManagerError("status ist ungültig.")
        if not isinstance(message, str) or not message:
            raise ModuleManagerError("message ist ungültig.")
        return ModuleActionResult(status=status, message=message, payload=payload)

    @staticmethod
    def _ensure_path(value: object, label: str) -> Path:
        if not isinstance(value, Path):
            raise ModuleManagerError(f"{label} ist kein Pfad (Path).")
        return value

    @staticmethod
    def _require_text(value: object, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ModuleManagerError(f"{label} ist leer oder ungültig.")
        return value.strip()

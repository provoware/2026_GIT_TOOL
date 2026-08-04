#!/usr/bin/env python3
"""UI-unabhängige Zustands- und Close-Policy für Modulkarten."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Tuple

from module_manager import ModuleActionResult, ModuleState


class ModuleLifecycleError(ValueError):
    """Ungültiger Modulzustand oder Lifecycle-Vertrag."""


@dataclass(frozen=True)
class ModuleCardPresentation:
    """Darstellung einer Modulkarte, vollständig aus dem Managerzustand abgeleitet."""

    active: bool
    status_text: str
    color_key: str
    activate_enabled: bool
    deactivate_enabled: bool


@dataclass(frozen=True)
class ModuleActionOutcome:
    """Aktionsergebnis zusammen mit dem danach erneut gelesenen Managerzustand."""

    result: ModuleActionResult
    state: ModuleState
    presentation: ModuleCardPresentation


@dataclass(frozen=True)
class CloseDecision:
    """Explizite Entscheidung, ob das Hauptfenster sicher geschlossen werden darf."""

    allow_close: bool
    message: str
    color_key: str
    report: str
    results: Tuple[ModuleActionResult, ...]
    remaining_module_ids: Tuple[str, ...]


def resolve_card_presentation(
    state: ModuleState,
    result: ModuleActionResult | None = None,
) -> ModuleCardPresentation:
    """Leitet Text, Farbe und Schaltflächen ausschließlich aus dem Ist-Zustand ab."""

    if not isinstance(state, ModuleState):
        raise ModuleLifecycleError("Modulzustand ist ungültig.")
    if result is not None and not isinstance(result, ModuleActionResult):
        raise ModuleLifecycleError("Aktionsergebnis ist ungültig.")

    active = bool(state.active)
    result_status = result.status if result is not None else state.last_status

    if state.error_message or result_status == "error":
        color_key = "status_error"
        signal = "Rot – Fehler"
    elif result_status == "warn":
        color_key = "status_busy"
        signal = "Gelb – Hinweis"
    elif active:
        color_key = "status_success"
        signal = "Grün – aktiv"
    else:
        color_key = "foreground"
        signal = "Grau – inaktiv"

    return ModuleCardPresentation(
        active=active,
        status_text=f"Ampel: {signal}",
        color_key=color_key,
        activate_enabled=bool(state.entry.enabled) and not active and not bool(state.error_message),
        deactivate_enabled=active,
    )


def perform_module_action(
    manager: Any,
    module_id: str,
    action: Literal["activate", "deactivate"],
) -> ModuleActionOutcome:
    """Führt eine Aktion aus und liest danach zwingend den autoritativen Zustand neu."""

    clean_module_id = _require_text(module_id, "module_id")
    if action not in {"activate", "deactivate"}:
        raise ModuleLifecycleError(f"Unbekannte Modulaktion: {action}.")

    method_name = "activate_module" if action == "activate" else "deactivate_module"
    action_method = getattr(manager, method_name, None)
    get_state = getattr(manager, "get_state", None)
    if not callable(action_method) or not callable(get_state):
        raise ModuleLifecycleError("Modul-Manager erfüllt den Aktionsvertrag nicht.")

    result = action_method(clean_module_id)
    if not isinstance(result, ModuleActionResult):
        raise ModuleLifecycleError("Modulaktion lieferte kein gültiges Ergebnis.")
    state = get_state(clean_module_id)
    if not isinstance(state, ModuleState):
        raise ModuleLifecycleError("Modul-Manager lieferte keinen gültigen Zustand.")

    return ModuleActionOutcome(
        result=result,
        state=state,
        presentation=resolve_card_presentation(state, result),
    )


def prepare_close(manager: Any) -> CloseDecision:
    """Deaktiviert aktive Fenstermodule und blockiert bei verbleibenden aktiven Modulen."""

    list_states = getattr(manager, "list_states", None)
    deactivate_all = getattr(manager, "deactivate_all", None)
    if not callable(list_states) or not callable(deactivate_all):
        raise ModuleLifecycleError("Modul-Manager erfüllt den Close-Vertrag nicht.")

    states_before = _validated_states(list_states(include_disabled=True))
    active_before = tuple(
        state.entry.module_id for state in states_before if bool(state.active)
    )

    raw_results = deactivate_all()
    if not isinstance(raw_results, list) or not all(
        isinstance(result, ModuleActionResult) for result in raw_results
    ):
        raise ModuleLifecycleError("deactivate_all lieferte ungültige Ergebnisse.")
    results = tuple(raw_results)

    states_after = _validated_states(list_states(include_disabled=True))
    remaining = tuple(
        state.entry.module_id for state in states_after if bool(state.active)
    )

    report_lines = ["Hauptfenster schließen: Modul-Lebenszyklus"]
    if not active_before:
        report_lines.append("Hinweis: Keine aktiven Module vorhanden.")
    for result in results:
        module_id = result.payload.get("module_id", "unbekannt")
        report_lines.append(f"{module_id}: {result.status} – {result.message}")

    if remaining:
        report_lines.append("Blockiert: Noch aktiv: " + ", ".join(remaining))
        message = (
            "Schließen blockiert: "
            f"{len(remaining)} Modul(e) konnten nicht sauber deaktiviert werden."
        )
        color_key = "status_error"
        allow_close = False
    elif any(result.status != "ok" for result in results):
        report_lines.append("Ergebnis: Schließen mit Hinweisen freigegeben.")
        message = "Alle Module sind beendet; beim Schließen gab es Hinweise."
        color_key = "status_busy"
        allow_close = True
    else:
        report_lines.append("Ergebnis: Sicheres Schließen freigegeben.")
        message = "Alle aktiven Module wurden sauber deaktiviert."
        color_key = "status_success"
        allow_close = True

    return CloseDecision(
        allow_close=allow_close,
        message=message,
        color_key=color_key,
        report="\n".join(report_lines).rstrip() + "\n",
        results=results,
        remaining_module_ids=remaining,
    )


def _validated_states(value: object) -> list[ModuleState]:
    if not isinstance(value, list) or not all(isinstance(item, ModuleState) for item in value):
        raise ModuleLifecycleError("Modul-Manager lieferte ungültige Zustände.")
    return value


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModuleLifecycleError(f"{label} fehlt oder ist leer.")
    return value.strip()

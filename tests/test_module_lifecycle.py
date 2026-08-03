from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system"))

from module_lifecycle import (
    ModuleLifecycleError,
    perform_module_action,
    prepare_close,
    resolve_card_presentation,
)
from module_manager import ModuleActionResult, ModuleState
from module_registry import ModuleEntry


def make_state(
    module_id: str,
    *,
    active: bool = False,
    enabled: bool = True,
    error_message: str | None = None,
) -> ModuleState:
    entry = ModuleEntry(
        module_id=module_id,
        name=module_id.title(),
        path=Path("modules") / module_id,
        enabled=enabled,
        description=f"Modul {module_id}",
    )
    return ModuleState(
        entry=entry,
        manifest=None,
        entry_path=Path("modules") / module_id / "main.py",
        active=active,
        module=object() if active else None,
        context=None,
        last_status="ok" if active else "idle",
        last_message="Aktiv" if active else "Inaktiv",
        error_message=error_message,
    )


def action_result(state: ModuleState, status: str, message: str) -> ModuleActionResult:
    return ModuleActionResult(
        status=status,
        message=message,
        payload={
            "module_id": state.entry.module_id,
            "name": state.entry.name,
            "active": state.active,
        },
    )


class FakeManager:
    def __init__(self, states: list[ModuleState]) -> None:
        self.states = {state.entry.module_id: state for state in states}
        self.activate_status: dict[str, str] = {}
        self.deactivate_status: dict[str, str] = {}
        self.deactivate_calls: list[str] = []

    def list_states(self, include_disabled: bool = True):
        states = list(self.states.values())
        if include_disabled:
            return states
        return [state for state in states if state.entry.enabled]

    def get_state(self, module_id: str):
        return self.states[module_id]

    def activate_module(self, module_id: str):
        state = self.states[module_id]
        status = self.activate_status.get(module_id, "ok")
        if status == "ok":
            state.active = True
            state.module = object()
            state.last_status = "ok"
            state.last_message = "Modul aktiviert."
            message = "Modul aktiviert."
        elif status == "warn":
            state.last_status = "warn"
            state.last_message = "Aktivierung mit Hinweis."
            message = state.last_message
        else:
            state.last_status = "error"
            state.last_message = "Aktivierung fehlgeschlagen."
            message = state.last_message
        return action_result(state, status, message)

    def deactivate_module(self, module_id: str):
        state = self.states[module_id]
        self.deactivate_calls.append(module_id)
        status = self.deactivate_status.get(module_id, "ok")
        if status == "ok":
            state.active = False
            state.module = None
            state.last_status = "ok"
            state.last_message = "Modul deaktiviert."
            message = state.last_message
        elif status == "warn":
            state.active = False
            state.module = None
            state.last_status = "warn"
            state.last_message = "Modul mit Hinweis deaktiviert."
            message = state.last_message
        else:
            state.last_status = "error"
            state.last_message = "Exit fehlgeschlagen."
            message = state.last_message
        return action_result(state, status, message)

    def deactivate_all(self):
        results = []
        for state in self.list_states(include_disabled=True):
            if state.active:
                results.append(self.deactivate_module(state.entry.module_id))
        return results


def test_inactive_card_uses_neutral_state_and_correct_buttons():
    presentation = resolve_card_presentation(make_state("alpha"))

    assert presentation.active is False
    assert presentation.status_text == "Status: inaktiv"
    assert presentation.color_key == "foreground"
    assert presentation.activate_enabled is True
    assert presentation.deactivate_enabled is False


def test_active_card_uses_success_state_and_correct_buttons():
    presentation = resolve_card_presentation(make_state("alpha", active=True))

    assert presentation.active is True
    assert presentation.status_text == "Status: aktiv"
    assert presentation.color_key == "status_success"
    assert presentation.activate_enabled is False
    assert presentation.deactivate_enabled is True


def test_disabled_or_broken_module_cannot_be_activated():
    disabled = resolve_card_presentation(make_state("disabled", enabled=False))
    broken = resolve_card_presentation(
        make_state("broken", error_message="Manifest fehlerhaft")
    )

    assert disabled.activate_enabled is False
    assert broken.activate_enabled is False
    assert broken.color_key == "status_error"


def test_failed_activation_keeps_card_authoritatively_inactive():
    state = make_state("alpha")
    manager = FakeManager([state])
    manager.activate_status["alpha"] = "error"

    outcome = perform_module_action(manager, "alpha", "activate")

    assert outcome.result.status == "error"
    assert outcome.state.active is False
    assert outcome.presentation.status_text == "Status: inaktiv"
    assert outcome.presentation.color_key == "status_error"
    assert outcome.presentation.activate_enabled is True
    assert outcome.presentation.deactivate_enabled is False


def test_successful_activation_and_deactivation_follow_manager_state():
    state = make_state("alpha")
    manager = FakeManager([state])

    activated = perform_module_action(manager, "alpha", "activate")
    deactivated = perform_module_action(manager, "alpha", "deactivate")

    assert activated.presentation.active is True
    assert activated.presentation.activate_enabled is False
    assert activated.presentation.deactivate_enabled is True
    assert deactivated.presentation.active is False
    assert deactivated.presentation.activate_enabled is True
    assert deactivated.presentation.deactivate_enabled is False


def test_failed_deactivation_keeps_card_active_and_retryable():
    state = make_state("alpha", active=True)
    manager = FakeManager([state])
    manager.deactivate_status["alpha"] = "error"

    outcome = perform_module_action(manager, "alpha", "deactivate")

    assert outcome.result.status == "error"
    assert outcome.presentation.active is True
    assert outcome.presentation.status_text == "Status: aktiv"
    assert outcome.presentation.activate_enabled is False
    assert outcome.presentation.deactivate_enabled is True


def test_close_without_active_modules_does_not_deactivate_anything():
    manager = FakeManager([make_state("alpha"), make_state("beta")])

    decision = prepare_close(manager)

    assert decision.allow_close is True
    assert decision.remaining_module_ids == ()
    assert manager.deactivate_calls == []
    assert "Keine aktiven Module" in decision.report


def test_close_deactivates_only_active_modules_and_allows_destroy():
    manager = FakeManager(
        [
            make_state("alpha", active=True),
            make_state("beta"),
            make_state("gamma", active=True),
        ]
    )

    decision = prepare_close(manager)

    assert decision.allow_close is True
    assert decision.color_key == "status_success"
    assert manager.deactivate_calls == ["alpha", "gamma"]
    assert all(not state.active for state in manager.states.values())


def test_close_allows_warning_when_module_is_no_longer_active():
    state = make_state("alpha", active=True)
    manager = FakeManager([state])
    manager.deactivate_status["alpha"] = "warn"

    decision = prepare_close(manager)

    assert decision.allow_close is True
    assert decision.color_key == "status_busy"
    assert decision.remaining_module_ids == ()
    assert "mit Hinweisen" in decision.report


def test_close_is_blocked_when_exit_error_leaves_module_active():
    alpha = make_state("alpha", active=True)
    beta = make_state("beta", active=True)
    manager = FakeManager([alpha, beta])
    manager.deactivate_status["beta"] = "error"

    decision = prepare_close(manager)

    assert decision.allow_close is False
    assert decision.color_key == "status_error"
    assert decision.remaining_module_ids == ("beta",)
    assert alpha.active is False
    assert beta.active is True
    assert "Blockiert: Noch aktiv: beta" in decision.report


def test_unknown_action_is_rejected_before_manager_mutation():
    manager = FakeManager([make_state("alpha")])

    with pytest.raises(ModuleLifecycleError, match="Unbekannte Modulaktion"):
        perform_module_action(manager, "alpha", "remove")  # type: ignore[arg-type]

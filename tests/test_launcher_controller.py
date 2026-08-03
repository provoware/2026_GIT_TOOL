from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system"))

from launcher_controller import (
    LauncherController,
    LauncherControllerError,
    RefreshDebouncer,
    build_help_entries,
    build_shortcut_specs,
    build_status_view,
    record_state_change,
)
from undo_redo import UndoRedoManager


class FakeScheduler:
    def __init__(self, *, cancel_raises: bool = False):
        self.jobs = {}
        self.cancelled = []
        self.counter = 0
        self.cancel_raises = cancel_raises

    def schedule(self, delay, callback):
        self.counter += 1
        job_id = f"job-{self.counter}"
        self.jobs[job_id] = (delay, callback)
        return job_id

    def cancel(self, job_id):
        self.cancelled.append(job_id)
        if self.cancel_raises:
            raise RuntimeError("cancel failed")


def make_controller() -> LauncherController:
    return LauncherController(
        show_all=False,
        debug=False,
        theme_name="hell",
        help_text="Standardhilfe",
    )


def test_controller_initial_state_is_typed_and_stable():
    controller = make_controller()

    assert controller.state.show_all is False
    assert controller.state.debug is False
    assert controller.state.theme_name == "hell"
    assert controller.state.help_text == "Standardhilfe"


def test_boolean_filter_change_updates_authoritative_state():
    controller = make_controller()

    change = controller.set_show_all(True)

    assert change.changed is True
    assert change.previous is False
    assert change.current is True
    assert change.metadata == {
        "field": "show_all",
        "previous": False,
        "current": True,
    }
    assert controller.state.show_all is True


def test_noop_filter_change_does_not_create_history_entry():
    controller = make_controller()
    manager = UndoRedoManager(limit=5)

    change = controller.set_debug(False)
    recorded = record_state_change(
        manager,
        change,
        lambda value: controller.set_debug(bool(value)),
    )

    assert change.changed is False
    assert recorded is False
    assert manager.can_undo() is False


def test_filter_change_roundtrips_through_undo_and_redo():
    controller = make_controller()
    manager = UndoRedoManager(limit=5)
    change = controller.set_show_all(True)

    assert record_state_change(
        manager,
        change,
        lambda value: controller.set_show_all(bool(value)),
    ) is True

    action = manager.undo()
    assert action.name == "Alle Module anzeigen"
    assert controller.state.show_all is False

    manager.redo()
    assert controller.state.show_all is True


def test_theme_change_validates_known_themes_and_roundtrips():
    controller = make_controller()
    manager = UndoRedoManager(limit=5)
    themes = {"hell": object(), "kontrast": object()}

    change = controller.set_theme("kontrast", themes)
    assert change.changed is True
    assert controller.state.theme_name == "kontrast"

    record_state_change(
        manager,
        change,
        lambda value: controller.set_theme(str(value), themes),
    )
    manager.undo()
    assert controller.state.theme_name == "hell"
    manager.redo()
    assert controller.state.theme_name == "kontrast"

    with pytest.raises(LauncherControllerError, match="Unbekanntes Farbschema"):
        controller.set_theme("fehlt", themes)


def test_help_state_rejects_empty_text_and_tracks_current_context():
    controller = make_controller()

    change = controller.set_help("  Kontext für Backup  ")

    assert change.current == "Kontext für Backup"
    assert controller.state.help_text == "Kontext für Backup"
    with pytest.raises(LauncherControllerError, match="help_text"):
        controller.set_help("   ")


def test_status_view_defines_text_and_cursor_for_all_states():
    success = build_status_view("Bereit.", "success")
    error = build_status_view("Fehler.", "error")
    busy = build_status_view("Prüfung läuft…", "busy")

    assert success.display_text == "Status: Bereit."
    assert success.cursor == ""
    assert error.cursor == ""
    assert busy.cursor == "watch"

    with pytest.raises(LauncherControllerError, match="Status-State"):
        build_status_view("Unbekannt", "warning")


def test_refresh_debouncer_runs_only_latest_callback():
    scheduler = FakeScheduler()
    calls = []
    debouncer = RefreshDebouncer(
        scheduler.schedule,
        scheduler.cancel,
        200,
        lambda: calls.append("refresh"),
    )

    first = debouncer.request()
    second = debouncer.request()

    assert scheduler.cancelled == [first]
    assert scheduler.jobs[first][0] == 200
    assert scheduler.jobs[second][0] == 200

    scheduler.jobs[first][1]()
    assert calls == []
    scheduler.jobs[second][1]()
    assert calls == ["refresh"]
    assert debouncer.job_id is None


def test_refresh_debouncer_ignores_stale_callback_when_cancel_fails():
    scheduler = FakeScheduler(cancel_raises=True)
    calls = []
    debouncer = RefreshDebouncer(
        scheduler.schedule,
        scheduler.cancel,
        50,
        lambda: calls.append("latest"),
    )

    first = debouncer.request()
    second = debouncer.request()
    scheduler.jobs[first][1]()
    scheduler.jobs[second][1]()

    assert calls == ["latest"]


def test_refresh_debouncer_cancel_prevents_pending_callback():
    scheduler = FakeScheduler()
    calls = []
    debouncer = RefreshDebouncer(
        scheduler.schedule,
        scheduler.cancel,
        25,
        lambda: calls.append("unexpected"),
    )

    job_id = debouncer.request()
    assert debouncer.cancel() is True
    scheduler.jobs[job_id][1]()

    assert calls == []
    assert debouncer.job_id is None
    assert debouncer.cancel() is False


def test_refresh_debouncer_clears_job_after_schedule_error():
    def fail_schedule(_delay, _callback):
        raise RuntimeError("scheduler unavailable")

    debouncer = RefreshDebouncer(fail_schedule, lambda _job: None, 10, lambda: None)

    with pytest.raises(RuntimeError, match="scheduler unavailable"):
        debouncer.request()
    assert debouncer.job_id is None


def test_shortcut_view_is_unique_and_contains_required_actions():
    specs = build_shortcut_specs()
    sequences = [item.sequence for item in specs]
    actions = {item.action for item in specs}

    assert len(sequences) == len(set(sequences))
    assert {
        "toggle_show_all",
        "toggle_debug",
        "refresh",
        "undo",
        "redo",
        "announce_help",
        "logout",
    }.issubset(actions)
    assert sum(item.action == "refresh" for item in specs) == 2
    assert sum(item.action == "redo" for item in specs) == 2


def test_help_view_has_unique_keys_and_complete_texts():
    entries = build_help_entries()
    keys = [entry.key for entry in entries]

    assert len(entries) == 17
    assert len(keys) == len(set(keys))
    assert "autostart_check" in keys
    assert "drop_zone_label" in keys
    assert all(entry.tooltip.strip() and entry.context.strip() for entry in entries)


def test_controller_rejects_invalid_initial_types():
    with pytest.raises(LauncherControllerError, match="show_all"):
        LauncherController(
            show_all=1,
            debug=False,
            theme_name="hell",
            help_text="Hilfe",
        )
    with pytest.raises(LauncherControllerError, match="debug"):
        LauncherController(
            show_all=False,
            debug="no",
            theme_name="hell",
            help_text="Hilfe",
        )

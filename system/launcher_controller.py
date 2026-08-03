#!/usr/bin/env python3
"""UI-unabhängiger Zustands-, View- und Debounce-Vertrag des Launchers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Iterable, Mapping

from undo_redo import UndoRedoAction, UndoRedoManager


class LauncherControllerError(ValueError):
    """Ungültiger Controllerzustand oder Viewvertrag."""


VALID_STATUS_STATES = frozenset({"success", "error", "busy"})


@dataclass(frozen=True)
class LauncherState:
    show_all: bool
    debug: bool
    theme_name: str
    help_text: str


@dataclass(frozen=True)
class StateChange:
    name: str
    field: str
    previous: object
    current: object

    @property
    def changed(self) -> bool:
        return self.previous != self.current

    @property
    def metadata(self) -> dict[str, object]:
        return {
            "field": self.field,
            "previous": self.previous,
            "current": self.current,
        }


@dataclass(frozen=True)
class StatusView:
    message: str
    state: str
    display_text: str
    cursor: str


@dataclass(frozen=True)
class ShortcutSpec:
    sequence: str
    action: str


@dataclass(frozen=True)
class HelpEntry:
    key: str
    tooltip: str
    context: str


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LauncherControllerError(f"{label} ist leer oder ungültig.")
    return value.strip()


def build_status_view(message: str, state: str = "success") -> StatusView:
    clean_message = _require_text(message, "status_message")
    clean_state = _require_text(state, "status_state")
    if clean_state not in VALID_STATUS_STATES:
        raise LauncherControllerError("Status-State ist ungültig.")
    return StatusView(
        message=clean_message,
        state=clean_state,
        display_text=f"Status: {clean_message}",
        cursor="watch" if clean_state == "busy" else "",
    )


class LauncherController:
    """Hält die testbare Launcher-Sicht unabhängig von Tkinter."""

    def __init__(
        self,
        *,
        show_all: bool,
        debug: bool,
        theme_name: str,
        help_text: str,
    ) -> None:
        if not isinstance(show_all, bool):
            raise LauncherControllerError("show_all ist kein boolescher Wert.")
        if not isinstance(debug, bool):
            raise LauncherControllerError("debug ist kein boolescher Wert.")
        self._state = LauncherState(
            show_all=show_all,
            debug=debug,
            theme_name=_require_text(theme_name, "theme_name"),
            help_text=_require_text(help_text, "help_text"),
        )

    @property
    def state(self) -> LauncherState:
        return self._state

    def set_show_all(self, value: bool) -> StateChange:
        if not isinstance(value, bool):
            raise LauncherControllerError("show_all ist kein boolescher Wert.")
        change = StateChange(
            name="Alle Module anzeigen",
            field="show_all",
            previous=self._state.show_all,
            current=value,
        )
        if change.changed:
            self._state = replace(self._state, show_all=value)
        return change

    def set_debug(self, value: bool) -> StateChange:
        if not isinstance(value, bool):
            raise LauncherControllerError("debug ist kein boolescher Wert.")
        change = StateChange(
            name="Debug-Details anzeigen",
            field="debug",
            previous=self._state.debug,
            current=value,
        )
        if change.changed:
            self._state = replace(self._state, debug=value)
        return change

    def set_theme(self, value: str, valid_themes: Iterable[str] | Mapping[str, object]) -> StateChange:
        clean_value = _require_text(value, "theme_name")
        names = set(valid_themes.keys() if isinstance(valid_themes, Mapping) else valid_themes)
        if clean_value not in names:
            raise LauncherControllerError("Unbekanntes Farbschema.")
        previous = self._state.theme_name
        change = StateChange(
            name=f"Farbschema wechseln ({previous} → {clean_value})",
            field="theme_name",
            previous=previous,
            current=clean_value,
        )
        if change.changed:
            self._state = replace(self._state, theme_name=clean_value)
        return change

    def set_help(self, value: str) -> StateChange:
        clean_value = _require_text(value, "help_text")
        change = StateChange(
            name="Kontext-Hilfe wechseln",
            field="help_text",
            previous=self._state.help_text,
            current=clean_value,
        )
        if change.changed:
            self._state = replace(self._state, help_text=clean_value)
        return change


def record_state_change(
    manager: UndoRedoManager,
    change: StateChange,
    apply_value: Callable[[object], None],
) -> bool:
    """Legt nur echte Zustandsänderungen in der Undo-/Redo-Historie ab."""

    if not isinstance(manager, UndoRedoManager):
        raise LauncherControllerError("undo_manager ist ungültig.")
    if not isinstance(change, StateChange):
        raise LauncherControllerError("state_change ist ungültig.")
    if not callable(apply_value):
        raise LauncherControllerError("apply_value ist nicht aufrufbar.")
    if not change.changed:
        return False
    manager.record(
        UndoRedoAction(
            name=change.name,
            undo=lambda: apply_value(change.previous),
            redo=lambda: apply_value(change.current),
            metadata=change.metadata,
        )
    )
    return True


class RefreshDebouncer:
    """Plant höchstens den neuesten Refresh und ignoriert veraltete Callbacks."""

    def __init__(
        self,
        schedule: Callable[[int, Callable[[], None]], object],
        cancel: Callable[[object], None],
        delay_ms: int,
        callback: Callable[[], None],
    ) -> None:
        if not callable(schedule):
            raise LauncherControllerError("Refresh-Scheduler ist nicht aufrufbar.")
        if not callable(cancel):
            raise LauncherControllerError("Refresh-Abbruch ist nicht aufrufbar.")
        if not isinstance(delay_ms, int) or delay_ms < 0:
            raise LauncherControllerError("Refresh-Delay ist ungültig.")
        if not callable(callback):
            raise LauncherControllerError("Refresh-Callback ist nicht aufrufbar.")
        self._schedule = schedule
        self._cancel = cancel
        self._delay_ms = delay_ms
        self._callback = callback
        self._job_id: object | None = None
        self._generation = 0

    @property
    def job_id(self) -> object | None:
        return self._job_id

    def request(self) -> object:
        previous = self._job_id
        self._generation += 1
        generation = self._generation
        self._job_id = None
        if previous is not None:
            try:
                self._cancel(previous)
            except Exception:
                pass

        def run_latest() -> None:
            if generation != self._generation:
                return
            self._job_id = None
            self._callback()

        try:
            job_id = self._schedule(self._delay_ms, run_latest)
        except Exception:
            self._job_id = None
            raise
        self._job_id = job_id
        return job_id

    def cancel(self) -> bool:
        previous = self._job_id
        self._generation += 1
        self._job_id = None
        if previous is None:
            return False
        try:
            self._cancel(previous)
        except Exception:
            return False
        return True


def build_shortcut_specs() -> tuple[ShortcutSpec, ...]:
    return (
        ShortcutSpec("<Alt-a>", "toggle_show_all"),
        ShortcutSpec("<Alt-d>", "toggle_debug"),
        ShortcutSpec("<Alt-r>", "refresh"),
        ShortcutSpec("<Alt-t>", "focus_theme"),
        ShortcutSpec("<Alt-k>", "toggle_contrast"),
        ShortcutSpec("<Alt-g>", "diagnostics"),
        ShortcutSpec("<Alt-m>", "main_window"),
        ShortcutSpec("<Alt-s>", "system_scan"),
        ShortcutSpec("<Alt-p>", "standards"),
        ShortcutSpec("<Alt-l>", "logs"),
        ShortcutSpec("<Alt-e>", "selective_export"),
        ShortcutSpec("<Alt-x>", "export_center"),
        ShortcutSpec("<Alt-b>", "backup"),
        ShortcutSpec("<Alt-q>", "logout"),
        ShortcutSpec("<Control-r>", "refresh"),
        ShortcutSpec("<Control-z>", "undo"),
        ShortcutSpec("<Control-y>", "redo"),
        ShortcutSpec("<Control-Shift-Z>", "redo"),
        ShortcutSpec("<F1>", "announce_help"),
    )


def build_help_entries() -> tuple[HelpEntry, ...]:
    return (
        HelpEntry(
            "theme_menu",
            "Farbschema wählen (Theme = Farbstil).",
            "Farbschema wählen: Wähle ein Theme (Farbstil), um Kontrast und Farben anzupassen.",
        ),
        HelpEntry(
            "show_all_check",
            "Zeigt alle Module (auch deaktivierte).",
            "Alle Module anzeigen: Zeigt auch deaktivierte Module, damit du sie prüfen kannst.",
        ),
        HelpEntry(
            "debug_check",
            "Zeigt technische Details (Debugging = Fehlersuche).",
            "Debug-Details: Zeigt technische Zusatzinfos (Debugging = Fehlersuche).",
        ),
        HelpEntry(
            "autostart_check",
            "Startet das Tool nach der Linux-Anmeldung automatisch.",
            "Autostart: Aktiviert oder deaktiviert den benutzerspezifischen Linux-Autostart.",
        ),
        HelpEntry(
            "refresh_button",
            "Aktualisiert die Modulübersicht.",
            "Übersicht aktualisieren: Lädt Module neu und prüft Fehler.",
        ),
        HelpEntry(
            "logout_button",
            "Sichert Daten und beendet das Tool.",
            "Abmelden: Erst wird eine Sicherung erstellt, danach wird sauber beendet.",
        ),
        HelpEntry(
            "diagnostics_button",
            "Startet Tests und Codeprüfungen.",
            "Diagnose starten: Führt Tests und Codequalität (Linting/Format) aus.",
        ),
        HelpEntry(
            "main_window_button",
            "Öffnet das Hauptfenster mit Modulraster.",
            "Hauptfenster öffnen: Zeigt ein 3x3-Modulraster mit Drag/Resize und Start/Stop.",
        ),
        HelpEntry(
            "scan_button",
            "Startet den System-Scan (Vorabprüfung).",
            "System-Scan: Prüft Dateien, Ordner und Rechte ohne Schreiben.",
        ),
        HelpEntry(
            "standards_button",
            "Zeigt die Standards (interne Regeln).",
            "Standards anzeigen: Zeigt die internen Regeln (Standards = Regeln).",
        ),
        HelpEntry(
            "logs_button",
            "Öffnet den Log-Ordner (Protokolle).",
            "Log-Ordner öffnen: Zeigt Protokolle (Logs), falls etwas schiefgeht.",
        ),
        HelpEntry(
            "export_button",
            "Erstellt einen Teil-Export (ZIP).",
            "Selektiver Export: Erstellt ein ZIP mit ausgewählten Bereichen (z. B. Logs).",
        ),
        HelpEntry(
            "export_center_button",
            "Exportiert JSON, TXT, PDF und ZIP.",
            "Export-Center: Erstellt Exporte (Ausgabedateien) in mehreren Formaten.",
        ),
        HelpEntry(
            "backup_button",
            "Erstellt ein vollständiges Backup (ZIP).",
            "Backup: Erstellt eine vollständige Sicherung in data/backups.",
        ),
        HelpEntry(
            "output_text",
            "Hier stehen Module und Prüfergebnisse.",
            "Modulübersicht: Zeigt Module, Prüfungen und Hinweise in einfacher Sprache.",
        ),
        HelpEntry(
            "status_label",
            "Zeigt Statusmeldungen (bereit, läuft, Fehler).",
            "Status: Zeigt ob das Tool bereit ist, arbeitet oder einen Fehler meldet.",
        ),
        HelpEntry(
            "drop_zone_label",
            "Dateien/Module per Drag-and-Drop ablegen.",
            "Drag-and-Drop: Ziehe Dateien oder Module auf diese Fläche, um sie zu prüfen.",
        ),
    )

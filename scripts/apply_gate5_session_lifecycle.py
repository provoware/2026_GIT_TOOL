#!/usr/bin/env python3
"""Wendet Gate 5 kontrolliert auf system/launcher_gui.py an."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "system" / "launcher_gui.py"
IMPORT = '''from autostart_manager import AutostartError, AutostartManager
from session_lifecycle import (
    AutosaveSession,
    ShutdownOutcome,
    complete_shutdown,
    run_shutdown_sequence,
)
'''

METHODS = {
    "request_logout": '''    def request_logout(self) -> None:
        if self.task_runner.is_running("shutdown"):
            self._set_status("Abmelden läuft bereits…", state="busy")
            return
        if self.logout_button is not None:
            self.logout_button.configure(state="disabled")
        self._set_status("Abmelden: Sicherung wird vorbereitet…", state="busy")
        try:
            started = self.task_runner.start(
                "shutdown",
                self._execute_logout,
                self._finish_logout,
            )
        except TaskRunnerError as exc:
            if self.logout_button is not None:
                self.logout_button.configure(state="normal")
            self._set_status(f"Abmelden konnte nicht starten: {exc}", state="error")
            return
        if not started:
            if self.logout_button is not None:
                self.logout_button.configure(state="normal")
            self._set_status("Abmelden läuft bereits…", state="busy")
''',
    "_execute_logout": '''    def _execute_logout(self) -> ShutdownOutcome:
        project_root = self.module_config.resolve().parents[1]
        return run_shutdown_sequence(
            autosave_config=self.autosave_config,
            data_root=DEFAULT_DATA_ROOT,
            logs_root=DEFAULT_LOG_ROOT,
            logger=self.logger,
            backup_config_path=project_root / "config" / "backup.json",
            backup_state_path=DEFAULT_DATA_ROOT / "backup_state.json",
        )
''',
    "_finish_logout": '''    def _finish_logout(self, outcome: TaskOutcome[ShutdownOutcome]) -> None:
        if self.logout_button is not None:
            self.logout_button.configure(state="normal")
        if outcome.error is not None:
            result = ShutdownOutcome(
                report=(
                    "Abmelden: Sicherung und sauberes Schließen\\n"
                    "Fehler: Shutdown konnte nicht vollständig ausgeführt werden.\\n"
                    f"Ursache: {outcome.error}\\n"
                ),
                success=False,
            )
        else:
            result = outcome.value
        if not isinstance(result, ShutdownOutcome):
            raise GuiLauncherError("Shutdown-Ergebnis ist ungültig.")
        complete_shutdown(
            result,
            append_report=self._append_output,
            set_status=lambda message, state: self._set_status(message, state=state),
            cancel_autosave=self._cancel_autosave_job,
            schedule=self.root.after,
            destroy=self.root.destroy,
        )
''',
    "_cancel_autosave_job": '''    def _cancel_autosave_job(self) -> None:
        self.autosave_session.cancel()
''',
    "_setup_autosave": '''    def _setup_autosave(self) -> None:
        try:
            config = autosave_manager.load_autosave_config(DEFAULT_SETTINGS_CONFIG)
        except autosave_manager.AutosaveError as exc:
            self.logger.error("Autosave: Konfiguration ungültig: %s", exc)
            return
        self.autosave_config = config
        if not config.enabled:
            self.logger.info("Autosave: Deaktiviert.")
            return
        self._schedule_autosave()
''',
    "_schedule_autosave": '''    def _schedule_autosave(self) -> None:
        if self.autosave_config is None:
            return
        self.autosave_session.start(self.autosave_config)
''',
    "_run_autosave": '''    def _run_autosave(self) -> None:
        if self.autosave_config is None:
            return
        try:
            autosave_manager.create_autosave(DEFAULT_DATA_ROOT, DEFAULT_LOG_ROOT, self.logger)
        except autosave_manager.AutosaveError as exc:
            self.logger.error("Autosave fehlgeschlagen: %s", exc)
''',
}

AUTOSTART_METHOD = '''    def _toggle_autostart(self) -> None:
        if self.autostart_var is None:
            raise GuiLauncherError("Autostart-Auswahl ist nicht verfügbar.")
        enabled = bool(self.autostart_var.get())
        try:
            active = self.autostart_manager.set_enabled(enabled)
        except AutostartError as exc:
            self.autostart_var.set(self.autostart_manager.is_enabled())
            self._append_output(f"Autostart:\\nFehler: {exc}\\n")
            self._set_status("Autostart konnte nicht geändert werden.", state="error")
            return
        label = "aktiviert" if active else "deaktiviert"
        self._set_status(f"Autostart beim Hochfahren: {label}.", state="success")

'''

AUTOSTART_UI = '''        self.autostart_var = tk.BooleanVar(value=self.autostart_manager.is_enabled())
        self.autostart_check = tk.Checkbutton(
            controls,
            text="Beim Hochfahren automatisch starten",
            variable=self.autostart_var,
            command=self._toggle_autostart,
        )
        if self.button_font is not None:
            self.autostart_check.configure(font=self.button_font)
        self.autostart_check.configure(
            padx=self.layout.field_padx,
            pady=self.layout.field_pady,
            takefocus=1,
            underline=0,
        )
        self.autostart_check.grid(
            row=2,
            column=0,
            sticky="w",
            pady=(self.layout.gap_sm, 0),
            padx=(0, self.layout.gap_md),
        )

'''

AUTOSTART_HELP = '''        if self.autostart_check is not None:
            self._register_help(
                self.autostart_check,
                "Startet das Tool nach der Linux-Anmeldung automatisch.",
                "Autostart: Aktiviert oder deaktiviert den benutzerspezifischen Linux-Autostart.",
            )
'''


def transform(source: str) -> str:
    tree = ast.parse(source)
    launcher_class = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "LauncherGui"),
        None,
    )
    if launcher_class is None:
        raise RuntimeError("LauncherGui fehlt.")
    found = {
        node.name: node
        for node in launcher_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing = sorted(set(METHODS) - set(found))
    if missing:
        raise RuntimeError(f"Methoden fehlen: {', '.join(missing)}")

    lines = source.splitlines(keepends=True)
    edits = []
    for name, replacement in METHODS.items():
        node = found[name]
        start = min([node.lineno] + [item.lineno for item in node.decorator_list]) - 1
        edits.append((start, node.end_lineno, replacement.rstrip("\n") + "\n"))
    for start, end, replacement in sorted(edits, reverse=True):
        lines[start:end] = [replacement]
    result = "".join(lines)

    result = result.replace("import threading\n", "", 1)
    if IMPORT not in result:
        anchor = "from task_runner import (\n"
        if anchor not in result:
            raise RuntimeError("Task-Runner-Importanker fehlt.")
        result = result.replace(anchor, IMPORT + anchor, 1)

    if "        self.autostart_var = None\n" not in result:
        result = result.replace(
            "        self.debug_var = None\n",
            "        self.debug_var = None\n        self.autostart_var = None\n",
            1,
        )
    if "        self.autostart_check = None\n" not in result:
        result = result.replace(
            "        self.debug_check = None\n",
            "        self.debug_check = None\n        self.autostart_check = None\n",
            1,
        )

    legacy_state = (
        "        self.autosave_config: autosave_manager.AutosaveConfig | None = None\n"
        "        self.autosave_job = None\n"
        "        self.logout_running = False\n"
    )
    lifecycle_state = (
        "        project_root = self.module_config.resolve().parents[1]\n"
        "        self.autostart_manager = AutostartManager(\n"
        "            project_root / \"scripts\" / \"start.sh\"\n"
        "        )\n"
        "        self.autosave_config: autosave_manager.AutosaveConfig | None = None\n"
        "        self.autosave_session = AutosaveSession(\n"
        "            self.root.after,\n"
        "            self.root.after_cancel,\n"
        "            self._run_autosave,\n"
        "        )\n"
    )
    if legacy_state in result:
        result = result.replace(legacy_state, lifecycle_state, 1)
    elif lifecycle_state not in result:
        raise RuntimeError("Lifecycle-Initialisierung konnte nicht verankert werden.")

    if AUTOSTART_UI not in result:
        anchor = "        self.refresh_button = tk.Button(\n"
        if anchor not in result:
            raise RuntimeError("Autostart-UI-Anker fehlt.")
        result = result.replace(anchor, AUTOSTART_UI + anchor, 1)

    if AUTOSTART_HELP not in result:
        anchor = "        if self.refresh_button is not None:\n"
        if anchor not in result:
            raise RuntimeError("Autostart-Hilfe-Anker fehlt.")
        result = result.replace(anchor, AUTOSTART_HELP + anchor, 1)

    if AUTOSTART_METHOD not in result:
        anchor = "    def _refresh_from_shortcut(self) -> None:\n"
        if anchor not in result:
            raise RuntimeError("Autostart-Methodenanker fehlt.")
        result = result.replace(anchor, AUTOSTART_METHOD + anchor, 1)

    ast.parse(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=TARGET)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    source = args.path.read_text(encoding="utf-8")
    result = transform(source)
    changed = result != source
    if args.check:
        return 1 if changed else 0
    if changed:
        args.path.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

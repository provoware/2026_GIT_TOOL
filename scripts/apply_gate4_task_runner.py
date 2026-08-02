#!/usr/bin/env python3
"""Wendet Gate 4 kontrolliert auf system/launcher_gui.py an."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "system" / "launcher_gui.py"
IMPORT = '''from task_runner import (
    CommandResult,
    CommandValidationError,
    TaskOutcome,
    TaskRunner,
    TaskRunnerError,
    execute_command,
    validate_command,
)
'''

METHODS = {
    "start_diagnostics": '''    def start_diagnostics(self) -> None:
        if self.task_runner.is_running("diagnostics"):
            self._set_status("Diagnose läuft bereits…", state="busy")
            return
        if self.diagnostics_button is not None:
            self.diagnostics_button.configure(state="disabled")
        self._set_status("Diagnose wird gestartet…", state="busy")
        try:
            started = self.task_runner.start(
                "diagnostics",
                self._run_diagnostics,
                self._finish_diagnostics,
            )
        except TaskRunnerError as exc:
            if self.diagnostics_button is not None:
                self.diagnostics_button.configure(state="normal")
            self._set_status(f"Diagnose konnte nicht starten: {exc}", state="error")
            return
        if not started:
            if self.diagnostics_button is not None:
                self.diagnostics_button.configure(state="normal")
            self._set_status("Diagnose läuft bereits…", state="busy")
''',
    "_run_maintenance_task": '''    def _run_maintenance_task(self, title: str, command: List[str]) -> None:
        clean_title = _require_text(title, "maintenance_title")
        try:
            clean_command = validate_command(command)
        except CommandValidationError as exc:
            self._set_status(exc.status_message, state="error")
            self._append_output(f"{clean_title}:\\nFehler: {exc}\\n")
            return
        if self.task_runner.is_running("maintenance"):
            self._set_status("Wartung läuft bereits…", state="busy")
            return
        self._set_maintenance_buttons("disabled")
        self._set_status(f"{clean_title} läuft…", state="busy")
        try:
            started = self.task_runner.start(
                "maintenance",
                lambda: self._execute_maintenance(clean_command),
                lambda outcome: self._finish_maintenance(clean_title, outcome),
            )
        except TaskRunnerError as exc:
            self._set_maintenance_buttons("normal")
            self._append_output(
                f"{clean_title}:\\nFehler: {exc}\\n"
                "Lösung: Bitte das Skript prüfen und erneut versuchen.\\n"
            )
            self._set_status(f"{clean_title} konnte nicht starten.", state="error")
            return
        if not started:
            self._set_maintenance_buttons("normal")
            self._set_status("Wartung läuft bereits…", state="busy")
''',
    "_execute_maintenance": '''    def _execute_maintenance(self, command: List[str]) -> CommandResult:
        return execute_command(command)
''',
    "_finish_maintenance": '''    def _finish_maintenance(
        self,
        title: str,
        outcome: TaskOutcome[CommandResult],
    ) -> None:
        self._set_maintenance_buttons("normal")
        if outcome.error is not None:
            status = "error"
            report = (
                f"{title}:\\n"
                f"Fehler: {outcome.error}\\n"
                "Lösung: Bitte das Skript prüfen und erneut versuchen.\\n"
            )
        else:
            result = outcome.value
            if not isinstance(result, CommandResult):
                raise GuiLauncherError("Wartungs-Ergebnis ist ungültig.")
            status = "success" if result.return_code == 0 else "error"
            report = self._format_maintenance_report(
                title,
                result.command,
                result.output,
                result.return_code,
            )
        self._append_output(report)
        if status == "success":
            self._set_status(f"{title} abgeschlossen.", state="success")
        else:
            self._set_status(f"{title} mit Problemen.", state="error")
''',
    "_run_diagnostics": '''    def _run_diagnostics(self) -> diagnostics_runner.DiagnosticsResult:
        script_path = self.module_config.resolve().parents[1] / "scripts" / "run_tests.sh"
        try:
            return diagnostics_runner.run_diagnostics(script_path)
        except diagnostics_runner.DiagnosticsError as exc:
            return diagnostics_runner.DiagnosticsResult(
                status="error",
                output=f"Diagnose fehlgeschlagen: {exc}",
                exit_code=2,
                duration_seconds=0.0,
                command=["bash", str(script_path)],
            )
''',
    "_finish_diagnostics": '''    def _finish_diagnostics(
        self,
        outcome: TaskOutcome[diagnostics_runner.DiagnosticsResult],
    ) -> None:
        if self.diagnostics_button is not None:
            self.diagnostics_button.configure(state="normal")
        if outcome.error is not None:
            script_path = self.module_config.resolve().parents[1] / "scripts" / "run_tests.sh"
            result = diagnostics_runner.DiagnosticsResult(
                status="error",
                output=f"Diagnose fehlgeschlagen: {outcome.error}",
                exit_code=2,
                duration_seconds=0.0,
                command=["bash", str(script_path)],
            )
        else:
            result = outcome.value
        if not isinstance(result, diagnostics_runner.DiagnosticsResult):
            raise GuiLauncherError("Diagnose-Ergebnis ist ungültig.")
        report = self._format_diagnostics_report(result)
        current = ""
        if self.output_text is not None:
            current = self.output_text.get("1.0", "end").strip()
        combined = f"{current}\\n\\n{report}" if current else report
        self._set_output(combined)
        if result.status == "ok":
            self._set_status("Diagnose abgeschlossen.", state="success")
        else:
            self._set_status("Diagnose mit Problemen abgeschlossen.", state="error")
''',
}


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

    legacy_state = (
        "        self.diagnostics_running = False\n"
        "        self.maintenance_running = False\n"
    )
    runner_state = "        self.task_runner = TaskRunner(self.root.after)\n"
    if legacy_state in result:
        result = result.replace(legacy_state, runner_state, 1)
    elif runner_state not in result:
        raise RuntimeError("Task-Runner-Initialisierung konnte nicht verankert werden.")

    result = result.replace("import subprocess\n", "", 1)
    if IMPORT not in result:
        anchor = "from undo_redo import UndoRedoAction, UndoRedoError, UndoRedoManager\n"
        if anchor not in result:
            raise RuntimeError("Importanker fehlt.")
        result = result.replace(anchor, IMPORT + anchor, 1)

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

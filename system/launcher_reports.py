#!/usr/bin/env python3
"""Pure report formatters for the Tkinter launcher.

This module must stay free of Tkinter access, logging, subprocess execution,
thread management and filesystem writes. It converts validated result objects
into stable human-readable text only.
"""

from __future__ import annotations

from typing import Iterable, Sequence


class LauncherReportError(ValueError):
    """Raised when a report formatter receives invalid input."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LauncherReportError(f"{label} fehlt oder ist leer.")
    return value.strip()


def _require_string_sequence(value: object, label: str) -> Sequence[str]:
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
        raise LauncherReportError(f"{label} ist keine Textliste.")
    return value


def format_maintenance_report(
    title: str,
    command: Sequence[str],
    output: str,
    return_code: int,
) -> str:
    clean_title = _require_text(title, "maintenance_title")
    clean_command = _require_string_sequence(command, "maintenance_command")
    clean_output = _require_text(output, "maintenance_output")
    if not isinstance(return_code, int):
        raise LauncherReportError("maintenance_return_code ist ungültig.")
    return "\n".join(
        [
            f"{clean_title}:",
            f"Kommando: {' '.join(clean_command)}",
            f"Exit-Code: {return_code}",
            "",
            "Ausgabe:",
            clean_output,
            "",
        ]
    )


def format_diagnostics_report(result: object) -> str:
    required = ("status", "duration_seconds", "exit_code", "command", "output")
    if any(not hasattr(result, name) for name in required):
        raise LauncherReportError("Diagnose-Ergebnis ist unvollständig.")
    command = _require_string_sequence(getattr(result, "command"), "diagnostics_command")
    status = _require_text(getattr(result, "status"), "diagnostics_status")
    duration = getattr(result, "duration_seconds")
    exit_code = getattr(result, "exit_code")
    if not isinstance(duration, (int, float)):
        raise LauncherReportError("diagnostics_duration ist ungültig.")
    if not isinstance(exit_code, int):
        raise LauncherReportError("diagnostics_exit_code ist ungültig.")
    output = getattr(result, "output")
    if output is None:
        output = ""
    if not isinstance(output, str):
        raise LauncherReportError("diagnostics_output ist ungültig.")
    lines = [
        "Diagnose (Tests + Codequalität):",
        f"Status: {status}",
        f"Dauer: {duration:.1f} Sekunden",
        f"Exit-Code: {exit_code}",
        f"Kommando: {' '.join(command)}",
        "",
        "Ausgabe:",
        output or "Keine Ausgabe erhalten.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def append_file_status(text: str, report: object) -> str:
    base = _require_text(text, "output_text")
    if not hasattr(report, "traffic_light") or not hasattr(report, "issues"):
        raise LauncherReportError("Datei-Statusbericht ist unvollständig.")
    traffic_light = _require_text(getattr(report, "traffic_light"), "traffic_light")
    issues = getattr(report, "issues")
    if not isinstance(issues, Iterable):
        raise LauncherReportError("file_status_issues ist ungültig.")
    issues = list(issues)
    lines = [base.rstrip(), "", "Datei-Status (Ampel):", f"Ampelstatus: {traffic_light}"]
    if issues:
        lines.append("Datei-Probleme:")
        for issue in issues:
            if not hasattr(issue, "message") or not hasattr(issue, "severity"):
                raise LauncherReportError("Datei-Problem ist unvollständig.")
            lines.append(f"- {issue.message} (Stufe: {issue.severity})")
    else:
        lines.append("Keine Datei-Probleme gefunden.")
    return "\n".join(lines).rstrip() + "\n"


def append_end_audit(text: str, report: object) -> str:
    base = _require_text(text, "output_text")
    required = ("status", "open_tasks", "issues")
    if any(not hasattr(report, name) for name in required):
        raise LauncherReportError("End-Audit-Bericht ist unvollständig.")
    issues = list(getattr(report, "issues"))
    lines = [
        base.rstrip(),
        "",
        "End-Audit (Release-Status):",
        f"Status: {report.status}",
        f"Offene Aufgaben: {report.open_tasks}",
    ]
    if issues:
        lines.append("Hinweise:")
        for issue in issues:
            if not hasattr(issue, "message") or not hasattr(issue, "severity"):
                raise LauncherReportError("Audit-Hinweis ist unvollständig.")
            lines.append(f"- {issue.message} (Stufe: {issue.severity})")
    else:
        lines.append("Keine offenen Hinweise. Release-Status ist grün.")
    return "\n".join(lines).rstrip() + "\n"


def append_selftests(text: str, results: Iterable[object]) -> str:
    base = _require_text(text, "output_text")
    items = list(results)
    lines = [base.rstrip(), "", "Modul-Selbsttests:"]
    for result in items:
        required = ("name", "module_id", "status", "message")
        if any(not hasattr(result, name) for name in required):
            raise LauncherReportError("Selbsttest-Ergebnis ist unvollständig.")
        lines.append(
            f"- {result.name} ({result.module_id}): {result.status} – {result.message}"
        )
    return "\n".join(lines).rstrip() + "\n"


def append_error_simulation(text: str, results: Iterable[object]) -> str:
    base = _require_text(text, "output_text")
    items = list(results)
    lines = [base.rstrip(), "", "Fehler-Simulation (Laienfehler):"]
    for result in items:
        required = ("title", "status", "message", "hint")
        if any(not hasattr(result, name) for name in required):
            raise LauncherReportError("Simulationsergebnis ist unvollständig.")
        lines.extend(
            [
                f"- Fall: {result.title}",
                f"  Ergebnis: {result.status}",
                f"  Meldung: {result.message}",
                f"  Hinweis: {result.hint}",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"

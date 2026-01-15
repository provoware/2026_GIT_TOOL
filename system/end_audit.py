#!/usr/bin/env python3
"""End-Audit-Check: Release-Status aus Kernindikatoren ableiten."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List

import qa_checks
import todo_manager
from config_utils import ensure_path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class EndAuditError(ValueError):
    """Fehler im End-Audit-Check."""


@dataclass(frozen=True)
class AuditIssue:
    message: str
    severity: str


@dataclass(frozen=True)
class AuditReport:
    status: str
    issues: List[AuditIssue]
    open_tasks: int


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EndAuditError(f"{label} ist leer oder ungültig.")
    return value.strip()


def run_end_audit(root: Path) -> AuditReport:
    ensure_path(root, "root", EndAuditError)
    root_dir = root.resolve()
    issues: List[AuditIssue] = []

    file_report = qa_checks.check_release_files(root_dir)
    for issue in file_report.issues:
        issues.append(AuditIssue(message=issue.message, severity=issue.severity))

    config = todo_manager.load_config(root_dir / "config" / "todo_config.json")
    lines = todo_manager.read_todo_lines(root_dir / config.todo_path)
    progress = todo_manager.calculate_progress(lines)
    open_tasks = max(progress.total - progress.done, 0)
    if open_tasks > 0:
        issues.append(
            AuditIssue(
                message=f"Offene Aufgaben in todo.txt: {open_tasks}.",
                severity="mittel",
            )
        )

    status = "bereit" if not issues else "nicht bereit"
    return AuditReport(status=status, issues=issues, open_tasks=open_tasks)


def render_report(report: AuditReport) -> str:
    if not isinstance(report, AuditReport):
        raise EndAuditError("report ist ungültig.")
    lines = [
        "End-Audit (Release-Status):",
        f"Status: {report.status}",
        f"Offene Aufgaben: {report.open_tasks}",
    ]
    if report.issues:
        lines.append("Hinweise:")
        for issue in report.issues:
            clean_message = _require_text(issue.message, "issue_message")
            clean_severity = _require_text(issue.severity, "issue_severity")
            lines.append(f"- {clean_message} (Stufe: {clean_severity})")
    else:
        lines.append("Keine offenen Hinweise. Release-Status ist grün.")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="End-Audit-Check: Release-Status aus Kernindikatoren ableiten.",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        report = run_end_audit(args.root)
    except (EndAuditError, qa_checks.QualityCheckError, todo_manager.TodoError) as exc:
        print(f"End-Audit fehlgeschlagen: {exc}")
        return 2
    print(render_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

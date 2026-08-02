#!/usr/bin/env python3
"""Apply the Gate-1 report formatter extraction to system/launcher_gui.py.

The codemod is intentionally narrow and idempotent. It updates only the import
section and the six pure report-formatting methods approved for Gate 1.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "system" / "launcher_gui.py"

IMPORT_LINE = (
    "from launcher_reports import (\n"
    "    append_end_audit,\n"
    "    append_error_simulation,\n"
    "    append_file_status,\n"
    "    append_selftests,\n"
    "    format_diagnostics_report,\n"
    "    format_maintenance_report,\n"
    ")\n"
)
IMPORT_ANCHOR = "from logging_center import setup_logging as setup_logging_center\n"

METHOD_REPLACEMENTS = {
    "_format_maintenance_report": (
        "    def _format_maintenance_report(\n"
        "        self, title: str, command: List[str], output: str, return_code: int\n"
        "    ) -> str:\n"
        "        return format_maintenance_report(title, command, output, return_code)\n"
    ),
    "_format_diagnostics_report": (
        "    def _format_diagnostics_report(self, result: diagnostics_runner.DiagnosticsResult) -> str:\n"
        "        return format_diagnostics_report(result)\n"
    ),
    "_append_file_status": (
        "    def _append_file_status(self, text: str, report: qa_checks.FileStatusReport) -> str:\n"
        "        return append_file_status(text, report)\n"
    ),
    "_append_end_audit": (
        "    def _append_end_audit(self, text: str, report: end_audit.AuditReport) -> str:\n"
        "        return append_end_audit(text, report)\n"
    ),
    "_append_selftests": (
        "    def _append_selftests(self, text: str, results: List[module_selftests.SelftestResult]) -> str:\n"
        "        return append_selftests(text, results)\n"
    ),
    "_append_error_simulation": (
        "    def _append_error_simulation(\n"
        "        self, text: str, results: List[error_simulation.SimulationResult]\n"
        "    ) -> str:\n"
        "        return append_error_simulation(text, results)\n"
    ),
}


class CodemodError(RuntimeError):
    """Raised when the source does not match the expected Gate-1 structure."""


def _launcher_class(tree: ast.Module) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "LauncherGui":
            return node
    raise CodemodError("Klasse LauncherGui wurde nicht gefunden.")


def _method_ranges(source: str) -> dict[str, tuple[int, int]]:
    tree = ast.parse(source)
    launcher = _launcher_class(tree)
    ranges: dict[str, tuple[int, int]] = {}
    for node in launcher.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in METHOD_REPLACEMENTS:
            if node.end_lineno is None:
                raise CodemodError(f"Endzeile für {node.name} fehlt.")
            ranges[node.name] = (node.lineno, node.end_lineno)
    missing = sorted(set(METHOD_REPLACEMENTS) - set(ranges))
    if missing:
        raise CodemodError(f"Erwartete Methoden fehlen: {', '.join(missing)}")
    return ranges


def transform(source: str) -> str:
    if not isinstance(source, str) or not source.strip():
        raise CodemodError("Quelldatei ist leer.")

    if "from launcher_reports import (" not in source:
        if IMPORT_ANCHOR not in source:
            raise CodemodError("Import-Anker wurde nicht gefunden.")
        source = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_LINE, 1)

    lines = source.splitlines(keepends=True)
    ranges = _method_ranges(source)
    for name, (start, end) in sorted(ranges.items(), key=lambda item: item[1][0], reverse=True):
        replacement = METHOD_REPLACEMENTS[name]
        lines[start - 1 : end] = [replacement]

    result = "".join(lines)
    ast.parse(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Prüft, ob der Codemod bereits angewendet ist")
    parser.add_argument("--path", type=Path, default=TARGET, help="Alternative launcher_gui.py")
    args = parser.parse_args()

    path = args.path.resolve()
    source = path.read_text(encoding="utf-8")
    transformed = transform(source)

    if args.check:
        if source != transformed:
            print(f"Gate-1-Codemod ist noch nicht angewendet: {path}")
            return 1
        print(f"Gate-1-Codemod ist aktuell: {path}")
        return 0

    if source == transformed:
        print(f"Keine Änderung erforderlich: {path}")
        return 0
    path.write_text(transformed, encoding="utf-8", newline="\n")
    print(f"Gate-1-Codemod angewendet: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

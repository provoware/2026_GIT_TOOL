import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "system"))

from launcher_reports import (
    LauncherReportError,
    append_end_audit,
    append_error_simulation,
    append_file_status,
    append_selftests,
    format_diagnostics_report,
    format_maintenance_report,
)


def test_format_maintenance_report_preserves_contract() -> None:
    report = format_maintenance_report(
        "System-Scan",
        ["bash", "scripts/system_scan.sh"],
        "Alles in Ordnung.",
        0,
    )
    assert report == (
        "System-Scan:\n"
        "Kommando: bash scripts/system_scan.sh\n"
        "Exit-Code: 0\n\n"
        "Ausgabe:\n"
        "Alles in Ordnung.\n"
    )


def test_format_diagnostics_report_uses_fallback_output() -> None:
    result = SimpleNamespace(
        status="ok",
        duration_seconds=1.25,
        exit_code=0,
        command=["bash", "scripts/run_tests.sh"],
        output="",
    )
    report = format_diagnostics_report(result)
    assert "Dauer: 1.2 Sekunden" in report
    assert "Keine Ausgabe erhalten." in report


def test_append_file_status_formats_issues() -> None:
    issue = SimpleNamespace(message="Datei fehlt", severity="kritisch")
    report = SimpleNamespace(traffic_light="rot", issues=[issue])
    text = append_file_status("Basis", report)
    assert "Datei-Status (Ampel):" in text
    assert "- Datei fehlt (Stufe: kritisch)" in text


def test_append_end_audit_formats_clean_state() -> None:
    report = SimpleNamespace(status="grün", open_tasks=0, issues=[])
    text = append_end_audit("Basis", report)
    assert "Status: grün" in text
    assert "Keine offenen Hinweise. Release-Status ist grün." in text


def test_append_selftests_preserves_result_order() -> None:
    results = [
        SimpleNamespace(name="A", module_id="a", status="ok", message="fertig"),
        SimpleNamespace(name="B", module_id="b", status="warn", message="Hinweis"),
    ]
    text = append_selftests("Basis", results)
    assert text.index("A (a)") < text.index("B (b)")


def test_append_error_simulation_formats_all_fields() -> None:
    result = SimpleNamespace(
        title="Ungültige Datei",
        status="ok",
        message="Fehler erkannt",
        hint="Datei korrigieren",
    )
    text = append_error_simulation("Basis", [result])
    assert "Fall: Ungültige Datei" in text
    assert "Hinweis: Datei korrigieren" in text


@pytest.mark.parametrize(
    "call",
    [
        lambda: format_maintenance_report("", ["bash"], "Ausgabe", 0),
        lambda: format_maintenance_report("Scan", "bash", "Ausgabe", 0),
        lambda: format_diagnostics_report(SimpleNamespace()),
        lambda: append_file_status("", SimpleNamespace(traffic_light="grün", issues=[])),
    ],
)
def test_invalid_inputs_raise_report_error(call) -> None:
    with pytest.raises(LauncherReportError):
        call()

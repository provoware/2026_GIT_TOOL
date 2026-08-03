#!/usr/bin/env python3
"""Erzeugt den konsolidierten UI-Abnahmebericht und einen belastbaren Exitcode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "system"))

from ui_acceptance import (
    DEVICE_PROFILES,
    Finding,
    evaluate_profile_support,
    evaluate_runtime_probe,
    evaluate_theme_contrast,
    summarize,
)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON-Wurzel muss ein Objekt sein: {path}")
    return payload


def _mobile_runtime_findings(records: Sequence[Mapping[str, Any]]) -> list[Finding]:
    profiles = {profile.key: profile for profile in DEVICE_PROFILES}
    findings: list[Finding] = []
    for record in records:
        profile_key = str(record.get("profile", "")).strip()
        surface = str(record.get("surface", "")).strip()
        profile = profiles.get(profile_key)
        if profile is None or profile.native_tk_supported:
            continue
        requested = list(record.get("requested_size", []))
        actual = list(record.get("actual_size", []))
        honored = len(requested) == 2 and len(actual) == 2 and actual[0] <= requested[0] and actual[1] <= requested[1]
        overflow = list(record.get("overflow_widgets", []))
        undersized = list(record.get("undersized_touch_targets", []))
        findings.extend(
            [
                Finding(
                    check="mobile_viewport_simulation",
                    status="simulated" if honored else "blocked",
                    severity="minor" if honored else "critical",
                    message=(
                        f"{surface}/{profile_key}: Viewportsimulation wurde eingehalten."
                        if honored
                        else f"{surface}/{profile_key}: Tk-Mindestgröße überschreitet den simulierten Viewport."
                    ),
                    profile=profile_key,
                    surface=surface,
                    details={"requested": requested, "actual": actual},
                ),
                Finding(
                    check="mobile_overflow_simulation",
                    status="simulated" if not overflow else "blocked",
                    severity="minor" if not overflow else "critical",
                    message=(
                        f"{surface}/{profile_key}: keine Überläufe in der Simulation."
                        if not overflow
                        else f"{surface}/{profile_key}: {len(overflow)} Überlaufproblem(e) in der Simulation."
                    ),
                    profile=profile_key,
                    surface=surface,
                    details={"widgets": overflow},
                ),
                Finding(
                    check="mobile_touch_simulation",
                    status="simulated" if not undersized else "warning",
                    severity="minor",
                    message=(
                        f"{surface}/{profile_key}: gemessene Ziele erreichen 44px."
                        if not undersized
                        else f"{surface}/{profile_key}: {len(undersized)} Ziel(e) unterschreiten 44px."
                    ),
                    profile=profile_key,
                    surface=surface,
                    details={"widgets": undersized},
                ),
            ]
        )
    return findings


def _markdown(findings: Sequence[Finding], summary: Mapping[str, Any]) -> str:
    lines = [
        "# UI-Abnahmebericht",
        "",
        "## Gesamtstatus",
        "",
        f"- Automatisierte Abnahme: **{'BESTANDEN' if summary['automated_passed'] else 'NICHT BESTANDEN'}**",
        f"- Physische Geräteabnahme: **{'ABGESCHLOSSEN' if summary['physical_complete'] else 'OFFEN'}**",
        "- Tablet- und iPhone-Messungen unter Xvfb sind ausschließlich Viewportsimulationen.",
        "- Tkinter ist keine native iOS-/iPadOS-/Android-Laufzeit.",
        "",
        "## Zählung",
        "",
    ]
    for status, count in summary["counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Befunde", ""])
    for finding in findings:
        location = "/".join(part for part in (finding.profile, finding.surface) if part)
        prefix = f"[{location}] " if location else ""
        lines.append(
            f"- **{finding.status.upper()} · {finding.severity} · {finding.check}:** "
            f"{prefix}{finding.message}"
        )
    lines.extend(
        [
            "",
            "## Verbindliche physische Restprüfung",
            "",
            "- Linux: Maus, vollständige Tastaturbedienung, sichtbarer Fokus, Themewechsel, Zoom, Fensterverkleinerung und Shutdown auf realem Desktop prüfen.",
            "- Tablet: Zielplattform und Auslieferungsweg festlegen; Rotation, Touchziele, Bildschirmtastatur und Skalierung auf echter Hardware prüfen.",
            "- iPhone: Vor einer Freigabe ist eine native oder webbasierte mobile Oberfläche erforderlich; danach VoiceOver, Dynamic Type, Safe Areas, Rotation und Touch prüfen.",
            "- Jeder physische Lauf benötigt Gerät, Betriebssystemversion, Auflösung/Skalierung, Datum, Prüfer und Screenshotnachweis.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "launcher_gui.json",
    )
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()

    config = _read_json(args.config)
    findings: list[Finding] = []
    findings.extend(evaluate_theme_contrast(config.get("themes", {})))
    findings.extend(evaluate_profile_support())

    if args.runtime is not None:
        runtime = _read_json(args.runtime)
        records = runtime.get("records", [])
        if not isinstance(records, list):
            raise ValueError("Runtime-Bericht enthält keine Datensatzliste.")
        native_profiles = {
            profile.key for profile in DEVICE_PROFILES if profile.native_tk_supported
        }
        native_records = [
            record
            for record in records
            if isinstance(record, Mapping) and record.get("profile") in native_profiles
        ]
        findings.extend(evaluate_runtime_probe(native_records))
        findings.extend(_mobile_runtime_findings(records))

    result = summarize(findings)
    document = {
        "schema_version": 1,
        "summary": result,
        "findings": [finding.to_dict() for finding in findings],
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(_markdown(findings, result), encoding="utf-8")
    return 0 if result["automated_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

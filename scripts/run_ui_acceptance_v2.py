#!/usr/bin/env python3
"""Kanonischer UI-Abnahmebericht einschließlich Pflichtsichtbarkeit."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import run_ui_acceptance as base
from ui_acceptance import DEVICE_PROFILES, Finding


def native_required_visibility_findings(
    records: Sequence[Mapping[str, Any]],
) -> list[Finding]:
    native_profiles = {
        profile.key for profile in DEVICE_PROFILES if profile.native_tk_supported
    }
    findings: list[Finding] = []
    for record in records:
        profile = str(record.get("profile", "")).strip()
        surface = str(record.get("surface", "")).strip()
        if profile not in native_profiles:
            continue
        hidden = list(record.get("hidden_required_widgets", []))
        findings.append(
            Finding(
                check="required_visibility",
                status="passed" if not hidden else "failed",
                severity="info" if not hidden else "critical",
                message=(
                    f"{surface}/{profile}: alle zentralen Bereiche sind sichtbar."
                    if not hidden
                    else f"{surface}/{profile}: {len(hidden)} zentrale Bereich(e) sind nicht sichtbar."
                ),
                profile=profile,
                surface=surface,
                details={"widgets": hidden},
            )
        )
    return findings


def mobile_required_visibility_findings(
    records: Sequence[Mapping[str, Any]],
) -> list[Finding]:
    mobile_profiles = {
        profile.key for profile in DEVICE_PROFILES if not profile.native_tk_supported
    }
    findings: list[Finding] = []
    for record in records:
        profile = str(record.get("profile", "")).strip()
        surface = str(record.get("surface", "")).strip()
        if profile not in mobile_profiles:
            continue
        hidden = list(record.get("hidden_required_widgets", []))
        findings.append(
            Finding(
                check="mobile_required_visibility_simulation",
                status="simulated" if not hidden else "blocked",
                severity="minor" if not hidden else "critical",
                message=(
                    f"{surface}/{profile}: alle zentralen Bereiche sind in der Simulation sichtbar."
                    if not hidden
                    else f"{surface}/{profile}: {len(hidden)} zentrale Bereich(e) sind in der Simulation nicht sichtbar."
                ),
                profile=profile,
                surface=surface,
                details={"widgets": hidden},
            )
        )
    return findings


_ORIGINAL_NATIVE = base._native_text_clipping_findings
_ORIGINAL_MOBILE = base._mobile_runtime_findings


def _native_with_visibility(records):
    return _ORIGINAL_NATIVE(records) + native_required_visibility_findings(records)


def _mobile_with_visibility(records):
    return _ORIGINAL_MOBILE(records) + mobile_required_visibility_findings(records)


def main() -> int:
    base._native_text_clipping_findings = _native_with_visibility
    base._mobile_runtime_findings = _mobile_with_visibility
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())

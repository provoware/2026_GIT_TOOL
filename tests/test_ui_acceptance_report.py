from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_ui_acceptance import _mobile_runtime_findings, _native_text_clipping_findings


def record(profile: str, clipped: list[dict]) -> dict:
    return {
        "profile": profile,
        "surface": "launcher",
        "requested_size": [1024, 768],
        "actual_size": [1024, 768],
        "overflow_widgets": [],
        "clipped_text_widgets": clipped,
        "undersized_touch_targets": [],
    }


def test_native_text_clipping_is_an_automated_failure():
    findings = _native_text_clipping_findings(
        [record("linux_compact", [{"widget": "Button:refresh"}])]
    )

    assert len(findings) == 1
    assert findings[0].status == "failed"
    assert findings[0].severity == "major"


def test_clean_native_text_is_passed():
    findings = _native_text_clipping_findings([record("linux_desktop", [])])

    assert findings[0].status == "passed"


def test_mobile_text_clipping_remains_simulation_blocker_not_physical_pass():
    findings = _mobile_runtime_findings(
        [record("tablet_portrait", [{"widget": "Button:logs"}])]
    )
    text = next(item for item in findings if item.check == "mobile_text_simulation")

    assert text.status == "blocked"
    assert text.severity == "critical"


def test_clean_mobile_text_is_still_only_simulated():
    findings = _mobile_runtime_findings([record("tablet_landscape", [])])
    text = next(item for item in findings if item.check == "mobile_text_simulation")

    assert text.status == "simulated"

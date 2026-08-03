from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system"))

from ui_acceptance import (
    DEVICE_PROFILES,
    Finding,
    UiAcceptanceError,
    contrast_ratio,
    evaluate_profile_support,
    evaluate_runtime_probe,
    evaluate_theme_contrast,
    summarize,
)


ROOT = Path(__file__).resolve().parents[1]


def launcher_config() -> dict:
    return json.loads((ROOT / "config" / "launcher_gui.json").read_text(encoding="utf-8"))


def test_contrast_ratio_is_symmetric_and_matches_reference_values():
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0)
    assert contrast_ratio("#ffffff", "#000000") == pytest.approx(21.0)
    assert contrast_ratio("#777777", "#ffffff") == pytest.approx(4.478, rel=1e-3)


def test_all_configured_text_pairs_reach_wcag_aa():
    findings = evaluate_theme_contrast(launcher_config()["themes"])
    failures = [finding.message for finding in findings if finding.status == "failed"]

    assert not failures, "\n".join(failures)


def test_profile_contract_distinguishes_native_simulation_and_blocker():
    findings = evaluate_profile_support()
    by_key = {(item.profile, item.surface): item for item in findings}

    assert by_key[("linux_desktop", "launcher")].status == "passed"
    assert by_key[("linux_desktop", "main_window")].status == "passed"
    assert by_key[("tablet_landscape", "launcher")].status == "simulated"
    assert by_key[("tablet_portrait", "main_window")].status == "blocked"
    assert by_key[("iphone_portrait", "launcher")].status == "blocked"
    assert all(profile.physical_required for profile in DEVICE_PROFILES)


def test_runtime_probe_detects_unhonored_viewport_overflow_and_small_targets():
    findings = evaluate_runtime_probe(
        [
            {
                "profile": "iphone_portrait",
                "surface": "launcher",
                "requested_size": [390, 844],
                "actual_size": [640, 844],
                "overflow_widgets": ["controls.show_all"],
                "focusable_count": 12,
                "undersized_touch_targets": [
                    {"widget": "controls.theme", "width": 80, "height": 31}
                ],
            }
        ]
    )
    by_check = {finding.check: finding for finding in findings}

    assert by_check["viewport_honored"].status == "failed"
    assert by_check["widget_overflow"].status == "failed"
    assert by_check["focus_order"].status == "passed"
    assert by_check["touch_targets"].status == "warning"


def test_runtime_probe_accepts_clean_measurement():
    findings = evaluate_runtime_probe(
        [
            {
                "profile": "linux_desktop",
                "surface": "launcher",
                "requested_size": [1440, 900],
                "actual_size": [1440, 900],
                "overflow_widgets": [],
                "focusable_count": 17,
                "undersized_touch_targets": [],
            }
        ]
    )

    assert {finding.status for finding in findings} == {"passed"}
    assert summarize(findings)["automated_passed"] is True


def test_summary_never_calls_simulated_or_blocked_profiles_physically_complete():
    findings = evaluate_profile_support()
    result = summarize(findings)

    assert result["physical_complete"] is False
    assert result["physical_pending"]


def test_invalid_colors_and_duplicate_runtime_records_fail_early():
    with pytest.raises(UiAcceptanceError):
        contrast_ratio("white", "#000000")

    record = {
        "profile": "linux_desktop",
        "surface": "launcher",
        "requested_size": [1440, 900],
        "actual_size": [1440, 900],
        "overflow_widgets": [],
        "focusable_count": 1,
        "undersized_touch_targets": [],
    }
    with pytest.raises(UiAcceptanceError):
        evaluate_runtime_probe([record, record])


def test_summary_rejects_unknown_status():
    finding = Finding(
        check="example",
        status="unknown",
        severity="info",
        message="invalid",
    )
    with pytest.raises(UiAcceptanceError):
        summarize([finding])

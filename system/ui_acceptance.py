#!/usr/bin/env python3
"""Prüfbarer Vertrag für UI-, Responsive- und Barrierefreiheitsabnahmen."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

from ui_responsive import MAIN_WINDOW_MIN_HEIGHT, MAIN_WINDOW_MIN_WIDTH


class UiAcceptanceError(ValueError):
    """Ungültige Eingaben oder inkonsistente Abnahmedaten."""


@dataclass(frozen=True)
class DeviceProfile:
    key: str
    label: str
    width: int
    height: int
    platform: str
    input_mode: str
    native_tk_supported: bool
    physical_required: bool


@dataclass(frozen=True)
class SurfaceSpec:
    key: str
    label: str
    minimum_width: int
    minimum_height: int


@dataclass(frozen=True)
class Finding:
    check: str
    status: str
    severity: str
    message: str
    profile: str | None = None
    surface: str | None = None
    details: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEVICE_PROFILES: tuple[DeviceProfile, ...] = (
    DeviceProfile(
        key="linux_desktop",
        label="Linux Desktop 1440×900",
        width=1440,
        height=900,
        platform="linux",
        input_mode="keyboard_pointer",
        native_tk_supported=True,
        physical_required=True,
    ),
    DeviceProfile(
        key="linux_compact",
        label="Linux kompakt 1024×768",
        width=1024,
        height=768,
        platform="linux",
        input_mode="keyboard_pointer",
        native_tk_supported=True,
        physical_required=True,
    ),
    DeviceProfile(
        key="tablet_landscape",
        label="Tablet quer 1024×768",
        width=1024,
        height=768,
        platform="tablet",
        input_mode="touch",
        native_tk_supported=False,
        physical_required=True,
    ),
    DeviceProfile(
        key="tablet_portrait",
        label="Tablet hoch 768×1024",
        width=768,
        height=1024,
        platform="tablet",
        input_mode="touch",
        native_tk_supported=False,
        physical_required=True,
    ),
    DeviceProfile(
        key="iphone_portrait",
        label="iPhone hoch 390×844",
        width=390,
        height=844,
        platform="ios",
        input_mode="touch",
        native_tk_supported=False,
        physical_required=True,
    ),
    DeviceProfile(
        key="iphone_landscape",
        label="iPhone quer 844×390",
        width=844,
        height=390,
        platform="ios",
        input_mode="touch",
        native_tk_supported=False,
        physical_required=True,
    ),
)

SURFACES: tuple[SurfaceSpec, ...] = (
    SurfaceSpec("launcher", "Launcher", 640, 420),
    SurfaceSpec(
        "main_window",
        "Hauptfenster",
        MAIN_WINDOW_MIN_WIDTH,
        MAIN_WINDOW_MIN_HEIGHT,
    ),
)

CONTRAST_PAIRS: tuple[tuple[str, str, str, float], ...] = (
    ("Grundtext", "background", "foreground", 4.5),
    ("Schaltflächen", "button_background", "button_foreground", 4.5),
    ("Status Erfolg", "status_success", "status_foreground", 4.5),
    ("Status Fehler", "status_error", "status_foreground", 4.5),
    ("Status beschäftigt", "status_busy", "status_foreground", 4.5),
)

VALID_STATUSES = {"passed", "warning", "failed", "simulated", "blocked", "pending"}
VALID_SEVERITIES = {"info", "minor", "major", "critical"}


def _require_positive_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise UiAcceptanceError(f"{name} muss eine positive Ganzzahl sein.")
    return value


def _require_hex_color(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise UiAcceptanceError(f"{name} ist keine Farbe.")
    candidate = value.strip().lower()
    if len(candidate) != 7 or not candidate.startswith("#"):
        raise UiAcceptanceError(f"{name} muss im Format #rrggbb vorliegen.")
    try:
        int(candidate[1:], 16)
    except ValueError as exc:
        raise UiAcceptanceError(f"{name} enthält ungültige Hex-Zeichen.") from exc
    return candidate


def _linear_channel(value: int) -> float:
    channel = value / 255.0
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    candidate = _require_hex_color(color, "color")
    red, green, blue = (int(candidate[index : index + 2], 16) for index in (1, 3, 5))
    return (
        0.2126 * _linear_channel(red)
        + 0.7152 * _linear_channel(green)
        + 0.0722 * _linear_channel(blue)
    )


def contrast_ratio(first: str, second: str) -> float:
    first_luminance = relative_luminance(first)
    second_luminance = relative_luminance(second)
    lighter = max(first_luminance, second_luminance)
    darker = min(first_luminance, second_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def evaluate_theme_contrast(themes: Mapping[str, Any]) -> list[Finding]:
    if not isinstance(themes, Mapping) or not themes:
        raise UiAcceptanceError("Themes fehlen.")
    findings: list[Finding] = []
    for theme_name, payload in themes.items():
        if not isinstance(theme_name, str) or not theme_name.strip():
            raise UiAcceptanceError("Theme-Name ist ungültig.")
        if not isinstance(payload, Mapping):
            raise UiAcceptanceError(f"Theme {theme_name} ist ungültig.")
        colors = payload.get("colors")
        if not isinstance(colors, Mapping):
            raise UiAcceptanceError(f"Theme {theme_name} enthält keine Farben.")
        for label, background_key, foreground_key, minimum in CONTRAST_PAIRS:
            background = _require_hex_color(colors.get(background_key), background_key)
            foreground = _require_hex_color(colors.get(foreground_key), foreground_key)
            ratio = contrast_ratio(background, foreground)
            passed = ratio >= minimum
            findings.append(
                Finding(
                    check="contrast",
                    status="passed" if passed else "failed",
                    severity="info" if passed else "major",
                    message=(
                        f"{theme_name}: {label} erreicht {ratio:.2f}:1 "
                        f"(Minimum {minimum:.1f}:1)."
                    ),
                    details={
                        "theme": theme_name,
                        "role": label,
                        "ratio": round(ratio, 3),
                        "minimum": minimum,
                        "background": background,
                        "foreground": foreground,
                    },
                )
            )
    return findings


def evaluate_profile_support(
    profiles: Sequence[DeviceProfile] = DEVICE_PROFILES,
    surfaces: Sequence[SurfaceSpec] = SURFACES,
) -> list[Finding]:
    findings: list[Finding] = []
    for profile in profiles:
        _require_positive_int(profile.width, "profile.width")
        _require_positive_int(profile.height, "profile.height")
        for surface in surfaces:
            fits = (
                profile.width >= surface.minimum_width
                and profile.height >= surface.minimum_height
            )
            details = {
                "viewport": [profile.width, profile.height],
                "minimum": [surface.minimum_width, surface.minimum_height],
                "native_tk_supported": profile.native_tk_supported,
                "input_mode": profile.input_mode,
            }
            if profile.native_tk_supported and fits:
                status = "passed"
                severity = "info"
                message = f"{surface.label} passt nativ in {profile.label}."
            elif profile.native_tk_supported:
                status = "failed"
                severity = "critical"
                message = (
                    f"{surface.label} überschreitet den nativen Viewport {profile.label}."
                )
            elif fits:
                status = "simulated"
                severity = "minor"
                message = (
                    f"{surface.label} passt geometrisch in {profile.label}; Tkinter ist auf "
                    "dieser Zielplattform jedoch nicht nativ verfügbar."
                )
            else:
                status = "blocked"
                severity = "critical"
                message = (
                    f"{surface.label} passt nicht in {profile.label} und Tkinter ist dort "
                    "nicht nativ verfügbar."
                )
            findings.append(
                Finding(
                    check="profile_support",
                    status=status,
                    severity=severity,
                    message=message,
                    profile=profile.key,
                    surface=surface.key,
                    details=details,
                )
            )
    return findings


def evaluate_runtime_probe(
    records: Iterable[Mapping[str, Any]],
    *,
    minimum_touch_target: int = 44,
) -> list[Finding]:
    _require_positive_int(minimum_touch_target, "minimum_touch_target")
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for record in records:
        if not isinstance(record, Mapping):
            raise UiAcceptanceError("Runtime-Datensatz ist ungültig.")
        profile = str(record.get("profile", "")).strip()
        surface = str(record.get("surface", "")).strip()
        if not profile or not surface:
            raise UiAcceptanceError("Runtime-Datensatz enthält kein Profil oder keine Oberfläche.")
        key = (profile, surface)
        if key in seen:
            raise UiAcceptanceError(f"Runtime-Datensatz ist doppelt: {profile}/{surface}.")
        seen.add(key)

        requested = record.get("requested_size")
        actual = record.get("actual_size")
        if not (
            isinstance(requested, Sequence)
            and len(requested) == 2
            and isinstance(actual, Sequence)
            and len(actual) == 2
        ):
            raise UiAcceptanceError("Runtime-Größen sind ungültig.")
        requested_width = _require_positive_int(requested[0], "requested_width")
        requested_height = _require_positive_int(requested[1], "requested_height")
        actual_width = _require_positive_int(actual[0], "actual_width")
        actual_height = _require_positive_int(actual[1], "actual_height")
        honored = actual_width <= requested_width and actual_height <= requested_height
        findings.append(
            Finding(
                check="viewport_honored",
                status="passed" if honored else "failed",
                severity="info" if honored else "major",
                message=(
                    f"{surface}/{profile}: angefordert {requested_width}×{requested_height}, "
                    f"tatsächlich {actual_width}×{actual_height}."
                ),
                profile=profile,
                surface=surface,
                details={"requested": list(requested), "actual": list(actual)},
            )
        )

        overflow = record.get("overflow_widgets", [])
        if not isinstance(overflow, Sequence) or isinstance(overflow, (str, bytes)):
            raise UiAcceptanceError("overflow_widgets ist ungültig.")
        findings.append(
            Finding(
                check="widget_overflow",
                status="passed" if not overflow else "failed",
                severity="info" if not overflow else "major",
                message=(
                    f"{surface}/{profile}: keine sichtbaren Überläufe."
                    if not overflow
                    else f"{surface}/{profile}: {len(overflow)} Widget(s) ragen aus dem Fenster."
                ),
                profile=profile,
                surface=surface,
                details={"widgets": list(overflow)},
            )
        )

        focusable = record.get("focusable_count", 0)
        focusable_count = _require_positive_int(focusable, "focusable_count")
        findings.append(
            Finding(
                check="focus_order",
                status="passed",
                severity="info",
                message=f"{surface}/{profile}: {focusable_count} fokussierbare Elemente erkannt.",
                profile=profile,
                surface=surface,
                details={"focusable_count": focusable_count},
            )
        )

        undersized = record.get("undersized_touch_targets", [])
        if not isinstance(undersized, Sequence) or isinstance(undersized, (str, bytes)):
            raise UiAcceptanceError("undersized_touch_targets ist ungültig.")
        findings.append(
            Finding(
                check="touch_targets",
                status="passed" if not undersized else "warning",
                severity="info" if not undersized else "minor",
                message=(
                    f"{surface}/{profile}: alle gemessenen Bedienelemente erreichen "
                    f"{minimum_touch_target}px."
                    if not undersized
                    else f"{surface}/{profile}: {len(undersized)} Touch-Ziel(e) sind kleiner "
                    f"als {minimum_touch_target}px."
                ),
                profile=profile,
                surface=surface,
                details={"widgets": list(undersized), "minimum": minimum_touch_target},
            )
        )
    return findings


def summarize(findings: Sequence[Finding]) -> dict[str, Any]:
    counts = {status: 0 for status in sorted(VALID_STATUSES)}
    severity_counts = {severity: 0 for severity in sorted(VALID_SEVERITIES)}
    for finding in findings:
        if not isinstance(finding, Finding):
            raise UiAcceptanceError("Finding ist ungültig.")
        if finding.status not in VALID_STATUSES:
            raise UiAcceptanceError(f"Unbekannter Status: {finding.status}")
        if finding.severity not in VALID_SEVERITIES:
            raise UiAcceptanceError(f"Unbekannte Schwere: {finding.severity}")
        counts[finding.status] += 1
        severity_counts[finding.severity] += 1
    automated_blockers = [
        finding
        for finding in findings
        if finding.status == "failed" and finding.severity in {"major", "critical"}
    ]
    physical_pending = [
        finding
        for finding in findings
        if finding.status in {"simulated", "blocked", "pending"}
    ]
    return {
        "counts": counts,
        "severities": severity_counts,
        "automated_passed": not automated_blockers,
        "physical_complete": not physical_pending,
        "automated_blockers": [finding.to_dict() for finding in automated_blockers],
        "physical_pending": [finding.to_dict() for finding in physical_pending],
    }

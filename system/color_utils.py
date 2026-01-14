"""Hilfsfunktionen für Farb- und Kontrastberechnungen."""

from __future__ import annotations

from typing import Tuple


def parse_hex_color(value: str) -> Tuple[int, int, int]:
    """Parst eine Hex-Farbe (#rgb oder #rrggbb) in RGB-Werte."""
    if not isinstance(value, str):
        raise ValueError("Farbwert ist kein Text.")
    text = value.strip().lower()
    if not text.startswith("#"):
        raise ValueError("Farbwert fehlt das #-Prefix.")
    text = text[1:]
    if len(text) == 3:
        text = "".join([c * 2 for c in text])
    if len(text) != 6:
        raise ValueError("Farbwert hat falsche Länge.")
    return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))


def _relative_luminance_component(channel: int) -> float:
    normalized = channel / 255.0
    return normalized / 12.92 if normalized <= 0.03928 else ((normalized + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """Berechnet die relative Helligkeit einer RGB-Farbe."""
    r, g, b = rgb
    return (
        0.2126 * _relative_luminance_component(r)
        + 0.7152 * _relative_luminance_component(g)
        + 0.0722 * _relative_luminance_component(b)
    )


def contrast_ratio(color_a: str, color_b: str) -> float:
    """Berechnet den Kontrast zwischen zwei Hex-Farben."""
    lum_a = relative_luminance(parse_hex_color(color_a))
    lum_b = relative_luminance(parse_hex_color(color_b))
    high = max(lum_a, lum_b)
    low = min(lum_a, lum_b)
    return (high + 0.05) / (low + 0.05)

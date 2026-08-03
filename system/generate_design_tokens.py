#!/usr/bin/env python3
"""Generate and verify derived design-token artifacts."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from pprint import pformat
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "config" / "design-tokens.json"
GENERATED = ROOT / "generated"
DOCS = ROOT / "docs"
REM_BASE_PX = Decimal("16")
REQUIRED_GROUPS = {
    "$schemaVersion",
    "meta",
    "themes",
    "spacing",
    "radius",
    "typography",
    "shadow",
    "motion",
    "zIndex",
    "breakpoint",
    "layout",
}
REQUIRED_THEME_COLORS = {
    "background",
    "surface",
    "surfaceElevated",
    "text",
    "textMuted",
    "border",
    "accent",
    "accentText",
    "success",
    "warning",
    "danger",
    "info",
}


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{label} muss ein nichtleeres Objekt sein")
    return value


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} muss nichtleerer Text sein")
    return value.strip()


def _require_positive_number(value: Any, label: str) -> int | float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{label} muss eine positive Zahl sein")
    return value


def _require_nonnegative_number(value: Any, label: str) -> int | float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} muss eine nichtnegative Zahl sein")
    return value


def load_tokens() -> dict[str, Any]:
    try:
        with SOURCE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise ValueError(f"Token-Quelle fehlt: {SOURCE.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Ungültiges JSON in {SOURCE.relative_to(ROOT)}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Die Token-Quelle muss ein JSON-Objekt sein")

    missing = sorted(REQUIRED_GROUPS.difference(data))
    if missing:
        raise ValueError(f"Fehlende Token-Gruppen: {', '.join(missing)}")

    meta = _require_mapping(data["meta"], "meta")
    themes = _require_mapping(data["themes"], "themes")
    default_theme = meta.get("defaultTheme")
    if not isinstance(default_theme, str) or default_theme not in themes:
        raise ValueError("meta.defaultTheme verweist auf kein vorhandenes Theme")

    for group in REQUIRED_GROUPS - {"$schemaVersion", "meta", "themes"}:
        _require_mapping(data[group], group)

    for theme_name, theme in themes.items():
        theme_data = _require_mapping(theme, f"themes.{theme_name}")
        colors = _require_mapping(theme_data.get("color"), f"themes.{theme_name}.color")
        missing_colors = sorted(REQUIRED_THEME_COLORS.difference(colors))
        if missing_colors:
            raise ValueError(
                f"Theme {theme_name} enthält nicht alle Pflichtfarben: "
                + ", ".join(missing_colors)
            )
        for color_name, color_value in colors.items():
            _require_text(color_value, f"themes.{theme_name}.color.{color_name}")

    return data


def flatten(prefix: str, value: Any, output: dict[str, Any]) -> None:
    if isinstance(value, dict):
        for key in sorted(value):
            next_prefix = f"{prefix}-{key}" if prefix else key
            flatten(next_prefix, value[key], output)
    else:
        output[prefix] = value


def css_name(name: str) -> str:
    result: list[str] = []
    for char in name:
        if char.isupper():
            result.extend(("-", char.lower()))
        else:
            result.append(char)
    return "".join(result).replace("_", "-")


def build_css(tokens: dict[str, Any]) -> str:
    lines = ["/* AUTO-GENERATED. DO NOT EDIT. Source: config/design-tokens.json */"]
    default_theme = tokens["meta"]["defaultTheme"]
    shared = {
        key: value
        for key, value in tokens.items()
        if key not in {"meta", "themes", "$schemaVersion"}
    }
    flat_shared: dict[str, Any] = {}
    flatten("", shared, flat_shared)
    flat_default: dict[str, Any] = {}
    flatten("color", tokens["themes"][default_theme]["color"], flat_default)
    lines.append(":root {")
    for key, value in sorted({**flat_shared, **flat_default}.items()):
        lines.append(f"  --pw-{css_name(key)}: {value};")
    lines.append("}")
    for theme_name, theme in sorted(tokens["themes"].items()):
        flat_theme: dict[str, Any] = {}
        flatten("color", theme["color"], flat_theme)
        lines.append(f'\n[data-theme="{theme_name}"] {{')
        for key, value in sorted(flat_theme.items()):
            lines.append(f"  --pw-{css_name(key)}: {value};")
        lines.append("}")
    return "\n".join(lines) + "\n"


def build_webmanifest(tokens: dict[str, Any]) -> dict[str, Any]:
    default = tokens["themes"][tokens["meta"]["defaultTheme"]]["color"]
    return {
        "generated": True,
        "theme_name": tokens["meta"]["defaultTheme"],
        "theme_color": default["accent"],
        "background_color": default["background"],
    }


def build_module_manifest(tokens: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated": True,
        "design_tokens_version": tokens["$schemaVersion"],
        "default_theme": tokens["meta"]["defaultTheme"],
        "available_themes": sorted(tokens["themes"]),
        "breakpoints": tokens["breakpoint"],
        "layout": tokens["layout"],
    }


def _parse_decimal_quantity(value: Any, *, units: tuple[str, ...], label: str) -> tuple[Decimal, str]:
    text = _require_text(value, label).lower()
    if text == "0":
        return Decimal(0), ""
    unit = next((candidate for candidate in units if text.endswith(candidate)), None)
    if unit is None:
        raise ValueError(f"{label} verwendet eine nicht unterstützte Einheit: {value}")
    number_text = text[: -len(unit)].strip()
    if not number_text:
        raise ValueError(f"{label} enthält keinen Zahlenwert")
    try:
        number = Decimal(number_text)
    except InvalidOperation as exc:
        raise ValueError(f"{label} enthält keinen gültigen Zahlenwert: {value}") from exc
    if number < 0:
        raise ValueError(f"{label} darf nicht negativ sein")
    return number, unit


def _to_pixel_value(value: Any, label: str) -> int:
    number, unit = _parse_decimal_quantity(value, units=("rem", "px"), label=label)
    pixels = number * REM_BASE_PX if unit == "rem" else number
    if pixels != pixels.to_integral_value():
        raise ValueError(f"{label} ergibt keine ganzzahlige Pixelgröße: {value}")
    return int(pixels)


def _to_milliseconds(value: Any, label: str) -> int:
    try:
        number, _unit = _parse_decimal_quantity(value, units=("ms",), label=label)
    except ValueError as exc:
        raise ValueError(f"{label} muss in Millisekunden angegeben sein: {value}") from exc
    if number != number.to_integral_value():
        raise ValueError(f"{label} ergibt keine ganzzahligen Millisekunden: {value}")
    return int(number)


def _sorted_text_mapping(value: Any, label: str) -> dict[str, str]:
    mapping = _require_mapping(value, label)
    return {
        str(key): _require_text(item, f"{label}.{key}")
        for key, item in sorted(mapping.items())
    }


def _sorted_positive_number_mapping(value: Any, label: str) -> dict[str, int | float]:
    mapping = _require_mapping(value, label)
    return {
        str(key): _require_positive_number(item, f"{label}.{key}")
        for key, item in sorted(mapping.items())
    }


def _sorted_nonnegative_number_mapping(value: Any, label: str) -> dict[str, int | float]:
    mapping = _require_mapping(value, label)
    return {
        str(key): _require_nonnegative_number(item, f"{label}.{key}")
        for key, item in sorted(mapping.items())
    }


def build_python_runtime_data(tokens: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(tokens, dict):
        raise ValueError("tokens muss ein Objekt sein")
    meta = _require_mapping(tokens.get("meta"), "meta")
    themes = _require_mapping(tokens.get("themes"), "themes")
    typography = _require_mapping(tokens.get("typography"), "typography")

    theme_colors: dict[str, dict[str, str]] = {}
    for theme_name, theme in sorted(themes.items()):
        theme_data = _require_mapping(theme, f"themes.{theme_name}")
        colors = _require_mapping(theme_data.get("color"), f"themes.{theme_name}.color")
        theme_colors[str(theme_name)] = {
            str(color_name): _require_text(
                color_value,
                f"themes.{theme_name}.color.{color_name}",
            )
            for color_name, color_value in sorted(colors.items())
        }

    spacing = _require_mapping(tokens.get("spacing"), "spacing")
    radius = _require_mapping(tokens.get("radius"), "radius")
    font_sizes = _require_mapping(typography.get("fontSize"), "typography.fontSize")
    motion = _require_mapping(tokens.get("motion"), "motion")
    breakpoints = _require_mapping(tokens.get("breakpoint"), "breakpoint")
    layout = _require_mapping(tokens.get("layout"), "layout")

    return {
        "schema_version": tokens.get("$schemaVersion"),
        "meta": {
            "name": _require_text(meta.get("name"), "meta.name"),
            "description": _require_text(meta.get("description"), "meta.description"),
            "default_theme": _require_text(meta.get("defaultTheme"), "meta.defaultTheme"),
        },
        "themes": theme_colors,
        "spacing_px": {
            str(key): _to_pixel_value(value, f"spacing.{key}")
            for key, value in sorted(spacing.items())
        },
        "radius_px": {
            str(key): _to_pixel_value(value, f"radius.{key}")
            for key, value in sorted(radius.items())
        },
        "font_family": _sorted_text_mapping(
            typography.get("fontFamily"),
            "typography.fontFamily",
        ),
        "font_size_px": {
            str(key): _to_pixel_value(value, f"typography.fontSize.{key}")
            for key, value in sorted(font_sizes.items())
        },
        "font_weight": _sorted_positive_number_mapping(
            typography.get("fontWeight"),
            "typography.fontWeight",
        ),
        "line_height": _sorted_positive_number_mapping(
            typography.get("lineHeight"),
            "typography.lineHeight",
        ),
        "shadow": _sorted_text_mapping(tokens.get("shadow"), "shadow"),
        "motion_ms": {
            str(key): _to_milliseconds(value, f"motion.{key}")
            for key, value in sorted(motion.items())
        },
        "z_index": _sorted_nonnegative_number_mapping(tokens.get("zIndex"), "zIndex"),
        "breakpoint_px": {
            str(key): _to_pixel_value(value, f"breakpoint.{key}")
            for key, value in sorted(breakpoints.items())
        },
        "layout_px": {
            str(key): _to_pixel_value(value, f"layout.{key}")
            for key, value in sorted(layout.items())
        },
    }


def build_python_runtime(tokens: dict[str, Any]) -> str:
    runtime = build_python_runtime_data(tokens)
    payload = pformat(runtime, width=100, sort_dicts=True)
    return f'''# AUTO-GENERATED. DO NOT EDIT. Source: config/design-tokens.json
from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({{key: _freeze(item) for key, item in value.items()}})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


_DATA = {payload}
TOKENS = _freeze(_DATA)
del _DATA

SCHEMA_VERSION = TOKENS["schema_version"]
META = TOKENS["meta"]
DEFAULT_THEME = META["default_theme"]
THEMES = TOKENS["themes"]
SPACING_PX = TOKENS["spacing_px"]
RADIUS_PX = TOKENS["radius_px"]
FONT_FAMILY = TOKENS["font_family"]
FONT_SIZE_PX = TOKENS["font_size_px"]
FONT_WEIGHT = TOKENS["font_weight"]
LINE_HEIGHT = TOKENS["line_height"]
SHADOW = TOKENS["shadow"]
MOTION_MS = TOKENS["motion_ms"]
Z_INDEX = TOKENS["z_index"]
BREAKPOINT_PX = TOKENS["breakpoint_px"]
LAYOUT_PX = TOKENS["layout_px"]


def theme_names() -> tuple[str, ...]:
    return tuple(THEMES.keys())


def get_theme(name: str | None = None) -> Mapping[str, str]:
    if name is None:
        selected = DEFAULT_THEME
    elif not isinstance(name, str):
        raise TypeError("name muss Text oder None sein")
    else:
        selected = name.strip() or DEFAULT_THEME
    if selected not in THEMES:
        raise KeyError(f"Unbekanntes Design-Token-Theme: {{selected}}")
    return THEMES[selected]


__all__ = [
    "SCHEMA_VERSION",
    "META",
    "DEFAULT_THEME",
    "THEMES",
    "SPACING_PX",
    "RADIUS_PX",
    "FONT_FAMILY",
    "FONT_SIZE_PX",
    "FONT_WEIGHT",
    "LINE_HEIGHT",
    "SHADOW",
    "MOTION_MS",
    "Z_INDEX",
    "BREAKPOINT_PX",
    "LAYOUT_PX",
    "TOKENS",
    "theme_names",
    "get_theme",
]
'''


def build_docs(tokens: dict[str, Any]) -> str:
    lines = [
        "<!-- AUTO-GENERATED. DO NOT EDIT. Source: config/design-tokens.json -->",
        "# Design-Tokens",
        "",
        f"Standard-Theme: `{tokens['meta']['defaultTheme']}`",
        "",
        "## Themes",
    ]
    for theme_name, theme in sorted(tokens["themes"].items()):
        lines.extend(("", f"### {theme_name}", "", "| Token | Wert |", "| --- | --- |"))
        for key, value in sorted(theme["color"].items()):
            lines.append(f"| `color.{key}` | `{value}` |")
    for group in ("spacing", "radius", "breakpoint", "layout"):
        lines.extend(("", f"## {group}", "", "| Token | Wert |", "| --- | --- |"))
        for key, value in sorted(tokens[group].items()):
            lines.append(f"| `{group}.{key}` | `{value}` |")
    return "\n".join(lines) + "\n"


def expected_outputs(tokens: dict[str, Any]) -> dict[Path, str]:
    return {
        GENERATED / "design-tokens.css": build_css(tokens),
        GENERATED / "design-tokens-webmanifest.json": json.dumps(
            build_webmanifest(tokens), indent=2, ensure_ascii=False
        ) + "\n",
        GENERATED / "design-tokens-module-manifest.json": json.dumps(
            build_module_manifest(tokens), indent=2, ensure_ascii=False
        ) + "\n",
        GENERATED / "design_tokens.py": build_python_runtime(tokens),
        DOCS / "DESIGN_TOKENS.generated.md": build_docs(tokens),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Nur prüfen, ob alle Ausgaben aktuell sind",
    )
    args = parser.parse_args()
    try:
        tokens = load_tokens()
        outputs = expected_outputs(tokens)
    except ValueError as exc:
        print(f"Design-Token-Fehler: {exc}")
        return 2

    stale: list[str] = []
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path.relative_to(ROOT).as_posix())
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")

    if stale:
        print("Veraltete oder fehlende Design-Token-Ausgaben:")
        for path in stale:
            print(f"- {path}")
        return 1

    print(
        "Design-Token-Ausgaben sind aktuell."
        if args.check
        else "Design-Token-Ausgaben wurden erzeugt."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

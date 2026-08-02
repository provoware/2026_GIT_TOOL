#!/usr/bin/env python3
"""Generate and verify derived design-token artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "config" / "design-tokens.json"
GENERATED = ROOT / "generated"
DOCS = ROOT / "docs"
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
    except ValueError as exc:
        print(f"Design-Token-Fehler: {exc}")
        return 2

    outputs = expected_outputs(tokens)
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

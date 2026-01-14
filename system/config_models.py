from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


class ConfigModelError(ValueError):
    pass


@dataclass(frozen=True)
class ModuleEntryModel:
    module_id: str
    name: str
    path: str
    enabled: bool
    description: str


@dataclass(frozen=True)
class ModulesConfigModel:
    modules: List[ModuleEntryModel]


@dataclass(frozen=True)
class ThemeConfig:
    name: str
    label: str
    colors: Dict[str, str]


@dataclass(frozen=True)
class GuiTextSpacingConfig:
    before: int
    line: int
    after: int


@dataclass(frozen=True)
class GuiLayoutConfig:
    gap_xs: int
    gap_sm: int
    gap_md: int
    gap_lg: int
    gap_xl: int
    button_padx: int
    button_pady: int
    field_padx: int
    field_pady: int
    text_spacing: GuiTextSpacingConfig
    focus_thickness: int


@dataclass(frozen=True)
class GuiConfigModel:
    default_theme: str
    themes: Dict[str, ThemeConfig]
    refresh_debounce_ms: int
    layout: GuiLayoutConfig


def load_modules_config(path: Path) -> ModulesConfigModel:
    data = _load_json(path)
    modules = _require_list(data.get("modules"), "modules")
    if not modules:
        raise ConfigModelError("modules darf nicht leer sein.")
    entries: List[ModuleEntryModel] = []
    seen_ids = set()
    for index, entry in enumerate(modules, start=1):
        entry_obj = _require_dict(entry, f"modules[{index}]")
        module_id = _require_module_id(entry_obj.get("id"), f"modules[{index}].id")
        if module_id in seen_ids:
            raise ConfigModelError(f"Module-ID doppelt vorhanden: {module_id}")
        seen_ids.add(module_id)
        module_path = _require_module_path(
            entry_obj.get("path"), module_id, f"modules[{index}].path"
        )
        entries.append(
            ModuleEntryModel(
                module_id=module_id,
                name=_require_text(entry_obj.get("name"), f"modules[{index}].name"),
                path=module_path,
                enabled=_require_bool(entry_obj.get("enabled"), f"modules[{index}].enabled"),
                description=_require_text(
                    entry_obj.get("description"), f"modules[{index}].description"
                ),
            )
        )
    return ModulesConfigModel(modules=entries)


def load_gui_config(path: Path) -> GuiConfigModel:
    data = _load_json(path)
    default_theme = _require_text(data.get("default_theme"), "default_theme")
    themes_raw = _require_dict(data.get("themes"), "themes")
    if not themes_raw:
        raise ConfigModelError("themes fehlen oder sind leer.")
    themes: Dict[str, ThemeConfig] = {}
    for name, entry in themes_raw.items():
        theme_name = _require_text(name, "theme_name")
        entry_obj = _require_dict(entry, f"themes.{theme_name}")
        label = _require_text(entry_obj.get("label"), f"themes.{theme_name}.label")
        colors = _require_dict(entry_obj.get("colors"), f"themes.{theme_name}.colors")
        _validate_colors(colors, theme_name)
        themes[theme_name] = ThemeConfig(name=theme_name, label=label, colors=colors)
    if default_theme not in themes:
        raise ConfigModelError("default_theme ist nicht in themes enthalten.")
    refresh_debounce_ms = _require_int(data.get("refresh_debounce_ms", 200), "refresh_debounce_ms")
    if refresh_debounce_ms < 50:
        raise ConfigModelError("refresh_debounce_ms ist zu klein (min. 50).")
    layout = _load_gui_layout(data)
    return GuiConfigModel(
        default_theme=default_theme,
        themes=themes,
        refresh_debounce_ms=refresh_debounce_ms,
        layout=layout,
    )


def _load_gui_layout(data: dict) -> GuiLayoutConfig:
    layout_raw = _require_dict(data.get("layout"), "layout")
    text_spacing = _require_dict(layout_raw.get("text_spacing"), "layout.text_spacing")
    spacing_config = GuiTextSpacingConfig(
        before=_require_int_min(text_spacing.get("before"), "layout.text_spacing.before", 0),
        line=_require_int_min(text_spacing.get("line"), "layout.text_spacing.line", 0),
        after=_require_int_min(text_spacing.get("after"), "layout.text_spacing.after", 0),
    )
    return GuiLayoutConfig(
        gap_xs=_require_int_min(layout_raw.get("gap_xs"), "layout.gap_xs", 0),
        gap_sm=_require_int_min(layout_raw.get("gap_sm"), "layout.gap_sm", 0),
        gap_md=_require_int_min(layout_raw.get("gap_md"), "layout.gap_md", 0),
        gap_lg=_require_int_min(layout_raw.get("gap_lg"), "layout.gap_lg", 0),
        gap_xl=_require_int_min(layout_raw.get("gap_xl"), "layout.gap_xl", 0),
        button_padx=_require_int_min(layout_raw.get("button_padx"), "layout.button_padx", 0),
        button_pady=_require_int_min(layout_raw.get("button_pady"), "layout.button_pady", 0),
        field_padx=_require_int_min(layout_raw.get("field_padx"), "layout.field_padx", 0),
        field_pady=_require_int_min(layout_raw.get("field_pady"), "layout.field_pady", 0),
        text_spacing=spacing_config,
        focus_thickness=_require_int_min(
            layout_raw.get("focus_thickness"), "layout.focus_thickness", 0
        ),
    )


def _load_json(path: Path) -> dict:
    if not isinstance(path, Path):
        raise ConfigModelError("path ist kein Pfad (Path).")
    if not path.exists():
        raise ConfigModelError(f"Konfiguration fehlt: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ConfigModelError(f"JSON ist ungültig: {path}") from exc
    if not isinstance(data, dict):
        raise ConfigModelError("Konfiguration ist kein Objekt (dict).")
    return data


def _validate_colors(colors: dict, theme_name: str) -> None:
    required = {
        "background",
        "foreground",
        "accent",
        "button_background",
        "button_foreground",
        "status_success",
        "status_error",
        "status_busy",
        "status_foreground",
    }
    for key in required:
        _require_hex_color(colors.get(key), f"themes.{theme_name}.colors.{key}")


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigModelError(f"{field} ist leer oder ungültig.")
    return value.strip()


def _require_module_id(value: object, field: str) -> str:
    module_id = _require_text(value, field)
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", module_id):
        raise ConfigModelError(f"{field} muss snake_case sein (z. B. modul_name_1).")
    return module_id


def _require_module_path(value: object, module_id: str, field: str) -> str:
    module_path = _require_text(value, field)
    path = Path(module_path)
    if path.is_absolute():
        raise ConfigModelError(f"{field} darf nicht absolut sein.")
    parts = path.parts
    if len(parts) != 2 or parts[0] != "modules" or parts[1] != module_id:
        raise ConfigModelError(f"{field} muss 'modules/{module_id}' entsprechen.")
    return module_path


def _require_hex_color(value: object, field: str) -> str:
    text = _require_text(value, field)
    if not text.startswith("#") or len(text) not in {4, 7}:
        raise ConfigModelError(f"{field} ist keine gültige Hex-Farbe (#fff oder #ffffff).")
    return text


def _require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigModelError(f"{field} ist kein Wahrheitswert.")
    return value


def _require_int(value: object, field: str) -> int:
    if not isinstance(value, int):
        raise ConfigModelError(f"{field} ist kein Integer.")
    return value


def _require_int_min(value: object, field: str, minimum: int) -> int:
    result = _require_int(value, field)
    if result < minimum:
        raise ConfigModelError(f"{field} ist kleiner als {minimum}.")
    return result


def _require_dict(value: object, field: str) -> dict:
    if not isinstance(value, dict):
        raise ConfigModelError(f"{field} ist kein Objekt (dict).")
    return value


def _require_list(value: object, field: str) -> list:
    if not isinstance(value, list):
        raise ConfigModelError(f"{field} ist keine Liste.")
    return value


def summarize_modules(modules: Iterable[ModuleEntryModel]) -> str:
    entries = list(modules)
    if not entries:
        return "Keine Module vorhanden."
    lines = ["Module aus Registry:"]
    for entry in entries:
        status = "aktiv" if entry.enabled else "deaktiviert"
        lines.append(f"- {entry.name} ({entry.module_id}) – {status}")
    return "\n".join(lines)

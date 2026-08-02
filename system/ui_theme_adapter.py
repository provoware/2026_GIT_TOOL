#!/usr/bin/env python3
"""Gemeinsamer Themevertrag und Tkinter-Adapter für die produktiven Fenster."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional

from config_models import GuiConfigModel


class UiThemeError(ValueError):
    """Ungültige Theme-Konfiguration oder nicht unterstütztes Theme-Ziel."""


COMMON_COLOR_KEYS = {
    "background",
    "foreground",
    "accent",
    "button_background",
    "button_foreground",
}
STATUS_COLOR_KEYS = {
    "status_success",
    "status_error",
    "status_busy",
    "status_foreground",
}


@dataclass(frozen=True)
class ResolvedTheme:
    name: str
    label: str
    colors: Mapping[str, str]


def resolve_theme(
    gui_config: GuiConfigModel,
    theme_name: Optional[str] = None,
    *,
    strict: bool = False,
) -> ResolvedTheme:
    if not isinstance(gui_config, GuiConfigModel):
        raise UiThemeError("gui_config ist ungültig.")
    if theme_name is not None and not isinstance(theme_name, str):
        raise UiThemeError("theme_name muss Text oder None sein.")

    requested = theme_name.strip() if isinstance(theme_name, str) else ""
    requested = requested or gui_config.default_theme
    if requested not in gui_config.themes:
        if strict:
            raise UiThemeError(f"Unbekanntes Farbschema: {requested}")
        requested = gui_config.default_theme

    theme = gui_config.themes[requested]
    colors = _validated_colors(theme.colors, COMMON_COLOR_KEYS | STATUS_COLOR_KEYS)
    return ResolvedTheme(
        name=requested,
        label=theme.label,
        colors=MappingProxyType(dict(colors)),
    )


def resolve_contrast_theme(gui_config: GuiConfigModel) -> Optional[str]:
    if not isinstance(gui_config, GuiConfigModel):
        raise UiThemeError("gui_config ist ungültig.")
    if "kontrast" in gui_config.themes:
        return "kontrast"
    for name, theme in gui_config.themes.items():
        if "kontrast" in theme.label.lower():
            return name
    return None


def build_status_palette(theme_or_colors) -> dict[str, str]:
    colors = _coerce_colors(theme_or_colors, STATUS_COLOR_KEYS)
    return {
        "success": colors["status_success"],
        "error": colors["status_error"],
        "busy": colors["status_busy"],
        "foreground": colors["status_foreground"],
    }


def build_tooltip_style(theme_or_colors) -> dict[str, str]:
    colors = _coerce_colors(theme_or_colors, COMMON_COLOR_KEYS)
    return {
        "bg": colors["button_background"],
        "fg": colors["button_foreground"],
        "border": colors["accent"],
    }


def apply_theme_tree(root, theme_or_colors, *, button_font=None) -> None:
    if root is None or not hasattr(root, "configure"):
        raise UiThemeError("Theme-Wurzel ist ungültig.")
    colors = _coerce_colors(theme_or_colors, COMMON_COLOR_KEYS)
    root.configure(background=colors["background"])
    for child in _children(root):
        apply_widget_style(child, colors, button_font=button_font)


def apply_widget_style(widget, theme_or_colors, *, button_font=None) -> None:
    if widget is None or not hasattr(widget, "configure"):
        raise UiThemeError("Widget ist ungültig.")
    colors = _coerce_colors(theme_or_colors, COMMON_COLOR_KEYS)
    widget_type = _widget_class(widget)

    if widget_type == "Frame":
        widget.configure(background=colors["background"])
    elif widget_type == "Label":
        widget.configure(
            background=colors["background"],
            foreground=colors["foreground"],
        )
    elif widget_type == "Labelframe":
        widget.configure(
            background=colors["background"],
            foreground=colors["foreground"],
            highlightbackground=colors["accent"],
            highlightcolor=colors["accent"],
        )
    elif widget_type in {"Checkbutton", "Button", "Menubutton", "OptionMenu"}:
        widget.configure(
            background=colors["button_background"],
            foreground=colors["button_foreground"],
            activebackground=colors["accent"],
            activeforeground=colors["button_foreground"],
            highlightbackground=colors["accent"],
            highlightcolor=colors["accent"],
            highlightthickness=2,
        )
        if button_font is not None:
            widget.configure(font=button_font)
        _apply_menu_style(widget, colors, button_font)
    elif widget_type == "Text":
        widget.configure(
            background=colors["background"],
            foreground=colors["foreground"],
            insertbackground=colors["foreground"],
            highlightbackground=colors["accent"],
            highlightcolor=colors["accent"],
        )

    for child in _children(widget):
        apply_widget_style(child, colors, button_font=button_font)


def apply_module_card_theme(module_widget, theme_or_colors) -> None:
    colors = _coerce_colors(theme_or_colors, COMMON_COLOR_KEYS)
    required = (
        "frame",
        "header",
        "title_label",
        "drag_label",
        "description",
        "status_label",
        "activate_button",
        "deactivate_button",
        "resize_handle",
    )
    missing = [name for name in required if not hasattr(module_widget, name)]
    if missing:
        raise UiThemeError(f"Modulkarte unvollständig: {', '.join(missing)}")

    module_widget.frame.configure(
        background=colors["background"],
        highlightbackground=colors["accent"],
    )
    module_widget.header.configure(background=colors["background"])
    module_widget.title_label.configure(
        background=colors["background"], foreground=colors["foreground"]
    )
    module_widget.drag_label.configure(
        background=colors["background"], foreground=colors["accent"]
    )
    module_widget.description.configure(
        background=colors["background"], foreground=colors["foreground"]
    )
    module_widget.status_label.configure(
        background=colors["background"], foreground=colors["foreground"]
    )
    module_widget.activate_button.configure(
        background=colors["button_background"],
        foreground=colors["button_foreground"],
    )
    module_widget.deactivate_button.configure(
        background=colors["button_background"],
        foreground=colors["button_foreground"],
    )
    module_widget.resize_handle.configure(
        background=colors["background"], foreground=colors["accent"]
    )


def _coerce_colors(theme_or_colors, required: set[str]) -> Mapping[str, str]:
    if isinstance(theme_or_colors, ResolvedTheme):
        colors = theme_or_colors.colors
    elif isinstance(theme_or_colors, Mapping):
        colors = theme_or_colors
    else:
        raise UiThemeError("Theme-Farben sind ungültig.")
    return _validated_colors(colors, required)


def _validated_colors(colors: Mapping[str, str], required: set[str]) -> Mapping[str, str]:
    missing = sorted(required - set(colors.keys()))
    if missing:
        raise UiThemeError(f"Theme-Farben fehlen: {', '.join(missing)}")
    for key in required:
        value = colors[key]
        if not isinstance(value, str) or not value.strip():
            raise UiThemeError(f"Theme-Farbe {key} ist ungültig.")
    return colors


def _widget_class(widget) -> str:
    if not hasattr(widget, "winfo_class"):
        raise UiThemeError("Widget-Klasse ist nicht bestimmbar.")
    value = widget.winfo_class()
    if not isinstance(value, str) or not value:
        raise UiThemeError("Widget-Klasse ist ungültig.")
    return value


def _children(widget) -> list:
    if not hasattr(widget, "winfo_children"):
        return []
    children = widget.winfo_children()
    return list(children) if children is not None else []


def _apply_menu_style(widget, colors: Mapping[str, str], button_font) -> None:
    if not hasattr(widget, "__getitem__"):
        return
    try:
        menu = widget["menu"]
    except (KeyError, TypeError, AttributeError):
        return
    if menu is None or not hasattr(menu, "configure"):
        return
    menu.configure(
        background=colors["button_background"],
        foreground=colors["button_foreground"],
        activebackground=colors["accent"],
        activeforeground=colors["button_foreground"],
    )
    if button_font is not None:
        menu.configure(font=button_font)

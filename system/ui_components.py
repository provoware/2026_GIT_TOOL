#!/usr/bin/env python3
"""Tokenbasierte, kleine Tk-Komponenten- und Zustandsregeln.

Das Modul ersetzt kein GUI-Framework. Es registriert Rollen an bestehenden Tk-Widgets,
berechnet ihre Darstellung rein und wendet die Regeln idempotent an.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


class UiComponentError(ValueError):
    """Komponentenrolle, Theme oder Widget ist ungültig."""


BUTTON_ROLES = frozenset({"primary", "secondary", "neutral", "danger"})
SURFACE_ROLES = frozenset({"panel", "card", "elevated"})
STATUS_STATES = frozenset({"idle", "busy", "success", "warning", "error", "disabled"})
BUTTON_WIDGET_CLASSES = frozenset({"Button", "Checkbutton", "Menubutton", "OptionMenu"})


@dataclass(frozen=True)
class ComponentMetrics:
    gap_xs: int
    gap_sm: int
    gap_md: int
    gap_lg: int
    radius_sm: int
    radius_md: int
    focus_thickness: int
    touch_target: int
    motion_fast_ms: int


@dataclass(frozen=True)
class ComponentPalette:
    background: str
    surface: str
    elevated: str
    text: str
    muted_text: str
    border: str
    accent: str
    accent_text: str
    success: str
    warning: str
    danger: str
    info: str


@dataclass(frozen=True)
class ButtonVisualStyle:
    role: str
    normal_background: str
    normal_foreground: str
    hover_background: str
    hover_foreground: str
    active_background: str
    active_foreground: str
    disabled_background: str
    disabled_foreground: str
    border: str
    focus: str


@dataclass(frozen=True)
class SurfaceVisualStyle:
    role: str
    background: str
    foreground: str
    border: str
    relief: str
    border_width: int


@dataclass(frozen=True)
class StatusVisualStyle:
    state: str
    background: str
    foreground: str
    border: str
    symbol: str


def _load_runtime_module():
    try:
        from generated import design_tokens

        return design_tokens
    except ModuleNotFoundError:
        path = Path(__file__).resolve().parents[1] / "generated" / "design_tokens.py"
        if not path.exists():
            raise UiComponentError(f"Generierte Design-Tokens fehlen: {path}")
        spec = importlib.util.spec_from_file_location("genrearchiv_design_tokens", path)
        if spec is None or spec.loader is None:
            raise UiComponentError("Design-Token-Runtime kann nicht geladen werden.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


_RUNTIME = _load_runtime_module()


def component_metrics() -> ComponentMetrics:
    spacing = _RUNTIME.SPACING_PX
    radius = _RUNTIME.RADIUS_PX
    layout = _RUNTIME.LAYOUT_PX
    motion = _RUNTIME.MOTION_MS
    metrics = ComponentMetrics(
        gap_xs=_positive_int(spacing["1"], "spacing.1", allow_zero=False),
        gap_sm=_positive_int(spacing["2"], "spacing.2", allow_zero=False),
        gap_md=_positive_int(spacing["3"], "spacing.3", allow_zero=False),
        gap_lg=_positive_int(spacing["4"], "spacing.4", allow_zero=False),
        radius_sm=_positive_int(radius["sm"], "radius.sm", allow_zero=True),
        radius_md=_positive_int(radius["md"], "radius.md", allow_zero=True),
        focus_thickness=max(2, _positive_int(spacing["1"], "spacing.1", allow_zero=False) // 2),
        touch_target=_positive_int(layout["touchTarget"], "layout.touchTarget", allow_zero=False),
        motion_fast_ms=_positive_int(motion["fast"], "motion.fast", allow_zero=True),
    )
    return metrics


def resolve_component_palette(theme_or_colors: Any) -> ComponentPalette:
    colors = _coerce_mapping(theme_or_colors)
    background = _color(colors, "background")
    text = _color(colors, "text", "foreground")
    accent = _color(colors, "accent")
    surface = _color(colors, "surface", "button_background", default=background)
    elevated = _color(colors, "surfaceElevated", "button_background", default=surface)
    border = _color(colors, "border", "accent", default=accent)
    accent_text = _color(colors, "accentText", "button_foreground", default=contrast_text(accent))
    muted = _color(colors, "textMuted", default=mix_hex(text, background, 0.38))
    success = _color(colors, "success", "status_success", default=accent)
    warning = _color(colors, "warning", "status_busy", default=accent)
    danger = _color(colors, "danger", "status_error", default=accent)
    info = _color(colors, "info", "status_busy", default=accent)
    return ComponentPalette(
        background=background,
        surface=surface,
        elevated=elevated,
        text=text,
        muted_text=muted,
        border=border,
        accent=accent,
        accent_text=accent_text,
        success=success,
        warning=warning,
        danger=danger,
        info=info,
    )


def build_button_style(theme_or_colors: Any, role: str = "secondary") -> ButtonVisualStyle:
    clean_role = _role(role, BUTTON_ROLES, "Buttonrolle")
    palette = resolve_component_palette(theme_or_colors)
    if clean_role == "primary":
        normal_bg = palette.accent
        normal_fg = palette.accent_text
    elif clean_role == "danger":
        normal_bg = palette.danger
        normal_fg = contrast_text(palette.danger)
    elif clean_role == "neutral":
        normal_bg = palette.surface
        normal_fg = palette.text
    else:
        normal_bg = palette.elevated
        normal_fg = palette.text
    hover_bg = mix_hex(normal_bg, palette.accent, 0.20)
    active_bg = mix_hex(normal_bg, palette.background, 0.22)
    disabled_bg = mix_hex(normal_bg, palette.background, 0.58)
    disabled_fg = mix_hex(normal_fg, disabled_bg, 0.48)
    return ButtonVisualStyle(
        role=clean_role,
        normal_background=normal_bg,
        normal_foreground=normal_fg,
        hover_background=hover_bg,
        hover_foreground=contrast_text(hover_bg, preferred=normal_fg),
        active_background=active_bg,
        active_foreground=contrast_text(active_bg, preferred=normal_fg),
        disabled_background=disabled_bg,
        disabled_foreground=disabled_fg,
        border=palette.border if clean_role != "primary" else palette.accent,
        focus=palette.accent,
    )


def build_surface_style(theme_or_colors: Any, role: str = "panel") -> SurfaceVisualStyle:
    clean_role = _role(role, SURFACE_ROLES, "Flächenrolle")
    palette = resolve_component_palette(theme_or_colors)
    if clean_role == "card":
        background = palette.elevated
        relief = "raised"
    elif clean_role == "elevated":
        background = mix_hex(palette.elevated, palette.accent, 0.06)
        relief = "ridge"
    else:
        background = palette.surface
        relief = "flat"
    return SurfaceVisualStyle(
        role=clean_role,
        background=background,
        foreground=palette.text,
        border=palette.border,
        relief=relief,
        border_width=1,
    )


def build_status_style(theme_or_colors: Any, state: str) -> StatusVisualStyle:
    clean_state = _role(state, STATUS_STATES, "Statuszustand")
    palette = resolve_component_palette(theme_or_colors)
    mapping = {
        "idle": (palette.surface, palette.text, "○"),
        "busy": (palette.info, contrast_text(palette.info), "●"),
        "success": (palette.success, contrast_text(palette.success), "✓"),
        "warning": (palette.warning, contrast_text(palette.warning), "!"),
        "error": (palette.danger, contrast_text(palette.danger), "×"),
        "disabled": (
            mix_hex(palette.surface, palette.background, 0.55),
            palette.muted_text,
            "–",
        ),
    }
    background, foreground, symbol = mapping[clean_state]
    return StatusVisualStyle(
        state=clean_state,
        background=background,
        foreground=foreground,
        border=palette.border,
        symbol=symbol,
    )


def register_component(widget: Any, role: str) -> Any:
    if widget is None or not hasattr(widget, "configure"):
        raise UiComponentError("Komponenten-Widget ist ungültig.")
    clean_role = _clean_text(role, "role")
    allowed = BUTTON_ROLES | SURFACE_ROLES | {"status", "output", "drop-zone"}
    if clean_role not in allowed:
        raise UiComponentError(f"Unbekannte Komponentenrolle: {clean_role}")
    setattr(widget, "_pw_component_role", clean_role)
    return widget


def component_role(widget: Any, default: str | None = None) -> str | None:
    role = getattr(widget, "_pw_component_role", default)
    if role is None:
        return None
    return _clean_text(role, "component_role")


def configure_button(
    widget: Any,
    theme_or_colors: Any,
    *,
    role: str | None = None,
    font: Any = None,
    bind_states: bool = True,
) -> ButtonVisualStyle:
    widget_class = _widget_class(widget)
    if widget_class not in BUTTON_WIDGET_CLASSES:
        raise UiComponentError(f"Widgetklasse ist kein Button: {widget_class}")
    selected_role = role or component_role(widget, "secondary") or "secondary"
    if selected_role not in BUTTON_ROLES:
        selected_role = "neutral" if widget_class == "Checkbutton" else "secondary"
    style = build_button_style(theme_or_colors, selected_role)
    metrics = component_metrics()
    setattr(widget, "_pw_component_role", selected_role)
    setattr(widget, "_pw_button_style", style)
    options = {
        "background": style.normal_background,
        "foreground": style.normal_foreground,
        "activebackground": style.active_background,
        "activeforeground": style.active_foreground,
        "disabledforeground": style.disabled_foreground,
        "highlightbackground": style.border,
        "highlightcolor": style.focus,
        "highlightthickness": metrics.focus_thickness,
        "borderwidth": 1,
        "relief": "flat",
        "takefocus": 1,
        "padx": metrics.gap_md,
        "pady": metrics.gap_sm,
    }
    if widget_class == "Button":
        options["overrelief"] = "raised"
    if font is not None:
        options["font"] = font
    _configure(widget, **options)
    _apply_button_visual(widget, "normal")
    if bind_states:
        _bind_button_states(widget)
    return style


def configure_surface(widget: Any, theme_or_colors: Any, *, role: str | None = None) -> SurfaceVisualStyle:
    selected_role = role or component_role(widget, "panel") or "panel"
    style = build_surface_style(theme_or_colors, selected_role)
    setattr(widget, "_pw_component_role", selected_role)
    widget_class = _widget_class(widget)
    options = {
        "background": style.background,
        "highlightbackground": style.border,
        "highlightcolor": style.border,
        "highlightthickness": 1,
        "borderwidth": style.border_width,
        "relief": style.relief,
    }
    if widget_class in {"Label", "Labelframe"}:
        options["foreground"] = style.foreground
    _configure(widget, **options)
    return style


def configure_status_widget(widget: Any, theme_or_colors: Any, state: str) -> StatusVisualStyle:
    style = build_status_style(theme_or_colors, state)
    setattr(widget, "_pw_component_role", "status")
    setattr(widget, "_pw_status_state", style.state)
    _configure(
        widget,
        background=style.background,
        foreground=style.foreground,
        highlightbackground=style.border,
        highlightcolor=style.border,
        highlightthickness=1,
        borderwidth=1,
        relief="flat",
    )
    return style


def apply_registered_style(widget: Any, theme_or_colors: Any, *, font: Any = None) -> None:
    role = component_role(widget)
    widget_class = _widget_class(widget)
    if role in BUTTON_ROLES or widget_class in BUTTON_WIDGET_CLASSES:
        configure_button(widget, theme_or_colors, role=role, font=font)
        return
    if role in SURFACE_ROLES:
        configure_surface(widget, theme_or_colors, role=role)
        return
    if role == "status":
        configure_status_widget(widget, theme_or_colors, getattr(widget, "_pw_status_state", "idle"))
        return
    if role == "drop-zone":
        configure_surface(widget, theme_or_colors, role="elevated")


def apply_component_tree(root: Any, theme_or_colors: Any, *, font: Any = None) -> None:
    if root is None or not hasattr(root, "winfo_children"):
        raise UiComponentError("Komponentenwurzel ist ungültig.")
    for child in list(root.winfo_children() or []):
        apply_registered_style(child, theme_or_colors, font=font)
        if hasattr(child, "winfo_children"):
            apply_component_tree(child, theme_or_colors, font=font)


def mix_hex(first: str, second: str, ratio: float) -> str:
    if not isinstance(ratio, (int, float)) or isinstance(ratio, bool) or not 0 <= ratio <= 1:
        raise UiComponentError("Mischverhältnis muss zwischen 0 und 1 liegen.")
    a = _hex_rgb(first)
    b = _hex_rgb(second)
    mixed = tuple(round(left * (1 - ratio) + right * ratio) for left, right in zip(a, b))
    return "#" + "".join(f"{value:02x}" for value in mixed)


def contrast_text(background: str, *, preferred: str | None = None) -> str:
    bg = _hex_rgb(background)
    candidates = [preferred] if preferred is not None else []
    candidates.extend(("#ffffff", "#000000"))
    best = None
    best_ratio = -1.0
    for candidate in candidates:
        if candidate is None:
            continue
        _hex_rgb(candidate)
        ratio = _contrast_ratio(bg, _hex_rgb(candidate))
        if ratio > best_ratio:
            best = candidate.lower()
            best_ratio = ratio
    if best is None:
        raise UiComponentError("Keine Kontrastfarbe verfügbar.")
    return best


def _bind_button_states(widget: Any) -> None:
    if getattr(widget, "_pw_component_states_bound", False):
        return
    if not hasattr(widget, "bind"):
        return
    widget.bind("<Enter>", lambda _event: _apply_button_visual(widget, "hover"), add="+")
    widget.bind("<Leave>", lambda _event: _apply_button_visual(widget, "normal"), add="+")
    widget.bind("<ButtonPress-1>", lambda _event: _apply_button_visual(widget, "active"), add="+")
    widget.bind("<ButtonRelease-1>", lambda _event: _apply_button_visual(widget, "hover"), add="+")
    widget.bind("<FocusIn>", lambda _event: _apply_button_visual(widget, "focus"), add="+")
    widget.bind("<FocusOut>", lambda _event: _apply_button_visual(widget, "normal"), add="+")
    setattr(widget, "_pw_component_states_bound", True)


def _apply_button_visual(widget: Any, state: str) -> None:
    style = getattr(widget, "_pw_button_style", None)
    if not isinstance(style, ButtonVisualStyle):
        return
    if _is_disabled(widget):
        _configure(
            widget,
            background=style.disabled_background,
            foreground=style.disabled_foreground,
            relief="flat",
        )
        return
    if state == "active":
        background = style.active_background
        foreground = style.active_foreground
        relief = "sunken"
    elif state in {"hover", "focus"}:
        background = style.hover_background
        foreground = style.hover_foreground
        relief = "raised" if state == "hover" else "flat"
    else:
        background = style.normal_background
        foreground = style.normal_foreground
        relief = "flat"
    _configure(
        widget,
        background=background,
        foreground=foreground,
        relief=relief,
        highlightcolor=style.focus,
    )


def _is_disabled(widget: Any) -> bool:
    if hasattr(widget, "cget"):
        try:
            return str(widget.cget("state")) == "disabled"
        except Exception:
            return False
    return False


def _coerce_mapping(theme_or_colors: Any) -> Mapping[str, str]:
    colors = getattr(theme_or_colors, "colors", theme_or_colors)
    if not isinstance(colors, Mapping):
        raise UiComponentError("Theme-Farben müssen ein Mapping sein.")
    return MappingProxyType(dict(colors))


def _color(colors: Mapping[str, str], *keys: str, default: str | None = None) -> str:
    for key in keys:
        value = colors.get(key)
        if isinstance(value, str) and value.strip():
            _hex_rgb(value)
            return value.lower()
    if default is not None:
        _hex_rgb(default)
        return default.lower()
    raise UiComponentError(f"Theme-Farbe fehlt: {' oder '.join(keys)}")


def _hex_rgb(value: str) -> tuple[int, int, int]:
    text = _clean_text(value, "Farbe").lower()
    if len(text) == 4 and text.startswith("#"):
        text = "#" + "".join(char * 2 for char in text[1:])
    if len(text) != 7 or not text.startswith("#"):
        raise UiComponentError(f"Ungültige Hex-Farbe: {value}")
    try:
        return tuple(int(text[index : index + 2], 16) for index in (1, 3, 5))
    except ValueError as exc:
        raise UiComponentError(f"Ungültige Hex-Farbe: {value}") from exc


def _linear_channel(value: int) -> float:
    channel = value / 255.0
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def _luminance(rgb: tuple[int, int, int]) -> float:
    red, green, blue = (_linear_channel(value) for value in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast_ratio(first: tuple[int, int, int], second: tuple[int, int, int]) -> float:
    high, low = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _positive_int(value: Any, label: str, *, allow_zero: bool) -> int:
    minimum = 0 if allow_zero else 1
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise UiComponentError(f"{label} muss eine Ganzzahl ab {minimum} sein.")
    return value


def _role(value: Any, allowed: frozenset[str], label: str) -> str:
    text = _clean_text(value, label)
    if text not in allowed:
        raise UiComponentError(f"{label} ist unbekannt: {text}")
    return text


def _clean_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UiComponentError(f"{label} muss nichtleerer Text sein.")
    return value.strip()


def _widget_class(widget: Any) -> str:
    if widget is None or not hasattr(widget, "configure") or not hasattr(widget, "winfo_class"):
        raise UiComponentError("Widget ist ungültig.")
    value = widget.winfo_class()
    return _clean_text(value, "Widgetklasse")


def _configure(widget: Any, **options: Any) -> None:
    try:
        widget.configure(**options)
    except Exception as exc:
        raise UiComponentError(f"Widget konnte nicht konfiguriert werden: {exc}") from exc


__all__ = [
    "BUTTON_ROLES",
    "STATUS_STATES",
    "ButtonVisualStyle",
    "ComponentMetrics",
    "ComponentPalette",
    "StatusVisualStyle",
    "SurfaceVisualStyle",
    "UiComponentError",
    "apply_component_tree",
    "apply_registered_style",
    "build_button_style",
    "build_status_style",
    "build_surface_style",
    "component_metrics",
    "component_role",
    "configure_button",
    "configure_status_widget",
    "configure_surface",
    "contrast_text",
    "mix_hex",
    "register_component",
    "resolve_component_palette",
]

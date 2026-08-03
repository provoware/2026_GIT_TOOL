# AUTO-GENERATED. DO NOT EDIT. Source: config/design-tokens.json
from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


_DATA = {'breakpoint_px': {'desktop': 1200, 'phone': 430, 'tablet': 768},
 'font_family': {'mono': "'JetBrains Mono', 'Fira Code', monospace",
                 'sans': "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', "
                         'sans-serif'},
 'font_size_px': {'2xl': 32, 'lg': 20, 'md': 16, 'sm': 14, 'xl': 24, 'xs': 12},
 'font_weight': {'bold': 700, 'medium': 500, 'normal': 400},
 'layout_px': {'contentMax': 1440,
               'headerHeight': 64,
               'sidebarWidth': 272,
               'tileMin': 208,
               'touchTarget': 44},
 'line_height': {'normal': 1.5, 'tight': 1.2},
 'meta': {'default_theme': 'acid-paper',
          'description': 'Single source of truth for UI colors, typography, spacing and responsive '
                         'dimensions.',
          'name': 'Provoware Design Tokens'},
 'motion_ms': {'fast': 120, 'normal': 200, 'slow': 320},
 'radius_px': {'lg': 12, 'md': 8, 'pill': 999, 'sm': 4},
 'schema_version': 1,
 'shadow': {'md': '0 6px 18px rgba(0,0,0,.22)', 'sm': '0 1px 2px rgba(0,0,0,.18)'},
 'spacing_px': {'0': 0, '1': 4, '2': 8, '3': 12, '4': 16, '5': 24, '6': 32, '7': 48},
 'themes': {'acid-paper': {'accent': '#C7FF00',
                           'accentText': '#101500',
                           'background': '#F2E8C9',
                           'border': '#2A261D',
                           'danger': '#B42318',
                           'info': '#1261A0',
                           'success': '#2B8A3E',
                           'surface': '#FFF8DE',
                           'surfaceElevated': '#FFFDF3',
                           'text': '#17150F',
                           'textMuted': '#5C5648',
                           'warning': '#C56A00'},
            'neon-scrap': {'accent': '#D8FF00',
                           'accentText': '#111500',
                           'background': '#0F1115',
                           'border': '#5B6472',
                           'danger': '#FF4D5E',
                           'info': '#36A3FF',
                           'success': '#46D369',
                           'surface': '#171A21',
                           'surfaceElevated': '#20242D',
                           'text': '#F5F7FA',
                           'textMuted': '#B5BDC9',
                           'warning': '#FFB020'}},
 'z_index': {'base': 0, 'dialog': 1000, 'header': 100, 'sidebar': 200, 'toast': 1100}}
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
        raise KeyError(f"Unbekanntes Design-Token-Theme: {selected}")
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

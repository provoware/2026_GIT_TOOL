from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SYSTEM_DIR = Path(__file__).resolve().parents[1] / "system"
if str(SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(SYSTEM_DIR))

from ui_components import (  # noqa: E402
    UiComponentError,
    apply_component_tree,
    build_button_style,
    build_status_style,
    build_surface_style,
    component_metrics,
    configure_button,
    configure_status_widget,
    contrast_text,
    mix_hex,
    register_component,
    resolve_component_palette,
)


LEGACY_COLORS = {
    "background": "#101820",
    "foreground": "#f7f9fb",
    "accent": "#d8ff00",
    "button_background": "#26313d",
    "button_foreground": "#ffffff",
    "status_success": "#2b8a3e",
    "status_error": "#b42318",
    "status_busy": "#1261a0",
    "status_foreground": "#ffffff",
}


class FakeWidget:
    def __init__(self, widget_class="Frame", children=None, state="normal"):
        self.widget_class = widget_class
        self.children = list(children or [])
        self.options = {"state": state}
        self.bindings: dict[str, list] = {}

    def configure(self, **options):
        self.options.update(options)

    def cget(self, key):
        return self.options.get(key, "")

    def winfo_class(self):
        return self.widget_class

    def winfo_children(self):
        return list(self.children)

    def bind(self, sequence, callback, add=None):
        assert add == "+"
        self.bindings.setdefault(sequence, []).append(callback)

    def emit(self, sequence):
        for callback in self.bindings.get(sequence, []):
            callback(SimpleNamespace(widget=self))


def test_metrics_are_loaded_from_generated_runtime():
    metrics = component_metrics()

    assert metrics.gap_xs == 4
    assert metrics.gap_sm == 8
    assert metrics.gap_md == 12
    assert metrics.radius_md == 8
    assert metrics.touch_target == 44
    assert metrics.motion_fast_ms == 120
    assert metrics.focus_thickness >= 2


def test_legacy_theme_is_mapped_to_semantic_palette():
    palette = resolve_component_palette(LEGACY_COLORS)

    assert palette.background == "#101820"
    assert palette.surface == "#26313d"
    assert palette.elevated == "#26313d"
    assert palette.text == "#f7f9fb"
    assert palette.success == "#2b8a3e"
    assert palette.danger == "#b42318"


def test_color_mixing_and_contrast_are_deterministic():
    assert mix_hex("#000000", "#ffffff", 0.5) == "#808080"
    assert contrast_text("#000000") == "#ffffff"
    assert contrast_text("#ffffff") == "#000000"

    with pytest.raises(UiComponentError):
        mix_hex("#000000", "#ffffff", 1.1)
    with pytest.raises(UiComponentError):
        contrast_text("not-a-color")


def test_button_roles_produce_distinct_visual_contracts():
    primary = build_button_style(LEGACY_COLORS, "primary")
    secondary = build_button_style(LEGACY_COLORS, "secondary")
    danger = build_button_style(LEGACY_COLORS, "danger")

    assert primary.normal_background == "#d8ff00"
    assert secondary.normal_background == "#26313d"
    assert danger.normal_background == "#b42318"
    assert primary.hover_background != primary.normal_background
    assert danger.disabled_background != danger.normal_background
    assert primary.focus == "#d8ff00"


def test_surface_and_status_contracts_do_not_depend_on_widget_runtime():
    panel = build_surface_style(LEGACY_COLORS, "panel")
    card = build_surface_style(LEGACY_COLORS, "card")
    success = build_status_style(LEGACY_COLORS, "success")
    warning = build_status_style(LEGACY_COLORS, "warning")

    assert panel.role == "panel"
    assert panel.relief == "flat"
    assert card.relief == "raised"
    assert success.symbol == "✓"
    assert warning.symbol == "!"
    assert success.background == "#2b8a3e"


def test_button_registration_applies_metrics_and_binds_states_once():
    button = FakeWidget("Button")
    register_component(button, "primary")

    first = configure_button(button, LEGACY_COLORS, font="ButtonFont")
    second = configure_button(button, LEGACY_COLORS, font="ButtonFont")

    assert first == second
    assert button.options["padx"] == component_metrics().gap_md
    assert button.options["pady"] == component_metrics().gap_sm
    assert button.options["takefocus"] == 1
    assert button.options["font"] == "ButtonFont"
    assert len(button.bindings["<Enter>"]) == 1
    assert len(button.bindings["<FocusIn>"]) == 1

    button.emit("<Enter>")
    assert button.options["background"] == first.hover_background
    assert button.options["relief"] == "raised"
    button.emit("<ButtonPress-1>")
    assert button.options["background"] == first.active_background
    assert button.options["relief"] == "sunken"
    button.emit("<Leave>")
    assert button.options["background"] == first.normal_background


def test_disabled_button_never_switches_to_hover_or_active_palette():
    button = FakeWidget("Button", state="disabled")
    style = configure_button(button, LEGACY_COLORS, role="danger")

    button.emit("<Enter>")
    button.emit("<ButtonPress-1>")

    assert button.options["background"] == style.disabled_background
    assert button.options["foreground"] == style.disabled_foreground
    assert button.options["relief"] == "flat"


def test_component_tree_styles_registered_surfaces_buttons_and_status():
    button = FakeWidget("Button")
    panel = FakeWidget("Labelframe", children=[button])
    indicator = FakeWidget("Label")
    root = FakeWidget("Tk", children=[panel, indicator])
    register_component(panel, "panel")
    register_component(button, "primary")
    register_component(indicator, "status")
    setattr(indicator, "_pw_status_state", "busy")

    apply_component_tree(root, LEGACY_COLORS, font="ButtonFont")

    assert panel.options["background"] == "#26313d"
    assert button.options["background"] == "#d8ff00"
    assert button.options["font"] == "ButtonFont"
    assert indicator.options["background"] == "#1261a0"


def test_status_widget_preserves_domain_text_and_only_changes_visuals():
    label = FakeWidget("Label")
    label.options["text"] = "Status: Prüfe Module"

    style = configure_status_widget(label, LEGACY_COLORS, "busy")

    assert label.options["text"] == "Status: Prüfe Module"
    assert label.options["background"] == style.background
    assert getattr(label, "_pw_status_state") == "busy"


def test_invalid_roles_and_widgets_fail_before_mutation():
    widget = FakeWidget("Button")

    with pytest.raises(UiComponentError, match="Unbekannte Komponentenrolle"):
        register_component(widget, "glow")
    with pytest.raises(UiComponentError, match="Buttonrolle"):
        build_button_style(LEGACY_COLORS, "glow")
    with pytest.raises(UiComponentError, match="kein Button"):
        configure_button(FakeWidget("Frame"), LEGACY_COLORS)

    assert widget.options == {"state": "normal"}

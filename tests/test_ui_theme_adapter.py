import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SYSTEM_DIR = Path(__file__).resolve().parents[1] / "system"
if str(SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(SYSTEM_DIR))

from config_models import (
    GuiConfigModel,
    GuiLayoutConfig,
    GuiTextSpacingConfig,
    ThemeConfig,
)
from ui_theme_adapter import (
    UiThemeError,
    apply_module_card_theme,
    apply_theme_tree,
    build_status_palette,
    build_tooltip_style,
    resolve_contrast_theme,
    resolve_theme,
)


COLORS = {
    "background": "#101010",
    "foreground": "#f0f0f0",
    "accent": "#00ff99",
    "button_background": "#202020",
    "button_foreground": "#ffffff",
    "status_success": "#006622",
    "status_error": "#990000",
    "status_busy": "#996600",
    "status_foreground": "#ffffff",
}
ALT_COLORS = {**COLORS, "background": "#ffffff", "foreground": "#111111"}


class FakeWidget:
    def __init__(self, widget_class="Frame", children=None, menu=None):
        self.widget_class = widget_class
        self.children = list(children or [])
        self.menu = menu
        self.options = {}

    def configure(self, **options):
        self.options.update(options)

    def winfo_class(self):
        return self.widget_class

    def winfo_children(self):
        return list(self.children)

    def __getitem__(self, key):
        if key != "menu" or self.menu is None:
            raise KeyError(key)
        return self.menu


class StrictButton(FakeWidget):
    def __getitem__(self, key):
        raise AssertionError(f"Ein normales Button-Widget darf {key!r} nicht abfragen.")


class NamedMenuButton(FakeWidget):
    def __init__(self, menu):
        super().__init__("Menubutton")
        self.menu = menu

    def __getitem__(self, key):
        if key != "menu":
            raise KeyError(key)
        return ".menu"

    def nametowidget(self, name):
        if name != ".menu":
            raise KeyError(name)
        return self.menu


def make_config():
    layout = GuiLayoutConfig(
        gap_xs=2,
        gap_sm=4,
        gap_md=8,
        gap_lg=12,
        gap_xl=16,
        button_padx=4,
        button_pady=3,
        button_min_width=12,
        button_font_size=12,
        field_padx=4,
        field_pady=3,
        text_spacing=GuiTextSpacingConfig(before=0, line=0, after=0),
        focus_thickness=2,
    )
    return GuiConfigModel(
        default_theme="standard",
        themes={
            "standard": ThemeConfig("standard", "Standard", dict(COLORS)),
            "hochkontrast": ThemeConfig(
                "hochkontrast", "Hoher Kontrast", dict(ALT_COLORS)
            ),
        },
        refresh_debounce_ms=200,
        layout=layout,
    )


def test_resolve_theme_uses_requested_theme_and_immutable_copy():
    config = make_config()
    resolved = resolve_theme(config, "hochkontrast", strict=True)

    assert resolved.name == "hochkontrast"
    assert resolved.label == "Hoher Kontrast"
    assert resolved.colors["background"] == "#ffffff"
    with pytest.raises(TypeError):
        resolved.colors["background"] = "#000000"


def test_resolve_theme_falls_back_or_rejects_unknown_name():
    config = make_config()

    assert resolve_theme(config, "unbekannt").name == "standard"
    with pytest.raises(UiThemeError, match="Unbekanntes Farbschema"):
        resolve_theme(config, "unbekannt", strict=True)


def test_resolve_contrast_theme_uses_label_when_key_differs():
    assert resolve_contrast_theme(make_config()) == "hochkontrast"


def test_status_and_tooltip_palettes_follow_same_theme_contract():
    resolved = resolve_theme(make_config(), "standard")

    assert build_status_palette(resolved) == {
        "success": "#006622",
        "error": "#990000",
        "busy": "#996600",
        "foreground": "#ffffff",
    }
    assert build_tooltip_style(resolved) == {
        "bg": "#202020",
        "fg": "#ffffff",
        "border": "#00ff99",
    }


def test_apply_theme_tree_styles_nested_widgets_and_option_menu():
    menu = FakeWidget("Menu")
    option_menu = FakeWidget("Menubutton", menu=menu)
    text = FakeWidget("Text")
    label = FakeWidget("Label")
    button = FakeWidget("Button")
    frame = FakeWidget("Frame", children=[label, button, text, option_menu])
    root = FakeWidget("Tk", children=[frame])

    apply_theme_tree(root, COLORS, button_font="ButtonFont")

    assert root.options["background"] == "#101010"
    assert frame.options["background"] == "#101010"
    assert label.options == {"background": "#101010", "foreground": "#f0f0f0"}
    assert button.options["background"] == "#202020"
    assert button.options["activebackground"] == "#00ff99"
    assert text.options["insertbackground"] == "#f0f0f0"
    assert option_menu.options["font"] == "ButtonFont"
    assert menu.options["activeforeground"] == "#ffffff"


def test_plain_button_never_queries_nonexistent_menu_option():
    button = StrictButton("Button")
    root = FakeWidget("Tk", children=[button])

    apply_theme_tree(root, COLORS, button_font="ButtonFont")

    assert button.options["background"] == "#202020"
    assert button.options["font"] == "ButtonFont"


def test_named_tk_menu_reference_is_resolved_and_styled():
    menu = FakeWidget("Menu")
    option_menu = NamedMenuButton(menu)
    root = FakeWidget("Tk", children=[option_menu])

    apply_theme_tree(root, COLORS, button_font="ButtonFont")

    assert menu.options["background"] == "#202020"
    assert menu.options["activeforeground"] == "#ffffff"
    assert menu.options["font"] == "ButtonFont"


def test_apply_module_card_theme_preserves_card_specific_accents():
    card = SimpleNamespace(
        frame=FakeWidget(),
        header=FakeWidget(),
        title_label=FakeWidget("Label"),
        drag_label=FakeWidget("Label"),
        description=FakeWidget("Label"),
        status_label=FakeWidget("Label"),
        activate_button=FakeWidget("Button"),
        deactivate_button=FakeWidget("Button"),
        resize_handle=FakeWidget("Label"),
    )

    apply_module_card_theme(card, COLORS)

    assert card.frame.options["highlightbackground"] == "#00ff99"
    assert card.drag_label.options["foreground"] == "#00ff99"
    assert card.activate_button.options["background"] == "#202020"
    assert card.resize_handle.options["foreground"] == "#00ff99"


def test_missing_theme_color_fails_before_widget_mutation():
    root = FakeWidget("Tk")
    incomplete = {key: value for key, value in COLORS.items() if key != "accent"}

    with pytest.raises(UiThemeError, match="accent"):
        apply_theme_tree(root, incomplete)
    assert root.options == {}

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
JAVASCRIPT = (ROOT / "web" / "app.js").read_text(encoding="utf-8")


class UiParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.views: set[str] = set()
        self.panels: set[str] = set()
        self.module_actions: set[tuple[str, str]] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        if values.get("data-view"):
            self.views.add(values["data-view"])
        if values.get("data-panel"):
            self.panels.add(values["data-panel"])
        if values.get("data-module-id") and values.get("data-module-action"):
            self.module_actions.add(
                (values["data-module-id"], values["data-module-action"])
            )


def parsed_ui() -> UiParser:
    parser = UiParser()
    parser.feed(HTML)
    return parser


def test_every_navigation_target_has_a_real_panel() -> None:
    parser = parsed_ui()
    assert parser.views <= parser.panels
    assert {
        "dashboard",
        "search",
        "memo",
        "tasks",
        "calendar",
        "characters",
        "archive",
        "files",
        "media",
        "profiles",
        "modules",
        "tools",
        "system",
        "help",
    } <= parser.panels


def test_every_literal_required_element_reference_exists() -> None:
    parser = parsed_ui()
    referenced = set(re.findall(r'byId\("([A-Za-z0-9_-]+)"', JAVASCRIPT))
    missing = referenced - parser.ids
    assert not missing, f"JavaScript referenziert fehlende IDs: {sorted(missing)}"


def test_interaction_core_uses_delegation_and_visible_error_boundary() -> None:
    assert 'document.addEventListener("click"' in JAVASCRIPT
    assert 'document.addEventListener("submit"' in JAVASCRIPT
    assert 'window.addEventListener("error"' in JAVASCRIPT
    assert 'window.addEventListener("unhandledrejection"' in JAVASCRIPT
    assert 'dataset.appReady = "true"' in JAVASCRIPT
    assert "refreshAll" not in JAVASCRIPT
    assert "calendarLoad" not in JAVASCRIPT
    assert 'id="fatalError"' in HTML


def test_previous_core_content_and_full_module_surfaces_are_present() -> None:
    parser = parsed_ui()
    assert ("notiz_editor", "list_templates") in parser.module_actions
    assert ("todo_kalender", "sync_todo_txt") in parser.module_actions
    assert ("charakter_modul", "list_templates") in parser.module_actions
    for required in {
        "fileTableBody",
        "filePreviewImage",
        "moduleCatalog",
        "systemActions",
        "globalSearchForm",
        "calendarGrid",
        "archiveEntries",
    }:
        assert required in parser.ids


def test_assets_are_versioned_and_no_inline_script_is_required() -> None:
    assert "/app.js?v=3" in HTML
    assert "/styles.css?v=3" in HTML
    assert "<script>" not in HTML

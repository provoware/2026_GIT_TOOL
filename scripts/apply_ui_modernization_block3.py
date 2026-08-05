#!/usr/bin/env python3
"""Integriert Block 3 idempotent in Launcher und Hauptfenster."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "components": Path("system/ui_components.py"),
    "launcher": Path("system/launcher_gui.py"),
    "main_window": Path("system/main_window.py"),
}


class Block3CodemodError(RuntimeError):
    pass


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise Block3CodemodError(f"{label}: erwartete Fundstelle {count} statt 1.")
    return text.replace(old, new, 1)


def _insert_before_once(text: str, marker: str, insertion: str, label: str) -> str:
    if insertion in text:
        return text
    count = text.count(marker)
    if count != 1:
        raise Block3CodemodError(f"{label}: erwartete Fundstelle {count} statt 1.")
    return text.replace(marker, insertion + marker, 1)


def transform_components(text: str) -> str:
    return _replace_once(
        text,
        '    hover_bg = mix_hex(normal_bg, palette.accent, 0.20)\n',
        '    hover_bg = mix_hex(normal_bg, "#ffffff", 0.12)\n'
        '    if hover_bg == normal_bg:\n'
        '        hover_bg = mix_hex(normal_bg, "#000000", 0.12)\n',
        "Komponenten-Hover",
    )


def transform_launcher(text: str) -> str:
    text = _insert_before_once(
        text,
        "from ui_theme_adapter import (\n",
        "from ui_components import UiComponentError, configure_status_widget, register_component\n",
        "Launcher-Komponentenimport",
    )
    text = _replace_once(
        text,
        "        self.tooltip_style: Dict[str, str] = {}\n",
        "        self.tooltip_style: Dict[str, str] = {}\n"
        "        self.component_theme = None\n",
        "Launcher-Komponententheme",
    )
    for label, creation, registration in (
        (
            "Launcher-Einstellungenpanel",
            '        controls_section = tk.LabelFrame(self.root, text="Einstellungen und Filter")\n',
            '        controls_section = tk.LabelFrame(self.root, text="Einstellungen und Filter")\n'
            '        register_component(controls_section, "panel")\n',
        ),
        (
            "Launcher-Hilfepanel",
            '        help_section = tk.LabelFrame(self.root, text="Hilfe (Kurzinfo)")\n',
            '        help_section = tk.LabelFrame(self.root, text="Hilfe (Kurzinfo)")\n'
            '        register_component(help_section, "panel")\n',
        ),
        (
            "Launcher-Entwicklerpanel",
            '        developer_section = tk.LabelFrame(\n'
            '            self.root, text=f"{ICON_SET[\'developer\']} Entwicklerbereich (für Profis)"\n'
            '        )\n',
            '        developer_section = tk.LabelFrame(\n'
            '            self.root, text=f"{ICON_SET[\'developer\']} Entwicklerbereich (für Profis)"\n'
            '        )\n'
            '        register_component(developer_section, "panel")\n',
        ),
        (
            "Launcher-Statuspanel",
            '        status_section = tk.LabelFrame(self.root, text="Status")\n',
            '        status_section = tk.LabelFrame(self.root, text="Status")\n'
            '        register_component(status_section, "panel")\n',
        ),
        (
            "Launcher-Ausgabepanel",
            '        output_section = tk.LabelFrame(self.root, text="Modulübersicht")\n',
            '        output_section = tk.LabelFrame(self.root, text="Modulübersicht")\n'
            '        register_component(output_section, "panel")\n',
        ),
    ):
        text = _replace_once(text, creation, registration, label)

    role_lines = {
        "self.refresh_button": "primary",
        "self.logout_button": "danger",
        "self.diagnostics_button": "secondary",
        "self.main_window_button": "secondary",
        "self.scan_button": "neutral",
        "self.standards_button": "neutral",
        "self.logs_button": "neutral",
        "self.export_button": "secondary",
        "self.export_center_button": "secondary",
        "self.backup_button": "primary",
    }
    for widget, role in role_lines.items():
        old = f"        {widget}.configure(takefocus=1, underline=0)\n"
        new = old + f'        register_component({widget}, "{role}")\n'
        text = _replace_once(text, old, new, f"Launcher-Rolle {widget}")

    text = _insert_before_once(
        text,
        "        self.drop_zone_label.grid(\n",
        '        register_component(self.drop_zone_label, "drop-zone")\n',
        "Launcher-Dropzone",
    )
    text = _replace_once(
        text,
        '        self.status_indicator = tk.Label(status_section, text="●", width=2, anchor="w")\n'
        '        self.status_indicator.pack(side="left", padx=(self.layout.gap_md, 0))\n',
        '        self.status_indicator = tk.Label(status_section, text="○", width=2, anchor="w")\n'
        '        register_component(self.status_indicator, "status")\n'
        '        self.status_indicator.pack(side="left", padx=(self.layout.gap_md, 0))\n',
        "Launcher-Statusindikator",
    )
    text = _replace_once(
        text,
        "        self.current_theme = theme.name\n"
        "        self.status_palette = build_status_palette(theme)\n",
        "        self.current_theme = theme.name\n"
        "        self.component_theme = theme\n"
        "        self.status_palette = build_status_palette(theme)\n",
        "Launcher-Themezustand",
    )
    old_status = '''    def _apply_status_style(self, state: str) -> None:
        if self.status_label is None or not self.status_palette:
            return
        bg = self.status_palette.get(state, self.status_palette.get("success", ""))
        fg = self.status_palette.get("foreground", "")
        if bg:
            self.status_label.configure(bg=bg)
            if self.status_indicator is not None:
                self.status_indicator.configure(bg=bg, fg=fg or "#ffffff")
        if fg:
            self.status_label.configure(fg=fg)
'''
    new_status = '''    def _apply_status_style(self, state: str) -> None:
        if self.status_label is None or self.component_theme is None:
            return
        try:
            style = configure_status_widget(
                self.status_indicator,
                self.component_theme,
                state,
            )
        except UiComponentError as exc:
            raise GuiLauncherError(str(exc)) from exc
        self.status_label.configure(bg=style.background, fg=style.foreground)
        if self.status_indicator is not None:
            self.status_indicator.configure(text=style.symbol)
'''
    text = _replace_once(text, old_status, new_status, "Launcher-Statusdarstellung")
    return text


def transform_main_window(text: str) -> str:
    text = _insert_before_once(
        text,
        "from ui_responsive import (\n",
        "from ui_components import register_component\n",
        "Hauptfenster-Komponentenimport",
    )
    text = _replace_once(
        text,
        "        for button in (self.activate_button, self.deactivate_button):\n"
        "            button.configure(pady=7, takefocus=1)\n",
        "        for button in (self.activate_button, self.deactivate_button, self.history_button):\n"
        "            button.configure(takefocus=1)\n",
        "Hauptfenster-Buttonduplikat",
    )
    text = _replace_once(
        text,
        "        menu.configure(padx=6, pady=8, takefocus=1)\n",
        "        menu.configure(takefocus=1)\n",
        "Hauptfenster-Menüduplikat",
    )
    text = _replace_once(
        text,
        "        controls = tk.Frame(self.root)\n"
        "        controls.pack(fill=\"x\", padx=16, pady=(0, 8))\n",
        "        controls = tk.Frame(self.root)\n"
        "        register_component(controls, \"panel\")\n"
        "        controls.pack(fill=\"x\", padx=16, pady=(0, 8))\n",
        "Hauptfenster-Steuerpanel",
    )
    text = _replace_once(
        text,
        "        self.workspace = tk.Frame(self.root)\n"
        "        self.workspace.pack(fill=\"both\", expand=True, padx=16, pady=8)\n",
        "        self.workspace = tk.Frame(self.root)\n"
        "        register_component(self.workspace, \"panel\")\n"
        "        self.workspace.pack(fill=\"both\", expand=True, padx=16, pady=8)\n",
        "Hauptfenster-Workspacepanel",
    )
    return text


def apply(root: Path, *, check: bool) -> list[str]:
    changed: list[str] = []
    transforms = {
        "components": transform_components,
        "launcher": transform_launcher,
        "main_window": transform_main_window,
    }
    for key, relative in TARGETS.items():
        path = root / relative
        original = path.read_text(encoding="utf-8")
        transformed = transforms[key](original)
        if transformed != original:
            changed.append(relative.as_posix())
            if not check:
                path.write_text(transformed, encoding="utf-8", newline="\n")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        changed = apply(args.root.resolve(), check=args.check)
    except (OSError, Block3CodemodError) as exc:
        print(f"Block-3-Codemod-Fehler: {exc}")
        return 2
    if args.check and changed:
        print("Block-3-Integration fehlt oder ist veraltet:")
        for path in changed:
            print(f"- {path}")
        return 1
    if changed:
        print("Block-3-Integration aktualisiert:")
        for path in changed:
            print(f"- {path}")
    else:
        print("Block-3-Integration ist aktuell.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Integriert Gate 6 kontrolliert in system/main_window.py."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


TARGET = Path(__file__).resolve().parents[1] / "system" / "main_window.py"
IMPORT = '''from module_lifecycle import (
    ModuleActionOutcome,
    ModuleCardPresentation,
    ModuleLifecycleError,
    perform_module_action,
    prepare_close,
    resolve_card_presentation,
)
'''

MODULE_WIDGET_METHODS = {
    "update_status": '''    def update_status(self, text: str, color: str) -> None:
        self.status_label.configure(text=text, foreground=color)

    def apply_presentation(
        self,
        presentation: ModuleCardPresentation,
        color: str,
    ) -> None:
        if not isinstance(presentation, ModuleCardPresentation):
            raise MainWindowError("Modulkarten-Darstellung ist ungültig.")
        self.update_status(presentation.status_text, color)
        self.activate_button.configure(
            state="normal" if presentation.activate_enabled else "disabled"
        )
        self.deactivate_button.configure(
            state="normal" if presentation.deactivate_enabled else "disabled"
        )
''',
}

MAIN_WINDOW_METHODS = {
    "_create_module_widgets": '''    def _create_module_widgets(self, tk) -> None:
        states = self.manager.list_states(include_disabled=False)
        visible_states = states[:9]
        if len(states) > 9:
            self._set_status(
                "Hinweis: Es werden die ersten 9 Module angezeigt.",
                self._theme_colors()["status_busy"],
            )
        theme = self._theme_colors()
        for state in visible_states:
            widget = ModuleWidget(
                self.workspace,
                state,
                theme,
                on_activate=self._activate_widget,
                on_deactivate=self._deactivate_widget,
                on_drag=self._drag_widget,
                on_resize=self._resize_widget,
                on_status=self._set_status,
            )
            self.module_widgets.append(widget)
            self._sync_widget_state(widget)
''',
    "_activate_widget": '''    def _activate_widget(self, widget: ModuleWidget) -> None:
        outcome = perform_module_action(
            self.manager,
            widget.state.entry.module_id,
            "activate",
        )
        self._apply_action_outcome(widget, outcome)
''',
    "_deactivate_widget": '''    def _deactivate_widget(self, widget: ModuleWidget) -> None:
        outcome = perform_module_action(
            self.manager,
            widget.state.entry.module_id,
            "deactivate",
        )
        self._apply_action_outcome(widget, outcome)
''',
    "_apply_action_result": '''    def _sync_widget_state(self, widget: ModuleWidget) -> None:
        presentation = resolve_card_presentation(widget.state)
        color = self._theme_colors()[presentation.color_key]
        widget.apply_presentation(presentation, color)

    def _sync_all_widgets(self) -> None:
        for widget in self.module_widgets:
            self._sync_widget_state(widget)

    def _apply_action_outcome(
        self,
        widget: ModuleWidget,
        outcome: ModuleActionOutcome,
    ) -> None:
        if not isinstance(outcome, ModuleActionOutcome):
            raise MainWindowError("Modulaktion lieferte kein gültiges Ergebnis.")
        widget.state = outcome.state
        color = self._theme_colors()[outcome.presentation.color_key]
        widget.apply_presentation(outcome.presentation, color)
        self._set_status(outcome.result.message, color)

    def _apply_theme_and_sync(self) -> None:
        self._apply_theme()
        self._sync_all_widgets()
''',
    "_on_close": '''    def _on_close(self) -> None:
        try:
            decision = prepare_close(self.manager)
        except (ModuleLifecycleError, ModuleManagerError) as exc:
            self.logger.error("Hauptfenster: Schließen fehlgeschlagen: %s", exc)
            self._set_status(
                f"Schließen fehlgeschlagen: {exc}",
                self._theme_colors()["status_error"],
            )
            return

        self._sync_all_widgets()
        color = self._theme_colors()[decision.color_key]
        self._set_status(decision.message, color)
        if decision.allow_close:
            self.logger.info(decision.report.rstrip())
            self.root.destroy()
            return
        self.logger.error(decision.report.rstrip())
''',
}


def _class_methods(tree: ast.Module, class_name: str) -> dict[str, ast.AST]:
    target = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name),
        None,
    )
    if target is None:
        raise RuntimeError(f"Klasse fehlt: {class_name}")
    return {
        node.name: node
        for node in target.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _replace_methods(
    source: str,
    class_name: str,
    replacements: dict[str, str],
) -> str:
    tree = ast.parse(source)
    methods = _class_methods(tree, class_name)
    missing = sorted(set(replacements) - set(methods))
    if missing:
        raise RuntimeError(f"Methoden fehlen in {class_name}: {', '.join(missing)}")

    lines = source.splitlines(keepends=True)
    edits = []
    for name, replacement in replacements.items():
        node = methods[name]
        start = min([node.lineno] + [item.lineno for item in node.decorator_list]) - 1
        edits.append((start, node.end_lineno, replacement.rstrip("\n") + "\n"))
    for start, end, replacement in sorted(edits, reverse=True):
        lines[start:end] = [replacement]
    result = "".join(lines)
    ast.parse(result)
    return result


def _is_integrated(source: str) -> bool:
    tree = ast.parse(source)
    widget_methods = _class_methods(tree, "ModuleWidget")
    window_methods = _class_methods(tree, "MainWindow")
    return (
        IMPORT in source
        and "apply_presentation" in widget_methods
        and "_apply_action_result" not in window_methods
        and {
            "_sync_widget_state",
            "_sync_all_widgets",
            "_apply_action_outcome",
            "_apply_theme_and_sync",
        }.issubset(window_methods)
        and 'command=lambda _value: self._apply_theme_and_sync(),' in source
    )


def transform(source: str) -> str:
    if _is_integrated(source):
        ast.parse(source)
        return source

    result = _replace_methods(source, "ModuleWidget", MODULE_WIDGET_METHODS)
    result = _replace_methods(result, "MainWindow", MAIN_WINDOW_METHODS)

    old_theme_command = 'command=lambda _value: self._apply_theme(),'
    new_theme_command = 'command=lambda _value: self._apply_theme_and_sync(),'
    if old_theme_command in result:
        result = result.replace(old_theme_command, new_theme_command, 1)
    elif new_theme_command not in result:
        raise RuntimeError("Theme-Menüanker fehlt.")

    if IMPORT not in result:
        anchor = (
            "from module_manager import ModuleActionResult, ModuleManager, "
            "ModuleManagerError, ModuleState\n"
        )
        if anchor not in result:
            raise RuntimeError("Modul-Lifecycle-Importanker fehlt.")
        result = result.replace(anchor, anchor + IMPORT, 1)

    ast.parse(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=TARGET)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    source = args.path.read_text(encoding="utf-8")
    result = transform(source)
    changed = result != source
    if args.check:
        return 1 if changed else 0
    if changed:
        args.path.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

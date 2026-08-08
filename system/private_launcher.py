#!/usr/bin/env python3
"""Schlanke Privattool-Oberfläche auf Basis des bestehenden Launchers."""

from __future__ import annotations

from pathlib import Path

import launcher_gui


class PrivateUiAdapter:
    """Reduziert die Standardansicht, ohne Profi-Funktionen zu entfernen."""

    def __init__(self, app: launcher_gui.LauncherGui) -> None:
        self.app = app
        self.advanced_visible = False
        self.advanced_button = None
        self._original_layout_update = app._update_layout_by_width
        self._original_finish_diagnostics = app._finish_diagnostics

    @property
    def advanced_buttons(self) -> tuple[object, ...]:
        return tuple(
            button
            for button in (
                self.app.scan_button,
                self.app.standards_button,
                self.app.export_button,
                self.app.export_center_button,
            )
            if button is not None
        )

    def install(self) -> None:
        import tkinter as tk

        frame = self.app.developer_frame
        if frame is None:
            raise launcher_gui.GuiLauncherError("Privatwartungsbereich fehlt.")

        section = getattr(frame, "master", None)
        if section is not None:
            try:
                section.configure(text="🛠️ Wartung")
            except Exception:
                pass

        if self.app.developer_hint is not None:
            self.app.developer_hint.configure(
                text=(
                    "Privatbetrieb: Diagnose + Privat-ZIP, Logs und Backup sind die "
                    "Kernfunktionen. Seltene technische Werkzeuge liegen unter „Erweitert“."
                )
            )

        if self.app.diagnostics_button is not None:
            self.app.diagnostics_button.configure(text="🧪 Diagnose + Privat-ZIP")

        self.advanced_button = tk.Button(
            frame,
            text="⚙ Erweitert anzeigen",
            command=self.toggle_advanced,
        )
        if self.app.button_font is not None:
            self.advanced_button.configure(font=self.app.button_font)
        self.advanced_button.configure(
            padx=self.app.layout.button_padx,
            pady=self.app.layout.button_pady,
            width=self.app.button_min_width,
            takefocus=1,
            underline=0,
        )
        launcher_gui.register_component(self.advanced_button, "neutral")
        self.app._register_help(
            self.advanced_button,
            "Blendet selten benötigte technische Werkzeuge ein oder aus.",
            "Erweitert enthält System-Scan, Standards und Exportwerkzeuge. Für den normalen Privatbetrieb sind diese Funktionen nicht erforderlich.",
        )

        self.app._finish_diagnostics = self._finish_diagnostics
        self.app._update_layout_by_width = self._update_layout_by_width
        self._apply_private_layout()
        self.app.apply_theme(self.app.current_theme)
        self.app._set_status("Bereit.", state="success")

    def _finish_diagnostics(self, outcome) -> None:
        self._original_finish_diagnostics(outcome)
        if outcome.error is not None:
            return
        result = outcome.value
        if not isinstance(result, launcher_gui.diagnostics_runner.DiagnosticsResult):
            return
        if result.status != "ok":
            return
        project_root = self.app.module_config.resolve().parents[1]
        zip_path = project_root / "dist" / "2026_GIT_TOOL_PRIVAT.zip"
        if zip_path.is_file():
            self.app._set_status("Geprüft – ZIP erstellt.", state="success")
        else:
            self.app._set_status("Prüfung abgeschlossen – ZIP fehlt.", state="error")

    def toggle_advanced(self) -> None:
        self.advanced_visible = not self.advanced_visible
        self._apply_private_layout()
        state = "eingeblendet" if self.advanced_visible else "ausgeblendet"
        self.app._set_status(f"Erweiterte Werkzeuge {state}.", state="success")

    def _update_layout_by_width(self) -> None:
        self._original_layout_update()
        self._apply_private_layout()

    def _apply_private_layout(self) -> None:
        frame = self.app.developer_frame
        if frame is None or self.advanced_button is None:
            return

        for column in range(4):
            frame.columnconfigure(column, weight=1 if column < 3 else 0)

        if self.app.developer_hint is not None:
            self.app.developer_hint.grid_configure(
                row=0,
                column=0,
                columnspan=3,
                sticky="w",
                padx=self.app.layout.gap_xs,
                pady=self.app.layout.gap_xs,
            )

        if self.app.logs_button is not None:
            self.app.logs_button.grid_configure(
                row=1,
                column=0,
                columnspan=1,
                sticky="ew",
                padx=self.app.layout.gap_xs,
                pady=self.app.layout.gap_xs,
            )
        if self.app.backup_button is not None:
            self.app.backup_button.grid_configure(
                row=1,
                column=1,
                columnspan=1,
                sticky="ew",
                padx=self.app.layout.gap_xs,
                pady=self.app.layout.gap_xs,
            )
        self.advanced_button.grid_configure(
            row=1,
            column=2,
            columnspan=1,
            sticky="ew",
            padx=self.app.layout.gap_xs,
            pady=self.app.layout.gap_xs,
        )

        if not self.advanced_visible:
            for button in self.advanced_buttons:
                button.grid_remove()
            self.advanced_button.configure(text="⚙ Erweitert anzeigen")
            return

        positions = {
            self.app.scan_button: (2, 0),
            self.app.standards_button: (2, 1),
            self.app.export_button: (3, 0),
            self.app.export_center_button: (3, 1),
        }
        for button, position in positions.items():
            if button is None:
                continue
            row, column = position
            button.grid(
                row=row,
                column=column,
                columnspan=1,
                sticky="ew",
                padx=self.app.layout.gap_xs,
                pady=self.app.layout.gap_xs,
            )
        self.advanced_button.configure(text="⚙ Erweitert ausblenden")


def run_gui(
    module_config: Path,
    gui_config: launcher_gui.GuiConfigModel,
    show_all: bool,
    debug: bool,
) -> int:
    import tkinter as tk

    root = tk.Tk()
    app = launcher_gui.LauncherGui(
        root=root,
        module_config=module_config,
        gui_config=gui_config,
        show_all=show_all,
        debug=debug,
    )
    PrivateUiAdapter(app).install()
    root.mainloop()
    return 0


def main() -> int:
    parser = launcher_gui.build_parser()
    args = parser.parse_args()
    launcher_gui.setup_logging(args.debug)
    logger = launcher_gui.get_logger("private_launcher")

    try:
        gui_config = launcher_gui.load_gui_config(args.gui_config)
        return run_gui(args.config, gui_config, args.show_all, args.debug)
    except (launcher_gui.GuiLauncherError, launcher_gui.LauncherError) as exc:
        logger.error("Privattool-Launcher konnte nicht starten: %s", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

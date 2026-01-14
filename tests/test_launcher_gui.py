import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from launcher import ModuleEntry
from launcher_gui import GuiLauncherError, build_module_lines, load_gui_config


class LauncherGuiTests(unittest.TestCase):
    def test_load_gui_config_reads_themes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "launcher_gui.json"
            config_path.write_text(
                json.dumps(
                    {
                        "default_theme": "hell",
                        "themes": {
                            "hell": {
                                "label": "Hell",
                                "colors": {
                                    "background": "#ffffff",
                                    "foreground": "#111111",
                                    "accent": "#005ea5",
                                    "button_background": "#e6f0fb",
                                    "button_foreground": "#0b2d4d",
                                    "status_success": "#1b5e20",
                                    "status_error": "#b00020",
                                    "status_busy": "#005ea5",
                                    "status_foreground": "#ffffff",
                                },
                            }
                        },
                        "layout": {
                            "gap_xs": 4,
                            "gap_sm": 8,
                            "gap_md": 12,
                            "gap_lg": 16,
                            "gap_xl": 24,
                            "button_padx": 12,
                            "button_pady": 6,
                            "field_padx": 6,
                            "field_pady": 4,
                            "text_spacing": {"before": 4, "line": 2, "after": 4},
                            "focus_thickness": 2,
                        },
                    }
                ),
                encoding="utf-8",
            )

            config = load_gui_config(config_path)

            self.assertEqual("hell", config.default_theme)
            self.assertIn("hell", config.themes)

    def test_load_gui_config_rejects_invalid_color(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "launcher_gui.json"
            config_path.write_text(
                json.dumps(
                    {
                        "default_theme": "hell",
                        "themes": {
                            "hell": {
                                "label": "Hell",
                                "colors": {
                                    "background": "white",
                                    "foreground": "#111111",
                                    "accent": "#005ea5",
                                    "button_background": "#e6f0fb",
                                    "button_foreground": "#0b2d4d",
                                    "status_success": "#1b5e20",
                                    "status_error": "#b00020",
                                    "status_busy": "#005ea5",
                                    "status_foreground": "#ffffff",
                                },
                            }
                        },
                        "layout": {
                            "gap_xs": 4,
                            "gap_sm": 8,
                            "gap_md": 12,
                            "gap_lg": 16,
                            "gap_xl": 24,
                            "button_padx": 12,
                            "button_pady": 6,
                            "field_padx": 6,
                            "field_pady": 4,
                            "text_spacing": {"before": 4, "line": 2, "after": 4},
                            "focus_thickness": 2,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(GuiLauncherError):
                load_gui_config(config_path)

    def test_build_module_lines_includes_debug_path(self):
        module = ModuleEntry(
            module_id="status",
            name="Status-Check",
            path="modules/status",
            enabled=True,
            description="Testmodul",
        )
        root = Path("/tmp")

        lines = build_module_lines([module], root, debug=True)

        self.assertTrue(any("Pfad:" in line for line in lines))


if __name__ == "__main__":
    unittest.main()

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from json_validator import validate_json_file


class JsonValidatorTests(unittest.TestCase):
    def test_launcher_gui_config_validates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir(parents=True)
            config_path = config_dir / "launcher_gui.json"
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

            result = validate_json_file(config_path)

            self.assertEqual([], result.issues)

    def test_modules_config_rejects_empty_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir(parents=True)
            config_path = config_dir / "modules.json"
            config_path.write_text(
                json.dumps({"version": "1.0", "modules": []}),
                encoding="utf-8",
            )

            result = validate_json_file(config_path)

            self.assertTrue(result.issues)

    def test_filename_suffixes_validates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir(parents=True)
            config_path = config_dir / "filename_suffixes.json"
            config_path.write_text(
                json.dumps({"defaults": {"data": ".json", "logs": ".log"}}),
                encoding="utf-8",
            )

            result = validate_json_file(config_path)

            self.assertEqual([], result.issues)

    def test_pin_config_validates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir(parents=True)
            config_path = config_dir / "pin.json"
            config_path.write_text(
                json.dumps(
                    {
                        "enabled": False,
                        "pin_hint": "Standard-PIN: 0000",
                        "pin_hash": "hash",
                        "salt": "salt",
                        "max_attempts": 3,
                        "lock_min_seconds": 2,
                        "lock_max_seconds": 5,
                    }
                ),
                encoding="utf-8",
            )

            result = validate_json_file(config_path)

            self.assertEqual([], result.issues)


if __name__ == "__main__":
    unittest.main()

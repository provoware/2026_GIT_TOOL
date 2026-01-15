import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from desktop_entry import DesktopEntryConfig, build_desktop_entry, load_config, validate_config


class DesktopEntryTests(unittest.TestCase):
    def test_build_desktop_entry_contains_required_fields(self):
        config = DesktopEntryConfig(
            app_name="Test App",
            app_id="test_app",
            comment="Test Kommentar",
            exec_path="./scripts/start.sh",
            icon_name="test_icon",
            categories=["Utility"],
            keywords=["test"],
            terminal=False,
        )
        content = build_desktop_entry(config, Path("/root/project"))
        self.assertIn("Name=Test App", content)
        self.assertIn("Exec=/root/project/scripts/start.sh", content)
        self.assertIn("Icon=test_icon", content)
        self.assertIn("Categories=Utility;", content)

    def test_load_config_parses_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "app_name": "Demo",
                        "app_id": "demo_app",
                        "comment": "Demo",
                        "exec": "./scripts/start.sh",
                        "icon_name": "demo_icon",
                        "categories": ["Utility"],
                        "keywords": ["demo"],
                        "terminal": False,
                    }
                ),
                encoding="utf-8",
            )
            config = load_config(path)
            self.assertEqual(config.app_name, "Demo")

    def test_validate_config_rejects_missing_name(self):
        config = DesktopEntryConfig(
            app_name="",
            app_id="demo_app",
            comment="Demo",
            exec_path="./scripts/start.sh",
            icon_name="demo_icon",
            categories=["Utility"],
            keywords=[],
            terminal=False,
        )
        with self.assertRaises(Exception):
            validate_config(config)


if __name__ == "__main__":
    unittest.main()

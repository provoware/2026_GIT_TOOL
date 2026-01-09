import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from launcher import (
    LauncherError,
    filter_modules,
    load_modules,
    render_module_overview,
)


class LauncherTests(unittest.TestCase):
    def test_load_modules_reads_valid_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            modules_dir = base / "modules" / "status"
            modules_dir.mkdir(parents=True)
            module_path = modules_dir / "module.py"
            module_path.write_text("# test", encoding="utf-8")

            config_path = base / "config" / "modules.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                json.dumps(
                    {
                        "modules": [
                            {
                                "id": "status",
                                "name": "Status-Check",
                                "path": "modules/status/module.py",
                                "enabled": True,
                                "description": "Testmodul",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            modules = load_modules(config_path, root=base)

            self.assertEqual(1, len(modules))
            self.assertEqual("status", modules[0].module_id)

    def test_load_modules_raises_when_enabled_module_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            config_path = base / "modules.json"
            config_path.write_text(
                json.dumps(
                    {
                        "modules": [
                            {
                                "id": "fehlend",
                                "name": "Fehlt",
                                "path": "modules/fehlend/module.py",
                                "enabled": True,
                                "description": "Fehlerfall",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(LauncherError):
                load_modules(config_path, root=base)

    def test_render_module_overview_outputs_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            modules_dir = base / "modules" / "status"
            modules_dir.mkdir(parents=True)
            module_path = modules_dir / "module.py"
            module_path.write_text("# test", encoding="utf-8")

            config_path = base / "config" / "modules.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                json.dumps(
                    {
                        "modules": [
                            {
                                "id": "status",
                                "name": "Status-Check",
                                "path": "modules/status/module.py",
                                "enabled": True,
                                "description": "Testmodul",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            modules = load_modules(config_path, root=base)
            filtered = filter_modules(modules, show_all=True)
            output = render_module_overview(filtered, base)

            self.assertIn("Launcher: Module im Überblick", output)
            self.assertIn("Status-Check", output)

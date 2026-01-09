import json
import tempfile
import unittest
from pathlib import Path

from system import module_checker


class ModuleCheckerTests(unittest.TestCase):
    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def test_check_modules_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            module_dir = root / "modules" / "demo"
            module_dir.mkdir(parents=True)
            (module_dir / "module.py").write_text("# demo", encoding="utf-8")
            self._write_json(
                module_dir / "manifest.json",
                {
                    "id": "demo",
                    "name": "Demo",
                    "version": "1.0.0",
                    "description": "Demo-Modul",
                    "entry": "module.py",
                },
            )
            config_path = root / "config" / "modules.json"
            config_path.parent.mkdir(parents=True)
            self._write_json(
                config_path,
                {
                    "version": "1.0",
                    "modules": [
                        {
                            "id": "demo",
                            "name": "Demo",
                            "path": "modules/demo",
                            "enabled": True,
                            "description": "Demo",
                        }
                    ],
                },
            )

            entries = module_checker.load_modules(config_path)
            issues = module_checker.check_modules(entries)

            self.assertEqual(issues, [])

    def test_check_modules_missing_entry_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            module_dir = root / "modules" / "demo"
            module_dir.mkdir(parents=True)
            self._write_json(
                module_dir / "manifest.json",
                {
                    "id": "demo",
                    "name": "Demo",
                    "version": "1.0.0",
                    "description": "Demo-Modul",
                    "entry": "module.py",
                },
            )
            config_path = root / "config" / "modules.json"
            config_path.parent.mkdir(parents=True)
            self._write_json(
                config_path,
                {
                    "version": "1.0",
                    "modules": [
                        {
                            "id": "demo",
                            "name": "Demo",
                            "path": "modules/demo",
                            "enabled": True,
                            "description": "Demo",
                        }
                    ],
                },
            )

            entries = module_checker.load_modules(config_path)
            issues = module_checker.check_modules(entries)

            self.assertEqual(len(issues), 1)
            self.assertIn("Modul-Datei fehlt", issues[0])


if __name__ == "__main__":
    unittest.main()

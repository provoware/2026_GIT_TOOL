import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

import module_selftests


class ModuleSelftestsTests(unittest.TestCase):
    def test_selftest_runs_module(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            module_dir = root / "modules" / "demo"
            module_dir.mkdir(parents=True)
            module_path = module_dir / "module.py"
            module_path.write_text(
                "\n".join(
                    [
                        "def init():",
                        "    return True",
                        "",
                        "def run(input_data):",
                        "    if input_data.get('ping') != 'pong':",
                        "        raise ValueError('ping fehlt')",
                        "    return {'status': 'ok'}",
                        "",
                        "def exit():",
                        "    return True",
                    ]
                ),
                encoding="utf-8",
            )
            manifest_path = module_dir / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "id": "demo",
                        "name": "Demo",
                        "version": "1.0.0",
                        "description": "Demo-Modul",
                        "entry": "module.py",
                    }
                ),
                encoding="utf-8",
            )

            config_dir = root / "config"
            config_dir.mkdir()
            modules_config = config_dir / "modules.json"
            modules_config.write_text(
                json.dumps(
                    {
                        "modules": [
                            {
                                "id": "demo",
                                "name": "Demo",
                                "path": "modules/demo",
                                "enabled": True,
                                "description": "Demo-Modul",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            selftests_config = config_dir / "module_selftests.json"
            selftests_config.write_text(
                json.dumps({"testcases": {"demo": {"ping": "pong"}}}),
                encoding="utf-8",
            )

            results = module_selftests.run_selftests(modules_config, selftests_config)
            self.assertEqual(1, len(results))
            self.assertEqual("ok", results[0].status)


if __name__ == "__main__":
    unittest.main()

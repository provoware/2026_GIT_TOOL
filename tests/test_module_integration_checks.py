import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from module_integration_checks import run_integration_checks


class ModuleIntegrationChecksTests(unittest.TestCase):
    def _write_module(
        self,
        root: Path,
        module_id: str,
        manifest_id: str | None = None,
    ) -> Path:
        module_dir = root / "modules" / module_id
        module_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "id": manifest_id or module_id,
            "name": f"{module_id}-name",
            "version": "1.0.0",
            "description": "Testmodul",
            "entry": "module.py",
        }
        (module_dir / "manifest.json").write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )
        (module_dir / "module.py").write_text(
            "\n".join(
                [
                    "def validateInput(input_data):",
                    "    return input_data",
                    "",
                    "def validateOutput(output):",
                    "    return output",
                    "",
                    "def run(input_data):",
                    "    return input_data",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return module_dir

    def _write_configs(self, root: Path, modules: list[dict], testcases: dict) -> None:
        config_dir = root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "modules.json").write_text(
            json.dumps({"modules": modules}),
            encoding="utf-8",
        )
        (config_dir / "module_selftests.json").write_text(
            json.dumps({"testcases": testcases}),
            encoding="utf-8",
        )

    def test_integration_checks_ok(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_module(root, "mod_a")
            modules = [
                {
                    "id": "mod_a",
                    "name": "Modul A",
                    "path": "modules/mod_a",
                    "enabled": True,
                    "description": "Test",
                }
            ]
            testcases = {"mod_a": {"text": "ok"}}
            self._write_configs(root, modules, testcases)

            result = run_integration_checks(
                root / "config" / "modules.json",
                root / "config" / "module_selftests.json",
            )

            self.assertEqual([], result.issues)

    def test_reports_missing_selftest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_module(root, "mod_a")
            modules = [
                {
                    "id": "mod_a",
                    "name": "Modul A",
                    "path": "modules/mod_a",
                    "enabled": True,
                    "description": "Test",
                }
            ]
            self._write_configs(root, modules, testcases={})

            result = run_integration_checks(
                root / "config" / "modules.json",
                root / "config" / "module_selftests.json",
            )

            self.assertTrue(any("Kein Selftest" in issue for issue in result.issues))

    def test_reports_manifest_id_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_module(root, "mod_a", manifest_id="mod_b")
            modules = [
                {
                    "id": "mod_a",
                    "name": "Modul A",
                    "path": "modules/mod_a",
                    "enabled": True,
                    "description": "Test",
                }
            ]
            testcases = {"mod_a": {"text": "ok"}}
            self._write_configs(root, modules, testcases)

            result = run_integration_checks(
                root / "config" / "modules.json",
                root / "config" / "module_selftests.json",
            )

            self.assertTrue(
                any(
                    "Manifest-ID passt nicht" in issue
                    or "Manifest: id muss dem Modulordner entsprechen" in issue
                    for issue in result.issues
                )
            )

    def test_reports_selftest_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            module_dir = self._write_module(root, "mod_a")
            (module_dir / "module.py").write_text(
                "\n".join(
                    [
                        "def validateInput(input_data):",
                        "    return input_data",
                        "",
                        "def validateOutput(output):",
                        "    return output",
                        "",
                        "def run(input_data):",
                        "    return None",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            modules = [
                {
                    "id": "mod_a",
                    "name": "Modul A",
                    "path": "modules/mod_a",
                    "enabled": True,
                    "description": "Test",
                }
            ]
            testcases = {"mod_a": {"text": "ok"}}
            self._write_configs(root, modules, testcases)

            result = run_integration_checks(
                root / "config" / "modules.json",
                root / "config" / "module_selftests.json",
            )

            self.assertTrue(any("Selftest fehlgeschlagen" in issue for issue in result.issues))


if __name__ == "__main__":
    unittest.main()

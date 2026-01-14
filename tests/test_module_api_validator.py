import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from module_api_validator import validate_module_api


class ModuleApiValidatorTests(unittest.TestCase):
    def _write_module(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def test_validate_module_api_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            entry = Path(tmp_dir) / "module.py"
            self._write_module(
                entry,
                "\n".join(
                    [
                        "def validateInput(input_data):",
                        "    return input_data",
                        "",
                        "def validateOutput(output):",
                        "    return output",
                        "",
                        "def run(input_data):",
                        "    return {'status': 'ok'}",
                        "",
                    ]
                ),
            )

            issues = validate_module_api(entry)

            self.assertEqual(issues, [])

    def test_validate_module_api_missing_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            entry = Path(tmp_dir) / "module.py"
            self._write_module(
                entry,
                "\n".join(
                    [
                        "def validateInput(input_data):",
                        "    return input_data",
                        "",
                        "def validateOutput(output):",
                        "    return output",
                    ]
                ),
            )

            issues = validate_module_api(entry)

            self.assertTrue(any("run" in issue for issue in issues))

    def test_validate_module_api_missing_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            entry = Path(tmp_dir) / "module.py"
            self._write_module(
                entry,
                "\n".join(
                    [
                        "def run(input_data):",
                        "    return {'status': 'ok'}",
                    ]
                ),
            )

            issues = validate_module_api(entry)

            self.assertTrue(any("validateInput" in issue for issue in issues))
            self.assertTrue(any("validateOutput" in issue for issue in issues))

    def test_validate_module_api_run_needs_args(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            entry = Path(tmp_dir) / "module.py"
            self._write_module(
                entry,
                "\n".join(
                    [
                        "def validateInput(input_data):",
                        "    return input_data",
                        "",
                        "def validateOutput(output):",
                        "    return output",
                        "",
                        "def run():",
                        "    return {'status': 'ok'}",
                    ]
                ),
            )

            issues = validate_module_api(entry)

            self.assertTrue(any("mindestens ein Argument" in issue for issue in issues))

    def test_validate_module_api_syntax_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            entry = Path(tmp_dir) / "module.py"
            self._write_module(entry, "def run(:\n    pass\n")

            issues = validate_module_api(entry)

            self.assertTrue(any("Syntaxfehler" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()

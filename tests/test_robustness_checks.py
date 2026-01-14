import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from health_check import run_health_check
from json_validator import validate_json_file


class RobustnessChecksTests(unittest.TestCase):
    def _build_health_root(self, root: Path) -> None:
        for folder in ("config", "system", "scripts", "modules", "data", "logs", "tests", "src"):
            (root / folder).mkdir(parents=True, exist_ok=True)

        (root / "config" / "modules.json").write_text("{}", encoding="utf-8")
        (root / "config" / "launcher_gui.json").write_text("{}", encoding="utf-8")
        (root / "config" / "requirements.txt").write_text("pytest\n", encoding="utf-8")
        test_gate_payload = {
            "threshold": 1,
            "todo_path": "todo.txt",
            "state_path": "data/test.json",
            "tests_command": ["echo", "ok"],
        }
        (root / "config" / "test_gate.json").write_text(
            json.dumps(test_gate_payload),
            encoding="utf-8",
        )
        (root / "todo.txt").write_text("# todo\n", encoding="utf-8")
        (root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
        (root / "DEV_DOKU.md").write_text("# DEV_DOKU\n", encoding="utf-8")
        (root / "DONE.md").write_text("# DONE\n", encoding="utf-8")
        (root / "PROGRESS.md").write_text("# PROGRESS\n", encoding="utf-8")

        for script_name in ("start.sh", "run_tests.sh"):
            script_path = root / "scripts" / script_name
            script_path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            script_path.chmod(0o755)

        klick_start = root / "klick_start.sh"
        klick_start.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        klick_start.chmod(0o755)

    def test_health_check_reports_unreadable_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._build_health_root(root)
            target = root / "config" / "requirements.txt"

            def fake_access(path, mode):
                if Path(path) == target:
                    return False
                return True

            with patch("os.access", side_effect=fake_access):
                issues, _ = run_health_check(root, self_repair=False)

            self.assertTrue(any("Datei nicht lesbar" in issue for issue in issues))

    def test_health_check_repairs_unreadable_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._build_health_root(root)
            target = root / "config" / "requirements.txt"
            target.chmod(0o644)

            def fake_access(path, mode):
                if Path(path) == target:
                    return False
                return True

            with patch("os.access", side_effect=fake_access):
                issues, repairs = run_health_check(root, self_repair=True)

            self.assertFalse(any("Datei nicht lesbar" in issue for issue in issues))
            self.assertTrue(any("Leserechte repariert" in repair for repair in repairs))

    def test_health_check_repairs_unexecutable_script(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._build_health_root(root)
            script_path = root / "scripts" / "run_tests.sh"
            script_path.chmod(0o644)

            issues, repairs = run_health_check(root, self_repair=True)

            self.assertFalse(any("nicht ausführbar" in issue for issue in issues))
            self.assertTrue(any("Ausführrechte repariert" in repair for repair in repairs))

    def test_json_validator_handles_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "broken.json"
            path.write_text("{ broken", encoding="utf-8")

            result = validate_json_file(path)

            self.assertTrue(any("JSON ist ungültig" in issue for issue in result.issues))


if __name__ == "__main__":
    unittest.main()

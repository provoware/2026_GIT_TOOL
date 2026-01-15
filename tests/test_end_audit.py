import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

import end_audit


class EndAuditTests(unittest.TestCase):
    def test_end_audit_reports_open_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "config").mkdir()
            (root / "modules").mkdir()
            (root / "scripts").mkdir()
            (root / "data").mkdir()

            (root / "config" / "modules.json").write_text(
                json.dumps({"modules": []}), encoding="utf-8"
            )
            (root / "config" / "launcher_gui.json").write_text("{}", encoding="utf-8")
            (root / "config" / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
            (root / "config" / "ruff.toml").write_text("[tool.ruff]\n", encoding="utf-8")
            (root / "config" / "black.toml").write_text("[tool.black]\n", encoding="utf-8")
            (root / "config" / "module_selftests.json").write_text(
                json.dumps({"testcases": {}}), encoding="utf-8"
            )
            (root / "config" / "selective_export.json").write_text(
                json.dumps(
                    {
                        "default_preset": "logs_only",
                        "output_dir": "data/exports",
                        "base_name": "selective_export",
                        "presets": {
                            "logs_only": {"label": "Nur Logs", "includes": ["logs"], "excludes": []}
                        },
                    }
                ),
                encoding="utf-8",
            )
            (root / "config" / "todo_config.json").write_text(
                json.dumps({"todo_path": "todo.txt", "archive_path": "data/todo_archive.txt"}),
                encoding="utf-8",
            )
            (root / "scripts" / "start.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            (root / "scripts" / "run_tests.sh").write_text(
                "#!/usr/bin/env bash\n", encoding="utf-8"
            )
            (root / "todo.txt").write_text("[ ] Demo-Aufgabe\n", encoding="utf-8")

            report = end_audit.run_end_audit(root)

            self.assertEqual(report.open_tasks, 1)
            self.assertEqual(report.status, "nicht bereit")


if __name__ == "__main__":
    unittest.main()

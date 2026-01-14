import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from diagnostics_runner import run_diagnostics


class DiagnosticsRunnerTests(unittest.TestCase):
    def test_run_diagnostics_returns_ok(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "diag.sh"
            script_path.write_text("echo 'ok'\n", encoding="utf-8")

            result = run_diagnostics(script_path, timeout_seconds=5)

            self.assertEqual("ok", result.status)
            self.assertEqual(0, result.exit_code)
            self.assertIn("ok", result.output)


if __name__ == "__main__":
    unittest.main()

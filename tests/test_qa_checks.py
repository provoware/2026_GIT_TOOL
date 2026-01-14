import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

import qa_checks


class QualityChecksTests(unittest.TestCase):
    def test_classify_issue_detects_severity(self):
        self.assertEqual("schwer", qa_checks.classify_issue("Datei fehlt: config.json"))
        self.assertEqual("leicht", qa_checks.classify_issue("Hinweis: optionaler Eintrag"))
        self.assertEqual("mittel", qa_checks.classify_issue("Unbekanntes Problem"))

    def test_check_release_files_reports_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "config").mkdir()
            (root / "scripts").mkdir()
            (root / "config" / "modules.json").write_text(
                json.dumps({"modules": []}), encoding="utf-8"
            )
            report = qa_checks.check_release_files(root)
            self.assertEqual("rot", report.traffic_light)
            self.assertTrue(report.issues)


if __name__ == "__main__":
    unittest.main()

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from log_exporter import export_logs


class LogExporterTests(unittest.TestCase):
    def test_export_logs_creates_zip_with_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            logs_dir = base / "logs"
            export_dir = base / "exports"
            logs_dir.mkdir()

            (logs_dir / "app.log").write_text("Testlog", encoding="utf-8")
            (logs_dir / "error.log").write_text("Fehler", encoding="utf-8")

            export_path = export_logs(logs_dir, export_dir)

            self.assertTrue(export_path.exists())
            with zipfile.ZipFile(export_path, "r") as archive:
                names = set(archive.namelist())
            self.assertEqual({"app.log", "error.log"}, names)

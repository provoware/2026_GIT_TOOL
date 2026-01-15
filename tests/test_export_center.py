import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from export_center import ExportConfig, run_export


class ExportCenterTests(unittest.TestCase):
    def test_run_export_creates_all_formats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = root / "data"
            logs_dir = root / "logs"
            data_dir.mkdir()
            logs_dir.mkdir()
            (data_dir / "sample.json").write_text('{"ok": true}', encoding="utf-8")
            (logs_dir / "sample.log").write_text("ok", encoding="utf-8")
            output_dir = root / "exports"

            config = ExportConfig(
                output_dir=output_dir,
                sources=[data_dir, logs_dir],
                report_base_name="report",
                include_extensions=[".json", ".log"],
                enabled_formats=["json", "txt", "pdf", "zip"],
            )

            result = run_export(config)

            self.assertTrue(result.report_paths)
            self.assertTrue(result.zip_path is not None)
            pdf_files = [path for path in result.report_paths if path.suffix == ".pdf"]
            self.assertTrue(pdf_files)
            self.assertTrue(pdf_files[0].read_bytes().startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src" / "records"))

from zip_exporter import ZipExportConfig, load_state, run_zip_export


class ZipExporterTests(unittest.TestCase):
    def test_run_zip_export_creates_archive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "data").mkdir()
            (root / "data" / "exports").mkdir(parents=True)
            (root / "file.txt").write_text("hi", encoding="utf-8")
            state_path = root / "data" / "zip_export_state.json"
            state_path.write_text(
                json.dumps({"pending_steps": 0, "export_index": 0, "last_export": None}),
                encoding="utf-8",
            )

            config = ZipExportConfig(
                enabled=True,
                step_count=2,
                state_path=Path("data/zip_export_state.json"),
                output_dir=Path("data/exports"),
                excludes=["data/exports"],
            )
            logger = __import__("logging").getLogger("test_zip")
            created = run_zip_export(root, 2, config, logger)

            self.assertEqual(len(created), 1)
            self.assertTrue(created[0].exists())
            state = load_state(state_path)
            self.assertEqual(state["export_index"], 1)


if __name__ == "__main__":
    unittest.main()

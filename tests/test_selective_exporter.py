import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

import selective_exporter


class SelectiveExporterTests(unittest.TestCase):
    def test_build_export_contains_only_included_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "config").mkdir()
            (root / "modules").mkdir()
            logs_dir = root / "logs"
            logs_dir.mkdir()
            config_dir = root / "config"
            (logs_dir / "app.log").write_text("log", encoding="utf-8")
            (config_dir / "settings.json").write_text("{}", encoding="utf-8")

            preset = selective_exporter.ExportPreset(
                name="logs_only",
                label="Nur Logs",
                includes=["logs"],
                excludes=[],
            )
            export_path = selective_exporter.build_export(
                root=root,
                preset=preset,
                output_dir=Path("data/exports"),
                base_name="selective_export",
            )

            with zipfile.ZipFile(export_path, "r") as archive:
                names = set(archive.namelist())

            self.assertIn("logs/app.log", names)
            self.assertNotIn("config/settings.json", names)


if __name__ == "__main__":
    unittest.main()

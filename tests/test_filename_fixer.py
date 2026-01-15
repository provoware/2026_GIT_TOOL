import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from filename_fixer import normalize_filename, run_fix


class FilenameFixerTests(unittest.TestCase):
    def test_normalize_filename_snake_case(self):
        path = Path("Bad Name.TXT")

        normalized = normalize_filename(path)

        self.assertEqual("bad_name.txt", normalized.name)

    def test_run_fix_renames_in_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = root / "data"
            data_dir.mkdir(parents=True)
            config_dir = root / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "filename_suffixes.json").write_text(
                '{\n  "defaults": {"data": ".json", "logs": ".log"}\n}\n',
                encoding="utf-8",
            )
            source = data_dir / "Mein Bericht 2026.TXT"
            source.write_text("ok", encoding="utf-8")

            actions = run_fix(root, dry_run=False)

            self.assertTrue(actions)
            expected = data_dir / "mein_bericht_2026.txt"
            self.assertTrue(expected.exists())

    def test_run_fix_adds_suffix_rule(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = root / "data"
            data_dir.mkdir(parents=True)
            config_dir = root / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "filename_suffixes.json").write_text(
                '{\n  "defaults": {"data": ".json", "logs": ".log"}\n}\n',
                encoding="utf-8",
            )
            source = data_dir / "Bericht_2026"
            source.write_text("ok", encoding="utf-8")

            actions = run_fix(root, dry_run=False)

            self.assertTrue(actions)
            expected = data_dir / "bericht_2026.json"
            self.assertTrue(expected.exists())


if __name__ == "__main__":
    unittest.main()

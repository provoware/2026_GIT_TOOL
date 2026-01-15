import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from backup_center import BackupConfig, create_backup


class BackupCenterTests(unittest.TestCase):
    def test_create_backup_writes_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = root / "data"
            data_dir.mkdir()
            (data_dir / "note.txt").write_text("ok", encoding="utf-8")
            output_dir = root / "backups"
            state_path = root / "backup_state.json"

            config = BackupConfig(
                output_dir=output_dir,
                sources=[data_dir],
                exclude_dirs=[],
                max_backups=3,
            )
            result = create_backup(config, state_path)

            self.assertTrue(result.archive_path.exists())
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(str(result.archive_path), payload["archive"])


if __name__ == "__main__":
    unittest.main()

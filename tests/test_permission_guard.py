import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

import permission_guard


class PermissionGuardTests(unittest.TestCase):
    def _write_manifest(self, module_dir: Path, permissions) -> None:
        payload = {
            "id": module_dir.name,
            "name": "Demo",
            "version": "1.0.0",
            "entry": "module.py",
            "permissions": permissions,
        }
        (module_dir / "manifest.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def test_write_allowed_with_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "config").mkdir()
            (root / "modules").mkdir()
            (root / "data").mkdir()
            module_dir = root / "modules" / "demo_modul"
            module_dir.mkdir()
            module_file = module_dir / "module.py"
            module_file.write_text("# demo", encoding="utf-8")
            self._write_manifest(module_dir, ["write:data"])

            target = root / "data" / "demo.json"
            permission_guard.require_write_access(module_file, target, "Test schreiben")

    def test_write_denied_without_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "config").mkdir()
            (root / "modules").mkdir()
            (root / "data").mkdir()
            module_dir = root / "modules" / "demo_modul"
            module_dir.mkdir()
            module_file = module_dir / "module.py"
            module_file.write_text("# demo", encoding="utf-8")
            self._write_manifest(module_dir, ["read:data"])

            target = root / "data" / "demo.json"
            with self.assertRaises(permission_guard.PermissionGuardError):
                permission_guard.require_write_access(module_file, target, "Test schreiben")

    def test_read_only_mode_blocks_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "config").mkdir()
            (root / "modules").mkdir()
            (root / "data").mkdir()
            module_dir = root / "modules" / "demo_modul"
            module_dir.mkdir()
            module_file = module_dir / "module.py"
            module_file.write_text("# demo", encoding="utf-8")
            self._write_manifest(module_dir, ["write:data"])

            target = root / "data" / "demo.json"
            original = os.environ.get("GENREARCHIV_WRITE_MODE")
            os.environ["GENREARCHIV_WRITE_MODE"] = "read-only"
            try:
                with self.assertRaises(permission_guard.PermissionGuardError):
                    permission_guard.require_write_access(module_file, target, "Test schreiben")
            finally:
                if original is None:
                    os.environ.pop("GENREARCHIV_WRITE_MODE", None)
                else:
                    os.environ["GENREARCHIV_WRITE_MODE"] = original


if __name__ == "__main__":
    unittest.main()

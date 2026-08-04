from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "system"))

import startup_preflight as preflight  # noqa: E402


def _build_root(tmp_path: Path) -> Path:
    root = tmp_path / "Provoware_Memo"
    for directory in preflight.REQUIRED_DIRS:
        (root / directory).mkdir(parents=True, exist_ok=True)
    for relative in preflight.REQUIRED_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative == "config/product.json":
            path.write_text(
                json.dumps({"id": "provoware_memo", "name": "Provoware Memo"}),
                encoding="utf-8",
            )
        elif relative.endswith(".json"):
            path.write_text("{}\n", encoding="utf-8")
        else:
            path.write_text("# test\n", encoding="utf-8")
    return root


def test_preflight_accepts_complete_provoware_memo_project(tmp_path: Path) -> None:
    root = _build_root(tmp_path)
    checks = preflight.validate(root)
    assert checks
    assert all(item.status == "ok" for item in checks)


def test_preflight_rejects_missing_launcher_before_any_start(tmp_path: Path) -> None:
    root = _build_root(tmp_path)
    (root / "system/launcher_gui.py").unlink()
    checks = preflight.validate(root)
    critical = next(item for item in checks if item.name == "critical_files")
    assert critical.status == "error"
    assert "system/launcher_gui.py" in critical.detail


def test_preflight_rejects_wrong_product_identity(tmp_path: Path) -> None:
    root = _build_root(tmp_path)
    (root / "config/product.json").write_text(
        json.dumps({"id": "other", "name": "Other"}), encoding="utf-8"
    )
    checks = preflight.validate(root)
    identity = next(item for item in checks if item.name == "product_identity")
    assert identity.status == "error"

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1] / "modules" / "archiv_manager"
sys.path.insert(0, str(MODULE_DIR))


def load_entry():
    path = MODULE_DIR / "entry.py"
    spec = importlib.util.spec_from_file_location("archiv_manager_entry_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_module_contract_and_shared_service_actions(tmp_path: Path):
    module = load_entry()
    database = tmp_path / "archive.sqlite3"
    init_result = module.init({"database_path": str(database), "headless": True})
    assert module.validateOutput(init_result)
    list_result = module.run({"action": "list_archives", "database_path": str(database)})
    assert list_result["status"] == "ok"
    assert len(list_result["payload"]["archives"]) == 7
    add_result = module.run({
        "action": "add_entries", "database_path": str(database),
        "archive": "stimmungen", "category": "Dunkel",
        "value": "Bedrohlich, bedrohlich, Düster", "source": "module-test",
    })
    assert add_result["status"] == "ok"
    assert len(add_result["payload"]["inserted"]) == 2
    assert add_result["payload"]["duplicates"] == ["bedrohlich"]
    assert module.validateInput({"action": "list_entries"})
    assert not module.validateInput("invalid")


def test_module_can_create_and_update_archive(tmp_path: Path):
    module = load_entry()
    database = tmp_path / "archive.sqlite3"
    created = module.run({
        "action": "create_archive", "database_path": str(database),
        "name": "Recherche", "description": "Quellen und Hinweise",
        "split_on_comma": True,
    })
    archive_id = created["payload"]["archive"]["id"]
    updated = module.run({
        "action": "update_archive", "database_path": str(database),
        "archive_id": archive_id, "split_on_comma": False,
    })
    assert updated["payload"]["archive"]["split_on_comma"] is False

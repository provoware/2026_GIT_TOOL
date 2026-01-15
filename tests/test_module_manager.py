from pathlib import Path

from module_manager import ModuleManager


def test_module_manager_loads_registry() -> None:
    config_path = Path(__file__).resolve().parents[1] / "config" / "modules.json"
    manager = ModuleManager(config_path=config_path, debug=False)
    states = manager.list_states()
    assert states
    assert all(state.entry.module_id for state in states)


def test_module_manager_activate_deactivate() -> None:
    config_path = Path(__file__).resolve().parents[1] / "config" / "modules.json"
    manager = ModuleManager(config_path=config_path, debug=True)
    result = manager.activate_module("status")
    assert result.status in {"ok", "warn"}
    state = manager.get_state("status")
    assert state.active

    result = manager.deactivate_module("status")
    assert result.status in {"ok", "warn"}
    state = manager.get_state("status")
    assert not state.active

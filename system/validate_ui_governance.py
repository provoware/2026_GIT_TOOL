#!/usr/bin/env python3
"""Validiert den maschinenlesbaren Vertrag der UI-Modernisierung."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config" / "ui-governance.json"
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "phase",
    "current_block",
    "title",
    "principles",
    "authoritative_sources",
    "transitional_sources",
    "planned_responsibilities",
    "forbidden_parallel_sources",
    "protected_contracts",
    "duplication_register",
    "non_goals",
    "acceptance_criteria",
    "migration_order",
    "next_permitted_block",
}
ALLOWED_SOURCE_STATUSES = {
    "authoritative",
    "generated",
    "hardened",
    "protected",
    "feature_local",
}
ALLOWED_SEVERITIES = {"info", "low", "medium", "high", "critical"}
BLOCK_1_ALLOWED_PATHS = frozenset(
    {
        ".github/workflows/ui-modernization-block-1.yml",
        "config/ui-governance.json",
        "system/validate_ui_governance.py",
        "tests/test_ui_governance.py",
        "dateiindex/struktur/UI_MODERNISIERUNG_BLOCK_1.md",
        "dateiindex/struktur/TESTMATRIX_UI_MODERNISIERUNG.md",
        "dateiindex/gehaertet/UI_MODERNISIERUNG_BLOCK_1.md",
        "dateiindex/index.json",
    }
)
BLOCK_2_ALLOWED_PATHS = frozenset(
    {
        ".github/workflows/ui-modernization-block-1.yml",
        ".github/workflows/ui-modernization-block-2.yml",
        "config/ui-governance.json",
        "system/validate_ui_governance.py",
        "tests/test_ui_governance.py",
        "system/generate_design_tokens.py",
        "tests/test_design_token_runtime.py",
        "generated/design_tokens.py",
        "dateiindex/struktur/UI_MODERNISIERUNG_BLOCK_1.md",
        "dateiindex/struktur/UI_MODERNISIERUNG_BLOCK_2.md",
        "dateiindex/struktur/TESTMATRIX_UI_MODERNISIERUNG.md",
        "dateiindex/gehaertet/UI_MODERNISIERUNG_BLOCK_2.md",
        "dateiindex/index.json",
    }
)
BLOCK_ALLOWED_PATHS = {1: BLOCK_1_ALLOWED_PATHS, 2: BLOCK_2_ALLOWED_PATHS}


class UiGovernanceError(ValueError):
    """Der Governance-Vertrag ist unvollständig oder widersprüchlich."""


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise UiGovernanceError(f"{label} muss ein Objekt sein.")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise UiGovernanceError(f"{label} muss eine nichtleere Liste sein.")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UiGovernanceError(f"{label} muss nichtleerer Text sein.")
    return value.strip()


def _positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise UiGovernanceError(f"{label} muss eine positive Ganzzahl sein.")
    return value


def _unique_texts(values: Sequence[Any], label: str) -> list[str]:
    texts = [_text(value, f"{label}[{index}]") for index, value in enumerate(values)]
    if len(set(texts)) != len(texts):
        raise UiGovernanceError(f"{label} enthält doppelte Einträge.")
    return texts


def _repo_path(root: Path, value: Any, label: str, *, must_exist: bool) -> Path:
    text = _text(value, label)
    relative = Path(text)
    if relative.is_absolute() or ".." in relative.parts:
        raise UiGovernanceError(f"{label} muss ein sicherer relativer Repositorypfad sein.")
    resolved_root = root.resolve()
    resolved = (resolved_root / relative).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise UiGovernanceError(f"{label} liegt außerhalb des Repositorys.")
    if must_exist and not resolved.exists():
        raise UiGovernanceError(f"{label} fehlt: {text}")
    return resolved


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    if not isinstance(path, Path):
        raise UiGovernanceError("policy_path muss ein Path sein.")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise UiGovernanceError(f"Governance-Datei fehlt: {path}") from exc
    except json.JSONDecodeError as exc:
        raise UiGovernanceError(f"Governance-JSON ist ungültig: {exc}") from exc
    if not isinstance(value, dict):
        raise UiGovernanceError("Governance-JSON muss ein Objekt sein.")
    return value


def _validate_current_sources(data: Mapping[str, Any], root: Path) -> dict[str, str]:
    responsibilities: list[str] = []
    owners: dict[str, str] = {}
    for index, raw in enumerate(_list(data["authoritative_sources"], "authoritative_sources")):
        item = _mapping(raw, f"authoritative_sources[{index}]")
        responsibility = _text(item.get("responsibility"), f"authoritative_sources[{index}].responsibility")
        owner = _text(item.get("owner"), f"authoritative_sources[{index}].owner")
        status = _text(item.get("status"), f"authoritative_sources[{index}].status")
        if status not in ALLOWED_SOURCE_STATUSES:
            raise UiGovernanceError(f"Unzulässiger Quellenstatus: {status}")
        _repo_path(root, owner, f"authoritative_sources[{index}].owner", must_exist=True)
        responsibilities.append(responsibility)
        owners[responsibility] = owner
    if len(set(responsibilities)) != len(responsibilities):
        raise UiGovernanceError("Eine aktuelle Verantwortung besitzt mehrere Quellenangaben.")
    if owners.get("design_tokens") != "config/design-tokens.json":
        raise UiGovernanceError("config/design-tokens.json muss die autoritative Tokenquelle bleiben.")
    return owners


def _validate_future_entries(data: Mapping[str, Any], root: Path, current_block: int) -> None:
    transitional_paths: list[str] = []
    for index, raw in enumerate(_list(data["transitional_sources"], "transitional_sources")):
        item = _mapping(raw, f"transitional_sources[{index}]")
        path = _text(item.get("path"), f"transitional_sources[{index}].path")
        _repo_path(root, path, f"transitional_sources[{index}].path", must_exist=True)
        _unique_texts(_list(item.get("duplicates"), f"transitional_sources[{index}].duplicates"), f"transitional_sources[{index}].duplicates")
        _unique_texts(_list(item.get("retain"), f"transitional_sources[{index}].retain"), f"transitional_sources[{index}].retain")
        if _positive_int(item.get("target_block"), f"transitional_sources[{index}].target_block") <= current_block:
            raise UiGovernanceError("Temporäre Quellen müssen in einem späteren Block behandelt werden.")
        transitional_paths.append(path)
    if len(set(transitional_paths)) != len(transitional_paths):
        raise UiGovernanceError("Temporäre Quellen sind doppelt eingetragen.")

    forbidden = _unique_texts(_list(data["forbidden_parallel_sources"], "forbidden_parallel_sources"), "forbidden_parallel_sources")
    for index, path in enumerate(forbidden):
        if _repo_path(root, path, f"forbidden_parallel_sources[{index}]", must_exist=False).exists():
            raise UiGovernanceError(f"Verbotene Parallelquelle existiert: {path}")

    ids: list[str] = []
    targets: list[str] = []
    for index, raw in enumerate(_list(data["planned_responsibilities"], "planned_responsibilities")):
        item = _mapping(raw, f"planned_responsibilities[{index}]")
        responsibility = _text(item.get("responsibility"), f"planned_responsibilities[{index}].responsibility")
        target = _text(item.get("target"), f"planned_responsibilities[{index}].target")
        _repo_path(root, target, f"planned_responsibilities[{index}].target", must_exist=False)
        if _positive_int(item.get("target_block"), f"planned_responsibilities[{index}].target_block") <= current_block:
            raise UiGovernanceError("Geplante Verantwortung muss in einem späteren Block liegen.")
        condition = _text(item.get("condition"), f"planned_responsibilities[{index}].condition")
        if condition != "always":
            consumers = _unique_texts(_list(item.get("current_consumers"), f"planned_responsibilities[{index}].current_consumers"), f"planned_responsibilities[{index}].current_consumers")
            for consumer_index, consumer in enumerate(consumers):
                _repo_path(root, consumer, f"planned_responsibilities[{index}].current_consumers[{consumer_index}]", must_exist=True)
        if target in forbidden:
            raise UiGovernanceError(f"Geplantes Ziel ist zugleich verboten: {target}")
        ids.append(responsibility)
        targets.append(target)
    if len(set(ids)) != len(ids) or len(set(targets)) != len(targets):
        raise UiGovernanceError("Geplante Verantwortungen und Zielpfade müssen eindeutig sein.")
    if "system/ui_tokens.py" in targets:
        raise UiGovernanceError("Ein handgepflegtes system/ui_tokens.py ist nicht zulässig.")


def _validate_contracts_and_duplicates(data: Mapping[str, Any], root: Path, current_block: int) -> None:
    contracts: list[str] = []
    for index, raw in enumerate(_list(data["protected_contracts"], "protected_contracts")):
        item = _mapping(raw, f"protected_contracts[{index}]")
        path = _text(item.get("path"), f"protected_contracts[{index}].path")
        _repo_path(root, path, f"protected_contracts[{index}].path", must_exist=True)
        evidence = _unique_texts(_list(item.get("evidence"), f"protected_contracts[{index}].evidence"), f"protected_contracts[{index}].evidence")
        for evidence_index, evidence_path in enumerate(evidence):
            _repo_path(root, evidence_path, f"protected_contracts[{index}].evidence[{evidence_index}]", must_exist=True)
        contracts.append(path)
    if len(set(contracts)) != len(contracts):
        raise UiGovernanceError("Geschützte Verträge sind doppelt eingetragen.")

    ids: list[str] = []
    topics: list[str] = []
    for index, raw in enumerate(_list(data["duplication_register"], "duplication_register")):
        item = _mapping(raw, f"duplication_register[{index}]")
        duplicate_id = _text(item.get("id"), f"duplication_register[{index}].id")
        topic = _text(item.get("topic"), f"duplication_register[{index}].topic")
        severity = _text(item.get("severity"), f"duplication_register[{index}].severity")
        if severity not in ALLOWED_SEVERITIES:
            raise UiGovernanceError(f"Unzulässige Duplikatschwere: {severity}")
        locations = _unique_texts(_list(item.get("locations"), f"duplication_register[{index}].locations"), f"duplication_register[{index}].locations")
        for location_index, location in enumerate(locations):
            _repo_path(root, location, f"duplication_register[{index}].locations[{location_index}]", must_exist=True)
        _text(item.get("decision"), f"duplication_register[{index}].decision")
        if _positive_int(item.get("target_block"), f"duplication_register[{index}].target_block") <= current_block:
            raise UiGovernanceError("Duplikatentscheidungen müssen einem späteren Block zugeordnet sein.")
        ids.append(duplicate_id)
        topics.append(topic)
    if len(set(ids)) != len(ids) or len(set(topics)) != len(topics):
        raise UiGovernanceError("Duplikat-IDs und Themen müssen eindeutig sein.")


def validate_policy(policy: Mapping[str, Any], *, root: Path = ROOT) -> Mapping[str, Any]:
    data = _mapping(policy, "policy")
    missing = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing:
        raise UiGovernanceError(f"Governance-Felder fehlen: {', '.join(missing)}")
    _positive_int(data["schema_version"], "schema_version")
    _text(data["phase"], "phase")
    current_block = _positive_int(data["current_block"], "current_block")
    _text(data["title"], "title")

    principles = _mapping(data["principles"], "principles")
    for key in (
        "single_authoritative_owner",
        "tests_before_visual_migration",
        "preserve_hardened_contracts",
        "prefer_extension_over_parallel_implementation",
        "forbid_parallel_token_sources",
        f"forbid_visual_runtime_migration_in_block_{current_block}",
    ):
        if principles.get(key) is not True:
            raise UiGovernanceError(f"principles.{key} muss true sein.")
    if _positive_int(principles.get("minimum_real_consumers_for_shared_component"), "principles.minimum_real_consumers_for_shared_component") < 2:
        raise UiGovernanceError("Gemeinsame Komponenten benötigen mindestens zwei reale Verbraucher.")
    _unique_texts(_list(principles.get("single_consumer_exceptions"), "principles.single_consumer_exceptions"), "principles.single_consumer_exceptions")

    owners = _validate_current_sources(data, root)
    if current_block >= 2 and owners.get("python_design_token_runtime") != "generated/design_tokens.py":
        raise UiGovernanceError("Block 2 benötigt generated/design_tokens.py als Runtimequelle.")
    _validate_future_entries(data, root, current_block)
    _validate_contracts_and_duplicates(data, root, current_block)
    _unique_texts(_list(data["non_goals"], "non_goals"), "non_goals")

    criterion_ids: list[str] = []
    for index, raw in enumerate(_list(data["acceptance_criteria"], "acceptance_criteria")):
        item = _mapping(raw, f"acceptance_criteria[{index}]")
        criterion_ids.append(_text(item.get("id"), f"acceptance_criteria[{index}].id"))
        _text(item.get("text"), f"acceptance_criteria[{index}].text")
    if len(set(criterion_ids)) != len(criterion_ids):
        raise UiGovernanceError("Akzeptanzkriterien besitzen doppelte IDs.")

    blocks: list[int] = []
    for index, raw in enumerate(_list(data["migration_order"], "migration_order")):
        item = _mapping(raw, f"migration_order[{index}]")
        block = _positive_int(item.get("block"), f"migration_order[{index}].block")
        if block <= current_block:
            raise UiGovernanceError("Migrationsblöcke müssen nach dem aktuellen Block liegen.")
        _text(item.get("name"), f"migration_order[{index}].name")
        if not isinstance(item.get("visual_migration"), bool):
            raise UiGovernanceError(f"migration_order[{index}].visual_migration muss bool sein.")
        blocks.append(block)
    if blocks != sorted(set(blocks)):
        raise UiGovernanceError("Migrationsblöcke müssen eindeutig und aufsteigend sortiert sein.")
    next_block = _positive_int(data["next_permitted_block"], "next_permitted_block")
    if next_block != blocks[0] or next_block != current_block + 1:
        raise UiGovernanceError("Der nächste zulässige Block muss unmittelbar auf den aktuellen Block folgen.")
    return data


def allowed_paths_for_block(block: int) -> frozenset[str]:
    block = _positive_int(block, "block")
    try:
        return BLOCK_ALLOWED_PATHS[block]
    except KeyError as exc:
        raise UiGovernanceError(f"Für Block {block} ist noch keine Diff-Whitelist definiert.") from exc


def validate_changed_paths(paths: Iterable[str], *, block: int = 1, allowed: frozenset[str] | None = None) -> list[str]:
    allowed_paths = allowed if allowed is not None else allowed_paths_for_block(block)
    normalized: list[str] = []
    for index, value in enumerate(paths):
        text = _text(value, f"changed_paths[{index}]").replace("\\", "/")
        if text.startswith("./"):
            text = text[2:]
        if text not in allowed_paths:
            raise UiGovernanceError(f"Block {block} darf diese Datei nicht ändern: {text}")
        normalized.append(text)
    if len(set(normalized)) != len(normalized):
        raise UiGovernanceError("Die Liste geänderter Pfade enthält Duplikate.")
    return normalized


def _read_changed_paths(path: Path) -> list[str]:
    try:
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except FileNotFoundError as exc:
        raise UiGovernanceError(f"Dateiliste fehlt: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="UI-Governance prüfen.")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--changed-paths-file", type=Path)
    args = parser.parse_args()
    try:
        policy = load_policy(args.policy)
        validate_policy(policy, root=args.root)
        changed_count = 0
        if args.changed_paths_file is not None:
            changed = _read_changed_paths(args.changed_paths_file)
            validate_changed_paths(changed, block=int(policy["current_block"]))
            changed_count = len(changed)
    except (UiGovernanceError, OSError) as exc:
        print(f"UI-Governance-Fehler: {exc}")
        return 2
    print(
        "UI-Governance ist gültig: "
        f"Block {policy['current_block']}, "
        f"{len(policy['authoritative_sources'])} Quellen, "
        f"{len(policy['protected_contracts'])} geschützte Verträge, "
        f"{changed_count} geprüfte Änderungsdateien."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
